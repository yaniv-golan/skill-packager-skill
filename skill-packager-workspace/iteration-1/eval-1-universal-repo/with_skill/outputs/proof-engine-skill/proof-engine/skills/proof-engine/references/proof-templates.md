# Proof Templates

Read this at **Step 3** when writing proof code. Choose the template that matches your claim type, then read the specific template file.

## Template Selection

| Claim type | Template file | When to use |
|------------|--------------|-------------|
| Date/age | [template-date-age.md](template-date-age.md) | Claim about when something happened or how old it is |
| Numeric/table data | [template-numeric.md](template-numeric.md) | CPI, GDP, population — primary evidence from HTML tables |
| Qualitative consensus | [template-qualitative.md](template-qualitative.md) | "Sources agree X is true" — source count, not numeric comparison |
| Compound (X AND Y) | [template-compound.md](template-compound.md) | Multiple independently verifiable sub-claims |
| Absence of evidence | [template-absence.md](template-absence.md) | "No published evidence that X causes Y" |
| Pure math | [template-pure-math.md](template-pure-math.md) | Entirely mathematical, no empirical sources |

## Decision Flowchart

1. Is the claim purely mathematical (no empirical sources)? → **Pure math**
2. Does the claim assert absence of evidence? → **Absence**
3. Does the claim have multiple sub-claims (X AND Y, X BECAUSE Y)? → **Compound**
4. Does the claim use an epistemic qualifier ("verified," "confirmed," "proven")? → **Compound** (contested qualifier pattern)
5. Does the claim use causal language ("causes," "leads to")? → **Compound** (causal decomposition)
6. Is the primary evidence numeric data from tables? → **Numeric/table**
7. Is the claim about a date or age? → **Date/age**
8. Does the claim depend on expert/source agreement? → **Qualitative consensus**

## Key Structural Elements (All Templates)

Every template includes:
- `CLAIM_FORMAL` with `operator_note` (Rule 4)
- `FACT_REGISTRY` mapping report IDs to proof-script keys
- `compare()` for claim evaluation (Rule 7)
- `adversarial_checks` with `verification_performed` (Rule 5)
- JSON summary in `__main__` ending with `=== PROOF SUMMARY (JSON) ===`
