"""
proof_types.py — TypedDict definitions for proof-engine artifacts.

Two categories of types:
  1. **Persisted** (proof.json): CitationEntry, ExtractionRecord, ProofData, etc.
     These match the actual JSON written to disk by build_citation_detail().
  2. **Runtime** (verifier returns): VerificationResult — the dict returned by
     verify_citation() before it's condensed into a CitationEntry.

These types are NOT enforced at runtime (Python TypedDicts are structural hints),
but they:
  - Enable IDE autocompletion and refactoring
  - Serve as authoritative schema documentation
  - Allow mypy/pyright to catch key typos

Authoritative sources for these shapes:
  - tools/validate-site-proof.py (REQUIRED_JSON_KEYS, SEARCH_REGISTRY_AUTHORED_KEYS)
  - proof-engine/skills/proof-engine/references/output-specs.md
  - 47 published proof.json files in site/proofs/
  - tools/lib/verdict.py (VERDICT_TAXONOMY)
"""

from typing import TypedDict, NotRequired


# ---------------------------------------------------------------------------
# Generator metadata
# ---------------------------------------------------------------------------

class Generator(TypedDict):
    name: str                   # "proof-engine"
    version: str                # e.g. "0.10.0"
    repo: str                   # e.g. "https://github.com/yaniv-golan/proof-engine"
    generated_at: str           # ISO date, e.g. "2026-03-28"


# ---------------------------------------------------------------------------
# Claim formal — varies by proof type
# ---------------------------------------------------------------------------

class SubClaim(TypedDict, total=False):
    id: str                     # e.g. "SC1", "SC2a"
    property: str
    operator: str               # ">=", "==", "within", etc.
    threshold: float | int | str
    threshold_pct: float        # used for "within" operator
    operator_note: str


class ClaimFormal(TypedDict, total=False):
    subject: str
    property: str
    operator: str               # ">=", "==", ">", "within"
    threshold: float | int | str
    operator_note: str
    # Compound proofs
    sub_claims: list[SubClaim] | dict[str, SubClaim | str]
    compound_operator: str      # "AND", "OR"
    # Qualitative disproofs
    proof_direction: str        # "disprove", "absence"
    # Open problems
    claim_type: str             # "open_problem"


# ---------------------------------------------------------------------------
# Fact registry
# ---------------------------------------------------------------------------

class FactRegistryEntry(TypedDict, total=False):
    label: str                  # Human-readable description
    key: str                    # Key into empirical_facts (Type B)
    method: str | None          # Computation method (Type A)
    result: object              # Computation result (Type A)


# ---------------------------------------------------------------------------
# Citation verification results
# ---------------------------------------------------------------------------

class CredibilityAssessment(TypedDict, total=False):
    domain: str
    source_type: str            # "government", "academic", "major_news", "reference",
                                # "unknown", "unreliable"
    tier: int                   # 1-5 (5=gov/intergovernmental, 4=academic, 3=news/reference,
                                #       2=unknown, 1=flagged unreliable)
    flags: list[str]            # e.g. ["flagged_unreliable"], ["satire_site"]
    note: str


# --- Persisted in proof.json (built by build_citation_detail) ---

class CitationEntry(TypedDict, total=False):
    source_key: str             # Key into empirical_facts
    source_name: str
    url: str
    quote: str
    status: str                 # "verified", "partial", "not_found", "fetch_failed"
    method: str                 # "full_quote", "unicode_normalized", "fragment",
                                # "aggressive_normalization"
    coverage_pct: float | None
    fetch_mode: str             # "live", "snapshot", "wayback"
    credibility: CredibilityAssessment


# --- Runtime only (returned by verify_citation, NOT persisted) ---

class VerificationResult(TypedDict, total=False):
    status: str                 # "verified", "partial", "not_found", "fetch_failed"
    method: str | None
    coverage_pct: float | None
    fetch_error: str | None
    fetch_mode: str
    message: str
    credibility: CredibilityAssessment


# ---------------------------------------------------------------------------
# Extraction records
# ---------------------------------------------------------------------------

class ExtractionRecord(TypedDict, total=False):
    value: object               # Extracted value (number, date, string)
    value_in_quote: bool        # Whether value was found in the quote text
    verified_via: str           # "verify_extraction", "data_values", etc.
    data_values_verified: bool  # For table-sourced data
    quote_snippet: str          # First ~80 chars of the quote


