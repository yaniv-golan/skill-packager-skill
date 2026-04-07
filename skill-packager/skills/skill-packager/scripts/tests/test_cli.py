"""Tests for the CLI entry point."""
import subprocess
import sys

from pathlib import Path

SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent)

SUBCOMMANDS = ["metadata", "scaffold", "build-zip", "validate", "bump-version"]


def run_cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "skill_packager", *args],
        cwd=SCRIPTS_DIR,
        capture_output=True,
        text=True,
    )


def test_cli_help_exits_zero():
    result = run_cli("--help")
    assert result.returncode == 0
    assert "usage:" in result.stdout.lower()


def test_cli_has_subcommands():
    result = run_cli("--help")
    for cmd in SUBCOMMANDS:
        assert cmd in result.stdout, f"Expected subcommand '{cmd}' in help output"


def test_cli_no_args_shows_help():
    result = run_cli()
    assert result.returncode != 0
