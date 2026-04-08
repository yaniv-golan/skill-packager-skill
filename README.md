# Skill Packager

![Skill Packager Banner](static/banner.png)

[![Install in Claude Desktop](https://img.shields.io/badge/Install_in_Claude_Desktop-D97757?style=for-the-badge&logo=claude&logoColor=white)](https://YanivGolan.github.io/skill-packager-marketplace/static/install-claude-desktop.html)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Agent Skills Compatible](https://img.shields.io/badge/Agent_Skills-compatible-4A90D9)](https://agentskills.io)
[![Claude Code Plugin](https://img.shields.io/badge/Claude_Code-plugin-F97316)](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/plugins)
[![Cursor Plugin](https://img.shields.io/badge/Cursor-plugin-00D886)](https://cursor.com/docs/plugins)
[![CI](https://github.com/yaniv-golan/skill-packager-skill/actions/workflows/ci.yml/badge.svg)](https://github.com/yaniv-golan/skill-packager-skill/actions/workflows/ci.yml)
[![Built with Skill Creator Plus](https://img.shields.io/badge/Built_with-Skill_Creator_Plus-4ecdc4?style=flat-square)](https://github.com/yaniv-golan/skill-creator-plus)

Package AI agent skills into deployment-ready formats for distribution across AI platforms.

Uses the open [Agent Skills](https://agentskills.io) standard. Works with Claude Desktop, Claude Cowork, Claude Code, Codex CLI, Cursor, Windsurf, Manus, ChatGPT, and any other compatible tool.

## What It Does

- Packages one or more skills (directories containing SKILL.md) into deployment-ready formats
- Generates Claude plugin manifests, Cursor plugin manifests, marketplace configs, and `.agents/skills/` directories
- Creates a universal repo with CI/CD (GitHub Actions release workflow + GitHub Pages), version management, and per-platform install instructions
- Handles path hygiene: keeps `${CLAUDE_SKILL_DIR}/` in canonical copies, strips it for cross-platform portability
- Includes bundled Python scripts for metadata extraction, scaffolding, validation, version bumping, and zip building

## Supported Formats

| Format | What it produces |
|--------|-----------------|
| **Universal repo** | Full repo with ALL formats + CI/CD + version management (recommended) |
| **Claude plugin** | `.claude-plugin/plugin.json` pointing at skills |
| **Claude marketplace** | Plugin + root `marketplace.json` for marketplace distribution |
| **Cursor plugin** | `.cursor-plugin/plugin.json` formatted for Cursor |
| **Agent Skills standard** | `.agents/skills/` directory structure for cross-client interop |
| **ZIP** | Clean zip with path hygiene (also works for ChatGPT, Manus, Codex CLI) |

## Installation

### Claude.ai (Web)

1. Download [`skill-packager-marketplace.zip`](https://github.com/YanivGolan/skill-packager-marketplace/releases/latest/download/skill-packager-marketplace.zip)
2. Click **Customize** in the sidebar
3. Go to **Skills** and click **+**
4. Choose **Upload a skill** and upload the zip file

### Claude Desktop

[![Install in Claude Desktop](https://img.shields.io/badge/Install_in_Claude_Desktop-D97757?style=for-the-badge&logo=claude&logoColor=white)](https://YanivGolan.github.io/skill-packager-marketplace/static/install-claude-desktop.html)

*-- or install manually --*

1. Click **Customize** in the sidebar
2. Click **Browse Plugins**
3. Go to the **Personal** tab and click **+**
4. Choose **Add marketplace**
5. Type `YanivGolan/skill-packager-marketplace` and click **Sync**

### Claude Code (CLI)

From your terminal:

```bash
claude plugin marketplace add https://github.com/YanivGolan/skill-packager-marketplace
claude plugin install skill-packager@skill-packager-marketplace
```

Or from within a Claude Code session:

```
/plugin marketplace add YanivGolan/skill-packager-marketplace
/plugin install skill-packager@skill-packager-marketplace
```

### Cursor

1. Open **Cursor Settings**
2. Paste `https://github.com/YanivGolan/skill-packager-marketplace` into the **Search or Paste Link** box

### Manus

1. Download [`skill-packager-marketplace.zip`](https://github.com/YanivGolan/skill-packager-marketplace/releases/latest/download/skill-packager-marketplace.zip)
2. Go to **Settings** -> **Skills**
3. Click **+ Add** -> **Upload**
4. Upload the zip

### ChatGPT

> **Note:** ChatGPT Skills are currently in beta, available on Business, Enterprise, Edu, Teachers, and Healthcare plans only.

> **Warning:** This skill requires Python 3.9+ which may have limited support in ChatGPT's execution sandbox.

1. Download [`skill-packager-marketplace.zip`](https://github.com/YanivGolan/skill-packager-marketplace/releases/latest/download/skill-packager-marketplace.zip)
2. Upload at [chatgpt.com/skills](https://chatgpt.com/skills)

### Codex CLI

Use the built-in skill installer:

```
$skill-installer https://github.com/YanivGolan/skill-packager-marketplace
```

Or install manually:

1. Download [`skill-packager-marketplace.zip`](https://github.com/YanivGolan/skill-packager-marketplace/releases/latest/download/skill-packager-marketplace.zip)
2. Extract the `skill-packager/` folder to `~/.codex/skills/`

### Any Agent (npx)

Works with Claude Code, Cursor, Copilot, Windsurf, and [40+ other agents](https://github.com/vercel-labs/skills):

```bash
npx skills add YanivGolan/skill-packager-marketplace
```

### Other Tools (Windsurf, etc.)

Download [`skill-packager-marketplace.zip`](https://github.com/YanivGolan/skill-packager-marketplace/releases/latest/download/skill-packager-marketplace.zip) and extract the `skill-packager/` folder to:

- **Project-level**: `.agents/skills/` in your project root
- **User-level**: `~/.agents/skills/`

## Usage

The skill auto-activates when you ask to package or deploy a skill. Examples:

```
Package this skill for distribution
```

```
Create a Claude marketplace plugin from my skill at ./skills/my-skill
```

```
Set up a universal repo for my skill with CI/CD
```

```
Make this skill work on Cursor and ChatGPT
```

## Prerequisites

- Python 3.9+ (for bundled packaging scripts)

## License

MIT

---

Built with [Skill Creator Plus](https://github.com/yaniv-golan/skill-creator-plus) and [Claude Code Internals](https://github.com/yaniv-golan/claude-code-internals).
