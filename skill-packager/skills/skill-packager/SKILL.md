---
name: skill-packager
description: >
  Package AI agent skills into deployment formats — .zip, .skill, Claude plugin, Claude marketplace,
  Cursor plugin, Cursor marketplace, ChatGPT/Manus zip, Codex CLI, NanoClaw marketplace,
  Agent Skills standard (.agents/), or a universal repo with all formats + CI/CD.
  Use when the user says "package this skill", "deploy my skill", "create a plugin from this skill",
  "make this work on Cursor/ChatGPT/Codex/NanoClaw", "set up a repo for my skill",
  or wants to distribute a SKILL.md to any platform.
metadata:
  author: Yaniv Golan
  version: "0.1.0"
---

# Skill Packager

You package one or more skills (directories containing SKILL.md) into deployment-ready formats for distribution across AI platforms.

## Step 1: Discover the input

Ask the user for the skill directory path(s). Then read each skill's SKILL.md to extract:
- `name` — the skill identifier
- `description` — what it does
- `metadata.author`, `metadata.version` — if present
- `license` — if present
- Whether it has `scripts/`, `references/`, `assets/`, `agents/`, `evals/`

If packaging multiple skills, confirm the list before proceeding.

## Step 2: Gather metadata

You need these values to generate manifests. Extract what you can from the SKILL.md frontmatter and the git repo (if any). Ask the user for anything missing:

| Field | Source | Fallback |
|-------|--------|----------|
| Skill name(s) | SKILL.md `name` | required |
| Description | SKILL.md `description` | required |
| Author name | SKILL.md `metadata.author` or git config | ask user |
| Author email | git config `user.email` | ask user |
| Version | SKILL.md `metadata.version` or `VERSION` file | default `0.1.0` |
| License | SKILL.md `license` | default `MIT` |
| GitHub owner/repo | git remote or ask | needed for marketplace/repo formats |
| Plugin name | derived from skill name | user can override |
| Keywords/tags | extracted from description | user can refine |

For multi-skill packages, also ask for an overall plugin/marketplace name and description.

When asking for fields that have a fixed set of choices (like license), use the **AskUserQuestion** tool to present structured options. For free-form fields (author name, email, description), ask in plain text — batch related free-form questions together to minimize back-and-forth.

## Step 3: Choose target format(s)

Use the **AskUserQuestion** tool to let the user choose format(s). Since AskUserQuestion supports 2–4 options per question (with an automatic "Other" escape hatch), group the 10 formats into two questions:

**Question 1** (single-select, header: "Scope"):
> "What kind of package do you need?"

| Option | Description |
|--------|-------------|
| Universal repo (Recommended) | Full repo with ALL formats, CI/CD, version management — best for public distribution |
| Single platform | Package for one specific platform only |
| Just a ZIP | Clean zip of skill folder(s) with path hygiene |

If the user picks "Universal repo", skip Question 2 — all formats are included.

**Question 2** (multiSelect, header: "Platforms", only if "Single platform" was chosen):
> "Which platform(s) should the package target?"

| Option | Description |
|--------|-------------|
| Claude plugin | Plugin directory with `.claude-plugin/plugin.json` and marketplace manifest |
| Cursor plugin | `.cursor-plugin/plugin.json` formatted for Cursor marketplace |
| Agent Skills standard | `.agents/skills/` directory structure for cross-client interop |

If the user picks "Other" on either question, fall back to presenting the full format table:

| # | Format | What it produces |
|---|--------|-----------------|
| 1 | **ZIP** | Clean zip of skill folder(s) with path hygiene |
| 2 | **Claude plugin** | Plugin directory with `.claude-plugin/plugin.json` |
| 3 | **Claude marketplace** | Plugin + root `marketplace.json` for marketplace distribution |
| 4 | **Cursor plugin** | `.cursor-plugin/plugin.json` pointing at skills |
| 5 | **Cursor marketplace** | Cursor plugin formatted for marketplace submission |
| 6 | **ChatGPT / Manus ZIP** | Same as #1 — these platforms accept skill zips |
| 7 | **Codex CLI** | Same zip + install instructions for `$skill-installer` and `~/.codex/skills/` |
| 8 | **Agent Skills standard** | `.agents/skills/` directory structure for cross-client interop |
| 9 | **NanoClaw marketplace** | Claude plugin marketplace format for NanoClaw's skill system |
| 10 | **Universal repo** | Full repo with ALL formats + CI/CD + version management |

**Format 10 (universal repo) is the recommended default** for skills intended for public distribution. It includes everything: dual plugin manifests, marketplace config, GitHub Actions release workflow, version management, README with per-platform install instructions, CHANGELOG, and the `.agents/skills/` symlink.

Formats 1, 6, and 7 produce the same zip — the difference is just which install instructions you include.

If the user asks for a `.skill` file specifically, use the `package_skill.py` script from the skill-creator-plus plugin if available, or tell them to run it separately.

## Step 4: Generate the output

### Output directory

Use the **AskUserQuestion** tool to confirm the output directory (header: "Output"):
> "Where should the packaged output go?"

