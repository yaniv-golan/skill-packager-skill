# Skill Packager Scripts Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python CLI (`scripts/skill_packager/`) with 5 subcommands (metadata, scaffold, build-zip, validate, bump-version) that handle all deterministic generation for skill packaging, replacing the current 659-line template-reading approach.

**Architecture:** Stdlib-only Python package invoked via `python3 ${CLAUDE_SKILL_DIR}/scripts/skill_packager <subcommand>`. Templates live in `templates.py` as format-string constants. All subcommands read/write a `meta.json` that acts as the single source of truth for repo structure. Generated repos get standalone `tools/bump-version.py` and `tools/build-zip.py` that also read `meta.json`.

**Tech Stack:** Python 3.8+ stdlib only (json, argparse, pathlib, shutil, zipfile, subprocess, re, os, textwrap)

**Spec:** `docs/superpowers/specs/2026-04-06-skill-packager-scripts-design.md`

**Existing templates:** `skills/skill-packager/references/formats.md` (all JSON/YAML/HTML templates with `{{variable}}` placeholders — convert to Python `{variable}` format strings)

---

## File Structure

All new files live under `skills/skill-packager/scripts/skill_packager/`:

| File | Responsibility |
|------|---------------|
| `__init__.py` | Empty package marker |
| `__main__.py` | CLI entry point — argparse with subcommands, dispatches to modules |
| `templates.py` | All file templates as Python string constants with `{variable}` placeholders |
| `metadata.py` | Parse SKILL.md frontmatter, detect subdirs, read git config/remote |
| `scaffold.py` | Generate repo directory structure from metadata + templates |
| `build_zip.py` | Copy skill dir, strip `${CLAUDE_SKILL_DIR}/`, create zip |
| `validate.py` | Format-aware validation: JSON parsing, version consistency, path resolution |
| `bump_version.py` | Propagate version to all locations discovered via `meta.json` |

Test files under `skills/skill-packager/scripts/tests/`:

| File | What it tests |
|------|--------------|
| `test_metadata.py` | SKILL.md parsing, subdir detection, multi-skill merging |
| `test_templates.py` | All templates render without KeyError, produce valid JSON where applicable |
| `test_scaffold.py` | Each format produces correct directory structure, file contents, path hygiene |
| `test_build_zip.py` | Zip layout (single/multi), `${CLAUDE_SKILL_DIR}` stripping, VERSION injection |
| `test_validate.py` | Pass/fail for each check, format-awareness, JSON output mode |
| `test_bump_version.py` | All version locations updated, format-awareness, `.agents/skills/` copy mode |
| `helpers.py` | Shared constants (SAMPLE_SKILL_MD, etc.) and factory functions (make_source_skill, make_sample_meta) |
| `conftest.py` | Pytest fixtures that delegate to helpers.py |

---

### Task 1: Package skeleton and CLI entry point

**Files:**
- Create: `skills/skill-packager/scripts/skill_packager/__init__.py`
- Create: `skills/skill-packager/scripts/skill_packager/__main__.py`
- Create: `skills/skill-packager/scripts/tests/__init__.py`
- Create: `skills/skill-packager/scripts/tests/helpers.py`
- Create: `skills/skill-packager/scripts/tests/conftest.py`
- Test: `skills/skill-packager/scripts/tests/test_cli.py`

- [ ] **Step 1: Write the failing test for CLI invocation**

```python
# skills/skill-packager/scripts/tests/test_cli.py
import subprocess
import sys

def test_cli_help_exits_zero():
    result = subprocess.run(
        [sys.executable, "-m", "skill_packager", "--help"],
        capture_output=True, text=True,
        cwd="skills/skill-packager/scripts"
    )
    assert result.returncode == 0
    assert "usage:" in result.stdout.lower()

def test_cli_has_subcommands():
    result = subprocess.run(
        [sys.executable, "-m", "skill_packager", "--help"],
        capture_output=True, text=True,
        cwd="skills/skill-packager/scripts"
    )
    for cmd in ["metadata", "scaffold", "build-zip", "validate", "bump-version"]:
        assert cmd in result.stdout, f"Missing subcommand: {cmd}"

def test_cli_no_args_shows_help():
    result = subprocess.run(
        [sys.executable, "-m", "skill_packager"],
        capture_output=True, text=True,
        cwd="skills/skill-packager/scripts"
    )
    # Should exit non-zero and show usage
    assert result.returncode != 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/yaniv/Documents/code/skill-packager-skill && python3 -m pytest skills/skill-packager/scripts/tests/test_cli.py -v`
Expected: FAIL — `skill_packager` module not found

- [ ] **Step 3: Create the package skeleton**

```python
# skills/skill-packager/scripts/skill_packager/__init__.py
# Empty — package marker
```

```python
# skills/skill-packager/scripts/skill_packager/__main__.py
"""Skill Packager CLI — deterministic generation for skill packaging."""
import argparse
import sys


def main():
    parser = argparse.ArgumentParser(
        prog="skill_packager",
        description="Package AI agent skills into deployment formats.",
    )
    subparsers = parser.add_subparsers(dest="command")

    # metadata
    meta_parser = subparsers.add_parser(
        "metadata", help="Extract metadata from skill directory"
    )
    meta_parser.add_argument(
        "--skill-path", action="append", required=True,
        help="Path to a skill directory (repeatable for multi-skill)",
    )

    # scaffold
    scaffold_parser = subparsers.add_parser(
        "scaffold", help="Generate repo directory structure from metadata"
    )
    scaffold_parser.add_argument("--metadata", required=True, help="Path to meta.json")
    scaffold_parser.add_argument("--output", required=True, help="Output directory")

    # build-zip
    zip_parser = subparsers.add_parser(
        "build-zip", help="Build cross-platform zip with path hygiene"
    )
    zip_parser.add_argument("--skill-dir", required=True, help="Skill directory to zip")
    zip_parser.add_argument("--output", help="Output zip path")
    zip_parser.add_argument("--version", help="Version to write into VERSION file")

    # validate
    validate_parser = subparsers.add_parser(
        "validate", help="Validate generated repo structure"
    )
    validate_parser.add_argument("repo_dir", help="Path to repo directory")
    validate_parser.add_argument(
        "--json", action="store_true", dest="json_output",
        help="Machine-readable JSON output",
    )

    # bump-version
    bump_parser = subparsers.add_parser(
        "bump-version", help="Propagate version to all locations"
    )
    bump_parser.add_argument("repo_dir", help="Path to repo directory")
    bump_parser.add_argument("version", help="New version string")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    if args.command == "metadata":
        from .metadata import run_metadata
        run_metadata(args)
    elif args.command == "scaffold":
        from .scaffold import run_scaffold
        run_scaffold(args)
    elif args.command == "build-zip":
        from .build_zip import run_build_zip
        run_build_zip(args)
    elif args.command == "validate":
        from .validate import run_validate
        run_validate(args)
    elif args.command == "bump-version":
        from .bump_version import run_bump_version
        run_bump_version(args)


if __name__ == "__main__":
    main()
```

Create stub modules so imports don't fail:

```python
# skills/skill-packager/scripts/skill_packager/metadata.py
def run_metadata(args):
    raise NotImplementedError("metadata not yet implemented")
```

```python
# skills/skill-packager/scripts/skill_packager/scaffold.py
def run_scaffold(args):
    raise NotImplementedError("scaffold not yet implemented")
```

```python
# skills/skill-packager/scripts/skill_packager/build_zip.py
def run_build_zip(args):
    raise NotImplementedError("build-zip not yet implemented")
```

```python
# skills/skill-packager/scripts/skill_packager/validate.py
def run_validate(args):
    raise NotImplementedError("validate not yet implemented")
```

```python
# skills/skill-packager/scripts/skill_packager/bump_version.py
def run_bump_version(args):
    raise NotImplementedError("bump-version not yet implemented")
```

```python
# skills/skill-packager/scripts/tests/__init__.py
# Empty
```

```python
# skills/skill-packager/scripts/tests/helpers.py
"""Shared constants and factory functions for skill_packager tests.

Import from here in test files: `from tests.helpers import ...`
Do NOT import from conftest.py — conftest is pytest infrastructure only.
"""
import json
from pathlib import Path


SAMPLE_SKILL_MD = """\
---
name: test-skill
description: >
  A test skill for unit testing.
  Use when testing the skill packager.
metadata:
  author: Test Author
  version: "1.0.0"
license: MIT
---

# Test Skill

You do test things.
"""

SAMPLE_SKILL_MD_NO_VERSION = """\
---
name: bare-skill
description: A minimal skill.
---

# Bare Skill

Minimal.
"""


def make_sample_meta(tmp_path, **overrides):
    """Create a sample meta.json and return its path."""
    meta = {
        "skills": [
            {
                "name": "test-skill",
                "source_path": str(tmp_path / "source" / "test-skill"),
                "description": "A test skill for unit testing.",
                "has_scripts": True,
                "has_references": True,
                "has_assets": False,
                "has_agents": False,
                "has_evals": False,
            }
        ],
        "plugin_name": "test-skill",
        "marketplace_name": "test-skill-marketplace",
        "display_name": "Test Skill",
        "description": "A test skill for unit testing.",
        "version": "1.0.0",
        "author_name": "Test Author",
        "author_email": "test@example.com",
        "github_owner": "test-owner",
        "github_repo": "test-skill-repo",
        "license": "MIT",
        "keywords": ["test"],
        "category": "development",
        "formats": ["universal"],
        "targets": ["claude-desktop", "claude-code", "cursor"],
    }
    meta.update(overrides)
    meta_path = tmp_path / "meta.json"
    meta_path.write_text(json.dumps(meta, indent=2))
    return meta_path


def make_source_skill(tmp_path, name="test-skill", skill_md=SAMPLE_SKILL_MD,
                      with_scripts=True, with_references=True):
    """Create a source skill directory with optional subdirs."""
    skill_dir = tmp_path / "source" / name
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(skill_md)
    (skill_dir / "VERSION").write_text("1.0.0")
    if with_scripts:
        scripts_dir = skill_dir / "scripts"
        scripts_dir.mkdir()
        (scripts_dir / "helper.py").write_text(
            '#!/usr/bin/env python3\nprint("hello from ${CLAUDE_SKILL_DIR}/scripts/helper.py")\n'
        )
    if with_references:
        refs_dir = skill_dir / "references"
        refs_dir.mkdir()
        (refs_dir / "guide.md").write_text(
            "# Guide\n\nSee [helper](${CLAUDE_SKILL_DIR}/scripts/helper.py) for details.\n"
        )
    return skill_dir
```

