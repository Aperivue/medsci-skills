#!/usr/bin/env python3
"""
validate_schema.py — JSON-LD validator for academic-aio schema markup files.

Validates:
- JSON-LD syntactic validity
- @context = "https://schema.org"
- @type matches one of the supported types
- Required fields present (per schema.org minimal recommendations + medsci-skills policy)
- Identifier format (DOI, ORCID incl. its ISO 7064 MOD 11-2 check digit), whether
  the identifier is a string, a PropertyValue object, or a list of them
- No unfilled template placeholder (<...>, 10.xxxx/yyyy, 0000-0000-0000-0000,
  YYYY-MM-DD): a file meant for deploy that still carries one FAILs with a
  "PLACEHOLDER:" line. Pass --template to validate an unfilled template.

Usage:
    python validate_schema.py path/to/file.jsonld [path/to/another.jsonld ...]
    python validate_schema.py --template references/schema_markup_templates/*.jsonld
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REQUIRED_BY_TYPE: dict[str, list[str]] = {
    "ScholarlyArticle": ["headline", "datePublished", "author", "identifier", "url"],
    "SoftwareSourceCode": ["name", "codeRepository", "license", "datePublished", "author"],
    "Dataset": ["name", "description", "license", "creator", "datePublished"],
    "Person": ["name", "identifier"],
}

# A paired "<...>" and "#" occur in legacy SICI-style DOI suffixes.
DOI_RE = re.compile(r"^10\.\d{4,9}/(?:[-._;()/:#A-Za-z0-9]|<[^<>\s]*>)+$")
ORCID_RE = re.compile(r"^https://orcid\.org/\d{4}-\d{4}-\d{4}-\d{3}[\dX]$")
ORCID_HTTP_RE = re.compile(r"^https?://orcid\.org/\d{4}-\d{4}-\d{4}-\d{3}[\dX]$")
ORCID_BARE_RE = re.compile(r"^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$")
DOI_PREFIX_RE = re.compile(r"^(?:doi:\s*|https?://(?:dx\.)?doi\.org/)", re.IGNORECASE)

# Template placeholders, as shipped in references/schema_markup_templates/:
#   a value that is wholly "<...>"         ("<First Last>", "<paper title verbatim>")
#   "<word...>" inside an identifier/URL   ("https://github.com/<org>/<repo>")
#   an all-x DOI registrant ("10.xxxx/")   and the all-zero ORCID
#   "YYYY" in a date field                 ("YYYY-MM-DD")
WHOLE_PLACEHOLDER_RE = re.compile(r"^\s*<[^<>]+>\s*$")
INNER_PLACEHOLDER_RE = re.compile(r"<[A-Za-z][^<>]*>|10\.x{2,}/|0000-0000-0000-0000", re.IGNORECASE)
IDENT_KEYS = {"identifier", "sameAs", "url", "@id", "codeRepository", "contentUrl"}
DATE_KEYS = {"datePublished", "dateCreated", "dateModified"}


def _is_placeholder(value: str, key: str | None = None, in_ident: bool = False) -> bool:
    """True for a template placeholder string (see the token list above)."""
    if not isinstance(value, str):
        return False
    if WHOLE_PLACEHOLDER_RE.match(value):
        return True
    if (in_ident or key in IDENT_KEYS) and INNER_PLACEHOLDER_RE.search(value):
        return True
    if key in DATE_KEYS and "YYYY" in value.upper():
        return True
    return False


def find_placeholders(node, path: str = "$", key: str | None = None, in_ident: bool = False) -> list[str]:
    """Paths of every unfilled template placeholder in the document."""
    hits: list[str] = []
    if isinstance(node, dict):
        for k, v in node.items():
            hits += find_placeholders(v, f"{path}.{k}", k, in_ident or k in IDENT_KEYS)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            hits += find_placeholders(v, f"{path}[{i}]", key, in_ident)
    elif _is_placeholder(node, key, in_ident):
        hits.append(f"{path}={node!r}")
    return hits


def orcid_checksum_ok(orcid: str) -> bool:
    """ISO 7064 MOD 11-2 check character of a 16-character ORCID iD."""
    digits = orcid.rsplit("/", 1)[-1].replace("-", "").upper()
    if len(digits) != 16 or not digits[:-1].isdigit():
        return False
    total = 0
    for ch in digits[:-1]:
        total = (total + int(ch)) * 2
    result = (12 - total % 11) % 11
    return digits[-1] == ("X" if result == 10 else str(result))


def _orcid_errors(value: str, where: str, allow_bare: bool) -> list[str]:
    # allow_bare (a PropertyValue "value"): a bare iD, or an http(s) ORCID URL.
    shape_ok = bool(ORCID_RE.match(value)) or (
        allow_bare and bool(ORCID_BARE_RE.match(value) or ORCID_HTTP_RE.match(value)))
    if not shape_ok:
        want = "an ORCID URL or iD" if allow_bare else "an ORCID URL"
        return [f"{where} should be {want} (got {value!r})"]
    if not orcid_checksum_ok(value):
        return [f"{where} ORCID check digit is invalid (ISO 7064 MOD 11-2): {value!r}"]
    return []


def _identifier_errors(ident, typ: str, template: bool) -> list[str]:
    """Format checks for the top-level identifier in each JSON-LD shape:
    a string, a single PropertyValue object, or a list of them."""
    errors: list[str] = []
    entries = ident if isinstance(ident, list) else [ident]
    from_list = isinstance(ident, list)
    for entry in entries:
        if isinstance(entry, str):
            if template and _is_placeholder(entry, "identifier", True):
                continue
            if typ == "Person":
                # A single string must be an ORCID URL (as on main). In a list, other
                # author identifiers (Scopus, ResearcherID, ...) are allowed; only an
                # entry that looks like an ORCID is checked.
                looks_orcid = "orcid.org" in entry.lower() or bool(ORCID_BARE_RE.match(entry.strip()))
                if (not from_list or looks_orcid) and not _is_placeholder(entry, "identifier", True):
                    errors += _orcid_errors(entry, "Person identifier", allow_bare=False)
            elif DOI_PREFIX_RE.match(entry) or entry.startswith("10."):
                bare = DOI_PREFIX_RE.sub("", entry).strip()
                if not _is_placeholder(entry, "identifier", True) and not DOI_RE.match(bare):
                    errors.append(f"DOI does not match canonical format: {entry!r}")
        elif isinstance(entry, dict):
            pid = str(entry.get("propertyID", "")).strip().lower()
            value = entry.get("value", "")
            if not isinstance(value, str) or not value:
                continue
            if _is_placeholder(value, "identifier", True):
                continue  # reported (or, under --template, allowed) as a placeholder
            if pid == "doi":
                bare = DOI_PREFIX_RE.sub("", value).strip()
                if not DOI_RE.match(bare):
                    errors.append(f"DOI does not match canonical format: {value!r}")
            elif pid == "orcid":
                errors += _orcid_errors(value, "ORCID identifier", allow_bare=True)
    return errors


def validate(path: Path, template: bool = False) -> list[str]:
    errors: list[str] = []
    try:
        data = json.loads(path.read_text())
    except FileNotFoundError:
        return [f"File not found: {path}"]
    except json.JSONDecodeError as exc:
        return [f"Invalid JSON: {exc}"]

    ctx = data.get("@context")
    if ctx != "https://schema.org":
        errors.append(f'@context must be "https://schema.org" (got {ctx!r})')

    typ = data.get("@type")
    if typ not in REQUIRED_BY_TYPE:
        errors.append(
            f"@type {typ!r} not recognized "
            f"(expected one of {sorted(REQUIRED_BY_TYPE)})"
        )
        return errors

    for field in REQUIRED_BY_TYPE[typ]:
        if field not in data or data[field] in (None, "", []):
            errors.append(f"Missing required field: {field}")

    if not template:
        hits = find_placeholders(data)
        for hit in hits:
            errors.append(f"PLACEHOLDER: unfilled template value {hit}")
        if hits:
            errors.append(
                "PLACEHOLDER: fill each value or remove the field "
                "(pass --template to validate an unfilled template)"
            )

    errors += _identifier_errors(data.get("identifier"), typ, template)

    authors = data.get("author") or data.get("creator") or []
    if isinstance(authors, list):
        for i, a in enumerate(authors):
            if isinstance(a, dict) and not a.get("name"):
                errors.append(f"author[{i}] missing 'name'")

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate academic-aio Schema.org JSON-LD markup files."
    )
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument(
        "--template",
        action="store_true",
        help="Validate an unfilled template: placeholder values (<...>, 10.xxxx/yyyy, "
             "0000-0000-0000-0000, YYYY-MM-DD) are allowed instead of failing.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 on any error (default behaviour; flag retained for clarity).",
    )
    args = parser.parse_args(argv)

    overall_ok = True
    for path in args.files:
        errors = validate(path, template=args.template)
        if errors:
            overall_ok = False
            print(f"FAIL  {path}")
            for e in errors:
                print(f"  - {e}")
        else:
            print(f"PASS  {path}")
    return 0 if overall_ok else 1


if __name__ == "__main__":
    sys.exit(main())