| Option | Description |
|--------|-------------|
| `../<skill-name>-skill/` (Recommended) | New directory next to the skill source (best for universal repo) |
| `./dist/` | Subdirectory inside the current project |

The user can also pick "Other" to specify a custom path.

### Generation process

Use the bundled scripts to handle all deterministic generation:

#### 1. Extract metadata from source skill(s)

```bash
# Single skill:
python3 ${CLAUDE_SKILL_DIR}/scripts/skill_packager metadata \
  --skill-path /path/to/skill > /tmp/partial-meta.json

# Multi-skill:
python3 ${CLAUDE_SKILL_DIR}/scripts/skill_packager metadata \
  --skill-path /path/to/skill-a --skill-path /path/to/skill-b > /tmp/partial-meta.json
```

Read the output JSON. Fill in any empty fields: `github_repo`, `formats`, `keywords`, `category`, `targets`. For multi-skill: also fill `plugin_name`, `marketplace_name`, `display_name`, `description`, `version`. Write the complete metadata to `meta.json`.

#### 2. Scaffold the repo

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/skill_packager scaffold \
  --metadata meta.json --output ./my-skill-repo/
```

This creates the full directory structure, copies skill files, renders all manifests, and creates the `.agents/skills/` stripped copy. The canonical copy (under `<plugin-name>/skills/`) keeps `${CLAUDE_SKILL_DIR}/` paths; the `.agents/skills/` copy has them stripped for cross-platform portability.

#### 3. Write README.md and CHANGELOG.md

These are the creative parts that require judgment. Read `${CLAUDE_SKILL_DIR}/references/platforms.md` for the per-platform installation instructions template.

The scaffolded README.md and CHANGELOG.md contain `<!-- SKILL_PACKAGER: REPLACE THIS -->` markers. Replace the entire file content with real content. The README should include:
- Title and badges (Agent Skills compatible, Claude Code plugin, Cursor plugin, license)
- Brief description of what the skill(s) do
- Installation sections for every supported platform
- Usage examples (pulled from the skill's description or examples)
- License

#### 4. Build zip (if needed)

For formats that need a zip (ZIP, ChatGPT/Manus, Codex CLI):

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/skill_packager build-zip \
  --skill-dir ./my-skill-repo/<plugin-name>/skills/<skill-name> \
  --output dist/<skill-name>.zip
```

## Step 5: Verify the output

Run the validation script:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/skill_packager validate ./my-skill-repo/
```

This checks JSON validity, version consistency across all locations, skill path resolution, `.agents/skills/` entries, and stub detection (README/CHANGELOG must not still contain the placeholder marker). Fix any failures and rerun until all checks pass.

For machine-readable output, add `--json`.

## Step 6: Present results

Tell the user what was generated with a file tree. Highlight:
- How to do the first release (bump version, tag, push)
- Which platforms are supported and how to install on each
- Any manual steps needed (e.g., marketplace registration)
- **GitHub Pages setup**: Remind the user to enable GitHub Pages in repo Settings → Pages → Source: GitHub Actions. This powers the "Install in Claude Desktop" button.

## Edge cases and gotchas

**Skills with dependencies.** If a skill's `compatibility` field mentions required tools (Python, ffmpeg, etc.), include a note in the README about prerequisites. For ChatGPT specifically, warn if the skill requires tools that won't work in ChatGPT's sandbox.

**Skills with scripts.** Scripts are included in the zip. Make sure relative paths in SKILL.md still resolve after the zip is extracted.

**The `.agents/skills/` symlink.** On Windows, symlinks may not work. The README should mention the alternative of copying the skill directory.

**ChatGPT limitations.** ChatGPT Skills are in beta (Business/Enterprise/Edu/Teachers/Healthcare plans only). Always include this caveat. If the skill requires network access or specific CLI tools, warn that it may not work in ChatGPT.

**Codex CLI.** Supports `$skill-installer <github-url>` for automated install, or manual extraction to `~/.codex/skills/`. Both should be documented.

**npx skills add.** The `vercel-labs/skills` package provides cross-platform install via `npx skills add <owner>/<repo>`. Include this in the README when generating a universal repo.

**Cursor plugin path.** The `.cursor-plugin/plugin.json` at repo root needs `"skills"` to point to the inner plugin's skills directory (e.g., `"./pretext/skills"`), not the repo root.

**Marketplace naming.** The marketplace name is `<plugin-name>-marketplace`. The inner plugin name is just `<plugin-name>`.

**NanoClaw.** NanoClaw uses standard Claude Code skills and distributes them via Claude plugin marketplace repos. The format is identical to Claude marketplace — a repo with `.claude-plugin/marketplace.json` pointing at plugins containing skills. NanoClaw's branch-based "feature skills" (where code lives on `skill/*` git branches) are a NanoClaw-specific pattern for skills that modify NanoClaw's own codebase — these are out of scope for generic skill packaging. For standalone skills that teach an agent a capability (operational/utility skills), the standard Claude marketplace format works directly with NanoClaw.