```python
# skills/skill-packager/scripts/tests/conftest.py
"""Pytest fixtures — delegates to helpers.py for constants and factory functions."""
import pytest
from tests.helpers import make_source_skill, make_sample_meta


@pytest.fixture
def sample_meta(tmp_path):
    """Fixture that creates a source skill and matching meta.json."""
    skill_dir = make_source_skill(tmp_path)
    meta_path = make_sample_meta(tmp_path)
    return meta_path, tmp_path
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/yaniv/Documents/code/skill-packager-skill && python3 -m pytest skills/skill-packager/scripts/tests/test_cli.py -v`
Expected: 3 tests PASS

- [ ] **Step 5: Commit**

```bash
git add skills/skill-packager/scripts/
git commit -m "feat: add skill_packager package skeleton with CLI entry point

Argparse-based CLI with 5 subcommands: metadata, scaffold, build-zip,
validate, bump-version. Stub implementations for each module.
Shared test fixtures in conftest.py."
```

---

### Task 2: Templates module

**Files:**
- Create: `skills/skill-packager/scripts/skill_packager/templates.py`
- Test: `skills/skill-packager/scripts/tests/test_templates.py`

This is the largest single file — all file templates converted from `references/formats.md` `{{variable}}` syntax to Python `{variable}` format strings.

- [ ] **Step 1: Write the failing test**

```python
# skills/skill-packager/scripts/tests/test_templates.py
import json
from skill_packager import templates


def _sample_vars():
    return {
        "skill_name": "proof-engine",
        "skill_description": "Create formal proofs",
        "plugin_name": "proof-engine",
        "marketplace_name": "proof-engine-marketplace",
        "display_name": "Proof Engine",
        "version": "1.0.0",
        "author_name": "Test Author",
        "author_email": "test@example.com",
        "github_owner": "test-owner",
        "github_repo": "proof-engine-skill",
        "license": "MIT",
        "keywords_json": '["proof", "verification"]',
        "category": "development",
        "repo_url": "https://github.com/test-owner/proof-engine-skill",
        "zip_filename": "proof-engine-skill.zip",
        "year": "2026",
        "date": "2026-04-07",
    }


def test_claude_plugin_json_is_valid():
    rendered = templates.CLAUDE_PLUGIN_JSON.format(**_sample_vars())
    data = json.loads(rendered)
    assert data["name"] == "proof-engine"
    assert data["version"] == "1.0.0"
    assert data["skills"] == "./skills"


def test_marketplace_json_is_valid():
    rendered = templates.MARKETPLACE_JSON.format(**_sample_vars())
    data = json.loads(rendered)
    assert data["metadata"]["version"] == "1.0.0"
    assert data["metadata"]["pluginRoot"] == "./proof-engine"


def test_cursor_plugin_json_is_valid():
    rendered = templates.CURSOR_PLUGIN_JSON.format(**_sample_vars())
    data = json.loads(rendered)
    assert data["skills"] == "./proof-engine/skills"
    assert data["displayName"] == "Proof Engine"


def test_release_yml_has_zip_step():
    rendered = templates.RELEASE_YML.format(**_sample_vars())
    assert "python3 tools/build-zip.py" in rendered
    assert "softprops/action-gh-release" in rendered


def test_deploy_pages_yml_copies_static():
    rendered = templates.DEPLOY_PAGES_YML.format(**_sample_vars())
    assert "install-claude-desktop.html" in rendered
    assert "actions/deploy-pages" in rendered


def test_install_html_has_deep_link():
    rendered = templates.INSTALL_HTML.format(**_sample_vars())
    assert "claude://claude.ai/customize/plugins/new" in rendered
    assert "test-owner" in rendered


def test_license_mit_has_author():
    rendered = templates.LICENSE_MIT.format(**_sample_vars())
    assert "Test Author" in rendered
    assert "2026" in rendered


def test_versioning_md_references_plugin():
    rendered = templates.VERSIONING_MD.format(**_sample_vars())
    assert "proof-engine" in rendered
    assert "bump-version.py" in rendered


def test_bump_version_py_is_valid_python():
    rendered = templates.BUMP_VERSION_PY.format(**_sample_vars())
    compile(rendered, "bump_version.py", "exec")  # syntax check


def test_build_zip_py_is_valid_python():
    rendered = templates.BUILD_ZIP_PY.format(**_sample_vars())
    compile(rendered, "build_zip.py", "exec")  # syntax check


def test_readme_stub_has_marker():
    rendered = templates.README_STUB.format(**_sample_vars())
    assert "<!-- SKILL_PACKAGER: REPLACE THIS -->" in rendered


def test_changelog_stub_has_marker():
    rendered = templates.CHANGELOG_STUB.format(**_sample_vars())
    assert "<!-- SKILL_PACKAGER: REPLACE THIS -->" in rendered


def test_all_templates_render_without_key_error():
    """Every template must render cleanly with the sample vars."""
    v = _sample_vars()
    for name in dir(templates):
        obj = getattr(templates, name)
        if isinstance(obj, str) and name.isupper() and "{" in obj:
            try:
                obj.format(**v)
            except KeyError as e:
                raise AssertionError(f"Template {name} has unresolved key: {e}")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/yaniv/Documents/code/skill-packager-skill && python3 -m pytest skills/skill-packager/scripts/tests/test_templates.py -v`
Expected: FAIL — `templates` module has no attributes

- [ ] **Step 3: Write templates.py**

Convert every template from `references/formats.md`. The file will be ~400 lines. Key conversions:
- `{{variable}}` → `{variable}` (Python format string)
- `{{keywords}}` → `{keywords_json}` (pre-serialized JSON array)
- Literal `{` and `}` in YAML/JSON/bash → `{{` and `}}` (escaped for Python format strings)
- `${{ github.xxx }}` in GitHub Actions YAML → `${{{{ github.xxx }}}}` (double-escaped)
- `bump-version.sh` → `bump-version.py` (per design spec)
- Release workflow uses `python3 tools/build-zip.py` instead of inline shell

The templates to create (all as module-level string constants):

1. `CLAUDE_PLUGIN_JSON` — from formats.md lines 131-144
2. `MARKETPLACE_JSON` — from formats.md lines 164-189
3. `CURSOR_PLUGIN_JSON` — from formats.md lines 217-231
4. `RELEASE_YML` — from formats.md lines 298-340, modified to call `tools/build-zip.py`
5. `DEPLOY_PAGES_YML` — from formats.md lines 557-590
6. `INSTALL_HTML` — from formats.md lines 502-552
7. `VERSIONING_MD` — from formats.md lines 404-447, updated for `.py` scripts and `meta.json`
8. `LICENSE_MIT` — from formats.md lines 470-492
9. `BUMP_VERSION_PY` — new: standalone Python script that reads `meta.json`, updates all version locations
10. `BUILD_ZIP_PY` — new: standalone Python script that reads `meta.json`, builds zip with path hygiene
11. `README_STUB` — minimal placeholder with marker comment
12. `CHANGELOG_STUB` — minimal placeholder with marker comment

**Critical for `BUMP_VERSION_PY` and `BUILD_ZIP_PY`:** These are Python scripts that will be written as files into generated repos. They must:
- Be stdlib-only Python
- Read `meta.json` from repo root (no baked-in values)
- Be syntactically valid (tested by `compile()`)
- Use `{{` and `}}` for any literal braces in the template, since the outer template uses `.format()`

For `BUMP_VERSION_PY`, the generated script must update:
- `meta.json` → `"version"` field
- Root `VERSION`
- `<plugin>/.claude-plugin/plugin.json` → `"version"`
- `.claude-plugin/marketplace.json` → `metadata.version` (if exists)
- `.cursor-plugin/plugin.json` → `"version"` (if exists)
- Each skill's `SKILL.md` → `metadata.version`
- Each skill's `VERSION`
- Each `.agents/skills/<name>/SKILL.md` and `VERSION` (if `.agents/skills/` exists)

For `BUILD_ZIP_PY`, the generated script must:
- Read `meta.json` for plugin/skill names
- Copy skill dirs to temp, strip `${CLAUDE_SKILL_DIR}/`, write VERSION
- Single skill: `<skill-name>/` at archive root
- Multi-skill: `skills/` at archive root
- Verify no `${CLAUDE_SKILL_DIR}` remains

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/yaniv/Documents/code/skill-packager-skill && python3 -m pytest skills/skill-packager/scripts/tests/test_templates.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add skills/skill-packager/scripts/skill_packager/templates.py skills/skill-packager/scripts/tests/test_templates.py
git commit -m "feat: add templates.py with all file templates as Python format strings

Converts formats.md templates to Python string constants. Includes
Claude/Cursor plugin manifests, marketplace.json, GitHub Actions
workflows, install HTML, standalone bump-version.py and build-zip.py
for generated repos, and stub templates for README/CHANGELOG."
```

---

### Task 3: Metadata extraction

**Files:**
- Modify: `skills/skill-packager/scripts/skill_packager/metadata.py`
- Test: `skills/skill-packager/scripts/tests/test_metadata.py`

- [ ] **Step 1: Write the failing tests**

```python
# skills/skill-packager/scripts/tests/test_metadata.py
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
    # Need a second source dir
    src_b = tmp_path / "source2" / "skill-b"
    src_b.mkdir(parents=True)
    (src_b / "SKILL.md").write_text(SAMPLE_SKILL_MD.replace("test-skill", "skill-b"))
    (src_b / "VERSION").write_text("1.0.0")

    result = extract_metadata([skill_a, src_b])
    assert len(result["skills"]) == 2
    # Bundle-level fields left empty for Claude to fill
    assert result["plugin_name"] == ""
    assert result["description"] == ""
    assert result["version"] == ""


