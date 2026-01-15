#!/usr/bin/env python3
"""Tests for the editor script (running as subprocess)."""

from pathlib import Path
from subprocess import run
from sys import executable
from textwrap import dedent

SCRIPT_PATH = Path(__file__).parent.parent / 'dpkg_reconfigure_automation_editor.py'


def test_script_help():
    result = run([executable, str(SCRIPT_PATH), '--help'], capture_output=True)
    assert result.returncode == 0
    assert b'usage:' in result.stdout


def test_script_processes_file_in_place(tmp_path):
    content = dedent("""\
        # (Choices: en_US.UTF-8 UTF-8, cs_CZ.UTF-8 UTF-8)
        # Locales to be generated:
        locales/locales_to_be_generated=""
        """)
    filepath = tmp_path / 'config.txt'
    filepath.write_text(content)

    result = run([executable, str(SCRIPT_PATH), str(filepath)], capture_output=True)
    assert result.returncode == 0
    assert result.stdout == b''
    assert result.stderr == b''
    assert 'locales/locales_to_be_generated="en_US.UTF-8 UTF-8"' in filepath.read_text()


def test_script_missing_argument_exits():
    result = run([executable, str(SCRIPT_PATH)], capture_output=True)
    assert result.returncode == 2  # argparse exits with 2 for missing arguments


def test_script_exits_with_1_for_unknown_key(tmp_path):
    content = 'unknown-package/option="value"'
    filepath = tmp_path / 'config.txt'
    filepath.write_text(content)

    result = run([executable, str(SCRIPT_PATH), str(filepath)], capture_output=True)
    assert result.returncode == 1
    assert b'Error: Unknown configuration key: unknown-package/option' in result.stderr


def test_script_does_not_modify_file_on_unknown_key(tmp_path):
    content = 'unknown-package/option="value"'
    filepath = tmp_path / 'config.txt'
    filepath.write_text(content)

    run([executable, str(SCRIPT_PATH), str(filepath)], capture_output=True)
    # File should remain unchanged
    assert filepath.read_text() == content


def test_script_processes_tzdata(tmp_path):
    content = dedent("""\
        # (Choices: Europe, None of the above)
        # Geographic area:
        tzdata/Areas="Europe"
        # (Choices: Prague, UTC)
        # Time zone:
        tzdata/Zones/Europe="Prague"
        """)
    filepath = tmp_path / 'config.txt'
    filepath.write_text(content)

    result = run([executable, str(SCRIPT_PATH), str(filepath)], capture_output=True)
    assert result.returncode == 0
    file_content = filepath.read_text()
    assert 'tzdata/Areas="None of the above"' in file_content
    assert 'tzdata/Zones/Europe="UTC"' in file_content
