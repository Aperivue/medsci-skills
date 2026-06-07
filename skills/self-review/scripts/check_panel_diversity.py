#!/usr/bin/env python3
"""Panel lens-diversity gate (self-review Phase 2.6, --panel).

A multi-agent panel is only worth its cost if its reviewers cover *distinct*
concern axes. Left unchecked, independent reviewers converge on the same easy
themes (everyone flags "missing calibration") while whole high-risk axes go
unprobed — the panel collapses to fewer effective lenses than reviewers, and
the editor synthesis cannot tell monoculture from genuine consensus. This gate
post-processes the reviewers' structured output (the panel_review_template
schema the editor already collects) and reports three diversity failures:

  UNCOVERED_AXIS     an expected high-risk axis for this research type produced
                     ZERO major findings across the whole panel. Mirrors the
                     "completeness critic" pattern: name what nobody probed so
                     the editor can re-probe it before finalizing. (Major)
  FAMILY_MONOCULTURE the panel's major findings concentrate in ONE concern
                     family beyond a threshold (one family holds the majority),
                     a signal the lenses converged rather than spanned the
                     manuscript. (Major)
  LENS_COLLAPSE      one reviewer contributed only families that another
                     reviewer already covered — a fully-redundant lens that
                     added no independent signal. Distinct from healthy
                     CONSENSUS (a reviewer agreeing on SOME themes but also
                     raising at least one family nobody else did). (Flag)

Healthy consensus is preserved: a finding family raised by ≥2 reviewers is a
strength, not a defect. The gate only fires LENS_COLLAPSE when a reviewer's
ENTIRE contribution is redundant, and UNCOVERED_AXIS/MONOCULTURE on
panel-level coverage, never on agreement per se.

INPUTS
  --panel  JSON file. Either a list of reviewer objects, or an object with a
           "reviewers" list (and optional "research_type"). Each reviewer
           object needs reviewer_id, expertise_area, and major[] (with heading
           and/or comment text); minor[] is ignored for axis coverage.
  --research-type  one of: survival, sr_ma, radiomics, dta, observational,
           narrative (synonyms accepted). Overrides any value in the JSON.
           When unknown/absent, UNCOVERED_AXIS is skipped (cannot know the
           expected axes) and noted in the summary.

OUTPUT
  A diversity table (stdout) and, with --out, a JSON artifact:
    {panel, research_type, claims[{verdict, severity, detail, where}], summary}
  summary carries the family histogram, concentration index, and the
  expected/covered/uncovered axes. Exit 1 (with --strict) when any Major claim
  exists; exit 2 on input error.

Stdlib-only (json / re / argparse / pathlib). Exit codes: 0 clean (or
report-only), 1 Major claim(s) found (with --strict), 2 input/usage error.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Concern families, aligned to the panel's per-domain focus checklists and the
# self-review A–J category system. Each finding is assigned to the FIRST family
# whose lexicon matches its text; order is most-specific to most-generic so a
# leakage finding is not swallowed by the generic "statistics" family.
FAMILY_LEXICON: list[tuple[str, re.Pattern]] = [
    ("search_screening", re.compile(
        r"search strateg|screening|eligibilit|inclusion criteri|exclusion criteri|"
        r"database\b|grey literature|gray literature|duplicate (?:removal|record)|"
        r"prisma flow|records identified|study selection", re.IGNORECASE)),
    ("design_leakage", re.compile(
        r"leakage|data (?:split|leak)|train(?:ing|/test| test)|test set|"
        r"contaminat|allocation|randomi[sz]|immortal time|time[-\s]?zero|"
        r"selection bias|spectrum bias|case[-\s]?control selection|"
        r"reference standard|verification bias", re.IGNORECASE)),
    ("confounding", re.compile(
        r"confound|residual confounding|covariate|adjust(?:ment|ed)|mediator|"
        r"collider|confounding by indication|propensity", re.IGNORECASE)),
    ("imaging", re.compile(
        r"acquisition|scanner|sequence|segmentation|voxel|kernel|reconstruction|"
        r"combat|harmoni[sz]|slice thickness|field strength|radiomic feature|"
        r"window(?:ing| level)|protocol heterogeneity", re.IGNORECASE)),
    ("reporting", re.compile(
        r"strobe|tripod|prisma\b|consort|claim\b|stard|reporting (?:guideline|standard|"
        r"completeness)|checklist|flow diagram|disclosure|registration|protocol "
        r"deviation|abstract (?:inconsisten|mismatch)", re.IGNORECASE)),
    ("reproducibility", re.compile(
        r"reproducib|code availab|data availab|random seed|\bseed\b|script\b|"
        r"open (?:data|code)|version pin", re.IGNORECASE)),
    ("statistics", re.compile(
        r"calibrat|discriminat|\bauc\b|c[-\s]?statistic|delong|confidence interval|"
        r"\bci\b|heterogeneit|\bi2\b|i\^?2|pooling|pooled|random[-\s]?effects|"
        r"multiplicit|multiple compar|\bp[-\s]?value|\bpower\b|sample size|"
        r"model specif|proportional hazard|missing data|imputation|competing risk|"
        r"events per variable|overfitting|effect size|subdistribution", re.IGNORECASE)),
    ("clinical", re.compile(
        r"clinical|actionab|guideline|management|generali[sz]ab|applicab|"
        r"external validit|patient[-\s]?care|over(?:reach|claim)|"
        r"clinical (?:relevance|utility|significance)", re.IGNORECASE)),
]

# Expected high-risk axes per research type (each SHOULD yield ≥1 major). Mirrors
# the Phase 2.6 reviewer-set table; optional axes (e.g. imaging when the exposure
# is non-imaging) are not required and so are omitted here.
EXPECTED_AXES: dict[str, list[str]] = {
    "survival": ["statistics", "clinical"],
    "sr_ma": ["search_screening", "clinical", "statistics"],
    "radiomics": ["imaging", "statistics", "clinical"],
    "dta": ["design_leakage", "statistics", "clinical"],
    "observational": ["confounding", "clinical", "statistics"],
    "narrative": ["clinical", "reporting"],
}

RESEARCH_TYPE_SYNONYMS: dict[str, str] = {
    "survival": "survival", "prognostic": "survival", "cohort": "survival",
    "sr": "sr_ma", "ma": "sr_ma", "sr_ma": "sr_ma", "sr/ma": "sr_ma",
    "systematic review": "sr_ma", "meta-analysis": "sr_ma", "meta analysis": "sr_ma",
    "radiomics": "radiomics", "feature": "radiomics",
    "dta": "dta", "diagnostic": "dta", "diagnostic-accuracy": "dta", "ai model": "dta",
    "observational": "observational", "strobe": "observational",
    "narrative": "narrative", "review article": "narrative", "sanra": "narrative",
}

MONOCULTURE_MIN_MAJORS = 4   # too few majors to call concentration meaningful
MONOCULTURE_SHARE = 0.60     # one family holding > this share = monoculture


def normalize_research_type(raw: str | None) -> str | None:
    if not raw:
        return None
    key = raw.strip().lower()
    if key in RESEARCH_TYPE_SYNONYMS:
        return RESEARCH_TYPE_SYNONYMS[key]
    for syn, canon in RESEARCH_TYPE_SYNONYMS.items():
        if syn in key:
            return canon
    return None


def classify(text: str) -> str:
    for family, pat in FAMILY_LEXICON:
        if pat.search(text):
            return family
    return "other"


def finding_text(major: dict) -> str:
    parts = [str(major.get(k, "")) for k in ("heading", "comment", "location")]
    return " ".join(p for p in parts if p)


def load_reviewers(obj) -> tuple[list[dict], str | None]:
    if isinstance(obj, list):
        return obj, None
    if isinstance(obj, dict):
        revs = obj.get("reviewers")
        if isinstance(revs, list):
            return revs, obj.get("research_type")
    raise ValueError("panel JSON must be a list of reviewers or an object with a 'reviewers' list")


def check(reviewers: list[dict], research_type: str | None) -> tuple[list[dict], dict]:
    claims: list[dict] = []

    # Per-reviewer families (set of distinct families this reviewer raised as majors)
    rev_families: dict[str, set[str]] = {}
    family_hist: dict[str, int] = {}
    n_majors = 0
    for i, rev in enumerate(reviewers):
        rid = str(rev.get("reviewer_id") or f"R{i + 1}")
        fams: set[str] = set()
        for maj in rev.get("major", []) or []:
            fam = classify(finding_text(maj))
            fams.add(fam)
            family_hist[fam] = family_hist.get(fam, 0) + 1
            n_majors += 1
        rev_families[rid] = fams

    covered = set(family_hist)
    covered.discard("other")

    # 1) UNCOVERED_AXIS — only when we know the expected axes
    expected: list[str] = []
    uncovered: list[str] = []
    if research_type and research_type in EXPECTED_AXES:
        expected = EXPECTED_AXES[research_type]
        uncovered = [ax for ax in expected if family_hist.get(ax, 0) == 0]
        for ax in uncovered:
            claims.append({
                "verdict": "UNCOVERED_AXIS",
                "severity": "Major",
                "detail": (f"no major finding addresses the '{ax}' axis, which a "
                           f"{research_type} panel is expected to probe; the editor "
                           f"should re-probe it before finalizing"),
                "where": f"expected axes for {research_type}: {', '.join(expected)}",
            })

    # 2) FAMILY_MONOCULTURE — concentration of majors in one family
    hhi = 0.0
    top_family = None
    top_share = 0.0
    if n_majors:
        shares = {f: c / n_majors for f, c in family_hist.items() if f != "other"}
        hhi = sum(s * s for s in shares.values())
        if shares:
            top_family, top_share = max(shares.items(), key=lambda kv: kv[1])
        if n_majors >= MONOCULTURE_MIN_MAJORS and top_share > MONOCULTURE_SHARE:
            claims.append({
                "verdict": "FAMILY_MONOCULTURE",
                "severity": "Major",
                "detail": (f"{top_share:.0%} of major findings fall in the '{top_family}' "
                           f"family ({family_hist.get(top_family, 0)}/{n_majors}); the panel "
                           f"converged on one axis rather than spanning the manuscript"),
                "where": "family histogram: " + ", ".join(
                    f"{f}={c}" for f, c in sorted(family_hist.items(), key=lambda kv: -kv[1])),
            })

    # 3) LENS_COLLAPSE — a reviewer whose every family is also covered by another
    for rid, fams in rev_families.items():
        own = {f for f in fams if f != "other"}
        if not own:
            continue
        others = set()
        for other_rid, other_fams in rev_families.items():
            if other_rid != rid:
                others |= {f for f in other_fams if f != "other"}
        if own and own <= others:  # fully subsumed by other reviewers
            claims.append({
                "verdict": "LENS_COLLAPSE",
                "severity": "Flag",
                "detail": (f"reviewer {rid} raised only families also covered by other "
                           f"reviewers ({', '.join(sorted(own))}); this lens added no "
                           f"independent axis — confirm it is a genuine consensus, not a "
                           f"redundant reviewer assignment"),
                "where": f"reviewer {rid}",
            })

    # 4) THIN_PANEL
    if len(reviewers) < 2:
        claims.append({
            "verdict": "THIN_PANEL",
            "severity": "Flag",
            "detail": (f"only {len(reviewers)} reviewer(s); a panel needs ≥2 independent "
                       f"lenses for diversity to be meaningful"),
            "where": "panel composition",
        })

    summary = {
        "n_reviewers": len(reviewers),
        "n_majors": n_majors,
        "family_histogram": family_hist,
        "concentration_hhi": round(hhi, 3),
        "top_family": top_family,
        "top_family_share": round(top_share, 3),
        "expected_axes": expected,
        "covered_axes": sorted(covered),
        "uncovered_axes": uncovered,
        "research_type_known": bool(research_type and research_type in EXPECTED_AXES),
    }
    return claims, summary


def analyze(panel: str, research_type_arg: str | None) -> dict:
    p = Path(panel)
    if not p.is_file():
        sys.stderr.write(f"ERROR: panel JSON not found: {panel}\n")
        sys.exit(2)
    try:
        obj = json.loads(p.read_text(encoding="utf-8"))
        reviewers, rt_in_json = load_reviewers(obj)
    except (ValueError, json.JSONDecodeError) as exc:
        sys.stderr.write(f"ERROR: {exc}\n")
        sys.exit(2)

    research_type = normalize_research_type(research_type_arg) or normalize_research_type(rt_in_json)
    claims, summary = check(reviewers, research_type)
    n_major = sum(1 for c in claims if c["severity"] == "Major")
    summary["n_claims"] = len(claims)
    summary["n_major"] = n_major
    summary["n_flag"] = len(claims) - n_major
    summary["verdict"] = "MAJOR_CANDIDATE" if n_major else "OK"
    return {
        "panel": str(p),
        "research_type": research_type,
        "claims": claims,
        "summary": summary,
    }


def render(result: dict) -> str:
    lines = ["| Check | Severity | Detail |", "|---|---|---|"]
    for c in result["claims"]:
        lines.append(f"| {c['verdict']} | {c['severity']} | {c['detail']} |")
    if len(lines) == 2:
        lines.append("| (none) | — | panel lenses span distinct axes; no monoculture |")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Panel lens-diversity gate (Phase 2.6, --panel).")
    ap.add_argument("--panel", required=True, help="reviewers JSON (list or {reviewers:[...]})")
    ap.add_argument("--research-type", help="survival|sr_ma|radiomics|dta|observational|narrative")
    ap.add_argument("--out", help="write JSON artifact to this path")
    ap.add_argument("--strict", action="store_true", help="exit 1 if any Major claim exists")
    ap.add_argument("--quiet", action="store_true", help="suppress stdout table")
    args = ap.parse_args()

    result = analyze(args.panel, args.research_type)

    if not args.quiet:
        print("=" * 41)
        print(" Panel Lens-Diversity (Phase 2.6)")
        print("=" * 41)
        print(render(result))
        print()
        s = result["summary"]
        if not s["research_type_known"]:
            print("NOTE: research type unknown — UNCOVERED_AXIS skipped "
                  "(pass --research-type to enable axis-coverage checks).")
        if s["n_major"]:
            print(f"MAJOR candidate: {s['n_major']} diversity failure(s); "
                  f"covered axes: {', '.join(s['covered_axes']) or '(none)'}.")
        else:
            print(f"OK: {s['n_reviewers']} reviewers spanning "
                  f"{len(s['covered_axes'])} distinct axes "
                  f"(HHI={s['concentration_hhi']}).")

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(result, indent=2), encoding="utf-8")
        if not args.quiet:
            print(f"\nwrote {args.out}")

    return 1 if (args.strict and result["summary"]["n_major"]) else 0


if __name__ == "__main__":
    sys.exit(main())
