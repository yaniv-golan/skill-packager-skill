# Skill Packager Scripts Design

**Date:** 2026-04-06
**Status:** Approved

## Problem

The skill-packager skill currently instructs Claude to read 659 lines of templates from `references/formats.md` and generate 15-20 files one-by-one. This is slow (50k-170k tokens, 144 tool uses), error-prone (baselines got manifest paths wrong), and wastes Claude's time on deterministic work. The only creative work is README and CHANGELOG content.

## Solution

Bundle a Python CLI (`scripts/skill_packager/`) with composable subcommands that handle all deterministic generation, leaving Claude to do metadata gathering, README/CHANGELOG writing, and orchestration.

## Design Decisions

- **Language:** Python only. Stdlib-only (no external deps). Avoids BSD/GNU sed cross-platform issues.
- **Architecture:** Composable subcommands (not monolithic). Each piece independently useful.
- **Generated repos:** Get standalone `tools/bump-version.py` and `tools/build-zip.py` (stdlib Python, no dependency on skill-packager being installed).
- **No PEP 723:** Not needed since all scripts are stdlib-only.
- **Script conventions:** Follows agentskills.io and Claude Code patterns — package structure with `__init__.py`, invoked via `${CLAUDE_SKILL_DIR}/scripts/skill_packager`.

## Metadata Schema

The central data structure that drives all generation. Claude produces this from Steps 1-2 of the skill workflow.

```json
{
  "skills": [
    {
      "name": "proof-engine",
      "source_path": "/abs/path/to/skills/proof-engine",
      "description": "Create formal proofs...",
      "has_scripts": true,
      "has_references": true,
      "has_assets": false,
      "has_agents": true,
      "has_evals": true
    }
  ],
  "plugin_name": "proof-engine",
  "marketplace_name": "proof-engine-marketplace",
  "display_name": "Proof Engine",
  "description": "Create formal, verifiable proofs...",
  "version": "1.7.0",
  "author_name": "Yaniv Golan",
  "author_email": "yaniv@golan.name",
  "github_owner": "yaniv-golan",
  "github_repo": "proof-engine-skill",
  "license": "MIT",
  "keywords": ["proof", "verification", "formal-methods"],
  "category": "development",
  "formats": ["universal"],
  "targets": ["claude-desktop", "claude-code", "claude-web", "cursor", "chatgpt", "manus", "codex", "nanoclaw", "agent-skills", "npx"]
}
```

For multi-skill packages, `skills` has multiple entries. `plugin_name` and `description` describe the bundle.

## Subcommands

### `metadata`

**Input:** `--skill-path /path/to/skills/proof-engine` (repeatable: `--skill-path /path/a --skill-path /path/b`)
**Output:** Partial metadata JSON to stdout.

