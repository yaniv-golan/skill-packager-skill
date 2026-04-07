"""
extract_values.py — Parse dates, numbers, and percentages FROM citation quote strings.

Enforces Rule 1: Never hand-type extracted values. All values must be
programmatically derived from the quote text so that transcription errors
are impossible.

Usage as module:
    from scripts.extract_values import parse_date_from_quote, parse_number_from_quote, parse_percentage_from_quote

Usage as CLI:
    python scripts/extract_values.py date "On May 14, 1948, David Ben-Gurion..."
    python scripts/extract_values.py number "population reached 13,988,129"
    python scripts/extract_values.py percent "grew by 12.5% in Q3"
"""

import re
import sys
import datetime


def parse_date_from_quote(quote: str, fact_id: str = "unknown") -> datetime.date:
    """Parse a date from a citation quote string.

    Tries patterns in order of specificity:
      1. "Month DD, YYYY"   (e.g., "May 14, 1948")
      2. "DD Month YYYY"    (e.g., "14 May 1948")
      3. "Month DD YYYY"    (no comma)
      4. ISO "YYYY-MM-DD"
      5. Fallback: dateutil fuzzy parse (prints warning)

    Returns:
        datetime.date

    Raises:
        ValueError: if no date pattern found in the quote.
    """
    MONTHS = {
        "january": 1, "february": 2, "march": 3, "april": 4,
        "may": 5, "june": 6, "july": 7, "august": 8,
        "september": 9, "october": 10, "november": 11, "december": 12,
    }

    # Pattern 1: Month DD, YYYY
    m = re.search(
        r'\b(' + '|'.join(MONTHS.keys()) + r')\s+(\d{1,2}),?\s+(\d{4})\b',
        quote, re.IGNORECASE,
    )
    if m:
        month = MONTHS[m.group(1).lower()]
        day = int(m.group(2))
        year = int(m.group(3))
        result = datetime.date(year, month, day)
        print(f"  {fact_id}: Parsed '{m.group(0)}' -> {result}")
        return result

    # Pattern 2: DD Month YYYY
    m = re.search(
        r'\b(\d{1,2})\s+(' + '|'.join(MONTHS.keys()) + r')\s+(\d{4})\b',
        quote, re.IGNORECASE,
    )
    if m:
        day = int(m.group(1))
        month = MONTHS[m.group(2).lower()]
        year = int(m.group(3))
        result = datetime.date(year, month, day)
        print(f"  {fact_id}: Parsed '{m.group(0)}' -> {result}")
        return result

    # Pattern 3: ISO YYYY-MM-DD
    m = re.search(r'\b(\d{4})-(\d{2})-(\d{2})\b', quote)
    if m:
        result = datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        print(f"  {fact_id}: Parsed '{m.group(0)}' -> {result}")
        return result

    # Pattern 4: dateutil fuzzy fallback
    try:
        import dateutil.parser
        result = dateutil.parser.parse(quote, fuzzy=True).date()
        print(f"  {fact_id}: [dateutil fuzzy] Parsed -> {result}  *** VERIFY MANUALLY ***")
        return result
    except (ValueError, ImportError):
        pass

    raise ValueError(
        f"{fact_id}: Could not parse any date from quote: '{quote[:80]}...'"
    )


def parse_number_from_quote(quote: str, pattern: str = None, fact_id: str = "unknown") -> float:
    """Parse a number from a citation quote string.

    Args:
        quote: The citation quote text.
        pattern: Optional regex with ONE capture group for the number.
                 The captured string is cleaned of commas before conversion.
        fact_id: Identifier for logging.

    Returns:
        float (integers are returned as float for consistency).

    Raises:
        ValueError: if no number found.
    """
    if pattern:
        m = re.search(pattern, quote)
        if m:
            try:
                raw = m.group(1).replace(",", "").strip()
            except IndexError:
                raise ValueError(
                    f"{fact_id}: Pattern '{pattern}' matched but has no capture group. "
                    f"Add parentheses around the number, e.g. r'population (\\d+)'"
                )
            result = float(raw)
            orig = m.group(1)
            # Show original string when float repr drops trailing zeros (9.900 -> 9.9)
            if raw != str(result):
                print(f"  {fact_id}: Parsed '{orig}' -> {result} (source text: '{orig}')")
            else:
                print(f"  {fact_id}: Parsed '{orig}' -> {result}")
            return result
        raise ValueError(f"{fact_id}: Pattern '{pattern}' not found in quote: '{quote[:80]}...'")

    # Default: find all number-like tokens in one unified regex.
    # The regex matches (in order of priority within alternation):
    #   1. Comma-formatted integers: 13,988,129
    #   2. Standard decimals: 3.14, 2023
    #   3. Leading-zero-omitted decimals: .40, -.33 (common in statistics)
    candidates = re.findall(r'-?[\d,]+\.?\d*|-?\.\d+', quote)
    # Filter out empty or trivial matches (lone commas, lone dots)
    candidates = [c for c in candidates if c.strip(",. ") and c not in (",", ".")]

    # Strip trailing/leading punctuation commas before classification
    # (e.g. "2023," from "In 2023, ..." should not be treated as comma-formatted)
    candidates = [c.strip(",") for c in candidates]
    candidates = [c for c in candidates if c.strip(",. ") and c not in (",", ".")]

    # Classify: substantial = comma-formatted (internal commas) or >2 digits (years, large numbers)
    substantial = [c for c in candidates
                   if "," in c or len(c.replace(",", "").replace(".", "").replace("-", "")) > 2]
    # Prefer comma-formatted (true large numbers) over plain multi-digit integers
    substantial.sort(key=lambda c: (0 if "," in c else 1))
    if substantial:
        raw = substantial[0].replace(",", "")
        result = float(raw)
        print(f"  {fact_id}: Parsed '{substantial[0]}' -> {result}")
        return result

    # Fall back to first candidate (could be LZO like .40, or a small int like 5)
    if candidates:
        raw = candidates[0].replace(",", "")
        result = float(raw)
        print(f"  {fact_id}: Parsed '{candidates[0]}' -> {result}")
        return result

    raise ValueError(f"{fact_id}: No number found in quote: '{quote[:80]}...'")