def test_source_path_is_absolute(tmp_path):
    skill_dir = make_source_skill(tmp_path, name="test-skill", skill_md=SAMPLE_SKILL_MD)
    result = extract_metadata([skill_dir])
    assert os.path.isabs(result["skills"][0]["source_path"])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/yaniv/Documents/code/skill-packager-skill && python3 -m pytest skills/skill-packager/scripts/tests/test_metadata.py -v`
Expected: FAIL — `extract_skill_metadata` not importable

- [ ] **Step 3: Implement metadata.py**

```python
# skills/skill-packager/scripts/skill_packager/metadata.py
"""Extract metadata from skill directories."""
import json
import os
import re
import subprocess
import sys
from pathlib import Path


def _parse_yaml_frontmatter(text):
    """Minimal YAML frontmatter parser — handles the fields we need.

    Parses: name, description (including multi-line >), metadata.author,
    metadata.version, license. Does not handle full YAML spec.
    """
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return {}

    # Find closing ---
    end = None
    for i, line in enumerate(lines[1:], 1):
        if line.strip() == "---":
            end = i
            break
    if end is None:
        return {}

    frontmatter = {}
    current_key = None
    current_value = []
    in_metadata = False
    metadata = {}

    for line in lines[1:end]:
        stripped = line.rstrip()

        # Top-level key
        match = re.match(r"^(\w[\w-]*):\s*(.*)", stripped)
        if match:
            # Save previous key
            if current_key:
                val = " ".join(current_value).strip()
                if in_metadata:
                    metadata[current_key] = val.strip('"').strip("'")
                else:
                    frontmatter[current_key] = val.strip('"').strip("'")

            key, value = match.group(1), match.group(2)
            if key == "metadata":
                in_metadata = True
                current_key = None
                current_value = []
                continue

            in_metadata = False if not line.startswith("  ") else in_metadata
            current_key = key
            # Handle > (folded block scalar)
            if value.strip() == ">":
                current_value = []
            else:
                current_value = [value]
            continue

        # Indented key under metadata:
        meta_match = re.match(r"^  (\w[\w-]*):\s*(.*)", stripped)
        if meta_match and in_metadata:
            if current_key:
                val = " ".join(current_value).strip()
                metadata[current_key] = val.strip('"').strip("'")
            current_key = meta_match.group(1)
            current_value = [meta_match.group(2)]
            continue

        # Continuation line (for folded >)
        if current_key and stripped.startswith("  "):
            current_value.append(stripped.strip())

    # Save last key
    if current_key:
        val = " ".join(current_value).strip()
        if in_metadata:
            metadata[current_key] = val.strip('"').strip("'")
        else:
            frontmatter[current_key] = val.strip('"').strip("'")

    if metadata:
        frontmatter["metadata"] = metadata

    return frontmatter


def extract_skill_metadata(skill_dir):
    """Extract metadata from a single skill directory.

    Returns a dict with: name, source_path, description, version,
    has_scripts, has_references, has_assets, has_agents, has_evals.
    """
    skill_dir = Path(skill_dir).resolve()
    skill_md = skill_dir / "SKILL.md"

    if not skill_md.exists():
        raise FileNotFoundError(f"No SKILL.md found in {skill_dir}")

    text = skill_md.read_text(encoding="utf-8")
    fm = _parse_yaml_frontmatter(text)

    name = fm.get("name", skill_dir.name)
    description = fm.get("description", "")

    # Version: metadata.version > VERSION file > None
    version = None
    meta = fm.get("metadata", {})
    if isinstance(meta, dict) and "version" in meta:
        version = meta["version"]
    elif (skill_dir / "VERSION").exists():
        version = (skill_dir / "VERSION").read_text().strip()

    author = None
    if isinstance(meta, dict) and "author" in meta:
        author = meta["author"]

    license_val = fm.get("license", None)

    return {
        "name": name,
        "source_path": str(skill_dir),
        "description": description,
        "version": version,
        "author": author,
        "license": license_val,
        "has_scripts": (skill_dir / "scripts").is_dir(),
        "has_references": (skill_dir / "references").is_dir(),
        "has_assets": (skill_dir / "assets").is_dir(),
        "has_agents": (skill_dir / "agents").is_dir(),
        "has_evals": (skill_dir / "evals").is_dir(),
    }


def _git_config(key, cwd=None):
    """Read a git config value, return None on failure."""
    try:
        result = subprocess.run(
            ["git", "config", "--get", key],
            capture_output=True, text=True, cwd=cwd,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except FileNotFoundError:
        pass
    return None


def _git_remote_owner_repo(cwd=None):
    """Parse github owner/repo from git remote origin, return (owner, repo) or (None, None)."""
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True, text=True, cwd=cwd,
        )
        if result.returncode == 0:
            url = result.stdout.strip()
            # Handle SSH: git@github.com:owner/repo.git
            m = re.match(r"git@github\.com:([^/]+)/(.+?)(?:\.git)?$", url)
            if m:
                return m.group(1), m.group(2)
            # Handle HTTPS: https://github.com/owner/repo.git
            m = re.match(r"https://github\.com/([^/]+)/(.+?)(?:\.git)?$", url)
            if m:
                return m.group(1), m.group(2)
    except FileNotFoundError:
        pass
    return None, None


def extract_metadata(skill_paths):
    """Extract metadata from one or more skill directories.

    Returns a dict matching the meta.json schema from the design spec.
    For single-skill, auto-populates bundle-level fields.
    For multi-skill, leaves bundle-level fields empty for Claude.
    """
    skills = []
    for path in skill_paths:
        skills.append(extract_skill_metadata(path))

    is_multi = len(skills) > 1

    # Git info from first skill's directory
    first_dir = skills[0]["source_path"]
    author_name = skills[0].get("author") or _git_config("user.name", cwd=first_dir)
    author_email = _git_config("user.email", cwd=first_dir)
    github_owner, github_repo = _git_remote_owner_repo(cwd=first_dir)

    if is_multi:
        plugin_name = ""
        marketplace_name = ""
        display_name = ""
        description = ""
        version = ""
    else:
        s = skills[0]
        plugin_name = s["name"]
        marketplace_name = f"{s['name']}-marketplace"
        display_name = s["name"].replace("-", " ").title()
        description = s["description"]
        version = s["version"] or "0.1.0"

    # Build skill entries (without author/license — those are bundle-level)
    skill_entries = []
    for s in skills:
        skill_entries.append({
            "name": s["name"],
            "source_path": s["source_path"],
            "description": s["description"],
            "has_scripts": s["has_scripts"],
            "has_references": s["has_references"],
            "has_assets": s["has_assets"],
            "has_agents": s["has_agents"],
            "has_evals": s["has_evals"],
        })

    return {
        "skills": skill_entries,
        "plugin_name": plugin_name,
        "marketplace_name": marketplace_name,
        "display_name": display_name,
        "description": description,
        "version": version,
        "author_name": author_name or "",
        "author_email": author_email or "",
        "github_owner": github_owner or "",
        "github_repo": github_repo or "",
        "license": skills[0].get("license") or "MIT",
        "keywords": [],
        "category": "",
        "formats": [],
        "targets": [],
    }


def run_metadata(args):
    """CLI entry point for 'metadata' subcommand."""
    paths = [Path(p) for p in args.skill_path]
    result = extract_metadata(paths)
    print(json.dumps(result, indent=2))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/yaniv/Documents/code/skill-packager-skill && python3 -m pytest skills/skill-packager/scripts/tests/test_metadata.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add skills/skill-packager/scripts/skill_packager/metadata.py skills/skill-packager/scripts/tests/test_metadata.py
git commit -m "feat: implement metadata extraction from SKILL.md frontmatter

Parses YAML frontmatter (name, description, metadata.version, license),
detects subdirectories, reads git config for author info and remote for
github owner/repo. Multi-skill leaves bundle fields empty for Claude."
```

---

### Task 4: Scaffold — core structure generation

**Files:**
- Modify: `skills/skill-packager/scripts/skill_packager/scaffold.py`
- Test: `skills/skill-packager/scripts/tests/test_scaffold.py`

This is the largest task. Scaffold reads `meta.json`, renders templates, copies skill files, creates the directory tree.

- [ ] **Step 1: Write the failing tests**

```python
# skills/skill-packager/scripts/tests/test_scaffold.py
import json
import os
from pathlib import Path
from skill_packager.scaffold import scaffold_repo
from tests.helpers import make_source_skill, make_sample_meta, SAMPLE_SKILL_MD


def test_scaffold_universal_creates_all_dirs(tmp_path):
    make_source_skill(tmp_path)
    meta_path = make_sample_meta(tmp_path, formats=["universal"])
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
    make_source_skill(tmp_path)
    meta_path = make_sample_meta(tmp_path, formats=["universal"])
    output = tmp_path / "output"
    scaffold_repo(meta_path, output)

    skill_dir = output / "test-skill" / "skills" / "test-skill"
    assert (skill_dir / "scripts" / "helper.py").exists()
    assert (skill_dir / "references" / "guide.md").exists()


def test_scaffold_canonical_keeps_claude_skill_dir(tmp_path):
    make_source_skill(tmp_path)
    meta_path = make_sample_meta(tmp_path, formats=["universal"])
    output = tmp_path / "output"
    scaffold_repo(meta_path, output)

    # Canonical copy keeps ${CLAUDE_SKILL_DIR}/
    ref = output / "test-skill" / "skills" / "test-skill" / "references" / "guide.md"
    assert "${CLAUDE_SKILL_DIR}/" in ref.read_text()


def test_scaffold_agents_skills_is_stripped_copy(tmp_path):
    make_source_skill(tmp_path)
    meta_path = make_sample_meta(tmp_path, formats=["universal"])
    output = tmp_path / "output"
    scaffold_repo(meta_path, output)

    # .agents/skills/ copy has ${CLAUDE_SKILL_DIR}/ stripped
    ref = output / ".agents" / "skills" / "test-skill" / "references" / "guide.md"
    assert "${CLAUDE_SKILL_DIR}/" not in ref.read_text()
    assert "scripts/helper.py" in ref.read_text()  # relative path preserved


