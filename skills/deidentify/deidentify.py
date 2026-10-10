#!/usr/bin/env python3
"""
Clinical research data de-identification (LLM-free).

Scans Excel/CSV files for Protected Health Information (PHI) using regex
and column-name heuristics, walks the researcher through an interactive
terminal review, then produces a de-identified copy with mapping and
audit trail.

Supports 12 country locales (kr, us, jp, cn, de, uk, fr, ca, au, in, it, es)
with country-specific PHI patterns.  Custom locales via --locale-file.

Usage:
    python deidentify.py scan  input.xlsx [--locale kr]
    python deidentify.py review scan_report.json
    python deidentify.py apply  reviewed_report.json [--hash-mapping]
    python deidentify.py full   input.xlsx [--locale kr] [--auto-accept-safe]
"""

# Annotations such as `re.Pattern | None` are evaluated at import time on
# Python 3.9 (macOS /usr/bin/python3) and crash it; postponing them keeps
# the script importable there.
from __future__ import annotations

import argparse
import csv
import hashlib
import hmac
import json
import logging
import os
import random
import re
import secrets
import stat
import sys
from datetime import date, datetime, time, timedelta
from pathlib import Path

log = logging.getLogger("deidentify")

REPORT_VERSION = 1

# ================================================================
# Section 1: Constants + Locale Loading
# ================================================================

LOCALES_DIR = Path(__file__).parent / "locales"

# Universal column names (English — common across all research locales).
UNIVERSAL_COLUMN_NAMES: dict[str, str] = {
    "patient_name": "name", "patientname": "name", "pt_name": "name",
    "name": "name", "first_name": "name", "last_name": "name",
    "ssn": "rrn", "social_security": "rrn",
    "dob": "date", "date_of_birth": "date", "birth_date": "date",
    "birthdate": "date",
    "phone": "phone", "telephone": "phone", "mobile": "phone",
    "phone_number": "phone", "cell": "phone",
    "address": "address", "home_address": "address", "street": "address",
    "zip": "address", "zipcode": "address", "zip_code": "address",
    "email": "email", "email_address": "email",
    "mrn": "id", "medical_record": "id", "chart_no": "id",
    "patient_id": "id", "patientid": "id", "chart_number": "id",
    "record_number": "id", "hospital_id": "id",
    "insurance_no": "insurance", "insurance_number": "insurance",
}

# An English month name or abbreviation, any case, as a whole word.
_MONTH_WORD = (r"(?i:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|june?"
               r"|july?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?"
               r"|nov(?:ember)?|dec(?:ember)?)(?![A-Za-z])")

# Universal value patterns (always active regardless of locale).
UNIVERSAL_VALUE_PATTERNS: list[tuple[re.Pattern, str]] = [
    # Email
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"), "email"),
    # ISO date  YYYY-MM-DD or YYYY.MM.DD or YYYY/MM/DD
    (re.compile(r"\b(19|20)\d{2}[-/.](0[1-9]|1[0-2])[-/.](0[1-9]|[12]\d|3[01])\b"), "date"),
    # YYMMDD (6 digits that look like a birthdate, standalone)
    (re.compile(r"\b([5-9]\d|0[0-4])(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\b"), "date"),
    # YYYYMMDD (compact date, also inside text such as "visit=20260930")
    (re.compile(r"\b(19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\b"), "date"),
    # D/M/YYYY or M/D/YYYY (also with - or .). Only the year-first form was
    # universal, so 03/15/2024 was SAFE under any locale whose pack did not
    # list it (kr), and a SAFE column is passed through un-stripped.
    (re.compile(r"\b(0?[1-9]|[12]\d|3[01])([-/.])(0?[1-9]|[12]\d|3[01])\2(19|20)\d{2}\b"), "date"),
    # Month written as a word: 15-Mar-2024, 15MAR2024, 15 March 2024,
    # 15-Mar-24, March 15, 2024, Mar. 15 2024. These were SAFE everywhere.
    (re.compile(r"\b(0?[1-9]|[12]\d|3[01])([-\s/]?)" + _MONTH_WORD +
                r"\.?\2(19|20)\d{2}\b"), "date"),
    (re.compile(r"\b(0?[1-9]|[12]\d|3[01])([-/])" + _MONTH_WORD + r"\2\d{2}\b"), "date"),
    (re.compile(r"\b" + _MONTH_WORD +
                r"\.?\s+(0?[1-9]|[12]\d|3[01])(?:st|nd|rd|th)?,?\s+(19|20)\d{2}\b"), "date"),
]

# Separators people put between digit groups ("010 1234 5678", "010.1234.5678").
_DIGIT_SEPARATORS = re.compile(r"(?<=\d)[\s.\-/()]+(?=\d)")
_INTL_PREFIX = {k: re.compile(r"\+\d{%d}" % k) for k in (1, 2, 3)}


def _value_forms(val: str) -> list[str]:
    """The value as written, plus the forms a locale pattern expects.

    Locale patterns are written for the domestic, hyphenated form. The same
    phone number written with spaces or dots, or with an international prefix
    ("+82 10 1234 5678"), used to match nothing, and a column that matches
    nothing is passed through. The extra forms drop the separators between
    digits and rewrite a +CC prefix the domestic way (trunk "0", or none), so
    every spelling meets the same pattern. The value itself is not changed.
    """
    forms = [val]
    compact = _DIGIT_SEPARATORS.sub("", val)
    if compact != val:
        forms.append(compact)
    if "+" in compact:
        for prefix in _INTL_PREFIX.values():
            forms.extend(prefix.sub(trunk, compact) for trunk in ("0", ""))
    return forms


def list_locales() -> list[dict]:
    """List available locales from the locales/ directory."""
    locales = []
    if not LOCALES_DIR.is_dir():
        return locales
    for f in sorted(LOCALES_DIR.glob("*.json")):
        if f.name.startswith("_"):
            continue
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            locales.append({
                "code": data.get("code", f.stem),
                "name": data.get("name", f.stem),
                "native_name": data.get("native_name", ""),
                "path": str(f),
            })
        except (json.JSONDecodeError, OSError):
            continue
    return locales


def load_locale(code: str) -> dict:
    """Load locale by country code (e.g., 'kr', 'us')."""
    path = LOCALES_DIR / f"{code}.json"
    if not path.exists():
        sys.exit(f"Locale not found: {code}\n"
                 f"Available: {', '.join(l['code'] for l in list_locales())}\n"
                 f"Or use --locale-file for a custom locale.")
    return json.loads(path.read_text(encoding="utf-8"))


def load_locale_file(path: str) -> dict:
    """Load a custom locale from an arbitrary JSON file."""
    p = Path(path)
    if not p.exists():
        sys.exit(f"Locale file not found: {path}")
    return json.loads(p.read_text(encoding="utf-8"))


