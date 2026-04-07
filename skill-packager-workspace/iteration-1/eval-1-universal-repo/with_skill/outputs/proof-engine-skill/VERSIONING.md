# Versioning

This project uses [Semantic Versioning](https://semver.org/) (`MAJOR.MINOR.PATCH`).

## Version Source of Truth

The canonical version lives in the `VERSION` file at the repo root. All other version locations are updated from it.

## Version Locations

The version appears in these files (all managed by the bump script):

1. `VERSION` — source of truth
2. `proof-engine/.claude-plugin/plugin.json` → `"version"` field
3. `.cursor-plugin/plugin.json` → `"version"` field
4. `.claude-plugin/marketplace.json` → `"version"` field in metadata
5. `proof-engine/skills/proof-engine/SKILL.md` → `metadata.version` in YAML frontmatter
6. `proof-engine/skills/proof-engine/VERSION` → copied from root

## Bumping the Version

```bash
# Set a new version and propagate to all locations:
./tools/bump-version.sh 0.2.0

# Or edit VERSION manually, then propagate:
./tools/bump-version.sh
```

## Release Process

```bash
# 1. Bump version
./tools/bump-version.sh X.Y.Z
# 2. Update CHANGELOG.md with release notes
# 3. Commit
git commit -am "chore: bump version to X.Y.Z"
# 4. Tag and push
git tag vX.Y.Z
git push origin main --tags
```

CI automatically creates a GitHub Release with a zip for all platforms.
