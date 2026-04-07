import json
import os
from pathlib import Path
from skill_packager.metadata import extract_skill_metadata, extract_metadata
from tests.helpers import SAMPLE_SKILL_MD, SAMPLE_SKILL_MD_NO_VERSION, make_source_skill


def test_parse_skill_md_frontmatter(tmp_path):
    skill_dir = make_source_skill(tmp_path, name="my-skill", skill_md=SAMPLE_SKILL_MD)
    result = extract_skill_metadata(skill_dir)
    assert result["name"] == "test-skill"
    assert "test skill" in result["description"].lower()
    assert result["has_scripts"] is True
    assert result["has_references"] is True
    assert result["has_assets"] is False
    assert result["has_agents"] is False


def test_parse_skill_md_extracts_version(tmp_path):
    skill_dir = make_source_skill(tmp_path, name="my-skill", skill_md=SAMPLE_SKILL_MD)
    result = extract_skill_metadata(skill_dir)
    assert result["version"] == "1.0.0"


def test_parse_skill_md_no_version_uses_version_file(tmp_path):
    skill_dir = make_source_skill(
        tmp_path, name="bare", skill_md=SAMPLE_SKILL_MD_NO_VERSION,
        with_scripts=False, with_references=False,
    )
    (skill_dir / "VERSION").write_text("2.3.0")
    result = extract_skill_metadata(skill_dir)
    assert result["version"] == "2.3.0"


def test_parse_skill_md_no_version_anywhere(tmp_path):
    skill_dir = make_source_skill(
        tmp_path, name="bare", skill_md=SAMPLE_SKILL_MD_NO_VERSION,
        with_scripts=False, with_references=False,
    )
    (skill_dir / "VERSION").unlink()
    result = extract_skill_metadata(skill_dir)
    assert result["version"] is None


def test_extract_metadata_single_skill(tmp_path):
    skill_dir = make_source_skill(tmp_path, name="test-skill", skill_md=SAMPLE_SKILL_MD)
    result = extract_metadata([skill_dir])
    assert len(result["skills"]) == 1
    assert result["version"] == "1.0.0"
    assert result["plugin_name"] == "test-skill"


def test_extract_metadata_multi_skill_leaves_bundle_fields_empty(tmp_path):
    skill_a = make_source_skill(tmp_path, name="skill-a", skill_md=SAMPLE_SKILL_MD)
    src_b = tmp_path / "source2" / "skill-b"
    src_b.mkdir(parents=True)
    (src_b / "SKILL.md").write_text(SAMPLE_SKILL_MD.replace("test-skill", "skill-b"))
    (src_b / "VERSION").write_text("1.0.0")

    result = extract_metadata([skill_a, src_b])
    assert len(result["skills"]) == 2
    assert result["plugin_name"] == ""
    assert result["description"] == ""
    assert result["version"] == ""


def test_source_path_is_absolute(tmp_path):
    skill_dir = make_source_skill(tmp_path, name="test-skill", skill_md=SAMPLE_SKILL_MD)
    result = extract_metadata([skill_dir])
    assert os.path.isabs(result["skills"][0]["source_path"])


def test_skill_entries_match_spec_schema(tmp_path):
    skill_dir = make_source_skill(tmp_path, name="test-skill", skill_md=SAMPLE_SKILL_MD)
    result = extract_metadata([skill_dir])
    entry = result["skills"][0]
    expected_keys = {
        "name", "source_path", "description",
        "has_scripts", "has_references", "has_assets", "has_agents", "has_evals",
    }
    assert set(entry.keys()) == expected_keys
