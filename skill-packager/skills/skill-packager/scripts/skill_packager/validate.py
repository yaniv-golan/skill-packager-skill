"""Validate a skill-packager repository."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List


STUB_MARKER = "SKILL_PACKAGER: REPLACE THIS"
SKILL_MD_LINE_LIMIT = 500


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def _check_json_valid(repo_dir: Path) -> List[Dict[str, Any]]:
    """Parse every .json file under repo_dir."""
    results: List[Dict[str, Any]] = []
    for jf in sorted(repo_dir.rglob("*.json")):
        rel = str(jf.relative_to(repo_dir))
        try:
            json.loads(jf.read_text())
            results.append({"check": f"json_valid: {rel}", "passed": True})
        except (json.JSONDecodeError, ValueError) as exc:
            results.append({"check": f"json_valid: {rel}", "passed": False,
                            "message": str(exc)})
    return results


def _extract_version_from_skill_md(path: Path) -> str | None:
    """Return the version string from a SKILL.md frontmatter, or None."""
    text = path.read_text()
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            break
        m = re.match(r'\s*version:\s*["\']?([0-9][^"\']*)', lines[i])
        if m:
            return m.group(1).strip()
    return None


def _check_version_consistency(repo_dir: Path, meta: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Compare version across VERSION, meta.json, plugin.json, marketplace.json, etc."""
    results: List[Dict[str, Any]] = []
    expected = meta.get("version", "0.0.0")

    # Root VERSION file
    version_file = repo_dir / "VERSION"
    if version_file.exists():
        found = version_file.read_text().strip()
        passed = found == expected
        results.append({"check": "version_consistency: VERSION",
                         "passed": passed,
                         "message": f"expected {expected}, found {found}" if not passed else ""})

    # meta.json version (always present since we loaded it)
    meta_path = repo_dir / "meta.json"
    if meta_path.exists():
        meta_on_disk = json.loads(meta_path.read_text())
        found = meta_on_disk.get("version", "")
        passed = found == expected
        results.append({"check": "version_consistency: meta.json",
                         "passed": passed,
                         "message": f"expected {expected}, found {found}" if not passed else ""})

    # Inner plugin.json
    plugin_name = meta.get("plugin_name", "")
    inner_plugin = repo_dir / plugin_name / ".claude-plugin" / "plugin.json"
    if inner_plugin.exists():
        try:
            data = json.loads(inner_plugin.read_text())
            found = data.get("version", "")
            passed = found == expected
            results.append({"check": "version_consistency: plugin.json",
                             "passed": passed,
                             "message": f"expected {expected}, found {found}" if not passed else ""})
        except (json.JSONDecodeError, ValueError):
            pass

    # marketplace.json (version is nested under metadata.version)
    mkt = repo_dir / ".claude-plugin" / "marketplace.json"
    if mkt.exists():
        try:
            data = json.loads(mkt.read_text())
            found = data.get("metadata", {}).get("version", "")
            passed = found == expected
            results.append({"check": "version_consistency: marketplace.json",
                             "passed": passed,
                             "message": f"expected {expected}, found {found}" if not passed else ""})
        except (json.JSONDecodeError, ValueError):
            pass

    # Cursor plugin.json
    cursor_plugin = repo_dir / ".cursor-plugin" / "plugin.json"
    if cursor_plugin.exists():
        try:
            data = json.loads(cursor_plugin.read_text())
            found = data.get("version", "")
            passed = found == expected
            results.append({"check": "version_consistency: cursor plugin.json",
                             "passed": passed,
                             "message": f"expected {expected}, found {found}" if not passed else ""})
        except (json.JSONDecodeError, ValueError):
            pass  # JSON validity is caught by _check_json_valid

    # Per-skill VERSION and SKILL.md in the plugin tree
    skills = meta.get("skills", [])
    for skill in skills:
        sname = skill["name"] if isinstance(skill, dict) else skill
        skill_tree = repo_dir / plugin_name / "skills" / sname
        sv = skill_tree / "VERSION"
        if sv.exists():
            found = sv.read_text().strip()
            passed = found == expected
            results.append({"check": f"version_consistency: {sname}/VERSION",
                             "passed": passed,
                             "message": f"expected {expected}, found {found}" if not passed else ""})
        smd = skill_tree / "SKILL.md"
        if smd.exists():
            found = _extract_version_from_skill_md(smd)
            if found is not None:
                passed = found == expected
                results.append({"check": f"version_consistency: {sname}/SKILL.md",
                                 "passed": passed,
                                 "message": f"expected {expected}, found {found}" if not passed else ""})

    return results


