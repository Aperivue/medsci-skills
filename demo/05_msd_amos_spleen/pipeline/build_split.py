#!/usr/bin/env python3
"""Build the seed-locked internal split for Demo 5 (MSD Task09 Spleen).

Design, decided from the Stage-0 profile and fixed before anything trains:

* The shipped `imagesTs` directory carries no labels (the gate's TEST_SET_UNLABELLED),
  so the internal held-out set is carved from the 41 labelled cases. It cannot come
  from anywhere else.
* One case = one patient in this dataset; there is no second study per subject, so the
  unit and the patient are the same row. Stated rather than assumed silently — if that
  were wrong, the split-leakage gate is what would catch it.
* The held-out set is stratified by **spleen-volume tertile**. The profile showed
  56-502 mL, i.e. the cohort contains splenomegaly; an unstratified draw of 9 from 41
  can easily land entirely in the normal range and leave the held-out set unable to say
  anything about enlarged spleens. Stratification uses the label volume to *balance* the
  split, never to inform training — and it is declared here because a split built with
  any label-derived quantity should be visible, not buried.
* The remaining cases go to nnU-Net's own 5-fold cross-validation, which is where the
  train/validation division actually happens. This script does not pre-empt that.

Output: splits/split_assignment.csv (patient_id, unit_id, split, volume_ml, volume_tertile)
        splits/split_seed.txt
"""
from __future__ import annotations

import csv
import json
import random
from pathlib import Path

SEED = 42
N_HOLDOUT = 9  # ~22% of 41; 3 per volume tertile
PROFILE = Path("eda/msd_spleen_profile.json")
OUT_DIR = Path("splits")


def main() -> None:
    profile = json.loads(PROFILE.read_text(encoding="utf-8"))
    train_cases = [c for c in profile["cases"]
                   if c["split"] == "train" and c.get("target_volume_ml") is not None]
    if len(train_cases) != 41:
        raise SystemExit(f"expected 41 labelled cases, profile has {len(train_cases)}")

    ranked = sorted(train_cases, key=lambda c: c["target_volume_ml"])
    n = len(ranked)
    tertile_of = {}
    for i, c in enumerate(ranked):
        tertile_of[c["case"]] = "low" if i < n / 3 else ("mid" if i < 2 * n / 3 else "high")

    rng = random.Random(SEED)
    holdout: list[str] = []
    per_tertile = N_HOLDOUT // 3
    for t in ("low", "mid", "high"):
        pool = sorted(c["case"] for c in ranked if tertile_of[c["case"]] == t)
        holdout += rng.sample(pool, per_tertile)
    holdout_set = set(holdout)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    for c in sorted(train_cases, key=lambda c: c["case"]):
        rows.append({
            "patient_id": c["case"],           # one case = one patient in this dataset
            "unit_id": c["case"],
            "split": "test" if c["case"] in holdout_set else "train",
            "volume_ml": round(c["target_volume_ml"], 1),
            "volume_tertile": tertile_of[c["case"]],
        })

    with (OUT_DIR / "split_assignment.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    (OUT_DIR / "split_seed.txt").write_text(f"{SEED}\n", encoding="utf-8")

    n_test = sum(r["split"] == "test" for r in rows)
    print(f"wrote {OUT_DIR/'split_assignment.csv'}  ({len(rows)} cases: "
          f"{len(rows) - n_test} train / {n_test} held-out, seed {SEED})")
    for t in ("low", "mid", "high"):
        sel = [r for r in rows if r["volume_tertile"] == t]
        held = [r for r in sel if r["split"] == "test"]
        vols = [r["volume_ml"] for r in sel]
        print(f"  {t:<4} n={len(sel):<3} held-out={len(held)}  "
              f"volume {min(vols):.0f}-{max(vols):.0f} mL")


if __name__ == "__main__":
    main()
