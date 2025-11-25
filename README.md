# clixaw

A command-line interface tool that translates natural language queries into executable shell commands using the [cmd.xaw.me](https://cmd.xaw.me) API.

## Installation

### From PyPI (when published)

```bash
pip install clixaw
```

### From source

```bash
git clone <repository-url>
cd clixaw
pip install -e .
```

### Development mode

```bash
pip install -e ".[dev]"
```

## Usage

### Basic Usage

Translate a natural language query to a shell command:

```bash
xaw show me big files
# Output: du -ah . | sort -rh | head -n 10
```

### Quoted Queries

For multi-word queries with special characters, use quotes:

```bash
xaw "git push new branch"
# Output: git push -u origin $(git branch --show-current)
```

### Execute Commands

Use the `--execute` or `-e` flag to execute the translated command:

```bash
xaw --execute list files in current directory
# Executes: ls -la
```

### Configuration

Set a custom API URL using the `XAW_API_URL` environment variable:

```bash
export XAW_API_URL="http://localhost:8000"
xaw show files
```

Or use the `--api-url` flag:

```bash
xaw --api-url http://localhost:8000 show files
```

### Safety Features

By default, `clixaw` only prints commands without executing them. When using `--execute`:

- Dangerous commands (like `rm -rf`, `format`, etc.) require confirmation
- Use `--no-confirm` to skip confirmation (use with caution)

```bash
xaw --execute remove all files
# Warning: This command may be dangerous!
# Command: rm -rf *
# Do you want to proceed? [y/N]:
```

## Command-Line Options

```
Usage: xaw [OPTIONS] QUERY...

  Translate natural language queries to shell commands using cmd.xaw.me API.

Options:
  -e, --execute          Execute the translated command instead of just printing it
  --api-url TEXT         API URL (defaults to XAW_API_URL env var or https://cmd.xaw.me)
  --no-confirm           Skip confirmation for dangerous commands (use with caution)
  --version              Show the version and exit
  --help                 Show this message and exit
```

## Examples

```bash
# Find large files
xaw show me big files

# Git operations
xaw "git push new branch"
xaw "create a new git branch"

# File operations
xaw list all python files
xaw find files modified today

# System information
xaw show disk usage
xaw check network connections

# Execute commands
xaw --execute show current directory
xaw -e "list files sorted by size"
```

## API Details

- **Base URL**: `https://cmd.xaw.me` (configurable)
- **Endpoints**: 
  - `GET /?q={query}` (query parameter style, preferred)
  - `GET /{query}` (path-based)
- **Response**: Plain text shell command
- **Authentication**: None required

## Error Handling

The tool handles various error scenarios:

- Network connection errors
- API timeouts
- HTTP errors from the API
- Invalid or empty responses
- Command execution errors

## Development

### Project Structure

```
clixaw/
├── clixaw/
│   ├── __init__.py
│   ├── cli.py          # Main CLI entry point
│   └── api.py          # API client module
├── pyproject.toml      # Package configuration
├── README.md
└── requirements.txt
```

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black clixaw/
```

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

