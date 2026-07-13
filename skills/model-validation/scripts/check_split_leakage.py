#!/usr/bin/env python3
"""Train/validation/test split-leakage gate for a medical-imaging model (model-validation).

The single most common — and most metric-inflating — defect in an engineer-built
imaging model is a data split that is NOT disjoint at the patient level: the same
patient contributes images to both the training and the test partition, so the model
memorises patient-specific anatomy and every reported metric is optimistic
(Kapoor & Narayanan, Patterns 2023; Varoquaux & Cheplygina, npj Digit Med 2022;
CLAIM 2024 data-partition items). Unlike a prose hygiene linter, this is a fully
*decidable* data check: it reads the emitted split-assignment table and proves, by
set arithmetic on the patient/subject IDs, whether any ID crosses partitions.

It also checks that the split is REPRODUCIBLE — a recorded random seed — because a
split with no seed cannot be regenerated and its disjointness cannot be re-verified.

CHECKS (verdicts):
  1. PATIENT_OVERLAP  (Major)  one or more IDs appear in >= 2 distinct partitions
                               (after collapsing train/training, val/validation,
                               test/testing/holdout synonyms). The decisive leak.
  2. MISSING_SEED     (Major)  no split seed found via --seed, --seed-file, an
                               auto-detected split_seed.txt next to the CSV, or a
                               seed / random_state column. Pass --no-require-seed to
                               downgrade to a flag when the seed is genuinely external.
  3. SINGLE_PARTITION (Minor)  fewer than two distinct partitions — the file is not a
                               train/val/test split (informational, not a leak).

An ID appearing multiple times WITHIN one partition (several images per patient) is
NOT a leak and does not fire; only an ID spanning >= 2 partitions does.

INPUTS
  --splits   split-assignment CSV (required). Columns auto-detected:
               id    : patient_id / subject_id / case_id / id / pid / mrn / studyid
               split : split / partition / set / subset / fold / phase / assignment
             Override with --id-col / --split-col.
  --seed     the split's random seed (int/str), to record reproducibility.
  --seed-file path to a file holding the seed (default: auto-detect split_seed.txt
             alongside --splits).

OUTPUT
  A reconciliation table (stdout) and, with --out, a JSON artifact:
    {splits, id_col, split_col, n_rows, n_subjects, partitions{name:count},
     seed, claims[{verdict, severity, detail, where}], summary}
  PATIENT_OVERLAP / MISSING_SEED are Major candidates.

Stdlib-only (csv / json / re / argparse / pathlib). Exit codes: 0 clean (or
report-only), 1 Major claim(s) found (with --strict), 2 input/usage error.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

ID_HINTS = ("patient_id", "subject_id", "case_id", "patientid", "subjectid", "caseid",
            "patient", "subject", "id", "pid", "eid", "uid", "mrn", "studyid", "study_id")
SPLIT_HINTS = ("split", "partition", "set", "subset", "fold", "phase", "assignment",
               "split_assignment", "data_split", "group_split")

# Synonym collapse so "train"/"training" do not register as two partitions (a
# conservative choice: real leakage is train-vs-test, not a labelling variant).
SPLIT_CANON = {
    "train": "train", "training": "train", "trn": "train",
    "val": "val", "valid": "val", "validation": "val", "dev": "val", "development": "val",
    "test": "test", "testing": "test", "holdout": "test", "hold-out": "test",
    "hold_out": "test", "eval": "test", "evaluation": "test",
}


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (s or "").strip().lower())


def _canon_split(v: str) -> str:
    n = _norm(v)
    return SPLIT_CANON.get(n, n)


def _pick(header: list[str], hints: tuple[str, ...]):
    norm = [_norm(h) for h in header]
    for hint in hints:                       # exact match first
        h = _norm(hint)
        for i, col in enumerate(norm):
            if col == h and h:
                return header[i]
    for hint in hints:                       # then substring
        h = _norm(hint)
        for i, col in enumerate(norm):
            if h and h in col:
                return header[i]
    return None


def _find_seed(splits_path: Path, rows: list[dict], header: list[str],
               seed: str | None, seed_file: str | None) -> str | None:
    if seed is not None and str(seed).strip() != "":
        return str(seed).strip()
    # explicit or auto-detected seed file
    candidates = []
    if seed_file:
        candidates.append(Path(seed_file))
    candidates.append(splits_path.with_name("split_seed.txt"))
    candidates.append(splits_path.parent / "split_seed.txt")
    for c in candidates:
        if c.is_file():
            txt = c.read_text(encoding="utf-8").strip()
            m = re.search(r"-?\d+", txt)
            if m:
                return m.group(0)
    # a seed / random_state column
    col = _pick(header, ("seed", "random_state", "random_seed", "rng_seed"))
    if col:
        for r in rows:
            v = (r.get(col) or "").strip()
            if v:
                return v
    return None


def analyze(splits: str, id_col: str | None, split_col: str | None,
            seed: str | None, seed_file: str | None, require_seed: bool) -> dict:
    p = Path(splits)
    if not p.is_file():
        sys.stderr.write(f"ERROR: --splits not found: {splits}\n")
        sys.exit(2)
    with p.open(encoding="utf-8-sig", newline="") as f:
        rows = [r for r in csv.DictReader(f)]
    if not rows:
        sys.stderr.write(f"ERROR: --splits has no rows: {splits}\n")
        sys.exit(2)
    header = list(rows[0].keys())

    if id_col and id_col not in header:
        sys.stderr.write(f"ERROR: --id-col '{id_col}' not in {header}\n")
        sys.exit(2)
    if split_col and split_col not in header:
        sys.stderr.write(f"ERROR: --split-col '{split_col}' not in {header}\n")
        sys.exit(2)
    idc = id_col or _pick(header, ID_HINTS)
    spc = split_col or _pick(header, SPLIT_HINTS)
    if idc is None:
        sys.stderr.write(f"ERROR: no ID column found (looked for {ID_HINTS[:6]}…); pass --id-col\n")
        sys.exit(2)
    if spc is None:
        sys.stderr.write(f"ERROR: no split column found (looked for {SPLIT_HINTS[:6]}…); pass --split-col\n")
        sys.exit(2)

    # ID -> set of canonical partitions it appears in.
    id_to_splits: dict[str, set[str]] = {}
    part_counts: dict[str, int] = {}
    for r in rows:
        sid = (r.get(idc) or "").strip()
        part = _canon_split(r.get(spc) or "")
        if not sid or not part:
            continue
        id_to_splits.setdefault(sid, set()).add(part)
        part_counts[part] = part_counts.get(part, 0) + 1

    n_subjects = len(id_to_splits)
    overlapping = sorted(sid for sid, parts in id_to_splits.items() if len(parts) > 1)
    seed_val = _find_seed(p, rows, header, seed, seed_file)

    claims: list[dict] = []
    if overlapping:
        shown = ", ".join(overlapping[:8]) + ("…" if len(overlapping) > 8 else "")
        # a representative offender with its partitions
        ex = overlapping[0]
        ex_parts = "/".join(sorted(id_to_splits[ex]))
        claims.append({
            "verdict": "PATIENT_OVERLAP",
            "severity": "Major",
            "detail": (f"{len(overlapping)} of {n_subjects} subjects appear in >= 2 partitions "
                       f"(e.g. '{ex}' in {ex_parts}); the same patient in train and test "
                       f"inflates every metric. Offenders: {shown}"),
            "where": f"--splits id column '{idc}', split column '{spc}'",
        })
    if seed_val is None and require_seed:
        claims.append({
            "verdict": "MISSING_SEED",
            "severity": "Major",
            "detail": ("no split seed found (--seed / --seed-file / split_seed.txt / a seed "
                       "column); the partition cannot be regenerated or re-verified"),
            "where": f"--splits {p.name}",
        })
    if len(part_counts) < 2:
        claims.append({
            "verdict": "SINGLE_PARTITION",
            "severity": "Minor",
            "detail": (f"only {len(part_counts)} distinct partition(s) "
                       f"({', '.join(sorted(part_counts)) or 'none'}); this is not a "
                       f"train/val/test split"),
            "where": f"--splits split column '{spc}'",
        })

    n_major = sum(1 for c in claims if c["severity"] == "Major")
    return {
        "splits": str(p),
        "id_col": idc,
        "split_col": spc,
        "n_rows": len(rows),
        "n_subjects": n_subjects,
        "partitions": dict(sorted(part_counts.items())),
        "seed": seed_val,
        "claims": claims,
        "summary": {
            "n_claims": len(claims),
            "n_major": n_major,
            "n_minor": len(claims) - n_major,
            "n_overlapping_subjects": len(overlapping),
            "verdict": "MAJOR_CANDIDATE" if n_major else "OK",
        },
    }


def render(result: dict) -> str:
    lines = ["| Check | Severity | Detail |", "|---|---|---|"]
    for c in result["claims"]:
        lines.append(f"| {c['verdict']} | {c['severity']} | {c['detail']} |")
    if len(lines) == 2:
        lines.append("| (none) | — | patient-disjoint split with a recorded seed |")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Train/val/test split-leakage gate (model-validation).")
    ap.add_argument("--splits", required=True, help="split-assignment CSV (id column + split column)")
    ap.add_argument("--id-col", help="patient/subject ID column (auto-detected if omitted)")
    ap.add_argument("--split-col", help="split/partition column (auto-detected if omitted)")
    ap.add_argument("--seed", help="the split's random seed, to record reproducibility")
    ap.add_argument("--seed-file", help="file holding the seed (default: auto-detect split_seed.txt)")
    ap.add_argument("--no-require-seed", dest="require_seed", action="store_false",
                    help="downgrade a missing seed from Major to no-finding")
    ap.add_argument("--out", help="write JSON artifact to this path")
    ap.add_argument("--strict", action="store_true", help="exit 1 if any Major claim exists")
    ap.add_argument("--quiet", action="store_true", help="suppress stdout table")
    ap.set_defaults(require_seed=True)
    args = ap.parse_args()

    result = analyze(args.splits, args.id_col, args.split_col,
                     args.seed, args.seed_file, args.require_seed)

    if not args.quiet:
        print("=" * 41)
        print(" Split-Leakage Gate (model-validation)")
        print("=" * 41)
        print(f"  rows={result['n_rows']}  subjects={result['n_subjects']}  "
              f"partitions={result['partitions']}  seed={result['seed']}")
        print(render(result))
        print()
        s = result["summary"]
        if s["n_major"]:
            print(f"MAJOR candidate: {s['n_major']} split-integrity issue(s).")
        else:
            print("OK: patient-disjoint split with a recorded seed.")

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps({"detector": "check_split_leakage", **result}, indent=2), encoding="utf-8")
        if not args.quiet:
            print(f"\nwrote {args.out}")

    return 1 if (args.strict and result["summary"]["n_major"]) else 0


if __name__ == "__main__":
    sys.exit(main())
