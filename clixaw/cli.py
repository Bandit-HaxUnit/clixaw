"""Command-line interface for clixaw."""

import os
import subprocess
import sys
from datetime import datetime
from typing import Optional

import click
import pyperclip
import requests

from clixaw import api, cache, config, history


# Dangerous command patterns that require confirmation
DANGEROUS_PATTERNS = [
    "rm -rf",
    "rm -r",
    "rm -f",
    "rmrf",
    "format",
    "mkfs",
    "dd if=",
    "> /dev/sd",
    "shutdown",
    "reboot",
    "halt",
    "poweroff",
]


def is_dangerous_command(command: str) -> bool:
    """Check if a command contains dangerous patterns."""
    command_lower = command.lower()
    return any(pattern in command_lower for pattern in DANGEROUS_PATTERNS)


def execute_command(command: str, confirm: bool = True) -> int:
    """
    Execute a shell command.
    
    Args:
        command: Shell command to execute
        confirm: Whether to confirm dangerous commands
    
    Returns:
        Exit code of the command
    """
    if confirm and is_dangerous_command(command):
        click.echo(
            click.style("⚠️  Warning: This command may be dangerous!", fg="yellow"),
            err=True,
        )
        click.echo(click.style(f"Command: {command}", fg="yellow"), err=True)
        
        if not click.confirm("Do you want to proceed?", default=False):
            click.echo("Aborted.", err=True)
            return 1
    
    try:
        # Execute the command in the user's shell
        result = subprocess.run(
            command,
            shell=True,
            check=False,
        )
        return result.returncode
    
    except KeyboardInterrupt:
        click.echo("\nInterrupted.", err=True)
        return 130
    
    except Exception as e:
        click.echo(
            click.style(f"Error executing command: {e}", fg="red"),
            err=True,
        )
        return 1


@click.group(invoke_without_command=True)
@click.version_option(version="0.1.0", prog_name="clixaw")
@click.pass_context
@click.argument("query", nargs=-1, required=False)
@click.option(
    "--execute",
    "-e",
    is_flag=True,
    help="Execute the translated command instead of just printing it",
)
@click.option(
    "--api-url",
    default=None,
    envvar="XAW_API_URL",
    help="API URL (defaults to XAW_API_URL env var, config file, or https://cmd.xaw.me)",
)
@click.option(
    "--provider",
    default=None,
    envvar="XAW_PROVIDER",
    help="Provider name (e.g., openai, gemini). Overrides config file and env var.",
)
@click.option(
    "--api-key",
    default=None,
    envvar="XAW_API_KEY",
    help="API key for custom provider. Overrides config file and env var.",
)
@click.option(
    "--model",
    default=None,
    envvar="XAW_MODEL",
    help="Model override (e.g., gemini-pro, gpt-4). Overrides config file and env var.",
)
@click.option(
    "--no-confirm",
    is_flag=True,
    help="Skip confirmation for dangerous commands (use with caution)",
)
@click.option(
    "--copy",
    "-c",
    is_flag=True,
    help="Copy the translated command to clipboard",
)
@click.option(
    "--no-cache",
    is_flag=True,
    help="Disable cache for this request",
)
def cli(
    ctx: click.Context,
    query: tuple,
    execute: bool,
    api_url: Optional[str],
    provider: Optional[str],
    api_key: Optional[str],
    model: Optional[str],
    no_confirm: bool,
    copy: bool,
    no_cache: bool,
) -> None:
    """Translate natural language queries to shell commands using cmd.xaw.me API."""
    # If a subcommand was invoked, don't process the main command
    if ctx.invoked_subcommand is not None:
        return
    
    # If no query provided, show help
    if not query:
        click.echo(ctx.get_help())
        ctx.exit()
    
    # Process the main command
    main(
        query=query,
        execute=execute,
        api_url=api_url,
        provider=provider,
        api_key=api_key,
        model=model,
        no_confirm=no_confirm,
        copy=copy,
        no_cache=no_cache,
    )


def main(
    query: tuple,
    execute: bool,
    api_url: Optional[str],
    provider: Optional[str],
    api_key: Optional[str],
    model: Optional[str],
    no_confirm: bool,
    copy: bool,
    no_cache: bool,
) -> None:
    """
    Translate natural language queries to shell commands using cmd.xaw.me API.
    
    QUERY: Natural language query describing the desired command.
    
    Examples:
    
        xaw show me big files
    
        xaw "git push new branch"
    
        xaw --execute list files in current directory
    """
    # Join all query parts into a single string
    query_str = " ".join(query)
    
    if not query_str.strip():
        click.echo(click.style("Error: Query cannot be empty", fg="red"), err=True)
        sys.exit(1)
    
    # Load configuration from config file
    config_provider = config.get_provider_config()
    
    # Priority: CLI flags > Environment variables > Config file > Defaults
    # For provider, api_key, model: CLI > Env > Config
    final_provider = provider or os.getenv("XAW_PROVIDER") or config_provider.get("provider")
    final_api_key = api_key or os.getenv("XAW_API_KEY") or config_provider.get("api_key")
    final_model = model or os.getenv("XAW_MODEL") or config_provider.get("model")
    
    # For api_url: CLI > Env > Config > Default
    final_api_url = api_url or os.getenv("XAW_API_URL") or config_provider.get("api_url")
    
    try:
        # Call API to translate query
        command = api.translate_query(
            query_str,
            api_url=final_api_url,
            provider=final_provider,
            api_key=final_api_key,
            model=final_model,
            use_cache=not no_cache,
        )
        
        if copy:
            # Copy to clipboard
            try:
                pyperclip.copy(command)
                click.echo(click.style("✓ Command copied to clipboard", fg="green"))
            except Exception as e:
                click.echo(
                    click.style(f"Warning: Could not copy to clipboard: {e}", fg="yellow"),
                    err=True,
                )
        
        if execute:
            # Execute the command
            exit_code = execute_command(command, confirm=not no_confirm)
            # Log to history with execution status
            history.add_to_history(query_str, command, executed=True, exit_code=exit_code)
            sys.exit(exit_code)
        else:
            # Just print the command
            click.echo(command)
            # Log to history (not executed)
            history.add_to_history(query_str, command, executed=False)
    
    except requests.exceptions.ConnectionError:
        click.echo(
            click.style(
                "Error: Could not connect to API. Check your internet connection and API URL.",
                fg="red",
            ),
            err=True,
        )
        sys.exit(1)
    
    except requests.exceptions.Timeout:
        click.echo(
            click.style("Error: API request timed out. Please try again.", fg="red"),
            err=True,
        )
        sys.exit(1)
    
    except requests.exceptions.HTTPError as e:
        click.echo(
            click.style(f"Error: API returned error {e.response.status_code}", fg="red"),
            err=True,
        )
        sys.exit(1)
    
    except ValueError as e:
        click.echo(
            click.style(f"Error: {e}", fg="red"),
            err=True,
        )
        sys.exit(1)
    
    except Exception as e:
        click.echo(
            click.style(f"Unexpected error: {e}", fg="red"),
            err=True,
        )
        sys.exit(1)


