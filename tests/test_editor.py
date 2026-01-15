#!/usr/bin/env python3
"""Tests for the editor script (running as subprocess)."""

from pathlib import Path
from subprocess import run
from sys import executable
from textwrap import dedent

SCRIPT_PATH = Path(__file__).parent.parent / "dpkg_reconfigure_automation_editor.py"


def test_script_help():
    result = run([executable, str(SCRIPT_PATH), "--help"], capture_output=True)
    assert result.returncode == 0
    assert b"usage:" in result.stdout


def test_script_processes_file_in_place(tmp_path):
    content = dedent("""\
        # (Choices: en_US.UTF-8 UTF-8, cs_CZ.UTF-8 UTF-8)
        # Locales to be generated:
        locales/locales_to_be_generated=""
        """)
    filepath = tmp_path / "config.txt"
    filepath.write_text(content)

    result = run([executable, str(SCRIPT_PATH), str(filepath)], capture_output=True)
    assert result.returncode == 0
    assert result.stdout == b""
    assert result.stderr == b""
    assert 'locales/locales_to_be_generated="en_US.UTF-8 UTF-8"' in filepath.read_text()


def test_script_missing_argument_exits():
    result = run([executable, str(SCRIPT_PATH)], capture_output=True)
    assert result.returncode == 2  # argparse exits with 2 for missing arguments


def test_script_exits_with_1_for_unknown_key(tmp_path):
    content = 'unknown-package/option="value"'
    filepath = tmp_path / "config.txt"
    filepath.write_text(content)

    result = run([executable, str(SCRIPT_PATH), str(filepath)], capture_output=True)
    assert result.returncode == 1
    assert b"Error: Unknown configuration key: unknown-package/option" in result.stderr


def test_script_does_not_modify_file_on_unknown_key(tmp_path):
    content = 'unknown-package/option="value"'
    filepath = tmp_path / "config.txt"
    filepath.write_text(content)

    run([executable, str(SCRIPT_PATH), str(filepath)], capture_output=True)
    # File should remain unchanged
    assert filepath.read_text() == content


def test_script_processes_tzdata(tmp_path):
    content = dedent("""\
        # (Choices: GMT, UTC, None of the above)
        # Geographic area:
        tzdata/Areas="GMT"
        # (Choices: GMT, UTC)
        # Time zone:
        tzdata/Zones/Etc="GMT"
        """)
    filepath = tmp_path / "config.txt"
    filepath.write_text(content)

    result = run([executable, str(SCRIPT_PATH), str(filepath)], capture_output=True)
    assert result.returncode == 0
    file_content = filepath.read_text()
    assert 'tzdata/Areas="None of the above"' in file_content
    assert 'tzdata/Zones/Etc="UTC"' in file_content


def test_script_with_overrides(tmp_path):
    content = dedent("""\
        # (Choices: Asia, Europe, None of the above)
        # Geographic area:
        tzdata/Areas="Europe"
        # (Choices: Shanghai, Tokyo)
        # Time zone:
        tzdata/Zones/Asia="Tokyo"
        """)
    filepath = tmp_path / "config.txt"
    filepath.write_text(content)

    result = run(
        [
            executable,
            str(SCRIPT_PATH),
            "tzdata/Areas=Asia",
            "tzdata/Zones/Asia=Shanghai",
            str(filepath),
        ],
        capture_output=True,
    )
    assert result.returncode == 0
    file_content = filepath.read_text()
    assert 'tzdata/Areas="Asia"' in file_content
    assert 'tzdata/Zones/Asia="Shanghai"' in file_content


def test_script_with_override_with_spaces(tmp_path):
    content = dedent("""\
        # (Choices: Europe, None of the above)
        # Geographic area:
        tzdata/Areas="Europe"
        """)
    filepath = tmp_path / "config.txt"
    filepath.write_text(content)

    result = run(
        [
            executable,
            str(SCRIPT_PATH),
            "tzdata/Areas=None of the above",
            str(filepath),
        ],
        capture_output=True,
    )
    assert result.returncode == 0
    file_content = filepath.read_text()
    assert 'tzdata/Areas="None of the above"' in file_content


def test_script_with_invalid_override(tmp_path):
    filepath = tmp_path / "config.txt"
    filepath.write_text("tzdata/Areas=Europe")

    result = run(
        [executable, str(SCRIPT_PATH), "invalid-no-equals", str(filepath)],
        capture_output=True,
    )
    assert result.returncode == 1
    assert b"Invalid override format" in result.stderr


def test_script_verbose_single(tmp_path):
    content = dedent("""\
        # (Choices: Asia, Europe, None of the above)
        tzdata/Areas="Europe"
        """)
    filepath = tmp_path / "config.txt"
    filepath.write_text(content)

    result = run(
        [executable, str(SCRIPT_PATH), "-v", str(filepath)],
        capture_output=True,
    )
    assert result.returncode == 0
    assert b"INFO" in result.stderr
    assert b"Processing file:" in result.stderr


def test_script_verbose_double(tmp_path):
    content = dedent("""\
        # (Choices: Asia, Europe, None of the above)
        tzdata/Areas="Europe"
        """)
    filepath = tmp_path / "config.txt"
    filepath.write_text(content)

    result = run(
        [executable, str(SCRIPT_PATH), "-vv", "tzdata/Areas=Asia", str(filepath)],
        capture_output=True,
    )
    assert result.returncode == 0
    assert b"DEBUG" in result.stderr
    assert b"Adding override:" in result.stderr


def test_script_debug_creates_files(tmp_path):
    content = dedent("""\
        # (Choices: Asia, Europe, None of the above)
        tzdata/Areas="Europe"
        """)
    filepath = tmp_path / "config.txt"
    filepath.write_text(content)

    result = run(
        [executable, str(SCRIPT_PATH), "--debug", "-v", "tzdata/Areas=Asia", str(filepath)],
        capture_output=True,
    )
    assert result.returncode == 0
    assert b"Wrote debug file:" in result.stderr

    # Check that debug files were created
    debug_files = list(Path("/tmp").glob("dpkg_reconfigure_automation_editor.*.before"))
    assert len(debug_files) >= 1
    latest_before = max(debug_files, key=lambda p: p.stat().st_mtime)
    latest_after = Path(str(latest_before).replace(".before", ".after"))

    assert latest_before.exists()
    assert latest_after.exists()

    # Check content
    before_content = latest_before.read_text()
    after_content = latest_after.read_text()
    assert 'tzdata/Areas="Europe"' in before_content
    assert 'tzdata/Areas="Asia"' in after_content
