"""
source_credibility.py — Assess source credibility from URL domain.

Provides a deterministic, auditable credibility assessment for citation URLs.
Uses bundled data files (no API keys required) to classify domains into tiers:

  Tier 5: Government / intergovernmental (primary official source)
  Tier 4: Academic / peer-reviewed publisher
  Tier 3: Established reference or major news organization
  Tier 2: Unknown commercial / unclassified domain
  Tier 1: Flagged unreliable or satire

The assessment is purely domain-based and offline — no network calls.
It surfaces information for the human reviewer; it does NOT auto-downgrade
verdicts. A tier-1 source with a verified quote is still a verified quote.

Usage as module:
    from scripts.source_credibility import assess_credibility, assess_all

Usage as CLI:
    python scripts/source_credibility.py --url https://example.com/page
    python scripts/source_credibility.py --facts facts.json
"""

import json
import os
import sys
from urllib.parse import urlparse


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

_cache = {}


def _load_json(filename: str) -> dict:
    """Load a bundled JSON data file, with caching."""
    if filename not in _cache:
        filepath = os.path.join(_DATA_DIR, filename)
        with open(filepath) as f:
            _cache[filename] = json.load(f)
    return _cache[filename]


# ---------------------------------------------------------------------------
# Domain extraction (no external dependencies)
# ---------------------------------------------------------------------------

def _extract_domain_parts(url: str) -> dict:
    """Extract domain components from a URL.

    Returns dict with:
        full_domain: "pubmed.ncbi.nlm.nih.gov"
        registered_domain: "nih.gov" (best guess without tldextract)
        suffix: ".gov"
    """
    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower().strip(".")

    if not hostname:
        return {"full_domain": "", "registered_domain": "", "suffix": ""}

    parts = hostname.split(".")

    # Handle common multi-part TLDs
    multi_tlds = [
        ".gov.uk", ".gov.au", ".gov.ca", ".gov.nz", ".gov.za", ".gov.in",
        ".gov.sg", ".gov.ie", ".gov.il", ".gov.br", ".gov.cn", ".gov.tw",
        ".gov.ph", ".gov.my", ".gov.eg", ".gov.ng", ".gov.gh", ".gov.ke",
        ".gc.ca", ".gouv.fr", ".gouv.qc.ca", ".gob.mx", ".gob.es",
        ".gob.ar", ".gob.cl", ".gob.pe", ".go.jp", ".go.kr", ".go.id",
        ".go.th", ".govt.nz", ".bund.de", ".admin.ch", ".overheid.nl",
        ".ac.uk", ".ac.jp", ".ac.kr", ".ac.il", ".ac.in", ".ac.nz",
        ".ac.za", ".ac.id", ".ac.th",
        ".edu.au", ".edu.br", ".edu.cn", ".edu.hk", ".edu.sg", ".edu.tw",
        ".edu.mx", ".edu.ar", ".edu.co", ".edu.pe", ".edu.pl", ".edu.tr",
        ".co.uk", ".co.jp", ".co.kr", ".co.nz", ".co.za", ".co.in",
        ".com.au", ".com.br", ".com.cn", ".com.mx", ".com.ar",
        ".or.jp", ".or.kr", ".ne.jp",
        ".ec.europa.eu",
    ]

    suffix = ""
    for tld in multi_tlds:
        if hostname.endswith(tld):
            suffix = tld
            break

    if not suffix and len(parts) >= 2:
        suffix = "." + parts[-1]

    # registered_domain = domain + suffix
    if suffix:
        suffix_parts = suffix.strip(".").split(".")
        suffix_len = len(suffix_parts)
        if len(parts) > suffix_len:
            registered_domain = ".".join(parts[-(suffix_len + 1):])
        else:
            registered_domain = hostname
    else:
        registered_domain = hostname

    return {
        "full_domain": hostname,
        "registered_domain": registered_domain,
        "suffix": suffix,
    }


# ---------------------------------------------------------------------------
# Credibility assessment
# ---------------------------------------------------------------------------

