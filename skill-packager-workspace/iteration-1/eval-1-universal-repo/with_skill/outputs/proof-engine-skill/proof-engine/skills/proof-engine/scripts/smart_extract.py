"""
smart_extract.py — LLM-assisted extraction that stays auditable and re-runnable.

The Problem:
  Rigid regex patterns fail on real-world text. Websites use en-dashes vs hyphens,
  curly quotes vs straight quotes, HTML entities vs Unicode characters, and other
  quirks that no single normalization pipeline can anticipate. The current approach
  (parse_number_from_quote with a hand-written regex) breaks whenever the quote
  text doesn't match the regex assumptions.

The Solution — Two-Phase Extraction:
  Phase 1 (proof-writing time, LLM available):
    The LLM writes a custom extraction function tailored to the specific quote.
    This function is literal Python code — it lives in the proof script, fully
    visible and auditable. It includes:
      - The quote string it operates on
      - A normalization step for the specific Unicode quirks found
      - The extraction logic (regex or string ops)
      - An assertion that the extracted value appears in the (normalized) quote
      - A comment explaining what it does and why

  Phase 2 (re-run time, no LLM needed):
    The custom function runs as normal Python. It's self-contained. No LLM
    needed. Anyone can read the code and see exactly how the value was extracted.

This module provides:
  - UNICODE_NORMALIZATIONS: a registry of known character substitutions
  - normalize_unicode(text): apply all known normalizations
  - verify_extraction(value, quote, fact_id): assert a value came from a quote
  - ExtractionRecord: dataclass for auditable extraction with provenance

Usage in a proof script:
  The LLM writes functions like this directly in the proof:

    def extract_ghg_warming_low(quote):
        '''Extract GHG low-end warming from Source B.
        The NOAA page uses en-dashes and ° symbols consistently,
        so we normalize those before extracting.'''
        normalized = normalize_unicode(quote)
        match = re.search(r'warming of ([\\d.]+).C', normalized)
        value = float(match.group(1))
        verify_extraction(value, quote, "source_b_ghg_low")
        return value

  This function is IN the proof script — auditable, re-runnable, no LLM needed.

Usage as CLI:
  python scripts/smart_extract.py normalize "text with –en-dash and 'curly quotes'"
  python scripts/smart_extract.py diagnose --url URL --quote "expected quote"
"""

import datetime
import re
import sys
import unicodedata
from dataclasses import dataclass, field
from typing import Optional, List, Any


# ---------------------------------------------------------------------------
# Unicode normalization registry
# ---------------------------------------------------------------------------

# These substitutions handle the most common mismatches between how text appears
# in a browser (and how an LLM transcribes it) vs. how it appears in raw HTML.
# Each entry: (from_char_or_pattern, to_char, description)
UNICODE_NORMALIZATIONS = [
    # Dashes
    ("\u2013", "-", "en-dash \u2192 hyphen"),
    ("\u2014", "-", "em-dash \u2192 hyphen"),
    ("\u2012", "-", "figure dash \u2192 hyphen"),
    ("\u2010", "-", "hyphen character \u2192 ASCII hyphen"),
    # Quotes
    ("\u2018", "'", "left single curly quote \u2192 straight"),
    ("\u2019", "'", "right single curly quote \u2192 straight"),
    ("\u201C", '"', "left double curly quote \u2192 straight"),
    ("\u201D", '"', "right double curly quote \u2192 straight"),
    # Degree symbols
    ("\u02DA", "\u00B0", "ring above \u2192 degree sign"),  # \u02da vs \u00b0
    # Spaces
    ("\u00A0", " ", "non-breaking space \u2192 space"),
    ("\u2009", " ", "thin space \u2192 space"),
    # Math/typography symbols that should normalize to ASCII equivalents
    ("\u2212", "-", "minus sign \u2192 ASCII hyphen"),
    # Invisible characters (zero-width / formatting)
    ("\u00AD", "", "soft hyphen \u2192 removed"),
    ("\u200B", "", "zero-width space \u2192 removed"),
    ("\u200C", "", "zero-width non-joiner \u2192 removed"),
    ("\u200D", "", "zero-width joiner \u2192 removed"),
    ("\u2060", "", "word joiner \u2192 removed"),
    ("\uFEFF", "", "BOM / zero-width no-break space \u2192 removed"),
    # Other common web characters
    ("\u2026", "...", "ellipsis \u2192 three dots"),
    ("\u00D7", "x", "multiplication sign \u2192 x"),
    ("\u221E", "infinity", "infinity symbol \u2192 word"),
]


