#!/usr/bin/env python3
"""Tests for processing functions."""

from pathlib import Path
from textwrap import dedent
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
import dpkg_reconfigure_automation_editor as editor


# Tests for tzdata processing

def test_tzdata_sets_area_to_etc():
    content = dedent("""\
        # Geographic area:
        tzdata/Areas="Europe"
        """)
    result = editor.process_tzdata(content)
    assert 'tzdata/Areas="Etc"' in result


def test_tzdata_sets_zone_to_utc():
    content = dedent("""\
        # Time zone:
        tzdata/Zones/Etc="GMT"
        """)
    result = editor.process_tzdata(content)
    assert 'tzdata/Zones/Etc="UTC"' in result


def test_tzdata_sets_any_zone_to_utc():
    content = dedent("""\
        # Time zone:
        tzdata/Zones/Europe="Prague"
        """)
    result = editor.process_tzdata(content)
    assert 'tzdata/Zones/Europe="UTC"' in result


def test_tzdata_full_config():
    content = dedent("""\
        # You are using the editor-based debconf frontend.
        ###############################################################################

        # Geographic area:
        tzdata/Areas="Europe"


        ###############################################################################
        # Instructions...
        """)
    result = editor.process_tzdata(content)
    assert 'tzdata/Areas="Etc"' in result
    assert "# You are using" in result
    assert "# Instructions" in result


# Tests for locales processing

def test_locales_sets_locales_to_generate():
    content = dedent("""\
        # Locales to be generated:
        locales/locales_to_be_generated=""
        """)
    result = editor.process_locales(content)
    assert 'locales/locales_to_be_generated="en_US.UTF-8 UTF-8"' in result


def test_locales_sets_default_locale():
    content = dedent("""\
        # Default locale:
        locales/default_environment_locale="cs_CZ.UTF-8"
        """)
    result = editor.process_locales(content)
    assert 'locales/default_environment_locale="en_US.UTF-8"' in result


def test_locales_full_config():
    content = dedent("""\
        # You are using the editor-based debconf frontend.
        ###############################################################################

        # Locales to be generated:
        locales/locales_to_be_generated="cs_CZ.UTF-8 UTF-8"


        ###############################################################################
        # Instructions...
        """)
    result = editor.process_locales(content)
    assert 'locales/locales_to_be_generated="en_US.UTF-8 UTF-8"' in result
    assert "# You are using" in result


# Tests for package detection

def test_detect_tzdata_by_areas():
    content = 'tzdata/Areas="Europe"\n'
    result = editor.detect_and_process(content)
    assert 'tzdata/Areas="Etc"' in result


def test_detect_tzdata_by_zones():
    content = 'tzdata/Zones/Europe="Prague"\n'
    result = editor.detect_and_process(content)
    assert 'tzdata/Zones/Europe="UTC"' in result


def test_detect_locales_by_locales_to_be_generated():
    content = 'locales/locales_to_be_generated=""\n'
    result = editor.detect_and_process(content)
    assert 'locales/locales_to_be_generated="en_US.UTF-8 UTF-8"' in result


def test_detect_locales_by_default_environment_locale():
    content = 'locales/default_environment_locale="cs_CZ.UTF-8"\n'
    result = editor.detect_and_process(content)
    assert 'locales/default_environment_locale="en_US.UTF-8"' in result


def test_unknown_package_unchanged():
    content = 'some-other-package/option="something"\n'
    result = editor.detect_and_process(content)
    assert result == content


# Edge case tests

def test_empty_content():
    result = editor.detect_and_process("")
    assert result == ""


def test_preserves_comments():
    content = dedent("""\
        # Comment line
        # Another comment
        locales/locales_to_be_generated=""
        # Trailing comment
        """)
    result = editor.process_locales(content)
    assert "# Comment line" in result
    assert "# Another comment" in result
    assert "# Trailing comment" in result


def test_handles_empty_value():
    content = 'locales/locales_to_be_generated=""\n'
    result = editor.process_locales(content)
    assert 'locales/locales_to_be_generated="en_US.UTF-8 UTF-8"' in result


def test_handles_existing_value():
    content = 'locales/locales_to_be_generated="cs_CZ.UTF-8 UTF-8, de_DE.UTF-8 UTF-8"\n'
    result = editor.process_locales(content)
    assert 'locales/locales_to_be_generated="en_US.UTF-8 UTF-8"' in result