def assess_credibility(url: str) -> dict:
    """Assess source credibility based on URL domain.

    Returns:
        {
            "domain": "bls.gov",
            "source_type": "government" | "academic" | "major_news" |
                           "reference" | "commercial" | "unknown",
            "tier": 5,  # 1-5
            "flags": [...],  # list of warning strings, empty if clean
            "note": "Official .gov domain"
        }

    Tier scale:
        5 = Government / intergovernmental primary source
        4 = Academic / peer-reviewed publisher
        3 = Major news org or established reference
        2 = Unclassified (commercial, personal, niche)
        1 = Flagged unreliable or known satire
    """
    parts = _extract_domain_parts(url)
    domain = parts["full_domain"]
    registered = parts["registered_domain"]
    suffix = parts["suffix"]
    flags = []

    if not domain:
        return {
            "domain": "",
            "source_type": "unknown",
            "tier": 2,
            "flags": ["empty_url"],
            "note": "Could not parse domain from URL",
        }

    # --- Check unreliable first (overrides everything) ---
    unreliable = _load_json("unreliable_domains.json")
    unreliable_set = set(unreliable.get("known_domains", []))
    satire_set = set(unreliable.get("satire_domains", []))

    if registered in unreliable_set or domain in unreliable_set:
        is_satire = registered in satire_set or domain in satire_set
        return {
            "domain": registered,
            "source_type": "unreliable",
            "tier": 1,
            "flags": ["satire_site"] if is_satire else ["flagged_unreliable"],
            "note": "Known satire site" if is_satire else "Flagged as unreliable source",
        }

    # --- Government / intergovernmental ---
    gov_data = _load_json("government_tlds.json")
    gov_suffixes = gov_data.get("tld_suffixes", [])
    gov_domains = set(gov_data.get("known_domains", []))

    for gov_suffix in gov_suffixes:
        if suffix == gov_suffix or hostname_ends_with(domain, gov_suffix):
            return {
                "domain": registered,
                "source_type": "government",
                "tier": 5,
                "flags": flags,
                "note": f"Government domain ({gov_suffix})",
            }

    if registered in gov_domains or domain in gov_domains:
        return {
            "domain": registered,
            "source_type": "government",
            "tier": 5,
            "flags": flags,
            "note": "Known government/intergovernmental organization",
        }
    # Also check if full_domain is a subdomain of a known gov domain
    for gov_domain in gov_domains:
        if domain.endswith("." + gov_domain):
            return {
                "domain": registered,
                "source_type": "government",
                "tier": 5,
                "flags": flags,
                "note": f"Subdomain of {gov_domain}",
            }

    # --- Academic / peer-reviewed ---
    acad_data = _load_json("academic_domains.json")
    acad_suffixes = acad_data.get("tld_suffixes", [])
    acad_domains = set(acad_data.get("known_domains", []))
    doi_prefixes = acad_data.get("doi_prefixes", [])

    # DOI link detection
    for prefix in doi_prefixes:
        if url.lower().startswith(prefix):
            return {
                "domain": registered,
                "source_type": "academic",
                "tier": 4,
                "flags": flags,
                "note": "DOI link (peer-reviewed publication)",
            }

    for acad_suffix in acad_suffixes:
        if suffix == acad_suffix or hostname_ends_with(domain, acad_suffix):
            return {
                "domain": registered,
                "source_type": "academic",
                "tier": 4,
                "flags": flags,
                "note": f"Academic domain ({acad_suffix})",
            }

    if registered in acad_domains or domain in acad_domains:
        return {
            "domain": registered,
            "source_type": "academic",
            "tier": 4,
            "flags": flags,
            "note": "Known academic/scholarly publisher",
        }
    for acad_domain in acad_domains:
        if domain.endswith("." + acad_domain):
            return {
                "domain": registered,
                "source_type": "academic",
                "tier": 4,
                "flags": flags,
                "note": f"Subdomain of {acad_domain}",
            }

    # --- Major news ---
    news_data = _load_json("major_news.json")
    news_domains = set(news_data.get("known_domains", []))

    if registered in news_domains or domain in news_domains:
        return {
            "domain": registered,
            "source_type": "major_news",
            "tier": 3,
            "flags": flags,
            "note": "Major news organization",
        }
    for news_domain in news_domains:
        if domain.endswith("." + news_domain):
            return {
                "domain": registered,
                "source_type": "major_news",
                "tier": 3,
                "flags": flags,
                "note": f"Subdomain of {news_domain}",
            }

    # --- Established reference ---
    ref_data = _load_json("reference_domains.json")
    ref_domains = set(ref_data.get("known_domains", []))

    if registered in ref_domains or domain in ref_domains:
        return {
            "domain": registered,
            "source_type": "reference",
            "tier": 3,
            "flags": flags,
            "note": "Established reference source",
        }
    for ref_domain in ref_domains:
        if domain.endswith("." + ref_domain):
            return {
                "domain": registered,
                "source_type": "reference",
                "tier": 3,
                "flags": flags,
                "note": f"Subdomain of {ref_domain}",
            }

    # --- HTTPS check for unclassified domains ---
    parsed = urlparse(url)
    if parsed.scheme == "http":
        flags.append("no_https")

    # --- Default: unclassified ---
    return {
        "domain": registered,
        "source_type": "unknown",
        "tier": 2,
        "flags": flags,
        "note": "Unclassified domain -- verify source authority manually",
    }


