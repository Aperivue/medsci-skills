#!/usr/bin/env python3
"""Perspective structural gate — two article-genre tells that mark a Perspective / opinion
essay drafted like an original article (self-review §J / §D). Genre-gated: fires only when the
manuscript is a Perspective (front-matter ``article_type:`` or ``--type``).

A Perspective's contribution lives in its prose, not in data, so two habits carried over from
IMRAD writing read as "this was drafted as a study, not argued":

  * **IMRAD section headings.** Published Perspectives name sections as argument-moves
    ("The model reads your account, not your patient"), never "Introduction / Methods / Results /
    Discussion". A generic IMRAD heading in a Perspective is the tell.
  * **A thesis abstract with no authorial move.** Eight of nine sampled npj Digital Medicine
    Perspectives open the abstract with an explicit "we argue" / "we propose" / "here we ...".
    A purely declarative abstract reads as a report, not a position.

Both are Minor (advisory). The gate never judges the argument — only these two surface forms.
Conclusion / Summary headings are allowed; an absent abstract is allowed (many Perspectives carry
the summary only in metadata / the submission portal, not the body).

Parser is deliberately careful (hardened against a Codex design review):
  * Only the leading ``---``-fenced front matter is read for the genre; a body ``**Article type**``
    line is ignored. Self-review passes its known type through ``--type``; on disagreement the gate
    warns and uses ``--type`` rather than guessing.
  * HTML comment blocks are blanked (newline-preserving) before any scan, so a commented-out
    ``## Methods`` is not flagged and a "we argue" inside a comment does not suppress the abstract
    verdict.
  * Only level-2 ``##`` headings are sections (``### Box 1`` is not); leading section numbers
    ("1.", "2.3") and markdown decoration are stripped before the IMRAD-token test.
  * Structural / front / back-matter headings (Title page, Abstract, Display items, Submission
    notes, References, ...) are skipped, never flagged.
  * The FIRST body Abstract is evaluated; a duplicate raises a parser warning.

v1 auto-activates on an exact "perspective" label only. Viewpoint / Comment are deferred until
they carry their own fixtures — a Lancet "Comment" and an RSNA "Perspective" are different genres.

Verdicts (both Minor; either can fire independently):
  PERSPECTIVE_HEADING_NOT_ASSERTION       a content-section heading is an IMRAD label.
  PERSPECTIVE_ABSTRACT_NO_AUTHORIAL_MOVE   a body abstract states its thesis with no authorial move.

Exit codes: 0 clean/report-only (Minor-only, so ``--strict`` never returns 1), 2 usage. Stdlib-only.

Usage:
    python3 check_perspective_structure.py --manuscript manuscript.md \
        [--type perspective] [--out qc/perspective_structure.json] [--min-words 120] \
        [--strict] [--quiet]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from _frontmatter import strip_frontmatter

DETECTOR = "check_perspective_structure"

# v1: exact "perspective" only. Viewpoint / Comment auto-activation deferred (different genres).
PERSPECTIVE_TYPES = {"perspective"}

HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.S)
H2_RE = re.compile(r"^##(?!#)\s+(.*\S)\s*$")
FENCE_RE = re.compile(r"```.*?```", re.S)
INLINE_RE = re.compile(r"[*_`]")
CITE_RE = re.compile(r"\[@[^\]]+\]|\[\d+(?:[,–-]\d+)*\]")
WORD_RE = re.compile(r"[A-Za-z0-9']+")
NUM_PREFIX_RE = re.compile(r"^\d+(?:\.\d+)*\.?\s+")
ARTICLE_TYPE_RE = re.compile(r"(?i)^\s*article[_-]?type\s*:\s*(.+?)\s*$")

IMRAD_TOKENS = {"introduction", "methods", "materials and methods", "results", "discussion"}

# Structural / front / back-matter headings — never a content argument-section, never flagged.
STRUCTURAL_SKIP = {
    "title page", "abstract", "keywords", "key points", "key messages", "essentials",
    "summary statement", "display items", "submission notes", "references", "reference",
    "data availability", "code availability", "acknowledgements", "acknowledgments",
    "author contributions", "competing interests", "conflicts of interest", "declarations",
    "funding", "supplementary information", "additional information", "figure legends",
    "figures", "tables", "abbreviations",
}

AUTHORIAL_MOVE_RE = re.compile(
    r"\b(?:we\s+(?:argue|propose|show|contend|claim|call|advocate|introduce|present|"
    r"demonstrate|find|maintain|hold|report|suggest)|here\s+we)\b",
    re.I,
)


def blank_comments(text: str) -> str:
    """Replace ``<!-- ... -->`` blocks with equal-count newlines (line structure preserved)."""
    return HTML_COMMENT_RE.sub(lambda m: "\n" * m.group(0).count("\n"), text)


def article_type_from_frontmatter(text: str) -> str | None:
    """Single ``article_type`` value from the leading ``---``-fenced front matter (casefolded)."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for line in lines[1:]:
        if line.strip() == "---":
            break
        m = ARTICLE_TYPE_RE.match(line)
        if m:
            val = HTML_COMMENT_RE.sub("", m.group(1)).strip()
            if len(val) >= 2 and val[0] in "\"'" and val[-1] == val[0]:
                val = val[1:-1].strip()
            return val.casefold()
    return None


