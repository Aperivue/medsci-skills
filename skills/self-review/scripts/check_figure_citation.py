#!/usr/bin/env python3
"""Orphan figure / table gate — every numbered float must be cited in the body
(self-review Phase 2.5d cross-reference).

A figure or table that has a legend/caption but is never cited in the running text
is an "orphan": a reviewer or production editor flags it, and a journal may refuse
the float. This gate cross-checks each declared "Figure N." / "Table N." caption
against at least one in-text "Figure N" / "Table N" citation elsewhere in the body.

Verdict:
  FIGURE_ORPHAN (Minor)  a figure with a caption "Figure N." has no in-text
                         "Figure N" / "Fig. N" citation anywhere outside its caption.
  TABLE_ORPHAN  (Minor)  the same for a "Table N." caption.
  FIGURE_NOT_EMBEDDED    the manuscript has figure captions but NO markdown image link
        (Minor;          (`![...](...)`) anywhere, so every figure is captioned yet
   Major w/ --require-   absent from the rendered output — the "complete" submission that
   embedded)             ships with the legends and none of the pictures. Advisory by
                         default (a drafting manuscript may keep figures as separate
                         files); --require-embedded (the submission preflight) makes it
                         Major. Conservative: fires only when ZERO images are embedded,
                         never a per-figure guess, so it stays silent once any figure is
                         embedded.

Deterministic and caption-anchored: a line beginning "Figure N." / "Table N." (with
optional **bold**) DECLARES float N; any "Figure N" / "Table N" mention on a
DIFFERENT line CITES it. A float declared but never cited elsewhere is the orphan.
This needs no section-boundary heuristic — the caption line itself is the anchor, so
a caption that happens to reference another float still counts as citing that other
float.

Exit codes: 0 clean/report-only, 1 with --strict when any Major (none — Minor only),
2 usage. Stdlib-only.

Usage:
    python3 check_figure_citation.py --manuscript manuscript.md \
        [--out qc/figure_citation.json] [--strict] [--quiet]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# A caption/legend line: (optional **) Figure|Table N (.|:) ...
CAPTION_RE = re.compile(r"^\s*\*{0,2}\s*(?P<kind>Figure|Fig\.?|Table)\s+(?P<num>\d+)\s*[.:]", re.I)
# Any in-text mention: Figure N / Fig N / Fig. N / Table N (+ "Figures 1 and 2" heads)
MENTION_RE = re.compile(r"\b(?P<kind>Figures?|Figs?\.?|Tables?)\s+(?P<num>\d+)\b", re.I)
# A markdown image embed: ![alt](path). Its presence is how a figure reaches the
# rendered output; a manuscript with figure captions but zero image links ships
# with every legend and no picture.
IMG_LINK_RE = re.compile(r"!\[[^\]]*\]\([^)]+\)")
# The author-contributions / CRediT heading.
CREDIT_HEADING_RE = re.compile(
    r"^#{1,6}\s*\*{0,2}\s*(?:Authors?[’'\s]*\s*[Cc]ontributions?|CRediT[^\n]*)\*{0,2}\s*:?\s*$",
    re.MULTILINE)


def _kind(raw: str) -> str:
    return "Table" if raw.lower().startswith("tab") else "Figure"


def check(text: str, require_embedded: bool = False) -> list[dict]:
    lines = text.splitlines()
    declared: dict[tuple[str, int], int] = {}   # (kind, num) -> caption line index
    for i, line in enumerate(lines):
        m = CAPTION_RE.match(line)
        if m:
            declared.setdefault((_kind(m.group("kind")), int(m.group("num"))), i)

    cited: set[tuple[str, int]] = set()
    for i, line in enumerate(lines):
        for m in MENTION_RE.finditer(line):
            key = (_kind(m.group("kind")), int(m.group("num")))
            # a mention on any line other than this float's own caption line = a citation
            if declared.get(key) != i:
                cited.add(key)

    claims = []
    for (kind, num), cap_line in sorted(declared.items(), key=lambda kv: (kv[0][0], kv[0][1])):
        if (kind, num) in cited:
            continue
        claims.append({
            "verdict": "TABLE_ORPHAN" if kind == "Table" else "FIGURE_ORPHAN",
            "severity": "Minor",
            "detail": (f"{kind} {num} has a caption (line {cap_line + 1}) but is never cited "
                       f"in the body; add an in-text '{kind} {num}' citation or remove the float"),
            "where": lines[cap_line].strip()[:120],
        })

    # FIGURE_NOT_EMBEDDED: captioned figures but no image link anywhere in the file.
    # Conservative on purpose (only the zero-embed case, never a per-figure guess) so
    # it stays silent whenever any figure is embedded. Tables are inline markdown, not
    # embedded images, so they are exempt.
    figures = sorted((n, ln) for (k, n), ln in declared.items() if k == "Figure")
    if figures and not IMG_LINK_RE.search(text):
        # Advisory by default: a markdown manuscript with figures kept as separate
        # attachment files legitimately embeds no image. --require-embedded (the
        # submission preflight) escalates to Major, where captions-with-no-picture
        # is the "complete package that ships with the legends and none of the
        # figures" failure.
        sev = "Major" if require_embedded else "Minor"
        for num, cap_line in figures:
            claims.append({
                "verdict": "FIGURE_NOT_EMBEDDED",
                "severity": sev,
                "detail": (f"Figure {num} is captioned (line {cap_line + 1}) but no image is embedded "
                           f"anywhere in the manuscript; confirm the figure is embedded or attached as a "
                           f"separate file before submission"),
                "where": lines[cap_line].strip()[:120],
            })

    # Author-contributions / CRediT figure-number attribution. A "prepared Figure 4"
    # attribution silently breaks when figures are renumbered or merged; the canonical
    # CRediT "Visualization" role carries no numbers and is drift-proof. Scanned ONLY
    # inside the author-contributions/CRediT section (never Results/Discussion, where
    # "Figure N" is a normal citation).
    cm = CREDIT_HEADING_RE.search(text)
    if cm:
        start = cm.end()
        nxt = re.search(r"^#{1,6}\s", text[start:], re.MULTILINE)
        region = text[start: start + nxt.start()] if nxt else text[start:]
        declared_fignums = {n for (k, n) in declared if k == "Figure"}
        fig_tokens = [int(m.group("num")) for m in MENTION_RE.finditer(region)
                      if _kind(m.group("kind")) == "Figure"]
        if fig_tokens:
            claims.append({
                "verdict": "AUTHOR_CONTRIB_FIGURE_REF",
                "severity": "Minor",
                "detail": ("the author-contributions/CRediT section attributes work by figure number "
                           "(e.g. 'prepared Figure N'); this attribution breaks on any figure renumber or "
                           "merge — use the CRediT 'Visualization' role, which carries no figure numbers"),
                "where": "author contributions",
            })
            for num in sorted(set(fig_tokens)):
                if num not in declared_fignums:
                    claims.append({
                        "verdict": "FIGURE_ATTR_STALE",
                        "severity": "Major",
                        "detail": (f"the author-contributions/CRediT section attributes Figure {num}, but no "
                                   f"Figure {num} is declared in the manuscript — a stale attribution left by a "
                                   f"figure renumber/merge (declared figures: "
                                   f"{', '.join(str(n) for n in sorted(declared_fignums)) or 'none'})"),
                        "where": "author contributions",
                    })
    return claims


def analyze(manuscript: str, require_embedded: bool = False) -> dict:
    p = Path(manuscript)
    if not p.is_file():
        sys.stderr.write(f"ERROR: manuscript not found: {manuscript}\n")
        sys.exit(2)
    claims = check(p.read_text(encoding="utf-8"), require_embedded=require_embedded)
    n_major = sum(1 for c in claims if c["severity"] == "Major")
    return {
        "manuscript": str(p),
        "claims": claims,
        "summary": {
            "n_claims": len(claims),
            "n_major": n_major,
            "n_flag": len(claims) - n_major,
            "verdict": "MAJOR_CANDIDATE" if n_major else ("REVIEW" if claims else "OK"),
        },
    }


def render(result: dict) -> str:
    lines = ["| Check | Severity | Detail |", "|---|---|---|"]
    for c in result["claims"]:
        lines.append(f"| {c['verdict']} | {c['severity']} | {c['detail']} |")
    if len(lines) == 2:
        lines.append("| (none) | — | every captioned figure/table is cited in the body |")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Orphan figure/table gate — captioned floats must be cited (Phase 2.5d).")
    ap.add_argument("--manuscript", required=True, help="manuscript markdown/text")
    ap.add_argument("--out", help="write JSON artifact to this path")
    ap.add_argument("--strict", action="store_true",
                    help="exit 1 if any Major (a captioned figure with no embedded image under --require-embedded)")
    ap.add_argument("--require-embedded", action="store_true",
                    help="submission context: escalate FIGURE_NOT_EMBEDDED to Major (figures must be "
                         "embedded in the manuscript, not kept as separate files)")
    ap.add_argument("--quiet", action="store_true", help="suppress stdout table")
    args = ap.parse_args()

    result = analyze(args.manuscript, require_embedded=args.require_embedded)

    if not args.quiet:
        print("=" * 44)
        print(" Orphan figure / table citation (§2.5d)")
        print("=" * 44)
        print(render(result))
        print()
        s = result["summary"]
        if s["n_major"]:
            print(f"MAJOR: {s['n_major']} figure(s) captioned but not embedded; {s['n_flag']} orphan float(s).")
        elif s["n_flag"]:
            print(f"REVIEW: {s['n_flag']} orphan float(s).")
        else:
            print("OK: every captioned float is cited and embedded.")

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps({"detector": "check_figure_citation", **result}, indent=2), encoding="utf-8")
        if not args.quiet:
            print(f"\nwrote {args.out}")

    return 1 if (args.strict and result["summary"]["n_major"]) else 0


if __name__ == "__main__":
    sys.exit(main())
