#!/usr/bin/env bash
set -euo pipefail

# Usage: ./tools/bump-version.sh [VERSION]
# If VERSION is provided, writes it to VERSION file first.
# Then propagates from VERSION to all other locations.

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if [ "${1:-}" != "" ]; then
  echo "$1" > "$REPO_ROOT/VERSION"
fi

VERSION="$(cat "$REPO_ROOT/VERSION" | tr -d '[:space:]')"
echo "Bumping to version: $VERSION"

# 1. Claude plugin manifest
sed -i '' "s/\"version\": \"[^\"]*\"/\"version\": \"$VERSION\"/" "$REPO_ROOT/proof-engine/.claude-plugin/plugin.json"

# 2. Cursor plugin manifest
sed -i '' "s/\"version\": \"[^\"]*\"/\"version\": \"$VERSION\"/" "$REPO_ROOT/.cursor-plugin/plugin.json"

# 3. Claude marketplace manifest
sed -i '' "s/\"version\": \"[^\"]*\"/\"version\": \"$VERSION\"/" "$REPO_ROOT/.claude-plugin/marketplace.json"

# 4. SKILL.md frontmatter (metadata.version)
sed -i '' "s/version: \"[^\"]*\"/version: \"$VERSION\"/" "$REPO_ROOT/proof-engine/skills/proof-engine/SKILL.md"

# 5. Skill VERSION file
cp "$REPO_ROOT/VERSION" "$REPO_ROOT/proof-engine/skills/proof-engine/VERSION"

echo "Version $VERSION propagated to all locations."
