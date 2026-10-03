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
  3. REGISTRATION CHRONOLOGY — a "prospectively registered" claim is falsifiable
     against the manuscript's own dates: if the registration date postdates search
     completion, the review was registered retrospectively. Manuscript-internal
     (needs no external prereg artifact); include supplement text in --manuscript
     to catch an overclaim that survives only in the supplement.

Figure/flow-count reconciliation, Methods-promised-analysis completeness, and
imputation-input integrity are separate subchecks (see /make-figures and
/write-paper); the JSON schema below reserves their `type` values so they can be
added without a breaking change.

INPUTS
  --manuscript  manuscript markdown/text.
  --prereg      pre-registration / protocol / project.yaml text (for estimand
                provenance). Optional; without it only the post-hoc-reassignment
                language scan and the E-value check run.
  --evalues     evalues.json: the E-values the manuscript reports, declared with
                their risk ratio and CI (references/evalues_schema.md). Each is
                recomputed (VanderWeele-Ding; the CI E-value from the limit nearest
                1, and 1 when the CI includes 1) over the printed precision of every
                number. Optional; the prose E-value scan runs either way.

OUTPUT  (--out path)
  {"claims": [{claim_id, type, prose_value, artifact_source, verdict, detail}],
   "summary": {...}}
  Major verdicts: PRIMARY_REASSIGNED (explicit post-hoc re-designation),
                  EVALUE_ARITHMETIC.
  Advisory flags (review, not strict-fail): ESTIMAND_DRIFT (fuzzy prereg↔manuscript
                  primary token overlap — confirm against the registration first),
                  PRIMARY_DISCLOSURE_NOTE (honest manuscript-stage disclosure),
                  EVALUE_NON_PRIMARY, EVALUE_UNVERIFIABLE, FLAG_NO_PREREG_PRIMARY.
  With --evalues: EVALUE_DECLARED_MISMATCH (Major: the declared point or CI
                  E-value cannot come from the declared RR at any value its rounding
                  allows); Minor EVALUE_DECLARED_NOT_IN_TEXT (the declared point
                  E-value is not a number in the manuscript), UNLISTED_METHOD and
                  EVALUE_DECLARED_NOT_ASSESSED (an "other:<description>" measure).

Stdlib-only (re / json / math / argparse). Exit codes: 0 clean (or report-only),
1 a Major verdict exists (with --strict), 2 input/usage error or a malformed
--evalues file (the message names the field).
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from decimal import Context, Decimal, InvalidOperation
from pathlib import Path

from _frontmatter import strip_frontmatter

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


# --- Check: REGISTRATION_CHRONOLOGY ----------------------------------------
# A "prospectively registered" claim is falsifiable against the manuscript's own
# dates: if the registration date postdates search completion, the review was
# registered *retrospectively*, and a reviewer flags the overclaim on sight. This
# is manuscript-internal (no external prereg artifact needed) -- both dates and the
# claim live in the text (body or supplement). Fires only when a prospective claim
# co-occurs with a registry AND both dates parse AND registration > search-end.
_MONTHS = ("January|February|March|April|May|June|July|August|September|October|"
           "November|December")
_MONTH_NUM = {m.lower(): i + 1 for i, m in enumerate(_MONTHS.split("|"))}
_DATE = (rf"\d{{4}}-\d{{2}}-\d{{2}}|\d{{1,2}}\s+(?:{_MONTHS})\s+\d{{4}}|"
         rf"(?:{_MONTHS})\s+\d{{1,2}},?\s+\d{{4}}")
_PROSPECTIVE_RE = re.compile(r"\bprospectiv\w*\b", re.I)
_REGISTRY_RE = re.compile(r"\b(?:PROSPERO|CRD42\d{9}|OSF|ClinicalTrials|NCT\d{6,})\b", re.I)
_REG_DATE_RE = re.compile(
    rf"(?:registered|registration|PROSPERO|CRD42\d{{9}}|OSF)[^.]*?\bon\b\s+({_DATE})"
    rf"|(?:registered|registration)[^.]{{0,60}}?({_DATE})", re.I)
_SEARCH_END_RE = re.compile(
    rf"search\w*[^.]*?\b(?:to|through|up to|until|inception to)\b\s+({_DATE})"
    rf"|search\w*[^.]{{0,80}}?({_DATE})", re.I)


