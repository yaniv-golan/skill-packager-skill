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
            raise ValueError(f"${{CLAUDE_SKILL_DIR}} still present in {md_file}")


def build_zip(skill_dir, output_path, version=None):
    """Build a zip from a skill directory with path hygiene.

    Single skill: skill_dir contains SKILL.md -> <skill-name>/ at archive root
    Multi-skill: skill_dir contains subdirectories with SKILL.md -> skills/ at archive root
    """
    skill_dir = Path(skill_dir).resolve()
    output_path = Path(output_path).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    is_single = (skill_dir / "SKILL.md").exists()

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        if is_single:
            skill_name = skill_dir.name
            dest = tmp_path / skill_name
            shutil.copytree(skill_dir, dest)
            _strip_claude_skill_dir(dest)
            if version:
                (dest / "VERSION").write_text(version)
            _verify_no_claude_skill_dir(dest)
            with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for root, dirs, files in os.walk(dest):
                    for f in files:
                        file_path = Path(root) / f
                        arcname = str(file_path.relative_to(tmp_path))
                        zf.write(file_path, arcname)
        else:
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
