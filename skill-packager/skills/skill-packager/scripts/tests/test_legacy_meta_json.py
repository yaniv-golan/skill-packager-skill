"""Tests that legacy meta.json is still accepted with deprecation warnings."""
import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path

from skill_packager.metadata import extract_metadata
from skill_packager.scaffold import scaffold_repo
from skill_packager.validate import validate_repo
from skill_packager.bump_version import bump_version
from tests.helpers import make_source_skill


def _scaffold_universal(tmp_path):
    """Scaffold a universal repo and return the output path (has skill-packager.json)."""
    skill_dir = make_source_skill(tmp_path)
    partial = extract_metadata([skill_dir])
    partial["github_owner"] = "test-owner"
    partial["github_repo"] = "test-skill-repo"
    partial["formats"] = ["universal"]
    partial["targets"] = ["claude-desktop"]
    partial["keywords"] = ["test"]
    partial["category"] = "development"
    meta_path = tmp_path / "skill-packager.json"
    meta_path.write_text(json.dumps(partial, indent=2))

    output = tmp_path / "output"
    scaffold_repo(meta_path, output)
    # Replace stub files so validate passes
    (output / "README.md").write_text("# Test Skill\n\nA real readme.\n")
    (output / "CHANGELOG.md").write_text("# Changelog\n\n## [1.0.0]\n\nFirst release.\n")
    return output


def _make_legacy(repo_path):
    """Rename skill-packager.json -> meta.json in the repo (simulate legacy state)."""
    new_manifest = repo_path / "skill-packager.json"
    legacy_manifest = repo_path / "meta.json"
    new_manifest.rename(legacy_manifest)


class TestValidateWithLegacyMeta:
    def test_validate_warns_on_legacy_meta(self, tmp_path):
        """validate_repo returns a manifest_filename warn entry when only meta.json exists."""
        repo = _scaffold_universal(tmp_path)
        _make_legacy(repo)

        results = validate_repo(repo)
        manifest_warn = [
            r for r in results
            if r.get("check") == "manifest_filename"
        ]
        assert len(manifest_warn) == 1
        entry = manifest_warn[0]
        assert entry["passed"] is True
        assert entry["severity"] == "warn"
        assert "meta.json" in entry["message"]
        assert "v0.3.0" in entry["message"]

    def test_validate_no_warn_on_new_manifest(self, tmp_path):
        """validate_repo has NO manifest_filename entry when skill-packager.json exists."""
        repo = _scaffold_universal(tmp_path)

        results = validate_repo(repo)
        manifest_warn = [
            r for r in results
            if r.get("check") == "manifest_filename"
        ]
        assert len(manifest_warn) == 0

    def test_validate_passes_with_legacy_meta(self, tmp_path):
        """validate_repo has no failed checks even when only meta.json exists."""
        repo = _scaffold_universal(tmp_path)
        _make_legacy(repo)

        results = validate_repo(repo)
        failed = [r for r in results if not r["passed"]]
        assert not failed, f"Unexpected failures: {failed}"


class TestBumpVersionWithLegacyMeta:
    def test_bump_succeeds_with_legacy_meta(self, tmp_path):
        """bump_version succeeds and updates the file when only meta.json exists."""
        repo = _scaffold_universal(tmp_path)
        _make_legacy(repo)

        updated = bump_version(repo, "2.0.0")
        assert len(updated) > 0
        meta = json.loads((repo / "meta.json").read_text())
        assert meta["version"] == "2.0.0"

    def test_bump_stderr_contains_deprecation_with_legacy_meta(self, tmp_path, capsys):
        """bump_version prints deprecation warning to stderr when using legacy meta.json."""
        repo = _scaffold_universal(tmp_path)
        _make_legacy(repo)

        bump_version(repo, "2.0.0")
        captured = capsys.readouterr()
        assert "[deprecation]" in captured.err
        assert "meta.json" in captured.err

    def test_bump_no_deprecation_with_new_manifest(self, tmp_path, capsys):
        """bump_version prints NO deprecation warning when skill-packager.json exists."""
        repo = _scaffold_universal(tmp_path)

        bump_version(repo, "2.0.0")
        captured = capsys.readouterr()
        assert "[deprecation]" not in captured.err


class TestGeneratedBuildZipWithLegacyMeta:
    def test_build_zip_succeeds_with_legacy_meta(self, tmp_path):
        """Generated tools/build-zip.py succeeds when only meta.json exists."""
        repo = _scaffold_universal(tmp_path)
        _make_legacy(repo)

        result = subprocess.run(
            [sys.executable, str(repo / "tools" / "build-zip.py"), "--version", "1.0.0"],
            capture_output=True, text=True, cwd=str(repo),
        )
        assert result.returncode == 0, f"build-zip.py failed: {result.stderr}"

    def test_build_zip_stderr_deprecation_with_legacy_meta(self, tmp_path):
        """Generated tools/build-zip.py prints [deprecation] to stderr for legacy meta.json."""
        repo = _scaffold_universal(tmp_path)
        _make_legacy(repo)

        result = subprocess.run(
            [sys.executable, str(repo / "tools" / "build-zip.py"), "--version", "1.0.0"],
            capture_output=True, text=True, cwd=str(repo),
        )
        assert result.returncode == 0, f"build-zip.py failed: {result.stderr}"
        assert "[deprecation]" in result.stderr

    def test_build_zip_no_deprecation_with_new_manifest(self, tmp_path):
        """Generated tools/build-zip.py prints NO deprecation when skill-packager.json exists."""
        repo = _scaffold_universal(tmp_path)

        result = subprocess.run(
            [sys.executable, str(repo / "tools" / "build-zip.py"), "--version", "1.0.0"],
            capture_output=True, text=True, cwd=str(repo),
        )
        assert result.returncode == 0, f"build-zip.py failed: {result.stderr}"
        assert "[deprecation]" not in result.stderr