def select_locale_interactive() -> dict:
    """Interactive country selection prompt."""
    locales = list_locales()
    if not locales:
        sys.exit("No locale files found in locales/ directory.")

    print(f"\n{_bold('Select country / 국가 선택:')}")
    for i, loc in enumerate(locales, 1):
        native = f" ({loc['native_name']})" if loc['native_name'] != loc['name'] else ""
        print(f"  {i:2d}. {loc['name']}{native}")
    print(f"   0. Other (provide custom locale file)")

    while True:
        choice = input(f"\n> ").strip()
        if choice == "0":
            custom_path = input("  Path to custom locale JSON: ").strip()
            locale = load_locale_file(custom_path)
            print(f"  Loaded custom locale: {locale.get('name', 'Custom')}")
            return locale
        try:
            idx = int(choice)
            if 1 <= idx <= len(locales):
                locale = load_locale(locales[idx - 1]["code"])
                print(f"  Loading {locale['name']} patterns...")
                return locale
        except ValueError:
            # Try as code
            for loc in locales:
                if choice.lower() == loc["code"]:
                    locale = load_locale(choice.lower())
                    print(f"  Loading {locale['name']} patterns...")
                    return locale
        print(f"  Invalid choice. Enter 1-{len(locales)} or a country code.")


def build_locale_patterns(locale: dict) -> tuple[
    dict[str, str],
    list[tuple[re.Pattern, str]],
    re.Pattern | None,
    re.Pattern | None,
    float,
    list[str],
]:
    """Build scanning patterns from a locale dict.

    Returns:
        (column_names, value_patterns, address_re, name_re, name_min_ratio, name_columns)
    """
    # Column names: universal + locale-specific
    column_names = dict(UNIVERSAL_COLUMN_NAMES)
    column_names.update(locale.get("column_names", {}))

    # Value patterns: universal + locale-specific
    value_patterns = list(UNIVERSAL_VALUE_PATTERNS)

    # National ID. Compiled case-insensitively: locale packs write letter
    # classes in upper case (UK NINO, Indian PAN), but IDs are often exported
    # in lower case, and a missed match classifies the column SAFE, so it is
    # passed through un-stripped. A miss here is a leak, not a lost warning.
    nid = locale.get("national_id", {})
    nid_type = nid.get("phi_type", "national_id")
    for pat in nid.get("patterns", []):
        value_patterns.append((re.compile(pat, re.IGNORECASE), nid_type))

    # Phone
    for phone in locale.get("phone", []):
        value_patterns.append((re.compile(phone["pattern"]), "phone"))

    # Extra date formats
    for df in locale.get("date_formats", []):
        value_patterns.append((re.compile(df["pattern"]), "date"))

    # Address pattern
    addr_cfg = locale.get("address", {})
    address_re = None
    if addr_cfg.get("type") == "suffix_regex" and addr_cfg.get("pattern"):
        address_re = re.compile(addr_cfg["pattern"])
    elif addr_cfg.get("type") == "keywords" and addr_cfg.get("keywords"):
        # Build a regex from keywords (case-insensitive word boundary match)
        escaped = [re.escape(kw) for kw in addr_cfg["keywords"]]
        address_re = re.compile(r"(?:" + "|".join(escaped) + r")", re.IGNORECASE)
    # Postcode pattern (if available, add to value_patterns as address type).
    # Case-insensitive for the same reason as national IDs above.
    if addr_cfg.get("postcode_pattern"):
        value_patterns.append(
            (re.compile(addr_cfg["postcode_pattern"], re.IGNORECASE), "address"))

    # Name heuristic
    name_cfg = locale.get("name_heuristic", {})
    name_re = None
    if name_cfg.get("type") == "regex" and name_cfg.get("pattern"):
        name_re = re.compile(name_cfg["pattern"])
    name_min_ratio = name_cfg.get("min_ratio", 0.3)

    # Name columns (for restricting name heuristic)
    name_columns = [k for k, v in column_names.items() if v == "name"]

    return column_names, value_patterns, address_re, name_re, name_min_ratio, name_columns

# Confidence thresholds
CONF_HIGH = "high"
CONF_MEDIUM = "medium"
CONF_LOW = "low"

# ANSI helpers (respect NO_COLOR)
_NO_COLOR = bool(os.environ.get("NO_COLOR"))


def _c(code: str, text: str) -> str:
    if _NO_COLOR:
        return text
    return f"\033[{code}m{text}\033[0m"


def _red(t: str) -> str: return _c("31", t)
def _green(t: str) -> str: return _c("32", t)
def _yellow(t: str) -> str: return _c("33", t)
def _bold(t: str) -> str: return _c("1", t)
def _dim(t: str) -> str: return _c("2", t)


# ================================================================
# Section 2: File I/O
# ================================================================

def detect_format(path: Path) -> str:
    """Return 'csv', 'tsv', or 'xlsx' based on extension."""
    ext = path.suffix.lower()
    if ext == ".xlsx":
        return "xlsx"
    if ext == ".tsv":
        return "tsv"
    if ext in (".csv", ".txt", ""):
        return "csv"
    sys.exit(f"Unsupported file format: {ext}")


def detect_encoding(path: Path) -> str:
    """Detect encoding: try UTF-8, fall back to EUC-KR."""
    raw = path.read_bytes()
    # UTF-8 BOM
    if raw[:3] == b"\xef\xbb\xbf":
        return "utf-8-sig"
    try:
        raw.decode("utf-8")
        return "utf-8"
    except UnicodeDecodeError:
        pass
    try:
        raw.decode("euc-kr")
        return "euc-kr"
    except UnicodeDecodeError:
        pass
    return "utf-8"  # best effort


def _cell_text(v) -> str:
    """Excel cell value as text. Native dates become ISO text the date
    shifter can parse; str() gave "2020-01-02 00:00:00", which it could not,
    so every Excel date was replaced by [DATE_SHIFTED] and intervals were lost.
    Fractional seconds are kept: dropping them turned a 0.8 s interval into 0."""
    if v is None:
        return ""
    if isinstance(v, datetime):
        if v.time() == time(0):
            return v.strftime("%Y-%m-%d")
        return v.strftime("%Y-%m-%d %H:%M:%S.%f" if v.microsecond else "%Y-%m-%d %H:%M:%S")
    if isinstance(v, date):
        return v.isoformat()
    return str(v)


def load_tabular(path: Path) -> tuple[list[dict], dict]:
    """Load CSV/TSV/XLSX into list of row-dicts + metadata dict."""
    fmt = detect_format(path)
    meta = {"format": fmt, "path": str(path), "sheets_skipped": []}

    if fmt == "xlsx":
        try:
            import openpyxl
        except ImportError:
            sys.exit("openpyxl is required for .xlsx files.  Install: pip install openpyxl")
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        if len(wb.sheetnames) > 1:
            meta["sheets_skipped"] = wb.sheetnames[1:]
            log.warning("Multiple sheets found. Processing '%s' only. Skipped: %s",
                        wb.sheetnames[0], ", ".join(wb.sheetnames[1:]))
        ws = wb[wb.sheetnames[0]]
        rows_iter = ws.iter_rows(values_only=True)
        headers = [str(h) if h is not None else f"col_{i}" for i, h in enumerate(next(rows_iter))]
        data = []
        for row in rows_iter:
            data.append({h: _cell_text(v) for h, v in zip(headers, row)})
        wb.close()
    else:
        delimiter = "\t" if fmt == "tsv" else ","
        enc = detect_encoding(path)
        with open(path, newline="", encoding=enc) as f:
            # A short row is only missing values (read as ""). A long row's
            # extra fields land under the key None, in no column: the review
            # never showed them and "keep" wrote them out. Refuse the file,
            # naming the line but not the values.
            reader = csv.DictReader(f, delimiter=delimiter, restval="")
            headers = reader.fieldnames or []
            data = []
            for row in reader:
                if None in row:
                    sys.exit(f"{path.name}, line {reader.line_num}: this row has more fields "
                             f"than the header ({len(headers)} columns). Fix the file "
                             "(for example an unquoted comma) and run again.")
                data.append(row)

    meta["rows"] = len(data)
    meta["columns"] = len(headers) if data else 0
    meta["headers"] = headers
    return data, meta


