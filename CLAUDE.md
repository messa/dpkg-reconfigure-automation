# Claude Code preferences

## Python code style

- Use `from A import B` style imports instead of `import A`
- Use `argparse` for command-line argument parsing
- Use `pathlib.Path` for file operations

## Running tests

Run tests using uv:

```
uv run pytest tests/
```
