# Publishing clixaw to PyPI

This guide walks you through publishing `clixaw` to the Python Package Index (PyPI).

## Prerequisites

1. **Python 3.7+** installed
2. **pip** and **build** tools installed
3. **PyPI account** (create at https://pypi.org/account/register/)
4. **TestPyPI account** (optional, for testing: https://test.pypi.org/account/register/)

## Step 1: Install Build Tools

```bash
pip install --upgrade build twine
```

## Step 2: Prepare Your Package

### Check Package Name Availability

Before publishing, verify the package name `clixaw` is available:
- Visit https://pypi.org/project/clixaw/ 
- If it exists, you'll need to choose a different name and update `pyproject.toml`

### Update Version Number

Before each release, update the version in `pyproject.toml`:
```toml
version = "0.1.0"  # Use semantic versioning: MAJOR.MINOR.PATCH
```

### Verify Package Structure

Ensure all files are in place:
```bash
# Check package structure
python -m pip install -e .
xaw --help  # Test that it works
```

## Step 3: Build Distribution Packages

Build both source distribution (sdist) and wheel:

```bash
python -m build
```

This creates:
- `dist/clixaw-0.1.0.tar.gz` (source distribution)
- `dist/clixaw-0.1.0-py3-none-any.whl` (wheel)

## Step 4: Test on TestPyPI (Recommended)

Before publishing to production PyPI, test on TestPyPI:

### Upload to TestPyPI

```bash
python -m twine upload --repository testpypi dist/*
```

You'll be prompted for:
- **Username**: Your TestPyPI username
- **Password**: Your TestPyPI password (or API token)

### Test Installation from TestPyPI

```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ clixaw
```

Test that it works:
```bash
xaw --help
```

## Step 5: Upload to Production PyPI

Once tested, upload to production PyPI:

```bash
python -m twine upload dist/*
```

You'll be prompted for:
- **Username**: Your PyPI username
- **Password**: Your PyPI password (or API token)

### Using API Tokens (Recommended)

For better security, use API tokens instead of passwords:

1. Go to https://pypi.org/manage/account/token/
2. Create a new API token (scope: "Entire account" or project-specific)
3. Use `__token__` as username and the token as password

```bash
# Example with token
python -m twine upload dist/*
# Username: __token__
# Password: pypi-xxxxxxxxxxxxx
```

## Step 6: Verify Publication

1. Visit https://pypi.org/project/clixaw/ (or your package URL)
2. Verify the package page looks correct
3. Test installation:
   ```bash
   pip install clixaw
   xaw --help
   ```

## Step 7: Update README

Update the README.md installation section to reflect that it's now on PyPI:

```markdown
## Installation

```bash
pip install clixaw
```
```

## Updating the Package

For subsequent releases:

1. **Update version** in `pyproject.toml`:
   ```toml
   version = "0.1.1"  # Increment version
   ```

2. **Update CHANGELOG** (if you maintain one)

3. **Build and upload**:
   ```bash
   python -m build
   python -m twine upload dist/*
   ```

## Troubleshooting

### "Package name already exists"
- Choose a different name or contact the existing maintainer

### "Invalid distribution"
- Ensure `pyproject.toml` is valid
- Check that all required files are included

### "Authentication failed"
- Verify your credentials
- Use API tokens instead of passwords
- Check if 2FA is enabled (may require API token)

### "File already exists"
- Increment version number
- Or use `--skip-existing` flag (not recommended)

## Best Practices

1. **Always test on TestPyPI first**
2. **Use semantic versioning** (MAJOR.MINOR.PATCH)
3. **Write clear release notes** in the description
4. **Keep README.md updated**
5. **Tag releases in git**: `git tag v0.1.0 && git push --tags`

## Quick Reference Commands

```bash
# Install build tools
pip install --upgrade build twine

# Build package
python -m build

# Upload to TestPyPI
python -m twine upload --repository testpypi dist/*

# Upload to PyPI
python -m twine upload dist/*

# Clean build artifacts (optional)
rm -rf dist/ build/ *.egg-info
```

## Additional Resources

- [PyPI Documentation](https://packaging.python.org/en/latest/guides/distributing-packages-using-setuptools/)
- [Twine Documentation](https://twine.readthedocs.io/)
- [Python Packaging Guide](https://packaging.python.org/)

