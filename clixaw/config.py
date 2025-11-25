"""Configuration management for clixaw."""

import os
from pathlib import Path
from typing import Optional

try:
    import tomli
except ImportError:
    tomli = None


def get_config_dir() -> Path:
    """Get the configuration directory path."""
    # Use XDG_CONFIG_HOME if available, otherwise use ~/.config
    config_home = os.getenv("XDG_CONFIG_HOME")
    if config_home:
        return Path(config_home) / "clixaw"
    else:
        return Path.home() / ".config" / "clixaw"


def get_config_path() -> Path:
    """Get the path to the config.toml file."""
    return get_config_dir() / "config.toml"


def load_config() -> dict:
    """
    Load configuration from config.toml file.
    
    Returns:
        Dictionary containing configuration values, or empty dict if file doesn't exist
    """
    config_path = get_config_path()
    
    if not config_path.exists():
        return {}
    
    if tomli is None:
        # Should not happen if dependencies are installed, but handle gracefully
        return {}
    
    try:
        with open(config_path, "rb") as f:
            return tomli.load(f)
    except Exception:
        # If config file is malformed, return empty dict
        return {}


def get_config_value(section: Optional[str], key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Get a configuration value from config.toml.
    
    Args:
        section: Optional section name (e.g., "api", "provider")
        key: Configuration key name
        default: Default value if not found
    
    Returns:
        Configuration value or default
    """
    config = load_config()
    
    if section:
        if section in config and isinstance(config[section], dict):
            return config[section].get(key, default)
    else:
        # Check root level
        return config.get(key, default)
    
    return default


def get_provider_config() -> dict:
    """
    Get provider-related configuration.
    
    Returns:
        Dictionary with provider, api_key, and model keys
    """
    config = load_config()
    
    provider_config = {}
    
    # Check for [provider] section
    if "provider" in config and isinstance(config["provider"], dict):
        provider_config["provider"] = config["provider"].get("name")
        provider_config["api_key"] = config["provider"].get("api_key")
        provider_config["model"] = config["provider"].get("model")
    else:
        # Check root level (backward compatibility)
        provider_config["provider"] = config.get("provider")
        provider_config["api_key"] = config.get("api_key")
        provider_config["model"] = config.get("model")
    
    # Check for [api] section for api_url
    if "api" in config and isinstance(config["api"], dict):
        provider_config["api_url"] = config["api"].get("url")
    else:
        provider_config["api_url"] = config.get("api_url")
    
    return provider_config

