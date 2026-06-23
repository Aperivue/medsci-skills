#!/usr/bin/env python3
"""Cohort arithmetic gate for observational studies (self-review Phase 2.5 / 2.5b).

Phase 2.5 covers n/N percentage arithmetic and Phase 2.5b reconciles SR/MA
study counts from ID sets. Neither covers the cohort-specific arithmetic that a
reviewer recomputes by hand and that survives a single prose pass because every
section echoes the same wrong number:

  1. RATE_BACKCALC     a reported incidence rate must invert to its own
                       numerator/denominator: rate ~= events / person-years * scale.
                       An impossible rate (more implied events than person-time, or
                       a rate that does not recompute from the stated events and PY)
                       is the failure mode where "X per 1,000 person-years" was
                       transcribed or computed wrong.
  2. CASCADE_SUM       a STROBE exclusion cascade must balance: start - sum(excluded)
                       == final analytic N; and a complete-case statement must
                       balance: total - missing == complete. A footnote that says
                       3,667 where 4,252 - 583 = 3,669 is this finding.
  3. PARTITION_OVERLAP an ordinal tier/stratum partition that is presented as
                       mutually exclusive must satisfy sum(stratum N) == unique
                       total and sum(stratum events) == total events. A tier split
                       whose denominators sum above the unique cohort double-counts
                       subjects; a table where every stratum n equals the grand
                       total is a stratum-total mis-entry.
  4. ANALYSIS_UNIT_   when --data carries a subject ID and records > unique
     UNDISCLOSED       subjects (health-screening / EMR / registry repeat
                       attendees), observations are non-independent -> anti-
                       conservative CIs. Fires only when the manuscript discloses
                       neither the analysis unit nor a one-record-per-subject
                       sensitivity. Pass --id-col, or it auto-detects a common ID
                       column name (with a cardinality guard).

The script is deterministic but conservative: it fires only when it can extract a
complete equation (all operands present in one window, or a Total row in a parsed
table, or recomputable columns in --data). Read the reconciliation table; a missed
case is safer than a false Major on a widely-used gate.

INPUTS
  --manuscript  manuscript markdown/text (required). Prose equations + GFM tables
                are parsed from it.
  --data        optional CSV for exact recompute. Auto-detected columns:
                  events / event / n_events / cases
                  person_years / py / person-years / personyears
                  rate / ir / incidence_rate          (RATE_BACKCALC)
                  stratum / tier / group + n / count + (events)  (PARTITION_OVERLAP)
                A row whose label normalizes to total/overall is the marginal.

OUTPUT
  A reconciliation table (stdout) and, with --out, a JSON artifact:
    {manuscript, data, claims[{verdict, severity, detail, where}], summary}
  verdicts RATE_BACKCALC / CASCADE_SUM / PARTITION_OVERLAP are Major candidates.
  Exit 1 (with --strict) when any Major-severity claim exists.

Stdlib-only (csv / json / re / argparse). Exit codes: 0 clean (or report-only),
1 Major claim(s) found (with --strict), 2 input/usage error.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

# Relative tolerance for a rate to "recompute" from events/PY (covers rounding of
# the displayed rate and of the inputs). 5% is generous; a real impossible rate
# misses it by far more.
RATE_REL_TOL = 0.05
SCALE_WORDS = {"100": 100, "1,000": 1000, "1000": 1000, "10,000": 10000, "10000": 10000,
               "100,000": 100000, "100000": 100000}

TOTAL_LABELS = ("total", "overall", "all", "whole cohort", "entire cohort", "full cohort",
                "all participants", "all subjects", "all patients")


# --- number / column helpers ----------------------------------------------

def _num(s: str):
    """Parse '1,234' / '1234' / '3.5' -> float, else None."""
    if s is None:
        return None
    m = re.search(r"-?\d[\d,]*\.?\d*", s.strip())
    if not m:
        return None
    try:
        return float(m.group(0).replace(",", ""))
    except ValueError:
        return None


def _ints_in(text: str) -> list[int]:
    """All comma-grouped integers in a span, as ints (drops decimals/percent)."""
    out = []
    for m in re.finditer(r"\d[\d,]*(?!\.\d)", text):
        try:
            out.append(int(m.group(0).replace(",", "")))
        except ValueError:
            pass
    return out


def _norm(s: str) -> str:
    s = s.lower()
    s = re.sub(r"\(.*?\)", " ", s)
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _is_total_label(label: str) -> bool:
    n = _norm(label)
    return any(n == t or n.startswith(t + " ") or n == t.replace(" ", "") for t in TOTAL_LABELS)


def _pick(header: list[str], hints: tuple[str, ...]):
    norm = [_norm(h) for h in header]
    for hint in hints:
        h = _norm(hint)
        for i, col in enumerate(norm):
            if col == h and h:
                return i
    for hint in hints:
        h = _norm(hint)
        for i, col in enumerate(norm):
            if h and h in col:
                return i
    return None


# --- Check 1: RATE_BACKCALC ------------------------------------------------

RATE_LINE_RE = re.compile(
    r"([0-9][0-9,]*\.?[0-9]*)\s*(?:per|/)\s*([0-9][0-9,]*)\s*person[-\s]?years?", re.I)
# The numerator must be a count glued to a count noun (events/cases), optionally
# "N incident cases/events". Two guards against grabbing the wrong integer:
#   (a) lookbehind (?<![A-Za-z0-9.]) so a tier label's digit ("T1") or a decimal's
#       fractional part ("0.97") is never captured as the numerator;
#   (b) drop the bare "incident" alternative, which matched the word in "incident
#       rate" and bound the nearest stray small integer (the false-positive source).
EVENTS_NEAR_RE = re.compile(
    r"(?<![A-Za-z0-9.])([0-9][0-9,]*)\s*(?:incident\s+)?(?:events?|cases?)\b", re.I)
PY_NEAR_RE = re.compile(r"([0-9][0-9,]*)\s*(?:person[-\s]?years?|py\b)", re.I)


def _sentences(text: str) -> list[str]:
    """Split into sentences after flattening intra-paragraph line wraps, so a
    sentence that the source wrapped across lines is still one unit. Markdown
    table rows (pipe-delimited) are kept as their own units."""
    units = []
    for para in re.split(r"\n[ \t]*\n", text):
        if para.lstrip().startswith("|"):
            units.extend(para.splitlines())
            continue
        flat = re.sub(r"\s*\n\s*", " ", para).strip()
        units.extend(re.split(r"(?<=[.;])\s+", flat))
    return [u for u in units if u.strip()]


def check_rate_text(text: str) -> list[dict]:
    """Fire when a single sentence carries a rate, an event count, and a
    person-time, and the rate does not recompute from them."""
    claims = []
    for line in _sentences(text):
        rm = RATE_LINE_RE.search(line)
        if not rm:
            continue
        rate = _num(rm.group(1))
        scale = _num(rm.group(2))
        if rate is None or not scale:
            continue
        em = EVENTS_NEAR_RE.search(line)
        # the PY in "rate per <scale> person-years" is the scale, not the cohort PY;
        # the cohort PY is a *different*, larger person-time figure in the same span.
        py_candidates = [int(g.replace(",", "")) for g in PY_NEAR_RE.findall(line)]
        py_candidates = [p for p in py_candidates if p != int(scale)]
        if not em or not py_candidates:
            continue
        events = _num(em.group(1))
        py = max(py_candidates)  # cohort person-time is the larger figure
        if events is None or py <= 0:
            continue
        expected = events / py * scale
        if expected <= 0:
            continue
        if abs(rate - expected) / max(expected, 1e-9) > RATE_REL_TOL:
            claims.append({
                "verdict": "RATE_BACKCALC",
                "severity": "Major",
                "detail": (f"reported rate {rate:g} per {int(scale):,} PY does not recompute "
                           f"from {int(events):,} events / {int(py):,} PY "
                           f"(= {expected:.4g} per {int(scale):,})"),
                "where": line.strip()[:160],
            })
    return claims


def check_rate_csv(rows: list[dict]) -> list[dict]:
    claims = []
    if not rows:
        return claims
    header = list(rows[0].keys())
    ei = _pick(header, ("events", "event", "n_events", "cases", "n_cases"))
    pi = _pick(header, ("person_years", "person-years", "personyears", "py", "person years"))
    ri = _pick(header, ("rate", "ir", "incidence_rate", "incidence rate"))
    si = _pick(header, ("scale", "per", "rate_per"))
    if ei is None or pi is None or ri is None:
        return claims
    cols = list(header)
    for idx, row in enumerate(rows):
        events = _num(row[cols[ei]])
        py = _num(row[cols[pi]])
        rate = _num(row[cols[ri]])
        scale = _num(row[cols[si]]) if si is not None else 1000.0
        if None in (events, py, rate) or not scale or py <= 0:
            continue
        expected = events / py * scale
        if expected <= 0:
            continue
        if abs(rate - expected) / max(expected, 1e-9) > RATE_REL_TOL:
            claims.append({
                "verdict": "RATE_BACKCALC",
                "severity": "Major",
                "detail": (f"row {idx + 1}: rate {rate:g} per {int(scale):,} PY != "
                           f"{events:g}/{py:g}*{int(scale):,} = {expected:.4g}"),
                "where": f"--data row {idx + 1}",
            })
    return claims


# --- Check 2: CASCADE_SUM --------------------------------------------------

COMPLETE_CASE_RE = re.compile(
    r"\b(?:of|among|from)\s+([0-9][0-9,]{2,})\b.{0,80}?"
    r"\b([0-9][0-9,]{1,})\s*(?:had|were|with)?\s*"
    r"(?:missing|incomplete|excluded|without)\b.{0,80}?"
    r"\b(?:leaving|remaining|resulting in|yielded?|left|final(?:ly)?|analyti\w+|included)\D{0,20}"
    r"([0-9][0-9,]{2,})\b",
    re.I | re.S)

START_RE = re.compile(
    r"\b([0-9][0-9,]{2,})\b\s*(?:participants?|subjects?|patients?|individuals?|records?)?\s*"
    r"(?:were\s+)?(?:initially\s+)?(?:screened|assessed|identified|enrolled|eligible|"
    r"recruited|included for screening)", re.I)
EXCLUDED_RE = re.compile(
    r"(?:excluded|removed)\D{0,20}?([0-9][0-9,]{1,})\b"
    r"|\b([0-9][0-9,]{1,})\s*(?:were\s+)?(?:excluded|removed)", re.I)
FINAL_RE = re.compile(
    r"\b(?:final|analytic|included|remaining)\D{0,30}?([0-9][0-9,]{2,})\b"
    r"|\b([0-9][0-9,]{2,})\b\D{0,20}(?:were included|comprised the (?:final|analytic)|"
    r"in the (?:final|analytic))", re.I)


def check_cascade_text(text: str) -> list[dict]:
    claims = []
    # (a) complete-case: total - missing == complete
    for m in COMPLETE_CASE_RE.finditer(text):
        total, missing, complete = (_num(m.group(1)), _num(m.group(2)), _num(m.group(3)))
        if None in (total, missing, complete):
            continue
        if abs((total - missing) - complete) >= 1:  # off by >= 1 (not rounding)
            claims.append({
                "verdict": "CASCADE_SUM",
                "severity": "Major",
                "detail": (f"complete-case arithmetic: {int(total):,} - {int(missing):,} = "
                           f"{int(total - missing):,}, but text states {int(complete):,}"),
                "where": m.group(0).strip()[:160],
            })
    # (b) exclusion cascade: start - sum(excluded) == final (within a flow window)
    sm = START_RE.search(text)
    fm = FINAL_RE.search(text)
    if sm and fm and fm.start() > sm.start():
        window = text[sm.start():fm.end()]
        start = _num(sm.group(1))
        final = next((_num(g) for g in fm.groups() if g), None)
        excluded = []
        for em in EXCLUDED_RE.finditer(window):
            v = next((g for g in em.groups() if g), None)
            if v:
                excluded.append(int(v.replace(",", "")))
        if start is not None and final is not None and excluded:
            if abs((start - sum(excluded)) - final) >= 1:
                claims.append({
                    "verdict": "CASCADE_SUM",
                    "severity": "Major",
                    "detail": (f"exclusion cascade: {int(start):,} - "
                               f"({' + '.join(f'{e:,}' for e in excluded)}) = "
                               f"{int(start - sum(excluded)):,}, but final stated {int(final):,}"),
                    "where": "study-population flow",
                })
    return claims


# --- Check 3: PARTITION_OVERLAP --------------------------------------------

def _parse_md_tables(text: str) -> list[list[list[str]]]:
    """Return GFM tables as lists of cell-rows (header + body, separator dropped)."""
    tables, cur = [], []
    for line in text.splitlines():
        if line.lstrip().startswith("|") and line.count("|") >= 2:
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if all(re.fullmatch(r":?-{2,}:?", c) or c == "" for c in cells) and cur:
                continue  # separator row
            cur.append(cells)
        else:
            if len(cur) >= 2:
                tables.append(cur)
            cur = []
    if len(cur) >= 2:
        tables.append(cur)
    return tables


def _partition_from_rows(label_of, n_of, ev_of, rows, source: str) -> list[dict]:
    claims = []
    body, total_row = [], None
    for r in rows:
        if _is_total_label(label_of(r)):
            total_row = r
        else:
            body.append(r)
    ns = [n_of(r) for r in body]
    ns = [x for x in ns if x is not None]
    if len(ns) < 2:
        return claims
    # all-equal-to-total mis-entry
    if total_row is not None:
        tot_n = n_of(total_row)
        if tot_n is not None and all(abs(x - tot_n) < 1 for x in ns):
            claims.append({
                "verdict": "PARTITION_OVERLAP",
                "severity": "Major",
                "detail": (f"every stratum n equals the grand total ({int(tot_n):,}) — "
                           f"stratum-total mis-entry, not a partition"),
                "where": source,
            })
            return claims
        if tot_n is not None and abs(sum(ns) - tot_n) >= 1:
            claims.append({
                "verdict": "PARTITION_OVERLAP",
                "severity": "Major",
                "detail": (f"stratum N sum to {int(sum(ns)):,} but the stated total is "
                           f"{int(tot_n):,} (difference {int(sum(ns) - tot_n):+,}) — "
                           f"non-disjoint strata or a missing/extra row"),
                "where": source,
            })
        # events partition
        evs = [ev_of(r) for r in body]
        evs = [x for x in evs if x is not None]
        tot_ev = ev_of(total_row)
        if len(evs) >= 2 and tot_ev is not None and abs(sum(evs) - tot_ev) >= 1:
            claims.append({
                "verdict": "PARTITION_OVERLAP",
                "severity": "Major",
                "detail": (f"stratum events sum to {int(sum(evs)):,} but total events "
                           f"stated {int(tot_ev):,}"),
                "where": source,
            })
    return claims


def check_partition_md(text: str) -> list[dict]:
    claims = []
    for tbl in _parse_md_tables(text):
        header = tbl[0]
        ni = _pick(header, ("n", "count", "number", "no", "denominator", "subjects", "patients"))
        ei = _pick(header, ("events", "event", "cases", "outcomes", "incident"))
        if ni is None:
            continue
        li = 0  # first column is the stratum label by convention
        if ni == li:
            li = 1 if len(header) > 1 else 0

        def label_of(r, li=li):
            return r[li] if li < len(r) else ""

        def n_of(r, ni=ni):
            return _num(r[ni]) if ni < len(r) else None

        def ev_of(r, ei=ei):
            return _num(r[ei]) if (ei is not None and ei < len(r)) else None

        claims += _partition_from_rows(label_of, n_of, ev_of, tbl[1:],
                                       source=f"table[{' | '.join(header)[:60]}]")
    return claims


def check_partition_csv(rows: list[dict]) -> list[dict]:
    if not rows:
        return []
    header = list(rows[0].keys())
    li = _pick(header, ("stratum", "tier", "group", "category", "level", "label"))
    ni = _pick(header, ("n", "count", "number", "denominator", "subjects", "patients"))
    ei = _pick(header, ("events", "event", "cases", "outcomes"))
    if li is None or ni is None:
        return []
    cols = list(header)

    def label_of(r):
        return r[cols[li]]

    def n_of(r):
        return _num(r[cols[ni]])

    def ev_of(r):
        return _num(r[cols[ei]]) if ei is not None else None

    return _partition_from_rows(label_of, n_of, ev_of, rows, source="--data partition")


# --- Check 4: ANALYSIS_UNIT_UNDISCLOSED ------------------------------------
# Health-screening / EMR / registry cohorts routinely have repeat attendees, so a
# record count is not a subject count. When the data carry a subject ID and
# records > subjects, non-independent observations give anti-conservative CIs. The
# finding is the *undisclosed* gap: fire only when the manuscript neither states
# the analysis unit nor reports a one-record-per-subject sensitivity.

# Safelist of normalized ID column names for auto-detection (tight, to avoid
# mistaking a low-cardinality flag like "valid" for an identifier). Explicit
# --id-col bypasses both the safelist and the cardinality guard.
ID_NAME_SAFELIST = {
    "id", "mockid", "mock id", "subjectid", "subject id", "patientid", "patient id",
    "personid", "person id", "recordid", "record id", "studyid", "study id",
    "pid", "eid", "uid", "mrn",
}

UNIT_STATED_RE = re.compile(
    r"one record per subject|per[-\s]subject|per subject|analysis unit|analytic unit|"
    r"screening encounter|one observation per (?:subject|participant|person)|"
    r"one row per (?:subject|participant|person)|first (?:qualifying )?(?:visit|encounter)",
    re.IGNORECASE)
SENSITIVITY_STATED_RE = re.compile(
    r"first[-\s](?:visit|encounter)|one[-\s]record[-\s]per[-\s]subject|de[-\s]?duplicat|"
    r"unique (?:subject|participant|individual)s?|repeat (?:attendee|visit|screen)|"
    r"sensitivity analysis[^.]{0,80}(?:subject|visit|first|repeat)",
    re.IGNORECASE)


def _detect_id_col(header: list[str], rows: list[dict], explicit: str | None) -> str | None:
    if explicit:
        for h in header:
            if _norm(h) == _norm(explicit) or h == explicit:
                return h
        sys.stderr.write(f"WARN: --id-col '{explicit}' not found in {header}\n")
        return None
    n = len(rows)
    for h in header:
        if _norm(h) in ID_NAME_SAFELIST:
            distinct = len({(r.get(h) or "").strip() for r in rows})
            if n and distinct >= 0.5 * n:   # subject-level, not a low-cardinality flag
                return h
    return None


def check_analysis_unit(rows: list[dict], text: str, id_col: str | None) -> list[dict]:
    if not rows:
        return []
    header = list(rows[0].keys())
    col = _detect_id_col(header, rows, id_col)
    if not col:
        return []
    ids = [(r.get(col) or "").strip() for r in rows]
    ids = [i for i in ids if i]
    nrow = len(ids)
    counts: dict[str, int] = {}
    for i in ids:
        counts[i] = counts.get(i, 0) + 1
    subjects = len(counts)
    if nrow <= subjects:
        return []                                   # already one record per subject
    if UNIT_STATED_RE.search(text) or SENSITIVITY_STATED_RE.search(text):
        return []                                   # disclosed -> not a finding
    repeats = sum(1 for c in counts.values() if c > 1)
    max_visits = max(counts.values())
    return [{
        "verdict": "ANALYSIS_UNIT_UNDISCLOSED",
        "severity": "Major",
        "detail": (f"records={nrow:,}, unique_subjects={subjects:,}, "
                   f"repeat_subjects={repeats:,}, max_visits={max_visits} "
                   f"(id column '{col}'); the manuscript states neither the analysis "
                   f"unit nor a one-record-per-subject sensitivity, so non-independent "
                   f"observations give anti-conservative CIs"),
        "where": f"--data id column '{col}'",
    }]


# --- driver ----------------------------------------------------------------

def load_csv(path: str) -> list[dict]:
    p = Path(path)
    if not p.is_file():
        sys.stderr.write(f"ERROR: --data not found: {path}\n")
        sys.exit(2)
    with p.open(encoding="utf-8-sig", newline="") as f:
        return [r for r in csv.DictReader(f)]


def analyze(manuscript: str, data: str | None, id_col: str | None = None) -> dict:
    p = Path(manuscript)
    if not p.is_file():
        sys.stderr.write(f"ERROR: manuscript not found: {manuscript}\n")
        sys.exit(2)
    text = p.read_text(encoding="utf-8")

    claims = []
    claims += check_rate_text(text)
    claims += check_cascade_text(text)
    claims += check_partition_md(text)

    if data:
        rows = load_csv(data)
        claims += check_rate_csv(rows)
        claims += check_partition_csv(rows)
        claims += check_analysis_unit(rows, text, id_col)

    n_major = sum(1 for c in claims if c["severity"] == "Major")
    return {
        "manuscript": str(p),
        "data": data,
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
        lines.append("| (none) | — | no cohort-arithmetic discrepancy detected |")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Cohort arithmetic gate (Phase 2.5 / 2.5b).")
    ap.add_argument("--manuscript", required=True, help="manuscript markdown/text")
    ap.add_argument("--data", help="optional CSV for exact recompute (rate / partition / analysis-unit)")
    ap.add_argument("--id-col", help="subject-ID column in --data for the records-vs-subjects "
                                     "analysis-unit check (auto-detected from common ID names if omitted)")
    ap.add_argument("--out", help="write JSON artifact to this path")
    ap.add_argument("--strict", action="store_true", help="exit 1 if any Major claim exists")
    ap.add_argument("--quiet", action="store_true", help="suppress stdout table")
    args = ap.parse_args()

    result = analyze(args.manuscript, args.data, args.id_col)

    if not args.quiet:
        print("=" * 41)
        print(" Cohort Arithmetic (Phase 2.5 / 2.5b)")
        print("=" * 41)
        print(render(result))
        print()
        s = result["summary"]
        if s["n_major"]:
            print(f"MAJOR candidate: {s['n_major']} cohort-arithmetic discrepancy(ies).")
        else:
            print("OK: no cohort-arithmetic discrepancy detected.")

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(result, indent=2), encoding="utf-8")
        if not args.quiet:
            print(f"\nwrote {args.out}")

    return 1 if (args.strict and result["summary"]["n_major"]) else 0


if __name__ == "__main__":
    sys.exit(main())
