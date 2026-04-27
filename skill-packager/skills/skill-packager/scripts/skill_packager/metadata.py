"""Extract metadata from SKILL.md frontmatter and skill directory structure."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Minimal YAML frontmatter parser
# ---------------------------------------------------------------------------

def _parse_yaml_frontmatter(text: str) -> Dict[str, Any]:
    """Parse YAML frontmatter delimited by ``---`` lines.

    Handles:
    - Top-level ``key: value`` pairs
    - ``metadata:`` nested block with indented keys
    - Folded block scalar (``>``) for multi-line values
    - Quoted and unquoted values
    """
    lines = text.split("\n")
    # Find the frontmatter block
    if not lines or lines[0].strip() != "---":
        return {}
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return {}

    fm_lines = lines[1:end]
    result: Dict[str, Any] = {}
    i = 0
    while i < len(fm_lines):
        line = fm_lines[i]
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            i += 1
            continue

        # Determine indentation level
        indent = len(line) - len(line.lstrip())

        if indent == 0:
            # Top-level key
            if ":" not in stripped:
                i += 1
                continue
            key, _, raw_value = stripped.partition(":")
            key = key.strip()
            raw_value = raw_value.strip()

            if raw_value == ">":
                # Folded block scalar: collect subsequent indented lines
                collected: list[str] = []
                i += 1
                while i < len(fm_lines):
                    nxt = fm_lines[i]
                    nxt_indent = len(nxt) - len(nxt.lstrip())
                    if nxt.strip() == "" or nxt_indent > 0:
                        collected.append(nxt.strip())
                        i += 1
                    else:
                        break
                result[key] = " ".join(part for part in collected if part)
                continue
            elif raw_value == "":
                # Possibly a nested block (like metadata:)
                nested: Dict[str, str] = {}
                i += 1
                while i < len(fm_lines):
                    nxt = fm_lines[i]
                    nxt_indent = len(nxt) - len(nxt.lstrip())
                    if nxt.strip() == "":
                        i += 1
                        continue
                    if nxt_indent > 0:
                        nk, _, nv = nxt.strip().partition(":")
                        nested[nk.strip()] = _unquote(nv.strip())
                        i += 1
                    else:
                        break
                result[key] = nested
                continue
            else:
                result[key] = _unquote(raw_value)
        i += 1

    return result


def _unquote(value: str) -> str:
    """Remove surrounding quotes from a YAML value."""
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
        return value[1:-1]
    return value


# ---------------------------------------------------------------------------
# Skill metadata extraction
# ---------------------------------------------------------------------------

def extract_skill_metadata(skill_dir: Path) -> Dict[str, Any]:
    """Extract metadata from a single skill directory.

    Returns a dict with keys: name, source_path, description, version,
    author, license, has_scripts, has_references, has_assets, has_agents,
    has_evals.
    """
    skill_dir = Path(skill_dir).resolve()
    skill_md_path = skill_dir / "SKILL.md"
    text = skill_md_path.read_text() if skill_md_path.exists() else ""
    fm = _parse_yaml_frontmatter(text)

    name = fm.get("name", skill_dir.name)
    description = fm.get("description", "")

    # Version fallback: metadata.version > VERSION file > None
    metadata_block = fm.get("metadata", {})
    if isinstance(metadata_block, dict):
        version = metadata_block.get("version")
        author = metadata_block.get("author")
    else:
        version = None
        author = None

    if not version:
        version_file = skill_dir / "VERSION"
        if version_file.exists():
            version = version_file.read_text().strip()
        else:
            version = None

    license_val = fm.get("license", "")

    return {
        "name": name,
        "source_path": str(skill_dir),
        "description": description,
        "version": version,
        "author": author or "",
        "license": license_val,
        "has_scripts": (skill_dir / "scripts").is_dir(),
        "has_references": (skill_dir / "references").is_dir(),
        "has_assets": (skill_dir / "assets").is_dir(),
        "has_agents": (skill_dir / "agents").is_dir(),
        "has_evals": (skill_dir / "evals").is_dir(),
    }


# ---------------------------------------------------------------------------
# Git helpers
# ---------------------------------------------------------------------------

def _git_config(key: str, cwd: Optional[Path] = None) -> str:
    """Read a git config value, returning empty string on failure."""
    try:
        result = subprocess.run(
            ["git", "config", "--get", key],
            capture_output=True, text=True, cwd=cwd,
        )
        return result.stdout.strip() if result.returncode == 0 else ""
    except FileNotFoundError:
        return ""


def _git_remote_owner_repo(cwd: Optional[Path] = None) -> tuple[str, str]:
    """Parse owner/repo from the git remote origin URL.

    Supports both SSH (git@github.com:owner/repo.git) and HTTPS URLs.
    Returns ("", "") on failure.
    """
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True, text=True, cwd=cwd,
        )
        if result.returncode != 0:
            return ("", "")
        url = result.stdout.strip()
    except FileNotFoundError:
        return ("", "")

    # SSH: git@github.com:owner/repo.git (no :// scheme)
    if "://" not in url and ":" in url:
        path = url.split(":")[-1]
    else:
        # HTTPS: https://github.com/owner/repo.git
        path = "/".join(url.split("/")[-2:])

    path = path.removesuffix(".git")
    parts = path.split("/")
    if len(parts) >= 2:
        return (parts[-2], parts[-1])
    return ("", "")


# ---------------------------------------------------------------------------
# Bundle metadata (skill-packager.json schema)
# ---------------------------------------------------------------------------

def extract_metadata(skill_paths: List[Path]) -> Dict[str, Any]:
    """Combine metadata from one or more skill directories.

    For a single skill, auto-populates bundle-level fields.
    For multiple skills, leaves bundle fields empty for the user to fill.
    """
    raw_skills = [extract_skill_metadata(p) for p in skill_paths]

    # Strip internal-only fields (author, license) from skill entries
    _SKILL_KEYS = (
        "name", "source_path", "description",
        "has_scripts", "has_references", "has_assets", "has_agents", "has_evals",
    )
    skills = [{k: s[k] for k in _SKILL_KEYS} for s in raw_skills]

    if len(raw_skills) == 1:
        s = raw_skills[0]
        cwd = Path(s["source_path"])
        author_name = s.get("author") or _git_config("user.name", cwd)
        author_email = _git_config("user.email", cwd)
        github_owner, github_repo = _git_remote_owner_repo(cwd)
        return {
            "skills": skills,
            "plugin_name": s["name"],
            "marketplace_name": s["name"],
            "display_name": s["name"].replace("-", " ").title(),
            "description": s["description"],
            "version": s["version"] or "",
            "author_name": author_name,
            "author_email": author_email,
            "github_owner": github_owner,
            "github_repo": github_repo,
            "license": s["license"],
            "keywords": [],
            "category": "",
            "formats": ["universal"],
            "targets": [],
        }
    else:
        return {
            "skills": skills,
            "plugin_name": "",
            "marketplace_name": "",
            "display_name": "",
            "description": "",
            "version": "",
            "author_name": "",
            "author_email": "",
            "github_owner": "",
            "github_repo": "",
            "license": "",
            "keywords": [],
            "category": "",
            "formats": ["universal"],
            "targets": [],
        }


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def run_metadata(args) -> None:
    """CLI entry: extract metadata and print JSON to stdout."""
    skill_paths = [Path(p) for p in args.skill_path]
    meta = extract_metadata(skill_paths)
    print(json.dumps(meta, indent=2))