@cli.command("history")
@click.option(
    "--limit",
    "-n",
    type=int,
    default=20,
    help="Number of history entries to show (default: 20)",
)
@click.option(
    "--all",
    "-a",
    is_flag=True,
    help="Show all history entries",
)
def show_history(limit: int, all: bool) -> None:
    """Show command history."""
    entries = history.get_history(limit=None if all else limit)
    
    if not entries:
        click.echo("No command history found.")
        return
    
    for idx, entry in enumerate(entries):
        timestamp_str = entry.get("timestamp", "")
        try:
            dt = datetime.fromisoformat(timestamp_str)
            timestamp_str = dt.strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError):
            pass
        
        query = entry.get("query", "")
        command = entry.get("command", "")
        executed = entry.get("executed", False)
        exit_code = entry.get("exit_code")
        
        # Format output
        status = ""
        if executed:
            if exit_code == 0:
                status = click.style(" ✓", fg="green")
            else:
                status = click.style(f" ✗ (exit {exit_code})", fg="red")
        else:
            status = click.style(" (not executed)", fg="yellow")
        
        click.echo(f"\n[{idx}] {timestamp_str}{status}")
        click.echo(f"  Query: {query}")
        click.echo(f"  Command: {command}")


@cli.command("repeat")
@click.argument("index", type=int, required=True)
@click.option(
    "--execute",
    "-e",
    is_flag=True,
    help="Execute the command instead of just printing it",
)
@click.option(
    "--no-confirm",
    is_flag=True,
    help="Skip confirmation for dangerous commands (use with caution)",
)
def repeat_command(index: int, execute: bool, no_confirm: bool) -> None:
    """Repeat a command from history by index."""
    entry = history.get_history_entry(index)
    
    if entry is None:
        click.echo(
            click.style(f"Error: No history entry found at index {index}", fg="red"),
            err=True,
        )
        sys.exit(1)
    
    command = entry.get("command", "")
    query = entry.get("query", "")
    
    if not command:
        click.echo(
            click.style("Error: History entry has no command", fg="red"),
            err=True,
        )
        sys.exit(1)
    
    click.echo(click.style(f"Repeating: {query}", fg="cyan"))
    click.echo(f"Command: {command}")
    
    if execute:
        exit_code = execute_command(command, confirm=not no_confirm)
        # Log the repeat to history
        history.add_to_history(
            f"[repeat] {query}",
            command,
            executed=True,
            exit_code=exit_code,
        )
        sys.exit(exit_code)
    else:
        click.echo(command)


@cli.command("clear-history")
@click.confirmation_option(
    prompt="Are you sure you want to clear all command history?",
)
def clear_history_cmd() -> None:
    """Clear all command history."""
    history.clear_history()
    click.echo(click.style("✓ Command history cleared", fg="green"))


@cli.command("clear-cache")
@click.confirmation_option(
    prompt="Are you sure you want to clear all cached API responses?",
)
def clear_cache_cmd() -> None:
    """Clear all cached API responses."""
    cache.clear_cache()
    click.echo(click.style("✓ Cache cleared", fg="green"))


@cli.command("cache-stats")
def cache_stats_cmd() -> None:
    """Show cache statistics."""
    stats = cache.get_cache_stats()
    
    click.echo("Cache Statistics:")
    click.echo(f"  Size: {stats['size']} entries")
    
    if stats["oldest_entry"]:
        try:
            dt = datetime.fromisoformat(stats["oldest_entry"])
            click.echo(f"  Oldest entry: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
        except (ValueError, TypeError):
            click.echo(f"  Oldest entry: {stats['oldest_entry']}")
    
    if stats["newest_entry"]:
        try:
            dt = datetime.fromisoformat(stats["newest_entry"])
            click.echo(f"  Newest entry: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
        except (ValueError, TypeError):
            click.echo(f"  Newest entry: {stats['newest_entry']}")
    
    if stats["size"] == 0:
        click.echo(click.style("  Cache is empty", fg="yellow"))


if __name__ == "__main__":
    cli()

