#!/usr/bin/env python3
"""Incorporation-bias gate — the reference standard and a reported predictor are
the same construct (self-review Phase 2.5, category B. Reference Standard).

A nodule study classified nodules benign by "(b) complete resolution / (c)
decrease in diameter / (d) size stability" — every tier a form of NOT GROWING —
and then reported, as a headline finding, that "growth carried an OR of 50.9 for
malignancy". A resolved nodule cannot be malignant under that reference standard,
so the growth–malignancy association is partly definitional: the predictor was
built into the outcome. Two panel reviewers (a chest radiologist and a
methodologist) reached this independently and both called it fatal; nothing in
the gate stack fired.

This is textbook incorporation bias, and its commonest form — a size/trajectory
reference standard with a size/trajectory predictor — is deterministic from the
Methods and Results text alone:

  INCORPORATION_BIAS (Major)  the reference-standard / outcome DEFINITION is stated
                              in trajectory terms (resolution, regression, decrease,
                              stability, no growth, progression, growth), AND a
                              variable reported as *associated with* the outcome
                              (carrying an OR/HR/RR or "associated with / predictor
                              of") is itself a trajectory variable (growth, interval
                              change, increase/decrease in size). The predictor is
                              not independent of the reference standard.

Deterministic and conservative. It reads trajectory tokens ONLY from the
reference-standard/outcome-defining sentences (not an incidental "we measured
growth rate" in Methods), requires the reported association to name the outcome
in the same sentence, and stays silent when the manuscript already discloses the
overlap ("incorporation bias", "partly definitional", "not independent of the
reference standard"). It deliberately covers only the trajectory sub-class; the
broader "framework-under-validation supplied the endpoint" instances are left to
the prose review probes, which are not deterministic from text alone.

INPUT   --manuscript  manuscript markdown/text (required).
OUTPUT  (--out path) {"detector": "check_incorporation_bias", "manuscript",
          "claims":[{verdict, severity, detail, where}], "summary":{...}}

Stdlib-only (re / json / argparse / pathlib). Exit codes: 0 clean (or report-only),
1 a Major claim exists (with --strict), 2 input/usage error.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# A reference-standard / outcome DEFINING heading.
REF_HEADING_RE = re.compile(
    r"^#{1,4}\s*\*{0,2}\s*(?:Reference standard|Outcome(?: definition| assessment| measure)?|"
    r"Ground truth|Gold standard|Definition of (?:benign|malignan\w+|the outcome))\*{0,2}\s*:?\s*$",
    re.IGNORECASE | re.MULTILINE)

# A sentence that DEFINES the benign/malignant outcome or the reference standard.
REF_CUE_SENTENCE_RE = re.compile(
    r"[^.\n]*\b(?:classified (?:as )?(?:benign|malignan\w+)"
    r"|(?:benign|malignan\w+)\s+(?:was|were|is|are)?\s*(?:defined|classified|confirmed|considered)"
    r"|reference standard (?:was|were|comprised|consisted|included|is|are)"
    r"|benign if|malignan\w+ if)\b[^.\n]*\.",
    re.IGNORECASE)

# Trajectory / size-change vocabulary — the family that a size reference standard
# and a size predictor share.
TRAJECTORY_RE = re.compile(
    r"\b(?:complete\s+)?resolution\b|\bregress\w+|\bdecreas\w+|\bshrink\w+|\bshrank\b|\bstabilit\w+"
    r"|\bstable\b|\bno growth\b|\bnot? grow\w*|\bunchanged\b|\bgrowth\b|\bgrew\b|\bgrow\w+"
    r"|\bprogress\w+|\benlarg\w+|increas\w+\s+in\s+(?:size|diameter)|interval change|size change"
    r"|\btrajector\w+", re.IGNORECASE)

# An association marker: a reported effect measure or "associated with / predictor of".
ASSOC_MARKER_RE = re.compile(
    r"\b(?:a?OR|a?HR|RR|odds ratio|hazard ratio|risk ratio)\b"
    r"|associated with|predictor of|risk factor for|predict\w*\s+(?:malignan|the outcome)",
    re.IGNORECASE)

# A trajectory-named PREDICTOR variable.
PREDICTOR_TRAJ_RE = re.compile(
    r"\bgrowth\b|\bgrew\b|interval change|size change|change in (?:size|diameter)"
    r"|increas\w+\s+in\s+(?:size|diameter)|\bdecreas\w+|\bresolution\b|\btrajector\w+|\benlarg\w+",
    re.IGNORECASE)

# The outcome named in the association sentence.
OUTCOME_RE = re.compile(r"malignan\w+|\bbenign\b|\bcancer\b|carcinoma|the outcome", re.IGNORECASE)

# The manuscript already names the overlap — do not fire.
DISCLOSURE_RE = re.compile(
    r"incorporation bias|partly definitional|not independent of the reference standard"
    r"|circular by construction|definitional(?:ly)?\s+(?:linked|related|confounded)|"
    r"by construction (?:linked|related|not independent)",
    re.IGNORECASE)

_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z(\"'])")


def _ref_standard_text(text: str) -> str:
    spans = []
    all_h = [m.start() for m in re.finditer(r"^#{1,4}\s", text, re.MULTILINE)]
    for m in REF_HEADING_RE.finditer(text):
        s = m.end()
        nxt = next((h for h in all_h if h > s), len(text))
        spans.append(text[s:nxt])
    for m in REF_CUE_SENTENCE_RE.finditer(text):
        spans.append(m.group(0))
    return "\n".join(spans)


def check(text: str) -> list[dict]:
    if DISCLOSURE_RE.search(text):
        return []  # the overlap is disclosed; not a hidden incorporation bias
    ref_text = _ref_standard_text(text)
    if not ref_text or not TRAJECTORY_RE.search(ref_text):
        return []  # the reference standard is not trajectory-defined
    for block in re.split(r"\n\s*\n|\n#{1,6}\s", text):
        for sent in _SENT_SPLIT.split(block):
            if (ASSOC_MARKER_RE.search(sent) and PREDICTOR_TRAJ_RE.search(sent)
                    and OUTCOME_RE.search(sent)):
                pm = PREDICTOR_TRAJ_RE.search(sent)
                return [{
                    "verdict": "INCORPORATION_BIAS",
                    "severity": "Major",
                    "detail": (f"the reference standard defines the outcome by size trajectory "
                               f"(resolution / decrease / stability / growth), and '{pm.group(0)}' — a "
                               f"trajectory variable — is reported as associated with the outcome: the "
                               f"predictor is built into the reference standard, so the association is "
                               f"partly definitional. Use a predictor independent of the reference "
                               f"standard, or disclose the overlap explicitly"),
                    "where": sent.strip().replace("\n", " ")[:160],
                }]
    return []


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
        "summary": {"n_claims": len(claims), "n_major": n_major,
                    "n_flag": len(claims) - n_major,
                    "verdict": "MAJOR_CANDIDATE" if n_major else "OK"},
    }


def render(result: dict) -> str:
    lines = ["| Check | Severity | Detail |", "|---|---|---|"]
    for c in result["claims"]:
        lines.append(f"| {c['verdict']} | {c['severity']} | {c['detail']} |")
    if len(lines) == 2:
        lines.append("| (none) | — | reference standard and reported predictors are independent |")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Incorporation-bias gate (Phase 2.5, reference standard).")
    ap.add_argument("--manuscript", required=True, help="manuscript markdown/text")
    ap.add_argument("--out", help="write JSON artifact to this path")
    ap.add_argument("--strict", action="store_true", help="exit 1 if any Major claim exists")
    ap.add_argument("--quiet", action="store_true", help="suppress stdout table")
    args = ap.parse_args()

    result = analyze(args.manuscript)
    if not args.quiet:
        print("=" * 41)
        print(" Incorporation Bias (Phase 2.5)")
        print("=" * 41)
        print(render(result))
        print()
        s = result["summary"]
        print(f"MAJOR candidate: {s['n_major']} incorporation-bias finding(s)." if s["n_major"]
              else "OK: reference standard and reported predictors are independent.")

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps({"detector": "check_incorporation_bias", **result}, indent=2),
                                  encoding="utf-8")
        if not args.quiet:
            print(f"\nwrote {args.out}")

    return 1 if (args.strict and result["summary"]["n_major"]) else 0


if __name__ == "__main__":
    sys.exit(main())
