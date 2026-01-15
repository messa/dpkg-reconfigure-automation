#!/usr/bin/env python3
"""Tests for dpkg-reconfigure-automation-editor.py"""

from importlib import import_module
from pathlib import Path
from tempfile import NamedTemporaryFile
from textwrap import dedent
import sys

import pytest

# Import the module under test
sys.path.insert(0, str(Path(__file__).parent.parent))
editor = import_module('dpkg-reconfigure-automation-editor')


# Tests for tzdata processing

def test_tzdata_sets_area_to_etc():
    content = dedent("""\
        Name: tzdata/Areas
        Value: Europe
        """)
    result = editor.process_tzdata(content)
    assert "Value: Etc" in result


def test_tzdata_sets_zone_to_utc():
    content = dedent("""\
        Name: tzdata/Zones/Etc
        Value: GMT
        """)
    result = editor.process_tzdata(content)
    assert "Value: UTC" in result


def test_tzdata_full_config():
    content = dedent("""\
        Name: tzdata/Areas
        Template: tzdata/Areas
        Value: Europe
        Owners: tzdata

        Name: tzdata/Zones/Europe
        Template: tzdata/Zones/Europe
        Value: Prague
        Owners: tzdata
        """)
    result = editor.process_tzdata(content)
    lines = result.split('\n')

    # Find the value after tzdata/Areas
    found_etc = False
    for i, line in enumerate(lines):
        if 'tzdata/Areas' in line and 'Name:' in line:
            for j in range(i + 1, min(i + 5, len(lines))):
                if lines[j].startswith('Value:'):
                    if 'Etc' in lines[j]:
                        found_etc = True
                    break
    assert found_etc, "Expected 'Etc' in tzdata/Areas value"


# Tests for locales processing

def test_locales_sets_locales_to_generate():
    content = dedent("""\
        Name: locales/locales_to_be_generated
        Value: cs_CZ.UTF-8 UTF-8
        """)
    result = editor.process_locales(content)
    assert "Value: en_US.UTF-8 UTF-8" in result


def test_locales_sets_default_locale():
    content = dedent("""\
        Name: locales/default_environment_locale
        Value: cs_CZ.UTF-8
        """)
    result = editor.process_locales(content)
    assert "Value: en_US.UTF-8" in result
    # Should not have "UTF-8 UTF-8" for default locale
    assert "en_US.UTF-8 UTF-8" not in result


def test_locales_full_config():
    content = dedent("""\
        Name: locales/locales_to_be_generated
        Template: locales/locales_to_be_generated
        Value: cs_CZ.UTF-8 UTF-8, de_DE.UTF-8 UTF-8
        Owners: locales

        Name: locales/default_environment_locale
        Template: locales/default_environment_locale
        Value: cs_CZ.UTF-8
        Owners: locales
        """)
    result = editor.process_locales(content)

    assert "en_US.UTF-8 UTF-8" in result

    # Find the default_environment_locale value
    lines = result.split('\n')
    in_default = False
    for line in lines:
        if 'locales/default_environment_locale' in line:
            in_default = True
        elif line.startswith('Name:'):
            in_default = False
        elif in_default and line.startswith('Value:'):
            assert line == "Value: en_US.UTF-8"


# Tests for package detection

def test_detect_tzdata_by_areas():
    content = "Name: tzdata/Areas\nValue: Europe\n"
    result = editor.detect_and_process(content)
    assert "Value: Etc" in result


def test_detect_tzdata_by_zones():
    content = "Name: tzdata/Zones/Europe\nValue: Prague\n"
    result = editor.detect_and_process(content)
    assert "Value: UTC" in result


def test_detect_locales_by_locales_to_be_generated():
    content = "Name: locales/locales_to_be_generated\nValue: cs_CZ.UTF-8 UTF-8\n"
    result = editor.detect_and_process(content)
    assert "en_US.UTF-8 UTF-8" in result


def test_detect_locales_by_default_environment_locale():
    content = "Name: locales/default_environment_locale\nValue: cs_CZ.UTF-8\n"
    result = editor.detect_and_process(content)
    assert "en_US.UTF-8" in result


def test_unknown_package_unchanged():
    content = "Name: some-other-package/option\nValue: something\n"
    result = editor.detect_and_process(content)
    assert result == content


# Tests for main function

def test_main_processes_file_in_place():
    content = dedent("""\
        Name: locales/locales_to_be_generated
        Value: cs_CZ.UTF-8 UTF-8
        """)
    with NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(content)
        filepath = Path(f.name)

    try:
        editor.main([str(filepath)])
        result = filepath.read_text()
        assert "en_US.UTF-8 UTF-8" in result
    finally:
        filepath.unlink()


def test_main_missing_argument_exits():
    with pytest.raises(SystemExit) as exc_info:
        editor.main([])
    assert exc_info.value.code == 2  # argparse exits with 2 for missing arguments


# Edge case tests

def test_empty_content():
    result = editor.detect_and_process("")
    assert result == ""


def test_preserves_other_lines():
    content = dedent("""\
        # Comment line
        Name: locales/locales_to_be_generated
        Template: locales/locales_to_be_generated
        Value: cs_CZ.UTF-8 UTF-8
        Owners: locales
        # Another comment
        """)
    result = editor.process_locales(content)
    assert "# Comment line" in result
    assert "# Another comment" in result
    assert "Template: locales/locales_to_be_generated" in result
    assert "Owners: locales" in result


def test_value_with_extra_whitespace():
    content = "Name: locales/locales_to_be_generated\nValue:   cs_CZ.UTF-8 UTF-8\n"
    result = editor.process_locales(content)
    assert "Value:   en_US.UTF-8 UTF-8" in result
