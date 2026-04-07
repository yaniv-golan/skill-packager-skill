"""
fetch.py — HTTP fetching with fallback chain for proof-engine.

Handles: live fetch -> snapshot -> Wayback Machine fallback.
Also handles PDF text extraction.

Extracted from verify_citations.py to separate transport from matching logic.
"""

import re

try:
    import requests
except ImportError:
    requests = None


# ---------------------------------------------------------------------------
# PDF text extraction
# ---------------------------------------------------------------------------

def extract_pdf_text(content: bytes) -> str | None:
    """Extract text from PDF bytes. Tries pdfplumber first, then PyPDF2.

    Returns None if no PDF library is available or if extraction fails.
    """
    try:
        import pdfplumber
        import io
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages)
    except ImportError:
        pass
    except Exception:
        pass
    try:
        import PyPDF2
        import io
        reader = PyPDF2.PdfReader(io.BytesIO(content))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except ImportError:
        pass
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# Wayback Machine fallback
# ---------------------------------------------------------------------------

def try_wayback(url: str, timeout: int = 15) -> str | None:
    """Try fetching a URL from the Wayback Machine. Returns page text or None."""
    if requests is None:
        return None
    wayback_url = f"https://web.archive.org/web/{url}"
    try:
        resp = requests.get(wayback_url, timeout=timeout,
                            headers={"User-Agent": "proof-engine/1.0"},
                            allow_redirects=True)
        resp.raise_for_status()
        return resp.text
    except requests.exceptions.RequestException:
        return None


# ---------------------------------------------------------------------------
# Page fetching with fallback chain
# ---------------------------------------------------------------------------

def fetch_page(url: str, timeout: int = 15, snapshot: str = None,
               wayback_fallback: bool = False,
               skip_live_fetch: bool = False) -> tuple[str | None, str, str | None]:
    """Fetch page text using the standard fallback chain.

    Args:
        url: The URL to fetch.
        timeout: Fetch timeout in seconds.
        snapshot: Pre-fetched page text for offline verification.
        wayback_fallback: If True, try Wayback Machine as last resort.
        skip_live_fetch: If True, skip live HTTP fetch (e.g., when requests
            is unavailable in the calling module).

    Returns:
        (page_text, fetch_mode, error_message)
        - page_text: The page text, or None if all methods failed
        - fetch_mode: "live", "snapshot", "wayback", or "fetch_failed"
        - error_message: Error description if failed, else None
    """
    # --- 1. Try live fetch ---
    fetch_error_msg = None
    if requests is not None and not skip_live_fetch:
        try:
            resp = requests.get(
                url,
                timeout=timeout,
                headers={"User-Agent": "proof-engine/1.0"},
                allow_redirects=True,
            )
            resp.raise_for_status()

            content_type = resp.headers.get("Content-Type", "")
            is_pdf = "application/pdf" in content_type or url.lower().endswith(".pdf")

            if is_pdf:
                pdf_text = extract_pdf_text(resp.content)
                if pdf_text is None:
                    fetch_error_msg = "PDF detected but no extraction library available (pip install pdfplumber)"
                else:
                    return pdf_text, "live", None
            else:
                return resp.text, "live", None

        except requests.exceptions.Timeout:
            fetch_error_msg = f"Timeout after {timeout}s on {url}"
        except requests.exceptions.ConnectionError as e:
            fetch_error_msg = f"Connection error on {url}: {e}"
        except requests.exceptions.HTTPError:
            fetch_error_msg = f"HTTP {resp.status_code} on {url}"
        except requests.exceptions.RequestException as e:
            fetch_error_msg = f"{e}"
    else:
        fetch_error_msg = "requests package not installed — skipping live fetch"

    # --- 2. Try snapshot fallback ---
    if snapshot:
        return snapshot, "snapshot", None

    # --- 3. Try Wayback Machine ---
    if wayback_fallback:
        wayback_text = try_wayback(url, timeout)
        if wayback_text is not None:
            return wayback_text, "wayback", None

    # --- 4. All methods exhausted ---
    return None, "fetch_failed", fetch_error_msg
