#!/usr/bin/env python3
"""Execute the nested-CV skeleton shipped in references/radiomics_ml_guide.md on synthetic
lesion-level data and check that it splits by patient.

The data have 60 patients x 4 lesions, 200 features that carry a per-patient fingerprint,
and an outcome drawn per patient independently of every feature, so the true AUROC is 0.5.
Row-wise folds put one patient's lesions on both sides of a split and the skeleton then
reports AUROC near 0.99; patient-grouped folds report about 0.5. The check fails if any
patient's rows land in more than one outer fold, or if the nested-CV AUROC on this null
data is implausibly high.

Needs numpy / pandas / scikit-learn (installed in CI). Without scikit-learn it prints SKIP
and exits 0 locally, but exits 2 when the CI environment variable is set, so the check
cannot pass silently in CI. Exit codes: 0 pass, 1 fail, 2 environment error.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
GUIDE = HERE.parent / "references" / "radiomics_ml_guide.md"
MARKER = "Nested-CV skeleton"
AUC_CEILING = 0.75  # null data: grouped folds land near 0.5, row-wise folds near 0.99


def extract_skeleton(guide: Path) -> str:
    blocks = re.findall(r"```python\n(.*?)```", guide.read_text(encoding="utf-8"), re.DOTALL)
    hits = [b for b in blocks if MARKER in b]
    if len(hits) != 1:
        raise SystemExit(f"ENV-ERR: expected one python block marked '{MARKER}' in {guide}, "
                         f"found {len(hits)}")
    return hits[0]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--guide", default=str(GUIDE), help="guide markdown holding the skeleton")
    args = ap.parse_args()

    try:
        import numpy as np
        import pandas as pd
        import sklearn  # noqa: F401
    except ImportError as e:
        if os.environ.get("CI"):
            print(f"ENV-ERR: {e} (required in CI)", file=sys.stderr)
            return 2
        print(f"  SKIP  nested-CV skeleton check ({e})")
        return 0

    code = extract_skeleton(Path(args.guide))

    rng = np.random.default_rng(7)
    n_pat, per, p = 60, 4, 200
    fingerprint = rng.normal(size=(n_pat, p))
    y_pat = rng.permutation(np.r_[np.ones(n_pat // 2), np.zeros(n_pat // 2)]).astype(int)
    X = np.repeat(fingerprint, per, axis=0) + 0.3 * rng.normal(size=(n_pat * per, p))
    y = np.repeat(y_pat, per)
    patient_id = np.repeat(np.array([f"P{i:03d}" for i in range(n_pat)]), per)

    ns = {"X": X, "y": y, "patient_id": patient_id}
    cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmp:
        os.chdir(tmp)
        try:
            exec(compile(code, "radiomics_ml_guide.md:nested-CV skeleton", "exec"), ns)
            folds = pd.read_csv("cv_folds.csv")
        finally:
            os.chdir(cwd)

    fail = 0
    per_patient = folds.groupby("patient_id")["split"].nunique()
    straddle = int((per_patient > 1).sum())
    if straddle:
        print(f"  FAIL  {straddle}/{n_pat} patients have rows in more than one outer fold "
              f"(the CV unit must be the patient)")
        fail += 1
    else:
        print(f"  PASS  every patient sits in exactly one outer fold ({n_pat} patients)")

    oof = np.asarray(ns.get("oof"))
    if oof.shape != y.shape or np.isnan(oof).any():
        print("  FAIL  out-of-fold predictions missing for some rows")
        fail += 1

    mean_auc = float(np.mean(ns["auc"]))
    if mean_auc >= AUC_CEILING:
        print(f"  FAIL  nested-CV AUROC {mean_auc:.2f} on features unrelated to the outcome "
              f"(ceiling {AUC_CEILING}); patient identity is leaking across folds")
        fail += 1
    else:
        print(f"  PASS  nested-CV AUROC {mean_auc:.2f} on null data (< {AUC_CEILING})")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
