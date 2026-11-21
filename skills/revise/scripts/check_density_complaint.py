#!/usr/bin/env python3
""""Your paper is too dense" is the one comment you cannot address by adding text.

The failure this gate catches, in the shape it takes:

    previous   as the reviewers saw it  ->  "too dense / shorten / move to supplement"
    revised    THE revision answering   ->  LONGER.  Every named term goes UP, because each
               those comments               comment is answered point-by-point, and point-by-point
                                            response REWARDS adding text.
    next       the cut version          ->  below where it started.  <- what the letter asked for.

Answering "your text is too dense" comment-by-comment makes it denser, because point-by-point
culture rewards showing you addressed each comment — and length is the one comment adding text
cannot address. The shrink then slips another round away.

This gate is pure arithmetic. If the reviewer comments contain a density/length complaint AND the
revised manuscript body did not get SHORTER than the previous version, the complaint was not
addressed — it was made worse. It fires on the longer revision immediately, and stays silent on the cut one.

It reads:
  --comments   the reviewer decision letter (where the complaint lives)
  --previous   the manuscript as the reviewers saw it   (the word count they complained about)
  --revised    the manuscript you are about to send back (must be shorter, if a complaint was made)

Body word count is measured the way a reviewer counts it: Introduction through Discussion, excluding
the title page, abstract, references, tables, figure legends, and — so a citation-heavy paragraph is
not scored as verbose — bracketed/parenthetical citation markers. It is a ratio check, so the exact
rule matters less than applying it identically to both versions, which it does.

Usage:
    check_density_complaint.py --comments letter.md --previous v_prev.docx --revised v_new.docx \
        [--out qc/density.json] [--strict]

Stdlib only (.docx via python-docx when present).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

# The vocabulary a reviewer reaches for when a manuscript is too long or too dense. Each is a
# complaint that adding text cannot answer.
COMPLAINT = re.compile(
    r"\b(too (long|dense|detailed|verbose|wordy)|overly (long|detailed|dense|complex)|"
    r"shorten(ed|ing)?|condens(e|ed|ing)|trim(med|ming)?|cut down|tighten(ed|ing)?|"
    r"reduce (the )?(length|word count|detail)|"
    r"(mov\w+|belongs?).{0,30}?(to (the )?supplement|to supplementary|in (the )?supplement)|"
    r"excessive(ly)? (detail|length|long)|"
    r"(somewhat |very |quite |rather |overly )?(dense|verbose|wordy)\b|"
    r"(is|are|reads?|too) (very )?(repetitive|redundant)|"
    r"difficult to follow|hard to follow|dilut(e|es|ing) the (main )?message|"
    r"streamlin(e|ed|ing)|language editing|more concise|less dense|for (legibility|readability)|"
    r"repeat(ed|s|ing)? (multiple times|throughout|itself))\b",
    re.IGNORECASE,
)

# Section headings, in reviewer-count order. Body = first Introduction..Introduction-like heading
# through the end of Discussion / before References.
# Where the body ends. A markdown heading ("## ...") that begins with one of the ending words
# ends it, as it always did ("## Supplementary Results", "## References ##"). A line WITHOUT a
# heading mark ends it only when the line is a section name: alone, or followed on the same line
# by a colon or a full stop and run-in text ("Funding: ...", "**Funding**. This work ..."). A
# line that merely begins with such a word is prose: "Supplementary Table 2 lists ...", "Funding
# for the registry came from ...". Ending the body there measured only the text above it in BOTH
# versions, so a revision that had been cut was reported as unchanged.
_HS = r"[^\S\r\n]"          # horizontal whitespace; never crosses a line
_END_WORD = (r"references|acknowledge?ments?|funding|conflicts?|data availability|supplementary|"
             r"supporting information|figure legends?")
_END_NAME = (
    r"references?(?:" + _HS + r"+list)?|bibliography|acknowledge?ments?|"
    r"funding(?:" + _HS + r"+(?:sources?|information|statement|support))?|"
    r"conflicts?(?:" + _HS + r"+of" + _HS + r"+interests?(?:" + _HS + r"+(?:statement|disclosures?))?)?|"
    r"competing" + _HS + r"+interests?|disclosures?|"
    r"declarations?" + _HS + r"+of" + _HS + r"+(?:competing" + _HS + r"+|conflicting" + _HS + r"+)?interests?|"
    r"data" + _HS + r"+(?:availability|sharing)(?:" + _HS + r"+statement)?|"
    r"supplementary(?:" + _HS + r"+(?:materials?|information|data|files?|appendix|appendices|methods|"
    r"results|tables?|figures?|text|notes?))?|"
    r"supporting" + _HS + r"+information|figure" + _HS + r"+legends?"
)
_NUMBERING = r"(?:\d+(?:\.\d+)*\.?" + _HS + r"+)?"
BODY_END = re.compile(
    r"^" + _HS + r"*(?:"
    # a markdown heading that begins with an ending word or is a section name
    r"#{1,6}" + _HS + r"*\**" + _HS + r"*" + _NUMBERING + r"(?P<h>" + _END_WORD + r"|" + _END_NAME + r")\b.*"
    # a line with no heading mark that IS a section name, optionally with a run-in after ":" or ". "
    r"|[*_]{0,3}" + _HS + r"*" + _NUMBERING + r"(?P<n>" + _END_NAME + r")"
    + _HS + r"*[*_]{0,3}" + _HS + r"*(?::.*|\.[*_]{0,3}(?:" + _HS + r".*)?)?"
    r")$",
    re.IGNORECASE | re.MULTILINE,
)
BODY_START = re.compile(r"^" + _HS + r"*#{0,4}" + _HS + r"*\**" + _HS + r"*(introduction|background)\b",
                        re.IGNORECASE | re.MULTILINE)


def _body_end(body: str):
    return BODY_END.search(body)
ABSTRACT = re.compile(r"^#{0,4}\s*\**\s*abstract\b", re.IGNORECASE | re.MULTILINE)

CITATION = re.compile(r"\[[\d,\s–\-]+\]|\((?:[A-Z][A-Za-z'`-]+(?: et al\.?)?,?\s*\d{4}[a-z]?;?\s*)+\)")


def read_text(path: Path) -> str:
    if path.suffix.lower() == ".docx":
        try:
            from docx import Document  # type: ignore
        except Exception as exc:  # pragma: no cover
            raise SystemExit(f"python-docx required to read {path}: {exc}")
        doc = Document(str(path))
        parts: list[str] = []

        def walk(tbl):
            for row in tbl.rows:
                for cell in row.cells:
                    for p in cell.paragraphs:
                        parts.append(p.text)
                    for t in cell.tables:
                        walk(t)

        for p in doc.paragraphs:
            parts.append(p.text)
        for t in doc.tables:
            walk(t)
        return "\n".join(parts)
    return path.read_text(encoding="utf-8", errors="replace")


def _bounds(text: str):
    """(start, end, start match, end match) of the measured body in NFKC text."""
    m0 = BODY_START.search(text)
    start = m0.start() if m0 else 0
    m1 = _body_end(text[start:])
    end = start + m1.start() if m1 else len(text)
    return start, end, m0, m1


def body_span(text: str) -> dict:
    """The lines that were counted (1-based, inclusive) and what bounded them.

    start_line and end_line are None when nothing was counted (the file is empty, or it ends
    its body on the first line)."""
    text = unicodedata.normalize("NFKC", text)
    start, end, m0, m1 = _bounds(text)
    counted = text[start:end]
    if counted.strip():
        first = text.count("\n", 0, start) + 1
        last = first + counted.rstrip().count("\n")
    else:
        first = last = None
    return {
        "start_line": first,
        "end_line": last,
        "start_marker": m0.group(1).lower() if m0 else "start of file (no Introduction/Background heading)",
        "end_marker": (re.sub(r"\s+", " ", m1.group("h") or m1.group("n")).lower()
                       if m1 else "end of file (no References-like heading)"),
    }


def body_word_count(text: str) -> int:
    """Introduction..before-References, abstract excluded, citation markers removed."""
    text = unicodedata.normalize("NFKC", text)
    start, end, m0, _ = _bounds(text)
    body = text[start:end]
    # if an Abstract heading is inside our slice (no Introduction found), drop it
    if not m0:
        a = ABSTRACT.search(body)
        if a:
            nxt = BODY_START.search(body, a.end())
            if nxt:
                body = body[nxt.start():]
    body = CITATION.sub(" ", body)
    body = re.sub(r"^#{1,6}\s.*$", " ", body, flags=re.MULTILINE)  # drop heading lines themselves
    body = re.sub(r"[*_`>|#]", " ", body)                          # markdown punctuation
    words = re.findall(r"[A-Za-z0-9][\w'–-]*", body)
    return len(words)


def complaints(text: str) -> list[str]:
    """The density/length complaint sentences in the decision letter."""
    out: list[str] = []
    for sent in re.split(r"(?<=[.!?])\s+|\n", text):
        if COMPLAINT.search(sent):
            out.append(re.sub(r"\s+", " ", sent).strip()[:160])
    # dedupe preserving order
    seen, uniq = set(), []
    for s in out:
        if s.lower() not in seen:
            seen.add(s.lower()); uniq.append(s)
    return uniq


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--comments", required=True, type=Path, help="reviewer decision letter (.md/.txt/.docx)")
    ap.add_argument("--previous", required=True, type=Path, help="manuscript the reviewers saw (.md/.txt/.docx)")
    ap.add_argument("--revised", required=True, type=Path, help="manuscript you are about to send back")
    ap.add_argument("--out", type=Path, help="write JSON report here")
    ap.add_argument("--strict", action="store_true", help="exit 1 if the complaint was not addressed")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args(argv)

    for p in (a.comments, a.previous, a.revised):
        if not p.is_file():
            print(f"error: file not found: {p}", file=sys.stderr)
            return 2

    comp = complaints(read_text(a.comments))
    prev_text, new_text = read_text(a.previous), read_text(a.revised)
    prev_wc = body_word_count(prev_text)
    new_wc = body_word_count(new_text)
    spans = {"previous": body_span(prev_text), "revised": body_span(new_text)}
    delta = new_wc - prev_wc

    fired = bool(comp) and delta >= 0
    report = {
        "detector": "check_density_complaint",
        "density_complaints": comp,
        "previous_body_words": prev_wc,
        "revised_body_words": new_wc,
        "delta_words": delta,
        # What was counted. A span that stops well short of the manuscript's end is the sign
        # that the body was bounded in the wrong place; read it before trusting the delta.
        "measured_span": spans,
        "verdict": "DENSITY_COMPLAINT_UNADDRESSED" if fired else "OK",
    }
    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(json.dumps(report, indent=2), encoding="utf-8")

    if not a.quiet:
        for name in ("previous", "revised"):
            s = spans[name]
            span = (f"lines {s['start_line']}-{s['end_line']}" if s["start_line"] else "no lines")
            print(f"measured {name}: {span} (from {s['start_marker']} to {s['end_marker']})")
        if not comp:
            print(f"OK: no density/length complaint in the decision letter "
                  f"(body {prev_wc} -> {new_wc} words, {delta:+d}).")
        elif not fired:
            print(f"OK: a density complaint was raised and the body got shorter "
                  f"({prev_wc} -> {new_wc} words, {delta:+d}).")
        else:
            print(f"DENSITY_COMPLAINT_UNADDRESSED: reviewers said the manuscript was too dense/long, "
                  f"and the body did not get shorter ({prev_wc} -> {new_wc} words, {delta:+d}).\n")
            for c in comp[:6]:
                print(f"  reviewer: {c}")
            print(
                "\n'Too dense' is the one comment you cannot address by adding text, and point-by-point\n"
                "response rewards adding it: answering each density comment individually is how a\n"
                "revision comes back longer than the version that drew the complaint. Cut, or move\n"
                "detail to the supplement — do not defend length by adding a paragraph that explains\n"
                "it."
            )
    return 1 if (fired and a.strict) else 0


if __name__ == "__main__":
    sys.exit(main())