def normalize_heading(h: str) -> str:
    h = INLINE_RE.sub("", h).strip()
    h = NUM_PREFIX_RE.sub("", h)
    return h.strip().rstrip(".").strip().casefold()


def parse(md: str) -> dict:
    """Structural facts about the (front-matter-stripped, comment-blanked) manuscript."""
    body = blank_comments(strip_frontmatter(md))
    lines = body.splitlines()

    heads = []  # (line_index, raw, normalized)
    for i, line in enumerate(lines):
        m = H2_RE.match(line)
        if m:
            heads.append((i, m.group(1).strip(), normalize_heading(m.group(1))))

    imrad = [raw for (_, raw, norm) in heads
             if norm not in STRUCTURAL_SKIP and norm in IMRAD_TOKENS]

    abstract_idxs = [k for k, (_, _, norm) in enumerate(heads) if norm == "abstract"]
    abstract_text = None
    if abstract_idxs:
        k = abstract_idxs[0]
        start = heads[k][0] + 1
        end = heads[k + 1][0] if k + 1 < len(heads) else len(lines)
        chunk = "\n".join(lines[start:end])
        chunk = FENCE_RE.sub(" ", chunk)
        chunk = CITE_RE.sub("", chunk)
        chunk = INLINE_RE.sub("", chunk)
        abstract_text = re.sub(r"\s+", " ", chunk).strip()

    prose = []
    for line in lines:
        s = line.strip()
        if not s or s.startswith(("#", "|", ">", "!", "---")):
            continue
        if re.match(r"^\s*(?:[-*+]|\d+\.)\s", line):
            continue
        prose.append(s)
    n_words = len(WORD_RE.findall(" ".join(prose)))

    return {
        "n_words": n_words,
        "n_headings": len(heads),
        "imrad_headings": imrad,
        "abstract_section_count": len(abstract_idxs),
        "abstract_text": abstract_text,
    }


