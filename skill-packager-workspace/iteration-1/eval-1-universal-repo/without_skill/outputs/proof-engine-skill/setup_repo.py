#!/usr/bin/env python3
"""
Setup script to finalize the proof-engine-skill repository.

Run this once after cloning or downloading the repo:

    python setup_repo.py

This script:
  - Copies claude-plugin/plugin.json to .claude/plugin.json
    (the .claude/ directory is the standard Claude Code plugin location,
    but some tools cannot create dotfiles directly)

After running, you can delete this script.
"""
import shutil
import os

def main():
    repo_root = os.path.dirname(os.path.abspath(__file__))

    # Set up .claude directory (copy claude-plugin/plugin.json -> .claude/plugin.json)
    claude_src = os.path.join(repo_root, 'claude-plugin', 'plugin.json')
    claude_dst_dir = os.path.join(repo_root, '.claude')
    claude_dst = os.path.join(claude_dst_dir, 'plugin.json')

    if os.path.exists(claude_src) and not os.path.exists(claude_dst):
        os.makedirs(claude_dst_dir, exist_ok=True)
        shutil.copy2(claude_src, claude_dst)
        print(f'  OK: .claude/plugin.json (copied from claude-plugin/)')
    elif os.path.exists(claude_dst):
        print(f'  SKIP: .claude/plugin.json already exists')
    else:
        print(f'  SKIP: claude-plugin/plugin.json not found')

    print('\nRepository setup complete.')
    print('You can now delete this setup_repo.py script.')

if __name__ == '__main__':
    main()
