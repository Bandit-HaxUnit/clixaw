"""Command-line interface for clixaw."""

import subprocess
import sys
from typing import Optional

import click
import pyperclip
import requests

from clixaw import api


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


@click.command()
@click.argument("query", nargs=-1, required=True)
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
    help="API URL (defaults to XAW_API_URL env var or https://cmd.xaw.me)",
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
@click.version_option(version="0.1.0", prog_name="clixaw")
def main(query: tuple, execute: bool, api_url: Optional[str], no_confirm: bool, copy: bool) -> None:
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
    
    try:
        # Call API to translate query
        command = api.translate_query(query_str, api_url=api_url)
        
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
            sys.exit(exit_code)
        else:
            # Just print the command
            click.echo(command)
    
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


if __name__ == "__main__":
    main()

