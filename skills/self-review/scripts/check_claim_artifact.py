#!/usr/bin/env python3
"""Claim-vs-artifact cross-check for self-review Phase 2.5f (narrowed 1st scope).

The errors that survive a single-pass review are the ones where the manuscript
text is internally consistent but disagrees with an external artifact — the
pre-registration, the analysis code, the qc outputs. This gate checks the two
highest-value, deterministic instances:

  1. ESTIMAND PROVENANCE — does the manuscript's stated primary contrast match
     the pre-registered / protocol primary, and is there language admitting the
     primary was re-designated after results were known (outcome-dependent
     primary selection)?
  2. E-VALUE — is a reported E-value arithmetically consistent with its adjacent
     effect estimate, and is it attached to the *primary* estimate rather than a
     secondary/exploratory one quoted as if it bounded the headline claim?

Figure/flow-count reconciliation, Methods-promised-analysis completeness, and
imputation-input integrity are separate subchecks (see /make-figures and
/write-paper); the JSON schema below reserves their `type` values so they can be
added without a breaking change.

INPUTS
  --manuscript  manuscript markdown/text.
  --prereg      pre-registration / protocol / project.yaml text (for estimand
                provenance). Optional; without it only the post-hoc-reassignment
                language scan and the E-value check run.

OUTPUT  (--out path)
  {"claims": [{claim_id, type, prose_value, artifact_source, verdict, detail}],
   "summary": {...}}
  Major verdicts: PRIMARY_REASSIGNED (explicit post-hoc re-designation),
                  EVALUE_ARITHMETIC.
  Advisory flags (review, not strict-fail): ESTIMAND_DRIFT (fuzzy prereg↔manuscript
                  primary token overlap — confirm against the registration first),
                  PRIMARY_DISCLOSURE_NOTE (honest manuscript-stage disclosure),
                  EVALUE_NON_PRIMARY, EVALUE_UNVERIFIABLE, FLAG_NO_PREREG_PRIMARY.

Stdlib-only (re / json / math / argparse). Exit codes: 0 clean (or report-only),
1 a Major verdict exists (with --strict), 2 input/usage error.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

EVALUE_TOL = 0.15  # relative tolerance for E-value recompute

PRIMARY_RE = re.compile(
    r"[^.]*\bprimary\b[^.]*\b(outcome|endpoint|analysis|objective|contrast|comparison|model|estimand)[^.]*\.",
    re.I,
)
# Explicit post-hoc re-designation of the primary (Major): the estimand was
# changed / switched / re-designated, chosen post-hoc, or selected after results
# were known. This is a genuine integrity issue.
REASSIGN_RE = re.compile(
    r"\bprimary\b[^.]*\b(re-?designat|re-?assign|re-?defin|switch|chang)\w*|"
    r"\b(re-?designat|re-?assign)\w*[^.]*\bprimary\b|"
    r"\bpost[- ]?hoc\b[^.]*\bprimary\b|"
    r"\bprimary\b[^.]*\bafter\b[^.]*\bresult",
    re.I,
)
# Honest disclosure of a manuscript-stage analytical decision (ADVISORY, not Major):
# estimand-provenance guidance *recommends writing* exactly this. Flag only to confirm
# it is disclosed coequally with the pre-specified analysis, not to allege a violation.
# Only emitted when the explicit-reassignment pattern above does NOT also match.
DISCLOSURE_RE = re.compile(
    r"\bmanuscript[- ]stage\b[^.]*\b(decision|primary|analy)|"
    r"\b(decision|analys[ie]s)\b[^.]*\bmanuscript[- ]stage\b",
    re.I,
)
EFFECT_RE = re.compile(r"\b(s?HR|a?HR|a?OR|RR|hazard ratio|odds ratio|risk ratio)\b\D{0,8}(\d+\.\d+)", re.I)
# The E-value figure follows a connective (was / of / = / :), so the non-greedy
# scan does not grab the effect estimate's number from an adjacent "(HR 1.34)".
EVALUE_RE = re.compile(
    r"E[- ]?value\b[^\n]{0,90}?\b(?:was|were|of|is|=|:|reached|equals?(?:\s+to)?)\s*\(?(\d+\.\d+)",
    re.I,
)
NONPRIMARY_KW = ("secondary", "exploratory", "subgroup", "sensitivity", "supporting",
                 "cause-specific", "cancer-specific", "post-hoc", "post hoc", "non-primary")

# The manuscript asserts exactly ONE primary model/analysis (so a script annotating a
# model as "co-primary" is a third-SSOT drift).
SINGLE_PRIMARY = re.compile(
    r"\bsingle\s+primary\b|\ba\s+single\s+primary\b|\bone\s+primary\s+(?:model|analysis|endpoint|outcome)\b"
    r"|\bthe\s+primary\s+(?:model|analysis|endpoint|outcome)\b[^.]{0,70}?"
    r"(?:consistent\s+with\s+the\s+(?:registered|pre-?specified)|registered\s+analysis\s+plan)",
    re.I)
# A model annotated "co-primary" in analysis code (a comment, string, or variable).
CO_PRIMARY_CODE = re.compile(r"\bco[-\s]?primary\b", re.I)

STOP = set("the a an of for in on to and or with by is was were are be been being this that "
           "between association associated estimated using model analysis primary outcome "
           "endpoint study patients group as at from".split())


def _tokens(s: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", s.lower()) if w not in STOP and len(w) > 2}


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


# Structured pre-registration fields — the authoritative anchor when the prereg is
# a project.yaml / registration form with explicit keys. Comparing the manuscript
# primary sentence against these VALUES (which carry the actual variable names)
# beats comparing it against a free-text "Strategy for data synthesis" paragraph or
# a `# PRIMARY — locked` YAML comment, which are lexically dissimilar even when
# semantically identical.
_STRUCT_PRIMARY_RE = re.compile(
    r"^\s*(primary_(?:exposure|outcome|estimand|endpoint|contrast|model|comparison|analysis))\s*:\s*(.+?)\s*$",
    re.I | re.M,
)


def _structured_primary(prereg: str) -> list[str]:
    """Values of explicit primary_* keys in a structured prereg (YAML/form)."""
    out = []
    for m in _STRUCT_PRIMARY_RE.finditer(prereg):
        v = m.group(2).strip().strip("\"'").strip()
        if v and not v.startswith("#"):
            out.append(v)
    return out


def _strip_yaml_comments(text: str) -> str:
    """Drop whole-line YAML/# comments so PRIMARY_RE does not anchor on a
    `# PRIMARY — locked` annotation rather than a real primary-outcome statement."""
    return "\n".join(ln for ln in text.splitlines() if not ln.lstrip().startswith("#"))


def evalue_point(rr: float) -> float:
    """VanderWeele-Ding E-value for a point estimate (risk-ratio scale)."""
    g = rr if rr >= 1 else 1.0 / rr
    return g + math.sqrt(g * (g - 1.0))


def _flatten(t: str) -> str:
    return re.sub(r"\s*\n\s*", " ", t)


def check_estimand(manuscript: str, prereg: str | None, prereg_raw: str | None = None) -> list[dict]:
    claims = []
    man_primary = [m.group(0).strip() for m in PRIMARY_RE.finditer(manuscript)]

    # 1. Explicit post-hoc reassignment language (highest-confidence Major catch).
    m = REASSIGN_RE.search(manuscript)
    if m:
        claims.append({
            "claim_id": "EST-reassign",
            "type": "estimand",
            "prose_value": re.sub(r"\s+", " ", manuscript[max(0, m.start() - 40):m.end() + 40]).strip(),
            "artifact_source": "manuscript (self-admission)",
            "verdict": "PRIMARY_REASSIGNED",
            "detail": "Language indicates the primary was re-designated after results were known; "
                      "report the pre-specified and revised models coequally and disclose the change.",
        })
    else:
        # 1b. Honest manuscript-stage disclosure → advisory note, NOT a Major. The
        # estimand-provenance guidance recommends writing this; do not penalise it.
        d = DISCLOSURE_RE.search(manuscript)
        if d:
            claims.append({
                "claim_id": "EST-disclosure",
                "type": "estimand",
                "prose_value": re.sub(r"\s+", " ", manuscript[max(0, d.start() - 40):d.end() + 40]).strip(),
                "artifact_source": "manuscript (disclosed analytical decision)",
                "verdict": "PRIMARY_DISCLOSURE_NOTE",
                "detail": "Discloses a manuscript-stage analytical decision — the honest disclosure "
                          "estimand-provenance guidance recommends, not a violation. Confirm the "
                          "pre-specified and revised analyses are reported coequally. Advisory, not Major.",
            })

    # 2. Manuscript primary vs prereg primary (token overlap).
    if prereg:
        # Prefer explicit structured primary_* fields (authoritative). Structured
        # extraction needs the RAW (line-based) prereg — the flattened form has no
        # line boundaries. Otherwise fall back to free-text primary sentences, with
        # YAML comment lines stripped so the anchor is a real statement, not a
        # `# PRIMARY — locked` annotation.
        raw = prereg_raw if prereg_raw is not None else prereg
        struct = _structured_primary(raw)
        pre_primary = struct or [m.group(0).strip()
                                 for m in PRIMARY_RE.finditer(_flatten(_strip_yaml_comments(raw)))]
        anchor = "structured prereg field" if struct else "prereg primary sentence"
        if man_primary and pre_primary:
            # tokens of every manuscript primary sentence vs the union of prereg
            # anchors — a structured field's variable names need only appear somewhere
            # in the manuscript's primary description to count as consistent.
            man_tok = set().union(*[_tokens(a) for a in man_primary])
            pre_tok = set().union(*[_tokens(b) for b in pre_primary])
            score = _jaccard(man_tok, pre_tok)
            best_a = max(man_primary, key=lambda a: _jaccard(_tokens(a), pre_tok))
            # Structured-field match is more reliable, so a moderate overlap is a
            # soft "confirm", not a drift allegation. Free-text stays at the old 0.30.
            drift_cut, confirm_cut = (0.20, 0.40) if struct else (0.30, 0.30)
            verdict = ("ESTIMAND_DRIFT" if score < drift_cut
                       else "ESTIMAND_CONFIRM" if score < confirm_cut else "OK")
            claims.append({
                "claim_id": "EST-primary",
                "type": "estimand",
                "prose_value": re.sub(r"\s+", " ", best_a)[:160],
                "artifact_source": (re.sub(r"\s+", " ", " | ".join(pre_primary))[:160]),
                "verdict": verdict,
                "detail": f"manuscript↔{anchor} token overlap = {score:.2f} "
                          f"(<{drift_cut:.2f} → drift candidate; {drift_cut:.2f}–{confirm_cut:.2f} → "
                          f"confirm). ADVISORY: fuzzy token overlap is noisy; confirm against the "
                          f"actual registration before treating as drift.",
            })
        elif man_primary and not pre_primary:
            claims.append({
                "claim_id": "EST-primary",
                "type": "estimand",
                "prose_value": re.sub(r"\s+", " ", man_primary[0])[:160],
                "artifact_source": "prereg (no primary statement found)",
                "verdict": "FLAG_NO_PREREG_PRIMARY",
                "detail": "No primary-outcome statement located in the prereg/protocol; confirm one exists.",
            })
    return claims


def check_evalue(manuscript: str) -> list[dict]:
    claims = []
    for i, m in enumerate(EVALUE_RE.finditer(manuscript), 1):
        stated = float(m.group(1))
        # sentence window around the E-value
        start = manuscript.rfind(".", 0, m.start()) + 1
        end = manuscript.find(".", m.end())
        sent = manuscript[start:(end if end != -1 else len(manuscript))]
        eff = EFFECT_RE.search(sent)
        nonprimary = any(kw in sent.lower() for kw in NONPRIMARY_KW)

        if not eff:
            claims.append({
                "claim_id": f"EVAL-{i}",
                "type": "evalue",
                "prose_value": f"E-value {stated}",
                "artifact_source": "no adjacent effect estimate",
                "verdict": "EVALUE_UNVERIFIABLE",
                "detail": "No HR/OR/RR found in the same sentence; confirm the E-value is computed "
                          "for the declared primary estimate.",
            })
            continue

        rr = float(eff.group(2))
        recomputed = evalue_point(rr)
        rel = abs(stated - recomputed) / recomputed if recomputed else 1.0
        if rel > EVALUE_TOL:
            verdict = "EVALUE_ARITHMETIC"
            detail = (f"stated E-value {stated} but {eff.group(1)} {rr} recomputes to "
                      f"{recomputed:.2f} (rel. diff {rel:.0%} > {EVALUE_TOL:.0%}); the stated value "
                      "likely belongs to a different (e.g. non-primary) estimate.")
        elif nonprimary:
            verdict = "EVALUE_NON_PRIMARY"
            detail = (f"E-value {stated} matches {eff.group(1)} {rr} (recompute {recomputed:.2f}), "
                      "but the sentence references a secondary/exploratory estimate; confirm the "
                      "headline E-value bounds the PRIMARY contrast, not this one.")
        else:
            verdict = "OK"
            detail = f"E-value {stated} consistent with {eff.group(1)} {rr} (recompute {recomputed:.2f})."
        claims.append({
            "claim_id": f"EVAL-{i}",
            "type": "evalue",
            "prose_value": f"E-value {stated} ({eff.group(1)} {rr})",
            "artifact_source": "recomputed (VanderWeele-Ding)",
            "verdict": verdict,
            "detail": detail,
        })
    return claims


# ESTIMAND_DRIFT (fuzzy prereg↔manuscript token overlap) and PRIMARY_DISCLOSURE_NOTE
# (honest manuscript-stage disclosure) are ADVISORY, not Major: the docs require
# manual confirmation against the registration before either is acted on, and a P0
# that needs hand-confirmation is not a P0. Only explicit re-designation and a
# non-recomputing E-value are Major.
def check_code_labels(manuscript: str, scripts_dir: str | None) -> list[dict]:
    """Reconcile the manuscript's declared primary against analysis-script labels.

    Fires only the specific conflict: the manuscript asserts a SINGLE primary while an
    analysis script annotates a model as 'co-primary' — the code label is a third SSOT
    that drifts across revisions. Advisory (code comments can lag)."""
    claims: list[dict] = []
    if not scripts_dir:
        return claims
    d = Path(scripts_dir)
    if not d.exists() or not SINGLE_PRIMARY.search(manuscript):
        return claims
    for p in sorted(d.rglob("*")):
        if p.suffix.lower() not in (".r", ".py"):
            continue
        try:
            txt = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        m = CO_PRIMARY_CODE.search(txt)
        if not m:
            continue
        ln = txt[:m.start()].count("\n") + 1
        snippet = txt.splitlines()[ln - 1].strip()[:80] if ln - 1 < len(txt.splitlines()) else ""
        claims.append({
            "claim_id": "EST-code-label",
            "type": "estimand",
            "prose_value": "manuscript asserts a single primary model/analysis",
            "artifact_source": f"{p.name}:{ln} labels a model 'co-primary'",
            "verdict": "PRIMARY_LABEL_CODE_DRIFT",
            "detail": (f"the manuscript declares a SINGLE primary while an analysis script "
                       f"annotates a model as co-primary ({p.name}:{ln}: '{snippet}'); reconcile "
                       f"the code's primary/co-primary label with the declared estimand — code "
                       f"labels are a third SSOT that can drift across revisions. ADVISORY."),
        })
        break  # one is enough to prompt a reconcile
    return claims


MAJOR = {"PRIMARY_REASSIGNED", "EVALUE_ARITHMETIC"}


def main() -> int:
    ap = argparse.ArgumentParser(description="Claim-vs-artifact cross-check (estimand + E-value).")
    ap.add_argument("--manuscript", required=True, help="manuscript markdown/text")
    ap.add_argument("--prereg", help="pre-registration / protocol / project.yaml text")
    ap.add_argument("--scripts", help="analysis-scripts directory (reconcile code primary/co-primary labels)")
    ap.add_argument("--out", help="write JSON artifact to this path")
    ap.add_argument("--strict", action="store_true", help="exit 1 if any Major verdict")
    args = ap.parse_args()

    mp = Path(args.manuscript)
    if not mp.is_file():
        sys.stderr.write(f"ERROR: manuscript not found: {args.manuscript}\n")
        return 2
    # Collapse hard-wrap newlines to spaces so a sentence-level claim is not split
    # across lines (the decimal points inside HR/E-value figures must survive).
    def _unwrap(t: str) -> str:
        return re.sub(r"\s*\n\s*", " ", t)

    manuscript = _unwrap(mp.read_text(encoding="utf-8"))
    prereg = None
    prereg_raw = None
    if args.prereg:
        pp = Path(args.prereg)
        if pp.is_file():
            prereg_raw = pp.read_text(encoding="utf-8")
            prereg = _unwrap(prereg_raw)
        else:
            sys.stderr.write(f"WARN: prereg not found: {args.prereg} (estimand provenance limited)\n")

    claims = (check_estimand(manuscript, prereg, prereg_raw) + check_evalue(manuscript)
              + check_code_labels(manuscript, args.scripts))
    n_major = sum(1 for c in claims if c["verdict"] in MAJOR)
    n_flag = sum(1 for c in claims if c["verdict"] not in MAJOR and c["verdict"] != "OK")

    result = {
        "manuscript": str(mp),
        "prereg": args.prereg,
        "claims": claims,
        "summary": {"n_claims": len(claims), "n_major": n_major, "n_flag": n_flag,
                    "verdict": "MAJOR_CANDIDATE" if n_major else ("REVIEW" if n_flag else "OK")},
    }

    print("=" * 41)
    print(" Claim-vs-Artifact Cross-Check (Phase 2.5f)")
    print("=" * 41)
    for c in claims:
        mark = "✗" if c["verdict"] in MAJOR else ("△" if c["verdict"] != "OK" else "✓")
        print(f"{mark} [{c['claim_id']}] {c['verdict']}")
        print(f"    {c['detail']}")
    print(f"\n{n_major} Major candidate(s), {n_flag} flag(s).")

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"wrote {args.out}")

    return 1 if (args.strict and n_major) else 0


if __name__ == "__main__":
    sys.exit(main())
