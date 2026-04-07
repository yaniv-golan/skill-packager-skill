import json
import os
import shutil
import zipfile
from pathlib import Path
from skill_packager.build_zip import build_zip
from skill_packager.scaffold import scaffold_repo
from tests.helpers import make_source_skill, make_sample_meta, SAMPLE_SKILL_MD


def _scaffold_for_zip(tmp_path, formats=None):
    """Create a scaffolded repo to test zip building."""
    skill_dir = make_source_skill(tmp_path)
    meta_path = make_sample_meta(tmp_path, formats=formats or ["claude-plugin"],
        skills=[{"name": "test-skill", "source_path": str(skill_dir),
                 "description": "A test skill", "has_scripts": True,
                 "has_references": True, "has_assets": False,
                 "has_agents": False, "has_evals": False}])
    output = tmp_path / "repo"
    scaffold_repo(meta_path, output)
    return output


def test_build_zip_creates_zip_file(tmp_path):
    repo = _scaffold_for_zip(tmp_path)
    skill_dir = repo / "test-skill" / "skills" / "test-skill"
    output = tmp_path / "dist" / "test.zip"
    build_zip(skill_dir, output)
    assert output.exists()
    assert zipfile.is_zipfile(output)


def test_build_zip_single_skill_root_layout(tmp_path):
    repo = _scaffold_for_zip(tmp_path)
    skill_dir = repo / "test-skill" / "skills" / "test-skill"
    output = tmp_path / "dist" / "test.zip"
    build_zip(skill_dir, output)
    with zipfile.ZipFile(output) as zf:
        names = zf.namelist()
        assert any(n.startswith("test-skill/") for n in names)
        assert any(n == "test-skill/SKILL.md" for n in names)


def test_build_zip_strips_claude_skill_dir(tmp_path):
    repo = _scaffold_for_zip(tmp_path)
    skill_dir = repo / "test-skill" / "skills" / "test-skill"
    output = tmp_path / "dist" / "test.zip"
    build_zip(skill_dir, output)
    with zipfile.ZipFile(output) as zf:
        for name in zf.namelist():
            if name.endswith(".md"):
                content = zf.read(name).decode("utf-8")
                assert "${CLAUDE_SKILL_DIR}/" not in content, f"Found in {name}"


def test_build_zip_writes_version(tmp_path):
    repo = _scaffold_for_zip(tmp_path)
    skill_dir = repo / "test-skill" / "skills" / "test-skill"
    output = tmp_path / "dist" / "test.zip"
    build_zip(skill_dir, output, version="2.0.0")
    with zipfile.ZipFile(output) as zf:
        version = zf.read("test-skill/VERSION").decode("utf-8").strip()
        assert version == "2.0.0"


def test_build_zip_preserves_scripts(tmp_path):
    repo = _scaffold_for_zip(tmp_path)
    skill_dir = repo / "test-skill" / "skills" / "test-skill"
    output = tmp_path / "dist" / "test.zip"
    build_zip(skill_dir, output)
    with zipfile.ZipFile(output) as zf:
        assert "test-skill/scripts/helper.py" in zf.namelist()
