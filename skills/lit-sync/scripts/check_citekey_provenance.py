#!/usr/bin/env python3
"""Check that every literature note's citekey exists in the reference library.

A literature note filename and its ``citekey:`` field assert that an entry with that
key exists in Zotero. When the key was composed rather than read, the note still looks
correct while ``[@key]`` resolves to nothing, ``[[key]]`` points at no file, and the
Zotero Integration plugin writes a second note under the real key. This reports the
keys that exist nowhere, and — where the note carries a DOI (or PMID) the library also
has — the real key it should have carried.

A citekey is a label, not an identity. Keys minted by content negotiation (``Author_Year``)
repeat across a library, and some arrive as URLs. Match notes to papers by DOI, never by
citekey; a key that names two entries identifies neither.

Verdicts
    OK             citekey is present exactly once in the library
    INVENTED       citekey absent, but the note's DOI (or PMID) resolves to a real key
                   (fixable here — unless that key is itself ambiguous, when no key is
                   suggested and ``reason`` says why)
    UNRESOLVED     the note's DOI/PMID and its citekey were not found in the library that was
                   searched. Not proof the paper was never added: check the whole library
                   (``--live``) before importing it again, or you create a duplicate
    NO_IDENTIFIER  citekey absent and the note has no DOI or PMID, so nothing could be looked
                   up — fill in the identifier first; this verdict is never a reason to import
    AMBIGUOUS      citekey is carried by two or more library entries, so it identifies no one
                   paper — refresh the keys in Better BibTeX; never merge notes on it
    UNUSABLE       citekey contains '/' or is a URL — it cannot be a filename or a [[link]]
    NO_CITEKEY     note has no citekey (recoverable; not a violation)
    FILENAME       citekey is real but the filename disagrees with it

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
from collections import Counter
from pathlib import Path

BBT_JSONRPC = "http://127.0.0.1:23119/better-bibtex/json-rpc"

FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---", re.S)
BIB_ENTRY_RE = re.compile(r"@\w+\{([^,]+),(.*?)(?=\n@|\Z)", re.S)
BIB_DOI_RE = re.compile(r"\bdoi\s*=\s*[{\"]([^}\"]+)", re.I)
BIB_PMID_RE = re.compile(r"\bpmid\s*=\s*[{\"]\s*(\d+)", re.I)
DOI_PREFIX_RE = re.compile(r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)", re.I)


def field(frontmatter: str, name: str) -> str:
    m = re.search(rf'^{name}:\s*"?([^"\n]*)"?\s*$', frontmatter, re.M)
    return m.group(1).strip() if m else ""


def norm_doi(value: str) -> str:
    """Lower-case a DOI and drop a resolver/``doi:`` prefix, so spellings compare equal."""
    return DOI_PREFIX_RE.sub("", (value or "").strip()).strip().lower()


def unusable(key: str) -> bool:
    """A key with '/' or a URL cannot be a note filename or a wikilink target."""
    return "/" in key or key.lower().startswith("http")


def parse_library(text: str) -> tuple:
    """One library source -> (key counts, key -> DOIs, doi -> citekey, pmid -> citekey)."""
    counts: Counter = Counter()
    key_dois: dict[str, set[str]] = {}
    doi_to_key: dict[str, str] = {}
    pmid_to_key: dict[str, str] = {}
    for key, body in BIB_ENTRY_RE.findall(text):
        key = key.strip()
        counts[key] += 1
        doi = BIB_DOI_RE.search(body)
        if doi:
            doi = norm_doi(doi.group(1))
            key_dois.setdefault(key, set()).add(doi)
            doi_to_key.setdefault(doi, key)
        pmid = BIB_PMID_RE.search(body)
        if pmid:
            pmid_to_key.setdefault(pmid.group(1), key)
    return counts, key_dois, doi_to_key, pmid_to_key


def merge_libraries(sources: list) -> tuple[set[str], set[str], dict[str, str], dict[str, str]]:
    """Return (citekeys, ambiguous citekeys, doi -> citekey, pmid -> citekey).

    A key is ambiguous when one source carries it on two or more entries, or when the
    sources give it two different DOIs. The same entry seen in a .bib snapshot AND the live
    library is one entry, not a duplicate, so counts are never summed across sources.
    """
    keys: set[str] = set()
    ambiguous: set[str] = set()
    key_dois: dict[str, set[str]] = {}
    doi_to_key: dict[str, str] = {}
    pmid_to_key: dict[str, str] = {}
    for counts, dois_by_key, dois, pmids in sources:
        keys |= set(counts)
        ambiguous |= {k for k, n in counts.items() if n > 1}
        for key, values in dois_by_key.items():
            key_dois.setdefault(key, set()).update(values)
        for doi, key in dois.items():
            doi_to_key.setdefault(doi, key)
        for pmid, key in pmids.items():
            pmid_to_key.setdefault(pmid, key)
    ambiguous |= {k for k, values in key_dois.items() if len(values) > 1}
    return keys, ambiguous, doi_to_key, pmid_to_key


def load_bib(paths: list[Path]) -> list:
    """Parse every readable .bib given, one library source each."""
    sources = []
    for p in paths:
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError as exc:
            print(f"warning: cannot read {p}: {exc}", file=sys.stderr)
            continue
        sources.append(parse_library(text))
    return sources


def load_live() -> list:
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
        return []
    return [parse_library(text)]


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

    sources = load_bib(list(args.bib))
    if args.live:
        sources += load_live()
    keys, ambiguous, doi_to_key, pmid_to_key = merge_libraries(sources)

    if not keys:
        print("error: reference library is empty — every note would be reported as "
              "unresolved, which says nothing. Check the .bib path or open Zotero.",
              file=sys.stderr)
        return 2

    rows = []
    counts = {"OK": 0, "INVENTED": 0, "UNRESOLVED": 0, "NO_IDENTIFIER": 0,
              "AMBIGUOUS": 0, "UNUSABLE": 0, "NO_CITEKEY": 0, "FILENAME": 0}
    for path, fm in iter_notes(args.vault):
        citekey = field(fm, "citekey")
        doi = norm_doi(field(fm, "doi"))
        pmid = field(fm, "pmid")
        suggestion = doi_to_key.get(doi, "") if doi else ""
        if not suggestion and pmid:
            suggestion = pmid_to_key.get(pmid, "")
        reason = ""

        if not citekey:
            verdict = "NO_CITEKEY"
        elif unusable(citekey):
            verdict, suggestion = "UNUSABLE", ""
            reason = "key contains '/' or is a URL; refresh it in Better BibTeX"
        elif citekey in ambiguous:
            verdict, suggestion = "AMBIGUOUS", ""
            reason = "key is carried by several library entries; refresh keys in Better BibTeX"
        elif citekey in keys:
            verdict = "OK" if path.stem == citekey else "FILENAME"
            suggestion = citekey if verdict == "FILENAME" else ""
        elif suggestion:
            verdict = "INVENTED"
            if suggestion in ambiguous or unusable(suggestion):
                reason = (f"the library key for this DOI/PMID ({suggestion}) is ambiguous or "
                          "unusable; refresh keys in Better BibTeX before renaming")
                suggestion = ""
        elif doi or pmid:
            verdict = "UNRESOLVED"
        else:
            verdict = "NO_IDENTIFIER"

        counts[verdict] += 1
        if verdict != "OK":
            row = {
                "file": str(path),
                "verdict": verdict,
                "citekey": citekey,
                "doi": doi,
                "pmid": pmid,
                "suggested_citekey": suggestion,
            }
            if reason:
                row["reason"] = reason
            rows.append(row)

    total = sum(counts.values())
    print(f"literature notes checked: {total}   (library: {len(keys)} keys)")
    for verdict in ("OK", "FILENAME", "INVENTED", "AMBIGUOUS", "UNUSABLE", "UNRESOLVED",
                    "NO_IDENTIFIER", "NO_CITEKEY"):
        if counts[verdict]:
            print(f"  {verdict:<13} {counts[verdict]}")

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
    if counts["AMBIGUOUS"] or counts["UNUSABLE"]:
        print(f"\n{counts['AMBIGUOUS'] + counts['UNUSABLE']} note(s) carry a key that names "
              "no single paper. Refresh keys in Better BibTeX; match notes by DOI, not key.")
    if counts["UNRESOLVED"] or counts["NO_IDENTIFIER"]:
        print("\nUNRESOLVED / NO_IDENTIFIER mean 'not found with what this note carries', not "
              "'never added'. Search the full library before importing, or you add a duplicate.")
    if args.strict and counts["INVENTED"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
