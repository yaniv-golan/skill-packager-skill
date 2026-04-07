# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.7.0] - 2026-04-06

### Added
- Initial public release as a universal skill repository
- Cross-platform support: Claude Code, Cursor, Windsurf, ChatGPT, Codex CLI, Manus
- GitHub Actions CI/CD pipeline
- Comprehensive README with installation instructions for all platforms
- Claude Code plugin configuration (`.claude/plugin.json`)
- Cursor rules file (`.cursor/rules/proof-engine.mdc`)
- Windsurf rules file (`.windsurfrules`)
- ChatGPT system prompt (`chatgpt/system-prompt.md`)

### Core Features
- 7 Hardening Rules for proof integrity
- 6 proof templates (date/age, numeric, qualitative, compound, absence, pure math)
- Bundled Python verification scripts
- Static proof validator
- Source credibility assessment (offline, domain-based)
- Citation verification with fallback chain (live, snapshot, Wayback)
- PDF text extraction support
- Unicode normalization for cross-site compatibility
