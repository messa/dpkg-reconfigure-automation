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
from datetime import datetime, timezone
from logging import DEBUG, ERROR, INFO, Formatter, StreamHandler, getLogger
from os import environ, getpid
from pathlib import Path
from socket import getfqdn
from sys import exit, stderr
from tempfile import gettempdir

# Also update version in pyproject.toml
__version__ = "0.2.0"

logger = getLogger(__name__)

log_format = "%(asctime)s [%(process)d] %(name)-40s %(levelname)5s: %(message)s"


def setup_logging(verbosity):
    """Setup logging to stderr."""
    getLogger("").setLevel(DEBUG)
    h = StreamHandler()
    h.setFormatter(Formatter(log_format))
    if not verbosity:
        h.setLevel(ERROR)
    elif verbosity == 1:
        h.setLevel(INFO)
    else:
        h.setLevel(DEBUG)
    getLogger("").addHandler(h)


class ConfigValues:
    """Configuration values with exact keys."""

    def __init__(self, content: str | None = None):
        # Do you need to add your own configuration options?
        # Use CLI arguments: script.py key=value key2=value2 file.txt
        #
        # Want to add defaults here? Open a PR or GitHub Issue!

        self.exact = {
            "tzdata/Areas": "None of the above" if (content and "None of the above" in content) else "Etc",
            "tzdata/Zones/Etc": "UTC",
            "locales/locales_to_be_generated": lambda: ", ".join(sorted(self.get_locales())),
            "locales/default_environment_locale": "en_US.UTF-8",
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

    def add_override(self, key: str, value: str) -> None:
        """Add an override value that takes precedence over defaults."""
        self.exact[key] = value

    def get(self, key: str) -> str | None:
        """Find the configured value for a key."""
        result_value = self.exact.get(key)

        if callable(result_value):
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


def process_content(content: str, config: ConfigValues | None = None) -> tuple[str, list[str], list[str]]:
    """
    Process the content and return (processed_content, unknown_keys, unknown_values).

    Only processes non-empty, non-comment lines.
    Returns list of unknown keys that were encountered and list of values
    that were not present in the content (usually in Choices comment).

    If config is provided, it will be used instead of creating a new ConfigValues.
    """
    if config is None:
        config = ConfigValues(content=content)
    lines = content.splitlines(True)
    result_lines = []
    unknown_keys = []
    unknown_values = []

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
            logger.error("Unknown configuration key: %r", stripped)
            unknown_keys.append(key)
            result_lines.append(line)
        else:
            if new_value not in content:
                # Usually the content contains a list of all permitted values.
                # The new_value seems to not be amongst them.
                logger.warning(
                    "Updating %r to value %r, but content does not contain string %r", stripped, new_value, new_value
                )
                unknown_values.append(new_value)
            else:
                logger.debug("Updating %r to value %r", stripped, new_value)
            result_lines.append(f'{key}="{new_value}"' + ending)

    return "".join(result_lines), unknown_keys, unknown_values


def generate_debug_prefix():
    """Generate debug file prefix with timestamp and PID."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return Path(gettempdir()) / f"dpkg_reconfigure_automation_editor.{ts}.{getpid()}"


def main(args=None):
    parser = ArgumentParser(description="Automate dpkg-reconfigure by modifying debconf editor files")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase verbosity (can be repeated: -v for INFO, -vv for DEBUG)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Write editor content to /tmp before and after processing",
    )
    parser.add_argument(
        "overrides_and_file",
        nargs="+",
        metavar="[key=value ...] file",
        help="Optional key=value overrides followed by the path to the debconf editor file",
    )
    parsed = parser.parse_args(args)

    setup_logging(parsed.verbose)

    # Last argument is the file, the rest are overrides
    [*overrides, filepath] = parsed.overrides_and_file
    filepath = Path(filepath)

    logger.info("Processing file: %s", filepath)
    logger.debug("Overrides: %s", overrides)

    content = filepath.read_text()

    config = ConfigValues(content=content)
    for override in overrides:
        if "=" not in override:
            print(f"Error: Invalid override format: {override!r} (expected key=value)", file=stderr)
            exit(1)
        key, value = override.split("=", 1)
        logger.debug("Adding override: %s = %s", key, value)
        config.add_override(key, value)

    # Write debug "before" file
    debug_prefix = None
    if parsed.debug:
        debug_prefix = generate_debug_prefix()
        before_path = Path(f"{debug_prefix}.before")
        before_path.write_text(content)
        logger.info("Wrote debug file: %s", before_path)

    processed, unknown_keys, unknown_values = process_content(content, config=config)

    if unknown_keys:
        print("ERROR: Unknown configuration key(s):", ", ".join(unknown_keys), file=stderr)
    if unknown_values:
        print("ERROR: Unknown values (they are not present in the content):", ", ".join(unknown_values), file=stderr)
    if unknown_keys or unknown_values:
        exit(1)

    filepath.write_text(processed)
    logger.info("File processed successfully")

    # Write debug "after" file
    if parsed.debug and debug_prefix:
        after_path = Path(f"{debug_prefix}.after")
        after_path.write_text(processed)
        logger.info("Wrote debug file: %s", after_path)


if __name__ == "__main__":
    main()
