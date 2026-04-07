# Media Tools

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Agent Skills Compatible](https://img.shields.io/badge/Agent_Skills-compatible-4A90D9)](https://agentskills.io)
[![Claude Code Plugin](https://img.shields.io/badge/Claude_Code-plugin-F97316)](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/plugins)
[![Cursor Plugin](https://img.shields.io/badge/Cursor-plugin-00D886)](https://cursor.com/docs/plugins)

A plugin bundling two media-related AI skills: **Pretext** (text measurement without DOM reflows) and **YouTube Downloader** (interactive video downloading with yt-dlp).

Uses the open [Agent Skills](https://agentskills.io) standard. Works with Claude Desktop, Claude Cowork, Claude Code, Codex CLI, Cursor, Windsurf, Manus, ChatGPT, and any other compatible tool.

## What It Does

### Pretext

- Helps developers use `@chenglou/pretext`, a 15KB TypeScript text measurement library
- Covers API usage, integration patterns, and critical gotchas
- Guides auto-fit font size, text around obstacles, height estimation, and creative demos
- Provides complete API reference and proven code patterns

### YouTube Downloader

- Downloads YouTube videos interactively with resolution and subtitle selection
- Auto-installs prerequisites (yt-dlp, ffmpeg) if missing
- Supports authentication for age-restricted, private, and members-only content
- Handles error translation with actionable next steps

> **Prerequisites for YouTube Downloader:** Requires `yt-dlp` and `ffmpeg`. The skill auto-installs both via pip if missing. A JavaScript runtime (Node.js or Deno) is optional but recommended for full format detection.

## Installation

### Claude.ai (Web)

1. Download [`media-tools-plugin.zip`](https://github.com/yaniv-golan/media-tools-plugin/releases/latest/download/media-tools-plugin.zip)
2. Click **Customize** in the sidebar
3. Go to **Skills** and click **+**
4. Choose **Upload a skill** and upload the zip file

### Claude Desktop

1. Click **Customize** in the sidebar
2. Click **Browse Plugins**
3. Go to the **Personal** tab and click **+**
4. Choose **Add marketplace**
5. Type `yaniv-golan/media-tools-plugin` and click **Sync**

### Claude Code (CLI)

From your terminal:

```bash
claude plugin marketplace add https://github.com/yaniv-golan/media-tools-plugin
claude plugin install media-tools@media-tools-marketplace
```

Or from within a Claude Code session:

```
/plugin marketplace add yaniv-golan/media-tools-plugin
/plugin install media-tools@media-tools-marketplace
```

### Cursor

1. Open **Cursor Settings**
2. Paste `https://github.com/yaniv-golan/media-tools-plugin` into the **Search or Paste Link** box

### Manus

1. Download [`media-tools-plugin.zip`](https://github.com/yaniv-golan/media-tools-plugin/releases/latest/download/media-tools-plugin.zip)
2. Go to **Settings** -> **Skills**
3. Click **+ Add** -> **Upload**
4. Upload the zip

### ChatGPT

> **Note:** ChatGPT Skills are currently in beta, available on Business, Enterprise, Edu, Teachers, and Healthcare plans only.

> **Warning:** The YouTube Downloader skill requires `yt-dlp` and `ffmpeg` which are not available in ChatGPT's execution sandbox. It may not work fully in ChatGPT. The Pretext skill works in ChatGPT's sandbox as it only provides guidance (no CLI tools required).

1. Download [`media-tools-plugin.zip`](https://github.com/yaniv-golan/media-tools-plugin/releases/latest/download/media-tools-plugin.zip)
2. Upload at [chatgpt.com/skills](https://chatgpt.com/skills)

### Codex CLI

Use the built-in skill installer:

```
$skill-installer https://github.com/yaniv-golan/media-tools-plugin
```

Or install manually:

1. Download [`media-tools-plugin.zip`](https://github.com/yaniv-golan/media-tools-plugin/releases/latest/download/media-tools-plugin.zip)
2. Extract the `skills/` folder to `~/.codex/skills/`

### Any Agent (npx)

Works with Claude Code, Cursor, Copilot, Windsurf, and [40+ other agents](https://github.com/vercel-labs/skills):

```bash
npx skills add yaniv-golan/media-tools-plugin
```

### Other Tools (Windsurf, etc.)

Download [`media-tools-plugin.zip`](https://github.com/yaniv-golan/media-tools-plugin/releases/latest/download/media-tools-plugin.zip) and extract the `skills/` folder to:

- **Project-level**: `.agents/skills/` in your project root
- **User-level**: `~/.agents/skills/`

## Usage

### Pretext

The skill auto-activates when you mention pretext, text measurement, text layout without DOM, auto-fit font size, or layoutNextLine. Examples:

```
Help me use @chenglou/pretext to auto-fit a headline into 3 lines
```

```
How do I flow text around a circular obstacle with pretext?
```

### YouTube Downloader

The skill auto-activates when you want to download a YouTube video, get subtitles, or mention yt-dlp. Examples:

```
Download this YouTube video: https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

```
Get the subtitles for this YouTube video in English
```

## License

MIT
