"""Bump version across all version locations in a scaffolded repo."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import List, Optional


NEW_MANIFEST = "skill-packager.json"
LEGACY_MANIFEST = "meta.json"


def _find_meta(repo_dir: Path):
    """Return (Path|None, is_legacy: bool). Prefers new name, falls back to legacy."""
    new = repo_dir / NEW_MANIFEST
    if new.exists():
        return new, False
    legacy = repo_dir / LEGACY_MANIFEST
    if legacy.exists():
        return legacy, True
    return None, False


def _update_json_version(path: Path, version: str, json_path: Optional[str] = None) -> bool:
    """Update version in a JSON file. Returns True if the file was updated.

    *json_path* is a dot-separated key path for nested keys
    (e.g. ``"metadata.version"``).  When ``None``, updates the top-level
    ``"version"`` key.
    """
    if not path.exists():
        return False

    data = json.loads(path.read_text())
    keys = json_path.split(".") if json_path else ["version"]

    obj = data
    for key in keys[:-1]:
        if key not in obj:
            return False
        obj = obj[key]

    obj[keys[-1]] = version
    path.write_text(json.dumps(data, indent=2) + "\n")
    return True


def _update_skill_md_version(path: Path, version: str) -> bool:
    """Regex-replace ``version: "X.Y.Z"`` in SKILL.md frontmatter.

    Returns True if the file was updated.
    """
    if not path.exists():
        return False

    text = path.read_text()
    new_text = re.sub(
        r'(version:\s*["\'])[\d]+\.[\d]+\.[\d]+(["\'])',
        rf'\g<1>{version}\2',
        text,
        count=1,
    )
    if new_text != text:
        path.write_text(new_text)
        return True
    return False


def bump_version(repo_dir: Path, version: str) -> List[str]:
    """Bump version in all known locations inside *repo_dir*.

    Returns a list of human-readable descriptions of updated locations.
    """
    repo_dir = Path(repo_dir)
    updated: List[str] = []

    # 1. skill-packager.json (or legacy meta.json) → "version"
    meta_path, is_legacy = _find_meta(repo_dir)
    if is_legacy:
        print("[deprecation] using legacy meta.json - rename to skill-packager.json before v0.3.0",
              file=sys.stderr)
    if meta_path is not None and _update_json_version(meta_path, version):
        updated.append(meta_path.name)

    # Read manifest for skill/plugin info
    meta = json.loads(meta_path.read_text()) if meta_path is not None and meta_path.exists() else {}
    plugin_name = meta.get("plugin_name", "")
    skills = meta.get("skills", [])

    # 2. Root VERSION file
    version_file = repo_dir / "VERSION"
    if version_file.exists():
        version_file.write_text(version + "\n")
        updated.append("VERSION")

    # 3. Inner plugin.json → "version"
    inner_plugin = repo_dir / plugin_name / ".claude-plugin" / "plugin.json"
    if _update_json_version(inner_plugin, version):
        updated.append(f"{plugin_name}/.claude-plugin/plugin.json")

    # 4. Marketplace marketplace.json → "metadata.version"
    marketplace = repo_dir / ".claude-plugin" / "marketplace.json"
    if _update_json_version(marketplace, version, "metadata.version"):
        updated.append(".claude-plugin/marketplace.json")

    # 5. Cursor plugin.json → "version"
    cursor = repo_dir / ".cursor-plugin" / "plugin.json"
    if _update_json_version(cursor, version):
        updated.append(".cursor-plugin/plugin.json")

    # Per-skill updates
    for skill in skills:
        sname = skill["name"] if isinstance(skill, dict) else skill

        # 6. Per-skill SKILL.md in canonical location
        skill_md = repo_dir / plugin_name / "skills" / sname / "SKILL.md"
        if _update_skill_md_version(skill_md, version):
            updated.append(f"{plugin_name}/skills/{sname}/SKILL.md")

        # 7. Per-skill VERSION file in canonical location
        skill_version = repo_dir / plugin_name / "skills" / sname / "VERSION"
        if skill_version.exists():
            skill_version.write_text(version + "\n")
            updated.append(f"{plugin_name}/skills/{sname}/VERSION")

        # 8. .agents/skills/ copies
        agents_version = repo_dir / ".agents" / "skills" / sname / "VERSION"
        if agents_version.exists():
            agents_version.write_text(version + "\n")
            updated.append(f".agents/skills/{sname}/VERSION")

        agents_skill_md = repo_dir / ".agents" / "skills" / sname / "SKILL.md"
        if _update_skill_md_version(agents_skill_md, version):
            updated.append(f".agents/skills/{sname}/SKILL.md")

    return updated


def run_bump_version(args) -> None:
    """CLI entry point for bump-version subcommand."""
    repo_dir = Path(args.repo_dir)
    version = args.version
    updated = bump_version(repo_dir, version)
    if updated:
        print(f"Updated version to {version} in {len(updated)} location(s):")
        for loc in updated:
            print(f"  - {loc}")
    else:
        print("No version files found to update.")