def parse_percentage_from_quote(quote: str, fact_id: str = "unknown") -> float:
    """Parse a percentage value from a citation quote string.

    Finds patterns like "45.7%", "45 %", "45 percent".

    Returns:
        float — the numeric value (e.g., 45.7, not 0.457).

    Raises:
        ValueError: if no percentage pattern found.
    """
    # "N%" or "N %" patterns
    m = re.search(r'([\d,]+\.?\d*)\s*%', quote)
    if m:
        raw = m.group(1).replace(",", "")
        result = float(raw)
        print(f"  {fact_id}: Parsed '{m.group(0)}' -> {result}%")
        return result

    # "N percent" pattern
    m = re.search(r'([\d,]+\.?\d*)\s+percent', quote, re.IGNORECASE)
    if m:
        raw = m.group(1).replace(",", "")
        result = float(raw)
        print(f"  {fact_id}: Parsed '{m.group(0)}' -> {result}%")
        return result

    raise ValueError(f"{fact_id}: No percentage found in quote: '{quote[:80]}...'")


def parse_range_from_quote(quote: str, pattern: str = None, fact_id: str = "unknown") -> tuple:
    """Parse a numeric range from a citation quote string.

    Finds patterns like "1.0°C to 2.0°C", "1.0–2.0", "93% to 123%",
    "0.8 to 1.3", "between 1.0 and 2.0".

    Args:
        quote: The citation quote text.
        pattern: Optional regex with TWO capture groups for low and high values.
        fact_id: Identifier for logging.

    Returns:
        tuple of (low: float, high: float).

    Raises:
        ValueError: if no range pattern found.
    """
    # Normalize Unicode first (en-dashes → hyphens, etc.)
    try:
        from scripts.smart_extract import normalize_unicode
    except ImportError:
        from smart_extract import normalize_unicode
    norm = normalize_unicode(quote)

    if pattern:
        m = re.search(pattern, norm)
        if m:
            try:
                low = float(m.group(1).replace(",", ""))
                high = float(m.group(2).replace(",", ""))
            except (IndexError, ValueError) as e:
                raise ValueError(
                    f"{fact_id}: Pattern '{pattern}' matched but could not extract two numbers: {e}"
                )
            print(f"  {fact_id}: Parsed range '{m.group(0)}' -> ({low}, {high})")
            return (low, high)
        raise ValueError(f"{fact_id}: Pattern '{pattern}' not found in quote: '{quote[:80]}...'")

    # Default patterns, tried in order.
    # Unit chars: °, %, letters — skipped between numbers and "to"/"and".
    _unit = r'[°%]?\w*'
    range_patterns = [
        # "N to N" with optional units (°C, %, etc.)
        r'([\d,]+\.?\d*)\s*' + _unit + r'\s+to\s+([\d,]+\.?\d*)',
        # "between N and N"
        r'between\s+([\d,]+\.?\d*)\s*' + _unit + r'\s+and\s+([\d,]+\.?\d*)',
        # "N–N" or "N-N" (en-dash or hyphen between numbers)
        r'([\d,]+\.?\d*)\s*[-]\s*([\d,]+\.?\d*)',
    ]

    for pat in range_patterns:
        for m in re.finditer(pat, norm, re.IGNORECASE):
            # Reject if this match sits inside an ISO date (YYYY-MM-DD)
            full_context = norm[max(0, m.start() - 5):m.end() + 5]
            if re.search(r'\d{4}-\d{2}-\d{2}', full_context):
                continue  # skip this match, try next occurrence of same pattern
            low = float(m.group(1).replace(",", ""))
            high = float(m.group(2).replace(",", ""))
            if low > high:
                low, high = high, low
            print(f"  {fact_id}: Parsed range '{m.group(0)}' -> ({low}, {high})")
            return (low, high)

    raise ValueError(f"{fact_id}: No range found in quote: '{quote[:80]}...'")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage:")
        print('  python extract_values.py date   "On May 14, 1948, David Ben-Gurion..."')
        print('  python extract_values.py number  "population reached 13,988,129"')
        print('  python extract_values.py percent "grew by 12.5% in Q3"')
        print('  python extract_values.py range   "warming of 1.0°C to 2.0°C"')
        sys.exit(1)

    mode = sys.argv[1].lower()
    quote = sys.argv[2]

    try:
        if mode == "date":
            result = parse_date_from_quote(quote, "cli")
            print(f"Result: {result}")
        elif mode == "number":
            result = parse_number_from_quote(quote, fact_id="cli")
            print(f"Result: {result}")
        elif mode in ("percent", "percentage"):
            result = parse_percentage_from_quote(quote, "cli")
            print(f"Result: {result}%")
        elif mode == "range":
            low, high = parse_range_from_quote(quote, fact_id="cli")
            print(f"Result: ({low}, {high})")
        else:
            print(f"Unknown mode '{mode}'. Use: date, number, percent, range")
            sys.exit(1)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