def _parse_date(s: str) -> tuple[int, int, int] | None:
    s = s.strip()
    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        return (int(m.group(1)), int(m.group(2)), int(m.group(3)))
    m = re.fullmatch(rf"(\d{{1,2}})\s+({_MONTHS})\s+(\d{{4}})", s, re.I)
    if m:
        return (int(m.group(3)), _MONTH_NUM[m.group(2).lower()], int(m.group(1)))
    m = re.fullmatch(rf"({_MONTHS})\s+(\d{{1,2}}),?\s+(\d{{4}})", s, re.I)
    if m:
        return (int(m.group(3)), _MONTH_NUM[m.group(1).lower()], int(m.group(2)))
    return None


def _first_group(m) -> str | None:
    return next((g for g in m.groups() if g), None) if m else None


def check_registration_chronology(manuscript: str) -> list[dict]:
    claims: list[dict] = []
    if not (_PROSPECTIVE_RE.search(manuscript) and _REGISTRY_RE.search(manuscript)):
        return claims
    reg_s = _first_group(_REG_DATE_RE.search(manuscript))
    srch_s = _first_group(_SEARCH_END_RE.search(manuscript))
    if not reg_s or not srch_s:
        return claims
    reg, srch = _parse_date(reg_s), _parse_date(srch_s)
    if not reg or not srch or reg <= srch:
        return claims
    claims.append({
        "claim_id": "registration-chronology",
        "type": "registration",
        "prose_value": f"registered {reg_s.strip()}",
        "artifact_source": f"search completed {srch_s.strip()} (manuscript)",
        "verdict": "REGISTRATION_CHRONOLOGY",
        "detail": (f"a prospective-registration claim, but registration ({reg_s.strip()}) postdates "
                   f"search completion ({srch_s.strip()}) — the review was registered "
                   f"retrospectively; reframe as \"registered with\" or correct the chronology"),
    })
    return claims


# --- Declared E-values (--evalues evalues.json) -----------------------------
# {"entries": [{"id", "measure", "estimate", "ci_low", "ci_high", "evalue_point",
#   "evalue_ci"?, "location"?}], "notes"?}. Schema: references/evalues_schema.md.
# The prose scan above cannot read every way an E-value is written and cannot see a
# CI-limit E-value (SR-02); a declared table can be checked exactly. Every printed
# number is rounded, so each value is read as the interval of its printed precision
# and a Major fires only when the recomputed and declared intervals cannot meet.
EV_TOP_KEYS = {"entries", "notes"}
EV_ENTRY_KEYS = {"id", "measure", "estimate", "ci_low", "ci_high", "evalue_point",
                 "evalue_ci", "location"}
EV_NUM_KEYS = ("estimate", "ci_low", "ci_high", "evalue_point", "evalue_ci")
# Only the risk ratio: no reference in this repository states an OR->RR or HR->RR
# conversion, so an OR or HR is declared as "other:<description>" or converted first.
EV_MEASURES = {"rr": "rr", "risk_ratio": "rr"}
_EV_OTHER = re.compile(r"^\s*other\s*:(.*)$", re.I | re.S)
_EV_NUMSTR = re.compile(r"^\s*(\d+(?:\.\d+)?|\.\d+)\s*$")
_EV_TEXT_NUM = re.compile(r"(?<![\d.])(\d+(?:\.\d+)?)(?![\d])")
_EV_MIN, _EV_MAX = Decimal("1e-300"), Decimal("1e300")
_EV_CTX = Context(prec=50)


class EValuesError(ValueError):
    pass


class _JNum(str):
    """A JSON number literal, kept as its printed text so its precision survives."""


def _ev_short(v) -> str:
    if isinstance(v, str):
        r = repr(str(v))
    elif isinstance(v, (list, dict)):
        r = f"a {type(v).__name__}"
    else:
        r = repr(v)
    return r if len(r) <= 60 else r[:57] + "..."


def _ev_reject_constant(name: str):
    raise EValuesError(f"{name} is not a finite number")


