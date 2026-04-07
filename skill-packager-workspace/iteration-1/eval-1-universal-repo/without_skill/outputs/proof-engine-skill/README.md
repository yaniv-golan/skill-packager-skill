# Proof Engine Skill

> Create formal, verifiable proofs of claims with machine-checkable reasoning.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-1.7.0-blue.svg)](./skill/VERSION)

LLMs hallucinate facts and make reasoning errors. Proof Engine overcomes both by offloading all verification to **code** and **citations**. Every fact is either computed by Python code anyone can re-run (Type A) or backed by a specific source, URL, and exact quote (Type B).

## What It Does

When you ask an AI to prove, verify, or fact-check a claim, Proof Engine produces three outputs:
- **`proof.py`** -- a re-runnable Python script that performs all verification
- **`proof.md`** -- a reader-facing report with verdict and evidence
- **`proof_audit.md`** -- full verification details for auditors

Trigger phrases: "is it really true", "can you prove", "verify this", "fact-check this", "prove it", "show me the logic".

## Supported Platforms

### Claude Code (as a skill/plugin)

```bash
# Option 1: Install directly from GitHub
claude plugin add yaniv-golan/proof-engine-skill

# Option 2: Clone and install locally
git clone https://github.com/yaniv-golan/proof-engine-skill.git
cd proof-engine-skill
claude plugin add .
```

Once installed, trigger it by asking Claude to prove or fact-check a claim:
```
Can you prove that the sum of the first 1000 prime numbers is itself a prime number?
```

### Cursor (as a plugin/rule)

1. Clone or download this repository:
   ```bash
   git clone https://github.com/yaniv-golan/proof-engine-skill.git
   ```

2. Copy the `.cursor/rules/proof-engine.mdc` file into your project's `.cursor/rules/` directory:
   ```bash
   mkdir -p .cursor/rules
   cp proof-engine-skill/.cursor/rules/proof-engine.mdc .cursor/rules/
   ```

3. Update the `PROOF_ENGINE_ROOT` path in the rule file to point to where you cloned this repo's `skill/` directory.

4. In Cursor, the skill activates when you ask to prove or fact-check claims.

### Windsurf

1. Clone this repository.
2. Copy `.windsurfrules` to your project root or add its content to your existing `.windsurfrules`.
3. Update `PROOF_ENGINE_ROOT` to point to this repo's `skill/` directory.

### ChatGPT / Custom GPTs

1. Download this repository as a ZIP from the [Releases](https://github.com/yaniv-golan/proof-engine-skill/releases) page.
2. Create a Custom GPT and upload the contents of the `skill/` directory as knowledge files.
3. Copy the system prompt from `chatgpt/system-prompt.md` into your GPT's instructions.
4. Note: ChatGPT's Python sandbox has no outbound HTTP. Use the browsing capability during research to pre-fetch source pages and include them as `snapshot` fields.

### Codex CLI (OpenAI)

1. Clone this repository.
2. Copy `skill/agents/openai.yaml` to your Codex agents directory.
3. Or reference the SKILL.md directly in your Codex system prompt.

### Manus / Other AI Platforms

1. Download this repository as a ZIP.
2. Include the `skill/` directory in your project.
3. Reference `skill/SKILL.md` in your system prompt or agent configuration.
4. Set `PROOF_ENGINE_ROOT` to the absolute path of the `skill/` directory.

### Generic / Manual Integration

For any AI coding environment:

1. Clone or download this repository.
2. Point `PROOF_ENGINE_ROOT` in your proof scripts to the `skill/` directory.
3. The AI reads `skill/SKILL.md` as its instruction set and imports from `skill/scripts/`.

## Requirements

- **Python 3.8+**
- **requests** library (for citation verification)
- Optional: `pdfplumber` (PDF citations), `sympy` (symbolic math), `dateutil` (fuzzy date parsing)

Install dependencies:
```bash
pip install requests
# Optional
pip install pdfplumber sympy python-dateutil
```

## Repository Structure

```
proof-engine-skill/
  skill/                      # The skill itself (portable across platforms)
    SKILL.md                  # Main instruction file
    VERSION                   # Version number
    agents/                   # Platform-specific agent configs
      openai.yaml             # OpenAI/Codex agent definition
    evals/                    # Evaluation test cases
      evals.json              # 13 eval scenarios
    references/               # Reference documentation (read on demand)
      hardening-rules.md      # The 7 hardening rules
      proof-templates.md      # Template selection guide
      output-specs.md         # Output format specifications
      self-critique-checklist.md
      advanced-patterns.md
      environment-and-sources.md
      template-absence.md
      template-compound.md
      template-date-age.md
      template-numeric.md
      template-pure-math.md
      template-qualitative.md
    scripts/                  # Python verification modules
      __init__.py
      ast_helpers.py          # AST-based source analysis
      computations.py         # Verified constants and formulas
      extract_values.py       # Parse values from quotes
      fetch.py                # HTTP transport with fallbacks
      latex_text.py           # LaTeX to text conversion
      proof_types.py          # TypedDict definitions
      smart_extract.py        # Unicode normalization
      source_credibility.py   # Domain credibility assessment
      validate_proof.py       # Static analysis validator
      verify_citations.py     # Citation verification
      data/                   # Domain classification data
        academic_domains.json
        government_tlds.json
        major_news.json
        reference_domains.json
        unreliable_domains.json
  .claude/                    # Claude Code plugin config
    plugin.json
  .cursor/                    # Cursor plugin config
    rules/
      proof-engine.mdc
  .windsurfrules              # Windsurf rules
  chatgpt/                    # ChatGPT integration
    system-prompt.md
  .github/                    # CI/CD
    workflows/
      ci.yml                  # Validation and testing
      release.yml             # Automated releases
  LICENSE                     # MIT License
  pyproject.toml              # Python project metadata
  CHANGELOG.md                # Version history
```

## How It Works

1. **Analyze the Claim** -- classify as mathematical, empirical, or mixed
2. **Gather Facts** -- search for supporting and counter-evidence
3. **Write Proof Code** -- using hardening rules and templates
4. **Validate** -- static analysis for rule compliance
5. **Execute and Report** -- run proof, generate three output files
6. **Self-Critique** -- checklist before presenting results

## Verdicts

| Verdict | Meaning |
|---------|---------|
| **PROVED** | All facts verified, logic valid, conclusion follows |
| **DISPROVED** | Verified counterexample or contradiction found |
| **PARTIALLY VERIFIED** | Some sub-claims met threshold, others did not |
| **SUPPORTED** | Absence-of-evidence threshold met |
| **UNDETERMINED** | Insufficient evidence either way |

Variants with "(with unverified citations)" indicate the logic is valid but some citation URLs could not be fetched for verification.

## Version Management

This project uses [Semantic Versioning](https://semver.org/). The version is tracked in `skill/VERSION` and `pyproject.toml`.

To create a new release:
1. Update `skill/VERSION` and `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create a git tag: `git tag v1.7.0`
4. Push with tags: `git push origin main --tags`
5. The GitHub Actions release workflow will create a GitHub Release automatically.

## Contributing

Contributions are welcome. Please:
1. Fork the repository
2. Create a feature branch
3. Ensure `python skill/scripts/validate_proof.py` passes on any proof scripts
4. Submit a pull request

## License

MIT License. See [LICENSE](./LICENSE) for details.

## Author

Yaniv Golan (yaniv@golan.name)
