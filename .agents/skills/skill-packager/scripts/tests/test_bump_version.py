import json
from pathlib import Path
from skill_packager.bump_version import bump_version
from skill_packager.scaffold import scaffold_repo
from tests.helpers import make_source_skill, make_sample_meta


def _scaffold_repo(tmp_path, formats=None):
    skill_dir = make_source_skill(tmp_path)
    meta_path = make_sample_meta(tmp_path, formats=formats or ["universal"],
        skills=[{"name": "test-skill", "source_path": str(skill_dir),
                 "description": "A test skill", "has_scripts": True,
                 "has_references": True, "has_assets": False,
                 "has_agents": False, "has_evals": False}])
    output = tmp_path / "repo"
    scaffold_repo(meta_path, output)
    return output


def test_bump_updates_root_version(tmp_path):
    repo = _scaffold_repo(tmp_path)
    bump_version(repo, "2.0.0")
    assert (repo / "VERSION").read_text().strip() == "2.0.0"


def test_bump_updates_meta_json(tmp_path):
    repo = _scaffold_repo(tmp_path)
    bump_version(repo, "2.0.0")
    meta = json.loads((repo / "meta.json").read_text())
    assert meta["version"] == "2.0.0"


def test_bump_updates_inner_plugin_json(tmp_path):
    repo = _scaffold_repo(tmp_path)
    bump_version(repo, "2.0.0")
    data = json.loads((repo / "test-skill" / ".claude-plugin" / "plugin.json").read_text())
    assert data["version"] == "2.0.0"


def test_bump_updates_marketplace_json(tmp_path):
    repo = _scaffold_repo(tmp_path)
    bump_version(repo, "2.0.0")
    data = json.loads((repo / ".claude-plugin" / "marketplace.json").read_text())
    assert data["metadata"]["version"] == "2.0.0"


def test_bump_updates_cursor_json(tmp_path):
    repo = _scaffold_repo(tmp_path)
    bump_version(repo, "2.0.0")
    data = json.loads((repo / ".cursor-plugin" / "plugin.json").read_text())
    assert data["version"] == "2.0.0"


def test_bump_updates_skill_version_file(tmp_path):
    repo = _scaffold_repo(tmp_path)
    bump_version(repo, "2.0.0")
    v = (repo / "test-skill" / "skills" / "test-skill" / "VERSION").read_text().strip()
    assert v == "2.0.0"


def test_bump_updates_agents_skills_version(tmp_path):
    repo = _scaffold_repo(tmp_path)
    bump_version(repo, "2.0.0")
    v = (repo / ".agents" / "skills" / "test-skill" / "VERSION").read_text().strip()
    assert v == "2.0.0"


def test_bump_skips_nonexistent_files(tmp_path):
    repo = _scaffold_repo(tmp_path, formats=["claude-plugin"])
    bump_version(repo, "2.0.0")
    meta = json.loads((repo / "meta.json").read_text())
    assert meta["version"] == "2.0.0"