def save_tabular(data: list[dict], path: Path, fmt: str) -> None:
    """Write de-identified data back to CSV/TSV/XLSX."""
    if not data:
        log.warning("No data to write.")
        return
    headers = list(data[0].keys())

    if fmt == "xlsx":
        try:
            import openpyxl
        except ImportError:
            fmt = "csv"
            path = path.with_suffix(".csv")
            log.warning("openpyxl not available; writing CSV instead: %s", path)

    if fmt == "xlsx":
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(headers)
        for row in data:
            ws.append([row.get(h, "") for h in headers])
        wb.save(path)
    else:
        delimiter = "\t" if fmt == "tsv" else ","
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=headers, delimiter=delimiter)
            writer.writeheader()
            writer.writerows(data)


# ================================================================
# Section 3: PHI Scanner
# ================================================================

def _normalize_col(name: str) -> str:
    """Normalize column name for matching: lowercase, strip, collapse whitespace."""
    return re.sub(r"[\s_\-]+", "_", name.strip().lower())


def _col_name_matches(norm_col: str, pattern: str) -> bool:
    """Check if a normalized column name matches a PHI pattern.

    Rules:
    - Short column names (<=10 chars): exact match or pattern equals norm
    - Long column names (>10 chars): only match if pattern IS the full norm
      (prevents 'cell' matching inside 'atypical cell carcinoma')
    - Korean patterns: use substring match only for dedicated Korean PHI words
    """
    # Exact match
    if norm_col == pattern:
        return True
    # Short column name that equals or is contained in pattern
    if len(norm_col) <= 10 and norm_col in pattern:
        return True
    # Short column name: check if pattern matches as a whole word
    if len(norm_col) <= 10 and pattern in norm_col:
        return True
    # Long column name: only match if the normalized name STARTS with the pattern
    # (e.g., "전화번호_집" matches "전화번호", but "bronchial...cell" doesn't match "cell")
    if norm_col.startswith(pattern):
        return True
    return False


def _col_name_mention(col: str, column_names: dict[str, str]) -> str | None:
    """PHI type of a PHI word that appears as a whole word inside a longer
    column name ("legal_patient_name"), or None.

    _col_name_matches deliberately ignores these, so that "cell" in
    "atypical_cell_carcinoma" is not anonymized by default. Ignoring them
    entirely called the column SAFE. They are review items instead.
    """
    padded = f"_{_normalize_col(col)}_"
    for pattern, phi_type in column_names.items():
        if f"_{pattern}_" in padded:
            return phi_type
    return None


def scan_column_names(headers: list[str],
                      column_names: dict[str, str] | None = None) -> dict[str, dict]:
    """Match column names against PHI dictionary.

    Returns {col: {"phi_type": str, "confidence": str, "source": "column_name"}}.
    """
    if column_names is None:
        column_names = UNIVERSAL_COLUMN_NAMES
    results: dict[str, dict] = {}
    for col in headers:
        norm = _normalize_col(col)
        for pattern, phi_type in column_names.items():
            if _col_name_matches(norm, pattern):
                results[col] = {
                    "phi_type": phi_type,
                    "confidence": CONF_HIGH,
                    "source": "column_name",
                }
                break
    return results


def _values_to_scan(values: list[str]) -> list[str]:
    """Return every non-empty value in the column.

    This used to be a random sample of at most 500 values, and that caused
    two defects. First, the same file could classify differently from one
    run to the next. Second, a column where only a few values carry PHI
    (three phone numbers in 2,000 notes) came out SAFE whenever the sample
    missed them, and a SAFE column is passed through un-stripped. A SAFE
    verdict asserts that no value matched, so every value has to be checked.
    """
    return [v for v in values if v and v.strip()]


def scan_column_values(col: str, values: list[str],
                       col_phi_hint: str | None = None,
                       value_patterns: list[tuple[re.Pattern, str]] | None = None,
                       address_re: re.Pattern | None = None,
                       name_re: re.Pattern | None = None,
                       name_min_ratio: float = 0.3,
                       name_columns: list[str] | None = None) -> dict | None:
    """Scan cell values in a column for PHI patterns.

    Returns a detection dict or None.
    """
    if value_patterns is None:
        value_patterns = UNIVERSAL_VALUE_PATTERNS
    if name_columns is None:
        name_columns = [k for k, v in UNIVERSAL_COLUMN_NAMES.items() if v == "name"]

    sample = _values_to_scan(values)
    if not sample:
        return None

    # Count matches per PHI type
    type_counts: dict[str, int] = {}
    for val in sample:
        forms = _value_forms(val)
        for regex, phi_type in value_patterns:
            if any(regex.search(f) for f in forms):
                type_counts[phi_type] = type_counts.get(phi_type, 0) + 1
                break  # one match per value is enough

    # Name heuristic check (only if column name hints at a name)
    if name_re is not None:
        if col_phi_hint == "name" or _normalize_col(col) in name_columns:
            name_count = sum(1 for v in sample if name_re.match(v.strip()))
            if name_count > len(sample) * name_min_ratio:
                type_counts["name"] = name_count

    # Address check. Any match counts: one address among ten notes is
    # still an address, and a column below a prevalence cut-off was passed
    # through. How many rows match only sets the confidence below.
    if address_re is not None:
        addr_count = sum(1 for v in sample if address_re.search(v))
        if addr_count:
            type_counts["address"] = addr_count

    if not type_counts:
        return None

    # Pick the most frequent type
    best_type = max(type_counts, key=lambda k: type_counts[k])
    ratio = type_counts[best_type] / len(sample)
    confidence = CONF_HIGH if ratio > 0.5 else CONF_MEDIUM if ratio > 0.2 else CONF_LOW

    return {
        "phi_type": best_type,
        "confidence": confidence,
        "source": "value_pattern",
        "match_ratio": round(ratio, 3),
        "sample_size": len(sample),
    }


