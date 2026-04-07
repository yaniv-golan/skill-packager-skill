# Media Tools Plugin

A Claude Code marketplace plugin that bundles two skills for media-related development tasks:

1. **Pretext** -- Text measurement without DOM reflows using @chenglou/pretext
2. **YouTube Downloader** -- Interactive YouTube video downloading with yt-dlp

## Installation

### Claude Code

```bash
claude plugin add yaniv-golan/media-tools-plugin
```

Or add to your project's `.claude/plugins.json`:

```json
{
  "plugins": [
    "yaniv-golan/media-tools-plugin"
  ]
}
```

### Cursor

Clone or download this repository into your Cursor plugins directory, or reference it via the `.cursor/plugin.json` manifest included in this package.

## Skills

### Pretext (`/pretext`)

Helps developers integrate [@chenglou/pretext](https://github.com/chenglou/pretext), a 15KB TypeScript library that computes exact text metrics using pure math -- no DOM reflows.

**When to use:**
- Know text dimensions before rendering (virtual scrolling, masonry layouts, card height estimation)
- Auto-fit text to a container (find largest font size within N lines -- CSS has no equivalent)
- Flow text around obstacles (magazine-style layouts)
- Measure text in canvas/SVG/WebGL
- Measure many text items fast (~0.0002ms per `layout()` call)

**Trigger phrases:** pretext, @chenglou/pretext, text measurement, text layout without DOM, text reflow, text around obstacles, auto-fit font size, layoutNextLine, measure text height/width in JavaScript

**Included reference files:**
- `skills/pretext/SKILL.md` -- Main skill instructions with API overview and critical gotchas
- `skills/pretext/references/api.md` -- Complete API reference for all functions and types
- `skills/pretext/references/patterns.md` -- Integration patterns, creative demos, and code examples

### YouTube Downloader (`/youtube-downloader`)

Downloads YouTube videos interactively -- lists available resolutions, checks for subtitles, and lets the user choose exactly what to download.

**When to use:**
- Download a YouTube video at a specific resolution
- Extract audio from YouTube videos
- Download subtitles/captions in SRT format
- Handle age-restricted or authenticated content

**Trigger phrases:** download YouTube video, save video from YouTube, video subtitles, youtube download, yt-dlp, video resolution, SRT subtitles

**Prerequisites (auto-installed):**
- yt-dlp (installed via pip)
- ffmpeg (installed via pip ffmpeg-static or system package manager)
- Node.js (optional, for some format detection)

**Included files:**
- `skills/youtube-downloader/SKILL.md` -- Main skill instructions with full workflow
- `skills/youtube-downloader/agents/openai.yaml` -- OpenAI agent configuration

## Project Structure

```
media-tools-plugin/
  package.json              # npm package manifest with claude-plugin config
  manifest.json             # Claude Code marketplace manifest
  .cursor/
    plugin.json             # Cursor plugin manifest
  skills/
    pretext/
      SKILL.md              # Pretext skill definition
      VERSION               # Version tracking
      references/
        api.md              # Full API reference
        patterns.md         # Integration and creative patterns
    youtube-downloader/
      SKILL.md              # YouTube Downloader skill definition
      agents/
        openai.yaml         # OpenAI agent config
      references/           # (empty, reserved for future use)
  README.md                 # This file
  LICENSE                   # MIT license
```

## License

MIT License. See [LICENSE](LICENSE) for details.

## Author

Yaniv Golan (yaniv@golan.name)

## Links

- GitHub: https://github.com/yaniv-golan/media-tools-plugin
- Pretext library: https://github.com/chenglou/pretext
- yt-dlp: https://github.com/yt-dlp/yt-dlp