def _ev_number(v, where: str) -> Decimal:
    if isinstance(v, _JNum):
        text = str(v)
    elif isinstance(v, str) and not isinstance(v, bool):
        if not _EV_NUMSTR.match(v):
            raise EValuesError(f"{where}: {_ev_short(v)} is not a plain decimal number "
                               "(digits with an optional decimal point, no sign or exponent)")
        text = v.strip()
    else:
        raise EValuesError(f"{where}: expected a number or a number string, got {_ev_short(v)}")
    if len(text) > 400:
        raise EValuesError(f"{where}: {_ev_short(text)} is out of range")
    try:
        d = Decimal(text)
    except InvalidOperation:
        raise EValuesError(f"{where}: {_ev_short(text)} is not a number")
    if not d.is_finite() or not math.isfinite(float(d)):
        raise EValuesError(f"{where}: {_ev_short(text)} is not a finite number")
    if d <= 0:
        raise EValuesError(f"{where}: {_ev_short(text)} must be greater than 0")
    if not (_EV_MIN <= d <= _EV_MAX):
        raise EValuesError(f"{where}: {_ev_short(text)} is out of range (1e-300 to 1e300)")
    return d


def load_evalues(path: Path) -> list[dict]:
    try:
        m = json.loads(path.read_text(encoding="utf-8-sig"), parse_constant=_ev_reject_constant,
                       parse_float=_JNum, parse_int=_JNum)
    except (OSError, ValueError, RecursionError) as e:   # ValueError covers JSONDecodeError
        raise EValuesError(f"cannot read evalues file: {str(e)[:200]}")
    if not isinstance(m, dict):
        raise EValuesError("evalues file must be a JSON object with an \"entries\" list")
    extra = set(m) - EV_TOP_KEYS
    if extra:
        raise EValuesError(f"unknown top-level key(s) {_ev_short(sorted(extra))}; "
                           f"allowed {sorted(EV_TOP_KEYS)}")
    entries = m.get("entries")
    if not isinstance(entries, list) or not entries:
        raise EValuesError("entries: expected a non-empty list")
    out = []
    for i, e in enumerate(entries):
        w = f"entries[{i}]"
        if not isinstance(e, dict):
            raise EValuesError(f"{w}: expected an object")
        extra = set(e) - EV_ENTRY_KEYS
        if extra:
            raise EValuesError(f"{w}: unknown key(s) {_ev_short(sorted(extra))}; "
                               f"allowed {sorted(EV_ENTRY_KEYS)}")
        eid = e.get("id")
        if not isinstance(eid, str) or isinstance(eid, _JNum) or not eid.strip():
            raise EValuesError(f"{w}.id: expected a non-empty string")
        meas = e.get("measure")
        if not isinstance(meas, str) or isinstance(meas, _JNum) or not meas.strip():
            raise EValuesError(f"{w}.measure: expected a string")
        om = _EV_OTHER.match(meas)
        if om:
            if not om.group(1).strip():
                raise EValuesError(f"{w}.measure: 'other:' needs a description")
            measure = "other"
        else:
            key = re.sub(r"[\s\-]+", "_", meas.strip().lower())
            if key not in EV_MEASURES:
                raise EValuesError(
                    f"{w}.measure: {_ev_short(meas)} is not one of ['rr']; no conversion from an "
                    "OR or HR to a risk ratio is stated in this skill's references, so declare a "
                    "converted RR as \"rr\" or write \"other:<description>\"")
            measure = EV_MEASURES[key]
        loc = e.get("location")
        if loc is not None and (not isinstance(loc, str) or isinstance(loc, _JNum)):
            raise EValuesError(f"{w}.location: expected a string")
        nums = {}
        for k in EV_NUM_KEYS:
            if k not in e:
                if k == "evalue_ci":
                    continue
                raise EValuesError(f"{w}.{k}: required")
            nums[k] = _ev_number(e[k], f"{w}.{k}")
        if not (nums["ci_low"] <= nums["estimate"] <= nums["ci_high"]):
            raise EValuesError(f"{w}: expected ci_low <= estimate <= ci_high, got "
                               f"{nums['ci_low']} / {nums['estimate']} / {nums['ci_high']}")
        out.append({"id": eid.strip(), "measure": measure, "measure_raw": meas.strip(),
                    "location": loc, **nums})
    return out


