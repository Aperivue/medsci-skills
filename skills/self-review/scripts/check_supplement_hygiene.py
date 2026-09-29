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
  SUPP_PARTICIPANT_PII_TIE a reader/participant identity (pseudonym R+hex, or a named
                         participant) tied to an INDIVIDUAL response on one line — a
                         re-identifiable datum in a reader-facing/public supplement. A
                         byline/roster without individual responses does not fire.
  SUPP_XREF_UNRESOLVED   (needs --manuscript) a body "Supplementary Table/Figure/
                         Material N" callout — or an S-prefixed / plural / range form
                         ("Table S4", "Supplementary Figures S2 and S3", "Figs S1–S3") —
                         with no matching supplement section. Tables and figures are
                         matched by kind: a "Table S2" does not resolve a cited "Figure S2".

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

# Participant-privacy tie: a reader/participant IDENTITY on the same line as an
# INDIVIDUAL-RESPONSE datum re-identifies that person's answers in a reader-facing /
# public supplement. Identity = a reader pseudonym token (R + hex) OR a proper "First
# Last" name accompanied by a participant word on the line. Response datum = an
# explicit per-trial answer. A byline / roster line (a name with NO individual
# response) is legitimate and must NOT fire.
READER_PSEUDONYM = re.compile(r"\bR[0-9a-f]{5,}\b")
PROPER_NAME = re.compile(r"\b[A-Z][a-z]+(?:\s+[A-Z]\.?)?\s+[A-Z][a-z]+\b")
PARTICIPANT_WORD = re.compile(r"\b(?:reader|participant|rater|observer|respondent|subject)\b", re.I)
RESPONSE_DATUM = re.compile(
    r"\bresponse\s*[=:]|\bconfidence\s*[=:]|\bcue\s*[=:]|\btrial\s+\d+\b"
    r"|\brated\s+(?:it|this|the\s+\w+)\b|\banswered\s+(?:real|fake|ai|synthetic)\b"
    r"|\bresponse\s+(?:was\s+)?(?:real|fake|ai|synthetic|authentic)\b",
    re.IGNORECASE)


def lint_pii_tie(path: Path) -> list[dict]:
    """Flag a line that ties a reader identity to an individual response (de-anon)."""
    claims: list[dict] = []
    text = path.read_text(encoding="utf-8", errors="replace")
    for i, line in enumerate(text.splitlines(), 1):
        if not RESPONSE_DATUM.search(line):
            continue
        has_pseudonym = READER_PSEUDONYM.search(line)
        has_named = PROPER_NAME.search(line) and PARTICIPANT_WORD.search(line)
        if not (has_pseudonym or has_named):
            continue
        who = "a reader pseudonym" if has_pseudonym else "a named participant"
        claims.append({
            "verdict": "SUPP_PARTICIPANT_PII_TIE",
            "severity": "Major",
            "detail": (f"{who} is tied to an individual response on one line in {path.name} — "
                       f"a re-identifiable participant-level datum in a reader-facing supplement; "
                       f"de-identify (a byline/roster without individual responses is fine)"),
            "where": f"{path.name}:{i}: …{line.strip()[:110]}…",
        })
        break  # one per file
    return claims


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
    claims.extend(lint_pii_tie(path))
    return claims


# --- body ↔ supplement cross-reference resolution --------------------------

# A body callout like "Supplementary Table 3", "Supplementary Figure 2",
# "Supplementary Material 5", "Supplementary Methods 1", "Supplementary Appendix 4" —
# and the forms people actually write for figures and tables: S-prefixed ("Table S4",
# "Fig. S1"), plural lists ("Supplementary Figures S2 and S3") and ranges ("Figs S1–S3").
# The S-prefixed and plural forms used to match nothing, so a cited-but-absent
# supplementary figure passed. A bare S-prefixed callout needs no "Supplementary"
# (the S is the supplement marker); a main-text "Figure 2" / "Tables 1-3" never matches.
_NUMTAIL = r"(?:\s*(?:,|&|–|—|-|and|to|through)\s*S?\d{1,3}[a-z]?)*"
BODY_CALLOUT = re.compile(
    # "Supplementary Figures S2 and S3", "Supplementary Tables 1-3"
    r"Supplementary\s+(?P<pk>Tables|Figures|Figs\.?|Materials|Notes)\s+"
    r"(?P<plist>S?\d{1,3}[a-z]?" + _NUMTAIL + r")"
    # "Supplementary Table 3", "Supplementary Fig. S2", "Supplementary Material 5"
    r"|Supplementary\s+(?P<k>Table|Figure|Fig\.?|Material|Methods?|Appendix|Data|Note)\s+"
    r"S?(?P<n>\d{1,3})(?!\d)"
    # "Figs S1–S3", "Tables S2 and S4" (the S marks the supplement)
    r"|(?<![A-Za-z])(?P<spk>Tables|Figures|Figs\.?)\s+(?P<splist>S\d{1,3}[a-z]?" + _NUMTAIL + r")"
    # "Table S4", "Fig. S1"
    r"|(?<![A-Za-z])(?P<sk>Table|Figure|Fig\.?)\s+S(?P<sn>\d{1,3})(?!\d)",
    re.IGNORECASE)

