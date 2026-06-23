#!/usr/bin/env python3
"""Reader-facing supplement / tables / caption hygiene gate (self-review §J supplement pass).

Existing classical-style and scope gates lint `manuscript.md` ONLY; the rendered
supplement, a separately-built tables file, and figure-caption files are never
linted — yet those are the artifacts where technical-check-fatal residue hides
(internal SAP labels, unfilled placeholders, build markers, response-letter
framing, and body↔supplement cross-reference numbers that do not resolve). This
detector lints a LIST of rendered submission artifacts for that residue and, when
given the manuscript body, checks that every "Supplementary X N" callout resolves
to a supplement section.

Verdicts (all Major — each reaches a reviewer/editor as a non-anonymous slip):
  SUPP_INTERNAL_LABEL    a § / §L internal section or SAP label (§L0, §L10b, "see
                         Methods §3") in a reader-facing file — internal scaffolding.
  SUPP_PLACEHOLDER       an unfilled placeholder: "Supplementary Table SX", "Table
                         S?", "Figure S-N", a literal "S-N"/"TABLE N", "[Authors]",
                         a figure-path brace-glob (figS_*.{png,pdf}), or an internal
                         build-dir path (1_Search/, 4_Analysis/, 5_Figures/).
  SUPP_BUILD_MARKER      a build/QA marker that should never ship: "[VERIFY…]",
                         "TODO", "FIXME", "XXXX", "Remove this line if…".
  SUPP_RESPONSE_FRAMING  response-to-reviewers framing in a reader-facing supplement:
                         "Per Section Editor #2", "Per Reviewer 2 #3", "Response to
                         Reviewer", "Reviewer 2 Comment 4".
  SUPP_PLANNING_RESIDUE  pre-execution planning residue: "Designed by:", "Expected
                         PRISMA Numbers", "Deduplication Plan", "to be executed/run".
  SUPP_XREF_UNRESOLVED   (needs --manuscript) a body "Supplementary Table/Figure/
                         Material N" callout with no matching supplement section.

Exit codes: 0 clean (or report-only), 1 with --strict when any Major exists, 2 usage.
Stdlib-only (json / re / argparse / pathlib).

Usage:
    python3 check_supplement_hygiene.py --supplement supplement.md [--supplement tables.md ...] \
        [--manuscript manuscript.md] [--out qc/supplement_hygiene.json] [--strict] [--quiet]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# --- residue patterns (per reader-facing file) -----------------------------

# § anywhere, or a §-less "§L" SAP label, or a "see Methods §3" cross-ref. In a
# reader-facing supplement any of these is internal scaffolding (manuscript-style
# bans § outright); we report per file with a count.
INTERNAL_LABEL = re.compile(r"§")

# Unfilled placeholders. Literal letter N/X (not a digit) after a table/figure
# label, "S?"/"SX"/"S-N" tokens, an author placeholder, a figure-path brace-glob,
# and internal build-dir paths.
PLACEHOLDER = re.compile(
    r"\b(?:Supplementary\s+)?(?:Table|Figure|Fig\.?|Appendix)\s+S?[NX]\b"  # Table SX / Figure N
    r"|\bS-?[NX]\b"                                                         # S-N / SN (letter)
    r"|\bS\?\b"                                                             # S?
    r"|\bTABLE\s+[NX]\b|\bFIGURE\s+[NX]\b"                                  # TABLE N
    r"|\[\s*Authors?\s*\]|\[\s*Author names?\s*\]"                          # [Authors]
    r"|[\w/]*\bfig\w*_\*\.\{[^}]*\}"                                        # figS_*.{png,pdf}
    r"|\*\.\{(?:png|pdf|jpe?g|tiff?|svg)[^}]*\}"                            # *.{png,pdf}
    r"|(?<![\w/])(?:0_|1_|2_|3_|4_|5_|6_)[A-Za-z][\w]*/",                   # 1_Search/ 5_Figures/
    re.IGNORECASE)

BUILD_MARKER = re.compile(
    r"\[\s*VERIFY[^\]]*\]|\bTODO\b|\bFIXME\b|\bXXXX+\b|\bTBD\b"
    r"|Remove this line if|placeholder text|<!--\s*(?:TODO|note|draft)",
    re.IGNORECASE)

RESPONSE_FRAMING = re.compile(
    r"\bPer\s+(?:Section\s+Editor|Reviewer|Editor)\s*#?\s*\d"
    r"|\bResponse\s+to\s+(?:the\s+)?Reviewers?\b"
    r"|\bReviewer\s+\d+\s*(?:Comment|#|,\s*(?:comment|point))"
    r"|\bin\s+response\s+to\s+(?:Reviewer|the\s+Editor|comment)\b",
    re.IGNORECASE)

PLANNING_RESIDUE = re.compile(
    r"\bDesigned\s+by\s*:|\bExpected\s+[\w\s]{0,30}\bNumbers\b"
    r"|\bDeduplication\s+Plan\b|\bSearch\s+Plan\b|\bAnalysis\s+Plan\s*:"
    r"|\bto\s+be\s+(?:executed|run|determined|finalized|completed)\b"
    r"|\bawaiting\s+(?:data|results|execution)\b",
    re.IGNORECASE)

PER_FILE_CHECKS = [
    ("SUPP_INTERNAL_LABEL", INTERNAL_LABEL,
     "a § / §L internal section or SAP label leaked into a reader-facing file"),
    ("SUPP_PLACEHOLDER", PLACEHOLDER,
     "an unfilled placeholder (S?/SX/S-N, [Authors], figure-path glob, or build-dir path)"),
    ("SUPP_BUILD_MARKER", BUILD_MARKER,
     "a build/QA marker that should not ship ([VERIFY]/TODO/FIXME/XXXX/'Remove this line if')"),
    ("SUPP_RESPONSE_FRAMING", RESPONSE_FRAMING,
     "response-to-reviewers framing in a reader-facing supplement"),
    ("SUPP_PLANNING_RESIDUE", PLANNING_RESIDUE,
     "pre-execution planning residue (Designed by:/Expected … Numbers/to be executed)"),
]


def _line_of(text: str, pos: int) -> int:
    return text[:pos].count("\n") + 1


def lint_file(path: Path) -> list[dict]:
    claims: list[dict] = []
    text = path.read_text(encoding="utf-8", errors="replace")
    for verdict, rx, detail in PER_FILE_CHECKS:
        m = rx.search(text)
        if not m:
            continue
        n = len(rx.findall(text))
        ln = _line_of(text, m.start())
        snippet = text[max(0, m.start() - 25):m.end() + 35].replace("\n", " ").strip()
        claims.append({
            "verdict": verdict,
            "severity": "Major",
            "detail": f"{detail} — {n} occurrence(s) in {path.name}",
            "where": f"{path.name}:{ln}: …{snippet[:120]}…",
        })
    return claims


# --- body ↔ supplement cross-reference resolution --------------------------

# A body callout like "Supplementary Table 3", "Supplementary Figure 2",
# "Supplementary Material 5", "Supplementary Methods 1", "Supplementary Appendix 4".
BODY_CALLOUT = re.compile(
    r"Supplementary\s+(Table|Figure|Fig\.?|Material|Methods?|Appendix|Data|Note)\s+(\d{1,3})\b",
    re.IGNORECASE)

# A supplement section identity: a heading that ends in / contains a number, or an
# explicit "Supplementary Table/Material N" / "Table SN" title line.
SUPP_SECTION = re.compile(
    r"^#{1,4}\s.*?\b(?:Supplementary\s+)?(?:Table|Figure|Material|Methods?|Appendix|Section|Data|Note)\s+S?(\d{1,3})\b"
    r"|^#{1,4}\s.*?\bS(\d{1,3})\b",
    re.IGNORECASE | re.MULTILINE)


def supplement_section_numbers(texts: list[str]) -> set[int]:
    nums: set[int] = set()
    for t in texts:
        for m in SUPP_SECTION.finditer(t):
            g = m.group(1) or m.group(2)
            if g:
                nums.add(int(g))
    return nums


def check_xref(manuscript_text: str, supplement_texts: list[str]) -> list[dict]:
    claims: list[dict] = []
    present = supplement_section_numbers(supplement_texts)
    seen: set[tuple[str, int]] = set()
    for m in BODY_CALLOUT.finditer(manuscript_text):
        kind = m.group(1).rstrip(".").title()
        num = int(m.group(2))
        key = (kind, num)
        if key in seen:
            continue
        seen.add(key)
        if num not in present:
            ln = _line_of(manuscript_text, m.start())
            claims.append({
                "verdict": "SUPP_XREF_UNRESOLVED",
                "severity": "Major",
                "detail": (f"body cites 'Supplementary {kind} {num}' but no supplement "
                           f"section numbered {num} was found (renumber drift or a "
                           f"silently-skipped/unrendered section)"),
                "where": f"manuscript:{ln}",
            })
    return claims


def analyze(supplements: list[str], manuscript: str | None) -> dict:
    supp_paths = []
    supp_texts = []
    claims: list[dict] = []
    for s in supplements:
        p = Path(s)
        if not p.is_file():
            sys.stderr.write(f"ERROR: supplement not found: {s}\n")
            sys.exit(2)
        supp_paths.append(p)
        supp_texts.append(p.read_text(encoding="utf-8", errors="replace"))
        claims.extend(lint_file(p))

    if manuscript:
        mp = Path(manuscript)
        if not mp.is_file():
            sys.stderr.write(f"ERROR: manuscript not found: {manuscript}\n")
            sys.exit(2)
        claims.extend(check_xref(mp.read_text(encoding="utf-8", errors="replace"), supp_texts))

    n_major = sum(1 for c in claims if c["severity"] == "Major")
    return {
        "supplements": [str(p) for p in supp_paths],
        "manuscript": manuscript,
        "claims": claims,
        "summary": {
            "n_claims": len(claims),
            "n_major": n_major,
            "n_flag": len(claims) - n_major,
            "verdict": "MAJOR_CANDIDATE" if n_major else "OK",
        },
    }


def render(result: dict) -> str:
    lines = ["| Check | Severity | Detail |", "|---|---|---|"]
    for c in result["claims"]:
        lines.append(f"| {c['verdict']} | {c['severity']} | {c['detail']} |")
    if len(lines) == 2:
        lines.append("| (none) | — | supplement / tables / caption files are reader-clean |")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Reader-facing supplement / tables / caption hygiene gate.")
    ap.add_argument("--supplement", action="append", default=[], metavar="PATH",
                    help="a rendered reader-facing file to lint (repeatable: supplement, tables, captions)")
    ap.add_argument("--manuscript", help="manuscript body (for Supplementary-X-N cross-ref resolution)")
    ap.add_argument("--out", help="write JSON artifact to this path")
    ap.add_argument("--strict", action="store_true", help="exit 1 if any Major claim exists")
    ap.add_argument("--quiet", action="store_true", help="suppress stdout table")
    args = ap.parse_args()

    if not args.supplement:
        sys.stderr.write("ERROR: at least one --supplement file is required\n")
        return 2

    result = analyze(args.supplement, args.manuscript)

    if not args.quiet:
        print("=" * 41)
        print(" Supplement Hygiene (§J supplement pass)")
        print("=" * 41)
        print(render(result))
        print()
        s = result["summary"]
        if s["n_major"]:
            print(f"MAJOR candidate: {s['n_major']} reader-facing supplement residue issue(s).")
        else:
            print("OK: supplement / tables / caption files are reader-clean.")

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(result, indent=2), encoding="utf-8")
        if not args.quiet:
            print(f"\nwrote {args.out}")

    return 1 if (args.strict and result["summary"]["n_major"]) else 0


if __name__ == "__main__":
    sys.exit(main())
