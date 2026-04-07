# Qualitative Consensus Proof Template

> You are reading one template. See [proof-templates.md](proof-templates.md) for the full index and selection guidance.

For claims where evidence is qualitative ("sources agree X is true") rather than numeric. Uses citation verification status as the counting mechanism: a source counts as "confirmed" if its citation was successfully verified (status = `verified` or `partial`).

**When to use:** The claim's truth depends on expert/source agreement, not a numeric comparison. Examples: "The adult brain generates new neurons," "Humans only use 10% of their brain," "Coffee reduces diabetes risk."

**Key differences from numeric templates:**
- Source count is based on citation verification status, not keyword extraction
- `claim_holds` MUST use `compare()` — never hardcode `True` or `False`
- Adversarial sources go in `adversarial_checks` only — NOT in `empirical_facts`

```python
"""
Proof: [claim text]
Generated: [date]
"""
import json
import os
import sys

PROOF_ENGINE_ROOT = "..."  # LLM fills this with the actual path at proof-writing time
sys.path.insert(0, PROOF_ENGINE_ROOT)
from datetime import date

from scripts.verify_citations import verify_all_citations, build_citation_detail
from scripts.computations import compare

# 1. CLAIM INTERPRETATION (Rule 4)
CLAIM_NATURAL = "..."
CLAIM_FORMAL = {
    "subject": "...",
    "property": "...",
    "operator": ">=",
    "operator_note": "...",
    "threshold": 3,            # min verified sources needed (see threshold guidance below)
    "proof_direction": "affirm",  # "affirm" or "disprove"
}

# 2. FACT REGISTRY
FACT_REGISTRY = {
    "B1": {"key": "source_a", "label": "..."},
    "B2": {"key": "source_b", "label": "..."},
    "B3": {"key": "source_c", "label": "..."},
    "A1": {"label": "Verified source count", "method": None, "result": None},
}

# 3. EMPIRICAL FACTS — sources that confirm the proof's conclusion
# For affirmative proofs: sources that AGREE with the claim
# For disproofs: sources that REJECT the claim (confirm it's false)
# IMPORTANT: adversarial sources go in adversarial_checks, NOT here.
empirical_facts = {
    "source_a": {
        "quote": "...", "url": "...", "source_name": "...",
    },
    "source_b": {
        "quote": "...", "url": "...", "source_name": "...",
    },
    "source_c": {
        "quote": "...", "url": "...", "source_name": "...",
    },
}

# 4. CITATION VERIFICATION (Rule 2)
citation_results = verify_all_citations(empirical_facts, wayback_fallback=True)

# 5. COUNT SOURCES WITH VERIFIED CITATIONS
# A source counts toward the threshold if its quote was found on the page
# (status = "verified" or "partial"). Sources with "not_found" or "fetch_failed"
# are excluded — we can't confirm the quote exists.
# Note: "partial" counts toward the threshold but still triggers the
# "with unverified citations" verdict variant (it's not fully verified).
COUNTABLE_STATUSES = ("verified", "partial")
n_confirmed = sum(
    1 for key in empirical_facts
    if citation_results[key]["status"] in COUNTABLE_STATUSES
)
print(f"  Confirmed sources: {n_confirmed} / {len(empirical_facts)}")

# 6. CLAIM EVALUATION — MUST use compare(), never hardcode claim_holds
claim_holds = compare(n_confirmed, CLAIM_FORMAL["operator"], CLAIM_FORMAL["threshold"],
                      label="verified source count vs threshold")

# 7. COI FLAGS — authored data, defined before verdict (like adversarial_checks)
# Populate during proof writing. Empty list if no COI identified.
coi_flags = [
    # Example:
    # {"source_key": "source_a", "coi_type": "organizational",
    #  "relationship": "Source is a subsidiary of the claim's subject",
    #  "direction": "favorable_to_subject", "severity": "direct"},
]

# 8. ADVERSARIAL CHECKS (Rule 5)
adversarial_checks = [
    {
        "question": "...",
        "verification_performed": "Searched for ...",
        "finding": "...",  # If counter-evidence found AND breaks_proof=False: MUST include explicit rebuttal (Rule 5)
        "breaks_proof": False,  # If True, verdict forced to UNDETERMINED
    },
]

# 9. VERDICT AND STRUCTURED OUTPUT
if __name__ == "__main__":
    # "partial" counts toward the threshold but is NOT fully verified —
    # only "verified" is clean. This preserves the existing semantics where
    # partial/fragment matches trigger "with unverified citations" verdicts.
    any_unverified = any(
        cr["status"] != "verified" for cr in citation_results.values()
    )
    is_disproof = CLAIM_FORMAL.get("proof_direction") == "disprove"
    any_breaks = any(ac.get("breaks_proof") for ac in adversarial_checks)

    # COI GATE (Rule 6) — after counting, before verdict
    confirmed_keys = {k for k in empirical_facts
                      if citation_results[k]["status"] in COUNTABLE_STATUSES}
    coi_favorable = {f["source_key"] for f in coi_flags
                     if f["direction"] == "favorable_to_subject"
                     and f["source_key"] in confirmed_keys}
    coi_unfavorable = {f["source_key"] for f in coi_flags
                       if f["direction"] == "unfavorable_to_subject"
                       and f["source_key"] in confirmed_keys}
    coi_majority = max(len(coi_favorable), len(coi_unfavorable)) if coi_flags else 0
    coi_override = n_confirmed > 0 and coi_majority > n_confirmed / 2

    if any_breaks:
        verdict = "UNDETERMINED"
    elif coi_override:
        verdict = "UNDETERMINED"
    elif claim_holds and not any_unverified:
        verdict = "DISPROVED" if is_disproof else "PROVED"
    elif claim_holds and any_unverified:
        verdict = ("DISPROVED (with unverified citations)" if is_disproof
                   else "PROVED (with unverified citations)")
    elif not claim_holds:
        verdict = "UNDETERMINED"
    else:
        verdict = "UNDETERMINED"

    FACT_REGISTRY["A1"]["method"] = f"count(verified citations) = {n_confirmed}"
    FACT_REGISTRY["A1"]["result"] = str(n_confirmed)

    citation_detail = build_citation_detail(FACT_REGISTRY, citation_results, empirical_facts)

    # Extractions: for qualitative proofs, each B-type fact records citation status
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
        "fact_registry": {
            fid: {k: v for k, v in info.items()}
            for fid, info in FACT_REGISTRY.items()
        },
        "claim_formal": CLAIM_FORMAL,
        "claim_natural": CLAIM_NATURAL,
        "citations": citation_detail,
        "extractions": extractions,
        # For qualitative proofs, cross_checks documents that multiple independent
        # sources were consulted and how many were successfully verified.
        "cross_checks": [
            {
                "description": "Multiple independent sources consulted",
                "n_sources_consulted": len(empirical_facts),
                "n_sources_verified": n_confirmed,
                "sources": {k: citation_results[k]["status"] for k in empirical_facts},
                "independence_note": "Sources are from different publications/institutions",
                "coi_flags": coi_flags,
            }
        ],
        "adversarial_checks": adversarial_checks,
        "verdict": verdict,
        "key_results": {
            "n_confirmed": n_confirmed,
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

### Disproof variant

To disprove a claim (e.g., "Humans only use 10% of their brain"):

1. Set `CLAIM_FORMAL["proof_direction"]` to `"disprove"` and `threshold` to `3`.
2. In `empirical_facts`, include authoritative sources that **reject** the claim. Choose quotes that clearly express the rejection — the quote must be verifiable on the source page.
3. `n_confirmed` counts sources whose quotes were verified on the live page.
4. `compare(3, ">=", 3)` returns `True`, so `claim_holds = True`.
5. The verdict block maps `claim_holds = True` → `DISPROVED` (via `proof_direction`).
6. In `adversarial_checks`, search for sources that **support** the claim.

No keyword selection is needed — the counting mechanism is citation verification, not keyword matching. The key requirement is that quotes are on-topic and verifiable.

### Adaptation notes

**Compound claims (X AND Y):** See the compound CLAIM_FORMAL variant below.

**Empirical consensus with numeric values:** When multiple sources agree on a specific number (e.g., "86 billion neurons"), use the Numeric/Table template instead — it handles numeric cross-checks better than keyword extraction.

**Citing structured/tabular data:** See the Numeric/Table Data template above. Key points:
- Quote verifies source authority; `data_values` hold the numbers
- Call `verify_data_values()` to confirm numbers appear on the source page
- Do NOT call `verify_extraction()` on data_values (circular)
- Use `cross_check()` with tolerance to compare across sources
- Use sub-IDs in extractions: `B1_val_1913`, `B1_val_2024`
