"""Client-side caching for API responses."""

import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any

from clixaw import config


# Default cache TTL: 7 days
DEFAULT_CACHE_TTL_SECONDS = 7 * 24 * 60 * 60

# Default max cache size: 1000 entries
DEFAULT_MAX_CACHE_SIZE = 1000


def get_cache_path() -> Path:
    """Get the path to the cache file."""
    return config.get_config_dir() / "cache.json"


def get_cache_config() -> Dict[str, Any]:
    """
    Get cache configuration from config file.
    
    Returns:
        Dictionary with cache settings (ttl, max_size, enabled)
    """
    cfg = config.load_config()
    
    cache_config = {
        "ttl": DEFAULT_CACHE_TTL_SECONDS,
        "max_size": DEFAULT_MAX_CACHE_SIZE,
        "enabled": True,
    }
    
    if "cache" in cfg and isinstance(cfg["cache"], dict):
        cache_config["ttl"] = cfg["cache"].get("ttl", DEFAULT_CACHE_TTL_SECONDS)
        cache_config["max_size"] = cfg["cache"].get("max_size", DEFAULT_MAX_CACHE_SIZE)
        cache_config["enabled"] = cfg["cache"].get("enabled", True)
    
    return cache_config


def generate_cache_key(
    query: str,
    api_url: str,
    provider: Optional[str] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
) -> str:
    """
    Generate a cache key from query and API parameters.
    
    Args:
        query: Natural language query
        api_url: API URL
        provider: Optional provider name
        api_key: Optional API key (not included in hash for privacy)
        model: Optional model name
    
    Returns:
        SHA256 hash string as cache key
    """
    # Create a string representation of the cache parameters
    # Note: We don't include api_key in the hash for security/privacy reasons
    # Different API keys with same query/provider/model should use same cache
    cache_string = f"{query}|{api_url}|{provider or ''}|{model or ''}"
    
    return hashlib.sha256(cache_string.encode("utf-8")).hexdigest()


def load_cache() -> Dict[str, Dict[str, Any]]:
    """
    Load cache from file.
    
    Returns:
        Dictionary mapping cache keys to cache entries
    """
    cache_path = get_cache_path()
    
    if not cache_path.exists():
        return {}
    
    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        # If cache file is corrupted, return empty dict
        return {}


def save_cache(cache: Dict[str, Dict[str, Any]]) -> None:
    """
    Save cache to file.
    
    Args:
        cache: Dictionary mapping cache keys to cache entries
    """
    cache_path = get_cache_path()
    
    # Ensure config directory exists
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)
    except IOError:
        # Silently fail if we can't write cache
        pass


def get_cached_response(
    query: str,
    api_url: str,
    provider: Optional[str] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
) -> Optional[str]:
    """
    Get a cached response if available and not expired.
    
    Args:
        query: Natural language query
        api_url: API URL
        provider: Optional provider name
        api_key: Optional API key
        model: Optional model name
    
    Returns:
        Cached command string if found and valid, None otherwise
    """
    cache_config = get_cache_config()
    
    # Check if caching is enabled
    if not cache_config.get("enabled", True):
        return None
    
    cache = load_cache()
    cache_key = generate_cache_key(query, api_url, provider, api_key, model)
    
    if cache_key not in cache:
        return None
    
    entry = cache[cache_key]
    
    # Check if entry is expired
    try:
        cached_time = datetime.fromisoformat(entry.get("timestamp", ""))
        ttl_seconds = cache_config.get("ttl", DEFAULT_CACHE_TTL_SECONDS)
        
        if datetime.now() - cached_time > timedelta(seconds=ttl_seconds):
            # Entry expired, remove it
            del cache[cache_key]
            save_cache(cache)
            return None
    except (ValueError, TypeError):
        # Invalid timestamp, remove entry
        del cache[cache_key]
        save_cache(cache)
        return None
    
    return entry.get("command")


def set_cached_response(
    query: str,
    command: str,
    api_url: str,
    provider: Optional[str] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
) -> None:
    """
    Store a response in the cache.
    
    Args:
        query: Natural language query
        command: Translated shell command
        api_url: API URL
        provider: Optional provider name
        api_key: Optional API key
        model: Optional model name
    """
    cache_config = get_cache_config()
    
    # Check if caching is enabled
    if not cache_config.get("enabled", True):
        return
    
    cache = load_cache()
    cache_key = generate_cache_key(query, api_url, provider, api_key, model)
    
    # Create cache entry
    entry = {
        "timestamp": datetime.now().isoformat(),
        "query": query,
        "command": command,
        "api_url": api_url,
        "provider": provider,
        "model": model,
    }
    
    cache[cache_key] = entry
    
    # Enforce max cache size
    max_size = cache_config.get("max_size", DEFAULT_MAX_CACHE_SIZE)
    if len(cache) > max_size:
        # Remove oldest entries (by timestamp)
        entries = [(k, v) for k, v in cache.items()]
        entries.sort(key=lambda x: x[1].get("timestamp", ""))
        
        # Keep only the most recent max_size entries
        cache = dict(entries[-max_size:])
    
    save_cache(cache)


def clear_cache() -> None:
    """Clear all cached responses."""
    cache_path = get_cache_path()
    
    if cache_path.exists():
        try:
            cache_path.unlink()
        except IOError:
            pass


def get_cache_stats() -> Dict[str, Any]:
    """
    Get cache statistics.
    
    Returns:
        Dictionary with cache statistics (size, oldest_entry, newest_entry)
    """
    cache = load_cache()
    
    if not cache:
        return {
            "size": 0,
            "oldest_entry": None,
            "newest_entry": None,
        }
    
    timestamps = []
    for entry in cache.values():
        try:
            ts = datetime.fromisoformat(entry.get("timestamp", ""))
            timestamps.append(ts)
        except (ValueError, TypeError):
            continue
    
    if not timestamps:
        return {
            "size": len(cache),
            "oldest_entry": None,
            "newest_entry": None,
        }
    
    return {
        "size": len(cache),
        "oldest_entry": min(timestamps).isoformat() if timestamps else None,
        "newest_entry": max(timestamps).isoformat() if timestamps else None,
    }

