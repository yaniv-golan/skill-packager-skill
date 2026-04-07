# Self-Critique Checklist

Read this at **Step 6** before presenting results.

**Must-check** items are structural — if these fail, the proof is broken. **Verify** items are quality checks.

## Must-check (structural correctness)

- [ ] validate_proof.py passes
- [ ] proof.py includes FACT_REGISTRY with IDs for all facts
- [ ] proof.py `__main__` emits `=== PROOF SUMMARY (JSON) ===` block
- [ ] JSON summary contains required keys: fact_registry (with method/result for A-types), claim_formal, adversarial_checks, verdict, key_results
- [ ] JSON summary contains `generator` block with `name`, `version`, `repo`, `generated_at`
- [ ] For empirical proofs: JSON summary also contains citations (with normalized status/method/coverage_pct/credibility), extractions, cross_checks
- [ ] For pure-math proofs: omit citations and extractions keys entirely. Use [template-pure-math.md](template-pure-math.md).
- [ ] FACT_REGISTRY keys in JSON match IDs used in both report documents
- [ ] Every fact ID in proof.md appears in JSON summary fact_registry and proof_audit.md evidence table
- [ ] All three files are consistent with each other

## Verify (quality and completeness)

- [ ] All 7 hardening rules checked in proof_audit.md hardening checklist
- [ ] proof.md has executive summary with key numbers directly under verdict
- [ ] proof.md verification statuses derivable from JSON summary `citations[].status` (not from message strings)
- [ ] proof.md conclusion addresses unverified/partially verified citations with impact analysis (if any)
- [ ] proof.md conclusion notes low-credibility sources if any cited source has tier ≤ 2
- [ ] proof_audit.md sections labeled with provenance (proof.py JSON summary / proof.py inline output / author analysis)
- [ ] proof_audit.md includes Computation Traces reproduced from inline output
- [ ] proof_audit.md presents "Partially verified" citations distinctly from "Verified"
- [ ] proof_audit.md includes Source Credibility Assessment table (for empirical proofs)
- [ ] proof.md and proof_audit.md end with generator footer line
- [ ] Each adversarial check that found counter-evidence and has `breaks_proof: False` includes an explicit rebuttal in `finding`. Reproducibility/null-result checks are exempt.
- [ ] If claim uses causal language ("causes," "leads to," "promotes," "damages," "prevents"): decomposed into association + causation sub-claims via compound template; verdict is PARTIALLY VERIFIED if only associational evidence found
- [ ] If `threshold < 3`: operator_note documents domain scarcity search, sources meet domain-appropriate quality bar, and no majority COI among threshold sources
- [ ] For comparative/superlative claims: if the cited source flags overlapping uncertainty in the compared values, `uncertainty_override = True` is set and verdict is UNDETERMINED
- [ ] If proof has `empirical_facts`: COI assessed for all citation sources. `coi_flags` populated in `cross_checks` (empty list if no COI identified). For source-counting proofs: majority COI check applied before verdict.
