#!/usr/bin/env python3
"""Confounding-completeness gate for observational studies (self-review Phase 2.5e).

The highest-yield observational reviewer finding is also the most mechanical: a
covariate that was *measured*, is *imbalanced across exposure groups* in the
baseline table, and is *absent from the adjustment set* is residual confounding
by a measured variable. A single-pass prose review misses it because the
manuscript text is internally consistent; only a join of the exposure-stratified
Table 1 against the Methods adjustment set exposes it. This script is that join
(probe O1 of observational_confounding.md), backported from the panel so the
deterministic finding lands without a multi-agent pass.

INPUTS
  --table1   exposure-stratified baseline table, CSV. One row per covariate.
             Needs a covariate-name column and a p-value (or SMD) column. Column
             names are auto-detected (case-insensitive); override with
             --name-col / --p-col / --smd-col. A file named like
             `table1_by_<exposure>.csv` is the convention.
  --adjusted adjustment-set variables. Either a path to a file (one variable per
             line, or a Methods paragraph the script greps after "adjusted for")
             or a comma-separated list passed inline with --adjusted-list.
  --exposure-defining[-list]
             covariates that are components of the exposure's own diagnostic
             criteria (e.g. BMI / glycaemia / lipids for a metabolic-syndrome or
             MASLD exposure). These are EXEMPT from the residual-confounding flag —
             adjusting for them is over-adjustment (probe O7), not a fix. The
             remedy for residual confounding is an extended-adjustment model with
             NON-defining prognostic covariates only.
  --group-cols A,B
             when the Table 1 has no p-value / SMD column but two exposure-stratum
             columns of "mean ± SD" (or "mean +/- SD") cells, name them here (or
             let the script auto-detect) and the SMD is computed per row. The
             "mean (SD)" paren form is intentionally NOT auto-parsed (it collides
             with "n (%)"); use the ± form or pass an explicit SMD column.

OUTPUT
  A reconciliation table (stdout) and, with --out, a JSON artifact:
    {covariate, imbalance_p / smd, in_adjustment_set, verdict}
  verdict UNADJUSTED_IMBALANCED is the Major candidate. Exit 1 (with --strict)
  when any UNADJUSTED_IMBALANCED row exists.

Matching the adjustment set to Table-1 covariate labels is fuzzy (a table row
"Smoking, pack-years" vs an adjustment token "smoking"), so the match is a
normalized-substring test in both directions; review the reconciliation table
rather than trusting the count blindly.

Stdlib-only (csv / json / re / argparse). Exit codes: 0 clean (or report-only),
1 unadjusted-imbalanced rows found (with --strict), 2 input/usage error.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

# --- column auto-detection -------------------------------------------------

NAME_HINTS = ("covariate", "variable", "characteristic", "feature", "name", "")
P_HINTS = ("p_value", "pvalue", "p-value", "p val", "p", "pr")
SMD_HINTS = ("smd", "std_diff", "standardized", "std. mean", "std mean")

P_THRESHOLD = 0.05
SMD_THRESHOLD = 0.10

# Header / summary rows that are not covariates (sample-size lines, group totals,
# trend-p rows). Matched on the whole normalized label, not a substring, so a real
# covariate like "Total cholesterol" is not swallowed by "total".
def _is_skip_row(cov: str) -> bool:
    c = _norm(cov)
    if c in ("", "total", "overall", "n", "no", "number"):
        return True
    if re.match(r"^n\s*[=:]", cov.strip().lower()):     # "N = ...", "n: ..."
        return True
    if "p for trend" in c or "p trend" in c or "for trend" in c:
        return True
    return False


def _norm(s: str) -> str:
    """Lowercase, drop punctuation/units, collapse whitespace for fuzzy match."""
    s = s.lower()
    s = re.sub(r"\(.*?\)", " ", s)            # drop "(mg/dL)", "(%)"
    s = re.sub(r"[^a-z0-9 ]+", " ", s)        # punctuation -> space
    s = re.sub(r"\s+", " ", s).strip()
    return s


# --- DB-code / prose synonym aliases ---------------------------------------
# A reviewer writes the adjustment set in prose ("systolic blood pressure") while
# a DB-exported Table 1 carries the column code ("he_sbp"); a normalized-substring
# match then fails and a covariate that *was* adjusted is false-flagged as
# imbalanced-and-unadjusted. Each row maps one canonical concept to the surface
# forms (DB code + prose synonyms) that denote it; two labels match when they
# resolve to a shared concept. This only ever *adds* matches (turns a false ✗ into
# ✓): a true unadjusted covariate shares no concept with any adjustment token, so
# no false ✓ is introduced. Extend as new DB dictionaries appear — one concept per
# row, lowercase, unit-free; multi-letter codes belong to the controlled
# `he_*` / `b_*` namespace so a bare token clash with a prose label is implausible.
ALIAS_GROUPS = {
    "sbp": ("he_sbp", "sbp", "systolic blood pressure", "systolic bp"),
    "dbp": ("he_dbp", "dbp", "diastolic blood pressure", "diastolic bp"),
    "uric_acid": ("b_uric", "uric acid", "serum uric acid", "urate"),
    "hdl": ("b_chol_hdl", "hdl", "hdl cholesterol", "high density lipoprotein"),
    "total_cholesterol": ("b_chol_t", "total cholesterol", "cholesterol total"),
    "triglycerides": ("b_tg", "tg", "triglyceride", "triglycerides"),
    "hba1c": ("b_hba1c", "hba1c", "glycated haemoglobin", "glycated hemoglobin",
              "glycohemoglobin"),
    "bmi": ("he_bmi", "bmi", "body mass index"),
    "waist": ("he_wc", "wc", "waist", "waist circumference"),
    "smoking": ("smk", "smk_packyrs", "smoking", "smoking status", "pack years",
                "pack-years", "smoker", "cigarette"),
    "fasting_glucose": ("he_glu", "b_glu", "fasting glucose", "fasting plasma glucose",
                        "fpg", "glucose"),
    "hemoglobin": ("he_hb", "b_hb", "hemoglobin", "haemoglobin"),
    "alcohol": ("alc", "alcohol", "alcohol intake", "drinking", "ethanol"),
    "egfr": ("egfr", "e_gfr", "estimated gfr", "estimated glomerular filtration rate"),
    "diabetes": ("dm", "diabetes", "diabetes mellitus"),
    "hypertension": ("htn", "hypertension", "high blood pressure"),
}

# concept -> set of normalized surface forms
_ALIAS_NORM = {c: {_norm(f) for f in forms if _norm(f)} for c, forms in ALIAS_GROUPS.items()}


def _concepts(label: str) -> set[str]:
    """Canonical concept keys a (normalized) covariate / adjustment label denotes.

    Single-token surface ("sbp", "wc"): whole-token match. Multi-word surface
    ("waist circumference"): contiguous phrase or all tokens present (so a Table-1
    row "Smoking, pack-years" -> 'smoking pack years' still resolves to smoking).
    """
    s = _norm(label)
    if not s:
        return set()
    tokens = set(s.split())
    out = set()
    for concept, surfaces in _ALIAS_NORM.items():
        for f in surfaces:
            ft = f.split()
            if len(ft) == 1:
                if ft[0] in tokens:
                    out.add(concept)
                    break
            elif f in s or all(t in tokens for t in ft):
                out.add(concept)
                break
    return out


def _pick_col(header: list[str], hints: tuple[str, ...], override: str | None) -> int | None:
    if override:
        for i, h in enumerate(header):
            if _norm(h) == _norm(override):
                return i
        sys.stderr.write(f"ERROR: column '{override}' not found in header {header}\n")
        return None
    norm = [_norm(h) for h in header]
    # exact-ish first
    for hint in hints:
        h = _norm(hint)
        for i, col in enumerate(norm):
            if col == h and h:
                return i
    # then substring — but only for hints >= 3 chars, so a 1-2 char hint like
    # "p" / "pr" does not match an unrelated column ("p" in "exposed").
    for hint in hints:
        h = _norm(hint)
        for i, col in enumerate(norm):
            if h and len(h) >= 3 and h in col:
                return i
    return None


def _parse_p(raw: str) -> float | None:
    """Parse a p-value cell: '0.001', '<0.001', 'p<0.01', '0.03*', 'NS'."""
    if raw is None:
        return None
    s = raw.strip().lower()
    if not s or s in ("ns", "na", "n/a", "-", "."):
        return 1.0 if s == "ns" else None
    m = re.search(r"<\s*(0?\.[0-9]+|[0-9]+\.?[0-9]*)", s)   # "<0.001", "p<.01"
    if m:
        try:                                   # report just under the stated bound
            return max(float(m.group(1)) - 1e-6, 0.0)
        except ValueError:
            return None
    m = re.search(r"0?\.[0-9]+|[0-9]+\.?[0-9]*", s)
    if m:
        try:
            return float(m.group(0))
        except ValueError:
            return None
    return None


def _parse_float(raw: str) -> float | None:
    if raw is None:
        return None
    m = re.search(r"-?[0-9]*\.?[0-9]+", raw.strip())
    return float(m.group(0)) if m else None


# --- adjustment set --------------------------------------------------------

def load_adjustment_set(path: str | None, inline: str | None) -> list[str]:
    if inline:
        return [t.strip() for t in inline.split(",") if t.strip()]
    if not path:
        return []
    p = Path(path)
    if not p.is_file():
        sys.stderr.write(f"ERROR: adjustment file not found: {path}\n")
        sys.exit(2)
    text = p.read_text(encoding="utf-8")
    # If the file is a Methods paragraph, grep the "adjusted for ..." clause.
    m = re.search(r"adjust(?:ed|ing)?\s+for\s+(.+?)(?:\.|;|\n\n|$)", text, re.I | re.S)
    if m:
        clause = m.group(1)
        parts = re.split(r",| and | as well as ", clause)
        return [p2.strip() for p2 in parts if p2.strip()]
    # Otherwise treat as one variable per line.
    return [ln.strip() for ln in text.splitlines() if ln.strip() and not ln.startswith("#")]


def in_adjustment_set(cov: str, adj_norm: list[str], adj_concepts: set[str] | None = None) -> bool:
    c = _norm(cov)
    if not c:
        return False
    # concept-level match across the DB-code / prose alias map (he_sbp ~ "systolic
    # blood pressure"); resolves the false ✗ when Table 1 carries DB column codes
    # and the adjustment set is written in prose.
    if adj_concepts and (_concepts(cov) & adj_concepts):
        return True
    for a in adj_norm:
        if not a:
            continue
        if a in c or c in a:
            return True
        # token overlap on the leading word (smoking ~ "smoking, pack-years")
        if c.split(" ")[0] == a.split(" ")[0] and len(c.split(" ")[0]) >= 3:
            return True
    return False


# --- A3: SMD computed from per-stratum mean ± SD ---------------------------
# The common wide Table 1 from /analyze-stats carries stratified "mean ± SD"
# (or "mean +/- SD") cells but no p / SMD column, so the gate could not run. When
# no p/SMD column is present, compute SMD from two group columns whose cells use
# the UNAMBIGUOUS mean±SD form (not "n (%)" / "mean (SD)", which collide), so a
# categorical "53 (52)" is never mistaken for a continuous mean(sd).
MEANSD_RE = re.compile(r"^\s*(-?\d[\d,]*\.?\d*)\s*(?:\+/-|±)\s*(\d[\d,]*\.?\d*)\s*$")


def _meansd(cell: str):
    if cell is None:
        return None
    m = MEANSD_RE.match(cell)
    if not m:
        return None
    try:
        return float(m.group(1).replace(",", "")), float(m.group(2).replace(",", ""))
    except ValueError:
        return None


def _smd_meansd(m1: float, s1: float, m2: float, s2: float):
    denom = ((s1 ** 2 + s2 ** 2) / 2.0) ** 0.5
    if denom <= 0:
        return None
    return (m1 - m2) / denom


def _detect_group_cols(header, body_rows, name_idx, override):
    """Return (i, j) column indices of the two exposure-stratum value columns to
    compute SMD from, or None. With --group-cols, resolve the two named columns;
    otherwise pick the first two non-name columns whose cells are mostly mean±SD."""
    if override:
        idxs = []
        for want in override:
            found = next((k for k, h in enumerate(header) if _norm(h) == _norm(want)), None)
            if found is None:
                sys.stderr.write(f"ERROR: --group-cols column '{want}' not found in {header}\n")
                sys.exit(2)
            idxs.append(found)
        return (idxs[0], idxs[1]) if len(idxs) >= 2 else None
    cand = []
    for k in range(len(header)):
        if k == name_idx:
            continue
        hits = sum(1 for r in body_rows if k < len(r) and _meansd(r[k]) is not None)
        if hits >= 2:
            cand.append(k)
    return (cand[0], cand[1]) if len(cand) >= 2 else None


def is_exposure_defining(cov: str, defining_norm: list[str], defining_concepts: set[str]) -> bool:
    """A4: a covariate that is a component of the exposure's diagnostic criteria
    (e.g. BMI/glycaemia/lipids for a metabolic-syndrome / MASLD exposure). Same
    fuzzy match as in_adjustment_set."""
    if not defining_norm and not defining_concepts:
        return False
    return in_adjustment_set(cov, defining_norm, defining_concepts)


# --- core ------------------------------------------------------------------

def analyze(table1: str, adj: list[str], name_col, p_col, smd_col,
            defining: list[str] | None = None, group_cols: list[str] | None = None) -> dict:
    p = Path(table1)
    if not p.is_file():
        sys.stderr.write(f"ERROR: table1 not found: {table1}\n")
        sys.exit(2)
    with p.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        rows = [r for r in reader if any(c.strip() for c in r)]
    if len(rows) < 2:
        sys.stderr.write("ERROR: table1 has no data rows\n")
        sys.exit(2)
    header = rows[0]
    ni = _pick_col(header, NAME_HINTS, name_col)
    pi = _pick_col(header, P_HINTS, p_col)
    si = _pick_col(header, SMD_HINTS, smd_col)
    if ni is None:
        ni = 0
    gi = None
    if pi is None and si is None:
        # A3: no p / SMD column — fall back to computing SMD from two mean±SD cols.
        gi = _detect_group_cols(header, rows[1:], ni, group_cols)
        if gi is None:
            sys.stderr.write(
                "ERROR: no p-value or SMD column found, and no two mean±SD group "
                "columns to compute SMD from; pass --p-col/--smd-col or --group-cols.\n")
            sys.exit(2)

    adj_norm = [_norm(a) for a in adj]
    adj_concepts = set().union(*(_concepts(a) for a in adj)) if adj else set()
    defining = defining or []
    def_norm = [_norm(d) for d in defining]
    def_concepts = set().union(*(_concepts(d) for d in defining)) if defining else set()
    smd_source = "reported" if (pi is not None or si is not None) else "computed_from_mean_sd"
    findings = []
    for r in rows[1:]:
        if ni >= len(r):
            continue
        cov = r[ni].strip()
        if _is_skip_row(cov):
            continue
        pval = _parse_p(r[pi]) if (pi is not None and pi < len(r)) else None
        smd = _parse_float(r[si]) if (si is not None and si < len(r)) else None
        if smd is None and gi is not None:                       # A3: compute SMD
            g1 = _meansd(r[gi[0]]) if gi[0] < len(r) else None
            g2 = _meansd(r[gi[1]]) if gi[1] < len(r) else None
            if g1 and g2:
                smd = _smd_meansd(g1[0], g1[1], g2[0], g2[1])
        imbalanced = (pval is not None and pval < P_THRESHOLD) or \
                     (smd is not None and abs(smd) >= SMD_THRESHOLD)
        if not imbalanced:
            continue
        # A4: a component of the exposure's own diagnostic criteria is over-
        # adjustment, not residual confounding — exempt it from the Major flag.
        if is_exposure_defining(cov, def_norm, def_concepts):
            verdict = "EXPOSURE_DEFINING_EXEMPT"
            adjusted = in_adjustment_set(cov, adj_norm, adj_concepts)
        else:
            adjusted = in_adjustment_set(cov, adj_norm, adj_concepts)
            verdict = "ADJUSTED" if adjusted else "UNADJUSTED_IMBALANCED"
        findings.append({
            "covariate": cov,
            "imbalance_p": pval,
            "smd": round(smd, 4) if smd is not None else None,
            "in_adjustment_set": adjusted,
            "verdict": verdict,
        })

    unadjusted = [f for f in findings if f["verdict"] == "UNADJUSTED_IMBALANCED"]
    exempt = [f for f in findings if f["verdict"] == "EXPOSURE_DEFINING_EXEMPT"]
    return {
        "table1": str(p),
        "adjustment_set": adj,
        "exposure_defining": defining,
        "thresholds": {"p": P_THRESHOLD, "smd": SMD_THRESHOLD},
        "smd_source": smd_source,
        "n_imbalanced": len(findings),
        "n_unadjusted_imbalanced": len(unadjusted),
        "n_exposure_defining_exempt": len(exempt),
        "findings": findings,
        "verdict": "MAJOR_CANDIDATE" if unadjusted else "OK",
        "suggested_fix": (
            "Report an extended-adjustment sensitivity model adding the unadjusted "
            "imbalanced covariates that are NON-defining prognostic factors (not the "
            "exposure's own diagnostic criteria); keep the original model primary "
            "only if the extended model agrees."
        ) if unadjusted else None,
    }


def render_table(result: dict) -> str:
    lines = [
        "| Covariate | Imbalance p | SMD | In adjustment set? | Verdict |",
        "|---|---|---|---|---|",
    ]
    marks = {
        "UNADJUSTED_IMBALANCED": "✗ Major",
        "ADJUSTED": "✓",
        "EXPOSURE_DEFINING_EXEMPT": "⊘ exposure-defining (exempt; adjusting = over-adjustment)",
    }
    for f in result["findings"]:
        p = "—" if f["imbalance_p"] is None else f"{f['imbalance_p']:.4g}"
        s = "—" if f["smd"] is None else f"{f['smd']:.3g}"
        mark = marks.get(f["verdict"], f["verdict"])
        lines.append(
            f"| {f['covariate']} | {p} | {s} | "
            f"{'yes' if f['in_adjustment_set'] else 'NO'} | {mark} |"
        )
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Observational confounding-completeness gate (O1).")
    ap.add_argument("--table1", required=True, help="exposure-stratified Table 1 CSV")
    ap.add_argument("--adjusted", help="adjustment-set file (var-per-line or Methods paragraph)")
    ap.add_argument("--adjusted-list", help="comma-separated adjustment variables (inline)")
    ap.add_argument("--name-col", help="override covariate-name column header")
    ap.add_argument("--p-col", help="override p-value column header")
    ap.add_argument("--smd-col", help="override SMD column header")
    ap.add_argument("--group-cols",
                    help="two stratum value-column headers (comma-separated) to compute SMD from "
                         "mean±SD cells when no p/SMD column exists (e.g. 'exposed,unexposed')")
    ap.add_argument("--exposure-defining",
                    help="file of exposure-defining covariates (components of the exposure's "
                         "diagnostic criteria); these are exempt from the residual-confounding flag")
    ap.add_argument("--exposure-defining-list",
                    help="comma-separated exposure-defining covariates (inline)")
    ap.add_argument("--out", help="write JSON artifact to this path")
    ap.add_argument("--strict", action="store_true", help="exit 1 if unadjusted-imbalanced rows exist")
    args = ap.parse_args()

    adj = load_adjustment_set(args.adjusted, args.adjusted_list)
    if not adj:
        sys.stderr.write("WARN: empty adjustment set — every imbalanced covariate will flag.\n")
    defining = load_adjustment_set(args.exposure_defining, args.exposure_defining_list)
    group_cols = [c.strip() for c in args.group_cols.split(",")] if args.group_cols else None

    result = analyze(args.table1, adj, args.name_col, args.p_col, args.smd_col,
                     defining, group_cols)

    print("=" * 41)
    print(" Confounding Completeness (Phase 2.5e / O1)")
    print("=" * 41)
    print(f"adjustment set: {', '.join(adj) if adj else '(none)'}")
    if defining:
        print(f"exposure-defining (exempt): {', '.join(defining)}")
    if result["smd_source"] == "computed_from_mean_sd":
        print("SMD source: computed from mean±SD group columns (no p/SMD column present)")
    print(render_table(result))
    print()
    if result["n_exposure_defining_exempt"]:
        print(f"Note: {result['n_exposure_defining_exempt']} imbalanced covariate(s) exempt as "
              f"exposure-defining (adjusting for them would be over-adjustment — see probe O7).")
    if result["n_unadjusted_imbalanced"]:
        print(f"MAJOR candidate: {result['n_unadjusted_imbalanced']} imbalanced covariate(s) "
              f"absent from the adjustment set.")
        print(f"Fix: {result['suggested_fix']}")
    else:
        print("OK: no measured-but-unadjusted imbalanced covariate.")

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"\nwrote {args.out}")

    return 1 if (args.strict and result["n_unadjusted_imbalanced"]) else 0


if __name__ == "__main__":
    sys.exit(main())
