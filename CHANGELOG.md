# Changelog

All notable changes to this project will be documented in this file.

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
