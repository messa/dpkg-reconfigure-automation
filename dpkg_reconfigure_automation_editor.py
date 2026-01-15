#!/usr/bin/env python3
"""
dpkg-reconfigure-automation-editor

A script to use as EDITOR for `dpkg-reconfigure -f editor` to automate
Debian package configuration.

Supported packages:
- tzdata: sets timezone to UTC
- locales: sets locale to en_US.UTF-8 (also cs_CZ.UTF-8 on servers with .cz FQDN)
"""

from argparse import ArgumentParser
from pathlib import Path
from re import compile, Pattern
from socket import getfqdn
from sys import exit, stderr


class ConfigValues:
    """Configuration values with exact keys and regex patterns."""

    def __init__(self):
        self.exact = {
            "tzdata/Areas": "None of the above",
            "tzdata/Zones/Etc": "UTC",
            "locales/locales_to_be_generated": ", ".join(self.get_locales()),
            "locales/default_environment_locale": "en_US.UTF-8",
        }
        self.patterns = {
            compile(r"tzdata/Zones/.+"): "UTC",
        }

    @staticmethod
    def get_locales(fqdn: str | None = None):
        """Yield locales to generate, including Czech on .cz servers."""
        if fqdn is None:
            fqdn = getfqdn()
        if fqdn.endswith(".cz"):
            yield "cs_CZ.UTF-8 UTF-8"
        yield "en_US.UTF-8 UTF-8"

    def get(self, key: str) -> str | None:
        """Find the configured value for a key, supporting regex patterns."""
        if key in self.exact:
            return self.exact[key]

        for pattern, value in self.patterns.items():
            if pattern.fullmatch(key):
                return value

        return None


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


def process_content(content: str) -> tuple[str, list[str]]:
    """
    Process the content and return (processed_content, unknown_keys).

    Only processes non-empty, non-comment lines.
    Returns list of unknown keys that were encountered.
    """
    config = ConfigValues()
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
        new_value = config.get(key)

        if new_value is None:
            unknown_keys.append(key)
            result_lines.append(line)
        else:
            if new_value not in content:
                # Usually the content contains a list of all permitted values.
                # Tne new_value seems to not be amongst them.
                raise Exception(f'Content does not contain string {new_value!r}')
            result_lines.append(f'{key}="{new_value}"')

    result = "\n".join(line + "\n" for line in result_lines)
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
