# Environment and Source Handling

Read this when facing fetch failures, paywalled sources, or sandboxed environments.

## Environment-Specific Notes

- **Claude Code:** Has outbound HTTP from Python, so live fetch is the primary path. `verify_all_citations()` fetches URLs directly. WebFetch/WebSearch tools return processed summaries, NOT raw page text — do not use them to populate `snapshot` fields. Keep web research (Step 2) in the main conversation thread; subagents may not have web access.
- **ChatGPT:** Python sandbox has no outbound HTTP. Use the browsing capability during Step 2 to fetch each source page and include raw page text as the `snapshot` field in `empirical_facts`.
- **Other sandboxed environments:** If Python cannot fetch URLs, use the snapshot workflow — pre-fetch page text by any available means and embed it in `empirical_facts`.

## Verification Fallback Chain

1. **Live fetch** — try to fetch the URL directly. If successful, verify against live page.
2. **Snapshot** — if live fetch fails and a `snapshot` field is present, verify against the pre-fetched text. This is deterministic and user-provided.
3. **Wayback Machine** — if live and snapshot both fail and `wayback_fallback=True`, try the Wayback Machine archive. This is opt-in to avoid silently changing existing proof behavior.

## Fetch Result Statuses

- `verified` — quote found (full match or >=80% fragment coverage)
- `partial` — only a fragment matched (degraded verification)
- `not_found` — page fetched but quote not there (wrong quote or URL)
- `fetch_failed` — could not obtain page text by any method

## PDF Citations

When a URL returns a PDF, `verify_citation()` extracts text using `pdfplumber` or `PyPDF2` (optional dependencies). Install with `pip install pdfplumber` for PDF support.

## Handling Paywalled Sources

Many scientific papers and reports are behind paywalls. When a key source returns 403 or requires authentication:

1. **Try the abstract URL** — PubMed (pubmed.ncbi.nlm.nih.gov), DOI resolver (doi.org), or Google Scholar often have abstracts with key findings. Cite the abstract URL instead.
2. **Check for open-access versions** — many papers have preprints on arXiv, bioRxiv, medRxiv, or the author's institutional page.
3. **Cite the abstract quote** — if the abstract contains the key finding, that's a valid citation. Note "cited from abstract; full text behind paywall" in the audit doc.
4. **Find alternative sources** — if the claim is well-established, there are usually multiple sources. Prefer open-access ones.
5. **Last resort** — if the paywalled source is essential and no alternative exists, cite it with whatever quote is publicly visible and mark as "Not verified (paywall)" in the audit doc. This does not invalidate the proof if other verified sources support the same finding.

## Government Statistics Sites (.gov)

BLS, FRED, Federal Reserve, Census, and similar .gov sites systematically return 403 to automated fetching. This is the norm, not the exception. For government statistics:
- **Preferred:** Use reliable aggregators as citation URLs: rateinflation.com, inflationdata.com (for CPI); measuringworth.com, officialdata.org (for historical data); fred.stlouisfed.org (for FRED series). These are tier 3 (established reference) in credibility scoring.
- **Fallback:** Use the snapshot workflow — fetch via browser during Step 2, embed as `snapshot` in `empirical_facts`
- Note in the audit doc that aggregator sources republish data from the primary authority (e.g., "sourced from BLS via rateinflation.com")

## International Organization Sites (.org / .int)

UN agencies, ICJ, WHO, and similar intergovernmental orgs frequently return 403 or serve JS-rendered pages. Common offenders: `unrwa.org`, `ohchr.org`, `un.org` subdomains, `who.int`, `icj-cij.org`.

- **Preferred:** Use the snapshot workflow — fetch via browser during Step 2, embed as `snapshot` in `empirical_facts`. Alternatively, use `wayback_fallback=True` — these domains are well-archived.
- **Fallback:** Cite official press releases (often static HTML and more fetchable than main site pages).
- **Last resort:** Cite major news coverage of the same finding. When doing this, warn that multiple news outlets may derive from the same press release or wire report — this does NOT count as independent sourcing for Rule 6. Note in the audit doc: "Primary source at [URL] returned 403; cited via [news outlet] coverage. Independence note: [outlet] reporting derives from [primary source] press release."
- When using any alternative URL for a primary source, always document the substitution in the audit doc.

## Major News and Advocacy Sites

Many news sites (timesofisrael.com, npr.org) and advocacy/think-tank sites (fdd.org, embassies.gov.il) also return 403 or block automated fetching. This is increasingly common, not limited to .gov/.int domains.

- **Preferred:** Use the snapshot workflow — fetch via browser during Step 2, embed as `snapshot` in `empirical_facts`.
- **Fallback:** Find the same reporting on a secondary outlet that is fetchable. Document the substitution in the audit: "Primary source at [URL] returned 403; cited via [alternative outlet]. Same underlying reporting."
- **Wayback:** Use `wayback_fallback=True` — major news sites are usually well-archived.

When multiple primary sources are unfetchable for a topic, this is a signal to prioritize snapshot pre-fetching during Step 2 rather than discovering 403s at citation verification time.

## WebFetch / WebSearch Summaries Are Not Quotes

WebFetch and WebSearch return processed summaries, not raw page text. Text from summaries must never be used directly as the `quote` field in `empirical_facts` — the wording may be paraphrased, reordered, or condensed.

**Workflow for obtaining verbatim quotes:**
1. Use WebFetch/WebSearch during Step 2 to identify relevant sources and understand their content.
2. Note the key finding and a distinctive keyword or phrase.
3. Before writing `empirical_facts`, obtain the actual page text via one of:
   - (a) Python `requests.get()` in proof.py (this is what `verify_all_citations` will use anyway)
   - (b) Browser fetch during Step 2, embedded as `snapshot`
   - (c) Wayback Machine archive
4. Extract the verbatim sentence from the raw page text and use it as the `quote` field.

Do NOT re-fetch via WebFetch expecting verbatim text — WebFetch always returns summaries regardless of how you prompt it.

If citation verification returns `not_found` or `partial` on a source you know contains the finding, suspect paraphrasing. Obtain the raw page text and update the quote before finalizing the proof.
