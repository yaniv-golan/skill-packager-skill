#!/usr/bin/env python3
"""Sync skill-packager/skills/skill-packager/ -> .agents/skills/skill-packager/.

Mirrors canonical skill source into the .agents/ tree, excluding __pycache__.
Idempotent. Run after editing the canonical source.
"""
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC = REPO_ROOT / "skill-packager" / "skills" / "skill-packager"
DST = REPO_ROOT / ".agents" / "skills" / "skill-packager"


def main():
    if DST.exists():
        shutil.rmtree(DST)
    shutil.copytree(SRC, DST, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    print(f"Synced {SRC} -> {DST}")


if __name__ == "__main__":
    main()
