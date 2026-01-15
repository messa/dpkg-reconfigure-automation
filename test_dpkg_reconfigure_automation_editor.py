#!/usr/bin/env python3
"""Tests for dpkg-reconfigure-automation-editor.py"""

import tempfile
import os
import sys
import unittest

# Import the module under test
sys.path.insert(0, os.path.dirname(__file__))
from importlib import import_module
editor = import_module('dpkg-reconfigure-automation-editor')


class TestProcessTzdata(unittest.TestCase):
    """Tests for tzdata processing."""

    def test_sets_area_to_etc(self):
        content = """Name: tzdata/Areas
Value: Europe
"""
        result = editor.process_tzdata(content)
        self.assertIn("Value: Etc", result)

    def test_sets_zone_to_utc(self):
        content = """Name: tzdata/Zones/Etc
Value: GMT
"""
        result = editor.process_tzdata(content)
        self.assertIn("Value: UTC", result)

    def test_full_tzdata_config(self):
        content = """Name: tzdata/Areas
Template: tzdata/Areas
Value: Europe
Owners: tzdata

Name: tzdata/Zones/Europe
Template: tzdata/Zones/Europe
Value: Prague
Owners: tzdata
"""
        result = editor.process_tzdata(content)
        lines = result.split('\n')

        # Find the value after tzdata/Areas
        found_etc = False
        for i, line in enumerate(lines):
            if 'tzdata/Areas' in line and 'Name:' in line:
                # Look for next Value line
                for j in range(i + 1, min(i + 5, len(lines))):
                    if lines[j].startswith('Value:'):
                        if 'Etc' in lines[j]:
                            found_etc = True
                        break
        self.assertTrue(found_etc, "Expected 'Etc' in tzdata/Areas value")


class TestProcessLocales(unittest.TestCase):
    """Tests for locales processing."""

    def test_sets_locales_to_generate(self):
        content = """Name: locales/locales_to_be_generated
Value: cs_CZ.UTF-8 UTF-8
"""
        result = editor.process_locales(content)
        self.assertIn("Value: en_US.UTF-8 UTF-8", result)

    def test_sets_default_locale(self):
        content = """Name: locales/default_environment_locale
Value: cs_CZ.UTF-8
"""
        result = editor.process_locales(content)
        self.assertIn("Value: en_US.UTF-8", result)
        # Should not have "UTF-8 UTF-8" for default locale
        self.assertNotIn("en_US.UTF-8 UTF-8", result)

    def test_full_locales_config(self):
        content = """Name: locales/locales_to_be_generated
Template: locales/locales_to_be_generated
Value: cs_CZ.UTF-8 UTF-8, de_DE.UTF-8 UTF-8
Owners: locales

Name: locales/default_environment_locale
Template: locales/default_environment_locale
Value: cs_CZ.UTF-8
Owners: locales
"""
        result = editor.process_locales(content)

        # Check locales_to_be_generated has correct value
        self.assertIn("en_US.UTF-8 UTF-8", result)

        # Find the default_environment_locale value
        lines = result.split('\n')
        in_default = False
        for line in lines:
            if 'locales/default_environment_locale' in line:
                in_default = True
            elif line.startswith('Name:'):
                in_default = False
            elif in_default and line.startswith('Value:'):
                # Should be just en_US.UTF-8, not en_US.UTF-8 UTF-8
                self.assertEqual(line, "Value: en_US.UTF-8")


class TestDetectAndProcess(unittest.TestCase):
    """Tests for package detection and processing."""

    def test_detects_tzdata_by_areas(self):
        content = "Name: tzdata/Areas\nValue: Europe\n"
        result = editor.detect_and_process(content)
        self.assertIn("Value: Etc", result)

    def test_detects_tzdata_by_zones(self):
        content = "Name: tzdata/Zones/Europe\nValue: Prague\n"
        result = editor.detect_and_process(content)
        self.assertIn("Value: UTC", result)

    def test_detects_locales_by_locales_to_be_generated(self):
        content = "Name: locales/locales_to_be_generated\nValue: cs_CZ.UTF-8 UTF-8\n"
        result = editor.detect_and_process(content)
        self.assertIn("en_US.UTF-8 UTF-8", result)

    def test_detects_locales_by_default_environment_locale(self):
        content = "Name: locales/default_environment_locale\nValue: cs_CZ.UTF-8\n"
        result = editor.detect_and_process(content)
        self.assertIn("en_US.UTF-8", result)

    def test_unknown_package_unchanged(self):
        content = "Name: some-other-package/option\nValue: something\n"
        result = editor.detect_and_process(content)
        self.assertEqual(result, content)


class TestMain(unittest.TestCase):
    """Tests for main function with file I/O."""

    def test_processes_file_in_place(self):
        content = """Name: locales/locales_to_be_generated
Value: cs_CZ.UTF-8 UTF-8
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            filepath = f.name

        try:
            # Simulate running main with the file
            original_argv = sys.argv
            sys.argv = ['dpkg-reconfigure-automation-editor', filepath]
            try:
                editor.main()
            finally:
                sys.argv = original_argv

            # Read back and verify
            with open(filepath, 'r') as f:
                result = f.read()

            self.assertIn("en_US.UTF-8 UTF-8", result)
        finally:
            os.unlink(filepath)

    def test_missing_argument_exits(self):
        original_argv = sys.argv
        sys.argv = ['dpkg-reconfigure-automation-editor']
        try:
            with self.assertRaises(SystemExit) as cm:
                editor.main()
            self.assertEqual(cm.exception.code, 1)
        finally:
            sys.argv = original_argv


class TestEdgeCases(unittest.TestCase):
    """Tests for edge cases and special scenarios."""

    def test_empty_content(self):
        result = editor.detect_and_process("")
        self.assertEqual(result, "")

    def test_preserves_other_lines(self):
        content = """# Comment line
Name: locales/locales_to_be_generated
Template: locales/locales_to_be_generated
Value: cs_CZ.UTF-8 UTF-8
Owners: locales
# Another comment
"""
        result = editor.process_locales(content)
        self.assertIn("# Comment line", result)
        self.assertIn("# Another comment", result)
        self.assertIn("Template: locales/locales_to_be_generated", result)
        self.assertIn("Owners: locales", result)

    def test_value_with_extra_whitespace(self):
        content = "Name: locales/locales_to_be_generated\nValue:   cs_CZ.UTF-8 UTF-8\n"
        result = editor.process_locales(content)
        # Should preserve the whitespace pattern
        self.assertIn("Value:   en_US.UTF-8 UTF-8", result)


if __name__ == '__main__':
    unittest.main()