# ---------------------------------------------------------------------------
# Conflict of Interest flags
# ---------------------------------------------------------------------------

class CoiFlag(TypedDict, total=False):
    source_key: str             # Top-level empirical_facts key
    coi_type: str               # "organizational", "funding_dependency",
                                # "institutional_co_benefit", "competitive_antagonism",
                                # "revolving_door", "advocacy_ideological"
    relationship: str           # Human-readable description
    direction: str              # "favorable_to_subject", "unfavorable_to_subject", "unknown"
    severity: str               # "direct", "indirect", "potential"


# ---------------------------------------------------------------------------
# Cross-checks and adversarial checks
# ---------------------------------------------------------------------------

class CrossCheck(TypedDict, total=False):
    description: str
    # Numeric/date proofs:
    values_compared: list
    agreement: bool
    tolerance: str              # e.g. "2% relative"
    # Source-counting proofs (qualitative, compound):
    n_sources_consulted: int
    n_sources_verified: int
    sources: dict[str, str]
    independence_note: str
    # Absence proofs:
    n_databases_searched: int
    n_null_verified: int
    n_reviewed: int
    databases: dict[str, dict]
    # COI (all proof types with empirical sources):
    coi_flags: list[CoiFlag]    # empty list if no COI identified


class AdversarialCheck(TypedDict, total=False):
    question: str
    search_performed: str       # Used in some proofs
    verification_performed: str  # Alternate key used in some proofs
    finding: str
    breaks_proof: bool


# ---------------------------------------------------------------------------
# Search registry (absence proofs)
# Authoritative field list: tools/validate-site-proof.py SEARCH_REGISTRY_AUTHORED_KEYS
# ---------------------------------------------------------------------------

class SearchRegistryEntry(TypedDict, total=False):
    database: str               # e.g. "PubMed", "Cochrane"
    url: str                    # Base URL of the database
    search_url: str             # Actual search query URL
    query_terms: str            # Search terms used
    date_range: str             # Date range searched
    result_count: int           # Number of results found
    source_name: str            # Display name for the source


# ---------------------------------------------------------------------------
# Top-level proof.json
# Authoritative required keys: tools/validate-site-proof.py REQUIRED_JSON_KEYS
# ---------------------------------------------------------------------------

class DataValueVerificationEntry(TypedDict, total=False):
    found: bool
    value: str
    fetch_mode: str             # "live", "snapshot", "wayback", "fetch_failed"
    error: str


class ProofData(TypedDict, total=False):
    # Required keys (per REQUIRED_JSON_KEYS in validate-site-proof.py)
    fact_registry: dict[str, FactRegistryEntry]
    claim_formal: ClaimFormal
    claim_natural: str
    verdict: str                # One of VERDICT_TAXONOMY keys
    key_results: dict[str, object]
    generator: Generator
    # Optional sections
    citations: dict[str, CitationEntry]
    extractions: dict[str, ExtractionRecord]
    cross_checks: list[CrossCheck]
    adversarial_checks: list[AdversarialCheck]
    search_registry: dict[str, SearchRegistryEntry]
    # Table-sourced data verification (present when verify_data_values() is used)
    data_value_verification: dict[str, dict[str, DataValueVerificationEntry]]
    # Time-sensitive proofs may include a date note
    date_note: str
    # Compound proof sub-claim results
    sub_claim_results: list[dict] | dict[str, dict]
    # Verdict annotations (used in some published proofs)
    verdict_note: str
    verdict_reason: str


# ---------------------------------------------------------------------------
# Normalized verdict (from tools/lib/verdict.py)
# ---------------------------------------------------------------------------

class NormalizedVerdict(TypedDict):
    raw: str
    category: str               # "proved", "proved-qualified", "disproved", etc.
    badge_color: str            # "green", "amber", "red", "gray", "blue"
    filter_value: str           # "proved", "disproved", "partial", "undetermined", "supported"
    rating: int                 # 1-5


# ---------------------------------------------------------------------------
# Proof loader output (tools/lib/proof_loader.py)
# ---------------------------------------------------------------------------

class LoadedProof(TypedDict, total=False):
    slug: str
    proof_data: ProofData
    sections_md: dict[str, str]
    sections_audit: dict[str, str]
    verdict: NormalizedVerdict
    tags: list[str]
    featured: bool
    citation_count: int | None
    search_count: int | None
    date: str
    proof_engine_version: str
