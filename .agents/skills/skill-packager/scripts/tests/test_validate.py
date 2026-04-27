import json
from pathlib import Path
from skill_packager.validate import validate_repo
from skill_packager.scaffold import scaffold_repo
from tests.helpers import make_source_skill, make_sample_meta, SAMPLE_SKILL_MD


def _scaffold_valid_repo(tmp_path, formats=None):
    """Scaffold a valid repo for validation testing."""
    skill_dir = make_source_skill(tmp_path)
    meta_path = make_sample_meta(tmp_path, formats=formats or ["universal"],
        skills=[{"name": "test-skill", "source_path": str(skill_dir),
                 "description": "A test skill", "has_scripts": True,
                 "has_references": True, "has_assets": False,
                 "has_agents": False, "has_evals": False}])
    output = tmp_path / "repo"
    scaffold_repo(meta_path, output)
    # Replace stubs so validation passes
    (output / "README.md").write_text("# Test Skill\n\nReal content.\n")
    (output / "CHANGELOG.md").write_text("# Changelog\n\n## [1.0.0]\n\nInitial.\n")
    return output


def test_validate_passes_on_valid_universal_repo(tmp_path):
    repo = _scaffold_valid_repo(tmp_path)
    results = validate_repo(repo)
    assert all(r["passed"] for r in results), \
        f"Failed: {[r for r in results if not r['passed']]}"


def test_validate_detects_invalid_json(tmp_path):
    repo = _scaffold_valid_repo(tmp_path)
    (repo / ".cursor-plugin" / "plugin.json").write_text("{invalid json")
    results = validate_repo(repo)
    json_checks = [r for r in results if "json" in r["check"].lower()]
    assert any(not r["passed"] for r in json_checks)


def test_validate_detects_version_mismatch(tmp_path):
    repo = _scaffold_valid_repo(tmp_path)
    (repo / "VERSION").write_text("9.9.9")
    results = validate_repo(repo)
    version_checks = [r for r in results if "version" in r["check"].lower()]
    assert any(not r["passed"] for r in version_checks)


def test_validate_detects_stub_readme(tmp_path):
    repo = _scaffold_valid_repo(tmp_path)
    (repo / "README.md").write_text("<!-- SKILL_PACKAGER: REPLACE THIS -->")
    results = validate_repo(repo)
    readme_checks = [r for r in results if "readme" in r["check"].lower()]
    assert any(not r["passed"] for r in readme_checks)


def test_validate_skips_irrelevant_checks_for_claude_plugin(tmp_path):
    skill_dir = make_source_skill(tmp_path)
    meta_path = make_sample_meta(tmp_path, formats=["claude-plugin"],
        skills=[{"name": "test-skill", "source_path": str(skill_dir),
                 "description": "A test skill", "has_scripts": True,
                 "has_references": True, "has_assets": False,
                 "has_agents": False, "has_evals": False}])
    output = tmp_path / "repo"
    scaffold_repo(meta_path, output)
    results = validate_repo(output)
    check_names = [r["check"] for r in results]
    assert not any("release" in c.lower() for c in check_names)
    assert not any("readme" in c.lower() for c in check_names)


def test_validate_json_output(tmp_path):
    repo = _scaffold_valid_repo(tmp_path)
    results = validate_repo(repo)
    json.dumps(results)  # Must be serializable
    assert all("check" in r and "passed" in r for r in results)


def test_validate_no_warning_for_short_skill_md(tmp_path):
    repo = _scaffold_valid_repo(tmp_path)
    results = validate_repo(repo)
    length_checks = [r for r in results if "skill_md_length" in r["check"]]
    assert all(r["passed"] for r in length_checks)
    assert all("warning" not in r.get("message", "").lower() for r in length_checks)


def test_validate_warns_for_long_skill_md(tmp_path):
    repo = _scaffold_valid_repo(tmp_path)
    # Find the SKILL.md in the plugin tree and make it 501 lines
    skill_mds = list(repo.rglob("SKILL.md"))
    assert skill_mds, "Expected at least one SKILL.md in scaffolded repo"
    for smd in skill_mds:
        smd.write_text("---\nname: test-skill\ndescription: test\n---\n" + "\n".join(f"line {i}" for i in range(501)))
    results = validate_repo(repo)
    length_checks = [r for r in results if "skill_md_length" in r["check"]]
    assert length_checks, "Expected skill_md_length checks"
    assert all(r["passed"] for r in length_checks), "Length check should pass (warning, not failure)"
    assert any("warning" in r.get("message", "").lower() for r in length_checks), \
        f"Expected warning message, got: {length_checks}"