def _half_unit(d: Decimal) -> Decimal:
    """Half a unit in the last printed place of d ("2.30" -> 0.005, "2" -> 0.5)."""
    return Decimal(5).scaleb(d.as_tuple().exponent - 1)


def _ev_dec(g: Decimal) -> Decimal:
    """VanderWeele-Ding E-value on the RR scale (g = RR, or 1/RR when RR < 1)."""
    if g < 1:
        g = _EV_CTX.divide(Decimal(1), g)
    return _EV_CTX.add(g, _EV_CTX.sqrt(_EV_CTX.multiply(g, _EV_CTX.subtract(g, Decimal(1)))))


def _ev_range(lo: Decimal, hi: Decimal) -> tuple[Decimal, Decimal]:
    """[Emin, Emax] of the E-value over every RR in [lo, hi]."""
    a, b = _ev_dec(lo), _ev_dec(hi)
    if lo <= 1 <= hi:
        return Decimal(1), max(a, b)
    return min(a, b), max(a, b)


def _ev_ci_range(e: dict) -> tuple[Decimal, Decimal]:
    """[Emin, Emax] of the CI E-value (near-null limit; 1 when the CI includes 1) over
    every estimate and limit inside their printed-precision intervals."""
    est, lo, hi = e["estimate"], e["ci_low"], e["ci_high"]
    p_lo, p_hi = est - _half_unit(est), est + _half_unit(est)
    vals: list[Decimal] = []
    if p_hi > 1:   # estimate may lie above 1: the near-null limit is ci_low
        h = _half_unit(lo)
        vals += [Decimal(1) if x <= 1 else _ev_dec(x) for x in (lo - h, lo + h)]
    if p_lo < 1:   # estimate may lie below 1: the near-null limit is ci_high
        h = _half_unit(hi)
        vals += [Decimal(1) if x >= 1 else _ev_dec(x) for x in (hi - h, hi + h)]
    if p_lo <= 1 <= p_hi:
        vals.append(Decimal(1))
    return min(vals), max(vals)


def _fmt(d: Decimal) -> str:
    return f"{float(d):.4g}"


def _text_numbers(manuscript: str) -> set[Decimal]:
    out = set()
    for m in _EV_TEXT_NUM.finditer(manuscript.replace("·", ".")):
        tok = m.group(1)
        if len(tok) <= 40:
            out.add(Decimal(tok))
    return out


def check_declared_evalues(manuscript: str, entries: list[dict]) -> list[dict]:
    claims: list[dict] = []
    in_text = _text_numbers(manuscript)
    for e in entries:
        cid = f"EVDECL-{e['id']}"
        where = f" ({e['location']})" if e["location"] else ""
        if e["measure"] == "other":
            claims.append({
                "claim_id": cid, "type": "evalue_declared",
                "prose_value": f"measure {e['measure_raw']}",
                "artifact_source": "evalues.json",
                "verdict": "UNLISTED_METHOD",
                "detail": f"measure {e['measure_raw']!r}{where} is not on the allow-list ['rr']; "
                          "recorded, not recomputed.",
            })
            claims.append({
                "claim_id": cid, "type": "evalue_declared",
                "prose_value": f"E-value {e['evalue_point']}",
                "artifact_source": "evalues.json",
                "verdict": "EVALUE_DECLARED_NOT_ASSESSED",
                "detail": "the E-value arithmetic was not checked because the measure is not a "
                          "risk ratio; convert to an RR and declare \"rr\", or check it by hand.",
            })
        else:
            checks = [("point", "E-value", _ev_range(e["estimate"] - _half_unit(e["estimate"]),
                                                     e["estimate"] + _half_unit(e["estimate"])),
                       e["evalue_point"])]
            if "evalue_ci" in e:
                checks.append(("ci", "CI E-value", _ev_ci_range(e), e["evalue_ci"]))
            for tag, label, (emin, emax), decl in checks:
                h = _half_unit(decl)
                d_lo, d_hi = decl - h, decl + h
                ok = not (emax < d_lo or emin > d_hi)
                src = (f"RR {e['estimate']} ({e['ci_low']}-{e['ci_high']})")
                rng = (f"recomputes to {_fmt(emin)}-{_fmt(emax)} over the printed precision"
                       if emin != emax else f"recomputes to {_fmt(emin)}")
                claims.append({
                    "claim_id": f"{cid}-{tag}", "type": "evalue_declared",
                    "prose_value": f"{label} {decl}",
                    "artifact_source": f"recomputed (VanderWeele-Ding) from declared {src}",
                    "verdict": "OK" if ok else "EVALUE_DECLARED_MISMATCH",
                    "detail": (f"declared {label} {decl}{where} is consistent with {src}: {rng}."
                               if ok else
                               f"declared {label} {decl}{where} (read as {_fmt(d_lo)}-{_fmt(d_hi)}) "
                               f"cannot come from {src}: it {rng}"
                               + ("; the CI E-value uses the confidence limit nearest 1, and is 1 "
                                  "when the CI includes 1." if tag == "ci" else ".")),
                })
        if e["evalue_point"] not in in_text:
            claims.append({
                "claim_id": cid, "type": "evalue_declared",
                "prose_value": f"E-value {e['evalue_point']}",
                "artifact_source": "manuscript text",
                "verdict": "EVALUE_DECLARED_NOT_IN_TEXT",
                "detail": f"the declared E-value {e['evalue_point']}{where} is not a number anywhere "
                          "in the manuscript; check the declaration matches what is reported.",
            })
    return claims


