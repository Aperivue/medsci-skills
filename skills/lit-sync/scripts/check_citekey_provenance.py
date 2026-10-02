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
    OK             citekey is present exactly once in the library (and the note's DOI is
                   not another key's library DOI)
    MISMATCH       citekey is real, but the note's DOI is the library's DOI for a
                   different, unambiguous key — the key belongs to another paper (a composed
                   key that collided with a real one). That other key is suggested. A note
                   DOI that matches no library DOI as spelled never raises MISMATCH
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
    UNPARSED       note declares ``notetype: literature`` but its frontmatter has no closing
                   ``---``, so its citekey could not be read

Exit status is 0 unless --strict is given, matching the repo's gate convention. Under
--strict, INVENTED, MISMATCH or UNPARSED exit 1, and a scan that found no literature note
at all exits 2 (the check did not run, so it cannot pass).

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
OPEN_FENCE_RE = re.compile(r"\A---\n")
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


def merge_libraries(sources: list) -> tuple:
    """Return (citekeys, ambiguous citekeys, key -> DOIs, doi -> citekey, pmid -> citekey).

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
    return keys, ambiguous, key_dois, doi_to_key, pmid_to_key


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
    """Yield (path, frontmatter) for each literature note; frontmatter is None when unparsed.

    Hidden folders are judged relative to the vault root, so a vault reached through
    ``../`` or stored under a dot-directory is still scanned. The whole frontmatter is
    read (no length cap) and a UTF-8 BOM or CRLF line endings do not hide a note.
    """
    for path in sorted(root.rglob("*.md")):
        try:
            rel_parts = path.relative_to(root).parts
        except ValueError:
            rel_parts = path.parts
        if any(part.startswith(".") for part in rel_parts):
            continue
        try:
            text = path.read_text(encoding="utf-8-sig", errors="ignore")
        except OSError:
            continue
        text = text.replace("\r\n", "\n")
        m = FRONTMATTER_RE.match(text)
        if not m:
            # An opening fence with no closing one: say so when the note declares itself
            # a literature note, instead of skipping it as if it were not one.
            if OPEN_FENCE_RE.match(text) and field(text, "notetype") == "literature":
                yield path, None
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
                    help="exit 1 when any INVENTED, MISMATCH or UNPARSED note is found; "
                         "exit 2 when no literature note was found")
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
    keys, ambiguous, key_dois, doi_to_key, pmid_to_key = merge_libraries(sources)

    if not keys:
        print("error: reference library is empty — every note would be reported as "
              "unresolved, which says nothing. Check the .bib path or open Zotero.",
              file=sys.stderr)
        return 2

    rows = []
    counts = {"OK": 0, "INVENTED": 0, "MISMATCH": 0, "UNRESOLVED": 0, "NO_IDENTIFIER": 0,
              "AMBIGUOUS": 0, "UNUSABLE": 0, "NO_CITEKEY": 0, "FILENAME": 0, "UNPARSED": 0}
    for path, fm in iter_notes(args.vault):
        if fm is None:
            counts["UNPARSED"] += 1
            rows.append({
                "file": str(path), "verdict": "UNPARSED", "citekey": "", "doi": "",
                "pmid": "", "suggested_citekey": "",
                "reason": "frontmatter opens with --- but never closes; citekey not read",
            })
            continue
        citekey = field(fm, "citekey")
        doi = norm_doi(field(fm, "doi"))
        pmid = field(fm, "pmid")
        doi_key = doi_to_key.get(doi, "") if doi else ""
        suggestion = doi_key
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
        elif (citekey in keys and doi_key and doi_key != citekey
              and doi_key not in ambiguous and not unusable(doi_key)
              and doi not in key_dois.get(citekey, set())):
            # Only a DOI the library itself knows, on a different unambiguous key, proves
            # the key belongs to another paper. A DOI spelled differently from the library
            # (quotes, resolver host, BibTeX braces or escapes) resolves to no key and so
            # never raises MISMATCH; it keeps main's OK.
            verdict, suggestion = "MISMATCH", doi_key
            reason = (f"this note's DOI {doi} is the library's DOI for {doi_key}, "
                      f"not for {citekey}; the key belongs to another paper")
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
    for verdict in ("OK", "FILENAME", "INVENTED", "MISMATCH", "UNPARSED", "AMBIGUOUS",
                    "UNUSABLE", "UNRESOLVED", "NO_IDENTIFIER", "NO_CITEKEY"):
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
    if counts["MISMATCH"]:
        print(f"\n{counts['MISMATCH']} note(s) carry a real key that the library gives to a "
              "different DOI. The citation will resolve — to the wrong paper.")
    if counts["UNPARSED"]:
        print(f"\n{counts['UNPARSED']} literature note(s) have frontmatter with no closing "
              "---; their citekeys were not checked.")
    if total == 0:
        print(f"warning: no literature note (notetype: literature) found under {args.vault}; "
              "nothing was checked", file=sys.stderr)
        if args.strict:
            return 2
    if args.strict and (counts["INVENTED"] or counts["MISMATCH"] or counts["UNPARSED"]):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