def test_scaffold_claude_plugin_only(tmp_path):
    make_source_skill(tmp_path)
    meta_path = make_sample_meta(tmp_path, formats=["claude-plugin"])
    output = tmp_path / "output"
    scaffold_repo(meta_path, output)

    assert (output / "test-skill" / ".claude-plugin" / "plugin.json").exists()
    assert (output / "test-skill" / "skills" / "test-skill" / "SKILL.md").exists()
    assert not (output / ".cursor-plugin").exists()
    assert not (output / ".agents").exists()
    assert not (output / ".github").exists()


def test_scaffold_agent_skills_standalone(tmp_path):
    make_source_skill(tmp_path)
    meta_path = make_sample_meta(tmp_path, formats=["agent-skills"])
    output = tmp_path / "output"
    scaffold_repo(meta_path, output)

    # Skills copied directly, stripped
    skill_md = output / ".agents" / "skills" / "test-skill" / "SKILL.md"
    assert skill_md.exists()
    assert "${CLAUDE_SKILL_DIR}/" not in skill_md.read_text()
    # No plugin tree
    assert not (output / "test-skill").exists()


def test_scaffold_aborts_if_output_exists_non_empty(tmp_path):
    make_source_skill(tmp_path)
    meta_path = make_sample_meta(tmp_path, formats=["universal"])
    output = tmp_path / "output"
    output.mkdir()
    (output / "existing-file.txt").write_text("I exist")

    import pytest
    with pytest.raises(SystemExit):
        scaffold_repo(meta_path, output)


def test_scaffold_json_files_are_valid(tmp_path):
    make_source_skill(tmp_path)
    meta_path = make_sample_meta(tmp_path, formats=["universal"])
    output = tmp_path / "output"
    scaffold_repo(meta_path, output)

    for json_file in output.rglob("*.json"):
        json.loads(json_file.read_text())  # Must not raise


def test_scaffold_tools_are_executable(tmp_path):
    make_source_skill(tmp_path)
    meta_path = make_sample_meta(tmp_path, formats=["universal"])
    output = tmp_path / "output"
    scaffold_repo(meta_path, output)

    assert os.access(output / "tools" / "bump-version.py", os.X_OK)
    assert os.access(output / "tools" / "build-zip.py", os.X_OK)


def test_scaffold_version_consistent(tmp_path):
    make_source_skill(tmp_path)
    meta_path = make_sample_meta(tmp_path, formats=["universal"])
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
    """Skills without metadata.version in SKILL.md get it injected."""
    from tests.helpers import SAMPLE_SKILL_MD_NO_VERSION
    make_source_skill(tmp_path, skill_md=SAMPLE_SKILL_MD_NO_VERSION,
                      with_scripts=False, with_references=False)
    meta_path = make_sample_meta(tmp_path, formats=["claude-plugin"])
    output = tmp_path / "output"
    scaffold_repo(meta_path, output)

    skill_md = (output / "test-skill" / "skills" / "test-skill" / "SKILL.md").read_text()
    assert 'version: "1.0.0"' in skill_md
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/yaniv/Documents/code/skill-packager-skill && python3 -m pytest skills/skill-packager/scripts/tests/test_scaffold.py -v`
Expected: FAIL — `scaffold_repo` not importable

- [ ] **Step 3: Implement scaffold.py**

```python
# skills/skill-packager/scripts/skill_packager/scaffold.py
"""Generate repo directory structure from metadata."""
import json
import os
import re
import shutil
import stat
import sys
from pathlib import Path

from . import templates


def _strip_claude_skill_dir(text):
    """Remove ${CLAUDE_SKILL_DIR}/ from text."""
    return text.replace("${CLAUDE_SKILL_DIR}/", "")


def _copy_skill_files(source_path, dest_path):
    """Copy all skill files from source to dest, preserving structure."""
    source = Path(source_path)
    dest = Path(dest_path)
    dest.mkdir(parents=True, exist_ok=True)

    for item in source.iterdir():
        src_item = source / item.name
        dst_item = dest / item.name
        if src_item.is_dir():
            shutil.copytree(src_item, dst_item)
        else:
            shutil.copy2(src_item, dst_item)


def _ensure_skill_md_has_version(skill_md_path, version):
    """If SKILL.md lacks metadata.version, inject it into the frontmatter.

    This ensures bump-version can later find and update the version field.
    Uses line-based manipulation to avoid regex issues with multiple --- markers.
    """
    path = Path(skill_md_path)
    if not path.exists():
        return
    content = path.read_text(encoding="utf-8")
    # Already has metadata.version — nothing to do
    if re.search(r'^\s+version:\s*["\']', content, re.MULTILINE):
        return

    lines = content.split("\n")
    has_metadata_section = any(line.strip() == "metadata:" for line in lines)

    if has_metadata_section:
        # Insert version line right after "metadata:"
        for i, line in enumerate(lines):
            if line.strip() == "metadata:":
                lines.insert(i + 1, f'  version: "{version}"')
                break
    else:
        # No metadata section — insert "metadata:\n  version:" before closing ---
        dash_count = 0
        for i, line in enumerate(lines):
            if line.strip() == "---":
                dash_count += 1
                if dash_count == 2:
                    lines.insert(i, f'metadata:\n  version: "{version}"')
                    break

    path.write_text("\n".join(lines), encoding="utf-8")


def _copy_skill_files_stripped(source_path, dest_path):
    """Copy skill files with ${CLAUDE_SKILL_DIR}/ stripped from .md files."""
    _copy_skill_files(source_path, dest_path)
    # Strip from all .md files
    for md_file in Path(dest_path).rglob("*.md"):
        content = md_file.read_text(encoding="utf-8")
        stripped = _strip_claude_skill_dir(content)
        if stripped != content:
            md_file.write_text(stripped, encoding="utf-8")


def _make_executable(path):
    """Add executable permission to a file."""
    st = os.stat(path)
    os.chmod(path, st.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def _template_vars(meta):
    """Build the variable dict for template rendering."""
    return {
        "skill_name": meta["skills"][0]["name"] if len(meta["skills"]) == 1 else "",
        "skill_description": meta["description"],
        "plugin_name": meta["plugin_name"],
        "marketplace_name": meta["marketplace_name"],
        "display_name": meta["display_name"],
        "version": meta["version"],
        "author_name": meta["author_name"],
        "author_email": meta["author_email"],
        "github_owner": meta["github_owner"],
        "github_repo": meta["github_repo"],
        "license": meta["license"],
        "keywords_json": json.dumps(meta.get("keywords", [])),
        "category": meta.get("category", ""),
        "repo_url": f"https://github.com/{meta['github_owner']}/{meta['github_repo']}",
        "zip_filename": f"{meta['github_repo']}.zip",
        "year": str(__import__("datetime").date.today().year),
        "date": str(__import__("datetime").date.today()),
    }


def scaffold_repo(meta_path, output_dir):
    """Generate repo directory structure from metadata.

    Args:
        meta_path: Path to meta.json
        output_dir: Output directory (must not exist or be empty)
    """
    meta_path = Path(meta_path)
    output_dir = Path(output_dir)

    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    formats = meta.get("formats", [])
    if not formats:
        print("Error: no formats specified in metadata", file=sys.stderr)
        sys.exit(1)

    # Check output dir
    if output_dir.exists() and any(output_dir.iterdir()):
        print(f"Error: output directory {output_dir} exists and is non-empty", file=sys.stderr)
        sys.exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)

    tvars = _template_vars(meta)

    # Determine what to generate based on formats
    is_universal = "universal" in formats
    needs_claude_plugin = is_universal or "claude-plugin" in formats or "claude-marketplace" in formats
    needs_marketplace = is_universal or "claude-marketplace" in formats
    needs_cursor = is_universal or "cursor-plugin" in formats
    needs_agent_skills = is_universal or "agent-skills" in formats
    needs_ci = is_universal
    needs_tools = is_universal

    # 1. Write meta.json to output
    shutil.copy2(meta_path, output_dir / "meta.json")

    # 2. Copy skill payload into plugin tree (if any plugin format)
    if needs_claude_plugin or needs_cursor:
        plugin_name = meta["plugin_name"]
        for skill in meta["skills"]:
            dest = output_dir / plugin_name / "skills" / skill["name"]
            _copy_skill_files(skill["source_path"], dest)
            # Write VERSION into skill dir
            (dest / "VERSION").write_text(meta["version"])
            # Ensure SKILL.md has metadata.version so bump-version can update it
            _ensure_skill_md_has_version(dest / "SKILL.md", meta["version"])

    # 3. Claude plugin manifest
    if needs_claude_plugin:
        plugin_json_dir = output_dir / meta["plugin_name"] / ".claude-plugin"
        plugin_json_dir.mkdir(parents=True, exist_ok=True)
        (plugin_json_dir / "plugin.json").write_text(
            templates.CLAUDE_PLUGIN_JSON.format(**tvars)
        )

    # 4. Marketplace manifest
    if needs_marketplace:
        marketplace_dir = output_dir / ".claude-plugin"
        marketplace_dir.mkdir(parents=True, exist_ok=True)
        (marketplace_dir / "marketplace.json").write_text(
            templates.MARKETPLACE_JSON.format(**tvars)
        )

    # 5. Cursor plugin manifest
    if needs_cursor:
        cursor_dir = output_dir / ".cursor-plugin"
        cursor_dir.mkdir(parents=True, exist_ok=True)
        (cursor_dir / "plugin.json").write_text(
            templates.CURSOR_PLUGIN_JSON.format(**tvars)
        )

    # 6. .agents/skills/ — always a stripped copy
    if needs_agent_skills:
        for skill in meta["skills"]:
            if needs_claude_plugin:
                # Agent-skills alongside plugin tree — copy from source, strip
                dest = output_dir / ".agents" / "skills" / skill["name"]
                _copy_skill_files_stripped(skill["source_path"], dest)
                (dest / "VERSION").write_text(meta["version"])
            else:
                # Standalone agent-skills format — this IS the payload
                dest = output_dir / ".agents" / "skills" / skill["name"]
                _copy_skill_files_stripped(skill["source_path"], dest)
                (dest / "VERSION").write_text(meta["version"])

    # 7. CI/CD workflows
    if needs_ci:
        workflows_dir = output_dir / ".github" / "workflows"
        workflows_dir.mkdir(parents=True, exist_ok=True)
        (workflows_dir / "release.yml").write_text(
            templates.RELEASE_YML.format(**tvars)
        )
        (workflows_dir / "deploy-pages.yml").write_text(
            templates.DEPLOY_PAGES_YML.format(**tvars)
        )

    # 8. Tools
    if needs_tools:
        tools_dir = output_dir / "tools"
        tools_dir.mkdir(parents=True, exist_ok=True)
        bump_path = tools_dir / "bump-version.py"
        bump_path.write_text(templates.BUMP_VERSION_PY.format(**tvars))
        _make_executable(bump_path)
        zip_path = tools_dir / "build-zip.py"
        zip_path.write_text(templates.BUILD_ZIP_PY.format(**tvars))
        _make_executable(zip_path)

    # 9. Static files
    if needs_ci:
        static_dir = output_dir / "static"
        static_dir.mkdir(parents=True, exist_ok=True)
        (static_dir / "install-claude-desktop.html").write_text(
            templates.INSTALL_HTML.format(**tvars)
        )

    # 10. Root files (universal only)
    if is_universal:
        (output_dir / "VERSION").write_text(meta["version"])
        (output_dir / "VERSIONING.md").write_text(
            templates.VERSIONING_MD.format(**tvars)
        )
        (output_dir / "LICENSE").write_text(
            templates.LICENSE_MIT.format(**tvars)
        )
        (output_dir / "README.md").write_text(
            templates.README_STUB.format(**tvars)
        )
        (output_dir / "CHANGELOG.md").write_text(
            templates.CHANGELOG_STUB.format(**tvars)
        )


