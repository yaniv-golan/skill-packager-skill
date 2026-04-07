# Numeric/Table Data Proof Template

> You are reading one template. See [proof-templates.md](proof-templates.md) for the full index and selection guidance.

For proofs where the primary evidence is numeric data from HTML tables (CPI, GDP, population).
Uses `data_values` for table numbers and `verify_data_values()` to confirm they appear on the page.

**Do NOT do this** — pseudo-quote fields with bare numeric literals are circular verification:
```python
# BAD — validator will reject this
empirical_facts = {
    "source_a": {
        "quote": "CPI data is published by the BLS.",
        "url": "...",
        "cpi_1913_quote": "9.883",      # authored literal, not a real quote
        "cpi_2024_quote": "313.689",     # authored literal, not a real quote
    },
}
val = parse_number_from_quote(empirical_facts["source_a"]["cpi_1913_quote"], ...)
verify_extraction(val, empirical_facts["source_a"]["cpi_1913_quote"], ...)  # circular!
```

Instead, use `data_values` + `verify_data_values()` as shown below:

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

from scripts.smart_extract import normalize_unicode
from scripts.verify_citations import verify_all_citations, build_citation_detail, verify_data_values
from scripts.extract_values import parse_number_from_quote
from scripts.computations import compare, explain_calc, cross_check, compute_percentage_change

# 1. CLAIM INTERPRETATION (Rule 4)
CLAIM_NATURAL = "..."
CLAIM_FORMAL = {
    "subject": "...",
    "property": "...",
    "operator": ">",
    "operator_note": "...",
    "threshold": ...,
}

# 2. FACT REGISTRY
FACT_REGISTRY = {
    "B1": {"key": "source_a", "label": "Source A: [description] ([site] sourced from [authority])"},
    "B2": {"key": "source_b", "label": "Source B: [description] ([site] sourced from [authority])"},
    "A1": {"label": "[computation description]", "method": None, "result": None},
    "A2": {"label": "[cross-check computation]", "method": None, "result": None},
}

# 3. EMPIRICAL FACTS — quote verifies source authority, data_values hold the numbers
empirical_facts = {
    "source_a": {
        "quote": "...",  # prose that confirms this source publishes the data
        "url": "...",
        "source_name": "... (sourced from [authority])",
        "data_values": {"val_1913": "9.883", "val_2024": "313.689"},
    },
    "source_b": {
        "quote": "...",
        "url": "...",
        "source_name": "... (sourced from [authority])",
        "data_values": {"val_1913": "9.9", "val_2024": "313.689"},
    },
}

# 4. CITATION VERIFICATION (Rule 2) — verifies quotes
citation_results = verify_all_citations(empirical_facts, wayback_fallback=True)

# 5. DATA VALUE VERIFICATION — confirms numbers appear on page
dv_results_a = verify_data_values(
    empirical_facts["source_a"]["url"],
    empirical_facts["source_a"]["data_values"],
    "B1",
)
dv_results_b = verify_data_values(
    empirical_facts["source_b"]["url"],
    empirical_facts["source_b"]["data_values"],
    "B2",
)

# 6. VALUE EXTRACTION — parse from data_values strings (no verify_extraction needed)
val_1913_a = parse_number_from_quote(empirical_facts["source_a"]["data_values"]["val_1913"], r"([\d.]+)", "B1_val_1913")
val_2024_a = parse_number_from_quote(empirical_facts["source_a"]["data_values"]["val_2024"], r"([\d.]+)", "B1_val_2024")
val_1913_b = parse_number_from_quote(empirical_facts["source_b"]["data_values"]["val_1913"], r"([\d.]+)", "B2_val_1913")
val_2024_b = parse_number_from_quote(empirical_facts["source_b"]["data_values"]["val_2024"], r"([\d.]+)", "B2_val_2024")

# 7. CROSS-CHECK (Rule 6) — independent sources must agree within tolerance
# Use mode="relative" when comparing values that may be rounded differently
cross_check(val_1913_a, val_1913_b, tolerance=0.02, mode="relative", label="1913 value cross-check")
cross_check(val_2024_a, val_2024_b, tolerance=0.001, mode="relative", label="2024 value cross-check")

