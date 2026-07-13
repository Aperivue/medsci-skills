#!/usr/bin/env python3
"""Duplicate-bibliography gate for a built manuscript (manage-refs / sync-submission).

A manuscript whose markdown carries BOTH inline `[@key]` citations AND a hand-typed
`## References` numbered list will, when built with pandoc `--citeproc`, render TWO
reference lists: the literal hand-typed one plus a citeproc-generated bibliography
appended at the end (often after the figure/table legends, where it is easy to
miss). A reviewer reads it as "the same reference is listed twice." A cross-
reference QC pass (check_xref) does not catch it because each entry is individually
valid; only a duplicate-list scan does.

This detector reads the BUILT artifact (docx via stdlib zipfile, or a rendered
md/txt) and fires when the reference list is duplicated. Signals, any of which is
load-bearing:

  DUP_REF_HEADING     two or more reference-section headings
                      (References / Bibliography / Works Cited).
  REF_NUMBER_RESTART  a numbered reference-entry sequence that restarts
                      (entry "1." appears two or more times) — the signature of a
                      second list concatenated after the first.
  REF_SIGNATURE_DUP   the (first-author surname, year) signature of >= 3 distinct
                      references each appears two or more times — a whole list
                      repeated, not a coincidental same-author-same-year pair.

A single duplicated (surname, year) with no other signal is reported as a
DUP_REF_ENTRY flag (Minor: verify — could be two distinct same-year papers by one
author), never a Major on its own.

Motivation: a built submission docx rendered the 15-entry hand-typed reference list
and then a second 15-entry citeproc bibliography after the legends; a co-author
flagged "a reference is repeated twice." See
~/.claude/rules/manuscript-references.md (Hybrid hand-list + citeproc section).

INPUTS  (one of)
  --docx PATH    built .docx (read via stdlib zipfile; word/document.xml)
  --text PATH    rendered markdown / plain text

OUTPUT  reconciliation table (stdout) + optional JSON:
  {source, ref_entries, headings, claims[{verdict, severity, detail, where}], summary}

Stdlib-only (re / json / zipfile / argparse / pathlib). Exit codes: 0 clean/
report-only, 1 Major with --strict, 2 input/usage error.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path

HEADING_RE = re.compile(
    r"^\s*#{0,6}\s*\**\s*(references|reference list|bibliography|works cited|literature cited)\s*\**\s*:?\s*$",
    re.I,
)
# A reference entry begins with an author "Surname I" token (capitalized surname
# followed by an uppercase initial), optionally preceded by a list number. This
# does NOT depend on a text-level number, because Word auto-numbered lists keep
# the number in list formatting (numPr), not in the paragraph text — so a hand
# list and a citeproc list render entries that both start at the surname.
ENTRY_RE = re.compile(
    r"^\s*(?P<num>\d{1,3})?\s*[.\)]?\s*"
    r"(?P<surname>[A-Z][A-Za-zÀ-ɏ'\-]{1,})\s*,?\s+[A-Z]"
)
YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")
SURNAME_RE = re.compile(r"[A-Z][A-Za-zÀ-ɏ'\-]+")
DOI_RE = re.compile(r"10\.\d{4,9}/[^\s\"'<>]+", re.I)


def _docx_paragraphs(path: Path) -> list[str]:
    try:
        with zipfile.ZipFile(path, "r") as z:
            xml = z.read("word/document.xml").decode("utf-8", errors="replace")
    except (zipfile.BadZipFile, KeyError, OSError):
        return []
    # Paragraph boundary = </w:p>. Strip remaining tags inside each paragraph.
    paras = re.split(r"</w:p>", xml)
    out = []
    for p in paras:
        txt = re.sub(r"<[^>]+>", "", p)
        txt = re.sub(r"\s+", " ", txt).strip()
        if txt:
            out.append(txt)
    return out


def _text_lines(path: Path) -> list[str]:
    raw = path.read_text(encoding="utf-8", errors="replace")
    return [ln.strip() for ln in raw.splitlines() if ln.strip()]


def analyze(lines: list[str], source: str) -> dict:
    headings = [i for i, ln in enumerate(lines) if HEADING_RE.match(ln)]

    # Reference entries: numbered lines whose tail looks like a citation (has a
    # 4-digit year somewhere). Restrict to lines that begin with a small integer
    # and contain a capitalized author-like token to avoid eating body numerals.
    entries = []
    for i, ln in enumerate(lines):
        m = ENTRY_RE.match(ln)
        if not m:
            continue
        if not YEAR_RE.search(ln):
            continue
        num = int(m.group("num")) if m.group("num") else None
        surname = m.group("surname").lower()
        year = YEAR_RE.search(ln).group(0)
        dm = DOI_RE.search(ln)
        entries.append({"line": i, "num": num, "tail": ln,
                        "sig": (surname, year),
                        "doi": dm.group(0).lower() if dm else None})

    claims = []

    # Signal 1: duplicate reference-section heading.
    if len(headings) >= 2:
        claims.append({
            "verdict": "DUP_REF_HEADING", "severity": "Major",
            "detail": f"{len(headings)} reference-section headings found "
                      f"(lines {', '.join(str(h + 1) for h in headings)}); a built "
                      f"manuscript should have exactly one bibliography.",
            "where": ", ".join(str(h + 1) for h in headings),
        })

    # Signal 2: numbered sequence restarts (entry '1' appears >= 2 times).
    ones = [e for e in entries if e["num"] == 1]
    if len(ones) >= 2 and len(entries) >= 4:
        claims.append({
            "verdict": "REF_NUMBER_RESTART", "severity": "Major",
            "detail": f"numbered reference list restarts: entry '1.' appears "
                      f"{len(ones)} times (lines {', '.join(str(o['line'] + 1) for o in ones)}) "
                      f"across {len(entries)} numbered entries — a second list is "
                      f"concatenated after the first.",
            "where": ", ".join(str(o["line"] + 1) for o in ones),
        })

    # Signal 3: (surname, year) signature of >= 3 distinct refs each duplicated.
    sigs = [e["sig"] for e in entries if e["sig"]]
    counts: dict = {}
    for s in sigs:
        counts[s] = counts.get(s, 0) + 1
    dup_sigs = [s for s, c in counts.items() if c >= 2]
    # DOI duplicates reinforce the signal.
    dois = [e["doi"] for e in entries if e["doi"]]
    dup_dois = {d for d in dois if dois.count(d) >= 2}

    if len(dup_sigs) >= 3:
        ex = ", ".join(f"{s[0].title()} {s[1]}" for s in dup_sigs[:4])
        claims.append({
            "verdict": "REF_SIGNATURE_DUP", "severity": "Major",
            "detail": f"{len(dup_sigs)} distinct references each appear >=2x in the "
                      f"reference list (e.g. {ex}{'…' if len(dup_sigs) > 4 else ''})"
                      + (f"; {len(dup_dois)} DOI(s) also duplicated" if dup_dois else "")
                      + " — the bibliography is duplicated.",
            "where": f"{len(entries)} numbered entries",
        })
    elif dup_sigs:
        ex = ", ".join(f"{s[0].title()} {s[1]}" for s in dup_sigs)
        claims.append({
            "verdict": "DUP_REF_ENTRY", "severity": "Minor",
            "detail": f"{len(dup_sigs)} reference signature(s) duplicated ({ex}). "
                      f"Verify these are not two distinct same-year papers by the "
                      f"same first author.",
            "where": ex,
        })

    n_major = sum(1 for c in claims if c["severity"] == "Major")
    return {
        "source": source,
        "ref_entries": len(entries),
        "headings": len(headings),
        "claims": claims,
        "summary": {
            "n_claims": len(claims),
            "n_major": n_major,
            "verdict": "MAJOR_CANDIDATE" if n_major else "OK",
        },
    }


def render(result: dict) -> str:
    lines = ["| Check | Severity | Detail |", "|---|---|---|"]
    for c in result["claims"]:
        lines.append(f"| {c['verdict']} | {c['severity']} | {c['detail']} |")
    if len(lines) == 2:
        lines.append("| (none) | — | single reference list; no duplication detected |")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Duplicate-bibliography gate for a built manuscript.")
    ap.add_argument("--docx", help="built .docx (read via stdlib zipfile)")
    ap.add_argument("--text", help="rendered markdown / plain text")
    ap.add_argument("--out", help="write JSON artifact to this path")
    ap.add_argument("--strict", action="store_true", help="exit 1 if any Major finding")
    ap.add_argument("--quiet", action="store_true", help="suppress stdout table")
    args = ap.parse_args()

    if not args.docx and not args.text:
        sys.stderr.write("ERROR: one of --docx / --text is required\n")
        return 2
    if args.docx:
        p = Path(args.docx)
        if not p.is_file():
            sys.stderr.write(f"ERROR: not a file: {p}\n")
            return 2
        lines = _docx_paragraphs(p)
        source = str(p)
    else:
        p = Path(args.text)
        if not p.is_file():
            sys.stderr.write(f"ERROR: not a file: {p}\n")
            return 2
        lines = _text_lines(p)
        source = str(p)

    result = analyze(lines, source)

    if not args.quiet:
        print("=" * 42)
        print(" Reference Duplication (build-time gate)")
        print("=" * 42)
        print(render(result))
        print()
        s = result["summary"]
        if s["n_major"]:
            print(f"MAJOR candidate: bibliography appears duplicated "
                  f"({result['ref_entries']} numbered entries, {result['headings']} headings).")
        else:
            print(f"OK: single reference list "
                  f"({result['ref_entries']} numbered entries, {result['headings']} headings).")

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps({"detector": "check_reference_duplication", **result}, indent=2), encoding="utf-8")
        if not args.quiet:
            print(f"\nwrote {args.out}")

    return 1 if (args.strict and result["summary"]["n_major"]) else 0


if __name__ == "__main__":
    sys.exit(main())
