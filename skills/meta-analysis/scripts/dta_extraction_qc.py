#!/usr/bin/env python3
"""
DTA Extraction QC — cross-check forest plot 2x2 cells against source paper sens/spec.

Motivation: recent SR-MA peer-review cycles found extracted (TP, FN, TN, FP)
cells with sensitivity/specificity values swapped versus the source paper. In
single-study k=1 subgroups this can invert reported p-values. This script
validates extracted cells against source-reported sens/spec with a tolerance and
FLAGs mismatches for manual review. It does NOT auto-correct.

Usage:
    python3 dta_extraction_qc.py --input extraction.csv --tolerance 0.02 --out qc_report.tsv

Input CSV schema (required columns):
    study_id          - e.g., "StudyA_2021_1"
    source_pmid       - PubMed ID (string)
    source_sens       - decimal 0-1 (e.g., 0.978)
    source_spec       - decimal 0-1 (e.g., 0.554)
    extracted_tp      - int (TP cell)
    extracted_fn      - int (FN cell)
    extracted_tn      - int (TN cell)
    extracted_fp      - int (FP cell)
    source_cohort     - e.g., "external_test_set" (which cohort the source values come from)
    source_page_ref   - e.g., "Table 3 page 7" (audit trail)

Output:
    Tab-separated table with one row per study, columns:
    study_id | extracted_sens | extracted_spec | source_sens | source_spec
            | sens_diff | spec_diff | status | swap_suspected | message
"""
import argparse
import csv
import sys
from pathlib import Path


def compute_sens_spec(tp: int, fn: int, tn: int, fp: int) -> tuple[float, float]:
    """Return (sensitivity, specificity)."""
    sens = tp / (tp + fn) if (tp + fn) > 0 else float("nan")
    spec = tn / (tn + fp) if (tn + fp) > 0 else float("nan")
    return sens, spec


def check_row(row: dict, tol: float) -> dict:
    """Return augmented row with status/diff fields."""
    try:
        tp = int(row["extracted_tp"])
        fn = int(row["extracted_fn"])
        tn = int(row["extracted_tn"])
        fp = int(row["extracted_fp"])
        source_sens = float(row["source_sens"])
        source_spec = float(row["source_spec"])
    except (KeyError, ValueError) as e:
        return {**row, "status": "PARSE_ERROR", "message": str(e)}

    ext_sens, ext_spec = compute_sens_spec(tp, fn, tn, fp)
    sens_diff = abs(ext_sens - source_sens)
    spec_diff = abs(ext_spec - source_spec)

    # Swap detection: extracted_sens ≈ source_spec AND extracted_spec ≈ source_sens
    swap_sens_match = abs(ext_sens - source_spec) <= tol
    swap_spec_match = abs(ext_spec - source_sens) <= tol
    swap_suspected = swap_sens_match and swap_spec_match

    if sens_diff <= tol and spec_diff <= tol:
        status = "OK"
        message = "Match within tolerance."
    elif swap_suspected:
        status = "FLAG_SWAP"
        message = (
            f"Possible sens/spec SWAP. "
            f"Extracted (sens={ext_sens:.3f}, spec={ext_spec:.3f}) matches "
            f"source swapped (source_sens={source_sens:.3f}, source_spec={source_spec:.3f})."
        )
    else:
        status = "FLAG_MISMATCH"
        message = (
            f"Discrepancy beyond tolerance ({tol:.3f}). "
            f"Check source_page_ref={row.get('source_page_ref','?')}."
        )

    return {
        **row,
        "extracted_sens": f"{ext_sens:.4f}",
        "extracted_spec": f"{ext_spec:.4f}",
        "sens_diff": f"{sens_diff:.4f}",
        "spec_diff": f"{spec_diff:.4f}",
        "swap_suspected": "YES" if swap_suspected else "NO",
        "status": status,
        "message": message,
    }


def main() -> int:
    p = argparse.ArgumentParser(description="DTA extraction sens/spec QC")
    p.add_argument("--input", required=True, type=Path, help="Input CSV file")
    p.add_argument("--tolerance", type=float, default=0.02,
                   help="Absolute tolerance for sens/spec match (default 0.02 = 2 percentage points)")
    p.add_argument("--out", required=True, type=Path, help="Output TSV report")
    args = p.parse_args()

    if not args.input.exists():
        print(f"ERROR: input file not found: {args.input}", file=sys.stderr)
        return 1

    with args.input.open(newline="", encoding="utf-8") as fin:
        reader = csv.DictReader(fin)
        rows = [check_row(r, args.tolerance) for r in reader]

    fieldnames = [
        "study_id", "source_pmid", "source_cohort", "source_page_ref",
        "extracted_tp", "extracted_fn", "extracted_tn", "extracted_fp",
        "extracted_sens", "extracted_spec", "source_sens", "source_spec",
        "sens_diff", "spec_diff", "swap_suspected", "status", "message",
    ]
    with args.out.open("w", newline="", encoding="utf-8") as fout:
        writer = csv.DictWriter(fout, fieldnames=fieldnames, delimiter="\t",
                                extrasaction="ignore")
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    # Summary stats
    n = len(rows)
    n_ok = sum(1 for r in rows if r.get("status") == "OK")
    n_swap = sum(1 for r in rows if r.get("status") == "FLAG_SWAP")
    n_mismatch = sum(1 for r in rows if r.get("status") == "FLAG_MISMATCH")
    n_err = sum(1 for r in rows if r.get("status") == "PARSE_ERROR")

    print(f"DTA QC: {n} studies | OK={n_ok} | SWAP={n_swap} | MISMATCH={n_mismatch} | PARSE_ERROR={n_err}")
    print(f"Report: {args.out}")

    return 1 if (n_swap + n_mismatch + n_err) > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