# 8. COMPUTATION (Rule 7)
# For purchasing power / inflation: use compute_percentage_change(old, new, mode="decline")
# For growth rates: use compute_percentage_change(old, new) (default mode="increase")
decline_a = compute_percentage_change(val_1913_a, val_2024_a, mode="decline", label="decline_source_a")
decline_b = compute_percentage_change(val_1913_b, val_2024_b, mode="decline", label="decline_source_b")

# 9. CLAIM EVALUATION
claim_holds = compare(decline_a, CLAIM_FORMAL["operator"], CLAIM_FORMAL["threshold"])

# 10. ADVERSARIAL CHECKS (Rule 5)
adversarial_checks = [
    {
        "question": "...",
        "verification_performed": "Searched for ...",
        "finding": "...",  # If counter-evidence found AND breaks_proof=False: MUST include explicit rebuttal (Rule 5)
        "breaks_proof": False,  # If True, verdict forced to UNDETERMINED
    },
]

# 11. VERDICT AND STRUCTURED OUTPUT
if __name__ == "__main__":
    any_unverified = any(
        cr["status"] != "verified" for cr in citation_results.values()
    )
    any_breaks = any(ac.get("breaks_proof") for ac in adversarial_checks)
    # Set to True if the source itself flags overlapping uncertainty ranges
    # for a comparative/superlative claim. See SKILL.md "Comparative claims
    # with source-acknowledged uncertainty."
    uncertainty_override = False  # change to True with documented reason if applicable

    if any_breaks:
        verdict = "UNDETERMINED"
    elif uncertainty_override:
        verdict = "UNDETERMINED"
    elif claim_holds and not any_unverified:
        verdict = "PROVED"
    elif claim_holds and any_unverified:
        verdict = "PROVED (with unverified citations)"
    elif not claim_holds and not any_unverified:
        verdict = "DISPROVED"
    elif not claim_holds and any_unverified:
        verdict = "DISPROVED (with unverified citations)"
    else:
        verdict = "UNDETERMINED"

    FACT_REGISTRY["A1"]["method"] = "compute_percentage_change(mode='decline')"
    FACT_REGISTRY["A1"]["result"] = f"{decline_a:.4f}%"
    FACT_REGISTRY["A2"]["method"] = "compute_percentage_change(mode='decline') [cross-check]"
    FACT_REGISTRY["A2"]["result"] = f"{decline_b:.4f}%"

    citation_detail = build_citation_detail(FACT_REGISTRY, citation_results, empirical_facts)

    # For data_values proofs, extractions use sub-IDs and note the data source
    extractions = {
        "B1_val_1913": {"value": str(val_1913_a), "value_in_quote": True, "quote_snippet": "data_values['val_1913']"},
        "B1_val_2024": {"value": str(val_2024_a), "value_in_quote": True, "quote_snippet": "data_values['val_2024']"},
        "B2_val_1913": {"value": str(val_1913_b), "value_in_quote": True, "quote_snippet": "data_values['val_1913']"},
        "B2_val_2024": {"value": str(val_2024_b), "value_in_quote": True, "quote_snippet": "data_values['val_2024']"},
    }

    # Include data value verification results
    data_value_verification = {
        "B1": {k: v for k, v in dv_results_a.items()},
        "B2": {k: v for k, v in dv_results_b.items()},
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
        "data_value_verification": data_value_verification,
        "cross_checks": [
            {"description": "1913 values", "values_compared": [str(val_1913_a), str(val_1913_b)],
             "agreement": True, "tolerance": "2% relative"},
            {"description": "2024 values", "values_compared": [str(val_2024_a), str(val_2024_b)],
             "agreement": True, "tolerance": "0.1% relative"},
        ],
        "adversarial_checks": adversarial_checks,
        "verdict": verdict,
        "key_results": {
            "decline_source_a": decline_a,
            "decline_source_b": decline_b,
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