def run_scaffold(args):
    """CLI entry point for 'scaffold' subcommand."""
    scaffold_repo(args.metadata, args.output)
    print(f"Scaffolded repo at {args.output}")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/yaniv/Documents/code/skill-packager-skill && python3 -m pytest skills/skill-packager/scripts/tests/test_scaffold.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add skills/skill-packager/scripts/skill_packager/scaffold.py skills/skill-packager/scripts/tests/test_scaffold.py
git commit -m "feat: implement scaffold subcommand for repo generation

Generates directory structures for all 5 scaffold formats (universal,
claude-plugin, claude-marketplace, cursor-plugin, agent-skills).
Copies skill files, renders templates, creates stripped .agents/skills/
copies, sets tool permissions. Aborts on non-empty output dir."
```

---

### Task 5: Build-zip with path hygiene

**Files:**
- Modify: `skills/skill-packager/scripts/skill_packager/build_zip.py`
- Test: `skills/skill-packager/scripts/tests/test_build_zip.py`

- [ ] **Step 1: Write the failing tests**

```python
# skills/skill-packager/scripts/tests/test_build_zip.py
import json
import zipfile
from pathlib import Path
from skill_packager.build_zip import build_zip
from tests.helpers import make_source_skill, make_sample_meta, SAMPLE_SKILL_MD


def _make_scaffolded_skill(tmp_path, meta_overrides=None):
    """Create a minimal scaffolded repo with one skill for zip testing."""
    make_source_skill(tmp_path)
    overrides = {"formats": ["claude-plugin"]}
    if meta_overrides:
        overrides.update(meta_overrides)
    meta_path = make_sample_meta(tmp_path, **overrides)

    # Simulate scaffold output
    repo = tmp_path / "repo"
    plugin_dir = repo / "test-skill" / "skills" / "test-skill"
    plugin_dir.mkdir(parents=True)
    src = tmp_path / "source" / "test-skill"
    for item in src.iterdir():
        if item.is_dir():
            import shutil
            shutil.copytree(item, plugin_dir / item.name)
        else:
            import shutil
            shutil.copy2(item, plugin_dir / item.name)

    # Write meta.json
    import shutil
    shutil.copy2(meta_path, repo / "meta.json")
    return repo


def test_build_zip_creates_zip_file(tmp_path):
    repo = _make_scaffolded_skill(tmp_path)
    skill_dir = repo / "test-skill" / "skills" / "test-skill"
    output = tmp_path / "dist" / "test.zip"
    build_zip(skill_dir, output)
    assert output.exists()
    assert zipfile.is_zipfile(output)


def test_build_zip_single_skill_root_layout(tmp_path):
    repo = _make_scaffolded_skill(tmp_path)
    skill_dir = repo / "test-skill" / "skills" / "test-skill"
    output = tmp_path / "dist" / "test.zip"
    build_zip(skill_dir, output)

    with zipfile.ZipFile(output) as zf:
        names = zf.namelist()
        # Single skill: <skill-name>/ at root
        assert any(n.startswith("test-skill/") for n in names)
        assert any(n == "test-skill/SKILL.md" for n in names)


def test_build_zip_strips_claude_skill_dir(tmp_path):
    repo = _make_scaffolded_skill(tmp_path)
    skill_dir = repo / "test-skill" / "skills" / "test-skill"
    output = tmp_path / "dist" / "test.zip"
    build_zip(skill_dir, output)

    with zipfile.ZipFile(output) as zf:
        for name in zf.namelist():
            if name.endswith(".md"):
                content = zf.read(name).decode("utf-8")
                assert "${CLAUDE_SKILL_DIR}/" not in content, f"Found in {name}"


def test_build_zip_writes_version(tmp_path):
    repo = _make_scaffolded_skill(tmp_path)
    skill_dir = repo / "test-skill" / "skills" / "test-skill"
    output = tmp_path / "dist" / "test.zip"
    build_zip(skill_dir, output, version="2.0.0")

    with zipfile.ZipFile(output) as zf:
        version = zf.read("test-skill/VERSION").decode("utf-8").strip()
        assert version == "2.0.0"


def test_build_zip_preserves_scripts(tmp_path):
    repo = _make_scaffolded_skill(tmp_path)
    skill_dir = repo / "test-skill" / "skills" / "test-skill"
    output = tmp_path / "dist" / "test.zip"
    build_zip(skill_dir, output)

    with zipfile.ZipFile(output) as zf:
        assert "test-skill/scripts/helper.py" in zf.namelist()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/yaniv/Documents/code/skill-packager-skill && python3 -m pytest skills/skill-packager/scripts/tests/test_build_zip.py -v`
Expected: FAIL — `build_zip` not importable

- [ ] **Step 3: Implement build_zip.py**

```python
# skills/skill-packager/scripts/skill_packager/build_zip.py
"""Build cross-platform zip with path hygiene."""
import json
import os
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path


def _strip_claude_skill_dir(directory):
    """Strip ${CLAUDE_SKILL_DIR}/ from all .md files in directory."""
    for md_file in Path(directory).rglob("*.md"):
        content = md_file.read_text(encoding="utf-8")
        stripped = content.replace("${CLAUDE_SKILL_DIR}/", "")
        if stripped != content:
            md_file.write_text(stripped, encoding="utf-8")


def _verify_no_claude_skill_dir(directory):
    """Verify no ${CLAUDE_SKILL_DIR} remains in any .md file."""
    for md_file in Path(directory).rglob("*.md"):
        content = md_file.read_text(encoding="utf-8")
        if "${CLAUDE_SKILL_DIR}" in content:
            raise ValueError(
                f"${'{'}CLAUDE_SKILL_DIR{'}'} still present in {md_file}"
            )


def build_zip(skill_dir, output_path, version=None):
    """Build a zip from a skill directory with path hygiene.

    Args:
        skill_dir: Path to skill directory (single skill) or skills parent dir (multi-skill)
        output_path: Where to write the zip file
        version: If provided, write this into VERSION files
    """
    skill_dir = Path(skill_dir).resolve()
    output_path = Path(output_path).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Determine if this is a single skill or multi-skill
    # Single skill: skill_dir contains SKILL.md directly
    # Multi-skill: skill_dir contains subdirectories with SKILL.md
    is_single = (skill_dir / "SKILL.md").exists()

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        if is_single:
            # Single skill: <skill-name>/ at archive root
            skill_name = skill_dir.name
            dest = tmp_path / skill_name
            shutil.copytree(skill_dir, dest)
            _strip_claude_skill_dir(dest)
            if version:
                (dest / "VERSION").write_text(version)
            _verify_no_claude_skill_dir(dest)
            # Create zip
            with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for root, dirs, files in os.walk(dest):
                    for f in files:
                        file_path = Path(root) / f
                        arcname = str(file_path.relative_to(tmp_path))
                        zf.write(file_path, arcname)
        else:
            # Multi-skill: skills/ at archive root
            dest = tmp_path / "skills"
            dest.mkdir()
            for sub in skill_dir.iterdir():
                if sub.is_dir() and (sub / "SKILL.md").exists():
                    skill_dest = dest / sub.name
                    shutil.copytree(sub, skill_dest)
                    _strip_claude_skill_dir(skill_dest)
                    if version:
                        (skill_dest / "VERSION").write_text(version)
            _verify_no_claude_skill_dir(dest)
            with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for root, dirs, files in os.walk(dest):
                    for f in files:
                        file_path = Path(root) / f
                        arcname = str(file_path.relative_to(tmp_path))
                        zf.write(file_path, arcname)


def run_build_zip(args):
    """CLI entry point for 'build-zip' subcommand."""
    build_zip(args.skill_dir, args.output, version=args.version)
    print(f"Built zip: {args.output}")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/yaniv/Documents/code/skill-packager-skill && python3 -m pytest skills/skill-packager/scripts/tests/test_build_zip.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add skills/skill-packager/scripts/skill_packager/build_zip.py skills/skill-packager/scripts/tests/test_build_zip.py
git commit -m "feat: implement build-zip with path hygiene