MAJOR = {"PRIMARY_REASSIGNED", "EVALUE_ARITHMETIC", "REGISTRATION_CHRONOLOGY",
         "EVALUE_DECLARED_MISMATCH"}


def main() -> int:
    ap = argparse.ArgumentParser(description="Claim-vs-artifact cross-check (estimand + E-value).")
    ap.add_argument("--manuscript", required=True, help="manuscript markdown/text")
    ap.add_argument("--prereg", help="pre-registration / protocol / project.yaml text")
    ap.add_argument("--scripts", help="analysis-scripts directory (reconcile code primary/co-primary labels)")
    ap.add_argument("--evalues", help="evalues.json: declared E-values to recompute "
                    "(see references/evalues_schema.md)")
    ap.add_argument("--out", help="write JSON artifact to this path")
    ap.add_argument("--strict", action="store_true", help="exit 1 if any Major verdict")
    args = ap.parse_args()

    mp = Path(args.manuscript)
    if not mp.is_file():
        sys.stderr.write(f"ERROR: manuscript not found: {args.manuscript}\n")
        return 2
    evalues = None
    if args.evalues is not None:
        ep = Path(args.evalues)
        if not ep.is_file():
            sys.stderr.write(f"ERROR: evalues file not found: {args.evalues}\n")
            return 2
        try:
            evalues = load_evalues(ep)
        except (EValuesError, ValueError, OverflowError, RecursionError, ArithmeticError) as e:
            sys.stderr.write(f"ERROR: {args.evalues}: {e}\n")
            return 2
    # Collapse hard-wrap newlines to spaces so a sentence-level claim is not split
    # across lines (the decimal points inside HR/E-value figures must survive).
    def _unwrap(t: str) -> str:
        return re.sub(r"\s*\n\s*", " ", t)

    # Strip the YAML front matter before any estimand pattern runs. A project that
    # honestly logs "the primary endpoint was changed ..." in a `changelog:` block was
    # read as a body self-admission and given PRIMARY_REASSIGNED — a Major that fires
    # harder the more openly a project records its own history, which is exactly the
    # Major most likely to get waved through.
    manuscript = _unwrap(strip_frontmatter(mp.read_text(encoding="utf-8")))
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
              + check_code_labels(manuscript, args.scripts)
              + check_registration_chronology(manuscript))
    if evalues is not None:
        claims += check_declared_evalues(manuscript, evalues)
    n_major = sum(1 for c in claims if c["verdict"] in MAJOR)
    n_flag = sum(1 for c in claims if c["verdict"] not in MAJOR and c["verdict"] != "OK")

    result = {
        "manuscript": str(mp),
        "prereg": args.prereg,
        **({"evalues": args.evalues} if evalues is not None else {}),
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
        Path(args.out).write_text(json.dumps({"detector": "check_claim_artifact", **result}, indent=2), encoding="utf-8")
        print(f"wrote {args.out}")

    return 1 if (args.strict and n_major) else 0


if __name__ == "__main__":
    sys.exit(main())
