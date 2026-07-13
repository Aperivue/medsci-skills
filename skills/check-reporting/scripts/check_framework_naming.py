#!/usr/bin/env python3
"""Reporting-framework naming discipline audit (check-reporting Step 4e).

A base reporting tool and its AI/extension are distinct instruments with separate
citations. Manuscripts routinely (a) invoke an extension (PROBAST+AI, STARD-AI,
TRIPOD+AI, PRISMA-DTA) without ever naming or citing the base instrument it
extends, (b) mix hyphenation for the same family within one document (PROBAST+AI
13x next to PROBAST-AI 2x), (c) coin item labels like "12-AI", or (d) wave at
"recent guidance" instead of naming the framework. Each is a reviewer red flag and
each is a deterministic grep.

INPUTS
  --manuscript  manuscript markdown/text (required).

CHECKS
  BASE_MISSING       (Major) an extension is used but its base instrument name never
                     appears standalone in the document.
  HYPHEN_MIX         (Minor) both "<FAMILY>+AI" and "<FAMILY>-AI" occur — inconsistent.
  CITE_MISSING       (Minor) the sentence first invoking an extension carries no
                     citation marker.
  SELF_COINED_LABEL  (Minor) a self-coined "<digits>-AI" item label.
  VAGUE_GUIDANCE     (Minor) "adapted per recent guidance"-style wording with no
                     named framework.

OUTPUT
  A reconciliation table (stdout) and, with --out, a JSON artifact:
    {manuscript, claims[{verdict, severity, detail, where}], summary}
  Exit 1 (with --strict) when any Major-severity claim exists.

Stdlib-only (json / re / argparse / pathlib). Exit codes: 0 clean (or report-only),
1 Major claim(s) found (with --strict), 2 input/usage error.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Extension regex -> base instrument name. The base must appear standalone (not as a
# prefix of the extension) somewhere in the document.
EXT_TO_BASE = [
    (r"PROBAST\s*\+\s*AI", "PROBAST"),
    (r"PROBAST-AI", "PROBAST"),
    (r"TRIPOD\s*\+\s*AI", "TRIPOD"),
    (r"TRIPOD-AI", "TRIPOD"),
    (r"TRIPOD-LLM", "TRIPOD"),
    (r"STARD-AI", "STARD"),
    (r"STARD\s*\+\s*AI", "STARD"),
    (r"CONSORT-AI", "CONSORT"),
    (r"SPIRIT-AI", "SPIRIT"),
    (r"PRISMA-DTA", "PRISMA"),
    (r"QUADAS-C", "QUADAS"),
]

HYPHEN_FAMILIES = ("PROBAST", "TRIPOD", "STARD", "CONSORT", "SPIRIT", "QUADAS", "DECIDE")

CITE_MARKER = re.compile(r"\[\d|\[@|\bet al\.?|\(\s*[A-Z][A-Za-z]+,?\s+\d{4}|\b\d{4}[a-z]?\)")
SELF_COINED = re.compile(r"\b\d{1,2}-AI\b")
VAGUE = re.compile(
    r"\b(?:adapted|adjusted|modified|aligned|updated|following|per|in line with)\b"
    r"[\w\s,]{0,20}?"
    r"\b(?:recent|current|emerging|latest|evolving)\b\s+"
    r"(?:best[- ]practice|guidance|practice|recommendations?|standards?|guidelines?)",
    re.I)
# VAGUE only counts inside a reporting-framework context; otherwise "recent
# best-practice recommendations" about a method is a false positive (F05).
REPORTING_CUE = re.compile(
    r"\b(?:report(?:ing|ed)?|checklist|EQUATOR|reporting\s+standard|"
    r"reporting\s+framework)\b", re.I)


def _sentences(text: str) -> list[str]:
    units = []
    for para in re.split(r"\n[ \t]*\n", text):
        flat = re.sub(r"\s*\n\s*", " ", para).strip()
        units.extend(re.split(r"(?<=[.;])\s+", flat))
    return [u for u in units if u.strip()]


def check(text: str) -> list[dict]:
    claims = []

    # BASE_MISSING + first-use CITE_MISSING
    flagged_base = set()
    for ext_re, base in EXT_TO_BASE:
        m = re.search(ext_re, text, re.I)
        if not m:
            continue
        standalone = re.search(rf"\b{base}\b(?!\s*[-+]\s*(?:AI|LLM))(?!-(?:AI|LLM|DTA|C\b))",
                               text, re.I)
        if not standalone and base not in flagged_base:
            flagged_base.add(base)
            claims.append({
                "verdict": "BASE_MISSING",
                "severity": "Major",
                "detail": (f"the extension '{m.group(0)}' is used but the base instrument "
                           f"'{base}' is never named standalone (name and cite both)"),
                "where": m.group(0),
            })
        # citation near first use
        sent = next((s for s in _sentences(text) if re.search(ext_re, s, re.I)), "")
        if sent and not CITE_MARKER.search(sent):
            claims.append({
                "verdict": "CITE_MISSING",
                "severity": "Minor",
                "detail": (f"first use of '{m.group(0)}' has no citation marker in its "
                           f"sentence"),
                "where": sent.strip()[:160],
            })

    # HYPHEN_MIX
    for fam in HYPHEN_FAMILIES:
        plus = len(re.findall(rf"{fam}\s*\+\s*AI", text, re.I))
        hyph = len(re.findall(rf"{fam}-AI", text, re.I))
        if plus and hyph:
            claims.append({
                "verdict": "HYPHEN_MIX",
                "severity": "Minor",
                "detail": (f"'{fam}+AI' ({plus}x) and '{fam}-AI' ({hyph}x) both used — "
                           f"pick one hyphenation"),
                "where": fam,
            })

    # SELF_COINED_LABEL
    for m in dict.fromkeys(SELF_COINED.findall(text)):
        claims.append({
            "verdict": "SELF_COINED_LABEL",
            "severity": "Minor",
            "detail": f"self-coined AI item label '{m}' — use the framework's own item numbering",
            "where": m,
        })

    # VAGUE_GUIDANCE — only when the sentence is clearly about REPORTING (a reporting
    # guideline / checklist) yet names no specific framework. Gating on a reporting cue
    # prevents firing on method-level wording like "external validation following recent
    # best-practice recommendations", which is not a reporting-framework claim at all.
    for s in _sentences(text):
        m = VAGUE.search(s)
        if m and REPORTING_CUE.search(s):
            claims.append({
                "verdict": "VAGUE_GUIDANCE",
                "severity": "Minor",
                "detail": (f"vague wording '{m.group(0).strip()}' in a reporting context — name "
                           f"the specific framework and cite it"),
                "where": m.group(0).strip()[:80],
            })

    return claims


def analyze(manuscript: str) -> dict:
    p = Path(manuscript)
    if not p.is_file():
        sys.stderr.write(f"ERROR: manuscript not found: {manuscript}\n")
        sys.exit(2)
    claims = check(p.read_text(encoding="utf-8"))
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
        lines.append("| (none) | — | reporting-framework naming is disciplined |")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Reporting-framework naming audit (Step 4e).")
    ap.add_argument("--manuscript", required=True, help="manuscript markdown/text")
    ap.add_argument("--out", help="write JSON artifact to this path")
    ap.add_argument("--strict", action="store_true", help="exit 1 if any Major claim exists")
    ap.add_argument("--quiet", action="store_true", help="suppress stdout table")
    args = ap.parse_args()

    result = analyze(args.manuscript)

    if not args.quiet:
        print("=" * 41)
        print(" Framework Naming (Step 4e)")
        print("=" * 41)
        print(render(result))
        print()
        s = result["summary"]
        if s["n_major"]:
            print(f"MAJOR candidate: {s['n_major']} base-instrument naming gap(s).")
        elif s["n_flag"]:
            print(f"FLAG: {s['n_flag']} naming/citation inconsistency(ies).")
        else:
            print("OK: reporting-framework naming is disciplined.")

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps({"detector": "check_framework_naming", **result}, indent=2), encoding="utf-8")
        if not args.quiet:
            print(f"\nwrote {args.out}")

    return 1 if (args.strict and result["summary"]["n_major"]) else 0


if __name__ == "__main__":
    sys.exit(main())
