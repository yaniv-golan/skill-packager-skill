"""
proof-engine/scripts — Bundled verification modules.

This package serves TWO audiences:

1. **LLM-generated proof.py scripts** import these at runtime:
   - computations.py — verified constants, compare(), cross_check(), explain_calc()
   - extract_values.py — parse dates/numbers/percentages from quote strings
   - smart_extract.py — Unicode normalization, verify_extraction()
   - verify_citations.py — fetch URLs, verify quotes, build citation details
   - fetch.py — HTTP transport layer (used by verify_citations.py)

2. **CI/developer pipeline** runs these as tools:
   - validate_proof.py — static analysis for Hardening Rule compliance (pre-execution)
   - source_credibility.py — offline domain credibility assessment (called by verify_citations.py)
   - ast_helpers.py — AST-based source analysis (used by validate_proof.py)

Supporting files:
   - proof_types.py — TypedDict definitions for proof artifacts (documentation + IDE support)
   - data/*.json — domain classification data for source_credibility.py
"""