Copies skill dir to temp, strips \${CLAUDE_SKILL_DIR}/ from .md files,
writes VERSION if provided, creates zip. Single skill uses <name>/ at
archive root, multi-skill uses skills/ wrapper. Verifies no
\${CLAUDE_SKILL_DIR} remains post-strip."
```

---

### Task 6: Validate subcommand

**Files:**
- Modify: `skills/skill-packager/scripts/skill_packager/validate.py`
- Test: `skills/skill-packager/scripts/tests/test_validate.py`

- [ ] **Step 1: Write the failing tests**

```python
# skills/skill-packager/scripts/tests/test_validate.py
import json
from pathlib import Path
from skill_packager.validate import validate_repo
from skill_packager.scaffold import scaffold_repo
from tests.helpers import make_source_skill, make_sample_meta, SAMPLE_SKILL_MD


def _scaffold_valid_repo(tmp_path, formats=None):
    """Helper: scaffold a valid universal repo for validation testing."""
    make_source_skill(tmp_path)
    meta_path = make_sample_meta(tmp_path, formats=formats or ["universal"])
    output = tmp_path / "repo"
    scaffold_repo(meta_path, output)
    # Replace README/CHANGELOG stubs so validation passes
    (output / "README.md").write_text("# Test Skill\n\nReal content here.\n")
    (output / "CHANGELOG.md").write_text("# Changelog\n\n## [1.0.0]\n\nInitial.\n")
    return output


def test_validate_passes_on_valid_universal_repo(tmp_path):
    repo = _scaffold_valid_repo(tmp_path)
    results = validate_repo(repo)
    assert all(r["passed"] for r in results), \
        f"Failed: {[r for r in results if not r['passed']]}"


def test_validate_detects_invalid_json(tmp_path):
    repo = _scaffold_valid_repo(tmp_path)
    # Break a JSON file
    (repo / ".cursor-plugin" / "plugin.json").write_text("{invalid json")
    results = validate_repo(repo)
    json_checks = [r for r in results if "json" in r["check"].lower()]
    assert any(not r["passed"] for r in json_checks)


def test_validate_detects_version_mismatch(tmp_path):
    repo = _scaffold_valid_repo(tmp_path)
    # Change version in one place
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
    make_source_skill(tmp_path)
    meta_path = make_sample_meta(tmp_path, formats=["claude-plugin"])
    output = tmp_path / "repo"
    scaffold_repo(meta_path, output)
    results = validate_repo(output)
    check_names = [r["check"] for r in results]
    # Should NOT check for release.yml, README stub, CHANGELOG stub
    assert not any("release" in c.lower() for c in check_names)
    assert not any("readme" in c.lower() for c in check_names)


def test_validate_json_output(tmp_path):
    repo = _scaffold_valid_repo(tmp_path)
    results = validate_repo(repo)
    # Each result should be JSON-serializable
    json.dumps(results)
    assert all("check" in r and "passed" in r for r in results)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/yaniv/Documents/code/skill-packager-skill && python3 -m pytest skills/skill-packager/scripts/tests/test_validate.py -v`
Expected: FAIL — `validate_repo` not importable

- [ ] **Step 3: Implement validate.py**

```python
# skills/skill-packager/scripts/skill_packager/validate.py
"""Format-aware validation for generated repos."""
import json
import sys
from pathlib import Path


def _check_json_valid(repo_dir):
    """Check all .json files parse correctly."""
    results = []
    for json_file in Path(repo_dir).rglob("*.json"):
        try:
            json.loads(json_file.read_text(encoding="utf-8"))
            results.append({
                "check": f"JSON valid: {json_file.relative_to(repo_dir)}",
                "passed": True,
            })
        except (json.JSONDecodeError, ValueError) as e:
            results.append({
                "check": f"JSON valid: {json_file.relative_to(repo_dir)}",
                "passed": False,
                "detail": str(e),
            })
    return results


def _check_version_consistency(repo_dir, meta):
    """Check version is consistent across all version-bearing files."""
    results = []
    expected = meta["version"]
    plugin_name = meta["plugin_name"]

    locations = []

    # Root VERSION
    version_file = repo_dir / "VERSION"
    if version_file.exists():
        locations.append(("VERSION", version_file.read_text().strip()))

    # meta.json version
    meta_file = repo_dir / "meta.json"
    if meta_file.exists():
        m = json.loads(meta_file.read_text())
        locations.append(("meta.json", m.get("version", "")))

    # Inner plugin.json
    inner = repo_dir / plugin_name / ".claude-plugin" / "plugin.json"
    if inner.exists():
        data = json.loads(inner.read_text())
        locations.append((f"{plugin_name}/.claude-plugin/plugin.json", data.get("version", "")))

    # Marketplace.json
    marketplace = repo_dir / ".claude-plugin" / "marketplace.json"
    if marketplace.exists():
        data = json.loads(marketplace.read_text())
        locations.append((".claude-plugin/marketplace.json", data.get("metadata", {}).get("version", "")))

    # Cursor plugin.json
    cursor = repo_dir / ".cursor-plugin" / "plugin.json"
    if cursor.exists():
        data = json.loads(cursor.read_text())
        locations.append((".cursor-plugin/plugin.json", data.get("version", "")))

    # Skill VERSION files and SKILL.md metadata.version
    for skill in meta.get("skills", []):
        skill_dir = repo_dir / plugin_name / "skills" / skill["name"]
        sv = skill_dir / "VERSION"
        if sv.exists():
            locations.append((f"{plugin_name}/skills/{skill['name']}/VERSION", sv.read_text().strip()))
        # Parse metadata.version from SKILL.md frontmatter
        skill_md = skill_dir / "SKILL.md"
        if skill_md.exists():
            import re as _re
            match = _re.search(r'^\s+version:\s*["\']([^"\']+)["\']',
                              skill_md.read_text(encoding="utf-8"),
                              _re.MULTILINE)
            if match:
                locations.append((f"{plugin_name}/skills/{skill['name']}/SKILL.md", match.group(1)))

    if not locations:
        return results

    mismatches = [(loc, ver) for loc, ver in locations if ver != expected]
    if mismatches:
        detail = "; ".join(f"{loc}={ver}" for loc, ver in mismatches)
        results.append({
            "check": "Version consistency",
            "passed": False,
            "detail": f"Expected {expected}, found mismatches: {detail}",
        })
    else:
        results.append({
            "check": "Version consistency",
            "passed": True,
        })

    return results


def _check_skill_paths(repo_dir, meta):
    """Check that manifest skill paths resolve to actual SKILL.md files."""
    results = []
    plugin_name = meta["plugin_name"]

    # Check inner Claude plugin manifest
    inner = repo_dir / plugin_name / ".claude-plugin" / "plugin.json"
    if inner.exists():
        data = json.loads(inner.read_text())
        skills_path = data.get("skills", "")
        # Resolve relative to plugin dir
        resolved = (repo_dir / plugin_name / skills_path).resolve()
        if not resolved.is_dir():
            results.append({
                "check": f"Skills path resolves: {plugin_name}/.claude-plugin/plugin.json",
                "passed": False,
                "detail": f"Path does not exist: {resolved}",
            })
        else:
            has_skills = any((resolved / d / "SKILL.md").exists()
                           for d in resolved.iterdir() if d.is_dir())
            results.append({
                "check": f"Skills path resolves: {plugin_name}/.claude-plugin/plugin.json",
                "passed": has_skills,
                "detail": "" if has_skills else f"No SKILL.md found under {resolved}",
            })

    # Check root Cursor plugin manifest
    cursor = repo_dir / ".cursor-plugin" / "plugin.json"
    if cursor.exists():
        data = json.loads(cursor.read_text())
        skills_path = data.get("skills", "")
        # Resolve relative to repo root
        resolved = (repo_dir / skills_path).resolve()
        if not resolved.is_dir():
            results.append({
                "check": "Skills path resolves: .cursor-plugin/plugin.json",
                "passed": False,
                "detail": f"Path does not exist: {resolved}",
            })
        else:
            has_skills = any((resolved / d / "SKILL.md").exists()
                           for d in resolved.iterdir() if d.is_dir())
            results.append({
                "check": "Skills path resolves: .cursor-plugin/plugin.json",
                "passed": has_skills,
                "detail": "" if has_skills else f"No SKILL.md found under {resolved}",
            })

    return results


def _check_agents_skills(repo_dir):
    """Check .agents/skills/ entries resolve."""
    results = []
    agents_dir = repo_dir / ".agents" / "skills"
    if not agents_dir.exists():
        return results

    for entry in agents_dir.iterdir():
        if entry.is_symlink():
            target_exists = entry.resolve().exists()
            results.append({
                "check": f".agents/skills/{entry.name} symlink resolves",
                "passed": target_exists,
            })
        elif entry.is_dir():
            has_skill = (entry / "SKILL.md").exists()
            results.append({
                "check": f".agents/skills/{entry.name} directory has SKILL.md",
                "passed": has_skill,
            })

    return results


