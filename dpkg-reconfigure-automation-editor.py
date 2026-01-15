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
from re import MULTILINE, sub


def process_tzdata(content: str) -> str:
    """Configure tzdata to use UTC timezone."""
    # Set Areas to Etc
    content = sub(
        r'^(tzdata/Areas=)".*"',
        r'\1"Etc"',
        content,
        flags=MULTILINE
    )
    # Set timezone to UTC (for any Zones/* question)
    content = sub(
        r'^(tzdata/Zones/[^=]+=)".*"',
        r'\1"UTC"',
        content,
        flags=MULTILINE
    )
    return content


def process_locales(content: str) -> str:
    """Configure locales to use en_US.UTF-8."""
    # Set locales to generate
    content = sub(
        r'^(locales/locales_to_be_generated=)".*"',
        r'\1"en_US.UTF-8 UTF-8"',
        content,
        flags=MULTILINE
    )
    # Set default locale
    content = sub(
        r'^(locales/default_environment_locale=)".*"',
        r'\1"en_US.UTF-8"',
        content,
        flags=MULTILINE
    )
    return content


def detect_and_process(content: str) -> str:
    """Detect package type and process accordingly."""
    if 'tzdata/Areas=' in content or 'tzdata/Zones/' in content:
        return process_tzdata(content)
    elif 'locales/locales_to_be_generated=' in content or 'locales/default_environment_locale=' in content:
        return process_locales(content)
    else:
        # Unknown package, return unchanged
        return content


def main(args=None):
    parser = ArgumentParser(
        description='Automate dpkg-reconfigure by modifying debconf editor files'
    )
    parser.add_argument('file', help='Path to the debconf editor file')
    parsed = parser.parse_args(args)

    filepath = Path(parsed.file)
    content = filepath.read_text()
    processed = detect_and_process(content)
    filepath.write_text(processed)


if __name__ == '__main__':
    main()
