# Proof Engine

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Agent Skills Compatible](https://img.shields.io/badge/Agent_Skills-compatible-4A90D9)](https://agentskills.io)
[![Claude Code Plugin](https://img.shields.io/badge/Claude_Code-plugin-F97316)](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/plugins)
[![Cursor Plugin](https://img.shields.io/badge/Cursor-plugin-00D886)](https://cursor.com/docs/plugins)

Create formal, verifiable proofs of claims with machine-checkable reasoning.

Uses the open [Agent Skills](https://agentskills.io) standard. Works with Claude Desktop, Claude Cowork, Claude Code, Codex CLI, Cursor, Windsurf, Manus, ChatGPT, and any other compatible tool.

## What It Does

- Produces formal proofs with machine-checkable reasoning for mathematical, empirical, and mixed claims
- Every fact is either computed by re-runnable Python code (Type A) or backed by a specific source, URL, and exact quote (Type B)
- Generates three outputs: a `proof.py` script anyone can re-run, a reader-facing `proof.md`, and a `proof_audit.md` with full verification details
- Includes bundled scripts for citation verification, value extraction, computation, and static analysis
- Enforces 7 hardening rules that close common LLM failure modes (hallucinated citations, hand-typed values, confirmation bias, etc.)

## Prerequisites

- Python 3
- `requests` library (for empirical/Type B proofs with citation verification)
- Optional: `pdfplumber` (PDF citation sources), `sympy` (symbolic math proofs)

## Installation

### Claude.ai (Web)

1. Download [`proof-engine-skill.zip`](https://github.com/yaniv-golan/proof-engine-skill/releases/latest/download/proof-engine-skill.zip)
2. Click **Customize** in the sidebar
3. Go to **Skills** and click **+**
4. Choose **Upload a skill** and upload the zip file

### Claude Desktop

1. Click **Customize** in the sidebar
2. Click **Browse Plugins**
3. Go to the **Personal** tab and click **+**
4. Choose **Add marketplace**
5. Type `yaniv-golan/proof-engine-skill` and click **Sync**

### Claude Code (CLI)

From your terminal:

```bash
claude plugin marketplace add https://github.com/yaniv-golan/proof-engine-skill
claude plugin install proof-engine@proof-engine-marketplace
```

Or from within a Claude Code session:

```
/plugin marketplace add yaniv-golan/proof-engine-skill
/plugin install proof-engine@proof-engine-marketplace
```

### Cursor

1. Open **Cursor Settings**
2. Paste `https://github.com/yaniv-golan/proof-engine-skill` into the **Search or Paste Link** box

### Manus

1. Download [`proof-engine-skill.zip`](https://github.com/yaniv-golan/proof-engine-skill/releases/latest/download/proof-engine-skill.zip)
2. Go to **Settings** -> **Skills**
3. Click **+ Add** -> **Upload**
4. Upload the zip

### ChatGPT

> **Note:** ChatGPT Skills are currently in beta, available on Business, Enterprise, Edu, Teachers, and Healthcare plans only.

> **Warning:** This skill requires Python with the `requests` library and outbound HTTP access for Type B (empirical) proofs, which may not be fully available in ChatGPT's execution sandbox.

1. Download [`proof-engine-skill.zip`](https://github.com/yaniv-golan/proof-engine-skill/releases/latest/download/proof-engine-skill.zip)
2. Upload at [chatgpt.com/skills](https://chatgpt.com/skills)

### Codex CLI

Use the built-in skill installer:

```
$skill-installer https://github.com/yaniv-golan/proof-engine-skill
```

Or install manually:

1. Download [`proof-engine-skill.zip`](https://github.com/yaniv-golan/proof-engine-skill/releases/latest/download/proof-engine-skill.zip)
2. Extract the `proof-engine/` folder to `~/.codex/skills/`

### Any Agent (npx)

Works with Claude Code, Cursor, Copilot, Windsurf, and [40+ other agents](https://github.com/vercel-labs/skills):

```bash
npx skills add yaniv-golan/proof-engine-skill
```

### Other Tools (Windsurf, etc.)

Download [`proof-engine-skill.zip`](https://github.com/yaniv-golan/proof-engine-skill/releases/latest/download/proof-engine-skill.zip) and extract the `proof-engine/` folder to:

- **Project-level**: `.agents/skills/` in your project root
- **User-level**: `~/.agents/skills/`

## Usage

The skill auto-activates when you ask it to prove, verify, fact-check, or rigorously establish whether a claim is true or false. Examples:

```
Can you prove that the sum of the first 1000 prime numbers is itself a prime number?
```

```
Is it really true that the State of Israel is over 70 years old? Prove it rigorously.
```

```
Fact-check this: Earth's average temperature has risen by more than 1 degree Celsius since 1880.
```

## License

MIT
