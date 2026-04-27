# Changelog

All notable changes to this project will be documented in this file.

## [0.2.1]

### Changed
- Bump GitHub Actions to Node.js 24-compatible majors in both live workflows
  and embedded templates: `actions/checkout@v4` → `@v6`,
  `actions/setup-python@v5` → `@v6`, `softprops/action-gh-release@v2` → `@v3`,
  `actions/upload-pages-artifact@v4` → `@v5`, `actions/deploy-pages@v4` → `@v5`.
  Avoids GitHub's June 2026 forced Node 24 migration warning.

## [0.2.0]

### Changed
- **Manifest renamed** `meta.json` → `skill-packager.json`. Existing repos
  continue to work in 0.2.x with a deprecation warning. Migration: rename the
  file at the repo root; if you've copied `tools/build-zip.py` or
  `tools/bump-version.py` into your downstream repo, update them from this
  release as well.
- New `tools/sync-agents-mirror.py` to keep the `.agents/` mirror in sync with
  canonical skill source.

### Deprecated
- Reading `meta.json` at the repo root. Will be removed in 0.3.0.

## [0.1.3] - 2026-04-14

### Fixed

- Fix `actions/checkout@v6` (non-existent) in generated `release.yml` and `deploy-pages.yml` — both now emit `actions/checkout@v4`
- Fix zip filename mismatch: `build-zip.py` and `release.yml` now name the artifact after `plugin_name` instead of `github_repo`, so the download URL in README always matches the uploaded artifact

## [0.1.2] - 2026-04-11

### Added

- OpenClaw/ClawHub platform support: formats.md section, platforms.md install instructions, SKILL.md note
- Improved NanoClaw documentation: accurate skill type coverage, upstream links, per-platform install instructions
- SKILL.md line-count validation warning (500-line limit, enforced by NanoClaw)
- 2 new validation tests (74 total)

## [0.1.1] - 2026-04-08

### Fixed

- Fix script invocation: scripts must be run as `python3 -m skill_packager` from the `scripts/` directory, not as `python3 scripts/skill_packager`
- Add name-to-path resolution guidance when user supplies a skill name instead of a full path
- Clarify that the `../<skill-name>-skill/` output option is relative to CWD, not to the skill source directory
- Flag that `marketplace_name` in extracted metadata needs a `-marketplace` suffix (the script omits it)
- Flag that extracted `description` must be truncated to first sentence for manifests

## [0.1.0] - 2026-04-07

### Added

- Initial release of the Skill Packager skill
- Python CLI with 5 subcommands: `metadata`, `scaffold`, `build-zip`, `validate`, `bump-version`
- Universal repo scaffolding with Claude plugin, Cursor plugin, marketplace manifests, `.agents/skills/`, CI/CD workflows, and version management
- Format-aware validation covering JSON validity, version consistency, skill path resolution, and stub detection
- Path hygiene: `${CLAUDE_SKILL_DIR}/` preserved in canonical copies, stripped in `.agents/skills/` and zip builds
- AskUserQuestion integration for structured format selection and output directory choice
- Cross-platform support: Claude Desktop, Claude Code, Claude.ai, Cursor, Manus, ChatGPT, Codex CLI, Windsurf, NanoClaw
- 72 tests across 8 test files with full integration coverage
