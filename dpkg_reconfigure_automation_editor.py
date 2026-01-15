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
from os import environ
from pathlib import Path
from re import compile
from socket import getfqdn
from sys import exit, stderr

# Also update version in pyproject.toml
__version__ = "0.1.0"


class MissingChoiceError(Exception):
    """Raised when the configured value is not present in the available choices."""

    pass


class ConfigValues:
    """Configuration values with exact keys and regex patterns."""

    def __init__(self):
        # Do you need to add your own configuration options here?
        #
        # - Copy this file and add it :)
        # - Open a PR if you think it would be great to share it
        # - Or describe your use case in an Github Issue and we can think
        #   about how to add options dynamically in some way (env vars etc.)

        self.exact = {
            "tzdata/Areas": "None of the above",
            "tzdata/Zones/Etc": "UTC",
            "locales/locales_to_be_generated": lambda: ", ".join(sorted(self.get_locales())),
            "locales/default_environment_locale": "en_US.UTF-8",
        }
        self.patterns = {
            compile(r"tzdata/Zones/.+"): "UTC",
        }

    @staticmethod
    def get_locales(fqdn: str | None = None):
        """Yield locales to generate, including Czech on .cz servers."""
        yield "en_US.UTF-8 UTF-8"
        if environ.get("EXTRA_LOCALES"):
            for s in environ["EXTRA_LOCALES"].split(","):
                yield s.strip()
        elif (fqdn or getfqdn()).endswith(".cz"):
            yield "cs_CZ.UTF-8 UTF-8"

    def get(self, key: str) -> str | None:
        """Find the configured value for a key, supporting regex patterns."""
        result_value = None

        if key in self.exact:
            result_value = self.exact[key]

        for pattern, value in self.patterns.items():
            if pattern.fullmatch(key):
                result_value = value

        if callable(result_value):
            # in case it is a lambda
            result_value = result_value()

        return result_value


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


def process_content(content: str, check: bool = True) -> tuple[str, list[str]]:
    """
    Process the content and return (processed_content, unknown_keys).

    Only processes non-empty, non-comment lines.
    Returns list of unknown keys that were encountered.

    If check=True (default), validates that new values are present in content
    (usually listed in the Choices comment).
    """
    config = ConfigValues()
    lines = content.splitlines(True)
    result_lines = []
    unknown_keys = []

    for line in lines:
        # Preserve line ending (e.g. '\n' or '\r\n')
        stripped = line.rstrip("\r\n")
        ending = line[len(stripped) :]

        parsed = parse_line(stripped)
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
            if check and new_value not in content:
                # Usually the content contains a list of all permitted values.
                # The new_value seems to not be amongst them.
                raise MissingChoiceError(f"Content does not contain string {new_value!r}")
            result_lines.append(f'{key}="{new_value}"' + ending)

    return "".join(result_lines), unknown_keys


def main(args=None):
    parser = ArgumentParser(
        description="Automate dpkg-reconfigure by modifying debconf editor files"
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("file", help="Path to the debconf editor file")
    parsed = parser.parse_args(args)

    filepath = Path(parsed.file)
    content = filepath.read_text()
    processed, unknown_keys = process_content(content)

    if unknown_keys:
        for key in unknown_keys:
            print(f"Error: Unknown configuration key: {key}", file=stderr)
        exit(1)

    filepath.write_text(processed)


if __name__ == "__main__":
    main()
