#!/usr/bin/env python3
"""Marked (tracked-changes) manuscript round-trip gate.

Every journal revision round asks for a *marked* manuscript: the revised paper
with tracked changes against the version the reviewers saw. It is produced by
Microsoft Word's Compare (see `build_marked_manuscript.py` — pandiff and
LibreOffice `--compare` corrupt OOXML tables and superscript runs), and its
correctness has traditionally been "checked" by grepping the file for a couple
of sentences that ought to be inserted or deleted. That check is far too weak:
it passes even when Compare has silently dropped a paragraph, duplicated one, or
attributed half the revisions to a different author.

This gate replaces the grep with a round trip that is correct *by construction*:

    accept every revision  -> must reproduce the revised document, exactly
    reject every revision  -> must reproduce the original document, exactly

If both hold, no content was invented, dropped, or duplicated — there is nothing
left for the marked file to get wrong.

MOVES ARE NOT INSERT+DELETE. Word encodes relocated content as `w:moveFrom` /
`w:moveTo`, not `w:ins` / `w:del`. A resolver that only knows ins/del sees a
moved paragraph in *both* halves of the round trip and reports an untracked
duplicate — a false "Word corrupted the document" alarm on a perfectly good
file. The resolution below is move-aware:

    revised  = unchanged + w:ins     + w:moveTo
    original = unchanged + w:delText + w:moveFrom

TEXT EXTRACTION. Text is read by walking exact `w:t` / `w:delText` elements.
The tempting regex `<w:t[^>]*>(.*?)</w:t>` also matches `<w:tbl>`, `<w:tc>` and
`<w:tr>`, swallowing table markup as prose and inflating the character count
(roughly doubling it on a table-heavy manuscript) — which then reads as a
mismatch. Do not reintroduce it.

Verdicts (all major):
  MARKED_ACCEPT_MISMATCH   accepting all revisions does not reproduce --revised
  MARKED_REJECT_MISMATCH   rejecting all revisions does not reproduce --original
  MARKED_NO_REVISIONS      the file carries no tracked changes at all
  MARKED_AUTHOR_MIXED      revisions are attributed to someone other than --author
  MARKED_TABLE_LOSS        the marked file has fewer/more tables than --revised
  MARKED_BASE_TRACKED      --original / --revised themselves carry tracked changes,
                           which makes the round trip ill-defined

Usage:
    check_marked_manuscript.py --marked marked.docx \\
        --original R0.docx --revised v8_clean.docx \\
        [--author "Submitting Author"] [--strict] [--out qc/marked.json]

Exit 0 when the round trip holds (or, without --strict, whenever the file could
be read). With --strict, exit 1 if any verdict fires. Stdlib only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

INS, DEL = W + "ins", W + "del"
MOVE_TO, MOVE_FROM = W + "moveTo", W + "moveFrom"
TEXT, DEL_TEXT = W + "t", W + "delText"
TBL = W + "tbl"


def document_xml(path: Path) -> bytes:
    """The main document part of a .docx (headers/footers are out of scope)."""
    try:
        with zipfile.ZipFile(path) as z:
            return z.read("word/document.xml")
    except (KeyError, zipfile.BadZipFile) as exc:
        raise SystemExit(f"not a readable .docx: {path} ({exc})")


def _norm(s: str) -> str:
    """Collapse runs of whitespace. Word splits a sentence across runs freely and
    re-splits it when comparing; only the character stream is meaningful."""
    return re.sub(r"\s+", " ", s).strip()


def resolve(root: ET.Element, accept: bool) -> str:
    """Text of a document with every revision accepted (or rejected).

    Walks the tree carrying the revision state of the enclosing elements, so a
    run nested inside `w:ins` / `w:del` / `w:moveTo` / `w:moveFrom` is resolved
    by the region it lives in rather than by its own tag.
    """
    out: list[str] = []

    def visit(el: ET.Element, added: bool, gone: bool) -> None:
        if el.tag in (INS, MOVE_TO):
            added = True
        elif el.tag in (DEL, MOVE_FROM):
            gone = True

        if el.tag == TEXT:
            # Present in the revised text unless it was deleted or moved away.
            # Present in the original text unless it was inserted or moved in.
            if (not gone) if accept else (not added):
                out.append(el.text or "")
        elif el.tag == DEL_TEXT:
            # Deleted/moved-away text: belongs to the original only.
            if not accept:
                out.append(el.text or "")

        for child in el:
            visit(child, added, gone)

    visit(root, False, False)
    return _norm("".join(out))


def plain_text(root: ET.Element) -> str:
    """Text of an ordinary (untracked) document."""
    return _norm("".join(e.text or "" for e in root.iter(TEXT)))


def revision_marks(root: ET.Element) -> dict[str, int]:
    counts = {"ins": 0, "del": 0, "moveTo": 0, "moveFrom": 0}
    for el in root.iter():
        if el.tag == INS:
            counts["ins"] += 1
        elif el.tag == DEL:
            counts["del"] += 1
        elif el.tag == MOVE_TO:
            counts["moveTo"] += 1
        elif el.tag == MOVE_FROM:
            counts["moveFrom"] += 1
    return counts


def revision_authors(root: ET.Element) -> set[str]:
    authors: set[str] = set()
    for el in root.iter():
        if el.tag in (INS, DEL, MOVE_TO, MOVE_FROM):
            a = el.get(W + "author")
            if a:
                authors.add(a)
    return authors


def n_tables(root: ET.Element) -> int:
    return sum(1 for _ in root.iter(TBL))


def first_divergence(a: str, b: str, window: int = 60) -> str:
    """Where two texts first differ, with context — a mismatch must be actionable."""
    i = 0
    for i, (ca, cb) in enumerate(zip(a, b)):
        if ca != cb:
            break
    else:
        i = min(len(a), len(b))
    lo = max(0, i - window)
    return (
        f"first differs at char {i}\n"
        f"      round-trip: ...{a[lo:i + window]!r}\n"
        f"      expected:   ...{b[lo:i + window]!r}"
    )


def check(
    marked: Path, original: Path, revised: Path, author: str | None
) -> tuple[list[dict], dict]:
    m_root = ET.fromstring(document_xml(marked))
    o_root = ET.fromstring(document_xml(original))
    r_root = ET.fromstring(document_xml(revised))

    marks = revision_marks(m_root)
    authors = sorted(revision_authors(m_root))
    tbl_marked, tbl_revised = n_tables(m_root), n_tables(r_root)

    findings: list[dict] = []

    # A baseline that itself carries revisions makes the round trip meaningless:
    # its plain text would contain both the inserted and the deleted wording.
    dirty = [
        name
        for name, root in (("original", o_root), ("revised", r_root))
        if any(revision_marks(root).values())
    ]
    if dirty:
        findings.append(
            {
                "verdict": "MARKED_BASE_TRACKED",
                "severity": "major",
                "detail": (
                    f"{' and '.join(dirty)} still carries tracked changes; accept or "
                    "reject them in Word first — the round trip compares against the "
                    "plain text of these files."
                ),
            }
        )

    if not any(marks.values()):
        findings.append(
            {
                "verdict": "MARKED_NO_REVISIONS",
                "severity": "major",
                "detail": (
                    "no w:ins / w:del / w:moveTo / w:moveFrom in the marked file — "
                    "Compare produced a clean copy, not a marked manuscript."
                ),
            }
        )

    accepted, want_revised = resolve(m_root, accept=True), plain_text(r_root)
    if accepted != want_revised:
        findings.append(
            {
                "verdict": "MARKED_ACCEPT_MISMATCH",
                "severity": "major",
                "detail": (
                    f"accepting every revision yields {len(accepted)} chars, but the "
                    f"revised manuscript has {len(want_revised)}; content was dropped, "
                    f"duplicated, or invented.\n      "
                    + first_divergence(accepted, want_revised)
                ),
            }
        )

    rejected, want_original = resolve(m_root, accept=False), plain_text(o_root)
    if rejected != want_original:
        findings.append(
            {
                "verdict": "MARKED_REJECT_MISMATCH",
                "severity": "major",
                "detail": (
                    f"rejecting every revision yields {len(rejected)} chars, but the "
                    f"original manuscript has {len(want_original)}; the marked file is "
                    f"not a faithful diff of the version the reviewers saw.\n      "
                    + first_divergence(rejected, want_original)
                ),
            }
        )

    if author is not None and authors and set(authors) != {author}:
        findings.append(
            {
                "verdict": "MARKED_AUTHOR_MIXED",
                "severity": "major",
                "detail": (
                    f"revisions are attributed to {authors} — expected only {author!r}. "
                    "Pass the submitting author to Word's Compare (`author name`) rather "
                    "than rewriting w:author afterwards."
                ),
            }
        )

    if tbl_marked != tbl_revised:
        findings.append(
            {
                "verdict": "MARKED_TABLE_LOSS",
                "severity": "major",
                "detail": (
                    f"marked file has {tbl_marked} tables, the revised manuscript has "
                    f"{tbl_revised}; Compare mangled the table structure."
                ),
            }
        )

    summary = {
        "marked": str(marked),
        "original": str(original),
        "revised": str(revised),
        "revision_marks": marks,
        "revision_authors": authors,
        "tables": {"marked": tbl_marked, "revised": tbl_revised},
        "accept_roundtrip_ok": accepted == want_revised,
        "reject_roundtrip_ok": rejected == want_original,
        "chars": {
            "accepted": len(accepted),
            "revised": len(want_revised),
            "rejected": len(rejected),
            "original": len(want_original),
        },
    }
    return findings, summary


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--marked", required=True, type=Path, help="the tracked-changes docx to verify")
    ap.add_argument(
        "--original", required=True, type=Path, help="baseline: the version the reviewers saw (R0)"
    )
    ap.add_argument("--revised", required=True, type=Path, help="the new clean manuscript")
    ap.add_argument("--author", help="the one name every revision must be attributed to")
    ap.add_argument("--out", type=Path, help="write the JSON audit record here")
    ap.add_argument("--strict", action="store_true", help="exit 1 if any verdict fires")
    a = ap.parse_args()

    for f in (a.marked, a.original, a.revised):
        if not f.is_file():
            raise SystemExit(f"not found: {f}")

    findings, summary = check(a.marked, a.original, a.revised, a.author)

    m = summary["revision_marks"]
    print(
        f"{a.marked.name}: ins {m['ins']}, del {m['del']}, "
        f"moveTo {m['moveTo']}, moveFrom {m['moveFrom']}, "
        f"tables {summary['tables']['marked']}"
    )
    print(f"  {'PASS' if summary['accept_roundtrip_ok'] else 'FAIL'}  accept-all reproduces the revised manuscript")
    print(f"  {'PASS' if summary['reject_roundtrip_ok'] else 'FAIL'}  reject-all reproduces the original manuscript")
    for f in findings:
        print(f"  [{f['severity'].upper()}] {f['verdict']}: {f['detail']}")
    if not findings:
        print("  OK — marked manuscript verified; safe to upload")

    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(
            json.dumps({"detector": "check_marked_manuscript", "summary": summary, "findings": findings}, indent=2) + "\n",
            encoding="utf-8",
        )

    if a.strict and findings:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
