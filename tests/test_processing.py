#!/usr/bin/env python3
"""Tests for processing functions."""

from pathlib import Path
from textwrap import dedent
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
import dpkg_reconfigure_automation_editor as editor


# Tests for parse_line

def test_parse_line_returns_key_value():
    result = editor.parse_line('tzdata/Areas="Europe"')
    assert result == ("tzdata/Areas", "Europe")


def test_parse_line_returns_none_for_empty():
    assert editor.parse_line("") is None
    assert editor.parse_line("   ") is None


def test_parse_line_returns_none_for_comment():
    assert editor.parse_line("# Comment") is None
    assert editor.parse_line("  # Indented comment") is None


def test_parse_line_returns_none_for_separator():
    assert editor.parse_line("###############") is None


# Tests for ConfigValues

def test_config_values_exact_match():
    config = editor.ConfigValues()
    assert config.get("tzdata/Areas") == "Etc"
    assert config.get("locales/locales_to_be_generated") == "en_US.UTF-8 UTF-8"


def test_config_values_pattern_match():
    config = editor.ConfigValues()
    assert config.get("tzdata/Zones/Etc") == "UTC"
    assert config.get("tzdata/Zones/Europe") == "UTC"
    assert config.get("tzdata/Zones/America") == "UTC"


def test_config_values_unknown():
    config = editor.ConfigValues()
    assert config.get("unknown/key") is None
    assert config.get("some-package/option") is None


# Tests for tzdata processing

def test_tzdata_sets_area_to_etc():
    content = 'tzdata/Areas="Europe"'
    result, unknown = editor.process_content(content)
    assert 'tzdata/Areas="Etc"' in result
    assert unknown == []


def test_tzdata_sets_zone_to_utc():
    content = 'tzdata/Zones/Etc="GMT"'
    result, unknown = editor.process_content(content)
    assert 'tzdata/Zones/Etc="UTC"' in result
    assert unknown == []


def test_tzdata_sets_any_zone_to_utc():
    content = 'tzdata/Zones/Europe="Prague"'
    result, unknown = editor.process_content(content)
    assert 'tzdata/Zones/Europe="UTC"' in result
    assert unknown == []


def test_tzdata_full_config():
    content = dedent("""\
        # You are using the editor-based debconf frontend.
        ###############################################################################

        # Geographic area:
        tzdata/Areas="Europe"


        ###############################################################################
        # Instructions...""")
    result, unknown = editor.process_content(content)
    assert 'tzdata/Areas="Etc"' in result
    assert "# You are using" in result
    assert "# Instructions" in result
    assert unknown == []


# Tests for get_locales

def test_get_locales_returns_english_on_non_cz_server():
    locales = list(editor.ConfigValues.get_locales(fqdn="server.example.com"))
    assert locales == ["en_US.UTF-8 UTF-8"]


def test_get_locales_returns_czech_and_english_on_cz_server():
    locales = list(editor.ConfigValues.get_locales(fqdn="server.example.cz"))
    assert locales == ["cs_CZ.UTF-8 UTF-8", "en_US.UTF-8 UTF-8"]


# Tests for locales processing

def test_locales_sets_locales_to_generate():
    content = 'locales/locales_to_be_generated=""'
    result, unknown = editor.process_content(content)
    assert 'locales/locales_to_be_generated="en_US.UTF-8 UTF-8"' in result
    assert unknown == []


def test_locales_sets_default_locale():
    content = 'locales/default_environment_locale="cs_CZ.UTF-8"'
    result, unknown = editor.process_content(content)
    assert 'locales/default_environment_locale="en_US.UTF-8"' in result
    assert unknown == []


def test_locales_full_config():
    content = dedent("""\
        # You are using the editor-based debconf frontend.
        ###############################################################################

        # Locales to be generated:
        locales/locales_to_be_generated="cs_CZ.UTF-8 UTF-8"


        ###############################################################################
        # Instructions...""")
    result, unknown = editor.process_content(content)
    assert 'locales/locales_to_be_generated="en_US.UTF-8 UTF-8"' in result
    assert "# You are using" in result
    assert unknown == []


# Tests for unknown keys

def test_unknown_key_is_reported():
    content = 'some-other-package/option="something"'
    result, unknown = editor.process_content(content)
    assert unknown == ["some-other-package/option"]


def test_multiple_unknown_keys():
    content = dedent("""\
        unknown/key1="value1"
        unknown/key2="value2"
        """)
    result, unknown = editor.process_content(content)
    assert "unknown/key1" in unknown
    assert "unknown/key2" in unknown


def test_mixed_known_and_unknown_keys():
    content = dedent("""\
        tzdata/Areas="Europe"
        unknown/key="value"
        """)
    result, unknown = editor.process_content(content)
    assert 'tzdata/Areas="Etc"' in result
    assert unknown == ["unknown/key"]


# Edge case tests

def test_empty_content():
    result, unknown = editor.process_content("")
    assert result == ""
    assert unknown == []


def test_only_comments():
    content = dedent("""\
        # Comment line
        # Another comment
        ###############################################################################
        """)
    result, unknown = editor.process_content(content)
    assert "# Comment line" in result
    assert "# Another comment" in result
    assert unknown == []


def test_preserves_comments():
    content = dedent("""\
        # Comment line
        # Another comment
        locales/locales_to_be_generated=""
        # Trailing comment""")
    result, unknown = editor.process_content(content)
    assert "# Comment line" in result
    assert "# Another comment" in result
    assert "# Trailing comment" in result
    assert unknown == []


def test_handles_empty_value():
    content = 'locales/locales_to_be_generated=""'
    result, unknown = editor.process_content(content)
    assert 'locales/locales_to_be_generated="en_US.UTF-8 UTF-8"' in result
    assert unknown == []


def test_handles_existing_value():
    content = 'locales/locales_to_be_generated="cs_CZ.UTF-8 UTF-8, de_DE.UTF-8 UTF-8"'
    result, unknown = editor.process_content(content)
    assert 'locales/locales_to_be_generated="en_US.UTF-8 UTF-8"' in result
    assert unknown == []


def test_preserves_trailing_newline():
    content = 'locales/locales_to_be_generated=""\n'
    result, unknown = editor.process_content(content)
    assert result.endswith("\n")
    assert unknown == []


def test_no_trailing_newline_when_input_has_none():
    content = 'locales/locales_to_be_generated=""'
    result, unknown = editor.process_content(content)
    assert not result.endswith("\n")
    assert unknown == []
