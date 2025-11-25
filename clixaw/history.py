"""Command history management for clixaw."""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

from clixaw import config


def get_history_path() -> Path:
    """Get the path to the history file."""
    return config.get_config_dir() / "history.json"


def load_history() -> List[Dict[str, Any]]:
    """
    Load command history from file.
    
    Returns:
        List of history entries, each containing query, command, timestamp, and executed flag
    """
    history_path = get_history_path()
    
    if not history_path.exists():
        return []
    
    try:
        with open(history_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        # If file is corrupted, return empty list
        return []


def save_history(history: List[Dict[str, Any]]) -> None:
    """
    Save command history to file.
    
    Args:
        history: List of history entries to save
    """
    history_path = get_history_path()
    
    # Ensure config directory exists
    history_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(history_path, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except IOError:
        # Silently fail if we can't write history
        pass


def add_to_history(
    query: str,
    command: str,
    executed: bool = False,
    exit_code: Optional[int] = None,
) -> None:
    """
    Add a command to history.
    
    Args:
        query: The natural language query
        command: The translated shell command
        executed: Whether the command was executed
        exit_code: Exit code if command was executed (None if not executed)
    """
    history = load_history()
    
    entry = {
        "timestamp": datetime.now().isoformat(),
        "query": query,
        "command": command,
        "executed": executed,
        "exit_code": exit_code,
    }
    
    history.append(entry)
    
    # Keep only last 1000 entries to prevent file from growing too large
    if len(history) > 1000:
        history = history[-1000:]
    
    save_history(history)


def get_history(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Get command history.
    
    Args:
        limit: Maximum number of entries to return (None for all)
    
    Returns:
        List of history entries, most recent first
    """
    history = load_history()
    
    # Return most recent first
    history.reverse()
    
    if limit is not None:
        history = history[:limit]
    
    return history


def clear_history() -> None:
    """Clear all command history."""
    history_path = get_history_path()
    
    if history_path.exists():
        try:
            history_path.unlink()
        except IOError:
            pass


def get_history_entry(index: int) -> Optional[Dict[str, Any]]:
    """
    Get a specific history entry by index (0-based, most recent first).
    
    Args:
        index: Index of the entry to retrieve (0 = most recent)
    
    Returns:
        History entry dict or None if index is out of range
    """
    history = get_history()
    
    if 0 <= index < len(history):
        return history[index]
    
    return None

