#!/usr/bin/env python3
"""Tests for processing functions."""

from textwrap import dedent

from dpkg_reconfigure_automation_editor import (
    ConfigValues,
    parse_line,
    process_content,
)

# Tests for parse_line


def test_parse_line_returns_key_value():
    result = parse_line('tzdata/Areas="Europe"')
    assert result == ("tzdata/Areas", "Europe")


def test_parse_line_returns_none_for_empty():
    assert parse_line("") is None
    assert parse_line("   ") is None


def test_parse_line_returns_none_for_comment():
    assert parse_line("# Comment") is None
    assert parse_line("  # Indented comment") is None


def test_parse_line_returns_none_for_separator():
    assert parse_line("###############") is None


# Tests for ConfigValues


def test_config_values_exact_match():
    config = ConfigValues()
    assert config.get("tzdata/Areas") == "None of the above"
    # Value depends on FQDN - on .cz servers includes cs_CZ locale
    locales = config.get("locales/locales_to_be_generated")
    assert "en_US.UTF-8 UTF-8" in locales


def test_config_values_unknown():
    config = ConfigValues()
    assert config.get("unknown/key") is None
    assert config.get("some-package/option") is None


# Tests for tzdata processing


def test_tzdata_sets_area_to_etc():
    content = 'tzdata/Areas="Europe"'
    result, unknown, _ = process_content(content)
    assert 'tzdata/Areas="None of the above"' in result
    assert unknown == []


def test_tzdata_sets_zone_to_utc():
    content = 'tzdata/Zones/Etc="GMT"'
    result, unknown, _ = process_content(content)
    assert 'tzdata/Zones/Etc="UTC"' in result
    assert unknown == []


def test_tzdata_full_config():
    content = dedent("""\
        # You are using the editor-based debconf frontend.
        ###############################################################################

        # Geographic area:
        tzdata/Areas="Europe"


        ###############################################################################
        # Instructions...""")
    result, unknown, _ = process_content(content)
    assert 'tzdata/Areas="None of the above"' in result
    assert "# You are using" in result
    assert "# Instructions" in result
    assert unknown == []


# Tests for get_locales


def test_get_locales_returns_english_on_non_cz_server():
    locales = list(ConfigValues.get_locales(fqdn="server.example.com"))
    assert locales == ["en_US.UTF-8 UTF-8"]


def test_get_locales_returns_czech_and_english_on_cz_server():
    locales = set(ConfigValues.get_locales(fqdn="server.example.cz"))
    assert locales == {"cs_CZ.UTF-8 UTF-8", "en_US.UTF-8 UTF-8"}


# Tests for locales processing


def test_locales_sets_locales_to_generate():
    content = 'locales/locales_to_be_generated=""'
    result, unknown, _ = process_content(content)
    # Value depends on FQDN - on .cz servers includes cs_CZ locale
    assert 'locales/locales_to_be_generated="' in result
    assert "en_US.UTF-8 UTF-8" in result
    assert unknown == []


def test_locales_sets_default_locale():
    content = 'locales/default_environment_locale="cs_CZ.UTF-8"'
    result, unknown, _ = process_content(content)
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
    result, unknown, _ = process_content(content)
    # Value depends on FQDN - on .cz servers includes cs_CZ locale
    assert 'locales/locales_to_be_generated="' in result
    assert "en_US.UTF-8 UTF-8" in result
    assert "# You are using" in result
    assert unknown == []


# Tests for unknown keys


def test_unknown_key_is_reported():
    content = 'some-other-package/option="something"'
    result, unknown, _ = process_content(content)
    assert unknown == ["some-other-package/option"]


def test_multiple_unknown_keys():
    content = dedent("""\
        unknown/key1="value1"
        unknown/key2="value2"
        """)
    result, unknown, _ = process_content(content)
    assert "unknown/key1" in unknown
    assert "unknown/key2" in unknown


def test_mixed_known_and_unknown_keys():
    content = dedent("""\
        tzdata/Areas="Europe"
        unknown/key="value"
        """)
    result, unknown, _ = process_content(content)
    assert 'tzdata/Areas="None of the above"' in result
    assert unknown == ["unknown/key"]


# Edge case tests


def test_empty_content():
    result, unknown, unknown_values = process_content("")
    assert result == ""
    assert unknown == []
    assert unknown_values == []


def test_only_comments():
    content = dedent("""\
        # Comment line
        # Another comment
        ###############################################################################
        """)
    result, unknown, _ = process_content(content)
    assert "# Comment line" in result
    assert "# Another comment" in result
    assert unknown == []


def test_preserves_comments():
    content = dedent("""\
        # Comment line
        # Another comment
        locales/locales_to_be_generated=""
        # Trailing comment""")
    result, unknown, _ = process_content(content)
    assert "# Comment line" in result
    assert "# Another comment" in result
    assert "# Trailing comment" in result
    assert unknown == []


def test_handles_empty_value():
    content = 'locales/locales_to_be_generated=""'
    result, unknown, _ = process_content(content)
    # Value depends on FQDN - on .cz servers includes cs_CZ locale
    assert 'locales/locales_to_be_generated="' in result
    assert "en_US.UTF-8 UTF-8" in result
    assert unknown == []


def test_handles_existing_value():
    content = 'locales/locales_to_be_generated="cs_CZ.UTF-8 UTF-8, de_DE.UTF-8 UTF-8"'
    result, unknown, _ = process_content(content)
    # Value depends on FQDN - on .cz servers includes cs_CZ locale
    assert 'locales/locales_to_be_generated="' in result
    assert "en_US.UTF-8 UTF-8" in result
    assert unknown == []