For each `--skill-path`, parses SKILL.md frontmatter (name, description, license, metadata.author, metadata.version), detects which subdirectories exist (scripts/, references/, assets/, agents/, evals/), reads VERSION file if present. Also reads git config for author name/email and git remote for owner/repo (once, from the first skill's directory).

When multiple `--skill-path` arguments are given, the output JSON contains multiple entries in the `skills` array. The top-level `plugin_name`, `description`, `version`, and other bundle-level fields are left empty for Claude to fill in (since naming and versioning a multi-skill bundle requires judgment).

For single-skill packages, `metadata` auto-populates the top-level `version` from the skill's `metadata.version` or `VERSION` file. For multi-skill, skills may have different versions — Claude picks the bundle version (typically the highest, or asks the user).

Claude fills in remaining fields (github_repo, formats, keywords, category, targets, and for multi-skill: plugin_name, description, version) and writes the complete `meta.json`.

### `scaffold`

**Input:** `--metadata meta.json --output ./repo/`
**Output:** Complete repo directory structure.

Generates a directory structure based on the `formats` field in metadata. `scaffold` always produces directories — it never produces zip files directly. Use `build-zip` as a separate step when a zip is needed.

Every format includes the skill payload (the inner `<plugin-name>/skills/<skill-name>/` tree with copied SKILL.md, scripts, references, etc.). The format determines which *additional* scaffolding surrounds it.

| Format value | What gets generated |
|---|---|
| `universal` | Everything below |
| `claude-plugin` | Inner plugin directory with `.claude-plugin/plugin.json` + skill payload |
| `claude-marketplace` | Plugin + root `.claude-plugin/marketplace.json` + skill payload |
| `cursor-plugin` | Root `.cursor-plugin/plugin.json` + inner plugin directory + skill payload |
| `agent-skills` | `.agents/skills/` directory with skill files copied directly (no symlink — standalone) |

For zip-only workflows, Claude runs `scaffold` with `claude-plugin` format, then `build-zip` on the result.

**Note on `agent-skills` format:** Since there's no inner plugin tree to symlink to, skills are copied directly into `.agents/skills/<skill-name>/`. This is the only format where the skill payload lives at the top level rather than nested under a plugin directory.

### User-facing targets → scaffold format mapping

The SKILL.md presents 10 user-facing targets. Several map to the same scaffold format, differing only in post-processing (zip build) or README install instructions. The `formats` field in `meta.json` uses the scaffold format values. Claude handles the mapping:

| User-facing target | Scaffold format | Post-processing | README sections |
|---|---|---|---|
| 1. ZIP | `claude-plugin` | `build-zip` | Claude.ai, Manus, Other Tools |
| 2. Claude plugin | `claude-plugin` | — | Claude Code CLI |
| 3. Claude marketplace | `claude-marketplace` | — | Claude Desktop, Claude Code CLI |
| 4. Cursor plugin | `cursor-plugin` | — | Cursor |
| 5. Cursor marketplace | `cursor-plugin` | — | Cursor (marketplace submission) |
| 6. ChatGPT / Manus ZIP | `claude-plugin` | `build-zip` | ChatGPT, Manus |
| 7. Codex CLI | `claude-plugin` | `build-zip` | Codex CLI |
| 8. Agent Skills standard | `agent-skills` | — | Any Agent (npx), Other Tools |
| 9. NanoClaw marketplace | `claude-marketplace` | — | NanoClaw (same as Claude marketplace) |
| 10. Universal repo | `universal` | — | All sections |

The `meta.json` also stores a `"targets"` list (e.g., `["chatgpt", "codex", "manus"]`) so Claude knows which README install sections to include. This is separate from `"formats"` which drives scaffold structure.

For `universal`, generates:

```
<github-repo>/
├── .github/workflows/
│   ├── release.yml
│   └── deploy-pages.yml
├── .claude-plugin/marketplace.json
├── .cursor-plugin/plugin.json
├── .agents/skills/<skill-name>/  ← stripped copy (portable, no ${CLAUDE_SKILL_DIR}/)
├── static/install-claude-desktop.html
├── <plugin-name>/
│   ├── .claude-plugin/plugin.json
│   └── skills/
│       └── <skill-name>/
│           ├── SKILL.md (copied from source)
│           ├── VERSION
│           ├── scripts/ (copied)
│           ├── references/ (copied)
│           ├── assets/ (copied)
│           └── agents/ (copied)
├── tools/
│   ├── bump-version.py
│   └── build-zip.py
├── meta.json                 ← scaffolding metadata (used by validate, build-zip, bump-version)
├── VERSION
├── VERSIONING.md
├── CHANGELOG.md              ← stub with marker for Claude
├── README.md                 ← stub with marker for Claude
└── LICENSE
```

**Behavior:**
- Aborts if output dir exists and is non-empty (no silent overwrite)
- Writes `meta.json` to the repo root (used by `validate` and `build-zip` to understand the repo structure)
- Copies skill files preserving directory structure
- Keeps `${CLAUDE_SKILL_DIR}/` in the canonical plugin copy (under `<plugin-name>/skills/`) — Claude Code expands this at runtime
- **`.agents/skills/` is always a stripped copy** with `${CLAUDE_SKILL_DIR}/` removed. This applies to all formats that include it (`universal`, `agent-skills`). The copy is portable and directly usable by non-Claude clients on any OS. `bump-version` always updates both the canonical copy and the `.agents/skills/` copy.
  - **Why not a symlink?** A symlink would point at the Claude-canonical copy which contains `${CLAUDE_SKILL_DIR}/` paths — unusable by non-Claude agents. The staleness concern is minimal: version strings are the only thing that changes post-scaffold (handled by `bump-version`), and content edits mean re-running the packager.
- Makes `tools/bump-version.py` and `tools/build-zip.py` executable
- README.md and CHANGELOG.md are stubs with `<!-- SKILL_PACKAGER: REPLACE THIS -->` markers

### `build-zip`

Two modes of operation:

**Explicit mode** (skill-packager CLI, used during Step 4):
**Input:** `--skill-dir ./repo/plugin/skills/my-skill --output dist/my-skill.zip` (or `--skill-dir ./repo/plugin/skills/` for multi-skill)

**Repo-root mode** (generated `tools/build-zip.py`, used in CI and local builds):
**Input:** `--version 0.2.0` (optional). Reads `meta.json` from repo root to discover skill directories and plugin name. Defaults output to `dist/<plugin-name>-<version>.zip`.

**Output:** ZIP file with path hygiene applied.

Steps:
1. Copy skill directory to temp staging area
2. Strip `${CLAUDE_SKILL_DIR}/` from all `.md` files in the copy
3. Write VERSION if `--version` flag provided
4. Create zip with correct root layout:
   - **Single skill:** `<skill-name>/` at archive root (e.g., `proof-engine/SKILL.md`). Consumers extract and get a single skill directory.
   - **Multi-skill:** `skills/` wrapper at archive root containing each skill (e.g., `skills/code-review/SKILL.md`, `skills/test-gen/SKILL.md`). This matches the `references/formats.md` multi-skill convention and the `.agents/skills/` directory layout that consumers expect.
5. Verify no `${CLAUDE_SKILL_DIR}` remains in the archive
6. Clean up temp staging area

Note: single-skill and multi-skill archives have different root shapes. This is intentional — single-skill archives are more common and simpler to extract. Consumers that support both (like `npx skills add`) handle the detection.

The generated `tools/build-zip.py` uses repo-root mode:
```yaml
- name: Build generic zip
  run: python3 tools/build-zip.py --version ${{ steps.version.outputs.version }}
```

### `validate`

**Input:** `./repo/` (reads `meta.json` from the repo to determine which format was scaffolded)
**Output:** Pass/fail per check, exit code 0 (all pass) or 1 (any fail). `--json` for machine-readable output.

Validation is format-aware. It reads `meta.json` from the repo root to determine which checks apply. Checks that don't apply to the scaffolded format are skipped (not failed).

**Always checked (all formats):**
- All `.json` files parse correctly
- Skills path in each manifest resolves to actual SKILL.md files
- Version consistent across all version-bearing files that exist

**Checked only when the format produces them:**
- `marketplace.json` version consistency (claude-marketplace, universal)
- `.agents/skills/` symlinks resolve or directory exists (agent-skills, universal)
- `release.yml` references correct paths (universal)
- `bump-version.py` targets all version locations (universal)
- `README.md` exists and is not a stub (universal)
- `CHANGELOG.md` exists and is not a stub (universal)

### `bump-version`

**Input:** `./repo/ 0.2.0`
**Output:** Updates version in all locations, prints what was changed.

Locations updated:
- `meta.json` → `"version"` field
- Root `VERSION`
- Each `<plugin-name>/.claude-plugin/plugin.json` → `"version"` field
- `.claude-plugin/marketplace.json` → `metadata.version` field (root marketplace wrapper)
- `.cursor-plugin/plugin.json` → `"version"` field
- Each `<plugin-name>/skills/<skill-name>/SKILL.md` → `metadata.version`
- Each `<plugin-name>/skills/<skill-name>/VERSION`
- Each `.agents/skills/<skill-name>/SKILL.md` → `metadata.version` (if `.agents/skills/` exists)
- Each `.agents/skills/<skill-name>/VERSION` (if `.agents/skills/` exists)

`bump-version` reads `meta.json` to discover which files exist (format-aware — only updates files that were scaffolded).

## Module Structure

```
skills/skill-packager/
├── SKILL.md
├── scripts/
│   └── skill_packager/
│       ├── __init__.py          (empty)
│       ├── __main__.py          (CLI entry point with argparse subcommands)
│       ├── metadata.py          (parse SKILL.md, detect subdirs, git info)
│       ├── scaffold.py          (generate repo from metadata)
│       ├── build_zip.py         (copy + path hygiene + zip)
│       ├── validate.py          (check JSON, versions, paths, symlinks)
│       ├── bump_version.py      (propagate version)
│       └── templates.py         (string constants for all generated files)
├── references/
│   ├── formats.md               (documentation of what scripts produce)
│   └── platforms.md             (Claude reads this to write README)
└── evals/
    └── evals.json
```

### `templates.py`

Contains all file templates as Python string constants with `{variable}` placeholders:

- `CLAUDE_PLUGIN_JSON` — inner plugin manifest
- `MARKETPLACE_JSON` — root marketplace wrapper
- `CURSOR_PLUGIN_JSON` — Cursor manifest
- `RELEASE_YML` — GitHub Actions release workflow
- `DEPLOY_PAGES_YML` — GitHub Pages workflow
- `INSTALL_HTML` — Claude Desktop install page
- `VERSIONING_MD` — how versioning works
- `LICENSE_MIT` — MIT license text
- `BUMP_VERSION_PY` — standalone bump script for generated repos
- `BUILD_ZIP_PY` — standalone zip builder for generated repos
- `README_STUB` — placeholder for Claude to fill in
- `CHANGELOG_STUB` — placeholder for Claude to fill in

## Updated Skill Workflow

Steps 1-3 unchanged (discover input, gather metadata, choose formats).

**Step 4 becomes:**

```bash
# 1. Extract metadata from source skill(s)
# Single skill:
python3 ${CLAUDE_SKILL_DIR}/scripts/skill_packager metadata \
  --skill-path /path/to/skill > /tmp/partial-meta.json
# Multi-skill:
python3 ${CLAUDE_SKILL_DIR}/scripts/skill_packager metadata \
  --skill-path /path/to/skill-a --skill-path /path/to/skill-b > /tmp/partial-meta.json

# 2. Claude reads partial metadata, fills gaps, writes complete meta.json

# 3. Scaffold the repo
python3 ${CLAUDE_SKILL_DIR}/scripts/skill_packager scaffold \
  --metadata meta.json --output ./my-skill-repo/

# 4. Claude writes README.md and CHANGELOG.md (the creative parts)

# 5. Validate
python3 ${CLAUDE_SKILL_DIR}/scripts/skill_packager validate ./my-skill-repo/
```

**Step 5:** Claude runs `validate`, reports results. Fixes and reruns if needed.

**Step 6:** Present results (unchanged).

## What Changes in Existing Files

### SKILL.md
- Step 4 updated to use script invocations instead of "read formats.md and generate files"
- Step 5 simplified to "run validate"
- Remove detailed file-by-file generation instructions
- Keep high-level principles (single source of truth, path hygiene rationale, etc.)

### references/formats.md
- Kept as documentation of what the scripts produce
- No longer on the critical path for generation
- Claude can reference it for debugging or understanding

### references/platforms.md
- Unchanged — Claude still reads this to write README content

## Generated Repo Tools

### `tools/bump-version.py`

Standalone Python script (stdlib only). Same logic as the `bump-version` subcommand but embedded in the generated repo. Users run it directly:

```bash
./tools/bump-version.py 0.2.0
```

### `tools/build-zip.py`

Standalone Python script (stdlib only). Used by `release.yml` and optionally by users for local builds:

```bash
python3 tools/build-zip.py                              # uses version from VERSION file
python3 tools/build-zip.py --version 0.2.0              # override version
python3 tools/build-zip.py --output custom-name.zip     # custom output name
```

Both generated tools read `meta.json` from the repo root to discover plugin name, skill names, and format. Nothing is baked into the scripts — they are identical across all generated repos. This means `meta.json` is the single source of truth for repo structure, and the generated tools, `validate`, and `bump-version` all agree on what exists.

## Expected Impact

Based on eval results:
- **Token reduction:** ~80% (from 50k-170k to ~10k-30k — Claude only writes meta.json + README + CHANGELOG)
- **Reliability:** Deterministic generation eliminates wrong manifest paths, missing files, inconsistent versions
- **User value:** `bump-version.py` and `build-zip.py` are tools users actually need day-to-day
- **CI simplification:** `release.yml` calls `build-zip.py` instead of inline shell with sed
