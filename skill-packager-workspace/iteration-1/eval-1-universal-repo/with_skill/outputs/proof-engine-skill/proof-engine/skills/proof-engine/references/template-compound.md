# Compound CLAIM_FORMAL Template

> You are reading one template. See [proof-templates.md](proof-templates.md) for the full index and selection guidance.

For claims with multiple sub-claims joined by AND. Each sub-claim gets its own confirmation list, source count, and `compare()` evaluation. The compound verdict aggregates sub-claim results.

**When to use:** The claim contains AND or implies multiple independently verifiable conditions. Examples: "Israel withdrew from Gaza AND Hamas won the 2006 election," "Brain weight is 2% of body weight AND uses 20% of oxygen."

**Not supported:** Negated sub-claims (X BUT NOT Y) require per-sub-claim `proof_direction`, which this template doesn't model. For claims with negated parts, decompose into separate proofs — one affirmative, one disproof — using the qualitative template's `proof_direction` field.

```python
"""
Proof: [compound claim text]
Generated: [date]
"""
import json
import os
import sys

PROOF_ENGINE_ROOT = "..."  # LLM fills with actual path
sys.path.insert(0, PROOF_ENGINE_ROOT)
from datetime import date

from scripts.verify_citations import verify_all_citations, build_citation_detail
from scripts.computations import compare

# 1. CLAIM INTERPRETATION (Rule 4)
CLAIM_NATURAL = "..."
CLAIM_FORMAL = {
    "subject": "...",
    "sub_claims": [
        {"id": "SC1", "property": "...", "operator": ">=", "threshold": 3, "operator_note": "..."},
        {"id": "SC2", "property": "...", "operator": ">=", "threshold": 3, "operator_note": "..."},
    ],
    "compound_operator": "AND",  # only AND is supported; OR claims should be decomposed into separate proofs
    "operator_note": "All sub-claims must hold for the compound claim to be PROVED",
}

# 2. FACT REGISTRY
FACT_REGISTRY = {
    "B1": {"key": "sc1_source_a", "label": "SC1 source A: ..."},
    "B2": {"key": "sc1_source_b", "label": "SC1 source B: ..."},
    "B3": {"key": "sc2_source_a", "label": "SC2 source A: ..."},
    "B4": {"key": "sc2_source_b", "label": "SC2 source B: ..."},
    "A1": {"label": "SC1 source count", "method": None, "result": None},
    "A2": {"label": "SC2 source count", "method": None, "result": None},
}

# 3. EMPIRICAL FACTS — grouped by sub-claim
empirical_facts = {
    "sc1_source_a": {"quote": "...", "url": "...", "source_name": "..."},
    "sc1_source_b": {"quote": "...", "url": "...", "source_name": "..."},
    "sc2_source_a": {"quote": "...", "url": "...", "source_name": "..."},
    "sc2_source_b": {"quote": "...", "url": "...", "source_name": "..."},
}

# 4. CITATION VERIFICATION (Rule 2)
citation_results = verify_all_citations(empirical_facts, wayback_fallback=True)

# 5. COUNT VERIFIED SOURCES PER SUB-CLAIM
COUNTABLE_STATUSES = ("verified", "partial")
sc1_keys = [k for k in empirical_facts if k.startswith("sc1_")]
sc2_keys = [k for k in empirical_facts if k.startswith("sc2_")]

n_sc1 = sum(1 for k in sc1_keys if citation_results[k]["status"] in COUNTABLE_STATUSES)
n_sc2 = sum(1 for k in sc2_keys if citation_results[k]["status"] in COUNTABLE_STATUSES)

# 6. PER-SUB-CLAIM EVALUATION — each uses compare()
sc1_holds = compare(n_sc1, ">=", CLAIM_FORMAL["sub_claims"][0]["threshold"],
                    label="SC1: " + CLAIM_FORMAL["sub_claims"][0]["property"])
sc2_holds = compare(n_sc2, ">=", CLAIM_FORMAL["sub_claims"][1]["threshold"],
                    label="SC2: " + CLAIM_FORMAL["sub_claims"][1]["property"])

# 7. COMPOUND EVALUATION
n_holding = sum([sc1_holds, sc2_holds])
n_total = len(CLAIM_FORMAL["sub_claims"])
claim_holds = compare(n_holding, "==", n_total, label="compound: all sub-claims hold")

# 8. COI FLAGS — per sub-claim, defined before verdict
sc1_coi_flags = [
    # Populate during proof writing. Empty list if no COI identified.
]
sc2_coi_flags = [
    # Populate during proof writing. Empty list if no COI identified.
]

# 9. ADVERSARIAL CHECKS (Rule 5)
adversarial_checks = [
    {
        "question": "...",
        "verification_performed": "Searched for ...",
        "finding": "...",  # If counter-evidence found AND breaks_proof=False: MUST include explicit rebuttal (Rule 5)
        "breaks_proof": False,  # If True, verdict forced to UNDETERMINED
    },
]

# 10. VERDICT — handles mixed results, proof direction, and unverified citations
if __name__ == "__main__":
    any_unverified = any(
        cr["status"] != "verified" for cr in citation_results.values()
    )
    any_breaks = any(ac.get("breaks_proof") for ac in adversarial_checks)
    is_disproof = CLAIM_FORMAL.get("proof_direction") == "disprove"

    # Per-sub-claim COI gate (Rule 6)
    sc1_confirmed_keys = {k for k in sc1_keys
                          if citation_results[k]["status"] in COUNTABLE_STATUSES}
    sc1_coi_favorable = {f["source_key"] for f in sc1_coi_flags
                         if f["direction"] == "favorable_to_subject"
                         and f["source_key"] in sc1_confirmed_keys}
    sc1_coi_unfavorable = {f["source_key"] for f in sc1_coi_flags
                           if f["direction"] == "unfavorable_to_subject"
                           and f["source_key"] in sc1_confirmed_keys}
    sc1_coi_majority = max(len(sc1_coi_favorable), len(sc1_coi_unfavorable)) if sc1_coi_flags else 0
    sc1_coi_override = n_sc1 > 0 and sc1_coi_majority > n_sc1 / 2

    sc2_confirmed_keys = {k for k in sc2_keys
                          if citation_results[k]["status"] in COUNTABLE_STATUSES}
    sc2_coi_favorable = {f["source_key"] for f in sc2_coi_flags
                         if f["direction"] == "favorable_to_subject"
                         and f["source_key"] in sc2_confirmed_keys}
    sc2_coi_unfavorable = {f["source_key"] for f in sc2_coi_flags
                           if f["direction"] == "unfavorable_to_subject"
                           and f["source_key"] in sc2_confirmed_keys}
    sc2_coi_majority = max(len(sc2_coi_favorable), len(sc2_coi_unfavorable)) if sc2_coi_flags else 0
    sc2_coi_override = n_sc2 > 0 and sc2_coi_majority > n_sc2 / 2

    any_coi_override = sc1_coi_override or sc2_coi_override

    # Contested qualifier override: SC1 holds + SC2 fails → DISPROVED
    # (assertion exists but the epistemic qualifier is not warranted).
    # For non-contested-qualifier compounds, set is_contested_qualifier = False
    # and this branch is skipped.
    is_contested_qualifier = "qualifier" in CLAIM_FORMAL.get("operator_note", "").lower()

    if any_breaks:
        verdict = "UNDETERMINED"
    elif any_coi_override:
        verdict = "UNDETERMINED"
    elif is_contested_qualifier and sc1_holds and not sc2_holds:
        if any_unverified:
            verdict = "DISPROVED (with unverified citations)"
        else:
            verdict = "DISPROVED"
    elif not claim_holds and n_holding > 0:
        verdict = "PARTIALLY VERIFIED"
    elif claim_holds and not any_unverified:
        verdict = "DISPROVED" if is_disproof else "PROVED"
    elif claim_holds and any_unverified:
        verdict = ("DISPROVED (with unverified citations)" if is_disproof
                   else "PROVED (with unverified citations)")
    elif not claim_holds and n_holding == 0:
        verdict = "UNDETERMINED"
    else:
        verdict = "UNDETERMINED"

    FACT_REGISTRY["A1"]["method"] = f"count(verified sc1 citations) = {n_sc1}"
    FACT_REGISTRY["A1"]["result"] = str(n_sc1)
    FACT_REGISTRY["A2"]["method"] = f"count(verified sc2 citations) = {n_sc2}"
    FACT_REGISTRY["A2"]["result"] = str(n_sc2)

    citation_detail = build_citation_detail(FACT_REGISTRY, citation_results, empirical_facts)

    # Extractions: each B-type fact records citation status
    extractions = {}
    for fid, info in FACT_REGISTRY.items():
        if not fid.startswith("B"):
            continue
        ef_key = info["key"]
        cr = citation_results.get(ef_key, {})
        extractions[fid] = {
            "value": cr.get("status", "unknown"),
            "value_in_quote": cr.get("status") in COUNTABLE_STATUSES,
            "quote_snippet": empirical_facts[ef_key]["quote"][:80],
        }

    summary = {
        "fact_registry": {fid: dict(info) for fid, info in FACT_REGISTRY.items()},
        "claim_formal": CLAIM_FORMAL,
        "claim_natural": CLAIM_NATURAL,
        "citations": citation_detail,
        "extractions": extractions,
        "cross_checks": [
            {"description": "SC1: independent sources consulted",
             "n_sources_consulted": len(sc1_keys), "n_sources_verified": n_sc1,
             "sources": {k: citation_results[k]["status"] for k in sc1_keys},
             "independence_note": "Sources from different publications",
             "coi_flags": sc1_coi_flags},
            {"description": "SC2: independent sources consulted",
             "n_sources_consulted": len(sc2_keys), "n_sources_verified": n_sc2,
             "sources": {k: citation_results[k]["status"] for k in sc2_keys},
             "independence_note": "Sources from different publications",
             "coi_flags": sc2_coi_flags},
        ],
        "sub_claim_results": [
            {"id": "SC1", "n_confirming": n_sc1,
             "threshold": CLAIM_FORMAL["sub_claims"][0]["threshold"], "holds": sc1_holds},
            {"id": "SC2", "n_confirming": n_sc2,
             "threshold": CLAIM_FORMAL["sub_claims"][1]["threshold"], "holds": sc2_holds},
        ],
        "adversarial_checks": adversarial_checks,
        "verdict": verdict,
        "key_results": {
            "n_holding": n_holding,
            "n_total": n_total,
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

**Key design points:**
- `PARTIALLY VERIFIED` is checked BEFORE the `claim_holds` branches — mixed results short-circuit the verdict.
- For **contested qualifier** claims: `is_contested_qualifier` auto-detects from `operator_note` and inserts a `sc1_holds and not sc2_holds → DISPROVED` branch before `PARTIALLY VERIFIED`. This ensures "assertion exists but qualifier is unwarranted" produces DISPROVED, not PARTIALLY VERIFIED. Standard compound claims are unaffected.
- `UNDETERMINED` when no sub-claims meet threshold — for source-counting proofs, insufficient evidence is not disproof.
- Per-sub-claim `compare()` calls use labels, so the computation trace is self-documenting.
- `any_unverified` modifies PROVED → PROVED (with unverified citations). For PARTIALLY VERIFIED and UNDETERMINED, citation status is documented in proof.md's Conclusion section rather than changing the verdict label — those verdicts already signal incompleteness.
- `sub_claim_results` in the JSON summary gives downstream tooling per-SC detail.
- Only `AND` compounds are supported. For OR claims ("X or Y is true"), decompose into separate proofs — an OR compound where either sub-claim suffices is just two independent proofs.

**Adapting for numeric compound claims:** Replace the citation-counting step with `parse_number_from_quote()` / `verify_data_values()` per the Numeric/Table template. The compound evaluation (steps 6-7) stays the same — only the per-sub-claim counting (step 5) changes.

**Sub-claims with no possible supporting sources:** Keep the sub-claim in `CLAIM_FORMAL["sub_claims"]` with its full structure — do not remove it from `n_total`. Set its `n_confirming` to 0 via an empty confirmations list (not a hardcoded literal). The compound verdict will naturally produce `PARTIALLY VERIFIED` (some hold, some don't) or `UNDETERMINED` (none hold). Removing a failing sub-claim from the denominator would change the claim's meaning and could turn a failing proof into a passing one. Document the sub-claim's failure and the evidence for it (e.g., adversarial findings) in the proof's adversarial_checks section.

### Adaptation: Contested Qualifier Claims

When a claim bundles a factual assertion with an epistemic qualifier ("verified," "confirmed," "proven," "established," "debunked"), decompose into:

- **SC1 (provenance):** Do the underlying assertions exist and originate from an identifiable source? SC1 means "the assertion exists and can be traced to an identifiable source" — NOT "the assertion is true."
- **SC2 (epistemic):** Has the assertion been independently verified/confirmed/etc. as claimed? SC2 is a meta-claim requiring different sources than SC1: independent audits, judicial findings, investigative bodies — entities that *evaluated* the evidence, not just reported it.

**Empty SC2 is expected.** For many contested qualifier claims, no sources exist that *confirm* independent verification — the qualifier simply hasn't been warranted. In this case, `sc2_keys` is empty and `n_sc2 = 0`, which causes SC2 to fail naturally. This is the normal pattern, not an error. Sources that *reject* the qualifier (e.g., an independent review finding "claims not substantiated") belong in `adversarial_checks`, not in SC2's `empirical_facts` — they are counter-evidence, not confirming sources.

**COI gate and provenance (SC1).** COI does not undermine provenance sources — a biased or interested party can still confirm that an allegation was made. For SC1 (provenance), bypass the COI gate:

```python
# In the COI gate section, replace the standard sc1_coi_override line with:
sc1_coi_override = False  # Provenance: COI does not invalidate "allegation was made"
```

COI is especially critical for SC2 — apply Rule 6 COI check rigorously.

**Verdict mapping** follows the compound template's existing logic:

| SC1 | SC2 | Verdict |
|-----|-----|---------|
| holds | holds | PROVED (assertion exists and qualifier is warranted) |
| holds | fails | DISPROVED (assertion exists but qualifier is false) |
| fails | fails | UNDETERMINED (insufficient evidence either way) |

Note: SC1-fails/SC2-holds is not a realistic state for this pattern — if the assertion's provenance can't be established (SC1 fails), there's nothing for SC2 to verify. The compound template's standard `n_holding > 0` → PARTIALLY VERIFIED branch handles this edge case if it ever arises, but no special logic is needed.

If SC1 fails because sources actively deny the assertion was ever made (not just absence of evidence), document this in `adversarial_checks` with `breaks_proof: True`. The `any_breaks` check at the top of the verdict block will force UNDETERMINED, and the proof.md Conclusion section should explain that the assertion's provenance itself is disputed.

**Example CLAIM_FORMAL:**

```python
CLAIM_FORMAL = {
    "subject": "...",
    "sub_claims": [
        {"id": "SC1", "property": "assertion originates from identifiable source",
         "operator": ">=", "threshold": 2,
         "operator_note": "SC1 checks provenance — does the assertion exist?"},
        {"id": "SC2", "property": "assertion independently verified as claimed",
         "operator": ">=", "threshold": 3,
         "operator_note": "SC2 checks the epistemic qualifier — was it independently verified?"},
    ],
    "compound_operator": "AND",
    "operator_note": (
        "The claim uses the qualifier '[qualifier]'. SC1 checks provenance "
        "(the assertion exists), SC2 checks the qualifier (independently verified). "
        "Both must hold for the claim to be PROVED."
    ),
}
```
