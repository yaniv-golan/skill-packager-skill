import json
import os
from pathlib import Path

import pytest

from skill_packager.scaffold import scaffold_repo
from tests.helpers import (
    make_source_skill,
    make_sample_meta,
    SAMPLE_SKILL_MD,
    SAMPLE_SKILL_MD_NO_VERSION,
)


def _scaffold_setup(tmp_path, formats=None, **meta_overrides):
    """Create source skill and meta.json with correct source_path."""
    skill_dir = make_source_skill(tmp_path)
    overrides = {
        "formats": formats or ["universal"],
        "skills": [{
            "name": "test-skill",
            "source_path": str(skill_dir),
            "description": "A test skill for unit testing",
            "has_scripts": True,
            "has_references": True,
            "has_assets": False,
            "has_agents": False,
            "has_evals": False,
        }],
    }
    overrides.update(meta_overrides)
    meta_path = make_sample_meta(tmp_path, **overrides)
    return meta_path


def test_scaffold_universal_creates_all_dirs(tmp_path):
    meta_path = _scaffold_setup(tmp_path)
    output = tmp_path / "output"
    scaffold_repo(meta_path, output)

    assert (output / ".github" / "workflows" / "release.yml").exists()
    assert (output / ".github" / "workflows" / "deploy-pages.yml").exists()
    assert (output / ".claude-plugin" / "marketplace.json").exists()
    assert (output / ".cursor-plugin" / "plugin.json").exists()
    assert (output / ".agents" / "skills" / "test-skill" / "SKILL.md").exists()
    assert (output / "test-skill" / ".claude-plugin" / "plugin.json").exists()
    assert (output / "test-skill" / "skills" / "test-skill" / "SKILL.md").exists()
    assert (output / "tools" / "bump-version.py").exists()
    assert (output / "tools" / "build-zip.py").exists()
    assert (output / "static" / "install-claude-desktop.html").exists()
    assert (output / "meta.json").exists()
    assert (output / "VERSION").exists()
    assert (output / "VERSIONING.md").exists()
    assert (output / "CHANGELOG.md").exists()
    assert (output / "README.md").exists()
    assert (output / "LICENSE").exists()


def test_scaffold_copies_skill_files(tmp_path):
    meta_path = _scaffold_setup(tmp_path)
    output = tmp_path / "output"
    scaffold_repo(meta_path, output)

    skill_dir = output / "test-skill" / "skills" / "test-skill"
    assert (skill_dir / "scripts" / "helper.py").exists()
    assert (skill_dir / "references" / "guide.md").exists()


def test_scaffold_canonical_keeps_claude_skill_dir(tmp_path):
    meta_path = _scaffold_setup(tmp_path)
    output = tmp_path / "output"
    scaffold_repo(meta_path, output)

    ref = output / "test-skill" / "skills" / "test-skill" / "references" / "guide.md"
    assert "${CLAUDE_SKILL_DIR}/" in ref.read_text()


def test_scaffold_agents_skills_is_stripped_copy(tmp_path):
    meta_path = _scaffold_setup(tmp_path)
    output = tmp_path / "output"
    scaffold_repo(meta_path, output)

    ref = output / ".agents" / "skills" / "test-skill" / "references" / "guide.md"
    assert "${CLAUDE_SKILL_DIR}/" not in ref.read_text()
    assert "scripts/helper.py" in ref.read_text()


def test_scaffold_claude_plugin_only(tmp_path):
    meta_path = _scaffold_setup(tmp_path, formats=["claude-plugin"])
    output = tmp_path / "output"
    scaffold_repo(meta_path, output)

    assert (output / "test-skill" / ".claude-plugin" / "plugin.json").exists()
    assert (output / "test-skill" / "skills" / "test-skill" / "SKILL.md").exists()
    assert not (output / ".cursor-plugin").exists()
    assert not (output / ".agents").exists()
    assert not (output / ".github").exists()


def test_scaffold_agent_skills_standalone(tmp_path):
    meta_path = _scaffold_setup(tmp_path, formats=["agent-skills"])
    output = tmp_path / "output"
    scaffold_repo(meta_path, output)

    skill_md = output / ".agents" / "skills" / "test-skill" / "SKILL.md"
    assert skill_md.exists()
    assert "${CLAUDE_SKILL_DIR}/" not in skill_md.read_text()
    # No plugin tree
    assert not (output / "test-skill").exists()


def test_scaffold_aborts_if_output_exists_non_empty(tmp_path):
    meta_path = _scaffold_setup(tmp_path)
    output = tmp_path / "output"
    output.mkdir()
    (output / "existing-file.txt").write_text("I exist")

    with pytest.raises(SystemExit):
        scaffold_repo(meta_path, output)


def test_scaffold_json_files_are_valid(tmp_path):
    meta_path = _scaffold_setup(tmp_path)
    output = tmp_path / "output"
    scaffold_repo(meta_path, output)

    for json_file in output.rglob("*.json"):
        json.loads(json_file.read_text())


def test_scaffold_tools_are_executable(tmp_path):
    meta_path = _scaffold_setup(tmp_path)
    output = tmp_path / "output"
    scaffold_repo(meta_path, output)

    assert os.access(output / "tools" / "bump-version.py", os.X_OK)
    assert os.access(output / "tools" / "build-zip.py", os.X_OK)


def test_scaffold_version_consistent(tmp_path):
    meta_path = _scaffold_setup(tmp_path)
    output = tmp_path / "output"
    scaffold_repo(meta_path, output)

    version = (output / "VERSION").read_text().strip()
    assert version == "1.0.0"

    plugin_json = json.loads(
        (output / "test-skill" / ".claude-plugin" / "plugin.json").read_text()
    )
    assert plugin_json["version"] == "1.0.0"

    cursor_json = json.loads(
        (output / ".cursor-plugin" / "plugin.json").read_text()
    )
    assert cursor_json["version"] == "1.0.0"

    marketplace_json = json.loads(
        (output / ".claude-plugin" / "marketplace.json").read_text()
    )
    assert marketplace_json["metadata"]["version"] == "1.0.0"


def test_scaffold_injects_metadata_version_if_absent(tmp_path):
    skill_dir = make_source_skill(
        tmp_path, skill_md=SAMPLE_SKILL_MD_NO_VERSION,
        with_scripts=False, with_references=False,
    )
    meta_path = make_sample_meta(
        tmp_path, formats=["claude-plugin"],
        skills=[{
            "name": "test-skill",
            "source_path": str(skill_dir),
            "description": "A test skill for unit testing",
            "has_scripts": False,
            "has_references": False,
            "has_assets": False,
            "has_agents": False,
            "has_evals": False,
        }],
    )
    output = tmp_path / "output"
    scaffold_repo(meta_path, output)

    skill_md = (output / "test-skill" / "skills" / "test-skill" / "SKILL.md").read_text()
    assert 'version: "1.0.0"' in skill_md