def hostname_ends_with(hostname: str, suffix: str) -> bool:
    """Check if hostname ends with a given suffix (handles dot boundary)."""
    if hostname == suffix.lstrip("."):
        return True
    return hostname.endswith(suffix)


# ---------------------------------------------------------------------------
# Batch assessment
# ---------------------------------------------------------------------------

def assess_all(empirical_facts: dict) -> dict:
    """Assess credibility for all URLs in an empirical_facts dict.

    Supports both single-source and multi-source formats (same as
    verify_all_citations).

    Returns:
        dict of {fact_id: credibility_result} or
               {fact_id_source_N: credibility_result} for multi-source.
    """
    results = {}

    for fact_id, fact in empirical_facts.items():
        if "sources" in fact:
            for i, source in enumerate(fact["sources"]):
                check_id = f"{fact_id}_source_{i}"
                url = source.get("url", "")
                if url:
                    results[check_id] = assess_credibility(url)
                    _print_credibility(check_id, results[check_id])
        else:
            url = fact.get("url", "")
            if url:
                results[fact_id] = assess_credibility(url)
                _print_credibility(fact_id, results[fact_id])

    return results


def _print_credibility(fact_id: str, result: dict):
    """Print a one-line credibility assessment."""
    tier = result["tier"]
    stype = result["source_type"]
    domain = result["domain"]
    note = result["note"]
    flags = result.get("flags", [])

    tier_icon = {5: "\u2605", 4: "\u25c6", 3: "\u25cf", 2: "\u25cb", 1: "\u26a0"}
    icon = tier_icon.get(tier, "?")

    flag_str = f" [{', '.join(flags)}]" if flags else ""
    print(f"  {icon} {fact_id}: tier {tier} ({stype}) -- {domain} -- {note}{flag_str}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Assess source credibility for citation URLs"
    )
    parser.add_argument("--url", help="Single URL to assess")
    parser.add_argument("--facts", help="Path to JSON file with empirical_facts dict")
    args = parser.parse_args()

    if args.url:
        result = assess_credibility(args.url)
        _print_credibility("cli", result)
        print(json.dumps(result, indent=2))
    elif args.facts:
        with open(args.facts) as f:
            facts = json.load(f)
        results = assess_all(facts)
        low_tier = [fid for fid, r in results.items() if r["tier"] <= 1]
        if low_tier:
            print(f"\n\u26a0 {len(low_tier)} source(s) flagged as unreliable: {', '.join(low_tier)}")
        else:
            print(f"\nAll {len(results)} source(s) assessed -- no unreliable sources flagged.")
    else:
        parser.print_help()
        sys.exit(1)