# One token of a callout number list, with an optional range tail ("S1–S3" = S1, S2, S3).
_NUM_TOKEN = re.compile(r"S?(\d{1,3})[a-z]?(?:\s*(?:[–—-]|to|through)\s*S?(\d{1,3})[a-z]?)?",
                        re.IGNORECASE)

_KIND_WORDS = (r"Tables?|Figures?|Figs?\.?|Materials?|Methods?|Appendix|Appendices"
               r"|Sections?|Data|Notes?")
# A supplement section identity: a heading naming a kind + number ("## Supplementary
# Figure S2. ..."), a heading with only a bare S-number ("## S3. ..."), or a caption
# definition line ("Figure S2. ..." / "**Table S4.** ...") as a captions file carries it.
_HEADING = re.compile(r"^#{1,4}\s")
_KINDED = re.compile(r"\b(?:Supplementary\s+)?(" + _KIND_WORDS + r")\s+S?(\d{1,3})[a-z]?\b",
                     re.IGNORECASE)
_BARE_S = re.compile(r"\bS(\d{1,3})[a-z]?\b")
_CAPTION_DEF = re.compile(
    r"^\s*(?:\*\*)?\s*(?:Supplementary\s+)?(Table|Figure|Fig\.?)\s+S?(\d{1,3})[a-z]?"
    r"\s*(?:\*\*)?\s*[.:|]", re.IGNORECASE)


def _kind_of(word: str, generic: str = "other") -> str:
    """table / figure, or ``generic`` for a container (Material, Methods, Appendix...)."""
    w = word.lower()
    if w.startswith("tab"):
        return "table"
    if w.startswith("fig"):
        return "figure"
    return generic


def _label_of(word: str) -> str:
    w = word.rstrip(".").lower()
    if w.startswith("tab"):
        return "Table"
    if w.startswith("fig"):
        return "Figure"
    return {"materials": "Material", "notes": "Note"}.get(w, w.title())


def _numbers_in(numlist: str) -> list[int]:
    out: list[int] = []
    for m in _NUM_TOKEN.finditer(numlist):
        a = int(m.group(1))
        b = int(m.group(2)) if m.group(2) else None
        if b is not None and b >= a:
            out.extend(range(a, b + 1))
        else:
            out.append(a)
            if b is not None:
                out.append(b)
    return out


def supplement_sections(texts: list[str]) -> set[tuple[str, int]]:
    """(kind, number) of every supplement section. kind is table / figure, or 'any' for a
    section that cannot be typed (a generic container such as "Supplementary Material 2",
    or a heading carrying only a bare S-number)."""
    present: set[tuple[str, int]] = set()
    for t in texts:
        for line in t.splitlines():
            if _HEADING.match(line):
                kinded = list(_KINDED.finditer(line))
                if kinded:
                    for m in kinded:
                        present.add((_kind_of(m.group(1), "any"), int(m.group(2))))
                else:
                    for m in _BARE_S.finditer(line):
                        present.add(("any", int(m.group(1))))
                continue
            m = _CAPTION_DEF.match(line)
            if m:
                present.add((_kind_of(m.group(1)), int(m.group(2))))
    return present


def _resolves(kind: str, num: int, present: set[tuple[str, int]]) -> bool:
    if (kind, num) in present or ("any", num) in present:
        return True
    # A generic container callout ("Supplementary Material 5") resolves against any
    # section with that number; a Table / Figure callout needs a Table / Figure (or
    # untyped) section — a "Table S2" no longer stands in for a cited "Figure S2".
    return kind == "other" and any(n == num for _, n in present)


def check_xref(manuscript_text: str, supplement_texts: list[str]) -> list[dict]:
    claims: list[dict] = []
    present = supplement_sections(supplement_texts)
    seen: set[tuple[str, int]] = set()
    for m in BODY_CALLOUT.finditer(manuscript_text):
        if m.group("pk") or m.group("spk"):
            word = m.group("pk") or m.group("spk")
            nums = _numbers_in(m.group("plist") or m.group("splist"))
        else:
            word = m.group("k") or m.group("sk")
            nums = [int(m.group("n") or m.group("sn"))]
        kind = _kind_of(word)
        label = _label_of(word)
        for num in nums:
            key = (label, num)
            if key in seen:
                continue
            seen.add(key)
            if not _resolves(kind, num, present):
                ln = _line_of(manuscript_text, m.start())
                what = (f"supplementary {label.lower()}" if kind != "other"
                        else "supplement section")
                claims.append({
                    "verdict": "SUPP_XREF_UNRESOLVED",
                    "severity": "Major",
                    "detail": (f"body cites 'Supplementary {label} {num}' but no {what} "
                               f"numbered {num} was found (renumber drift, a table/figure "
                               f"mix-up, or a silently-skipped/unrendered section)"),
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
        Path(args.out).write_text(json.dumps({"detector": "check_supplement_hygiene", **result}, indent=2), encoding="utf-8")
        if not args.quiet:
            print(f"\nwrote {args.out}")

    return 1 if (args.strict and result["summary"]["n_major"]) else 0


if __name__ == "__main__":
    sys.exit(main())