def normalize_unicode(text: str) -> str:
    """Apply all known Unicode normalizations.

    This handles common mismatches between browser-rendered text (which an LLM
    transcribes) and the raw characters in HTML (which verify_citations fetches).

    Steps:
      1. Apply the character substitution registry FIRST (before NFKC can
         decompose characters like \u02da into combining forms we can't match)
      2. NFKC normalization (canonical decomposition + compatibility composition)
      3. Apply substitutions again (NFKC may produce new matchable characters)
      4. Collapse whitespace

    Returns the normalized text. Does NOT lowercase (that's for matching, not extraction).
    """
    # 1. Apply registered substitutions FIRST — some characters (like \u02da U+02DA)
    # get decomposed by NFKC into combining forms we can't easily match
    for from_char, to_char, _desc in UNICODE_NORMALIZATIONS:
        text = text.replace(from_char, to_char)

    # 2. NFKC handles many decomposition issues (e.g., \ufb01 \u2192 fi, \u00b2 \u2192 2)
    text = unicodedata.normalize("NFKC", text)

    # 3. Apply substitutions again in case NFKC produced new matchable characters
    for from_char, to_char, _desc in UNICODE_NORMALIZATIONS:
        text = text.replace(from_char, to_char)

    # 4. Collapse whitespace (but preserve newlines)
    text = re.sub(r'[^\S\n]+', ' ', text)

    return text


def diagnose_mismatch(page_text: str, quote: str, context_chars: int = 200) -> dict:
    """Diagnose why a quote isn't found on a page.

    Performs progressively aggressive normalization and searching to find where
    the quote (or fragments of it) actually appears, and reports what character
    differences cause the mismatch.

    Returns a dict with:
      - found: bool — whether the quote was found after normalization
      - method: str — what normalization was needed
      - char_diffs: list — specific character differences found
      - page_fragment: str — the matching fragment from the page (if found)
      - suggestion: str — a suggested normalization approach
    """
    result = {
        "found": False,
        "method": None,
        "char_diffs": [],
        "page_fragment": None,
        "suggestion": None,
    }

    # Try 1: Exact match after Unicode normalization
    norm_page = normalize_unicode(page_text).lower()
    norm_quote = normalize_unicode(quote).lower()

    if norm_quote in norm_page:
        result["found"] = True
        result["method"] = "unicode_normalization"
        result["suggestion"] = "Use normalize_unicode() before matching"
        return result

    # Try 2: Strip ALL non-alphanumeric characters and match
    stripped_page = re.sub(r'[^a-z0-9]', '', norm_page)
    stripped_quote = re.sub(r'[^a-z0-9]', '', norm_quote)

    if stripped_quote in stripped_page:
        result["found"] = True
        result["method"] = "alphanumeric_only"

        # Find which characters differ
        _find_char_diffs(page_text, quote, result)

        result["suggestion"] = (
            "Quote found after stripping punctuation. "
            "Write a custom normalizer that handles the specific character differences."
        )
        return result

    # Try 3: Look for significant fragments (first 5 words, last 5 words)
    words = norm_quote.split()
    for length in [8, 6, 4, 3]:
        if len(words) >= length:
            fragment = ' '.join(words[:length])
            if fragment in norm_page:
                idx = norm_page.index(fragment)
                result["found"] = True
                result["method"] = f"fragment_match ({length} words)"
                result["page_fragment"] = page_text[max(0,idx-20):idx+context_chars]
                _find_char_diffs(page_text[idx:idx+len(quote)+50], quote, result)
                result["suggestion"] = (
                    f"First {length} words match. Write a custom extraction "
                    f"that targets this fragment and handles: {result['char_diffs']}"
                )
                return result

    result["suggestion"] = (
        "Quote not found even as fragments. Verify the URL is correct "
        "and the quote is accurately transcribed."
    )
    return result


