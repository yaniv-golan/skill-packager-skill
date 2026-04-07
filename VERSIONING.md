# Versioning

This project uses [Semantic Versioning](https://semver.org/) (`MAJOR.MINOR.PATCH`).

## Version Source of Truth

The canonical version lives in `meta.json` (and the root `VERSION` file) at the repo root. All other version locations are updated from it.

## Version Locations

The version appears in these files (all managed by the bump script):

1. `meta.json` — source of truth
2. `VERSION` — plain-text copy at repo root
3. `skill-packager/.claude-plugin/plugin.json` — `"version"` field
4. `.claude-plugin/marketplace.json` — `metadata.version` (if marketplace format enabled)
5. `.cursor-plugin/plugin.json` — `"version"` field (if Cursor format enabled)
6. `skill-packager/skills/*/SKILL.md` — `metadata.version` in YAML frontmatter
7. `skill-packager/skills/*/VERSION` — copied from root
8. `.agents/skills/` copies (if they exist)

## Bumping the Version

```bash
# Set a new version and propagate to all locations:
python3 tools/bump-version.py . 0.2.0

# Or from the repo root with current directory:
python3 tools/bump-version.py . 0.2.0
```

## Release Process

```bash
# 1. Bump version
python3 tools/bump-version.py . X.Y.Z
# 2. Update CHANGELOG.md with release notes
# 3. Commit
git commit -am "chore: bump version to X.Y.Z"
# 4. Tag and push
git tag vX.Y.Z
git push origin main --tags
```

CI automatically creates a GitHub Release with a zip for all platforms.
