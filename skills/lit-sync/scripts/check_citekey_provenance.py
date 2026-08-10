#!/usr/bin/env python3
"""Check that every literature note's citekey exists in the reference library.

A literature note filename and its ``citekey:`` field assert that an entry with that
key exists in Zotero. When the key was composed rather than read, the note still looks
correct while ``[@key]`` resolves to nothing, ``[[key]]`` points at no file, and the
Zotero Integration plugin writes a second note under the real key. This reports the
keys that exist nowhere, and — where the note carries a DOI the library also has —
the real key it should have carried.

Verdicts
    OK           citekey is present in the library
    INVENTED     citekey absent, but the note's DOI resolves to a real key (fixable here)
    UNRESOLVED   neither citekey nor DOI is in the library (the paper was never added)
    NO_CITEKEY   note has no citekey (recoverable; not a violation)
    FILENAME     citekey is real but the filename disagrees with it

Exit status is 0 unless --strict is given, matching the repo's gate convention.

Usage
    check_citekey_provenance.py --vault ~/Vault/Literature --bib refs.bib
    check_citekey_provenance.py --vault ~/Vault --live --json audit.json --strict
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

BBT_JSONRPC = "http://127.0.0.1:23119/better-bibtex/json-rpc"

FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---", re.S)
BIB_ENTRY_RE = re.compile(r"@\w+\{([^,]+),(.*?)(?=\n@|\Z)", re.S)
BIB_DOI_RE = re.compile(r"\bdoi\s*=\s*[{\"]([^}\"]+)", re.I)


def field(frontmatter: str, name: str) -> str:
    m = re.search(rf'^{name}:\s*"?([^"\n]*)"?\s*$', frontmatter, re.M)
    return m.group(1).strip() if m else ""


def load_bib(paths: list[Path]) -> tuple[set[str], dict[str, str]]:
    """Return (citekeys, doi -> citekey) across every .bib given."""
    keys: set[str] = set()
    doi_to_key: dict[str, str] = {}
    for p in paths:
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError as exc:
            print(f"warning: cannot read {p}: {exc}", file=sys.stderr)
            continue
        for key, body in BIB_ENTRY_RE.findall(text):
            key = key.strip()
            keys.add(key)
            doi = BIB_DOI_RE.search(body)
            if doi:
                doi_to_key.setdefault(doi.group(1).strip().lower(), key)
    return keys, doi_to_key


def load_live() -> tuple[set[str], dict[str, str]]:
    """Ask the running Better BibTeX for the whole library.

    Falls back to an empty library (with a warning) when Zotero is not up, so the
    check degrades to whatever .bib files were supplied instead of dying.
    """
    url = "http://127.0.0.1:23119/better-bibtex/export/library?/1/library.bibtex"
    try:
        with urllib.request.urlopen(url, timeout=120) as resp:
            text = resp.read().decode("utf-8", errors="ignore")
    except (urllib.error.URLError, OSError) as exc:
        print(
            f"warning: Better BibTeX did not answer ({exc}); "
            "open Zotero for a live check",
            file=sys.stderr,
        )
        return set(), {}
    keys: set[str] = set()
    doi_to_key: dict[str, str] = {}
    for key, body in BIB_ENTRY_RE.findall(text):
        key = key.strip()
        keys.add(key)
        doi = BIB_DOI_RE.search(body)
        if doi:
            doi_to_key.setdefault(doi.group(1).strip().lower(), key)
    return keys, doi_to_key


def iter_notes(root: Path):
    for path in sorted(root.rglob("*.md")):
        if any(part.startswith(".") for part in path.parts):
            continue
        try:
            head = path.read_text(encoding="utf-8", errors="ignore")[:4000]
        except OSError:
            continue
        m = FRONTMATTER_RE.match(head)
        if not m:
            continue
        fm = m.group(1)
        if field(fm, "notetype") != "literature":
            continue
        yield path, fm


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--vault", required=True, type=Path,
                    help="vault root or the literature folder inside it")
    ap.add_argument("--bib", type=Path, nargs="*", default=[],
                    help="one or more .bib snapshots to check against")
    ap.add_argument("--live", action="store_true",
                    help="also query the running Better BibTeX for the full library")
    ap.add_argument("--json", type=Path, help="write the full audit here")
    ap.add_argument("--strict", action="store_true",
                    help="exit 1 when any INVENTED note is found")
    args = ap.parse_args()

    if not args.vault.exists():
        print(f"error: vault not found: {args.vault}", file=sys.stderr)
        return 2
    if not args.bib and not args.live:
        print("error: give --bib and/or --live; there is nothing to check against",
              file=sys.stderr)
        return 2

    keys, doi_to_key = load_bib(list(args.bib))
    if args.live:
        live_keys, live_dois = load_live()
        keys |= live_keys
        for doi, key in live_dois.items():
            doi_to_key.setdefault(doi, key)

    if not keys:
        print("error: reference library is empty — every note would be reported as "
              "unresolved, which says nothing. Check the .bib path or open Zotero.",
              file=sys.stderr)
        return 2

    rows = []
    counts = {"OK": 0, "INVENTED": 0, "UNRESOLVED": 0, "NO_CITEKEY": 0, "FILENAME": 0}
    for path, fm in iter_notes(args.vault):
        citekey = field(fm, "citekey")
        doi = field(fm, "doi").lower()
        suggestion = doi_to_key.get(doi, "") if doi else ""

        if not citekey:
            verdict = "NO_CITEKEY"
        elif citekey in keys:
            verdict = "OK" if path.stem == citekey else "FILENAME"
            suggestion = citekey if verdict == "FILENAME" else ""
        elif suggestion:
            verdict = "INVENTED"
        else:
            verdict = "UNRESOLVED"

        counts[verdict] += 1
        if verdict != "OK":
            rows.append({
                "file": str(path),
                "verdict": verdict,
                "citekey": citekey,
                "doi": doi,
                "suggested_citekey": suggestion,
            })

    total = sum(counts.values())
    print(f"literature notes checked: {total}   (library: {len(keys)} keys)")
    for verdict in ("OK", "FILENAME", "INVENTED", "UNRESOLVED", "NO_CITEKEY"):
        if counts[verdict]:
            print(f"  {verdict:<11} {counts[verdict]}")

    for row in rows[:20]:
        name = Path(row["file"]).name
        arrow = f"  ->  {row['suggested_citekey']}" if row["suggested_citekey"] else ""
        print(f"  [{row['verdict']}] {name}: {row['citekey'] or '(none)'}{arrow}")
    if len(rows) > 20:
        print(f"  ... {len(rows) - 20} more (use --json for the full list)")

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(
            json.dumps(
                {
                    "detector": "check_citekey_provenance",
                    "counts": counts,
                    "findings": rows,
                },
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        print(f"audit written: {args.json}")

    if counts["INVENTED"]:
        print(f"\n{counts['INVENTED']} note(s) carry a citekey that exists nowhere. "
              "Each one is a citation that will not resolve.")
    if args.strict and counts["INVENTED"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
