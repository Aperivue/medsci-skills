#!/usr/bin/env python3
"""Float citation-ORDER gate (journal technical-check pass).

Journals (KJR, Radiology, AJR, and most others) require that numbered floats be
**cited in ascending order of first appearance** in the narrative text, evaluated
per series independently:

    main Tables   (Table 1, 2, 3, …)
    main Figures  (Figure 1, 2, 3, …)
    Suppl. Tables (Table S1, S2, … / Supplementary Table S1, …)
    Suppl. Figures(Supplementary Figure S1, … / Figure S1, …)

This is a deterministic, pre-peer-review desk/technical-check item: editorial
offices "unsubmit" manuscripts for it before a reviewer ever sees them. Existing
self-review gates lint xref *resolution* (does the callout resolve to a section)
but never *order*.

What it does: scans the NARRATIVE body (everything before the first float-definition
/ back-matter section header — Figure Legends, Tables, Supplementary, References —
so a legends block that lists figures in order does not mask an out-of-order body),
extracts the first-citation position of every numbered float per series, and flags
any series whose first-appearance number sequence is not ascending.

Verdicts:
  CITATION_ORDER (Major)  a series is cited out of numerical order (e.g., Table 3
                          first-cited before Table 1, or Suppl. Tables cited
                          S4, S9, S16, S12, …). Technical-check-fatal.
  CITATION_GAP  (Minor)   a series' cited numbers are not contiguous from 1
                          (a possible missing / mis-numbered float). Report-only.
  DANGLING_SECTION_XREF   an in-text "Section N" / "Section N.M" reference has no
        (Major)           matching numbered heading — the common case being a
                          journal that typesets UNNUMBERED headings, where every
                          such reference dangles at production. Name the heading
                          instead of a number. ("Supplementary/Appendix Section N"
                          is exempt — it points at the supplement.)

Fix: renumber the series by first-citation order (and reorder the float/supplement
document + remap ALL cross-references, expanding ranges like "S12–S15" by hand and
leaving non-float "S1–S6" sensitivity-spec labels untouched), or rephrase to remove
the early out-of-order citation. See ~/.claude/rules/journal-technical-check-gate.md.

INPUT
  --manuscript  manuscript markdown/text (required).
  --include-back-matter  also scan back-matter sections (legends/refs) — off by default.

OUTPUT
  stdout table and, with --out, a JSON artifact {manuscript, claims[], summary}.

Stdlib-only (re / json / argparse / pathlib). Exit codes: 0 clean (or report-only),
1 Major claim(s) found (with --strict), 2 input/usage error.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# A back-matter / float-definition section header. Everything from the first such
# header onward is excluded from the body citation-order scan (legends list floats
# in order by construction; references are not citations).
BACK_MATTER_RE = re.compile(
    r"(?im)^#{1,6}\s*\**\s*"
    r"(figure\s+legends?|figure\s+captions?|table\s+legends?|table\s+captions?|"
    r"tables?|supplementary|supplement|references|bibliography)\b")

# A "Table(s)/Figure(s) <numlist>" mention. numlist = S?<digits> tokens joined by
# comma / ampersand / en-dash / hyphen / "and". Captures the kind word + the list.
MENTION_RE = re.compile(
    r"\b(Tables?|Figures?)\s+"
    r"(S?\d+(?:\s*(?:,|&|–|-|and)\s*S?\d+)*)", re.IGNORECASE)

# Individual S?<number> token inside a numlist.
TOKEN_RE = re.compile(r"(S?)(\d+)", re.IGNORECASE)

SERIES_LABEL = {
    ("table", False): "Table",
    ("figure", False): "Figure",
    ("table", True): "Supplementary Table",
    ("figure", True): "Supplementary Figure",
}

# In-text reference to a numbered section ("as reported in Section 3.4"). Many
# medical journals typeset UNNUMBERED headings (house style), so a "Section N"
# cross-reference written during drafting dangles at production — a deterministic
# desk/galley flag the float-order check does not cover.
SECTION_REF_RE = re.compile(r"\bSection\s+(\d+(?:\.\d+)?)\b")
# A heading that carries a leading number: "## 3 Results", "### 3.4 Foo".
NUMBERED_HEADING_RE = re.compile(r"^#{1,6}\s+\*{0,2}\s*(\d+(?:\.\d+)*)\b", re.MULTILINE)


def _check_section_xref(body: str) -> list[dict]:
    """A `Section N` / `Section N.M` reference must resolve to a numbered heading.
    If the manuscript has no numbered headings at all (the common unnumbered-house-
    style case), every such reference dangles at typeset."""
    refs: list[str] = []
    for m in SECTION_REF_RE.finditer(body):
        pre = body[max(0, m.start() - 18):m.start()].lower()
        if "supplement" in pre or "appendix" in pre:
            continue  # "Supplementary Section 3" points at the supplement, not a body section
        refs.append(m.group(1))
    if not refs:
        return []
    heading_nums = set(NUMBERED_HEADING_RE.findall(body))
    dangling = [r for r in dict.fromkeys(refs)
                if not any(h == r or h.startswith(r + ".") for h in heading_nums)]
    if not dangling:
        return []
    refs_str = ", ".join(f"Section {d}" for d in dangling)
    if not heading_nums:
        detail = (f"in-text cross-reference(s) to numbered sections ({refs_str}) but the manuscript "
                  f"has no numbered headings — every 'Section N' reference dangles at typeset "
                  f"(unnumbered-heading house style); name the heading (e.g. 'the Sensitivity analyses "
                  f"section') instead of a number")
    else:
        detail = (f"{refs_str} has no matching numbered heading "
                  f"(numbered headings present: {', '.join(sorted(heading_nums))}); "
                  f"name the heading or correct the number")
    return [{
        "verdict": "DANGLING_SECTION_XREF",
        "severity": "Major",
        "detail": detail,
        "where": refs_str[:160],
    }]


def _body(text: str, include_back_matter: bool) -> str:
    if include_back_matter:
        return text
    m = BACK_MATTER_RE.search(text)
    return text[: m.start()] if m else text


def _first_appearance(text: str):
    """Return {series_label: [numbers in order of first appearance]} for the body."""
    seen: dict[str, dict[int, int]] = {}  # label -> {number: first_position}
    for m in MENTION_RE.finditer(text):
        kind = "table" if m.group(1).lower().startswith("table") else "figure"
        for tm in TOKEN_RE.finditer(m.group(2)):
            supp = bool(tm.group(1))
            num = int(tm.group(2))
            label = SERIES_LABEL[(kind, supp)]
            seen.setdefault(label, {})
            # keep the EARLIEST position for each number
            pos = m.start() + tm.start()
            if num not in seen[label] or pos < seen[label][num]:
                seen[label][num] = pos
    order = {}
    for label, num_pos in seen.items():
        order[label] = [n for n, _ in sorted(num_pos.items(), key=lambda kv: kv[1])]
    return order


def check(text: str, include_back_matter: bool) -> list[dict]:
    claims = []
    body = _body(text, include_back_matter)
    claims += _check_section_xref(body)
    order = _first_appearance(body)
    for label in ("Table", "Figure", "Supplementary Table", "Supplementary Figure"):
        seq = order.get(label)
        if not seq or len(seq) < 2:
            continue
        prefix = "S" if label.startswith("Supplementary") else ""
        pretty = ", ".join(f"{prefix}{n}" for n in seq)
        # ORDER: first-appearance sequence must be ascending.
        if seq != sorted(seq):
            # locate the first inversion for a precise message
            inv = next((seq[i] for i in range(1, len(seq)) if seq[i] < seq[i - 1]), seq[-1])
            claims.append({
                "verdict": "CITATION_ORDER",
                "severity": "Major",
                "detail": (f"{label}s are cited out of numerical order — first-citation "
                           f"sequence is {pretty}; renumber by first-citation order or "
                           f"rephrase (first inversion at {prefix}{inv})"),
                "where": f"{label} series",
            })
        else:
            # GAP (Minor) only when order is otherwise fine, to avoid double-flagging.
            expected = list(range(1, max(seq) + 1))
            if seq != expected:
                missing = [f"{prefix}{n}" for n in expected if n not in seq]
                claims.append({
                    "verdict": "CITATION_GAP",
                    "severity": "Minor",
                    "detail": (f"{label}s cited {pretty} are not contiguous from 1 "
                               f"(not cited in body: {', '.join(missing)}) — check for a "
                               f"missing or mis-numbered float"),
                    "where": f"{label} series",
                })
    return claims


def analyze(manuscript: str, include_back_matter: bool) -> dict:
    p = Path(manuscript)
    if not p.is_file():
        sys.stderr.write(f"ERROR: manuscript not found: {manuscript}\n")
        sys.exit(2)
    claims = check(p.read_text(encoding="utf-8"), include_back_matter)
    n_major = sum(1 for c in claims if c["severity"] == "Major")
    n_minor = sum(1 for c in claims if c["severity"] == "Minor")
    return {
        "manuscript": str(p),
        "claims": claims,
        "summary": {
            "n_claims": len(claims),
            "n_major": n_major,
            "n_minor": n_minor,
            "verdict": "MAJOR_CANDIDATE" if n_major else "OK",
        },
    }


def render(result: dict) -> str:
    lines = ["| Check | Severity | Detail |", "|---|---|---|"]
    for c in result["claims"]:
        lines.append(f"| {c['verdict']} | {c['severity']} | {c['detail']} |")
    if len(lines) == 2:
        lines.append("| (none) | — | all float series cited in ascending order |")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Float citation-order gate (technical-check pass).")
    ap.add_argument("--manuscript", required=True, help="manuscript markdown/text")
    ap.add_argument("--include-back-matter", action="store_true",
                    help="also scan legends/references back-matter (off by default)")
    ap.add_argument("--out", help="write JSON artifact to this path")
    ap.add_argument("--strict", action="store_true", help="exit 1 if any Major claim exists")
    ap.add_argument("--quiet", action="store_true", help="suppress stdout table")
    args = ap.parse_args()

    result = analyze(args.manuscript, args.include_back_matter)
    if not args.quiet:
        print("=" * 41)
        print(" Float Citation Order")
        print("=" * 41)
        print(render(result))
        print()
        s = result["summary"]
        print(f"MAJOR candidate: {s['n_major']} out-of-order series." if s["n_major"]
              else "OK: every float series is cited in ascending order.")

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps({"detector": "check_citation_order", **result}, indent=2), encoding="utf-8")
        if not args.quiet:
            print(f"\nwrote {args.out}")

    return 1 if (args.strict and result["summary"]["n_major"]) else 0


if __name__ == "__main__":
    sys.exit(main())