def is_high_cardinality_numeric(values: list[str], threshold: float = 0.9) -> bool:
    """Detect columns that look like MRN/chart numbers:
    high-cardinality pure-numeric values.

    There is no minimum row count: nine chart numbers are as identifying
    as ten, and a small file used to get these columns called SAFE."""
    non_empty = [v.strip() for v in values if v and v.strip()]
    if not non_empty:
        return False
    numeric_count = sum(1 for v in non_empty if v.isdigit() and len(v) >= 5)
    if numeric_count / len(non_empty) < threshold:
        return False
    unique_ratio = len(set(non_empty)) / len(non_empty)
    return unique_ratio > 0.8


def looks_like_free_text(values: list[str]) -> bool:
    """True if any value reads like prose (over 50 characters, or five or
    more words). The scanner finds identifiers that have a shape (phone,
    ID, date, address); it cannot find a name written into a sentence."""
    return any(len(v) > 50 or len(v.split()) >= 5
               for v in values if v and v.strip())


def classify_columns(data: list[dict], headers: list[str],
                      locale: dict | None = None) -> list[dict]:
    """Classify every column as PHI, SAFE, or REVIEW_NEEDED.

    Returns a list of classification dicts (one per column).
    """
    # Build patterns from locale (or use universal defaults)
    if locale is not None:
        col_names, val_patterns, addr_re, name_re, name_ratio, name_cols = \
            build_locale_patterns(locale)
    else:
        col_names = UNIVERSAL_COLUMN_NAMES
        val_patterns = UNIVERSAL_VALUE_PATTERNS
        addr_re = None
        name_re = None
        name_ratio = 0.3
        name_cols = [k for k, v in UNIVERSAL_COLUMN_NAMES.items() if v == "name"]

    # Pass 1: column name matching
    name_hits = scan_column_names(headers, col_names)

    classifications = []
    for col in headers:
        values = [row.get(col, "") for row in data]

        # Already matched by name?
        if col in name_hits:
            entry = {
                "column": col,
                "classification": "PHI",
                **name_hits[col],
            }
            # Refine with value scan
            val_hit = scan_column_values(
                col, values, name_hits[col]["phi_type"],
                val_patterns, addr_re, name_re, name_ratio, name_cols)
            if val_hit:
                entry["value_scan"] = val_hit
            classifications.append(entry)
            continue

        # Pass 2: value pattern scan
        val_hit = scan_column_values(
            col, values, None,
            val_patterns, addr_re, name_re, name_ratio, name_cols)
        if val_hit:
            classifications.append({
                "column": col,
                "classification": "PHI" if val_hit["confidence"] == CONF_HIGH else "REVIEW_NEEDED",
                **val_hit,
            })
            continue

        # Pass 2b: a PHI word inside a longer column name
        mention = _col_name_mention(col, col_names)
        if mention:
            classifications.append({
                "column": col,
                "classification": "REVIEW_NEEDED",
                "phi_type": mention,
                "confidence": CONF_LOW,
                "source": "column_name_partial",
            })
            continue

        # Pass 3: high-cardinality numeric (possible MRN). No values are
        # stored in the report: the report is read by the agent, and the
        # review shows samples in the researcher's terminal instead.
        if is_high_cardinality_numeric(values):
            classifications.append({
                "column": col,
                "classification": "REVIEW_NEEDED",
                "phi_type": "id",
                "confidence": CONF_LOW,
                "source": "high_cardinality_numeric",
            })
            continue

        # Pass 4: free text. A pattern hit would have been caught in Pass 2;
        # what is left is prose the scanner cannot vouch for, because a name
        # inside a sentence has no pattern. Never SAFE: the researcher decides.
        if looks_like_free_text(values):
            classifications.append({
                "column": col,
                "classification": "REVIEW_NEEDED",
                "phi_type": "free_text",
                "confidence": CONF_LOW,
                "source": "free_text",
            })
            continue

        # Default: SAFE
        classifications.append({
            "column": col,
            "classification": "SAFE",
            "phi_type": None,
            "confidence": CONF_HIGH,
            "source": "no_match",
        })

    return classifications


# A review is a decision about the table it was shown. Apply used to check the decisions and
# the column names but not the data, so a value put into a kept column after the review (an
# e-mail address in a numeric column) went into the output. The scan report now carries a
# fingerprint of the table, and review and apply refuse a table that no longer matches it.
# It is salted and slow (PBKDF2) because the report is the file an agent may read: a plain
# SHA-256 of a one-cell table is reversed by hashing every candidate chart number.
FINGERPRINT_ITERATIONS = 200_000


def data_fingerprint(data: list[dict], headers: list[str], salt: bytes | None = None,
                     iterations: int = FINGERPRINT_ITERATIONS) -> str:
    """Salted PBKDF2 fingerprint of the column names and every cell, in order.

    A row with no value in any column holds nothing to review, so adding or dropping one
    (a spreadsheet's trailing blank rows) does not change the fingerprint.
    """
    salt = secrets.token_bytes(16) if salt is None else salt
    h = hashlib.sha256(json.dumps(headers, ensure_ascii=False).encode("utf-8"))
    for row in data:
        cells = [row.get(c, "") for c in headers]
        if not any(str(v).strip() for v in cells):
            continue
        h.update(b"\n" + json.dumps(cells, ensure_ascii=False, default=str).encode("utf-8"))
    digest = hashlib.pbkdf2_hmac("sha256", h.digest(), salt, iterations)
    return f"pbkdf2-sha256${iterations}${salt.hex()}${digest.hex()}"


def fingerprint_problem(report: dict, data: list[dict], headers: list[str]) -> str | None:
    """Why the report does not describe this table, or None when it does."""
    stored = report.get("data_fingerprint")
    if not stored:
        return ("the report records no fingerprint of the data it was made from (it predates "
                "medsci-skills 6.0.1), so nothing shows the data is the data reviewed. "
                "Scan and review again.")
    try:
        algo, iterations, salt_hex, _ = str(stored).split("$")
        n = int(iterations)
        if algo != "pbkdf2-sha256" or not 0 < n <= 10 * FINGERPRINT_ITERATIONS:
            raise ValueError(algo)
        current = data_fingerprint(data, headers, bytes.fromhex(salt_hex), n)
        matches = hmac.compare_digest(current.encode("utf-8"), str(stored).encode("utf-8"))
    except ValueError:  # includes UnicodeEncodeError (a lone surrogate in the stored value)
        return "the report's data fingerprint is malformed. Scan and review again."
    if not matches:
        return ("the input data changed after the scan, so the reviewed decisions do not "
                "describe it. Scan and review again.")
    return None


def build_scan_report(input_path: Path, data: list[dict],
                      meta: dict, classifications: list[dict],
                      locale: dict | None = None) -> dict:
    """Build the full scan report JSON."""
    report = {
        "version": REPORT_VERSION,
        "timestamp": datetime.now().isoformat(),
        "input_file": str(input_path),
        "meta": meta,
        "data_fingerprint": data_fingerprint(data, meta["headers"]),
        "classifications": classifications,
    }
    if locale is not None:
        report["locale"] = {
            "code": locale.get("code", "custom"),
            "name": locale.get("name", "Custom"),
        }
    return report


# ================================================================
# Section 4: Interactive Reviewer
# ================================================================

