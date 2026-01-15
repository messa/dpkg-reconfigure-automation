#!/usr/bin/env python3
"""Tests for the editor script (running as subprocess)."""

from pathlib import Path
from subprocess import run
from sys import executable
from tempfile import NamedTemporaryFile
from textwrap import dedent

SCRIPT_PATH = Path(__file__).parent.parent / 'dpkg_reconfigure_automation_editor.py'


def test_script_processes_file_in_place():
    content = dedent("""\
        # Locales to be generated:
        locales/locales_to_be_generated=""
        """)
    with NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(content)
        filepath = Path(f.name)

    try:
        result = run([executable, str(SCRIPT_PATH), str(filepath)], capture_output=True)
        assert result.returncode == 0
        assert result.stdout == b''
        assert result.stderr == b''
        file_content = filepath.read_text()
        assert 'locales/locales_to_be_generated="en_US.UTF-8 UTF-8"' in file_content
    finally:
        filepath.unlink()


def test_script_missing_argument_exits():
    result = run([executable, str(SCRIPT_PATH)], capture_output=True)
    assert result.returncode == 2  # argparse exits with 2 for missing arguments


def test_script_exits_with_1_for_unknown_key():
    content = 'unknown-package/option="value"'
    with NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(content)
        filepath = Path(f.name)

    try:
        result = run([executable, str(SCRIPT_PATH), str(filepath)], capture_output=True)
        assert result.returncode == 1
        assert b'Error: Unknown configuration key: unknown-package/option' in result.stderr
    finally:
        filepath.unlink()


def test_script_does_not_modify_file_on_unknown_key():
    content = 'unknown-package/option="value"'
    with NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(content)
        filepath = Path(f.name)

    try:
        run([executable, str(SCRIPT_PATH), str(filepath)], capture_output=True)
        # File should remain unchanged
        file_content = filepath.read_text()
        assert file_content == content
    finally:
        filepath.unlink()


def test_script_processes_tzdata():
    content = dedent("""\
        # Geographic area:
        tzdata/Areas="Europe"
        # Time zone:
        tzdata/Zones/Europe="Prague"
        """)
    with NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(content)
        filepath = Path(f.name)

    try:
        result = run([executable, str(SCRIPT_PATH), str(filepath)], capture_output=True)
        assert result.returncode == 0
        file_content = filepath.read_text()
        assert 'tzdata/Areas="Etc"' in file_content
        assert 'tzdata/Zones/Europe="UTC"' in file_content
    finally:
        filepath.unlink()
