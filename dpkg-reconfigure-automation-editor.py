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


def process_tzdata(content: str) -> str:
    """Configure tzdata to use UTC timezone."""
    lines = content.split('\n')
    result = []

    for line in lines:
        # Handle Area selection (e.g., "Europe" -> "Etc" for UTC)
        if line.startswith('Name: tzdata/Areas'):
            # Find the value line (next non-comment line with "Value:")
            result.append(line)
            continue

        # Set Area to "Etc" for UTC
        m = match(r'^(Value:\s*)(.*)$', line)
        if m and result and 'tzdata/Areas' in result[-1]:
            result.append(f'{m.group(1)}Etc')
            continue

        # Set Zone to "UTC"
        if result and 'tzdata/Zones' in ''.join(result[-3:]):
            if m:
                result.append(f'{m.group(1)}UTC')
                continue

        result.append(line)

    return '\n'.join(result)


def process_locales(content: str) -> str:
    """Configure locales to use en_US.UTF-8."""
    lines = content.split('\n')
    result = []
    in_locales_to_generate = False
    in_default_locale = False

    for line in lines:
        # Track which question we're in
        if 'locales/locales_to_be_generated' in line:
            in_locales_to_generate = True
            in_default_locale = False
        elif 'locales/default_environment_locale' in line:
            in_locales_to_generate = False
            in_default_locale = True
        elif line.startswith('Name:'):
            in_locales_to_generate = False
            in_default_locale = False

        # Modify values
        m = match(r'^(Value:\s*)(.*)$', line)
        if m:
            if in_locales_to_generate:
                result.append(f'{m.group(1)}en_US.UTF-8 UTF-8')
                continue
            elif in_default_locale:
                result.append(f'{m.group(1)}en_US.UTF-8')
                continue

        result.append(line)

    return '\n'.join(result)


def detect_and_process(content: str) -> str:
    """Detect package type and process accordingly."""
    if 'tzdata/Areas' in content or 'tzdata/Zones' in content:
        return process_tzdata(content)
    elif 'locales/locales_to_be_generated' in content or 'locales/default_environment_locale' in content:
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
