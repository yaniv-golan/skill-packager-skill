# Platform Installation Instructions

Templates for the README.md installation section. Replace `{{variables}}` with actual values.

## Table of Contents

- [Badges](#badges)
- [README structure](#readme-structure)
- [Per-platform instructions](#per-platform-instructions)
- [Platform compatibility notes](#platform-compatibility-notes)

---

## Badges

Include these at the top of the README, after the title:

```markdown
[![Install in Claude Desktop](https://img.shields.io/badge/Install_in_Claude_Desktop-D97757?style=for-the-badge&logo=claude&logoColor=white)](https://{{github-owner}}.github.io/{{github-repo}}/static/install-claude-desktop.html)

[![License: {{license}}](https://img.shields.io/badge/License-{{license}}-blue.svg)](https://opensource.org/licenses/{{license}})
[![Agent Skills Compatible](https://img.shields.io/badge/Agent_Skills-compatible-4A90D9)](https://agentskills.io)
[![Claude Code Plugin](https://img.shields.io/badge/Claude_Code-plugin-F97316)](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/plugins)
[![Cursor Plugin](https://img.shields.io/badge/Cursor-plugin-00D886)](https://cursor.com/docs/plugins)
[![Packaged with Skill Packager](https://img.shields.io/badge/Packaged_with-Skill_Packager-8B5CF6?style=flat-square)](https://github.com/yaniv-golan/skill-packager-skill)
```

The "Install in Claude Desktop" badge goes first as a prominent call-to-action (larger `for-the-badge` style). The "Packaged with Skill Packager" badge is optional — include it by default but the user can remove it.

---

## README structure

```markdown
# {{Skill Display Name}}

[![Install in Claude Desktop](https://img.shields.io/badge/Install_in_Claude_Desktop-D97757?style=for-the-badge&logo=claude&logoColor=white)](https://{{github-owner}}.github.io/{{github-repo}}/static/install-claude-desktop.html)

[![License: {{license}}](https://img.shields.io/badge/License-{{license}}-blue.svg)](https://opensource.org/licenses/{{license}})
[![Agent Skills Compatible](https://img.shields.io/badge/Agent_Skills-compatible-4A90D9)](https://agentskills.io)
[![Claude Code Plugin](https://img.shields.io/badge/Claude_Code-plugin-F97316)](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/plugins)
[![Cursor Plugin](https://img.shields.io/badge/Cursor-plugin-00D886)](https://cursor.com/docs/plugins)
[![Packaged with Skill Packager](https://img.shields.io/badge/Packaged_with-Skill_Packager-8B5CF6?style=flat-square)](https://github.com/yaniv-golan/skill-packager-skill)

{{One-line description of what the skill does.}}

Uses the open [Agent Skills](https://agentskills.io) standard. Works with Claude Desktop, Claude Cowork, Claude Code, Codex CLI, Cursor, Windsurf, Manus, ChatGPT, and any other compatible tool.

## What It Does

{{2-5 bullet points about the skill's capabilities}}

## Installation

{{per-platform sections — see below}}

## Usage

The skill auto-activates when you {{describe trigger conditions}}. Examples:

\`\`\`
{{example prompt 1}}
\`\`\`

\`\`\`
{{example prompt 2}}
\`\`\`

## License

{{license}}
```

---

## Per-platform instructions

Include ALL of the following sections in the README. If a platform is known to be incompatible with this specific skill (e.g., ChatGPT for skills requiring network tools), include the section but add a warning.

### Claude.ai (Web)

```markdown
### Claude.ai (Web)

1. Download [`{{zip-filename}}`](https://github.com/{{github-owner}}/{{github-repo}}/releases/latest/download/{{zip-filename}})
2. Click **Customize** in the sidebar
3. Go to **Skills** and click **+**
4. Choose **Upload a skill** and upload the zip file
```

### Claude Desktop

```markdown
### Claude Desktop

[![Install in Claude Desktop](https://img.shields.io/badge/Install_in_Claude_Desktop-D97757?style=for-the-badge&logo=claude&logoColor=white)](https://{{github-owner}}.github.io/{{github-repo}}/static/install-claude-desktop.html)

*— or install manually —*

1. Click **Customize** in the sidebar
2. Click **Browse Plugins**
3. Go to the **Personal** tab and click **+**
4. Choose **Add marketplace**
5. Type `{{github-owner}}/{{github-repo}}` and click **Sync**
```

### Claude Code (CLI)

```markdown
### Claude Code (CLI)

From your terminal:

\`\`\`bash
claude plugin marketplace add https://github.com/{{github-owner}}/{{github-repo}}
claude plugin install {{plugin-name}}@{{marketplace-name}}
\`\`\`

Or from within a Claude Code session:

\`\`\`
/plugin marketplace add {{github-owner}}/{{github-repo}}
/plugin install {{plugin-name}}@{{marketplace-name}}
\`\`\`
```

### Cursor

```markdown
### Cursor

1. Open **Cursor Settings**
2. Paste `https://github.com/{{github-owner}}/{{github-repo}}` into the **Search or Paste Link** box
```

### Manus

```markdown
### Manus

1. Download [`{{zip-filename}}`](https://github.com/{{github-owner}}/{{github-repo}}/releases/latest/download/{{zip-filename}})
2. Go to **Settings** -> **Skills**
3. Click **+ Add** -> **Upload**
4. Upload the zip
```

### ChatGPT

```markdown
### ChatGPT

> **Note:** ChatGPT Skills are currently in beta, available on Business, Enterprise, Edu, Teachers, and Healthcare plans only.

1. Download [`{{zip-filename}}`](https://github.com/{{github-owner}}/{{github-repo}}/releases/latest/download/{{zip-filename}})
2. Upload at [chatgpt.com/skills](https://chatgpt.com/skills)
```

**When to add a warning:** If the skill requires CLI tools, network access, or a specific runtime that ChatGPT's sandbox doesn't provide, add:

```markdown
> **Warning:** This skill requires {{tool/capability}} which is not available in ChatGPT's execution sandbox. It may not work fully in ChatGPT.
```

### Codex CLI

```markdown
### Codex CLI

Use the built-in skill installer:

\`\`\`
$skill-installer https://github.com/{{github-owner}}/{{github-repo}}
\`\`\`

Or install manually:

1. Download [`{{zip-filename}}`](https://github.com/{{github-owner}}/{{github-repo}}/releases/latest/download/{{zip-filename}})
2. Extract the `{{skill-name}}/` folder to `~/.codex/skills/`
```

### Any Agent (npx)

```markdown
### Any Agent (npx)

Works with Claude Code, Cursor, Copilot, Windsurf, and [40+ other agents](https://github.com/vercel-labs/skills):

\`\`\`bash
npx skills add {{github-owner}}/{{github-repo}}
\`\`\`
```

### Other Tools

```markdown
### Other Tools (Windsurf, etc.)

Download [`{{zip-filename}}`](https://github.com/{{github-owner}}/{{github-repo}}/releases/latest/download/{{zip-filename}}) and extract the `{{skill-name}}/` folder to:

- **Project-level**: `.agents/skills/` in your project root
- **User-level**: `~/.agents/skills/`
```

### NanoClaw

```markdown
### NanoClaw

NanoClaw uses the same plugin marketplace as Claude Code. Install via:

\`\`\`bash
claude plugin marketplace add https://github.com/{{github-owner}}/{{github-repo}}
claude plugin install {{plugin-name}}@{{marketplace-name}} --scope project
\`\`\`

> **Note:** NanoClaw enforces a 500-line limit on SKILL.md files. Skills run inside isolated Docker containers with their own filesystem. Keep instructions concise and move detail to reference files.
```

---

## Platform compatibility notes

Use these to decide which warnings to include:

| Platform | Requires network | Has filesystem | Has CLI tools | Has Python | Has Node.js |
|----------|-----------------|----------------|---------------|------------|-------------|
| Claude Code | Yes | Yes | Yes | Yes | Yes |
| Claude Desktop | Yes | Yes | Yes | Yes | Yes |
| Claude.ai | Yes | Sandbox | Limited | Yes (sandbox) | No |
| Cursor | Yes | Yes | Yes | Yes | Yes |
| Codex CLI | Yes | Yes | Yes | Yes | Yes |
| Manus | Yes | Sandbox | Yes (Ubuntu) | Yes | Yes |
| ChatGPT | Limited | Sandbox | Limited | Yes (sandbox) | No |
| Windsurf | Yes | Yes | Yes | Yes | Yes |
| NanoClaw | Yes | Container | Yes (Docker) | Yes | Yes |

**Skills that need specific tools** (e.g., `yt-dlp`, `ffmpeg`): Warn for ChatGPT and note prerequisites for all platforms.

**Skills that need network access**: Warn for ChatGPT (limited outbound).

**Skills with Python scripts**: Work everywhere except possibly ChatGPT (sandbox limitations on pip install).
