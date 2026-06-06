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
  EM_DASH_OVERUSE       (Minor) more than 25 em-dashes — a generation tell.

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

    # SECTION_SYMBOL (Major)
    if "§" in text:
        n = text.count("§")
        first = text.find("§")
        claims.append({
            "verdict": "SECTION_SYMBOL",
            "severity": "Major",
            "detail": f"the § symbol appears {n} time(s) — a senior-reviewer AI tell; "
                      f"replace with the section name (manuscript-style-classical §6)",
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

    # EM_DASH_OVERUSE (Minor)
    n_dash = text.count("—")
    if n_dash > em_dash_max:
        claims.append({
            "verdict": "EM_DASH_OVERUSE",
            "severity": "Minor",
            "detail": f"{n_dash} em-dashes (> {em_dash_max}); a generation tell — "
                      f"replace some with commas/colons or split sentences",
            "where": f"{n_dash} em-dashes",
        })

    return claims


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