def _format_classification(c: dict) -> str:
    cls = c["classification"]
    phi = c.get("phi_type", "")
    conf = c.get("confidence", "")
    if cls == "PHI":
        return f"{_red('PHI')} ({phi}, {conf})"
    if cls == "REVIEW_NEEDED":
        return f"{_yellow('REVIEW_NEEDED')} ({phi}, {conf})"
    return _green("SAFE")


def _show_sample_values(col: str, data: list[dict], n: int = 10) -> None:
    """Print up to n unique sample values for a column."""
    values = list(set(row.get(col, "") for row in data if row.get(col, "").strip()))
    sample = values[:n]
    if sample:
        print(f"  Sample values: {', '.join(repr(v) for v in sample)}")
    if len(values) > n:
        print(f"  ... and {len(values) - n} more unique values")


def _ask(prompt: str, choices: str, default: str | None = None) -> str:
    """Read one of the single-letter `choices`. Enter gives `default`; with no
    default the question repeats until it is answered. A column the scanner
    was unsure of used to be kept when the researcher pressed Enter."""
    while True:
        try:
            choice = input(prompt).strip().lower()[:1]
        except EOFError:
            sys.exit("\nReview stopped before every column was answered. Nothing was written.")
        if not choice and default is not None:
            return default
        if choice and choice in choices:
            return choice
        print(f"  Please type one of: {', '.join(choices)}")


def _ask_patient_key(classifications: list[dict]) -> dict:
    """Ask which column identifies the patient, for date shifting.

    Each patient's dates move by that patient's own offset, so intervals
    within a patient are kept and one known date does not reveal everyone
    else's. The tool used to guess the patient from ID-typed columns and,
    finding none, shifted every row by one shared offset.
    """
    cols = [c["column"] for c in classifications]
    print(f"\n{_bold('=== Patient key for date shifting ===')}")
    print("Dates are shifted by a random offset per patient. "
          "Which column identifies the patient?")
    for n, c in enumerate(classifications, 1):
        hint = "  (ID column)" if c.get("phi_type") == "id" else ""
        print(f"  {n:2d}. {c['column']}{hint}")
    print("  row. Every row is a different patient")
    while True:
        try:
            answer = input("> ").strip()
        except EOFError:
            sys.exit("\nReview stopped: date shifting needs a patient key. Nothing was written.")
        if answer.lower() == "row":
            return {"type": "row"}
        if answer.isdigit() and 1 <= int(answer) <= len(cols):
            return {"type": "column", "column": cols[int(answer) - 1]}
        if answer in cols:
            return {"type": "column", "column": answer}
        print(f"  Enter 1-{len(cols)}, a column name, or 'row'.")


def review_scan_report(report: dict, data: list[dict],
                       auto_accept_safe: bool = False) -> dict:
    """Interactive three-pass review.  Mutates and returns the report.

    Sample values are printed to the researcher's terminal only; nothing
    from the data is written into the report.
    """
    classifications = report["classifications"]
    total = len(classifications)

    # ---- Pass 1: Column-level review ----
    print(f"\n{_bold('=== Pass 1: Column Classification Review ===')}")
    print(f"Total columns: {total}\n")

    phi_count = sum(1 for c in classifications if c["classification"] == "PHI")
    review_count = sum(1 for c in classifications if c["classification"] == "REVIEW_NEEDED")
    safe_count = sum(1 for c in classifications if c["classification"] == "SAFE")
    print(f"  {_red(f'PHI: {phi_count}')}  |  "
          f"{_yellow(f'REVIEW_NEEDED: {review_count}')}  |  "
          f"{_green(f'SAFE: {safe_count}')}\n")

    for i, c in enumerate(classifications):
        col = c["column"]
        cls = c["classification"]
        c.pop("sample_values", None)  # older scan reports stored raw values here

        if cls == "SAFE" and auto_accept_safe:
            c["approved_action"] = "keep"
            continue

        print(f"[{i + 1}/{total}] {_bold(col)}: {_format_classification(c)}")
        # SAFE only means no pattern matched, so SAFE columns are shown too.
        _show_sample_values(col, data)

        if cls == "SAFE":
            choice = _ask("  Action [K]eep / (r)eview_needed? ", "kr", default="k")
            if choice == "r":
                c["classification"] = "REVIEW_NEEDED"
                c["approved_action"] = None
            else:
                c["approved_action"] = "keep"
        elif cls == "PHI":
            choice = _ask("  Action [A]nonymize / (k)eep / (r)eview? ", "akr", default="a")
            if choice == "k":
                c["approved_action"] = "keep"
            elif choice == "r":
                c["classification"] = "REVIEW_NEEDED"
                c["approved_action"] = None
            else:
                c["approved_action"] = "anonymize"
        else:  # REVIEW_NEEDED: no default, so Enter cannot keep an identifier
            if c.get("phi_type") == "free_text":
                print("  Anonymize replaces each whole text with [REDACTED]: "
                      "names inside text cannot be found by pattern.")
            choice = _ask("  Action (a)nonymize / (k)eep? ", "ak")
            if choice == "a":
                c["approved_action"] = "anonymize"
                c["classification"] = "PHI"
            else:
                c["approved_action"] = "keep"

    # ---- Pass 2: Re-examine REVIEW_NEEDED items without decisions ----
    undecided = [c for c in classifications if c.get("approved_action") is None]
    if undecided:
        print(f"\n{_bold('=== Pass 2: Undecided Items ===')}")
        for c in undecided:
            col = c["column"]
            print(f"\n  {_bold(col)}: {_format_classification(c)}")
            _show_sample_values(col, data, n=15)
            choice = _ask("  Action (a)nonymize / (k)eep? ", "ak")
            c["approved_action"] = "anonymize" if choice == "a" else "keep"

    # ---- Pass 3: Final summary ----
    print(f"\n{_bold('=== Pass 3: Final Summary ===')}")
    to_anonymize = [c for c in classifications if c.get("approved_action") == "anonymize"]
    to_keep = [c for c in classifications if c.get("approved_action") == "keep"]

    print(f"\n  Anonymize ({len(to_anonymize)}): "
          + ", ".join(c["column"] for c in to_anonymize) if to_anonymize else "  Anonymize: none")
    print(f"  Keep ({len(to_keep)}): "
          + ", ".join(c["column"] for c in to_keep) if to_keep else "  Keep: none")

    print()
    confirm = _ask("Proceed with these actions? [Y]es / (e)dit / (q)uit: ", "yeq", default="y")
    if confirm == "q":
        sys.exit("Aborted by user.")
    if confirm == "e":
        # Allow editing individual items
        while True:
            col_name = input("  Column name to change (or 'done'): ").strip()
            if col_name.lower() == "done":
                break
            match = [c for c in classifications if c["column"] == col_name]
            if not match:
                print(f"  Column '{col_name}' not found.")
                continue
            c = match[0]
            choice = _ask(f"  New action for {col_name} — (a)nonymize / (k)eep: ", "ak")
            c["approved_action"] = "anonymize" if choice == "a" else "keep"

    if any(c.get("approved_action") == "anonymize" and c.get("phi_type") == "date"
           for c in classifications):
        report["patient_key"] = _ask_patient_key(classifications)

    report["reviewed"] = True
    report["review_timestamp"] = datetime.now().isoformat()
    return report