def test_preserves_trailing_newline():
    content = 'locales/locales_to_be_generated=""\n'
    result, unknown, _ = process_content(content)
    assert result.endswith("\n")
    assert unknown == []


def test_no_trailing_newline_when_input_has_none():
    content = 'locales/locales_to_be_generated=""'
    result, unknown, _ = process_content(content)
    assert not result.endswith("\n")
    assert unknown == []


# Tests for choice validation (check=True)


def test_tzdata_accepts_value_when_in_choices():
    content = dedent("""\
        # (Choices: Africa, Americas, Europe, None of the above)
        # Geographic area:
        tzdata/Areas="Europe"
        """)
    result, unknown, unknown_values = process_content(content)
    assert 'tzdata/Areas="None of the above"' in result
    assert unknown == []
    assert unknown_values == []


def test_tzdata_warns_when_value_not_in_choices():
    content = dedent("""\
        # (Choices: Africa, Americas, Europe)
        # Geographic area:
        tzdata/Areas="Europe"
        """)
    result, unknown, unknown_values = process_content(content)
    # Value is set even when not in choices
    assert 'tzdata/Areas="None of the above"' in result
    assert unknown == []
    assert "None of the above" in unknown_values


def test_tzdata_zone_accepts_utc_when_in_choices():
    content = dedent("""\
        # (Choices: GMT, GMT0, UCT, UTC, Universal, Zulu)
        # Time zone:
        tzdata/Zones/Etc="GMT"
        """)
    result, unknown, unknown_values = process_content(content)
    assert 'tzdata/Zones/Etc="UTC"' in result
    assert unknown == []
    assert unknown_values == []


def test_locales_accepts_value_when_in_choices():
    content = dedent("""\
        # (Choices: cs_CZ.UTF-8 UTF-8, en_US.UTF-8 UTF-8)
        # Locales to be generated:
        locales/locales_to_be_generated=""
        """)
    result, unknown, unknown_values = process_content(content)
    # Value depends on FQDN - on .cz servers includes cs_CZ locale
    assert 'locales/locales_to_be_generated="' in result
    assert "en_US.UTF-8 UTF-8" in result
    assert unknown == []
    assert unknown_values == []


def test_locales_warns_when_value_not_in_choices():
    content = dedent("""\
        # (Choices: cs_CZ.UTF-8 UTF-8, de_DE.UTF-8 UTF-8)
        # Locales to be generated:
        locales/locales_to_be_generated=""
        """)
    result, unknown, unknown_values = process_content(content)
    # Value is set even when not in choices
    assert 'locales/locales_to_be_generated="' in result
    assert "en_US.UTF-8 UTF-8" in result
    assert unknown == []
    # Value depends on FQDN - the full value string should be in unknown_values
    assert len(unknown_values) == 1
    assert "en_US.UTF-8 UTF-8" in unknown_values[0]


# Tests for add_override


def test_add_override_adds_to_exact():
    config = ConfigValues()
    config.add_override("tzdata/Areas", "Asia")
    assert config.get("tzdata/Areas") == "Asia"


def test_add_override_overrides_default():
    config = ConfigValues()
    assert config.get("tzdata/Areas") == "Etc"
    config.add_override("tzdata/Areas", "Europe")
    assert config.get("tzdata/Areas") == "Europe"


def test_add_override_multiple_values():
    config = ConfigValues()
    config.add_override("tzdata/Areas", "Asia")
    config.add_override("tzdata/Zones/Asia", "Shanghai")
    assert config.get("tzdata/Areas") == "Asia"
    assert config.get("tzdata/Zones/Asia") == "Shanghai"


def test_process_content_with_custom_config():
    config = ConfigValues()
    config.add_override("tzdata/Areas", "Asia")
    config.add_override("tzdata/Zones/Asia", "Shanghai")
    content = dedent("""\
        # (Choices: Asia, Europe, None of the above)
        tzdata/Areas="Europe"
        # (Choices: Shanghai, Tokyo)
        tzdata/Zones/Asia="Tokyo"
        """)
    result, unknown, unknown_values = process_content(content, config=config)
    assert 'tzdata/Areas="Asia"' in result
    assert 'tzdata/Zones/Asia="Shanghai"' in result
    assert unknown == []
    assert unknown_values == []


def test_full_tzdata_content_with_check():
    """Test with realistic tzdata content from how_it_works.md"""
    content = dedent("""\
        # You are using the editor-based debconf frontend to configure your system.
        ###########################################################################################

        # Please select the geographic area in which you live.
        #
        # (Choices: Africa, Americas, Antarctica, Arctic Ocean, Asia, Atlantic Ocean, Australia, Europe, Indian Ocean, Pacific Ocean, None of the above)
        # Geographic area:
        tzdata/Areas="Europe"


        ###########################################################################################
        # The editor-based debconf frontend presents you with one or more text files to edit.
        """)
    result, unknown, unknown_values = process_content(content)
    assert 'tzdata/Areas="None of the above"' in result
    assert unknown == []
    assert unknown_values == []


def test_full_tzdata_zones_content_with_check():
    """Test with realistic tzdata zones content from how_it_works.md"""
    content = dedent("""\
        # You are using the editor-based debconf frontend to configure your system.
        ###########################################################################################

        # Please select your time zone.
        #
        # (Choices: GMT, GMT0, GMT+0, GMT+1, GMT-1, Greenwich, UCT, UTC, Universal, Zulu)
        # Time zone:
        tzdata/Zones/Etc="GMT"


        ###########################################################################################
        # The editor-based debconf frontend presents you with one or more text files to edit.
        """)
    result, unknown, unknown_values = process_content(content)
    assert 'tzdata/Zones/Etc="UTC"' in result
    assert unknown == []
    assert unknown_values == []