def _find_char_diffs(page_fragment: str, quote: str, result: dict):
    """Compare characters between page and quote to find specific differences."""
    diffs = []
    norm_q = normalize_unicode(quote)
    # Try to align by finding common starting substring
    for i, (pc, qc) in enumerate(zip(page_fragment.lower(), norm_q.lower())):
        if pc != qc:
            diffs.append({
                "position": i,
                "page_char": repr(pc),
                "page_ord": f"U+{ord(pc):04X}",
                "quote_char": repr(qc),
                "quote_ord": f"U+{ord(qc):04X}",
            })
            if len(diffs) >= 10:
                break
    result["char_diffs"] = diffs


# ---------------------------------------------------------------------------
# Extraction verification
# ---------------------------------------------------------------------------

def verify_extraction(value: Any, quote: str, fact_id: str, description: str = "", strict: bool = True):
    """Assert that an extracted value or keyword is plausibly from the quote text.

    This is a sanity check — it verifies that the value (numeric or string)
    appears somewhere in the quote. Works for numbers, dates, percentages,
    and also for keywords/phrases in qualitative proofs. It's not a proof
    that the extraction is correct, but it catches cases where the extraction
    logic returns a value that has nothing to do with the quote.

    Args:
        value: The extracted value (number, date, string, keyword).
        quote: The original quote string.
        fact_id: Identifier for error messages.
        description: Optional human-readable description of what was extracted.
        strict: If True (default), raises ValueError on mismatch. If False,
                logs a warning and returns False.

    Returns:
        True if the value was found in the quote.

    Examples:
        # Numeric extraction
        verify_extraction(1.1, "temperature rose 1.1 degrees", "B1")
        # Keyword/qualitative extraction
        verify_extraction("reactivates", "the virus reactivates under stress", "B2")

    Raises:
        ValueError: If strict=True and the value is not found in the quote.
    """
    value_str = str(value)
    # For floats, also check the integer form and common representations.
    # Only include the integer/rounded form if it equals the original value
    # (e.g., 77.0 \u2192 "77" is safe, but 1.1 \u2192 "1" is a lossy round that
    # would false-positive on "11.1").
    check_forms = [value_str]
    if isinstance(value, datetime.date) and not isinstance(value, datetime.datetime):
        _MONTHS = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December",
        ]
        m = _MONTHS[value.month - 1]
        check_forms.extend([
            f"{m} {value.day}, {value.year}",          # December 23, 1913
            f"{value.day} {m} {value.year}",            # 23 December 1913
            value.isoformat(),                           # 1913-12-23
            f"{value.month}/{value.day}/{value.year}",   # 12/23/1913
            str(value.year),                             # 1913 (year alone)
        ])
    elif isinstance(value, (int, float)):
        int_form = str(int(value))
        check_forms.extend([
            int_form if value == int(value) else "",
            f"{value:.1f}",
            f"{value:.2f}",
            f"{value:.3f}",
            f"{value:,.0f}" if value == round(value) else "",
        ])
        # Handle trailing-zero mismatch: Python's float\u2192str drops trailing zeros
        # (9.900 \u2192 9.9), but the quote may keep them. Generate padded forms so
        # "9.9" can match inside "9.900".
        base = value_str
        if "." in base:
            for pad in range(1, 4):
                padded = base + "0" * pad
                if padded not in check_forms:
                    check_forms.append(padded)

    # Normalize quote for comparison
    norm_quote = normalize_unicode(quote.lower())

    # Use context-aware boundary matching to avoid false positives.
    # For numeric values: (?<![\d.]) and (?![\d]) prevents "1.1" matching "11.1".
    #   The trailing boundary excludes digits but NOT dots/punctuation, so "1913."
    #   (sentence-ending period) still matches.
    # For string values (dates, keywords): simple substring match after lowercasing,
    #   since the value is already specific enough (e.g., "december 23, 1913").
    def _boundary_match(v, text, is_numeric=False):
        v_lower = v.lower()
        if is_numeric:
            # Numeric boundary: not preceded by digit/dot, not followed by digit
            return bool(re.search(r'(?<![\d.])' + re.escape(v_lower) + r'(?![\d])', text))
        else:
            # String/date: simple substring match (already specific enough)
            return v_lower in text

    is_num = isinstance(value, (int, float))
    found = any(v and _boundary_match(v, norm_quote, is_numeric=is_num) for v in check_forms if v)
    desc = f" ({description})" if description else ""

    if found:
        print(f"  [\u2713] {fact_id}{desc}: extracted {value} from quote")
        return True

    msg = f"{fact_id}{desc}: extracted value {value} not found in quote text"
    if strict:
        raise ValueError(msg)
    else:
        print(f"  [\u26a0] {msg} \u2014 verify extraction logic")
        return False


