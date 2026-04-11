# Changelog

All notable changes to this project will be documented in this file.

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
