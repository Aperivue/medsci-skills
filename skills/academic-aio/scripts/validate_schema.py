#!/usr/bin/env python3
"""
validate_schema.py — JSON-LD validator for academic-aio schema markup files.

Validates:
- JSON-LD syntactic validity
- @context = "https://schema.org"
- @type matches one of the supported types
- Required fields present (per schema.org minimal recommendations + medsci-skills policy)
- Identifier format (DOI, ORCID)

Usage:
    python validate_schema.py path/to/file.jsonld [path/to/another.jsonld ...]
    python validate_schema.py --strict references/schema_markup_templates/*.jsonld
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

DOI_RE = re.compile(r"^10\.\d{4,9}/[-._;()/:A-Za-z0-9]+$")
ORCID_RE = re.compile(r"^https://orcid\.org/\d{4}-\d{4}-\d{4}-\d{3}[\dX]$")

PLACEHOLDER_TOKENS = ("<", "xxxx", "yyyy", "0000-0000-0000-0000")


def _is_placeholder(value: str) -> bool:
    """Return True for template placeholder strings that should skip strict checks."""
    if not isinstance(value, str):
        return False
    lowered = value.lower()
    return any(tok in lowered for tok in PLACEHOLDER_TOKENS)


def validate(path: Path) -> list[str]:
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

    ident = data.get("identifier")
    if isinstance(ident, list):
        for entry in ident:
            if isinstance(entry, dict) and entry.get("propertyID") == "DOI":
                value = entry.get("value", "")
                if value and not _is_placeholder(value) and not DOI_RE.match(value):
                    errors.append(f"DOI does not match canonical format: {value!r}")

    if typ == "Person" and isinstance(ident, str):
        if not _is_placeholder(ident) and not ORCID_RE.match(ident):
            errors.append(f"Person identifier should be an ORCID URL (got {ident!r})")

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
        "--strict",
        action="store_true",
        help="Exit 1 on any error (default behaviour; flag retained for clarity).",
    )
    args = parser.parse_args(argv)

    overall_ok = True
    for path in args.files:
        errors = validate(path)
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