# ---------------------------------------------------------------------------
# Extraction record (for structured proof output)
# ---------------------------------------------------------------------------

@dataclass
class ExtractionRecord:
    """Auditable record of a value extraction from a quote.

    Captures everything needed to verify and reproduce the extraction:
      - What was extracted and from which quote
      - The extraction method (code) used
      - Whether the extraction passed sanity checks

    Include these records in the proof's __main__ output for full transparency.
    """
    fact_id: str
    quote: str
    extracted_value: Any
    extraction_method: str  # Human-readable description of the extraction approach
    normalization_applied: str  # What normalizations were needed (if any)
    verified: bool = False  # Did verify_extraction() pass?
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "fact_id": self.fact_id,
            "extracted_value": self.extracted_value,
            "extraction_method": self.extraction_method,
            "normalization_applied": self.normalization_applied,
            "verified": self.verified,
            "notes": self.notes,
        }

    def __str__(self):
        status = "\u2713" if self.verified else "\u26a0"
        return (
            f"[{status}] {self.fact_id}: {self.extracted_value} "
            f"(via {self.extraction_method})"
        )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Smart extraction diagnostics")
    sub = parser.add_subparsers(dest="command")

    # normalize command
    norm_p = sub.add_parser("normalize", help="Normalize Unicode text")
    norm_p.add_argument("text", help="Text to normalize")

    # diagnose command
    diag_p = sub.add_parser("diagnose", help="Diagnose why a quote isn't found on a page")
    diag_p.add_argument("--url", required=True, help="URL to fetch")
    diag_p.add_argument("--quote", required=True, help="Expected quote")

    args = parser.parse_args()

    if args.command == "normalize":
        result = normalize_unicode(args.text)
        print(f"Input:  {repr(args.text)}")
        print(f"Output: {repr(result)}")

        # Show what changed
        for i, (a, b) in enumerate(zip(args.text, result)):
            if a != b:
                print(f"  Position {i}: {repr(a)} (U+{ord(a):04X}) \u2192 {repr(b)} (U+{ord(b):04X})")

    elif args.command == "diagnose":
        import requests
        resp = requests.get(args.url, timeout=15, headers={"User-Agent": "proof-engine/1.0"})
        resp.raise_for_status()

        # Strip HTML tags for diagnosis
        page_text = re.sub(r'<[^>]+>', ' ', resp.text)
        page_text = re.sub(r'\s+([,.:;!?\)\]])', r'\1', page_text)
        page_text = ' '.join(page_text.split())

        result = diagnose_mismatch(page_text, args.quote)
        print(f"Found: {result['found']}")
        print(f"Method: {result['method']}")
        if result['char_diffs']:
            print(f"Character differences:")
            for d in result['char_diffs']:
                print(f"  Position {d['position']}: page={d['page_char']} ({d['page_ord']}) vs quote={d['quote_char']} ({d['quote_ord']})")
        if result['suggestion']:
            print(f"Suggestion: {result['suggestion']}")
        if result['page_fragment']:
            print(f"Page fragment: {result['page_fragment'][:200]}")

    else:
        parser.print_help()
        sys.exit(1)
