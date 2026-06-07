#!/usr/bin/env python3
"""Reference adequacy gate for self-review Phase 2.5c-2 / write-paper Step 7.3c.

Reference INTEGRITY (are the cited references real and metadata-valid?) is the
job of verify-refs. This is the complementary REFERENCE ADEQUACY check: are
there enough relevant references, in the right sections, and does every named
statistical method or reporting guideline carry a citation? The highest-value,
most-deterministic instance is Methods named-method citation coverage -- an
autonomous draft can name a competing-risk model, multiple imputation, the
E-value, and an eGFR equation in its Statistical Analysis subsection with zero
citations and still read as internally consistent.

This gate NEVER proposes reference text. It diagnoses gaps (fixable_by_ai=false);
fix-forward belongs to /search-lit -> /lit-sync -> /verify-refs.

INPUTS
  --manuscript    manuscript markdown/qmd (required).
  --bib           optional refs.bib; reports the bib entry count for cross-check.
  --article-type  repo paper-type name or target bucket (see ALIASES); default
                  original_article.
  --journal-cap   optional journal reference cap (int).

OUTPUT  (--out path)
  {article_type, article_bucket, journal_cap, cited_reference_count,
   bib_entry_count, effective_target, section_distribution,
   named_methods_found, uncited_named_methods, methods_zero_citations,
   reference_count_verdict, adequacy_safe,
   findings[{issue_type, subtype, severity, location, description,
             fixable_by_ai, suggested_fix}], summary{major, minor, notes}}

Stdlib-only (re / json / argparse / pathlib). Exit codes: 0 clean (or
report-only), 1 a Major adequacy finding exists (with --strict), 2 input/usage
error.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# --------------------------------------------------------------------------- #
# Article-type targets and aliases (single SSOT for the named-method registry  #
# and the reference-count ranges; write-paper Step 7.3c calls this script      #
# directly rather than mirroring these constants).                             #
# --------------------------------------------------------------------------- #

# bucket -> (min, max) recommended reference count
TARGETS = {
    "original_research": (25, 45),
    "ai_validation": (25, 45),
    "meta_analysis": (40, 80),   # also systematic_review
    "review": (50, 100),         # narrative / review
    "technical_note": (10, 20),
    "case_report": (10, 20),
    "editorial": (5, 15),
    "letter": (0, 10),
}

# repo paper-type filename (skills/write-paper/references/paper_types/) -> bucket
ALIASES = {
    "original_article": "original_research",
    "original_research": "original_research",
    "nhis_cohort": "original_research",
    "cross_national": "original_research",
    "animal_study": "original_research",
    "ai_validation": "ai_validation",
    "meta_analysis": "meta_analysis",
    "systematic_review": "meta_analysis",
    "review": "review",
    "narrative": "review",
    "narrative_review": "review",
    "technical_note": "technical_note",
    "brief": "technical_note",
    "case_report": "case_report",
    "editorial": "editorial",
    "commentary": "editorial",
    "letter": "letter",
}

# Buckets where a Methods/Statistical-Analysis section is expected to carry
# citations; methods_zero_citations escalates to Major only for these.
METHODS_SECTION_EXPECTED = {"original_research", "ai_validation", "meta_analysis"}

# Named methods whose mention without a citation is a Major adequacy gap.
STATISTICAL = [
    "Cox proportional hazards", "Cox",
    "Fine-Gray", "competing risk", "subdistribution hazard",
    "multiple imputation", "MICE", "White-Royston",
    "E-value", "Benjamini-Hochberg", "FDR", "bootstrap", "Schoenfeld",
    "CKD-EPI", "Harrell C-index", "DeLong", "calibration", "Brier",
    "decision curve", "net benefit", "propensity score",
    "inverse probability weighting",
]
# Reporting/diagnostic standards whose mention without a citation is Minor.
GUIDELINE_REPORTING = [
    "GOLD", "FEV1/FVC", "STROBE", "TRIPOD", "CONSORT", "PRISMA", "STARD",
]

# --------------------------------------------------------------------------- #
# Citation-marker detection (union of pandoc, numbered, author-year,           #
# superscript). Paragraph-level clustering keeps the check conservative.       #
# --------------------------------------------------------------------------- #

_SUP = {"⁰": "0", "¹": "1", "²": "2", "³": "3", "⁴": "4",
        "⁵": "5", "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9"}
_SUP_CLASS = r"[⁰¹²³⁴-⁹]+"
# A name token allows internal apostrophes/hyphens (O'Brien, Smith-Jones).
_NAME = r"[A-Z][A-Za-z'’\-]+"

CITE_RE = re.compile(
    r"\[@[^\]]+\]"                                                  # pandoc [@key] / [@a; @b]
    r"|\[\d+(?:[–—-]\d+)?(?:,\s*\d+(?:[–—-]\d+)?)*\]"  # [12] [1-3] [1,2,5]
    r"|\((?:" + _NAME + r")(?:\s+(?:et al\.?|and|&)\s+" + _NAME + r")?,?\s*(?:19|20)\d{2}[a-z]?\)"  # (Author, 2020)
    r"|" + _SUP_CLASS,                                              # superscript ¹²
    re.UNICODE,
)


def normalize(text: str) -> str:
    """Fold non-breaking/figure hyphens to ASCII so 'E-value' matches."""
    return text.replace("‑", "-").replace("‐", "-")


def distinct_refs(body: str) -> set[str]:
    """Distinct reference identifiers cited in `body` (keys/numbers/author-year)."""
    keys: set[str] = set()
    for m in re.finditer(r"\[@([^\]]+)\]", body):
        for k in re.split(r"[;,]\s*@?", m.group(1)):
            k = k.strip().lstrip("@")
            if k:
                keys.add("@" + k)
    for m in re.finditer(r"\[(\d+(?:[–—-]\d+)?(?:,\s*\d+(?:[–—-]\d+)?)*)\]", body):
        for part in m.group(1).split(","):
            part = part.strip()
            rng = re.match(r"(\d+)[–—-](\d+)$", part)
            if rng:
                a, b = int(rng.group(1)), int(rng.group(2))
                if 0 < b - a < 500:
                    keys.update("#" + str(n) for n in range(a, b + 1))
            elif part.isdigit():
                keys.add("#" + part)
    for m in re.finditer(r"\((" + _NAME + r")(?:\s+(?:et al\.?|and|&)\s+" + _NAME +
                         r")?,?\s*((?:19|20)\d{2}[a-z]?)\)", body):
        keys.add("AY:" + m.group(1) + m.group(2))
    for m in re.finditer(_SUP_CLASS, body):
        num = "".join(_SUP.get(c, "") for c in m.group(0))
        if num:
            keys.add("^" + num)
    return keys


# --------------------------------------------------------------------------- #
# Section parsing                                                              #
# --------------------------------------------------------------------------- #

SEC_PATTERNS = {
    "introduction": re.compile(r"^(introduction|background)\b", re.I),
    "methods": re.compile(r"^(materials and methods|methods and materials|methods|"
                          r"statistical analysis|statistical methods)\b", re.I),
    "results": re.compile(r"^(results|findings)\b", re.I),
    "discussion": re.compile(r"^(discussion|comment)\b", re.I),
}


def top_sections(md: str) -> list[tuple[str, int, str]]:
    """Return (clean_title, level, body) for every header (any level)."""
    lines = md.split("\n")
    heads = []
    for i, line in enumerate(lines):
        m = re.match(r"(#{1,6})\s+(.*)$", line)
        if m:
            title = re.sub(r"[*_`]", "", m.group(2)).strip()
            heads.append((i, len(m.group(1)), title))
    out = []
    for idx, (li, lvl, title) in enumerate(heads):
        end = len(lines)
        for lj, lvl2, _ in heads[idx + 1:]:
            if lvl2 <= lvl:
                end = lj
                break
        out.append((title, lvl, "\n".join(lines[li + 1:end])))
    return out


def section_text(sections, key: str) -> str:
    """Concatenate top-level (h1/h2) section bodies matching a canonical key."""
    pat = SEC_PATTERNS[key]
    return "\n\n".join(body for title, lvl, body in sections
                       if lvl <= 2 and pat.match(title))


# --------------------------------------------------------------------------- #
# Named-method coverage                                                        #
# --------------------------------------------------------------------------- #

def scan_named_methods(methods_body: str) -> dict[str, dict]:
    """term -> {cited: bool, tier: 'stat'|'guide'} for every registry term found.

    A term is 'cited' if any paragraph containing it also carries a citation
    marker. Longest term first so 'Cox proportional hazards' claims its span
    before the bare 'Cox' can double-count it.
    """
    terms = [(t, "stat") for t in STATISTICAL] + [(t, "guide") for t in GUIDELINE_REPORTING]
    terms.sort(key=lambda x: -len(x[0]))
    compiled = [(t, tier, re.compile(r"(?<![A-Za-z0-9])" + re.escape(t) + r"(?![A-Za-z0-9])", re.I))
                for t, tier in terms]
    found: dict[str, dict] = {}
    for para in re.split(r"\n\s*\n", methods_body):
        has_cite = bool(CITE_RE.search(para))
        covered: list[tuple[int, int]] = []
        for term, tier, pat in compiled:
            for m in pat.finditer(para):
                span = (m.start(), m.end())
                if any(span[0] >= c[0] and span[1] <= c[1] for c in covered):
                    continue
                covered.append(span)
                rec = found.setdefault(term, {"cited": False, "tier": tier})
                rec["cited"] = rec["cited"] or has_cite
                break
    return found


# --------------------------------------------------------------------------- #
# Main                                                                         #
# --------------------------------------------------------------------------- #

def _finding(subtype, severity, location, description, fix):
    return {"issue_type": "reference_adequacy", "subtype": subtype,
            "severity": severity, "location": location, "description": description,
            "fixable_by_ai": False, "suggested_fix": fix}


def assess(manuscript: str, article_type: str, journal_cap, bib_entry_count) -> dict:
    notes = []
    key = article_type.strip().lower().replace(" ", "_").replace("-", "_")
    bucket = ALIASES.get(key)
    if bucket is None:
        bucket = "original_research"
        notes.append(f"unknown article-type '{article_type}'; defaulted to original_research")

    sections = top_sections(manuscript)
    methods_body = section_text(sections, "methods")
    distribution = {k: len(distinct_refs(section_text(sections, k))) for k in SEC_PATTERNS}
    cited_count = len(distinct_refs(manuscript))

    found = scan_named_methods(methods_body)
    methods_has_citation = bool(CITE_RE.search(methods_body))
    methods_zero_citations = bool(methods_body.strip()) and not methods_has_citation

    named_methods_found = sorted(found)
    uncited = sorted(t for t, r in found.items() if not r["cited"])

    amin, amax = TARGETS[bucket]
    if journal_cap is not None and journal_cap < amin:
        eff_min, eff_max = journal_cap, journal_cap
        notes.append(f"journal cap {journal_cap} below article-type floor {amin}; "
                     f"effective target lowered to the cap")
    else:
        eff_min, eff_max = amin, amax

    findings = []

    if methods_zero_citations and bucket in METHODS_SECTION_EXPECTED:
        listed = ", ".join(named_methods_found) if named_methods_found else "named methods/scores"
        findings.append(_finding(
            "methods_zero_citations", "major", "Methods - Statistical Analysis",
            f"The Methods/Statistical Analysis section contains no citations; every named "
            f"method, score, guideline, and diagnostic criterion needs a canonical source "
            f"(found uncited: {listed}).",
            "Run /search-lit (paper mode) for canonical methodology sources, sync via "
            "/lit-sync, then rerun /verify-refs --strict."))
    else:
        for term in uncited:
            if found[term]["tier"] == "stat":
                findings.append(_finding(
                    "methods_named_method_uncited", "major", "Methods - Statistical Analysis",
                    f"{term} is named in the Statistical Analysis subsection without a citation "
                    f"in its paragraph.",
                    f"Run /search-lit (paper mode) for the canonical {term} source, sync via "
                    f"/lit-sync, then rerun /verify-refs --strict."))
            else:
                findings.append(_finding(
                    "reporting_guideline_uncited", "minor", "Methods",
                    f"The {term} standard is named without a citation in its paragraph.",
                    f"Run /search-lit for the {term} reference, sync via /lit-sync, then rerun "
                    f"/verify-refs --strict."))

    verdict = "ADEQUATE" if cited_count >= eff_min else "BELOW_TARGET"
    if verdict == "BELOW_TARGET":
        sev = "major" if cited_count < 0.5 * eff_min else "minor"
        findings.append(_finding(
            "below_article_type_target", sev, "Whole manuscript",
            f"Cited references ({cited_count}) are below the {bucket} target "
            f"({eff_min}-{eff_max}).",
            "Run /search-lit (paper mode) to retrieve verified candidates across the six "
            "categories, sync via /lit-sync, then rerun /verify-refs --strict."))

    n_major = sum(1 for f in findings if f["severity"] == "major")
    n_minor = sum(1 for f in findings if f["severity"] == "minor")

    return {
        "article_type": article_type,
        "article_bucket": bucket,
        "journal_cap": journal_cap,
        "cited_reference_count": cited_count,
        "bib_entry_count": bib_entry_count,
        "effective_target": [eff_min, eff_max],
        "section_distribution": distribution,
        "named_methods_found": named_methods_found,
        "uncited_named_methods": uncited,
        "methods_zero_citations": methods_zero_citations,
        "reference_count_verdict": verdict,
        "adequacy_safe": n_major == 0,
        "findings": findings,
        "summary": {"major": n_major, "minor": n_minor, "notes": notes},
    }


def count_bib_entries(bib_path: Path) -> int:
    try:
        text = bib_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return -1
    return len(re.findall(r"^\s*@\w+\s*\{", text, re.M))


def main() -> int:
    ap = argparse.ArgumentParser(description="Reference adequacy gate (count + section + named-method coverage).")
    ap.add_argument("--manuscript", required=True, help="manuscript markdown/qmd")
    ap.add_argument("--bib", help="optional refs.bib (reports entry count)")
    ap.add_argument("--article-type", default="original_article",
                    help="repo paper-type name or target bucket (see ALIASES)")
    ap.add_argument("--journal-cap", type=int, help="optional journal reference cap")
    ap.add_argument("--out", help="write JSON artifact to this path")
    ap.add_argument("--strict", action="store_true", help="exit 1 if any Major adequacy finding")
    ap.add_argument("--quiet", action="store_true", help="suppress the stdout table")
    args = ap.parse_args()

    mp = Path(args.manuscript)
    if not mp.is_file():
        sys.stderr.write(f"ERROR: manuscript not found: {args.manuscript}\n")
        return 2
    manuscript = normalize(mp.read_text(encoding="utf-8"))

    bib_entry_count = None
    if args.bib:
        bp = Path(args.bib)
        if bp.is_file():
            bib_entry_count = count_bib_entries(bp)
        else:
            sys.stderr.write(f"WARN: bib not found: {args.bib} (bib entry count skipped)\n")

    result = assess(manuscript, args.article_type, args.journal_cap, bib_entry_count)

    if not args.quiet:
        s = result
        print("=" * 46)
        print(" Reference Adequacy Gate (count + named methods)")
        print("=" * 46)
        print(f" Article type   : {s['article_type']} -> {s['article_bucket']}")
        print(f" Cited refs     : {s['cited_reference_count']}  "
              f"(target {s['effective_target'][0]}-{s['effective_target'][1]}"
              f"{', cap ' + str(s['journal_cap']) if s['journal_cap'] is not None else ''})")
        d = s["section_distribution"]
        print(f" Distribution   : Intro {d['introduction']} / Methods {d['methods']} / "
              f"Results {d['results']} / Discussion {d['discussion']}")
        print(f" Methods 0-cite : {s['methods_zero_citations']}")
        if s["uncited_named_methods"]:
            print(f" Uncited methods: {', '.join(s['uncited_named_methods'])}")
        for f in s["findings"]:
            mark = "✗" if f["severity"] == "major" else "△"
            print(f" {mark} [{f['severity']}] {f['subtype']}: {f['description']}")
        print(f"\n Verdict: {s['reference_count_verdict']}  |  "
              f"{s['summary']['major']} major, {s['summary']['minor']} minor  |  "
              f"adequacy_safe={s['adequacy_safe']}")
        for note in s["summary"]["notes"]:
            print(f"   note: {note}")

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(result, indent=2), encoding="utf-8")
        if not args.quiet:
            print(f" wrote {args.out}")

    return 1 if (args.strict and result["summary"]["major"]) else 0


if __name__ == "__main__":
    sys.exit(main())
