#!/usr/bin/env python3
"""
dpkg-reconfigure-automation-editor

A script to use as EDITOR for `dpkg-reconfigure -f editor` to automate
Debian package configuration.

Supported packages:
- tzdata: sets timezone to UTC
- locales: sets locale to en_US.UTF-8
"""

from argparse import ArgumentParser
from pathlib import Path
from re import match
from sys import exit, stderr

# Mapping of known configuration keys to their desired values
# Keys starting with ~ are treated as regex patterns
CONFIG_VALUES = {
    "tzdata/Areas": "Etc",
    "~tzdata/Zones/.+": "UTC",
    "locales/locales_to_be_generated": "en_US.UTF-8 UTF-8",
    "locales/default_environment_locale": "en_US.UTF-8",
}


def parse_line(line: str) -> tuple[str, str] | None:
    """Parse a configuration line and return (key, value) or None if not a config line."""
    line = line.strip()
    if not line or line.startswith("#"):
        return None

    if "=" not in line:
        return None

    key, value = line.split("=", 1)
    # Remove quotes from value
    if value.startswith('"') and value.endswith('"'):
        value = value[1:-1]
    return key, value


def find_config_value(key: str) -> str | None:
    """Find the configured value for a key, supporting regex patterns."""
    # First try exact match
    if key in CONFIG_VALUES:
        return CONFIG_VALUES[key]

    # Then try regex patterns (keys starting with ~)
    for pattern, value in CONFIG_VALUES.items():
        if pattern.startswith("~"):
            if match(pattern[1:] + "$", key):
                return value

    return None


def process_content(content: str) -> tuple[str, list[str]]:
    """
    Process the content and return (processed_content, unknown_keys).

    Only processes non-empty, non-comment lines.
    Returns list of unknown keys that were encountered.
    """
    lines = content.splitlines()
    result_lines = []
    unknown_keys = []

    for line in lines:
        parsed = parse_line(line)
        if parsed is None:
            # Empty line or comment - keep as-is
            result_lines.append(line)
            continue

        key, _old_value = parsed
        new_value = find_config_value(key)

        if new_value is None:
            unknown_keys.append(key)
            result_lines.append(line)
        else:
            result_lines.append(f'{key}="{new_value}"')

    result = "\n".join(result_lines)
    if content.endswith("\n"):
        result += "\n"
    return result, unknown_keys


def main(args=None):
    parser = ArgumentParser(
        description='Automate dpkg-reconfigure by modifying debconf editor files'
    )
    parser.add_argument('file', help='Path to the debconf editor file')
    parsed = parser.parse_args(args)

    filepath = Path(parsed.file)
    content = filepath.read_text()
    processed, unknown_keys = process_content(content)

    if unknown_keys:
        for key in unknown_keys:
            print(f"Error: Unknown configuration key: {key}", file=stderr)
        exit(1)

    filepath.write_text(processed)


if __name__ == '__main__':
    main()