def check(md: str, front_type: str | None, cli_type: str | None, min_words: int) -> dict:
    warnings = []
    ft = front_type or None
    ct = cli_type.casefold() if cli_type else None
    if ct and ft and ct != ft:
        warnings.append(f"article_type mismatch: front-matter '{ft}' vs --type '{ct}'; using --type")
    active_type = ct or ft
    active = bool(active_type) and active_type in PERSPECTIVE_TYPES

    r = parse(md)
    findings = []
    if active and r["n_words"] >= min_words:
        if r["imrad_headings"]:
            findings.append({
                "verdict": "PERSPECTIVE_HEADING_NOT_ASSERTION",
                "severity": "Minor",
                "detail": (
                    f"{len(r['imrad_headings'])} IMRAD section heading(s) in a Perspective "
                    f"({', '.join(r['imrad_headings'])}) — published Perspectives name sections as "
                    "argument-moves, not \"Introduction / Methods / Results / Discussion\". Rename "
                    "each heading to the claim it makes; Conclusion / Summary are fine."
                ),
                "where": "; ".join(r["imrad_headings"]),
            })
        if r["abstract_text"] is not None and not AUTHORIAL_MOVE_RE.search(r["abstract_text"]):
            findings.append({
                "verdict": "PERSPECTIVE_ABSTRACT_NO_AUTHORIAL_MOVE",
                "severity": "Minor",
                "detail": (
                    "the abstract states its thesis declaratively, with no explicit authorial move "
                    "(\"we argue\" / \"we propose\" / \"here we ...\"). Eight of nine sampled npj "
                    "Digital Medicine Perspectives open the abstract with one; a report-style "
                    "abstract reads as a study, not a position. Lead the thesis with the move."
                ),
                "where": (r["abstract_text"][:70] + "...") if r["abstract_text"] else "",
            })
    if r["abstract_section_count"] > 1:
        warnings.append(f"{r['abstract_section_count']} '## Abstract' sections; evaluated the first")

    return {
        "metrics": {
            "active": active,
            "article_type": active_type,
            "body_words": r["n_words"],
            "imrad_heading_count": len(r["imrad_headings"]),
            "abstract_present": r["abstract_text"] is not None,
            "abstract_section_count": r["abstract_section_count"],
        },
        "warnings": warnings,
        "findings": findings,
    }


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Perspective structural gate — IMRAD headings + abstract authorial move (§J/§D).")
    ap.add_argument("--manuscript", required=True, help="manuscript markdown/text")
    ap.add_argument("--type", help="known article type (overrides front matter on disagreement)")
    ap.add_argument("--out", help="write JSON artifact to this path")
    ap.add_argument("--min-words", type=int, default=120,
                    help="stay silent below this many body words (default 120)")
    ap.add_argument("--strict", action="store_true",
                    help="exit 1 if any Major (none — this gate is Minor-only)")
    ap.add_argument("--quiet", action="store_true", help="suppress stdout table")
    a = ap.parse_args()

    src = Path(a.manuscript)
    if not src.is_file():
        sys.stderr.write(f"error: no such file: {src}\n")
        return 2

    raw = src.read_text(encoding="utf-8", errors="ignore")
    result = check(raw, article_type_from_frontmatter(raw), a.type, a.min_words)
    findings = result["findings"]
    m = result["metrics"]

    for w in result["warnings"]:
        sys.stderr.write(f"warning: {w}\n")

    if not a.quiet:
        print("=" * 42)
        print(" Perspective structure (§J / §D)")
        print("=" * 42)
        print("| Verdict | Severity | Detail |")
        print("|---|---|---|")
        if findings:
            for f in findings:
                print(f"| {f['verdict']} | {f['severity']} | {f['detail']} |")
            for f in findings:
                print(f"\n{f['verdict']} - {f['where']}")
        elif not m["active"]:
            print("| (none) | - | not gated as a Perspective |")
            print(f"\nOK: article_type={m['article_type']!r} is not a Perspective; no findings.")
        else:
            print("| (none) | - | Perspective structure within convention |")
            print("\nOK: argument-move headings and an abstract that carries an authorial move.")

    if a.out:
        out = Path(a.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps({
            "detector": DETECTOR,
            "manuscript": str(src),
            "metrics": m,
            "warnings": result["warnings"],
            "findings": findings,
        }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        if not a.quiet:
            print(f"\nwrote {out}")

    return 1 if (a.strict and any(f["severity"] == "Major" for f in findings)) else 0


if __name__ == "__main__":
    sys.exit(main())