def review_problems(report: dict, data: list[dict], headers: list[str]) -> list[str]:
    """Reasons a report must not be applied; an empty list means it may be.

    Applying used to go ahead, with only a warning, on a report nobody had
    reviewed, and wrote the input out unchanged under a *_deidentified name.
    """
    if not report.get("reviewed"):
        return ["the report has not been reviewed. Run: deidentify.py review <scan_report.json>"]
    changed = fingerprint_problem(report, data, headers)
    if changed:
        return [changed]
    problems = []
    decided = {c["column"]: c.get("approved_action") for c in report["classifications"]}
    unresolved = [col for col, act in decided.items() if act not in ("anonymize", "keep")]
    if unresolved:
        problems.append("no anonymize/keep decision for: " + ", ".join(unresolved)
                        + ". Run review again.")
    unscanned = [h for h in headers if h not in decided]
    if unscanned:
        problems.append("columns missing from the report (the file changed after the scan): "
                        + ", ".join(unscanned) + ". Scan and review again.")
    date_cols = [c["column"] for c in report["classifications"]
                 if c.get("approved_action") == "anonymize" and c.get("phi_type") == "date"]
    if date_cols:
        key = report.get("patient_key") or {}
        if key.get("type") == "column" and key.get("column") in headers:
            k = key["column"]
            blank = sum(1 for row in data if not row.get(k, "").strip()
                        and any(row.get(dc, "").strip() for dc in date_cols))
            if blank:
                problems.append(f"{blank} rows with a date to shift have no value in the "
                                f"patient key column '{k}'. Fill it, or run review again "
                                "and choose another key (or 'row').")
        elif key.get("type") != "row":
            problems.append("dates are marked for shifting but no patient key was chosen. "
                            "Run review again.")
    return problems


# ================================================================
# Section 5: Anonymizers
# ================================================================

class PseudonymGenerator:
    """Maps original values to consistent pseudonyms (P001, P002, ...)."""

    def __init__(self, prefix: str = "P"):
        self._map: dict[str, str] = {}
        self._counter = 0
        self._prefix = prefix

    def get(self, original: str) -> str:
        if original not in self._map:
            self._counter += 1
            self._map[original] = f"{self._prefix}{self._counter:04d}"
        return self._map[original]

    @property
    def mapping(self) -> dict[str, str]:
        return dict(self._map)


class DateShifter:
    """Shifts dates by a consistent per-entity offset.

    The same entity (identified by entity_id) always gets the same offset,
    preserving relative time intervals between events for the same entity.
    """

    def __init__(self, seed: int | None = None, max_days: int = 365):
        # Each offset is drawn from the operating system's CSPRNG. Offsets
        # used to come from random.Random(seed) with a seed drawn from
        # 1..999999, in row order: anyone who knew two or three patients'
        # true dates could try every seed and recover every other patient's
        # original dates. The offsets are stored in mapping.json, so no seed
        # is needed to reproduce a run. An explicit seed is for tests only.
        self._rng = (random.Random(seed) if seed is not None
                     else secrets.SystemRandom())
        self._max_days = max_days
        self._offsets: dict[str, int] = {}
        self.seed = seed

    def _get_offset(self, entity_id: str) -> int:
        # Never 0: a zero offset (one patient in 731 under randint(-365, 365))
        # wrote the original date to the output and the audit log.
        if entity_id not in self._offsets:
            days = self._rng.randint(1, self._max_days)
            self._offsets[entity_id] = days if self._rng.random() < 0.5 else -days
        return self._offsets[entity_id]

    def shift(self, date_str: str, entity_id: str) -> str:
        """Attempt to parse, shift, and re-format a date string."""
        offset = self._get_offset(entity_id)
        delta = timedelta(days=offset)

        # Try common formats
        for fmt_in, fmt_out in [
            ("%Y-%m-%d", "%Y-%m-%d"),
            ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S"),
            ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S.%f"),
            ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M"),
            ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S"),
            ("%Y.%m.%d", "%Y.%m.%d"),
            ("%Y/%m/%d", "%Y/%m/%d"),
            ("%Y%m%d", "%Y%m%d"),
        ]:
            try:
                dt = datetime.strptime(date_str.strip(), fmt_in)
                return (dt + delta).strftime(fmt_out)
            except ValueError:
                continue

        # Korean format
        m = re.match(r"(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일", date_str)
        if m:
            try:
                dt = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
                shifted = dt + delta
                return f"{shifted.year}년 {shifted.month}월 {shifted.day}일"
            except ValueError:
                pass

        # Cannot parse — return suppressed
        return "[DATE_SHIFTED]"

    @property
    def offsets(self) -> dict[str, int]:
        return dict(self._offsets)


class IDReplacer:
    """Replaces identifiers with sequential IDs (ID001, ID002, ...)."""

    def __init__(self, prefix: str = "ID"):
        self._map: dict[str, str] = {}
        self._counter = 0
        self._prefix = prefix

    def get(self, original: str) -> str:
        if original not in self._map:
            self._counter += 1
            self._map[original] = f"{self._prefix}{self._counter:04d}"
        return self._map[original]

    @property
    def mapping(self) -> dict[str, str]:
        return dict(self._map)


def _suppress(val: str) -> str:
    return "[REDACTED]"


def _sha256(val: str) -> str:
    return hashlib.sha256(val.encode("utf-8")).hexdigest()


def _keyed_hash(key: bytes, val: str) -> str:
    """HMAC-SHA256 of a value under a per-run key.

    The audit log used a plain SHA-256, and a plain hash of a date or a chart
    number is reversed by hashing every candidate (every date of a century
    takes under a second). The key is stored only in mapping.json, which is
    restricted like the original values it maps.
    """
    return hmac.new(key, val.encode("utf-8"), hashlib.sha256).hexdigest()


