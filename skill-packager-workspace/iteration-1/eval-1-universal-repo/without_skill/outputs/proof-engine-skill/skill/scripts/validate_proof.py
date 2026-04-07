"""
validate_proof.py — Static analysis of proof scripts for Hardening Rule compliance.

Runs BEFORE execution to catch LLM errors early. Checks that the generated
proof code follows all 7 Hardening Rules without actually running it.

Usage:
    python scripts/validate_proof.py proof_file.py

Exit code 0 = pass (warnings OK), 1 = fail (issues found).
"""

import re
import sys
import os

try:
    from scripts.ast_helpers import extract_script_imports, find_call_sites, extract_dict_keys
except ImportError:
    from ast_helpers import extract_script_imports, find_call_sites, extract_dict_keys


class ProofValidator:
    """Static analyzer for proof-engine proof scripts."""

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.filename = os.path.basename(filepath)
        with open(filepath) as f:
            self.source = f.read()
        self.lines = self.source.splitlines()

        self.passed = []
        self.warnings = []
        self.issues = []

    # ------------------------------------------------------------------
    # Rule checks
    # ------------------------------------------------------------------

    def _build_code_body(self):
        """Build source with imports and comments stripped, for call-site detection."""
        code_lines = []
        for line in self.lines:
            stripped = line.strip()
            if stripped.startswith("#") or stripped.startswith("from scripts.") or stripped.startswith("import "):
                continue
            comment_pos = stripped.find("#")
            if comment_pos >= 0:
                stripped = stripped[:comment_pos]
            code_lines.append(stripped)
        return "\n".join(code_lines)

    def check_rule1_no_handtyped_values(self):
        """Rule 1: No hand-typed extracted values.

        Scans for date() literals and 'value': N patterns near quote definitions
        that suggest the LLM typed a value instead of parsing it from the quote.
        """
        problems = []

        for i, line in enumerate(self.lines, 1):
            stripped = line.strip()

            # Skip PROOF_GENERATION_DATE (that's Rule 3, it's OK)
            if "PROOF_GENERATION_DATE" in line:
                continue
            # Skip lines inside parse/extract functions / import statements
            if any(kw in line for kw in ["parse_date", "parse_number", "parse_percentage", "verify_extraction", "normalize_unicode", "def ", "import "]):
                continue
            # Skip comment lines
            if stripped.startswith("#"):
                continue

            # Check for bare date() literals that look like hand-typed dates
            # Match date(YYYY, M, D) but not date.today()
            date_match = re.search(r'\bdate\(\s*\d{4}\s*,\s*\d{1,2}\s*,\s*\d{1,2}\s*\)', line)
            if date_match:
                # Check if this is near a quote/fact definition (within 10 lines)
                context_start = max(0, i - 11)
                context_end = min(len(self.lines), i + 5)
                context = "\n".join(self.lines[context_start:context_end])
                if '"quote"' in context or "'quote'" in context or "empirical" in context.lower():
                    problems.append(f"  Line {i}: {date_match.group(0)} — possible hand-typed date near fact definition")

            # Check for "value": <number> in dict literals
            value_match = re.search(r'["\']value["\']\s*:\s*[\d.]+', line)
            if value_match:
                problems.append(f"  Line {i}: {value_match.group(0)} — possible hand-typed value")

        if problems:
            self.warnings.append(("Rule 1: Possible hand-typed extracted values detected", problems))
        else:
            self.passed.append("Rule 1: No hand-typed extracted values detected")

    def _has_nonempty_empirical_facts(self) -> bool:
        """Check if the source defines empirical_facts with actual entries.

        Returns False for:
          - no empirical_facts at all
          - empirical_facts = {}
          - empirical_facts = dict()
        Returns True if empirical_facts is assigned a non-empty dict.
        """
        if "empirical_facts" not in self.source:
            return False
        # Match empty dict assignments: empirical_facts = {} or = { }
        if re.search(r'empirical_facts\s*=\s*\{\s*\}', self.source):
            return False
        # Match empty dict() call
        if re.search(r'empirical_facts\s*=\s*dict\(\s*\)', self.source):
            return False
        return True

    def _has_search_registry(self) -> bool:
        """Check if the source defines search_registry with entries."""
        if "search_registry" not in self.source:
            return False
        if re.search(r'search_registry\s*=\s*\{\s*\}', self.source):
            return False
        return True

    def _extract_search_registry_domains(self) -> set:
        """Extract unique URL domains from search_registry entries."""
        domains = set()
        sr_match = re.search(r'search_registry\s*=\s*\{', self.source)
        if not sr_match:
            return domains
        start = sr_match.end()
        depth = 1
        i = start
        while i < len(self.source) and depth > 0:
            if self.source[i] == '{':
                depth += 1
            elif self.source[i] == '}':
                depth -= 1
            i += 1
        sr_text = self.source[start:i]
        from urllib.parse import urlparse
        # Match both single and double quoted Python strings
        for url_match in re.finditer(r'''["']url["']\s*:\s*["']([^"']+)["']''', sr_text):
            url = url_match.group(1)
            domain = urlparse(url).netloc
            if domain:
                domains.add(domain)
        return domains

    def _extract_empirical_facts_keys(self) -> list:
        """Extract top-level key names from the empirical_facts dict.

        Uses AST when source parses cleanly. Falls back to brace-depth
        regex parser when AST returns empty but the source has an
        empirical_facts assignment. This catches:
          - SyntaxError in source (AST can't parse at all)
          - Unsupported assignment shapes (dict(), comprehensions)
          - Any other case where AST returns [] but keys exist

        The fallback is always safe — worst case it returns the same []
        that AST did. It cannot produce false positives because the
        brace-depth parser only matches `empirical_facts = {`.
        """
        keys = extract_dict_keys(self.source, "empirical_facts")
        if keys:
            return keys
        # AST returned empty. If source doesn't even mention empirical_facts,
        # there are no keys to find.
        if not re.search(r'empirical_facts\s*=\s*\{', self.source):
            return []
        # Source has `empirical_facts = {` but AST returned empty —
        # fall back to brace-depth parser.
        return self._extract_empirical_facts_keys_regex()

    def _extract_empirical_facts_keys_regex(self) -> list:
        """Regex/brace-depth fallback for _extract_empirical_facts_keys.

        Handles malformed source that ast.parse() rejects.
        """
        match = re.search(r'empirical_facts\s*=\s*\{', self.source)
        if not match:
            return []
        keys = []
        start = match.end()
        depth = 1
        i = start
        while i < len(self.source) and depth > 0:
            ch = self.source[i]
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
            elif ch in ('"', "'") and depth == 1:
                quote_char = ch
                try:
                    end_quote = self.source.index(quote_char, i + 1)
                except ValueError:
                    break
                key = self.source[i + 1:end_quote]
                rest = self.source[end_quote + 1:end_quote + 10].strip()
                if rest.startswith(':'):
                    keys.append(key)
                i = end_quote
            i += 1
        return keys

    def check_rule2_citation_verification(self):
        """Rule 2: Citation verification code present (actual call, not just import).

        Uses AST to require an actual call site — importing verify_all_citations
        without calling it does not satisfy Rule 2.

        If AST parsing fails (find_call_sites returns None), falls back to
        regex on _build_code_body-style stripped source to avoid false positives
        on malformed drafts.
        """
        call_sites = find_call_sites(self.source)
        if call_sites is not None:
            has_verify_call = (
                "verify_citation" in call_sites or
                "verify_all_citations" in call_sites
            )
            has_verify_search = "verify_search_registry" in call_sites
        else:
            # AST failed — fall back to regex on comment-stripped source.
            # This matches the pre-AST behavior exactly.
            code_body = self._build_code_body()
            has_verify_call = bool(re.search(
                r'(?:verify_citation|verify_all_citations)\s*\(', code_body
            ))
            has_verify_search = bool(re.search(
                r'verify_search_registry\s*\(', code_body
            ))
        has_smart_extract = bool(re.search(r'smart_extract|normalize_unicode|verify_extraction', self.source))
        has_requests = bool(re.search(r'requests\.get', self.source))
        has_search_registry = self._has_search_registry()

        if has_search_registry:
            if not has_verify_search:
                self.issues.append((
                    "Rule 2: Has search_registry but no verify_search_registry call",
                    [],
                ))
            else:
                self.passed.append("Rule 2: verify_search_registry found for search_registry")
            has_empirical = self._has_nonempty_empirical_facts()
            if has_empirical and not has_verify_call:
                self.issues.append((
                    "Rule 2: Has corroborating empirical_facts but no verify_all_citations call",
                    [],
                ))
        elif has_verify_call:
            extra = " (with Unicode normalization)" if has_smart_extract else ""
            self.passed.append(f"Rule 2: Citation verification code found (bundled script){extra}")
        elif has_requests:
            self.warnings.append(("Rule 2: Inline requests.get found — prefer bundled verify_citations.py", []))
        else:
            has_empirical = self._has_nonempty_empirical_facts()
            if has_empirical or "Type B" in self.source or '"url"' in self.source:
                self.issues.append(("Rule 2: Has empirical facts but no citation verification code", []))
            else:
                self.passed.append("Rule 2: No empirical facts — citation verification not needed")

    def check_rule3_system_time(self):
        """Rule 3: Anchored to system time via date.today()."""
        has_today = "date.today()" in self.source
        has_hardcoded = bool(re.search(r'\bdate\(\s*\d{4}\s*,', self.source))

        # Check if the proof is time-dependent
        time_keywords = ["today", "current", "age", "years old", "elapsed", "since", "duration"]
        is_time_dependent = any(kw in self.source.lower() for kw in time_keywords)

        if has_today:
            self.passed.append("Rule 3: date.today() found — anchored to system time")
        elif not is_time_dependent:
            self.passed.append("Rule 3: Proof does not appear time-dependent — no date anchoring needed")
        elif has_hardcoded:
            self.issues.append(("Rule 3: Found hardcoded date() but no date.today() in time-dependent proof", []))
        else:
            self.passed.append("Rule 3: No date operations found")

    def check_rule4_claim_interpretation(self):
        """Rule 4: Explicit claim interpretation via CLAIM_FORMAL dict."""
        has_formal = bool(re.search(r'CLAIM_FORMAL|claim_formal', self.source))
        has_operator_note = bool(re.search(r'operator_note', self.source))

        if has_formal and has_operator_note:
            self.passed.append("Rule 4: CLAIM_FORMAL with operator_note found")
        elif has_formal:
            self.warnings.append(("Rule 4: CLAIM_FORMAL found but missing operator_note", []))
        else:
            self.issues.append(("Rule 4: No CLAIM_FORMAL dict — claim interpretation not explicit", []))

    def check_rule5_adversarial(self):
        """Rule 5: Structurally independent adversarial check."""
        adversarial_patterns = [
            r'adversarial', r'disproof', r'counter.?evidence',
            r'counter.?example', r'contradict', r'disprove',
        ]
        found = any(re.search(p, self.source, re.IGNORECASE) for p in adversarial_patterns)

        if found:
            self.passed.append("Rule 5: Adversarial check section found")
        else:
            self.issues.append(("Rule 5: No adversarial check found — proof may have confirmation bias", []))

    def check_rule6_independent_crosscheck(self):
        """Rule 6: Cross-checks use truly independent sources.

        Counts distinct top-level keys in empirical_facts dict,
        and unique URL domains in search_registry.
        """
        ef_keys = self._extract_empirical_facts_keys()
        sr_domains = self._extract_search_registry_domains()

        if sr_domains:
            if len(sr_domains) >= 2:
                self.passed.append(
                    f"Rule 6: {len(sr_domains)} unique database domains in search_registry "
                    f"({', '.join(sorted(sr_domains))})"
                )
            else:
                self.warnings.append((
                    f"Rule 6: Only 1 unique database domain in search_registry ({next(iter(sr_domains))}) — "
                    "cross-check requires multiple independent databases",
                    [],
                ))
            if ef_keys and len(ef_keys) >= 2:
                self.passed.append(
                    f"Rule 6: {len(ef_keys)} distinct corroborating sources "
                    f"({', '.join(sorted(ef_keys))})"
                )
        elif len(ef_keys) >= 2:
            self.passed.append(
                f"Rule 6: {len(ef_keys)} distinct source references found "
                f"({', '.join(sorted(ef_keys))})"
            )
        elif len(ef_keys) == 1:
            self.warnings.append((
                f"Rule 6: Only one source in empirical_facts ({ef_keys[0]}) — "
                "cross-check may not be truly independent",
                [],
            ))
        else:
            if self._has_nonempty_empirical_facts() or '"url"' in self.source:
                self.warnings.append(("Rule 6: No distinct source references found for empirical proof", []))
            else:
                self.passed.append("Rule 6: Pure computation — independent sources not required")

    def check_rule6_per_subclaim(self):
        """Check that each sub-claim in a compound proof has >=2 sources.

        For compound proofs, extracts SC IDs from CLAIM_FORMAL (supports both
        list-of-dicts and dict forms). Groups empirical_facts keys by lowercase
        SC prefix (sc1_, sc2a_, etc.). Only warns if prefixed keys exist but
        are unbalanced — skips silently when keys are descriptive (no prefix
        match), since source-to-subclaim mapping can't be reliably inferred.
        """
        if "sub_claims" not in self.source:
            return

        # Extract SC IDs from both forms:
        #   list form: {"id": "SC1", ...}
        #   dict form: "SC1": { or "SC1": "
        sc_ids = re.findall(r'"id"\s*:\s*"(SC\w+)"', self.source, re.IGNORECASE)
        if not sc_ids:
            # Try dict form: "SC1": { or "SC1": "
            sc_ids = re.findall(r'"(SC\w+)"\s*:', self.source, re.IGNORECASE)
            # Filter to only SC-prefixed keys that are sub-claim IDs (not random keys)
            sc_ids = [s for s in sc_ids if re.match(r'^SC\d+\w*$', s, re.IGNORECASE)]
        if not sc_ids:
            return

        ef_keys = self._extract_empirical_facts_keys()
        if not ef_keys:
            return

        # Check if ALL sub-claims have at least one prefixed key.
        # If any sub-claim has zero prefixed keys, the proof likely uses
        # descriptive keys for that sub-claim — skip the whole check to
        # avoid false positives on mixed-shape proofs.
        for sc_id in sc_ids:
            prefix = sc_id.lower() + "_"
            if not any(k.startswith(prefix) for k in ef_keys):
                # At least one sub-claim has no prefixed keys — can't
                # reliably assess balance, skip entirely
                return

        for sc_id in sc_ids:
            prefix = sc_id.lower() + "_"
            sc_keys = [k for k in ef_keys if k.startswith(prefix)]
            if len(sc_keys) < 2:
                self.warnings.append((
                    f"Rule 6: Sub-claim {sc_id} has only {len(sc_keys)} source(s) "
                    f"in empirical_facts (keys starting with '{prefix}') — "
                    "cross-check may not be truly independent for this sub-claim",
                    [],
                ))

    def check_coi_flags_presence(self):
        """Warn if proof has empirical_facts but no coi_flags key in cross_checks.

        Checks that "coi_flags" appears as a dict key (quoted string followed
        by colon) in non-comment code. This catches "COI not assessed" without
        judging whether the flags are correct. The self-critique checklist
        is the primary enforcement; this is a backstop.
        """
        has_empirical = self._has_nonempty_empirical_facts()
        if not has_empirical:
            return  # Pure-math or search-only — exempt

        # Check for "coi_flags" or 'coi_flags' as a dict key in non-comment lines.
        # Pattern: quoted "coi_flags" followed by optional whitespace and colon.
        # Matches both `"coi_flags": [...]` and `'coi_flags': coi_flags`.
        code_lines = [
            line for line in self.lines
            if not line.strip().startswith("#")
        ]
        code_body = "\n".join(code_lines)
        has_coi_key = bool(re.search(r'''["']coi_flags["']\s*:''', code_body))

        if has_coi_key:
            self.passed.append("Rule 6: coi_flags key found in proof — COI assessment present")
        else:
            self.warnings.append((
                "Rule 6: No \"coi_flags\" key found in proof with empirical_facts — "
                "COI assessment may be missing (see self-critique checklist)",
                [],
            ))

    def check_rule7_no_hardcoded_constants(self):
        """Rule 7: No hard-coded well-known constants or formulas.

        LLMs can misremember constants (365.25 vs 365.2425, using eval() for
        comparisons, rolling their own age calculation). The bundled
        computations.py provides verified implementations.
        """
        problems = []

        for i, line in enumerate(self.lines, 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            # Skip imports and the computations module itself
            if "import" in line or "DAYS_PER" in line:
                continue

            # Check for hard-coded days-per-year constants
            if re.search(r'365\.24', line) or re.search(r'365\.25\b', line):
                # OK if it's in a comment or a string defining the constant
                if not stripped.startswith("#") and "DAYS_PER" not in line:
                    problems.append(
                        f"  Line {i}: Hard-coded year-length constant — use DAYS_PER_GREGORIAN_YEAR from scripts/computations.py"
                    )

            # Check for eval() used with operators (unsafe and error-prone)
            if re.search(r'\beval\s*\(', line):
                problems.append(
                    f"  Line {i}: eval() call — use compare() from scripts/computations.py instead"
                )

        # Check if age is computed inline instead of using compute_age()
        has_inline_age = bool(re.search(
            r'\.year\s*-\s*\w+\.year', self.source
        ))
        has_compute_age = bool(re.search(r'compute_age', self.source))
        if has_inline_age and not has_compute_age:
            problems.append(
                "  Inline age calculation detected (year subtraction) — "
                "consider using compute_age() from scripts/computations.py"
            )

        if problems:
            self.warnings.append(("Rule 7: Possible hard-coded constants or formulas", problems))
        else:
            self.passed.append("Rule 7: No hard-coded constants or inline formulas detected")

    def check_fact_registry(self):
        """Check that proof defines a FACT_REGISTRY dict."""
        has_registry = bool(re.search(r'FACT_REGISTRY\s*=\s*\{', self.source))
        if has_registry:
            self.passed.append("Contract: FACT_REGISTRY dict found")
        else:
            self.issues.append(("Contract: No FACT_REGISTRY dict — required for report generation", []))

    def check_json_summary(self):
        """Check that proof emits a JSON summary block in __main__."""
        has_json_import = bool(re.search(r'import json', self.source))
        has_summary_print = bool(re.search(r'PROOF SUMMARY.*JSON', self.source))
        has_json_dumps = bool(re.search(r'json\.dumps\s*\(', self.source))

        if has_json_import and has_summary_print and has_json_dumps:
            self.passed.append("Contract: JSON summary block found (import json + PROOF SUMMARY header + json.dumps)")
        elif has_summary_print or has_json_dumps:
            self.warnings.append(("Contract: Partial JSON summary block — verify all components present", []))
        else:
            self.issues.append(("Contract: No JSON summary block — required for report generation", []))

    def check_extraction_verification(self):
        """Check that extracted values are verified, not just parsed.

        Three valid patterns:
          1. parse_*() + verify_extraction() — standard free-text extraction
          2. verify_extraction() without parse_*() — qualitative/keyword proof
          3. parse_*() + data_values (no verify_extraction) — table-sourced data
             where cross-check replaces verify_extraction (it would be circular)
        """
        has_parse = bool(re.search(
            r'parse_date_from_quote|parse_number_from_quote|parse_percentage_from_quote|parse_range_from_quote',
            self.source,
        ))
        has_verify = bool(re.search(r'verify_extraction\s*\(', self.source))
        has_data_values = bool(re.search(r'data_values', self.source))

        if has_parse and has_verify and has_data_values:
            self.passed.append("Contract: Mixed extraction — free-text values verified via verify_extraction(), table data via data_values (cross-check)")
        elif has_parse and has_verify:
            self.passed.append("Contract: Extracted values verified via verify_extraction()")
        elif has_verify and not has_parse:
            self.passed.append("Contract: Custom extraction with verify_extraction() (no standard parse functions — qualitative or keyword-based proof)")
        elif has_parse and not has_verify and has_data_values:
            self.passed.append("Contract: Table-sourced data via data_values — verify_extraction() correctly skipped (cross-check is the verification)")
        elif has_parse and not has_verify:
            self.warnings.append(("Contract: Values parsed from quotes but verify_extraction() not called — extraction records may be incomplete", []))
        else:
            self.passed.append("Contract: No value parsing detected (pure-math proof or no extractions)")

    def check_table_data_integrity(self):
        """Check that table/numeric data uses data_values + verify_data_values(),
        not pseudo-quote fields with circular verify_extraction().

        Four sub-rules:
          1. data_values present → verify_data_values() must be called
          2. verify_extraction() must not be called on data_values-derived values
          3. *_quote fields containing bare numeric/date literals are rejected
          4. Multiple short numeric "quotes" without data_values → warning
        """
        has_data_values = bool(re.search(r'["\']data_values["\']', self.source))
        has_verify_dv = bool(re.search(r'verify_data_values\s*\(', self.source))
        has_verify_ext = bool(re.search(r'verify_extraction\s*\(', self.source))

        # --- Rule 1: data_values requires verify_data_values() ---
        if has_data_values and not has_verify_dv:
            self.issues.append((
                "Rule 2/Contract: data_values present but verify_data_values() "
                "not called — table values are unverified.",
                [],
            ))
        elif has_data_values and has_verify_dv:
            self.passed.append(
                "Table integrity: data_values verified via verify_data_values()"
            )

        # --- Rule 2: verify_extraction() on data_values-derived values ---
        if has_data_values and has_verify_ext:
            # Linkage check: verify_extraction called with data_values path
            linkage = re.search(
                r'verify_extraction\s*\([^)]*\[["\']data_values["\']\]',
                self.source,
            )
            if linkage:
                self.issues.append((
                    "Rule 1/Contract: verify_extraction() used on "
                    "data_values-derived value — circular verification. "
                    "Use verify_data_values() + cross-check instead.",
                    [],
                ))

        # --- Rule 3: pseudo-quote fields with bare numeric/date literals ---
        # Find keys ending in _quote with short atomic values
        pseudo_quote_re = re.compile(
            r'["\'](\w+_quote)["\']\s*:\s*["\']([^"\']+)["\']'
        )
        pseudo_quotes = []
        for m in pseudo_quote_re.finditer(self.source):
            key, value = m.group(1), m.group(2)
            # Classify as atomic if: bare number, percentage, date-like, or
            # very short fragment (< 20 chars with no spaces beyond one)
            is_bare_number = bool(re.fullmatch(r'[\d,.\-+]+', value.strip()))
            is_percentage = bool(re.fullmatch(r'[\d.]+\s*%', value.strip()))
            is_date_like = bool(re.fullmatch(
                r'(?:January|February|March|April|May|June|July|August|'
                r'September|October|November|December)\s+\d{1,2},?\s+\d{4}',
                value.strip(),
            ))
            is_very_short = len(value.strip()) < 20 and value.strip().count(' ') <= 1

            if is_bare_number or is_percentage or is_date_like:
                pseudo_quotes.append((key, value))
            elif is_very_short and not any(c.isalpha() for c in value):
                pseudo_quotes.append((key, value))

        if pseudo_quotes:
            # Check if these pseudo-quotes are parsed as evidence
            parsed_as_evidence = []
            for key, value in pseudo_quotes:
                # Look for parse_*_from_quote(...[key]...) usage
                if re.search(
                    r'parse_(?:number|date|percentage|range)_from_quote\s*\([^)]*'
                    + re.escape(key),
                    self.source,
                ):
                    parsed_as_evidence.append(key)
                # Also check verify_extraction on the pseudo-quote
                elif re.search(
                    r'verify_extraction\s*\([^)]*' + re.escape(key),
                    self.source,
                ):
                    parsed_as_evidence.append(key)

            if parsed_as_evidence:
                details = [
                    f"  '{k}' = '{v}'" for k, v in pseudo_quotes
                    if k in parsed_as_evidence
                ]
                self.issues.append((
                    "Rule 1: pseudo-quote fields contain authored literals and "
                    "are parsed as evidence. For table data, use data_values + "
                    "verify_data_values(); for prose evidence, store the real quote.",
                    details,
                ))
            elif pseudo_quotes:
                details = [f"  '{k}' = '{v}'" for k, v in pseudo_quotes]
                self.warnings.append((
                    "Table integrity: possible pseudo-quote fields with atomic "
                    "values detected (not currently parsed as evidence).",
                    details,
                ))

        # --- Rule 4: table-like extraction without data_values (warning) ---
        if not has_data_values and not pseudo_quotes:
            # Count short numeric _quote fields in empirical_facts
            quote_fields = re.findall(
                r'["\'](\w+_quote)["\']\s*:\s*["\']([^"\']+)["\']',
                self.source,
            )
            numeric_quotes = [
                (k, v) for k, v in quote_fields
                if re.fullmatch(r'[\d,.\-+%]+', v.strip())
            ]
            if len(numeric_quotes) >= 3:
                details = [f"  '{k}' = '{v}'" for k, v in numeric_quotes]
                self.warnings.append((
                    "Rule 1/Rule 2: multiple numeric _quote fields found "
                    "without data_values — consider using data_values + "
                    "verify_data_values() for table-sourced data.",
                    details,
                ))

    def check_general_selfcontained(self):
        """General: proof is self-contained and runnable."""
        problems = []

        if '__main__' not in self.source and 'if __name__' not in self.source:
            problems.append("  No __main__ block — proof may not be directly runnable")

        if 'verdict' not in self.source.lower():
            problems.append("  No 'verdict' found — proof may not produce a clear conclusion")

        if problems:
            self.issues.append(("General: Proof may not be self-contained", problems))
        else:
            self.passed.append("General: Self-contained proof with __main__ and verdict")

    def check_claim_holds_computed(self):
        """Check that verdict-controlling variables are computed, not hardcoded.

        Scans for any variable named *claim_holds* (including variants like
        overall_claim_holds, sc1_claim_holds) and checks that they are assigned
        from compare() or a compound expression, not from bare True/False literals.
        """
        # Match claim_holds and variants: overall_claim_holds, sc1_claim_holds,
        # subclaim_a_holds, subclaim_b_holds, etc.
        pattern = re.compile(r'\s*(\w*(?:claim_holds|_holds)\w*)\s*=\s*(.+)')
        found_any = False

        for i, line in enumerate(self.lines, 1):
            if line.strip().startswith("#"):
                continue
            m = pattern.match(line)
            if m:
                found_any = True
                var_name = m.group(1)
                rhs = m.group(2).strip()
                if rhs in ("True", "False"):
                    self.issues.append((
                        f"Verdict: {var_name} is hardcoded to {rhs} (line {i}) — "
                        "must use compare() so the verdict is computed from evidence",
                        [],
                    ))
                elif "compare(" in rhs:
                    self.passed.append(f"Verdict: {var_name} assigned from compare()")
                else:
                    # Could be a variable alias (overall_claim_holds = sc1 and sc2)
                    # or a boolean expression — warn, don't fail
                    self.warnings.append((
                        f"Verdict: {var_name} assigned from '{rhs}' (line {i}) — "
                        "prefer using compare() for auditable verdict computation",
                        [],
                    ))

        if not found_any:
            # Check inside __main__ block as fallback
            for i, line in enumerate(self.lines, 1):
                if "claim_holds" in line and "compare(" in line:
                    self.passed.append("Verdict: claim_holds assigned from compare() (inside __main__)")
                    return

    def check_unused_imports(self):
        """Check for imported-but-unused functions from scripts.*

        Uses AST to find actual call sites. For critical functions
        (verify_all_citations, etc.), requires a real call — promotes to ISSUE.
        For non-critical functions, falls back to word-occurrence count
        to tolerate comment/docstring mentions (preserving existing behavior).

        If AST parsing fails (SyntaxError), skips the check entirely —
        we cannot distinguish "imported but unused" from "can't parse".
        """
        CRITICAL_FUNCTIONS = {
            "verify_all_citations", "verify_citation",
            "verify_data_values", "verify_search_registry",
        }

        imported = extract_script_imports(self.source)
        call_sites = find_call_sites(self.source)

        if call_sites is None:
            # Source has syntax errors — can't reliably detect call sites.
            # Record as a warning (not silent skip) so the validator output
            # shows this check was not performed.
            self.warnings.append((
                "Contract: Could not check unused imports — source has syntax errors",
                [],
            ))
            return

        unused = []
        for name in imported:
            if name in call_sites:
                continue  # Actually called — not unused
            if name in CRITICAL_FUNCTIONS:
                # Critical: no call site = unused, period
                unused.append(name)
            else:
                # Non-critical: fall back to word-occurrence count.
                # A name mentioned >1 time (import + comment/docstring)
                # is tolerated — matches existing behavior.
                occurrences = len(re.findall(
                    r'\b' + re.escape(name) + r'\b', self.source
                ))
                if occurrences <= 1:
                    unused.append(name)

        if unused:
            critical_unused = [n for n in unused if n in CRITICAL_FUNCTIONS]
            other_unused = [n for n in unused if n not in CRITICAL_FUNCTIONS]

            if critical_unused:
                self.issues.append((
                    f"Unused critical imports: {', '.join(critical_unused)} — "
                    "imported but never called; their presence falsely satisfies "
                    "rule checks (Rule 2 / table integrity)",
                    [],
                ))
            if other_unused:
                self.warnings.append((
                    f"Unused imports from scripts.*: {', '.join(other_unused)} — "
                    "imported but never called (dead code that may falsely satisfy rule checks)",
                    [],
                ))
        else:
            self.passed.append("Contract: All imported script functions are used")

    def check_verdict_branches(self):
        """Check that verdict assignment has proper conditional branches.

        Instead of checking indentation (which fails inside __main__), we check:
        1. Single verdict assignment with no `if` on line → hardcoded
        2. Multiple verdict assignments → conditional (branched)
        3. Ternary → conditional
        4. Warn if no else/fallback branch
        """
        verdict_lines = []
        for i, line in enumerate(self.lines, 1):
            if line.strip().startswith("#"):
                continue
            if re.search(r'\bverdict\s*=\s*["\']', line):
                verdict_lines.append((i, line))

        if not verdict_lines:
            return

        if len(verdict_lines) == 1:
            lineno, line = verdict_lines[0]
            if " if " in line:
                self.passed.append("Verdict: ternary verdict assignment (conditional)")
            else:
                self.issues.append((
                    f"Verdict: only one verdict assignment found (line {lineno}) — "
                    "verdict appears hardcoded. Use if/elif/else branches or a ternary.",
                    [],
                ))
            return

        has_else_verdict = bool(re.search(
            r'^\s+else\s*:\s*\n\s+verdict\s*=', self.source, re.MULTILINE
        ))
        if not has_else_verdict:
            self.warnings.append((
                "Verdict: no fallback (else) branch in verdict assignment — "
                "verdict variable may be unassigned on some code paths",
                [],
            ))
        else:
            self.passed.append("Verdict: verdict assignment has conditional branches with fallback")

    def check_proof_direction(self):
        """Check that proof_direction is present when disproof logic is used.

        The qualitative template uses CLAIM_FORMAL.get("proof_direction") == "disprove"
        to flip the verdict. If proof_direction is missing, the get() silently returns
        None, and the verdict defaults to the affirm path — a 180-degree flip.

        Exception: contested qualifier proofs produce DISPROVED via the
        is_contested_qualifier branch, not via proof_direction. Suppress
        the warning when that branch is detected.
        """
        # Match any code that reads proof_direction:
        #   - is_disproof = CLAIM_FORMAL.get("proof_direction") == "disprove"
        #   - if CLAIM_FORMAL.get("proof_direction") == "disprove":
        #   - is_disproof = ... "proof_direction" ...
        uses_disproof_logic = bool(re.search(
            r'''\.get\(\s*["']proof_direction["']\s*\)|'''
            r'''(?:is_disproof|proof_direction)\s*=.*(?:disprove|proof_direction)''',
            self.source,
        ))
        has_proof_direction_key = bool(re.search(
            r'''["']proof_direction["']\s*:''',
            self.source,
        ))
        has_contested_qualifier = bool(re.search(
            r'is_contested_qualifier', self.source,
        ))

        if uses_disproof_logic and not has_proof_direction_key and not has_contested_qualifier:
            self.issues.append((
                "Verdict: Code references proof_direction but CLAIM_FORMAL has no "
                "\"proof_direction\" key — verdict will silently default to affirm "
                "(PROVED instead of DISPROVED)",
                [],
            ))
        elif uses_disproof_logic and has_proof_direction_key:
            self.passed.append("Verdict: proof_direction present in CLAIM_FORMAL")
        elif uses_disproof_logic and has_contested_qualifier:
            self.passed.append("Verdict: contested qualifier branch handles disproof logic")

    def check_compound_operator(self):
        """Check that compound proofs include compound_operator in CLAIM_FORMAL."""
        has_sub_claims = bool(re.search(r'"sub_claims"', self.source))
        has_compound_operator = bool(re.search(
            r'''["']compound_operator["']\s*:''', self.source,
        ))
        if has_sub_claims and not has_compound_operator:
            self.warnings.append((
                "Compound: sub_claims found but no compound_operator in CLAIM_FORMAL",
                [],
            ))
        elif has_sub_claims and has_compound_operator:
            self.passed.append("Compound: compound_operator present in CLAIM_FORMAL")

    # ------------------------------------------------------------------
    # Run all checks
    # ------------------------------------------------------------------

    def validate(self) -> bool:
        """Run all rule checks and print results.

        Returns True if no issues (warnings are OK).
        """
        self.check_rule1_no_handtyped_values()
        self.check_rule2_citation_verification()
        self.check_rule3_system_time()
        self.check_rule4_claim_interpretation()
        self.check_rule5_adversarial()
        self.check_rule6_independent_crosscheck()
        self.check_rule6_per_subclaim()
        self.check_rule7_no_hardcoded_constants()
        self.check_fact_registry()
        self.check_json_summary()
        self.check_extraction_verification()
        self.check_table_data_integrity()
        self.check_general_selfcontained()
        self.check_claim_holds_computed()
        self.check_unused_imports()
        self.check_verdict_branches()
        self.check_proof_direction()
        self.check_compound_operator()
        self.check_coi_flags_presence()

        # Print report
        print(f"Validating: {self.filename}")
        print("=" * 60)

        if self.passed:
            print("\n\u2713 PASSED:")
            for msg in self.passed:
                print(f"  {msg}")

        if self.warnings:
            print("\n\u26a0 WARNINGS:")
            for msg, details in self.warnings:
                print(f"  {msg}")
                for d in details:
                    print(f"    {d}")

        if self.issues:
            print("\n\u2717 ISSUES (must fix):")
            for msg, details in self.issues:
                print(f"  {msg}")
                for d in details:
                    print(f"    {d}")

        total = len(self.passed) + len(self.warnings) + len(self.issues)
        print(f"\n{'=' * 60}")
        print(f"Result: {len(self.passed)}/{total} checks passed, "
              f"{len(self.issues)} issues, {len(self.warnings)} warnings")

        if self.issues:
            print("STATUS: FAIL — fix issues before presenting proof")
            return False
        elif self.warnings:
            print("STATUS: PASS with warnings — review recommended")
            return True
        else:
            print("STATUS: PASS")
            return True


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/validate_proof.py proof_file.py")
        sys.exit(1)

    filepath = sys.argv[1]
    if not os.path.isfile(filepath):
        print(f"ERROR: File not found: {filepath}")
        sys.exit(1)

    validator = ProofValidator(filepath)
    ok = validator.validate()
    sys.exit(0 if ok else 1)
