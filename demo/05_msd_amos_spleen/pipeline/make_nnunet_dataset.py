#!/usr/bin/env python3
"""Build the nnU-Net v2 raw dataset from MSD Task09 — training cases only.

The 9 held-out cases are deliberately absent from this directory. nnU-Net fits its
dataset fingerprint — the resampling target AND the CT intensity statistics — on
whatever sits in imagesTr, so the held-out cases being here at all would leak them
into preprocessing. That is the PREPROCESS_BEFORE_SPLIT finding from Stage 2, and the
only way to avoid it is to not copy the files.

MSD layout            -> nnU-Net v2 layout
  imagesTr/spleen_2.nii.gz  ->  imagesTr/spleen_2_0000.nii.gz   (channel suffix)
  labelsTr/spleen_2.nii.gz  ->  labelsTr/spleen_2.nii.gz
"""
from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path

SRC = Path("data/msd_spleen/Task09_Spleen")
DST = Path("work/nnUNet_raw/Dataset009_Spleen")
SPLITS = Path("splits/split_assignment.csv")


def main() -> None:
    rows = list(csv.DictReader(SPLITS.open(encoding="utf-8")))
    train = sorted(r["unit_id"] for r in rows if r["split"] == "train")
    held = sorted(r["unit_id"] for r in rows if r["split"] == "test")
    if len(train) != 32 or len(held) != 9:
        raise SystemExit(f"expected 32/9, got {len(train)}/{len(held)}")

    (DST / "imagesTr").mkdir(parents=True, exist_ok=True)
    (DST / "labelsTr").mkdir(parents=True, exist_ok=True)

    for case in train:
        shutil.copy2(SRC / "imagesTr" / f"{case}.nii.gz", DST / "imagesTr" / f"{case}_0000.nii.gz")
        shutil.copy2(SRC / "labelsTr" / f"{case}.nii.gz", DST / "labelsTr" / f"{case}.nii.gz")

    (DST / "dataset.json").write_text(json.dumps({
        "channel_names": {"0": "CT"},
        "labels": {"background": 0, "spleen": 1},
        "numTraining": len(train),
        "file_ending": ".nii.gz",
        "licence": "CC-BY-SA 4.0",
        "reference": "Memorial Sloan Kettering Cancer Center (MSD Task09_Spleen)",
        "description": ("Demo 5 internal training arm. The 9 seed-42 held-out cases are "
                        "excluded from this directory so the nnU-Net fingerprint is fit on "
                        "training data only."),
    }, indent=1), encoding="utf-8")

    n_img = len(list((DST / "imagesTr").glob("*.nii.gz")))
    n_lab = len(list((DST / "labelsTr").glob("*.nii.gz")))
    print(f"wrote {DST}: {n_img} images / {n_lab} labels")
    print(f"held out (absent by design): {', '.join(held)}")
    leaked = [c for c in held if (DST / "imagesTr" / f"{c}_0000.nii.gz").exists()]
    print("held-out leakage into nnUNet_raw:", leaked or "none")
    if leaked:
        raise SystemExit("held-out case copied into the fingerprint directory")


if __name__ == "__main__":
    main()