def apply_anonymization(data: list[dict], report: dict,
                        date_shift_seed: int | None = None) -> tuple[list[dict], dict, list[dict]]:
    """Apply approved anonymization actions.

    Returns (de-identified data, mapping dict, audit entries).
    """
    classifications = report["classifications"]
    to_anonymize = {c["column"]: c for c in classifications
                    if c.get("approved_action") == "anonymize"}

    if not to_anonymize:
        log.info("No columns marked for anonymization.")
        return data, {}, []

    # The patient key the researcher chose in review (see review_problems).
    # Without one, each row gets its own offset: never one shared offset.
    key = report.get("patient_key") or {}
    key_col = key.get("column") if key.get("type") == "column" else None

    # Initialize anonymizers
    name_gen = PseudonymGenerator(prefix="P")
    id_gen = IDReplacer(prefix="ID")
    # No seed by default: offsets come from the OS CSPRNG (see DateShifter).
    date_shifter = DateShifter(seed=date_shift_seed)
    audit_key = secrets.token_bytes(32)

    meta: dict = {
        "date_shift_rng": ("seeded (test only)" if date_shift_seed is not None
                           else "secrets.SystemRandom"),
        "audit_hash_key": audit_key.hex(),
        "timestamp": datetime.now().isoformat(),
        "version": REPORT_VERSION,
    }
    if date_shift_seed is not None:
        meta["date_shift_seed"] = date_shift_seed
    mapping: dict[str, dict] = {"_meta": meta}
    audit: list[dict] = []

    # Process each row
    clean_data = []
    for row_idx, row in enumerate(data):
        new_row = dict(row)

        # Determine entity ID for this row (for date shifting)
        entity_id = (row.get(key_col, "").strip() if key_col else "") or f"row {row_idx + 1}"

        for col, spec in to_anonymize.items():
            original = row.get(col, "")
            if not original or not original.strip():
                continue

            phi_type = spec.get("phi_type", "unknown")
            original_stripped = original.strip()

            if phi_type == "name":
                replacement = name_gen.get(original_stripped)
            elif phi_type == "id":
                replacement = id_gen.get(original_stripped)
            elif phi_type == "date":
                replacement = date_shifter.shift(original_stripped, entity_id)
            elif phi_type in ("phone", "rrn", "email", "insurance"):
                replacement = _suppress(original_stripped)
            elif phi_type == "address":
                replacement = _suppress(original_stripped)
            elif phi_type == "free_text":
                # A name inside prose has no pattern, so redacting only the
                # patterns would leave it in. The whole text is removed.
                replacement = _suppress(original_stripped)
            else:
                replacement = _suppress(original_stripped)

            new_row[col] = replacement

            audit.append({
                "row": row_idx,
                "column": col,
                "phi_type": phi_type,
                "action": "anonymize",
                "before_hash": _keyed_hash(audit_key, original_stripped),
                "after_value": replacement,
            })

        clean_data.append(new_row)

    # Build mapping
    mapping["names"] = name_gen.mapping
    mapping["ids"] = id_gen.mapping
    mapping["date_offsets"] = date_shifter.offsets

    return clean_data, mapping, audit


# ================================================================
# Section 6: Output
# ================================================================

def write_deidentified_file(data: list[dict], input_path: Path,
                            output_dir: Path) -> Path:
    """Write de-identified data to output_dir/{stem}_deidentified.{ext}."""
    fmt = detect_format(input_path)
    out_name = f"{input_path.stem}_deidentified{input_path.suffix}"
    out_path = output_dir / out_name
    save_tabular(data, out_path, fmt)
    log.info("De-identified data written to: %s", out_path)
    return out_path


def write_mapping(mapping: dict, path: Path, hash_mode: bool = False) -> Path:
    """Write mapping file.  In hash mode, original values are SHA-256 hashed.

    The hashes are not keyed, so a date or a numeric ID can be recovered from
    them by trying every candidate: mapping.json stays restricted either way.
    """
    if hash_mode:
        hashed = {"_meta": mapping.get("_meta", {})}
        for section in ("names", "ids"):
            if section in mapping:
                hashed[section] = {_sha256(k): v for k, v in mapping[section].items()}
        if "date_offsets" in mapping:
            hashed["date_offsets"] = {_sha256(k): v for k, v in mapping["date_offsets"].items()}
        out_data = hashed
    else:
        out_data = mapping

    path.write_text(json.dumps(out_data, ensure_ascii=False, indent=2), encoding="utf-8")

    # Set restrictive permissions (owner-only read/write)
    try:
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)  # 0600
    except OSError:
        log.warning("Could not set restrictive permissions on mapping file: %s", path)

    log.info("Mapping file written to: %s (permissions: 0600)", path)
    return path


