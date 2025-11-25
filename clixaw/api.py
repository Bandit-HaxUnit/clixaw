"""API client for cmd.xaw.me service."""

import os
import urllib.parse
from typing import Optional

import requests

from clixaw import cache


def get_api_url() -> str:
    """Get the API URL from environment variable or use default."""
    return os.getenv("XAW_API_URL", "https://cmd.xaw.me")


def translate_query(
    query: str,
    api_url: Optional[str] = None,
    provider: Optional[str] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    use_cache: bool = True,
) -> str:
    """
    Translate a natural language query to a shell command.
    
    Args:
        query: Natural language query string
        api_url: Optional API URL (defaults to XAW_API_URL env var or https://cmd.xaw.me)
        provider: Optional provider name (e.g., "openai", "gemini")
        api_key: Optional API key for custom provider
        model: Optional model override (e.g., "gemini-pro", "gpt-4")
        use_cache: Whether to use cache (default: True)
    
    Returns:
        Translated shell command as plain text
    
    Raises:
        requests.RequestException: If the API request fails
        ValueError: If the response is invalid
    """
    if api_url is None:
        api_url = get_api_url()
    
    # Remove trailing slash if present
    api_url = api_url.rstrip("/")
    
    # Check cache first
    if use_cache:
        cached_command = cache.get_cached_response(
            query, api_url, provider, api_key, model
        )
        if cached_command is not None:
            return cached_command
    
    # Build headers if provider is specified
    headers = {}
    if provider:
        headers["X-Provider"] = provider
    if api_key:
        headers["X-API-Key"] = api_key
    if model:
        headers["X-Model"] = model
    
    # Try query parameter style first (more reliable for special characters)
    try:
        encoded_query = urllib.parse.quote(query, safe="")
        url = f"{api_url}/?q={encoded_query}"
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # API returns plain text, strip whitespace
        command = response.text.strip()
        
        if not command:
            raise ValueError("API returned empty response")
        
        # Cache the response
        if use_cache:
            cache.set_cached_response(query, command, api_url, provider, api_key, model)
        
        return command
    
    except requests.exceptions.RequestException as e:
        # If query parameter style fails, try path-based
        try:
            encoded_query = urllib.parse.quote(query, safe="")
            url = f"{api_url}/{encoded_query}"
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            command = response.text.strip()
            
            if not command:
                raise ValueError("API returned empty response")
            
            # Cache the response
            if use_cache:
                cache.set_cached_response(query, command, api_url, provider, api_key, model)
            
            return command
        
        except requests.exceptions.RequestException:
            # Re-raise the original exception
            raise e

