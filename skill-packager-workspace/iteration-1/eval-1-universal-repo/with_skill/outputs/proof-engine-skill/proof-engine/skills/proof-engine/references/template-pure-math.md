# Pure-Math Proof Template

> You are reading one template. See [proof-templates.md](proof-templates.md) for the full index and selection guidance.

For claims that are entirely mathematical (no empirical sources, no URLs, no citations).

```python
"""
Proof: [claim text]
Generated: [date]
"""
import json
import os
import sys

PROOF_ENGINE_ROOT = "..."
sys.path.insert(0, PROOF_ENGINE_ROOT)
from datetime import date

from scripts.computations import compare, explain_calc

# 1. CLAIM INTERPRETATION (Rule 4)
CLAIM_NATURAL = "..."
CLAIM_FORMAL = {
    "subject": "...",
    "property": "...",
    "operator": "==",
    "operator_note": "...",
    "threshold": ...,
}

# 2. FACT REGISTRY — A-types only for pure math
FACT_REGISTRY = {
    "A1": {"label": "...", "method": None, "result": None},
    "A2": {"label": "...", "method": None, "result": None},
}

# 3. COMPUTATION — primary method
primary_result = ...

# 4. CROSS-CHECKS — mathematically independent methods (Rule 6)
crosscheck_result = ...
assert primary_result == crosscheck_result, (
    f"Cross-check failed: primary={primary_result}, crosscheck={crosscheck_result}"
)

# 5. ADVERSARIAL CHECKS (Rule 5)
adversarial_checks = [
    {
        "question": "...",
        "verification_performed": "...",
        "finding": "...",  # If counter-evidence found AND breaks_proof=False: MUST include explicit rebuttal (Rule 5)
        "breaks_proof": False,  # If True, verdict forced to UNDETERMINED
    },
]

# 6. VERDICT AND STRUCTURED OUTPUT
if __name__ == "__main__":
    claim_holds = compare(primary_result, CLAIM_FORMAL["operator"], CLAIM_FORMAL["threshold"])
    any_breaks = any(ac.get("breaks_proof") for ac in adversarial_checks)
    # Pure-math: no citations, so no unverified-citation variants needed
    if any_breaks:
        verdict = "UNDETERMINED"
    else:
        verdict = "PROVED" if claim_holds else "DISPROVED"

    FACT_REGISTRY["A1"]["method"] = "..."
    FACT_REGISTRY["A1"]["result"] = str(primary_result)
    FACT_REGISTRY["A2"]["method"] = "..."
    FACT_REGISTRY["A2"]["result"] = str(crosscheck_result)

    summary = {
        "fact_registry": {
            fid: {k: v for k, v in info.items()}
            for fid, info in FACT_REGISTRY.items()
        },
        "claim_formal": CLAIM_FORMAL,
        "claim_natural": CLAIM_NATURAL,
        "cross_checks": [
            {
                "description": "...",
                "values_compared": [str(primary_result), str(crosscheck_result)],
                "agreement": primary_result == crosscheck_result,
            },
        ],
        "adversarial_checks": adversarial_checks,
        "verdict": verdict,
        "key_results": {
            "primary_result": primary_result,
            "threshold": CLAIM_FORMAL["threshold"],
            "operator": CLAIM_FORMAL["operator"],
            "claim_holds": claim_holds,
        },
        "generator": {
            "name": "proof-engine",
            "version": open(os.path.join(PROOF_ENGINE_ROOT, "VERSION")).read().strip(),
            "repo": "https://github.com/yaniv-golan/proof-engine",
            "generated_at": date.today().isoformat(),
        },
    }

    print("\n=== PROOF SUMMARY (JSON) ===")
    print(json.dumps(summary, indent=2, default=str))
```

Key differences from the empirical template:
- No `empirical_facts`, `verify_all_citations`, `extract_values`, or `smart_extract` imports
- No `citations` or `extractions` keys in the JSON summary (omitted, not empty)
- Cross-checks use mathematically independent methods instead of independent sources
- `explain_calc()` is optional — use for scalar expressions; for aggregations over lists, use descriptive `print()` instead

### Adaptation: Open Problems (Unproved Conjectures)

For claims about conjectures that have no known proof or disproof (e.g., "The Goldbach conjecture holds for every even integer greater than 2"):

1. **CLAIM_FORMAL:** Set `operator` to `"=="`, `threshold` to `0` (zero counterexamples expected), and add `"claim_type": "open_problem"` and `"operator_note"` explaining that this is an unresolved conjecture — computational verification provides evidence but not proof.
2. **Computation:** Verify the conjecture computationally up to a large bound (e.g., 10^6). Record the bound explicitly.
3. **Cross-check:** Use a second independent computational method (different algorithm, library, or approach) to verify the same bound.
4. **Adversarial checks:** Search for known counterexample attempts, the current verified bound in the literature, and any conditional results.
5. **Verdict:** Always `UNDETERMINED`. Do NOT use `claim_holds` to drive the verdict — the computational check confirms "no counterexamples found up to N" which is not the same as proving the universal claim. The `operator_note` must state this explicitly.
6. **JSON summary:** Include `"verified_up_to"` in `key_results` documenting the computational bound, and `"counterexamples_found": 0`.

```python
# Example CLAIM_FORMAL for open problems
CLAIM_FORMAL = {
    "subject": "Goldbach conjecture",
    "property": "counterexamples in range [4, 10^6]",
    "operator": "==",
    "threshold": 0,
    "claim_type": "open_problem",
    "operator_note": (
        "Universal conjecture — computational verification up to a finite bound "
        "provides evidence but cannot prove the claim. Verdict is always UNDETERMINED."
    ),
}

# Example verdict logic for open problems
# NOTE: Uses if/else to satisfy check_verdict_branches() in validate_proof.py.
# Both branches produce UNDETERMINED — the conditional documents *why*.
if __name__ == "__main__":
    no_counterexamples = compare(n_counterexamples, "==", 0,
                                  label="no counterexamples in [4, 10^6]")
    if no_counterexamples:
        verdict = "UNDETERMINED"  # verified up to bound, but finite check ≠ proof
    else:
        verdict = "UNDETERMINED"  # counterexample found — but for open problems,
                                  # a counterexample would actually be DISPROVED;
                                  # adjust if your conjecture admits this
```

### Adaptation: Proof-by-Contradiction / Infinite Descent

For proofs that establish truth via logical contradiction rather than direct computation:

1. **Split into verifiable sub-steps:** Decompose the logical argument into steps that CAN be verified computationally. For infinite descent: (a) verify the descent produces a strictly smaller solution for small cases, (b) verify the base case, (c) verify modular constraints.
2. **Each sub-step is a separate A-type fact** with its own `explain_calc()` or `compare()` call.
3. **Cross-check:** Use an independent method (e.g., exhaustive search up to a bound confirming no solutions exist).
4. **Limitations:** Document in `operator_note` that the logical chain (parametrization, factorization, descent step) is presented as prose and not machine-verified. The computational checks verify necessary conditions, not the full argument.
5. **Verdict:** Use PROVED only if the computational verification is sufficient (e.g., exhaustive search for a finite domain). For infinite domains where the proof relies on unverified logical steps, prefer `UNDETERMINED` with documentation of what was verified computationally vs. what relies on the logical argument.

```python
# Example: cross-check via exhaustive search
exhaustive_solutions = [
    (x, y, z) for x in range(1, bound)
    for y in range(x, bound) for z in range(y, bound)
    if x**4 + y**4 == z**4
]
A2_result = compare(len(exhaustive_solutions), "==", 0,
                    label="exhaustive search confirms no solutions")
```
