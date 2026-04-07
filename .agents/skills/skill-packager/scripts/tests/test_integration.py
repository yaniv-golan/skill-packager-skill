"""Full round-trip integration test: metadata → scaffold → validate → bump → zip."""
import json
import subprocess
import sys
import zipfile
from pathlib import Path

from skill_packager.metadata import extract_metadata
from skill_packager.scaffold import scaffold_repo
from skill_packager.validate import validate_repo
from skill_packager.bump_version import bump_version
from skill_packager.build_zip import build_zip
from tests.helpers import make_source_skill, SAMPLE_SKILL_MD


def test_full_round_trip_universal(tmp_path):
    """Single-skill universal repo: metadata → scaffold → validate → bump → zip."""
    skill_dir = make_source_skill(tmp_path)
    partial = extract_metadata([skill_dir])
    partial["github_owner"] = "test-owner"
    partial["github_repo"] = "test-skill-repo"
    partial["formats"] = ["universal"]
    partial["targets"] = ["claude-desktop", "cursor"]
    partial["keywords"] = ["test"]
    partial["category"] = "development"
    meta_path = tmp_path / "meta.json"
    meta_path.write_text(json.dumps(partial, indent=2))

    output = tmp_path / "output"
    scaffold_repo(meta_path, output)

    (output / "README.md").write_text("# Test Skill\n\nA real readme.\n")
    (output / "CHANGELOG.md").write_text("# Changelog\n\n## [1.0.0]\n\nFirst release.\n")

    results = validate_repo(output)
    failed = [r for r in results if not r["passed"]]
    assert not failed, f"Validation failed: {failed}"

    updated = bump_version(output, "1.1.0")
    assert len(updated) > 5

    results = validate_repo(output)
    failed = [r for r in results if not r["passed"]]
    assert not failed, f"Post-bump validation failed: {failed}"

    skill_dir_in_repo = output / "test-skill" / "skills" / "test-skill"
    zip_path = tmp_path / "dist" / "test.zip"
    build_zip(skill_dir_in_repo, zip_path, version="1.1.0")

    assert zip_path.exists()
    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
        assert "test-skill/SKILL.md" in names
        for name in names:
            if name.endswith(".md"):
                content = zf.read(name).decode()
                assert "${CLAUDE_SKILL_DIR}" not in content
        v = zf.read("test-skill/VERSION").decode().strip()
        assert v == "1.1.0"


def test_full_round_trip_cli(tmp_path):
    """Test the CLI interface end-to-end via subprocess."""
    skill_dir = make_source_skill(tmp_path)
    scripts_dir = str(Path(__file__).resolve().parent.parent)

    result = subprocess.run(
        [sys.executable, "-m", "skill_packager", "metadata",
         "--skill-path", str(skill_dir)],
        capture_output=True, text=True, cwd=scripts_dir,
    )
    assert result.returncode == 0, f"metadata failed: {result.stderr}"
    meta = json.loads(result.stdout)
    assert meta["skills"][0]["name"] == "test-skill"

    meta["github_owner"] = "test-owner"
    meta["github_repo"] = "test-skill-repo"
    meta["formats"] = ["claude-plugin"]
    meta["keywords"] = ["test"]
    meta["category"] = "development"
    meta_path = tmp_path / "meta.json"
    meta_path.write_text(json.dumps(meta, indent=2))

    output = tmp_path / "output"
    result = subprocess.run(
        [sys.executable, "-m", "skill_packager", "scaffold",
         "--metadata", str(meta_path), "--output", str(output)],
        capture_output=True, text=True, cwd=scripts_dir,
    )
    assert result.returncode == 0, f"scaffold failed: {result.stderr}"

    result = subprocess.run(
        [sys.executable, "-m", "skill_packager", "validate", str(output), "--json"],
        capture_output=True, text=True, cwd=scripts_dir,
    )
    assert result.returncode == 0, f"validate failed: {result.stderr}"
    results = json.loads(result.stdout)
    assert all(r["passed"] for r in results)


def test_generated_bump_version_py_works(tmp_path):
    """Test the generated tools/bump-version.py actually bumps versions."""
    skill_dir = make_source_skill(tmp_path)
    partial = extract_metadata([skill_dir])
    partial["github_owner"] = "test-owner"
    partial["github_repo"] = "test-skill-repo"
    partial["formats"] = ["universal"]
    partial["targets"] = ["claude-desktop"]
    partial["keywords"] = ["test"]
    partial["category"] = "development"
    meta_path = tmp_path / "meta.json"
    meta_path.write_text(json.dumps(partial, indent=2))
    output = tmp_path / "output"
    scaffold_repo(meta_path, output)

    result = subprocess.run(
        [sys.executable, str(output / "tools" / "bump-version.py"), str(output), "3.0.0"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr

    assert (output / "VERSION").read_text().strip() == "3.0.0"
    meta = json.loads((output / "meta.json").read_text())
    assert meta["version"] == "3.0.0"
    plugin = json.loads((output / "test-skill" / ".claude-plugin" / "plugin.json").read_text())
    assert plugin["version"] == "3.0.0"


def test_generated_build_zip_py_works(tmp_path):
    """Test the generated tools/build-zip.py actually builds a valid zip."""
    skill_dir = make_source_skill(tmp_path)
    partial = extract_metadata([skill_dir])
    partial["github_owner"] = "test-owner"
    partial["github_repo"] = "test-skill-repo"
    partial["formats"] = ["universal"]
    partial["targets"] = ["claude-desktop"]
    partial["keywords"] = ["test"]
    partial["category"] = "development"
    meta_path = tmp_path / "meta.json"
    meta_path.write_text(json.dumps(partial, indent=2))
    output = tmp_path / "output"
    scaffold_repo(meta_path, output)

    result = subprocess.run(
        [sys.executable, str(output / "tools" / "build-zip.py"), "--version", "1.0.0"],
        capture_output=True, text=True, cwd=str(output),
    )
    assert result.returncode == 0, result.stderr

    zips = list(output.glob("dist/*.zip"))
    assert len(zips) == 1
    with zipfile.ZipFile(zips[0]) as zf:
        names = zf.namelist()
        assert any("SKILL.md" in n for n in names)
        for name in names:
            if name.endswith(".md"):
                content = zf.read(name).decode()
                assert "${CLAUDE_SKILL_DIR}" not in content