def write_audit_log(audit: list[dict], path: Path) -> Path:
    """Write audit log CSV.  before_hash is an HMAC-SHA256 of the original
    value under the per-run key kept in mapping.json (see _keyed_hash)."""
    if not audit:
        log.info("No changes made; audit log is empty.")
        return path

    fieldnames = ["row", "column", "phi_type", "action", "before_hash", "after_value"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(audit)

    log.info("Audit log written to: %s (%d entries)", path, len(audit))
    return path


# ================================================================
# Section 7: Main + CLI
# ================================================================

def _resolve_locale(args: argparse.Namespace) -> dict | None:
    """Resolve locale from CLI args or interactive selection."""
    if getattr(args, "locale_file", None):
        locale = load_locale_file(args.locale_file)
        log.info("Using custom locale: %s", locale.get("name", "Custom"))
        return locale
    if getattr(args, "locale", None):
        locale = load_locale(args.locale)
        log.info("Using locale: %s (%s)", locale["name"], locale["code"])
        return locale
    # Interactive selection
    return select_locale_interactive()


def cmd_scan(args: argparse.Namespace) -> None:
    """Scan command: profile and classify columns."""
    input_path = Path(args.input_file)
    if not input_path.exists():
        sys.exit(f"File not found: {input_path}")

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    locale = _resolve_locale(args)

    log.info("Loading %s ...", input_path)
    data, meta = load_tabular(input_path)
    log.info("Loaded %d rows, %d columns", meta["rows"], meta["columns"])

    log.info("Scanning for PHI ...")
    classifications = classify_columns(data, meta["headers"], locale)

    report = build_scan_report(input_path, data, meta, classifications, locale)
    report_path = output_dir / "scan_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    # Print summary
    phi = sum(1 for c in classifications if c["classification"] == "PHI")
    review = sum(1 for c in classifications if c["classification"] == "REVIEW_NEEDED")
    safe = sum(1 for c in classifications if c["classification"] == "SAFE")
    print(f"\n{_bold('Scan Results')}:")
    print(f"  {_red(f'PHI: {phi}')}  |  {_yellow(f'REVIEW_NEEDED: {review}')}  |  {_green(f'SAFE: {safe}')}")
    print(f"\nReport saved: {report_path}")
    print(f"Next step: python deidentify.py review {report_path}")


def cmd_review(args: argparse.Namespace) -> None:
    """Review command: interactive terminal review of scan report."""
    report_path = Path(args.report_file)
    if not report_path.exists():
        sys.exit(f"Report not found: {report_path}")

    report = json.loads(report_path.read_text(encoding="utf-8"))
    if report.get("version", 0) != REPORT_VERSION:
        log.warning("Report version mismatch (expected %d, got %d)",
                    REPORT_VERSION, report.get("version", 0))

    # Reload original data for sample display
    input_path = Path(report["input_file"])
    if not input_path.exists():
        sys.exit(f"Original file not found: {input_path}")
    data, meta = load_tabular(input_path)
    changed = fingerprint_problem(report, data, meta["headers"])
    if changed:
        sys.exit(f"Not reviewed: {changed}")

    reviewed = review_scan_report(report, data,
                                  auto_accept_safe=getattr(args, "auto_accept_safe", False))

    out_path = report_path.parent / "reviewed_report.json"
    out_path.write_text(json.dumps(reviewed, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nReviewed report saved: {out_path}")
    print(f"Next step: python deidentify.py apply {out_path}")


def _exit_on_review_problems(report: dict, data: list[dict], headers: list[str]) -> None:
    problems = review_problems(report, data, headers)
    if problems:
        sys.exit("Not applied; no de-identified file was written:\n  - " + "\n  - ".join(problems))


def cmd_apply(args: argparse.Namespace) -> None:
    """Apply command: anonymize based on reviewed report."""
    report_path = Path(args.report_file)
    if not report_path.exists():
        sys.exit(f"Report not found: {report_path}")

    report = json.loads(report_path.read_text(encoding="utf-8"))
    if not report.get("reviewed"):
        sys.exit("Not applied; no de-identified file was written: the report has not been reviewed.\n"
                 f"Run: deidentify.py review {report_path}")

    input_path = Path(report["input_file"])
    if not input_path.exists():
        sys.exit(f"Original file not found: {input_path}")

    output_dir = report_path.parent
    data, meta = load_tabular(input_path)
    _exit_on_review_problems(report, data, meta["headers"])

    log.info("Applying anonymization ...")
    clean_data, mapping, audit = apply_anonymization(data, report)

    # Write outputs
    deid_path = write_deidentified_file(clean_data, input_path, output_dir)
    mapping_path = write_mapping(mapping, output_dir / "mapping.json",
                                 hash_mode=getattr(args, "hash_mapping", False))
    audit_path = write_audit_log(audit, output_dir / "audit_log.csv")

    # Warn if mapping is in same dir as de-identified data
    if mapping_path.parent == deid_path.parent:
        print(f"\n{_yellow('WARNING')}: mapping.json is in the same directory as the "
              "de-identified data. For security, store mapping.json separately.")

    # Summary
    changes = len(audit)
    cols_changed = len(set(a["column"] for a in audit))
    print(f"\n{_bold('De-identification Complete')}:")
    print(f"  Changes: {changes} cells across {cols_changed} columns")
    print(f"  Output:  {deid_path}")
    print(f"  Mapping: {mapping_path}")
    print(f"  Audit:   {audit_path}")


def cmd_full(args: argparse.Namespace) -> None:
    """Full pipeline: scan -> review -> apply in one go."""
    input_path = Path(args.input_file)
    if not input_path.exists():
        sys.exit(f"File not found: {input_path}")

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    locale = _resolve_locale(args)

    # Scan
    log.info("Loading %s ...", input_path)
    data, meta = load_tabular(input_path)
    log.info("Loaded %d rows, %d columns", meta["rows"], meta["columns"])

    log.info("Scanning for PHI ...")
    classifications = classify_columns(data, meta["headers"], locale)
    report = build_scan_report(input_path, data, meta, classifications, locale)

    # Quick summary before review
    phi = sum(1 for c in classifications if c["classification"] == "PHI")
    review_n = sum(1 for c in classifications if c["classification"] == "REVIEW_NEEDED")
    safe = sum(1 for c in classifications if c["classification"] == "SAFE")
    print(f"\n{_bold('Scan Results')}:")
    print(f"  {_red(f'PHI: {phi}')}  |  {_yellow(f'REVIEW_NEEDED: {review_n}')}  |  {_green(f'SAFE: {safe}')}")

    if phi == 0 and review_n == 0:
        print(f"\n{_green('No identifier patterns matched.')} That is not proof the data "
              "holds none: the review shows each column's values.")
        confirm = input("Proceed anyway? (y/n) ").strip().lower()
        if confirm != "y":
            return

    # Review
    reviewed = review_scan_report(report, data,
                                  auto_accept_safe=args.auto_accept_safe)

    # Save report
    report_path = output_dir / "reviewed_report.json"
    report_path.write_text(json.dumps(reviewed, ensure_ascii=False, indent=2), encoding="utf-8")
    _exit_on_review_problems(reviewed, data, meta["headers"])

    # Apply
    log.info("Applying anonymization ...")
    clean_data, mapping, audit = apply_anonymization(data, reviewed)

    # Write outputs
    deid_path = write_deidentified_file(clean_data, input_path, output_dir)
    mapping_path = write_mapping(mapping, output_dir / "mapping.json",
                                 hash_mode=args.hash_mapping)
    audit_path = write_audit_log(audit, output_dir / "audit_log.csv")

    if mapping_path.parent == deid_path.parent:
        print(f"\n{_yellow('WARNING')}: mapping.json is in the same directory as the "
              "de-identified data. For security, store mapping.json separately.")

    changes = len(audit)
    cols_changed = len(set(a["column"] for a in audit))
    print(f"\n{_bold('De-identification Complete')}:")
    print(f"  Changes: {changes} cells across {cols_changed} columns")
    print(f"  Output:  {deid_path}")
    print(f"  Mapping: {mapping_path}")
    print(f"  Audit:   {audit_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="deidentify",
        description="Clinical research data de-identification (LLM-free).",
    )
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Enable verbose logging")
    sub = parser.add_subparsers(dest="command", required=True)

    # Locale options (shared by scan and full)
    def _add_locale_args(p: argparse.ArgumentParser) -> None:
        g = p.add_mutually_exclusive_group()
        g.add_argument("--locale", type=str, metavar="CODE",
                       help="Country code (kr, us, jp, cn, de, uk, fr, ca, au, in, it, es). "
                            "If omitted, interactive selection is shown.")
        g.add_argument("--locale-file", type=str, metavar="PATH",
                       help="Path to a custom locale JSON file")

    # scan
    p_scan = sub.add_parser("scan", help="Scan a file for PHI")
    p_scan.add_argument("input_file", help="Path to CSV/TSV/XLSX file")
    p_scan.add_argument("-o", "--output-dir", default=".", help="Output directory (default: .)")
    _add_locale_args(p_scan)

    # review
    p_review = sub.add_parser("review", help="Interactive review of scan report")
    p_review.add_argument("report_file", help="Path to scan_report.json")
    p_review.add_argument("--auto-accept-safe", action="store_true",
                          help="Keep SAFE columns without showing them (SAFE means no pattern matched)")

    # apply
    p_apply = sub.add_parser("apply", help="Apply anonymization from reviewed report")
    p_apply.add_argument("report_file", help="Path to reviewed_report.json")
    p_apply.add_argument("--hash-mapping", action="store_true",
                         help="Hash original values in mapping file (unkeyed: dates and IDs stay recoverable)")

    # full
    p_full = sub.add_parser("full", help="Full pipeline: scan + review + apply")
    p_full.add_argument("input_file", help="Path to CSV/TSV/XLSX file")
    p_full.add_argument("-o", "--output-dir", default=".", help="Output directory (default: .)")
    _add_locale_args(p_full)
    p_full.add_argument("--auto-accept-safe", action="store_true",
                        help="Keep SAFE columns without showing them (SAFE means no pattern matched)")
    p_full.add_argument("--hash-mapping", action="store_true",
                        help="Hash original values in mapping file (unkeyed: dates and IDs stay recoverable)")

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    if args.command == "scan":
        cmd_scan(args)
    elif args.command == "review":
        cmd_review(args)
    elif args.command == "apply":
        cmd_apply(args)
    elif args.command == "full":
        cmd_full(args)


if __name__ == "__main__":
    main()