def validate_repo(repo_dir):
    """Validate a generated repo. Returns list of check results.

    Each result: {"check": str, "passed": bool, "detail"?: str}
    """
    repo_dir = Path(repo_dir).resolve()

    # Read meta.json to determine format
    meta_file = repo_dir / "meta.json"
    if not meta_file.exists():
        return [{"check": "meta.json exists", "passed": False,
                 "detail": "No meta.json found — cannot determine format"}]

    try:
        meta = json.loads(meta_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, ValueError) as e:
        return [{"check": "meta.json is valid JSON", "passed": False,
                 "detail": f"Cannot parse meta.json: {e}"}]

    formats = meta.get("formats", [])
    is_universal = "universal" in formats

    results = []

    # Always: JSON validity
    results.extend(_check_json_valid(repo_dir))

    # Always: skill paths resolve
    results.extend(_check_skill_paths(repo_dir, meta))

    # Always: version consistency
    results.extend(_check_version_consistency(repo_dir, meta))

    # Format-specific checks
    if is_universal or "agent-skills" in formats:
        results.extend(_check_agents_skills(repo_dir))

    if is_universal:
        # release.yml exists and references correct paths
        release = repo_dir / ".github" / "workflows" / "release.yml"
        if release.exists():
            release_content = release.read_text()
            # Check it references tools/build-zip.py
            has_build_zip = "tools/build-zip.py" in release_content
            results.append({
                "check": "release.yml references tools/build-zip.py",
                "passed": has_build_zip,
                "detail": "" if has_build_zip else "release.yml does not call tools/build-zip.py",
            })
        else:
            results.append({
                "check": "release.yml exists",
                "passed": False,
            })

        # bump-version.py exists and targets all version locations
        bump_script = repo_dir / "tools" / "bump-version.py"
        if bump_script.exists():
            bump_content = bump_script.read_text()
            # Verify it reads meta.json (not baked-in values)
            reads_meta = "meta.json" in bump_content
            results.append({
                "check": "bump-version.py reads meta.json",
                "passed": reads_meta,
                "detail": "" if reads_meta else "bump-version.py does not reference meta.json",
            })
        else:
            results.append({
                "check": "bump-version.py exists",
                "passed": False,
            })

        # README is not a stub
        readme = repo_dir / "README.md"
        if readme.exists():
            content = readme.read_text()
            is_stub = "<!-- SKILL_PACKAGER: REPLACE THIS -->" in content
            results.append({
                "check": "README.md is not a stub",
                "passed": not is_stub,
                "detail": "Contains stub marker" if is_stub else "",
            })

        # CHANGELOG is not a stub
        changelog = repo_dir / "CHANGELOG.md"
        if changelog.exists():
            content = changelog.read_text()
            is_stub = "<!-- SKILL_PACKAGER: REPLACE THIS -->" in content
            results.append({
                "check": "CHANGELOG.md is not a stub",
                "passed": not is_stub,
                "detail": "Contains stub marker" if is_stub else "",
            })

    return results


def run_validate(args):
    """CLI entry point for 'validate' subcommand."""
    results = validate_repo(args.repo_dir)

    if args.json_output:
        print(json.dumps(results, indent=2))
    else:
        all_passed = True
        for r in results:
            status = "PASS" if r["passed"] else "FAIL"
            if not r["passed"]:
                all_passed = False
            detail = f" — {r.get('detail', '')}" if r.get("detail") else ""
            print(f"  [{status}] {r['check']}{detail}")

        if all_passed:
            print(f"\nAll {len(results)} checks passed.")
        else:
            failed = sum(1 for r in results if not r["passed"])
            print(f"\n{failed}/{len(results)} checks failed.")
            sys.exit(1)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/yaniv/Documents/code/skill-packager-skill && python3 -m pytest skills/skill-packager/scripts/tests/test_validate.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add skills/skill-packager/scripts/skill_packager/validate.py skills/skill-packager/scripts/tests/test_validate.py
git commit -m "feat: implement format-aware validate subcommand

Reads meta.json to determine format, runs checks appropriate to that
format. Validates JSON parsing, version consistency across all locations,
skill path resolution, .agents/skills/ entries, and stub detection.
Supports --json output mode."
```

---

### Task 7: Bump-version subcommand

**Files:**
- Modify: `skills/skill-packager/scripts/skill_packager/bump_version.py`
- Test: `skills/skill-packager/scripts/tests/test_bump_version.py`

- [ ] **Step 1: Write the failing tests**

```python
# skills/skill-packager/scripts/tests/test_bump_version.py
import json
from pathlib import Path
from skill_packager.bump_version import bump_version
from skill_packager.scaffold import scaffold_repo
from tests.helpers import make_source_skill, make_sample_meta, SAMPLE_SKILL_MD


def _scaffold_repo(tmp_path, formats=None):
    make_source_skill(tmp_path)
    meta_path = make_sample_meta(tmp_path, formats=formats or ["universal"])
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
    data = json.loads(
        (repo / "test-skill" / ".claude-plugin" / "plugin.json").read_text()
    )
    assert data["version"] == "2.0.0"


def test_bump_updates_marketplace_json(tmp_path):
    repo = _scaffold_repo(tmp_path)
    bump_version(repo, "2.0.0")
    data = json.loads(
        (repo / ".claude-plugin" / "marketplace.json").read_text()
    )
    assert data["metadata"]["version"] == "2.0.0"


def test_bump_updates_cursor_json(tmp_path):
    repo = _scaffold_repo(tmp_path)
    bump_version(repo, "2.0.0")
    data = json.loads(
        (repo / ".cursor-plugin" / "plugin.json").read_text()
    )
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
    """claude-plugin format has no marketplace/cursor — should not crash."""
    repo = _scaffold_repo(tmp_path, formats=["claude-plugin"])
    bump_version(repo, "2.0.0")
    # Should succeed without error
    meta = json.loads((repo / "meta.json").read_text())
    assert meta["version"] == "2.0.0"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/yaniv/Documents/code/skill-packager-skill && python3 -m pytest skills/skill-packager/scripts/tests/test_bump_version.py -v`
Expected: FAIL — `bump_version` not importable

- [ ] **Step 3: Implement bump_version.py**

```python
# skills/skill-packager/scripts/skill_packager/bump_version.py
"""Propagate version to all locations in a generated repo."""
import json
import re
import sys
from pathlib import Path


def _update_json_version(path, version, json_path=None):
    """Update a version field in a JSON file.

    Args:
        path: Path to JSON file
        version: New version string
        json_path: Dot-separated path to version field (e.g., "metadata.version").
                   If None, updates top-level "version".
    """
    if not path.exists():
        return False

    data = json.loads(path.read_text(encoding="utf-8"))

    if json_path:
        parts = json_path.split(".")
        obj = data
        for part in parts[:-1]:
            obj = obj[part]
        obj[parts[-1]] = version
    else:
        data["version"] = version

    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return True


def _update_skill_md_version(path, version):
    """Update metadata.version in SKILL.md YAML frontmatter."""
    if not path.exists():
        return False

    content = path.read_text(encoding="utf-8")
    # Match version: "X.Y.Z" in frontmatter
    updated = re.sub(
        r'(version:\s*["\'])[\d]+\.[\d]+\.[\d]+(["\'])',
        rf'\g<1>{version}\g<2>',
        content,
    )
    if updated != content:
        path.write_text(updated, encoding="utf-8")
        return True
    return False


def bump_version(repo_dir, version):
    """Update version in all locations discovered via meta.json.

    Args:
        repo_dir: Path to repo root (must contain meta.json)
        version: New version string (e.g., "2.0.0")
    """
    repo_dir = Path(repo_dir).resolve()
    meta_path = repo_dir / "meta.json"

    if not meta_path.exists():
        print("Error: no meta.json found in repo", file=sys.stderr)
        sys.exit(1)

    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    plugin_name = meta["plugin_name"]
    updated = []

    # 1. meta.json
    _update_json_version(meta_path, version)
    updated.append("meta.json")

    # 2. Root VERSION
    version_file = repo_dir / "VERSION"
    if version_file.exists():
        version_file.write_text(version)
        updated.append("VERSION")

    # 3. Inner plugin.json
    inner = repo_dir / plugin_name / ".claude-plugin" / "plugin.json"
    if _update_json_version(inner, version):
        updated.append(f"{plugin_name}/.claude-plugin/plugin.json")

    # 4. Marketplace json
    marketplace = repo_dir / ".claude-plugin" / "marketplace.json"
    if _update_json_version(marketplace, version, "metadata.version"):
        updated.append(".claude-plugin/marketplace.json")

    # 5. Cursor plugin.json
    cursor = repo_dir / ".cursor-plugin" / "plugin.json"
    if _update_json_version(cursor, version):
        updated.append(".cursor-plugin/plugin.json")

    # 6-7. Per-skill: SKILL.md and VERSION
    for skill in meta.get("skills", []):
        skill_dir = repo_dir / plugin_name / "skills" / skill["name"]
        if _update_skill_md_version(skill_dir / "SKILL.md", version):
            updated.append(f"{plugin_name}/skills/{skill['name']}/SKILL.md")
        sv = skill_dir / "VERSION"
        if sv.exists():
            sv.write_text(version)
            updated.append(f"{plugin_name}/skills/{skill['name']}/VERSION")

    # 8. .agents/skills/ copies (if they exist)
    agents_dir = repo_dir / ".agents" / "skills"
    if agents_dir.exists():
        for skill in meta.get("skills", []):
            agent_skill = agents_dir / skill["name"]
            if agent_skill.is_dir() and not agent_skill.is_symlink():
                if _update_skill_md_version(agent_skill / "SKILL.md", version):
                    updated.append(f".agents/skills/{skill['name']}/SKILL.md")
                asv = agent_skill / "VERSION"
                if asv.exists():
                    asv.write_text(version)
                    updated.append(f".agents/skills/{skill['name']}/VERSION")

    return updated


def run_bump_version(args):
    """CLI entry point for 'bump-version' subcommand."""
    updated = bump_version(args.repo_dir, args.version)
    for loc in updated:
        print(f"  Updated: {loc}")
    print(f"\nVersion {args.version} propagated to {len(updated)} locations.")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/yaniv/Documents/code/skill-packager-skill && python3 -m pytest skills/skill-packager/scripts/tests/test_bump_version.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add skills/skill-packager/scripts/skill_packager/bump_version.py skills/skill-packager/scripts/tests/test_bump_version.py
git commit -m "feat: implement bump-version subcommand

