"""Shared constants and factory functions for tests (NOT pytest fixtures)."""
import json
import os

SAMPLE_SKILL_MD = """\
---
name: test-skill
description: >
  A test skill for unit testing.
metadata:
  author: Test Author
  version: "1.0.0"
license: MIT
---

# Test Skill

A test skill for unit testing.
"""

SAMPLE_SKILL_MD_NO_VERSION = """\
---
name: test-skill
description: A minimal skill with no metadata section.
---

# Test Skill

A minimal skill.
"""


def make_sample_meta(tmp_path, **overrides):
    """Create a meta.json file at tmp_path and return its path."""
    meta = {
        "skills": [
            {
                "name": "test-skill",
                "source_path": "skills/test-skill",
                "description": "A test skill for unit testing",
                "has_scripts": True,
                "has_references": True,
                "has_assets": False,
                "has_agents": False,
                "has_evals": False,
            }
        ],
        "plugin_name": "test-skill",
        "marketplace_name": "test-skill",
        "display_name": "Test Skill",
        "description": "A test skill for unit testing",
        "version": "1.0.0",
        "author_name": "Test Author",
        "author_email": "test@example.com",
        "github_owner": "test-owner",
        "github_repo": "test-skill-repo",
        "license": "MIT",
        "keywords": ["test"],
        "category": "development",
        "formats": ["universal"],
        "targets": [],
    }
    meta.update(overrides)
    meta_path = tmp_path / "skill-packager.json"
    meta_path.write_text(json.dumps(meta, indent=2))
    return meta_path


def make_source_skill(
    tmp_path,
    name="test-skill",
    skill_md=SAMPLE_SKILL_MD,
    with_scripts=True,
    with_references=True,
):
    """Create a source skill directory with SKILL.md and optional extras."""
    skill_dir = tmp_path / name
    skill_dir.mkdir(parents=True, exist_ok=True)

    (skill_dir / "SKILL.md").write_text(skill_md)
    (skill_dir / "VERSION").write_text("1.0.0")

    if with_scripts:
        scripts_dir = skill_dir / "scripts"
        scripts_dir.mkdir(exist_ok=True)
        (scripts_dir / "helper.py").write_text(
            "${CLAUDE_SKILL_DIR}/scripts/helper.py\n"
        )

    if with_references:
        references_dir = skill_dir / "references"
        references_dir.mkdir(exist_ok=True)
        (references_dir / "guide.md").write_text(
            "${CLAUDE_SKILL_DIR}/scripts/helper.py\n"
        )

    return skill_dir
