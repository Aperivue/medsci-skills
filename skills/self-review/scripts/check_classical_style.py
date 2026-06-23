#!/usr/bin/env python3
"""Classical-style body lint (self-review §J / write-paper Phase 7.1).

A senior meta-analysis reviewer reads several surface signals as "AI wrote this"
or as a policy violation. They are all deterministic greps, so they belong in a
gate rather than a prose checklist (manuscript-style-classical.md §5/§6/§7/§8):

  SECTION_SYMBOL        (Major) the § symbol anywhere in the body — the canonical
                        AI tell; also catches "see Methods §2" self-references.
  INBODY_AI_DISCLOSURE  (Major) an AI/LLM-use disclosure paragraph in the body
                        ("Generative AI was not used", "During the preparation of
                        this manuscript the authors used …"). For a classical /
                        senior-MA target this belongs on the title page, not the body.
  ELIGIBILITY_PROSE     (Minor) eligibility/inclusion criteria written as a prose
                        sentence rather than a numbered list.
  DECIMAL_INCONSISTENCY (Minor) OR/HR/RR reported with mixed decimal places (some
                        2 dp, some 3 dp) in the same manuscript.
  EM_DASH_OVERUSE       (Minor) more than 25 *prose* em-dashes — a generation tell.
                        Structural dashes (markdown table cells incl. "—" N/A
                        placeholders and panel-label captions, ORCID separators,
                        author/affiliation lines) are excluded and reported
                        separately, so a cohort manuscript with large baseline
                        tables is not pushed into destructive edits on correct
                        table dashes.

INPUTS
  --manuscript   manuscript markdown/text (required).
  --em-dash-max  em-dash threshold (default 25).

OUTPUT
  A reconciliation table (stdout) and, with --out, a JSON artifact:
    {manuscript, claims[{verdict, severity, detail, where}], summary}
  Exit 1 (with --strict) when any Major-severity claim exists (§ symbol or in-body
  AI disclosure).

Stdlib-only (json / re / argparse / pathlib). Exit codes: 0 clean (or report-only),
1 Major claim(s) found (with --strict), 2 input/usage error.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# The § AI-tell is a SECTION CROSS-REFERENCE ("Methods §2", "(see §3.1)", "§L4"),
# not the dagger-family footnote markers (†, ‡, §, ¶) that legitimately mark
# author/affiliation footnotes and co-senior-author lines (e.g. "§ Dr. Hong and
# Dr. Kim are co-senior authors", a superscript "^§"). Count only § that is part
# of a section reference: § followed by a section id (digit, or up to 3 letters
# then a digit — §3, §L4, §S1, §2.1), or a section noun immediately before §.
SECTION_XREF = re.compile(
    r"§\s*[A-Za-z]{0,3}\d"
    r"|(?:see|in|per|section|sections|methods?|results?|discussion|introduction|"
    r"appendix|appendices|supplement(?:ary|al)?|table|figure)\s+§",
    re.IGNORECASE)

INBODY_AI_DISCLOSURE = re.compile(
    r"generative ai was not used|artificial intelligence disclosure|"
    r"during the preparation of (?:this|the) (?:manuscript|work|study)[^.]{0,120}?"
    r"(?:used|use[d]?|employed)[^.]{0,60}?(?:ai|gpt|chatgpt|claude|copilot|gemini|language model)",
    re.IGNORECASE)

ELIGIBILITY_LEAD = re.compile(
    r"(?:studies|articles|records|participants|patients|trials)\s+were\s+eligible\s+if|"
    r"eligibility criteria were|inclusion criteria (?:were|included)|"
    r"(?:studies|articles) were included if",
    re.IGNORECASE)
NUMBERED_MARKER = re.compile(r"\(\s*1\s*\)|\(\s*i\s*\)|(?:^|\s)1\.\s")

EFFECT_DECIMAL = re.compile(
    r"(?:\b(?:a?OR|a?HR|RR|sHR)\b|\bodds ratio\b|\bhazard ratio\b|\brisk ratio\b)"
    r"\s*(?:of|was|were|=|:|,)?\s*(\d+\.(\d+))", re.IGNORECASE)


def check(text: str, em_dash_max: int) -> list[dict]:
    claims = []

    # SECTION_SYMBOL (Major) — only § used as a section cross-reference, not the
    # dagger-family author/affiliation footnote markers.
    xrefs = list(SECTION_XREF.finditer(text))
    if xrefs:
        n = len(xrefs)
        first = xrefs[0].start()
        claims.append({
            "verdict": "SECTION_SYMBOL",
            "severity": "Major",
            "detail": f"a § section cross-reference appears {n} time(s) — a senior-reviewer "
                      f"AI tell; replace with the section name (manuscript-style-classical §6)",
            "where": text[max(0, first - 30):first + 20].replace("\n", " ").strip()[:120],
        })

    # INBODY_AI_DISCLOSURE (Major)
    m = INBODY_AI_DISCLOSURE.search(text)
    if m:
        claims.append({
            "verdict": "INBODY_AI_DISCLOSURE",
            "severity": "Major",
            "detail": "an AI/LLM-use disclosure paragraph is in the body; for a classical / "
                      "senior-MA target it belongs on the title page (manuscript-style-classical §7)",
            "where": m.group(0)[:120],
        })

    # ELIGIBILITY_PROSE (Minor)
    em = ELIGIBILITY_LEAD.search(text)
    if em and not NUMBERED_MARKER.search(text[em.start():em.start() + 320]):
        claims.append({
            "verdict": "ELIGIBILITY_PROSE",
            "severity": "Minor",
            "detail": "eligibility/inclusion criteria are written as prose; senior reviewers "
                      "expect a numbered list (1)…(2)…(3) (manuscript-style-classical §5)",
            "where": em.group(0)[:120],
        })

    # DECIMAL_INCONSISTENCY (Minor)
    dps = {len(mm.group(2)) for mm in EFFECT_DECIMAL.finditer(text)}
    if len(dps) > 1:
        claims.append({
            "verdict": "DECIMAL_INCONSISTENCY",
            "severity": "Minor",
            "detail": f"OR/HR/RR reported with mixed decimal places ({sorted(dps)}); "
                      f"standardize (OR/HR to 2 dp)",
            "where": "effect-size decimals",
        })

    # EM_DASH_OVERUSE (Minor) — count PROSE em-dashes only. Structural dashes are
    # legitimate, not a generation tell: markdown table cells (incl. "—" = N/A
    # placeholders and "(A) — label" panel captions), ORCID separators, and
    # author/affiliation lines ("Name, MD — Department of …"). Counting them forces
    # destructive edits on correct table dashes in cohort manuscripts with large
    # Table 1 / Table 3.
    prose_dash, structural_dash = _count_em_dashes(text)
    if prose_dash > em_dash_max:
        claims.append({
            "verdict": "EM_DASH_OVERUSE",
            "severity": "Minor",
            "detail": f"{prose_dash} prose em-dashes (> {em_dash_max}); a generation tell — "
                      f"replace some with commas/colons or split sentences "
                      f"({structural_dash} structural em-dashes in tables/ORCID/affiliation "
                      f"lines were excluded)",
            "where": f"{prose_dash} prose em-dashes ({structural_dash} structural excluded)",
        })

    return claims


_ORCID_RE = re.compile(r"\d{4}-\d{4}-\d{4}-\d{3}[\dXx]")
# A credential token immediately before the dash, or an affiliation noun right
# after it — the "Name, MD — Department of …" author/affiliation signature.
_AFFIL_DASH_RE = re.compile(
    r"\b(?:MD|PhD|MSc|MPH|MBBS|DO|DrPH|RN)\b[^—|]{0,20}—"
    r"|—[^—|]{0,20}\b(?:Department|Division|Institute|Faculty|College|University|Hospital|Center|Centre)\b",
    re.IGNORECASE)
# Figure/table/panel caption lines ("(A) — obesity stratum", "Figure 1. …",
# "*(A) S1 — …*") — structural, not prose.
_CAPTION_RE = re.compile(
    r"^\s*\*{0,2}(?:\(?[A-Za-z]\)|(?:Figure|Fig\.?|Table|Panel|Supplementary)\b)", re.IGNORECASE)


def _count_em_dashes(text: str) -> tuple[int, int]:
    """Return (prose, structural) em-dash counts. Structural = table rows, ORCID /
    affiliation / author lines, and standalone-cell dashes; prose = everything else
    (the genuine generation-tell surface)."""
    prose = structural = 0
    for line in text.splitlines():
        n = line.count("—")
        if not n:
            continue
        s = line.strip()
        is_table = "|" in line
        is_orcid = "orcid" in line.lower() or bool(_ORCID_RE.search(line))
        is_standalone = bool(re.fullmatch(r"[-–—\s]*", s))
        is_affil = bool(_AFFIL_DASH_RE.search(line))
        is_caption = bool(_CAPTION_RE.match(line))
        if is_table or is_orcid or is_standalone or is_affil or is_caption:
            structural += n
        else:
            prose += n
    return prose, structural


def analyze(manuscript: str, em_dash_max: int) -> dict:
    p = Path(manuscript)
    if not p.is_file():
        sys.stderr.write(f"ERROR: manuscript not found: {manuscript}\n")
        sys.exit(2)
    claims = check(p.read_text(encoding="utf-8"), em_dash_max)
    n_major = sum(1 for c in claims if c["severity"] == "Major")
    return {
        "manuscript": str(p),
        "claims": claims,
        "summary": {
            "n_claims": len(claims),
            "n_major": n_major,
            "n_flag": len(claims) - n_major,
            "verdict": "MAJOR_CANDIDATE" if n_major else ("FLAG" if claims else "OK"),
        },
    }


def render(result: dict) -> str:
    lines = ["| Check | Severity | Detail |", "|---|---|---|"]
    for c in result["claims"]:
        lines.append(f"| {c['verdict']} | {c['severity']} | {c['detail']} |")
    if len(lines) == 2:
        lines.append("| (none) | — | classical-style body conventions satisfied |")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Classical-style body lint (§J).")
    ap.add_argument("--manuscript", required=True, help="manuscript markdown/text")
    ap.add_argument("--em-dash-max", type=int, default=25, help="em-dash threshold (default 25)")
    ap.add_argument("--out", help="write JSON artifact to this path")
    ap.add_argument("--strict", action="store_true", help="exit 1 if any Major claim exists")
    ap.add_argument("--quiet", action="store_true", help="suppress stdout table")
    args = ap.parse_args()

    result = analyze(args.manuscript, args.em_dash_max)

    if not args.quiet:
        print("=" * 41)
        print(" Classical-Style Body Lint (§J)")
        print("=" * 41)
        print(render(result))
        print()
        s = result["summary"]
        if s["n_major"]:
            print(f"MAJOR candidate: {s['n_major']} policy/AI-tell violation(s).")
        elif s["n_flag"]:
            print(f"FLAG: {s['n_flag']} style inconsistency(ies).")
        else:
            print("OK: classical-style body conventions satisfied.")

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(result, indent=2), encoding="utf-8")
        if not args.quiet:
            print(f"\nwrote {args.out}")

    return 1 if (args.strict and result["summary"]["n_major"]) else 0


if __name__ == "__main__":
    sys.exit(main())