Reads meta.json to discover all version locations. Updates meta.json,
VERSION files, plugin.json, marketplace.json (metadata.version),
cursor plugin.json, SKILL.md frontmatter, and .agents/skills/ copies.
Format-aware — skips files that don't exist for the scaffolded format."
```

---

### Task 8: Integration test — full round-trip

**Files:**
- Create: `skills/skill-packager/scripts/tests/test_integration.py`

This test exercises the full workflow: metadata → scaffold → validate → bump-version → build-zip.

- [ ] **Step 1: Write the integration test**

```python
# skills/skill-packager/scripts/tests/test_integration.py
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
    # 1. Create source skill
    skill_dir = make_source_skill(tmp_path)

    # 2. Extract metadata
    partial = extract_metadata([skill_dir])

    # 3. Fill in remaining fields (simulating what Claude does)
    partial["github_owner"] = "test-owner"
    partial["github_repo"] = "test-skill-repo"
    partial["formats"] = ["universal"]
    partial["targets"] = ["claude-desktop", "cursor"]
    partial["keywords"] = ["test"]
    partial["category"] = "development"
    meta_path = tmp_path / "meta.json"
    meta_path.write_text(json.dumps(partial, indent=2))

    # 4. Scaffold
    output = tmp_path / "output"
    scaffold_repo(meta_path, output)

    # 5. Replace stubs (simulating what Claude does)
    (output / "README.md").write_text("# Test Skill\n\nA real readme.\n")
    (output / "CHANGELOG.md").write_text("# Changelog\n\n## [1.0.0]\n\nFirst release.\n")

    # 6. Validate — should all pass
    results = validate_repo(output)
    failed = [r for r in results if not r["passed"]]
    assert not failed, f"Validation failed: {failed}"

    # 7. Bump version
    updated = bump_version(output, "1.1.0")
    assert len(updated) > 5  # Should update many locations

    # Re-validate after bump
    results = validate_repo(output)
    failed = [r for r in results if not r["passed"]]
    assert not failed, f"Post-bump validation failed: {failed}"

    # 8. Build zip
    skill_dir_in_repo = output / "test-skill" / "skills" / "test-skill"
    zip_path = tmp_path / "dist" / "test.zip"
    build_zip(skill_dir_in_repo, zip_path, version="1.1.0")

    assert zip_path.exists()
    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
        assert "test-skill/SKILL.md" in names
        # Verify path hygiene
        for name in names:
            if name.endswith(".md"):
                content = zf.read(name).decode()
                assert "${CLAUDE_SKILL_DIR}" not in content
        # Verify version
        v = zf.read("test-skill/VERSION").decode().strip()
        assert v == "1.1.0"


def test_full_round_trip_cli(tmp_path):
    """Test the CLI interface end-to-end via subprocess."""
    skill_dir = make_source_skill(tmp_path)
    scripts_dir = str(Path(__file__).resolve().parent.parent)

    # metadata
    result = subprocess.run(
        [sys.executable, "-m", "skill_packager", "metadata",
         "--skill-path", str(skill_dir)],
        capture_output=True, text=True, cwd=scripts_dir,
    )
    assert result.returncode == 0
    meta = json.loads(result.stdout)
    assert meta["skills"][0]["name"] == "test-skill"

    # Fill gaps and save
    meta["github_owner"] = "test-owner"
    meta["github_repo"] = "test-skill-repo"
    meta["formats"] = ["claude-plugin"]
    meta["keywords"] = ["test"]
    meta["category"] = "development"
    meta_path = tmp_path / "meta.json"
    meta_path.write_text(json.dumps(meta, indent=2))

    # scaffold
    output = tmp_path / "output"
    result = subprocess.run(
        [sys.executable, "-m", "skill_packager", "scaffold",
         "--metadata", str(meta_path), "--output", str(output)],
        capture_output=True, text=True, cwd=scripts_dir,
    )
    assert result.returncode == 0

    # validate
    result = subprocess.run(
        [sys.executable, "-m", "skill_packager", "validate", str(output), "--json"],
        capture_output=True, text=True, cwd=scripts_dir,
    )
    assert result.returncode == 0
    results = json.loads(result.stdout)
    assert all(r["passed"] for r in results)


def test_generated_bump_version_py_works(tmp_path):
    """Test the generated tools/bump-version.py actually bumps versions."""
    # Scaffold a universal repo
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

    # Run the generated bump-version.py
    result = subprocess.run(
        [sys.executable, str(output / "tools" / "bump-version.py"), str(output), "3.0.0"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr

    # Verify versions were actually bumped
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

    # Run the generated build-zip.py
    result = subprocess.run(
        [sys.executable, str(output / "tools" / "build-zip.py"), "--version", "1.0.0"],
        capture_output=True, text=True, cwd=str(output),
    )
    assert result.returncode == 0, result.stderr

    # Find the zip and verify it
    zips = list(output.glob("dist/*.zip"))
    assert len(zips) == 1
    with zipfile.ZipFile(zips[0]) as zf:
        names = zf.namelist()
        assert any("SKILL.md" in n for n in names)
        # Verify path hygiene
        for name in names:
            if name.endswith(".md"):
                content = zf.read(name).decode()
                assert "${CLAUDE_SKILL_DIR}" not in content
```

- [ ] **Step 2: Run the integration test**

Run: `cd /Users/yaniv/Documents/code/skill-packager-skill && python3 -m pytest skills/skill-packager/scripts/tests/test_integration.py -v`
Expected: All tests PASS

- [ ] **Step 3: Run the full test suite**

Run: `cd /Users/yaniv/Documents/code/skill-packager-skill && python3 -m pytest skills/skill-packager/scripts/tests/ -v`
Expected: All tests PASS across all test files

- [ ] **Step 4: Commit**

```bash
git add skills/skill-packager/scripts/tests/test_integration.py
git commit -m "test: add full round-trip integration tests

Tests metadata → scaffold → validate → bump-version → build-zip flow
for both the Python API and CLI subprocess interface."
```

---

### Task 9: Update SKILL.md to use scripts

**Files:**
- Modify: `skills/skill-packager/SKILL.md`

The existing SKILL.md (200 lines) needs Step 4 and Step 5 updated to use the new scripts instead of manual file generation. Per the design spec:
- Step 4: use `metadata`, `scaffold`, then Claude writes README/CHANGELOG
- Step 5: run `validate`
- Remove detailed file-by-file generation instructions
- Keep high-level principles (single source of truth, path hygiene rationale)

- [ ] **Step 1: Read current SKILL.md**

Read the full file to understand what to change. Focus on Step 4 (generation process — lines ~74-156) and Step 5 (verify — lines ~158-172).

- [ ] **Step 2: Rewrite Step 4**

Replace the "Generation process" section (starting from "### Generation process") with script-based workflow. Keep the "### Output directory" section and "### README generation" section. Remove the "### Universal repo structure" duplicate (scaffold handles this now) and the detailed bash commands for copying/stripping.

New Step 4 content:

```markdown
### Generation process

Use the bundled scripts to handle deterministic generation:

#### 1. Extract metadata from source skill(s)

```bash
# Single skill:
python3 ${CLAUDE_SKILL_DIR}/scripts/skill_packager metadata \
  --skill-path /path/to/skill > /tmp/partial-meta.json

# Multi-skill:
python3 ${CLAUDE_SKILL_DIR}/scripts/skill_packager metadata \
  --skill-path /path/to/skill-a --skill-path /path/to/skill-b > /tmp/partial-meta.json
```

Read the output JSON. Fill in any empty fields: `github_repo`, `formats`, `keywords`, `category`, `targets`. For multi-skill: also fill `plugin_name`, `marketplace_name`, `display_name`, `description`, `version`. Write the complete metadata to `meta.json`.

#### 2. Scaffold the repo

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/skill_packager scaffold \
  --metadata meta.json --output ./my-skill-repo/
```

This creates the full directory structure, copies skill files, renders all manifests, and creates the `.agents/skills/` stripped copy.

#### 3. Write README.md and CHANGELOG.md

These are the creative parts that require judgment. Read `${CLAUDE_SKILL_DIR}/references/platforms.md` for the per-platform installation instructions template.

The scaffolded README.md and CHANGELOG.md contain `<!-- SKILL_PACKAGER: REPLACE THIS -->` markers. Replace the entire file content with real content.

#### 4. Build zip (if needed)

For formats that need a zip (ZIP, ChatGPT/Manus, Codex CLI):

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/skill_packager build-zip \
  --skill-dir ./my-skill-repo/<plugin-name>/skills/<skill-name> \
  --output dist/<skill-name>.zip
```
```

- [ ] **Step 3: Rewrite Step 5**

Replace the manual checklist with:

```markdown
## Step 5: Verify the output

Run the validation script:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/skill_packager validate ./my-skill-repo/
```

This checks JSON validity, version consistency, skill path resolution, and stub detection. Fix any failures and rerun until all checks pass.
```

- [ ] **Step 4: Remove redundant content**

Remove:
- The detailed universal repo directory tree (now in the spec and handled by scaffold)
- The bash commands for `cp -r`, `find ... -exec sed`, `chmod +x`
- The manual file-by-file verification checklist
- The `cat ... | python3 -m json.tool` instruction

Keep:
- High-level principles (single source of truth, path hygiene rationale, dual manifests explanation)
- Edge cases section (unchanged — Claude still needs this guidance)
- README generation reference to `platforms.md`

- [ ] **Step 5: Commit**

```bash
git add skills/skill-packager/SKILL.md
git commit -m "refactor: update SKILL.md to use bundled scripts

Step 4 now uses metadata/scaffold/build-zip scripts instead of manual
file generation from formats.md templates. Step 5 uses validate script.
Removes 80+ lines of bash commands and file-by-file instructions while
keeping high-level principles and edge case guidance."
```

---

### Task 10: Run evals and verify end-to-end

This task verifies the updated skill works by running the existing eval test cases.

- [ ] **Step 1: Run the full test suite one final time**

Run: `cd /Users/yaniv/Documents/code/skill-packager-skill && python3 -m pytest skills/skill-packager/scripts/tests/ -v --tb=short`
Expected: All tests PASS

- [ ] **Step 2: Manually test the CLI**

Create a minimal test skill and run the full workflow:

```bash
# Create a tiny test skill
mkdir -p /tmp/test-packager/skills/demo-skill
cat > /tmp/test-packager/skills/demo-skill/SKILL.md << 'EOF'
---
name: demo-skill
description: A demo skill for testing the packager.
metadata:
  author: Test
  version: "0.1.0"
---

# Demo Skill

You demonstrate things.
EOF

# Run metadata
python3 skills/skill-packager/scripts/skill_packager metadata \
  --skill-path /tmp/test-packager/skills/demo-skill

# (manually fill gaps in meta.json, then scaffold, validate, etc.)
```

- [ ] **Step 3: Commit any fixes**

If the manual test reveals issues, fix them and commit.

- [ ] **Step 4: Final commit with all tests passing**

```bash
git status
# Ensure everything is committed and clean
```
