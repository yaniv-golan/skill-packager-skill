# Deployment Format Templates

This reference contains the exact file templates for each deployment format. Variables in `{{double braces}}` should be replaced with actual values from the skill metadata.

## Table of Contents

- [Common variables](#common-variables)
- [ZIP format](#zip-format)
- [Claude plugin](#claude-plugin)
- [Claude marketplace](#claude-marketplace)
- [Cursor plugin](#cursor-plugin)
- [Cursor marketplace](#cursor-marketplace)
- [Agent Skills standard](#agent-skills-standard)
- [NanoClaw marketplace](#nanoclaw-marketplace)
- [GitHub Actions release workflow](#github-actions-release-workflow)
- [Version management](#version-management)
- [Universal repo — full file list](#universal-repo--full-file-list)

---

## Common variables

These are used across all templates. Collect them in Step 2 of the main skill.

| Variable | Example | Notes |
|----------|---------|-------|
| `{{skill-name}}` | `proof-engine` | From SKILL.md `name` field |
| `{{skill-description}}` | `Create formal proofs...` | From SKILL.md `description` |
| `{{plugin-name}}` | `proof-engine` | Usually same as skill name; for multi-skill, user chooses |
| `{{marketplace-name}}` | `proof-engine-marketplace` | `{{plugin-name}}-marketplace` |
| `{{version}}` | `0.1.0` | From metadata or VERSION file |
| `{{author-name}}` | `Yaniv Golan` | From metadata or git config |
| `{{author-email}}` | `yaniv@golan.name` | From git config |
| `{{github-owner}}` | `yaniv-golan` | GitHub username or org |
| `{{github-repo}}` | `proof-engine-skill` | Repository name |
| `{{license}}` | `MIT` | From SKILL.md or default |
| `{{keywords}}` | `["proof", "verification"]` | JSON array of strings |
| `{{category}}` | `development` | One of: development, productivity, data, creative, devops |
| `{{repo-url}}` | `https://github.com/yaniv-golan/proof-engine-skill` | Full repo URL |
| `{{zip-filename}}` | `proof-engine-skill.zip` | `{{github-repo}}.zip` |

For multi-skill packages, also collect:
| Variable | Example |
|----------|---------|
| `{{plugin-description}}` | Overall description for the plugin |
| `{{skill-names}}` | Array of all skill names |

---

## ZIP format

The ZIP contains the full skill folder(s) — SKILL.md, scripts, references, assets, agents, and any other files — with `${CLAUDE_SKILL_DIR}/` path references stripped for cross-platform compatibility.

### Why path hygiene is needed

In Claude Code, `${CLAUDE_SKILL_DIR}` is expanded at runtime to the skill's absolute path on disk. Skills use it for:
- **Script invocations**: `python3 ${CLAUDE_SKILL_DIR}/scripts/validate.py proof.py`
- **Markdown links to references**: `[api.md](${CLAUDE_SKILL_DIR}/references/api.md)`
- **Cross-references between files**: reference files linking to other reference files

Other platforms (Manus, ChatGPT, Codex, Windsurf, etc.) don't expand this variable. Stripping the prefix converts absolute paths to relative paths (`scripts/validate.py`, `references/api.md`), which work because the skill directory is extracted as a flat structure where these subdirectories are siblings of SKILL.md.

### Build process

```bash
mkdir -p dist

# For single skill — copy the ENTIRE skill directory (not just SKILL.md)
cp -r {{plugin-name}}/skills/{{skill-name}} dist/{{skill-name}}

# For multi-skill:
# for skill in {{skill-names}}; do
#   cp -r {{plugin-name}}/skills/$skill dist/$skill
# done

# Path hygiene — strip ${CLAUDE_SKILL_DIR}/ from ALL markdown files
# This includes SKILL.md AND reference files that cross-reference each other
find dist/ -name '*.md' -exec sed -i '' 's|\${CLAUDE_SKILL_DIR}/||g' {} +

# Write version
echo "{{version}}" > dist/{{skill-name}}/VERSION

cd dist && zip -r ../{{zip-filename}} {{skill-name}}/
```

### What gets included in the zip

The zip should contain everything in the skill directory:

```
{{skill-name}}/
├── SKILL.md              (with ${CLAUDE_SKILL_DIR}/ stripped)
├── VERSION
├── scripts/              (if exists — copied as-is, these are executed by the agent)
├── references/           (if exists — .md files have paths stripped too)
├── assets/               (if exists — templates, data files, etc.)
├── agents/               (if exists — subagent definitions)
└── evals/                (if exists — test cases)
```

### Verification

After building the zip, verify:
1. All `.md` files have no remaining `${CLAUDE_SKILL_DIR}` references: `grep -r 'CLAUDE_SKILL_DIR' dist/`
2. Scripts are present and have the same relative paths referenced in SKILL.md
3. Reference files are present and their cross-references resolve

The resulting zip works for: Claude.ai upload, Manus upload, ChatGPT upload, Codex CLI manual install, and extraction to `.agents/skills/` for any agent.

---

## Claude plugin

The inner plugin directory that Claude Code discovers.

### Directory structure

```
{{plugin-name}}/
├── .claude-plugin/
│   └── plugin.json
└── skills/
    └── {{skill-name}}/
        ├── SKILL.md
        ├── VERSION
        └── ... (scripts/, references/, etc.)
```

### `{{plugin-name}}/.claude-plugin/plugin.json`

```json
{
  "name": "{{plugin-name}}",
  "version": "{{version}}",
  "description": "{{skill-description}}",
  "author": {
    "name": "{{author-name}}",
    "email": "{{author-email}}"
  },
  "repository": "{{repo-url}}",
  "license": "{{license}}",
  "keywords": {{keywords}},
  "skills": "./skills"
}
```

For multi-skill plugins, `skills` still points to `"./skills"` — Claude Code discovers all subdirectories containing SKILL.md.

---

## Claude marketplace

A root-level marketplace manifest that wraps the inner plugin.

### Directory structure (additions to repo root)

```
.claude-plugin/
└── marketplace.json
```

### `.claude-plugin/marketplace.json`

```json
{
  "name": "{{marketplace-name}}",
  "owner": {
    "name": "{{author-name}}",
    "email": "{{author-email}}"
  },
  "metadata": {
    "description": "{{skill-description}}",
    "version": "{{version}}",
    "pluginRoot": "./{{plugin-name}}"
  },
  "plugins": [
    {
      "name": "{{plugin-name}}",
      "source": "./{{plugin-name}}",
      "description": "{{skill-description}}",
      "author": {
        "name": "{{author-name}}",
        "email": "{{author-email}}"
      },
      "category": "{{category}}",
      "tags": {{keywords}}
    }
  ]
}
```

**Installation commands** (for README):

```bash
# CLI
claude plugin marketplace add https://github.com/{{github-owner}}/{{github-repo}}
claude plugin install {{plugin-name}}@{{marketplace-name}}

# Or from within a Claude Code session:
/plugin marketplace add {{github-owner}}/{{github-repo}}
/plugin install {{plugin-name}}@{{marketplace-name}}
```

---

## Cursor plugin

### Directory structure (at repo root)

```
.cursor-plugin/
└── plugin.json
```

### `.cursor-plugin/plugin.json`

```json
{
  "name": "{{plugin-name}}",
  "displayName": "{{display-name}}",
  "version": "{{version}}",
  "description": "{{skill-description}}",
  "author": {
    "name": "{{author-name}}",
    "email": "{{author-email}}"
  },
  "license": "{{license}}",
  "keywords": {{keywords}},
  "skills": "./{{plugin-name}}/skills"
}
```

Note: `skills` path is relative from repo root and points into the inner plugin's skills directory.

**Installation** (for README):

```
1. Open Cursor Settings
2. Paste https://github.com/{{github-owner}}/{{github-repo}} into "Search or Paste Link"
```

---

## Cursor marketplace

Same as Cursor plugin. The `.cursor-plugin/plugin.json` at repo root is what the Cursor marketplace indexes. No separate marketplace manifest is needed — Cursor discovers plugins from the repo directly.

---

## Agent Skills standard

The `.agents/skills/` directory provides cross-client skill discovery per the agentskills.io spec.

### Directory structure (at repo root)

```
.agents/
└── skills/
    └── {{skill-name}} -> ../../{{plugin-name}}/skills/{{skill-name}}
```

Create as a symlink so there's a single copy of the skill files:

```bash
mkdir -p .agents/skills
cd .agents/skills
ln -s ../../{{plugin-name}}/skills/{{skill-name}} {{skill-name}}
```

For multi-skill packages, create one symlink per skill.

**Why a symlink?** The skill files live in the plugin directory (canonical location). The `.agents/skills/` symlink makes them discoverable by agents that scan the agentskills.io standard path without duplicating content.

**Fallback for environments without symlinks (Windows):** Copy the skill directory instead. The bump-version.sh and CI/CD should handle either case.

---

## NanoClaw marketplace

NanoClaw uses the standard Claude Code plugin marketplace format. If you're already generating a Claude marketplace (`.claude-plugin/marketplace.json`), that same repo structure works with NanoClaw.

NanoClaw users install via:
```bash
# In .claude/settings.json, add to extraKnownMarketplaces:
# Or use Claude Code:
claude plugin marketplace add https://github.com/{{github-owner}}/{{github-repo}}
claude plugin install {{plugin-name}}@{{marketplace-name}} --scope project
```

No separate format is needed. The Claude marketplace format covers NanoClaw.

---

## GitHub Actions release workflow

### `.github/workflows/release.yml`

```yaml
name: Release

on:
  push:
    tags:
      - 'v*'

permissions:
  contents: write

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6

      - name: Extract version from tag
        id: version
        run: echo "version=${GITHUB_REF#refs/tags/v}" >> "$GITHUB_OUTPUT"

      - name: Build generic zip
        run: |
          mkdir -p dist
          cp -r {{plugin-name}}/skills/{{skill-name}} dist/{{skill-name}}
          find dist/{{skill-name}} -name '*.md' -exec sed -i 's|\${CLAUDE_SKILL_DIR}/||g' {} +
          echo "${{ steps.version.outputs.version }}" > dist/{{skill-name}}/VERSION
          cd dist && zip -r ../{{zip-filename}} {{skill-name}}/

      - name: Extract release notes from CHANGELOG.md
        id: changelog
        run: |
          VERSION="${{ steps.version.outputs.version }}"
          NOTES=$(awk "/^## \\[${VERSION}\\]/{found=1; next} /^## \\[/{if(found) exit} found{print}" CHANGELOG.md)
          echo "$NOTES" > release-notes.md

      - name: Create GitHub Release
        uses: softprops/action-gh-release@v2
        with:
          body_path: release-notes.md
          files: |
            {{zip-filename}}
```

For multi-skill packages, the build step copies the entire skills directory:
```yaml
      - name: Build generic zip
        run: |
          mkdir -p dist
          cp -r {{plugin-name}}/skills dist/skills
          find dist/skills -name '*.md' -exec sed -i 's|\${CLAUDE_SKILL_DIR}/||g' {} +
          cd dist && zip -r ../{{zip-filename}} skills/
```

---

## Version management

### `VERSION`

```
{{version}}
```

Plain text, no trailing newline issues. This is the single source of truth.

### `tools/bump-version.sh`

```bash
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
sed -i '' "s/\"version\": \"[^\"]*\"/\"version\": \"$VERSION\"/" "$REPO_ROOT/{{plugin-name}}/.claude-plugin/plugin.json"

# 2. Cursor plugin manifest
sed -i '' "s/\"version\": \"[^\"]*\"/\"version\": \"$VERSION\"/" "$REPO_ROOT/.cursor-plugin/plugin.json"

# 3. SKILL.md frontmatter (metadata.version)
sed -i '' "s/version: \"[^\"]*\"/version: \"$VERSION\"/" "$REPO_ROOT/{{plugin-name}}/skills/{{skill-name}}/SKILL.md"

# 4. Skill VERSION file
cp "$REPO_ROOT/VERSION" "$REPO_ROOT/{{plugin-name}}/skills/{{skill-name}}/VERSION"

echo "Version $VERSION propagated to all locations."
```

For multi-skill packages, add a sed line for each skill's SKILL.md and copy VERSION to each skill directory.

**Cross-platform note:** The `sed -i ''` syntax is BSD (macOS). The GitHub Actions release workflow runs on Ubuntu where `sed -i` (no quotes) is correct. The bump script is intended for local use on macOS; CI uses its own version extraction.

### `VERSIONING.md`

```markdown
# Versioning

This project uses [Semantic Versioning](https://semver.org/) (`MAJOR.MINOR.PATCH`).

## Version Source of Truth

The canonical version lives in the `VERSION` file at the repo root. All other version locations are updated from it.

## Version Locations

The version appears in these files (all managed by the bump script):

1. `VERSION` — source of truth
2. `{{plugin-name}}/.claude-plugin/plugin.json` → `"version"` field
3. `.cursor-plugin/plugin.json` → `"version"` field
4. `{{plugin-name}}/skills/{{skill-name}}/SKILL.md` → `metadata.version` in YAML frontmatter
5. `{{plugin-name}}/skills/{{skill-name}}/VERSION` → copied from root

## Bumping the Version

\`\`\`bash
# Set a new version and propagate to all locations:
./tools/bump-version.sh 0.2.0

# Or edit VERSION manually, then propagate:
./tools/bump-version.sh
\`\`\`

## Release Process

\`\`\`bash
# 1. Bump version
./tools/bump-version.sh X.Y.Z
# 2. Update CHANGELOG.md with release notes
# 3. Commit
git commit -am "chore: bump version to X.Y.Z"
# 4. Tag and push
git tag vX.Y.Z
git push origin main --tags
\`\`\`

CI automatically creates a GitHub Release with a zip for all platforms.
```

### `CHANGELOG.md`

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [{{version}}] - {{date}}

### Added
- Initial release of the {{skill-name}} skill
- Cross-platform support: Claude Code, Claude Desktop, Cursor, Manus, ChatGPT, Codex CLI
- Claude Code plugin marketplace support
- Cursor plugin support
- GitHub Release workflow for zip distribution
```

Replace `{{date}}` with the current date in YYYY-MM-DD format.

### `LICENSE` (MIT)

```
MIT License

Copyright (c) {{year}} {{author-name}}

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## Claude Desktop install button

A one-click install button for Claude Desktop. Requires GitHub Pages enabled on the repo.

### `static/install-claude-desktop.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Install {{Skill Display Name}} in Claude Desktop</title>
<style>
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; background: #f9f5f1; color: #3d3929; }
.card { text-align: center; padding: 3rem; max-width: 480px; }
h1 { font-size: 1.4rem; margin-bottom: 1rem; }
p { color: #6b5e4f; line-height: 1.6; }
a { color: #d97757; text-decoration: none; font-weight: 600; }
a:hover { text-decoration: underline; }
.fallback { display: none; }
</style>
</head>
<body>
<div class="card">
<h1>Installing {{Skill Display Name}}</h1>
<p id="status">Opening Claude Desktop...</p>
<div id="fallback" class="fallback">
<p>Claude Desktop didn't open. You can:</p>
<p><a href="claude://claude.ai/customize/plugins/new?marketplace=https://github.com/{{github-owner}}/{{github-repo}}&plugin={{plugin-name}}">Try again</a></p>
<p>Or install manually: open Claude Desktop, click <strong>Customize</strong>, then <strong>Browse Plugins</strong>, add marketplace <code>{{github-owner}}/{{github-repo}}</code>.</p>
</div>
<p><a href="https://github.com/{{github-owner}}/{{github-repo}}">Back to {{Skill Display Name}} on GitHub</a></p>
</div>
<script>
var deepLink = "claude://claude.ai/customize/plugins/new?marketplace=https://github.com/{{github-owner}}/{{github-repo}}&plugin={{plugin-name}}";
var repo = "https://github.com/{{github-owner}}/{{github-repo}}";

// Try opening the deep link
window.location = deepLink;

// If the page is still visible after 5s, the deep link likely didn't work
setTimeout(function() {
  if (!document.hidden) {
    document.getElementById("status").textContent = "";
    document.getElementById("fallback").style.display = "block";
  }
}, 5000);

// If the user comes back to this tab (Claude opened then they switched back), redirect to repo
document.addEventListener("visibilitychange", function() {
  if (!document.hidden) {
    setTimeout(function() { window.location = repo; }, 500);
  }
});
</script>
</body>
</html>
```

### `.github/workflows/deploy-pages.yml`

```yaml
name: Deploy Pages

on:
  push:
    branches: [main]

permissions:
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: true

jobs:
  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6

      - name: Build site
        run: |
          mkdir -p _site/static
          cp static/install-claude-desktop.html _site/static/

      - uses: actions/upload-pages-artifact@v3

      - id: deployment
        uses: actions/deploy-pages@v4
```

### README badge

Add this badge near the top of the README (requires GitHub Pages to be enabled in repo settings):

```markdown
[![Install in Claude Desktop](https://img.shields.io/badge/Install_in_Claude_Desktop-D97757?style=for-the-badge&logo=claude&logoColor=white)](https://{{github-owner}}.github.io/{{github-repo}}/static/install-claude-desktop.html)
```

### Setup note

GitHub Pages must be enabled on the repo for the install button to work:
1. Go to repo **Settings** → **Pages**
2. Set **Source** to **GitHub Actions**
3. The `deploy-pages.yml` workflow handles the rest

---

## Universal repo — full file list

When generating a universal repo, create all of the following:

```
{{github-repo}}/
├── .github/
│   └── workflows/
│       ├── release.yml              ← GitHub Actions release workflow
│       └── deploy-pages.yml         ← GitHub Pages for install button
├── .claude-plugin/
│   └── marketplace.json             ← Claude marketplace wrapper
├── .cursor-plugin/
│   └── plugin.json                  ← Cursor plugin manifest (root)
├── .agents/
│   └── skills/
│       └── {{skill-name}} → …      ← Symlink for agentskills.io compat
├── {{plugin-name}}/
│   ├── .claude-plugin/
│   │   └── plugin.json              ← Claude plugin manifest (inner)
│   └── skills/
│       └── {{skill-name}}/
│           ├── SKILL.md             ← Copied from source
│           ├── VERSION              ← Copied from root VERSION
│           ├── scripts/             ← Copied from source (if exists)
│           ├── references/          ← Copied from source (if exists)
│           ├── assets/              ← Copied from source (if exists)
│           └── agents/              ← Copied from source (if exists)
├── static/
│   └── install-claude-desktop.html  ← One-click install page (GitHub Pages)
├── tools/
│   └── bump-version.sh             ← Version propagation script
├── VERSION                          ← Source of truth for version
├── VERSIONING.md                    ← How versioning works
├── CHANGELOG.md                     ← Release notes
├── README.md                        ← With per-platform install instructions
└── LICENSE                          ← License file
```

Generation order:
1. Create directory structure
2. Copy skill files into `{{plugin-name}}/skills/{{skill-name}}/`
3. Generate VERSION file
4. Generate all JSON manifests (Claude plugin, Claude marketplace, Cursor plugin)
5. Generate bump-version.sh (make executable: `chmod +x`)
6. Generate release.yml and deploy-pages.yml
7. Generate static/install-claude-desktop.html
8. Create `.agents/skills/` symlink
9. Generate VERSIONING.md, CHANGELOG.md, LICENSE
10. Generate README.md (using platforms.md template, include install button badge)
11. Validate all JSON files
