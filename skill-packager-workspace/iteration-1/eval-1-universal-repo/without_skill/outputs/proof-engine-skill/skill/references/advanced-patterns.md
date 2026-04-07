# Advanced Patterns

Read this when encountering complex quotes, table-sourced data, or Unicode extraction issues.

## Two-Phase Extraction (for complex quotes)

When `parse_number_from_quote()` or simple regex fails on real-world text (Unicode mismatches, special characters, unusual formatting), use the **two-phase extraction** pattern:

**Phase 1 (proof-writing time, LLM available):** Write a custom extraction function tailored to the specific quote. This function is literal Python code in the proof script — fully visible and auditable. It includes the quote it operates on, a normalization step for the specific Unicode quirks found, the extraction logic, and an assertion via `verify_extraction()`.

**Phase 2 (re-run time, no LLM needed):** The custom function runs as normal Python. It's self-contained. Anyone can read the code and see exactly how the value was extracted.

```python
from scripts.smart_extract import normalize_unicode, verify_extraction

def extract_ghg_warming_low(quote):
    '''Extract GHG low-end warming from NOAA page.
    The page uses en-dashes and degree symbols — normalize before extracting.'''
    normalized = normalize_unicode(quote)
    match = re.search(r'warming of ([\d.]+)', normalized)
    value = float(match.group(1))
    verify_extraction(value, quote, "ghg_warming_low")
    return value
```

Use `diagnose_mismatch(page_text, quote)` to understand WHY a quote fails verification, then write the custom extractor to handle those specific differences.

## Table-Sourced Numeric Data

For claims backed by HTML tables (CPI values, GDP figures, population data), the numeric values aren't in prose text that can be quoted. Use the `data_values` pattern.

**Choosing quotes for data-table pages**: Many aggregator sites are mostly tables with minimal prose. Page titles and JS-rendered headings often fail live verification. Strategies for picking quotes that survive:
- Use static footer text (e.g., "Data sourced from U.S. Bureau of Labor Statistics")
- Use the `<meta name="description">` content (often static HTML)
- Use column headers or table captions that appear in raw HTML
- If no stable prose exists, use `snapshot` mode or accept partial verification — the real verification is `verify_data_values()` confirming the numbers appear on the page

**Verdict when quotes fail but data_values pass**: If `verify_all_citations()` returns `not_found` or `partial` for the quote, but `verify_data_values()` confirms all numeric values on the page, this is stronger evidence than it looks. The quote verification failing is a page-structure issue, not an accuracy issue. Note this in the adversarial checks and consider the data verified for verdict purposes — the verdict can still be `PROVED` if the data values are confirmed and cross-checked, even if the prose quote failed verification. Document the reasoning in the proof's verdict logic.

```python
empirical_facts = {
    "source_a_cpi": {
        # Prose quote verifies source authority
        "quote": "The CPI for USA is calculated and issued by: U.S. Bureau of Labor Statistics",
        "url": "https://www.rateinflation.com/consumer-price-index/usa-historical-cpi/",
        "source_name": "RateInflation.com (sourced from BLS)",
        # Table values stored as strings — parsed via parse_number_from_quote()
        "data_values": {"cpi_1913": "9.883", "cpi_2024": "313.689"},
    },
}
```

- The `quote` field verifies the source's authority via `verify_all_citations()`
- Parse table values with `parse_number_from_quote(fact["data_values"]["cpi_1913"], r"([\d.]+)", "B1_cpi_1913")`
- **Do NOT call `verify_extraction()` on data_values** — it's circular. Instead, call `verify_data_values()` to confirm each value appears on the source page:
  ```python
  dv_results_a = verify_data_values(
      url=empirical_facts["source_a"]["url"],
      data_values=empirical_facts["source_a"]["data_values"],
      fact_id="B1",
  )
  ```
  This fetches the page and checks that each value string (e.g., "9.883") appears in the page text. If the site returns 403, it falls back to snapshot/Wayback like `verify_citation()`.
- Use `cross_check()` to compare values across independent sources
- The audit doc should distinguish "source authority verified via quote" from "numeric data extracted from table"

**Multiple extractions per source**: When a single source provides multiple data values, use sub-IDs in the extractions dict:

```python
extractions = {
    "B1_cpi_1913": {
        "value": str(cpi_1913_a),
        "value_in_quote": True,  # parsed from data_values, not free-text
        "quote_snippet": "data_values['cpi_1913']",
    },
    "B1_cpi_2024": {
        "value": str(cpi_2024_a),
        "value_in_quote": True,
        "quote_snippet": "data_values['cpi_2024']",
    },
}
```

These sub-IDs (B1_cpi_1913, B1_cpi_2024) don't need to match FACT_REGISTRY keys — they are extraction-level detail within a single source fact.

See hardening-rules.md "Citing structured/tabular data" for the full template.