def _check_skill_paths(repo_dir: Path, meta: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Verify that manifest skill paths resolve to SKILL.md."""
    results: List[Dict[str, Any]] = []
    plugin_name = meta.get("plugin_name", "")
    skills = meta.get("skills", [])
    for skill in skills:
        sname = skill["name"] if isinstance(skill, dict) else skill
        skill_md = repo_dir / plugin_name / "skills" / sname / "SKILL.md"
        passed = skill_md.exists()
        results.append({"check": f"skill_path: {sname}",
                         "passed": passed,
                         "message": "" if passed else f"missing {skill_md.relative_to(repo_dir)}"})
    return results


def _check_agents_skills(repo_dir: Path) -> List[Dict[str, Any]]:
    """Verify .agents/skills/ entries have SKILL.md."""
    results: List[Dict[str, Any]] = []
    agents_dir = repo_dir / ".agents" / "skills"
    if not agents_dir.exists():
        return results
    for entry in sorted(agents_dir.iterdir()):
        if entry.is_dir():
            skill_md = entry / "SKILL.md"
            passed = skill_md.exists()
            results.append({"check": f"agents_skill: {entry.name}",
                             "passed": passed,
                             "message": "" if passed else f"missing SKILL.md in .agents/skills/{entry.name}"})
    return results


def _check_skill_md_length(repo_dir: Path, meta: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Warn when SKILL.md exceeds 500 lines (NanoClaw enforces this limit)."""
    results: List[Dict[str, Any]] = []
    plugin_name = meta.get("plugin_name", "")
    skills = meta.get("skills", [])

    # Check plugin tree
    for skill in skills:
        sname = skill["name"] if isinstance(skill, dict) else skill
        skill_md = repo_dir / plugin_name / "skills" / sname / "SKILL.md"
        if skill_md.exists():
            line_count = len(skill_md.read_text().splitlines())
            if line_count > SKILL_MD_LINE_LIMIT:
                results.append({"check": f"skill_md_length: {sname}",
                                 "passed": True,
                                 "message": f"warning: SKILL.md is {line_count} lines "
                                            f"(NanoClaw enforces {SKILL_MD_LINE_LIMIT}-line limit)"})
            else:
                results.append({"check": f"skill_md_length: {sname}",
                                 "passed": True, "message": ""})

    # Check .agents/skills/ tree
    agents_dir = repo_dir / ".agents" / "skills"
    if agents_dir.exists():
        for entry in sorted(agents_dir.iterdir()):
            if entry.is_dir():
                skill_md = entry / "SKILL.md"
                if skill_md.exists():
                    line_count = len(skill_md.read_text().splitlines())
                    if line_count > SKILL_MD_LINE_LIMIT:
                        results.append({"check": f"skill_md_length: .agents/{entry.name}",
                                         "passed": True,
                                         "message": f"warning: SKILL.md is {line_count} lines "
                                                    f"(NanoClaw enforces {SKILL_MD_LINE_LIMIT}-line limit)"})

    return results


def _check_release_yml(repo_dir: Path) -> List[Dict[str, Any]]:
    """Check release.yml exists."""
    path = repo_dir / ".github" / "workflows" / "release.yml"
    passed = path.exists()
    return [{"check": "release_yml", "passed": passed,
             "message": "" if passed else "missing .github/workflows/release.yml"}]


def _check_bump_version(repo_dir: Path) -> List[Dict[str, Any]]:
    """Check bump-version.py exists."""
    path = repo_dir / "tools" / "bump-version.py"
    passed = path.exists()
    return [{"check": "bump_version_script", "passed": passed,
             "message": "" if passed else "missing tools/bump-version.py"}]


def _check_stub_readme(repo_dir: Path) -> List[Dict[str, Any]]:
    """Detect stub marker in README.md."""
    readme = repo_dir / "README.md"
    if not readme.exists():
        return [{"check": "readme_stub", "passed": False, "message": "README.md missing"}]
    text = readme.read_text()
    has_stub = STUB_MARKER in text
    return [{"check": "readme_stub", "passed": not has_stub,
             "message": "README.md still contains stub marker" if has_stub else ""}]


def _check_stub_changelog(repo_dir: Path) -> List[Dict[str, Any]]:
    """Detect stub marker in CHANGELOG.md."""
    cl = repo_dir / "CHANGELOG.md"
    if not cl.exists():
        return [{"check": "changelog_stub", "passed": False, "message": "CHANGELOG.md missing"}]
    text = cl.read_text()
    has_stub = STUB_MARKER in text
    return [{"check": "changelog_stub", "passed": not has_stub,
             "message": "CHANGELOG.md still contains stub marker" if has_stub else ""}]


# ---------------------------------------------------------------------------
# Main validation function
# ---------------------------------------------------------------------------

def validate_repo(repo_dir: Path) -> List[Dict[str, Any]]:
    """Run format-aware validation checks and return a list of result dicts."""
    repo_dir = Path(repo_dir)
    results: List[Dict[str, Any]] = []

    # Load meta.json for format awareness
    meta_path = repo_dir / "meta.json"
    if not meta_path.exists():
        return [{"check": "meta_json_exists", "passed": False,
                 "message": "meta.json not found in repo root"}]
    meta = json.loads(meta_path.read_text())
    formats = meta.get("formats", ["universal"])

    # Always run: JSON validity, skill paths, version consistency
    results.extend(_check_json_valid(repo_dir))
    results.extend(_check_skill_paths(repo_dir, meta))
    results.extend(_check_skill_md_length(repo_dir, meta))
    results.extend(_check_version_consistency(repo_dir, meta))

    # Universal or agent-skills: .agents/skills/ checks
    if any(f in formats for f in ("universal", "agent-skills")):
        results.extend(_check_agents_skills(repo_dir))

    # Universal only: release.yml, bump-version.py, README/CHANGELOG stub detection
    if "universal" in formats:
        results.extend(_check_release_yml(repo_dir))
        results.extend(_check_bump_version(repo_dir))
        results.extend(_check_stub_readme(repo_dir))
        results.extend(_check_stub_changelog(repo_dir))

    return results


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def run_validate(args) -> None:
    """CLI entry: validate a skill repository."""
    repo_dir = Path(args.repo_dir)
    results = validate_repo(repo_dir)

    if args.json_output:
        print(json.dumps(results, indent=2))
    else:
        failed = [r for r in results if not r["passed"]]
        for r in results:
            status = "PASS" if r["passed"] else "FAIL"
            msg = f"  -- {r.get('message', '')}" if r.get("message") else ""
            print(f"  [{status}] {r['check']}{msg}")
        print()
        if failed:
            print(f"{len(failed)} check(s) failed.")
            sys.exit(1)
        else:
            print(f"All {len(results)} checks passed.")
