#!/usr/bin/env python3
"""Tests for the editor script (main function)."""

from pathlib import Path
from tempfile import NamedTemporaryFile
from textwrap import dedent
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
import dpkg_reconfigure_automation_editor as editor


def test_main_processes_file_in_place():
    content = dedent("""\
        # Locales to be generated:
        locales/locales_to_be_generated=""
        """)
    with NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(content)
        filepath = Path(f.name)

    try:
        editor.main([str(filepath)])
        result = filepath.read_text()
        assert 'locales/locales_to_be_generated="en_US.UTF-8 UTF-8"' in result
    finally:
        filepath.unlink()


def test_main_missing_argument_exits():
    with pytest.raises(SystemExit) as exc_info:
        editor.main([])
    assert exc_info.value.code == 2  # argparse exits with 2 for missing arguments


def test_main_exits_with_1_for_unknown_key():
    content = 'unknown-package/option="value"'
    with NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(content)
        filepath = Path(f.name)

    try:
        with pytest.raises(SystemExit) as exc_info:
            editor.main([str(filepath)])
        assert exc_info.value.code == 1
    finally:
        filepath.unlink()


def test_main_does_not_modify_file_on_unknown_key():
    content = 'unknown-package/option="value"'
    with NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(content)
        filepath = Path(f.name)

    try:
        with pytest.raises(SystemExit):
            editor.main([str(filepath)])
        # File should remain unchanged
        result = filepath.read_text()
        assert result == content
    finally:
        filepath.unlink()


def test_main_processes_tzdata():
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
        editor.main([str(filepath)])
        result = filepath.read_text()
        assert 'tzdata/Areas="Etc"' in result
        assert 'tzdata/Zones/Europe="UTC"' in result
    finally:
        filepath.unlink()
