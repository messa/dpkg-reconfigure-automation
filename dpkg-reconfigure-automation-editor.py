#!/usr/bin/env python3
"""
dpkg-reconfigure-automation-editor

A script to use as EDITOR for `dpkg-reconfigure -f editor` to automate
Debian package configuration.

Supported packages:
- tzdata: sets timezone to UTC
- locales: sets locale to en_US.UTF-8
"""

import sys
import re


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
        match = re.match(r'^(Value:\s*)(.*)$', line)
        if match and result and 'tzdata/Areas' in result[-1]:
            result.append(f'{match.group(1)}Etc')
            continue

        # Set Zone to "UTC"
        if result and 'tzdata/Zones' in ''.join(result[-3:]):
            if match:
                result.append(f'{match.group(1)}UTC')
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
        match = re.match(r'^(Value:\s*)(.*)$', line)
        if match:
            if in_locales_to_generate:
                result.append(f'{match.group(1)}en_US.UTF-8 UTF-8')
                continue
            elif in_default_locale:
                result.append(f'{match.group(1)}en_US.UTF-8')
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


def main():
    if len(sys.argv) < 2:
        print("Usage: dpkg-reconfigure-automation-editor <file>", file=sys.stderr)
        sys.exit(1)

    filepath = sys.argv[1]

    # Read the file
    with open(filepath, 'r') as f:
        content = f.read()

    # Process and write back
    processed = detect_and_process(content)

    with open(filepath, 'w') as f:
        f.write(processed)


if __name__ == '__main__':
    main()
