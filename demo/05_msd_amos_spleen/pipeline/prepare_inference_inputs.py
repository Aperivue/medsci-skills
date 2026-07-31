#!/usr/bin/env python3
"""Build the three inference arms as nnU-Net-style input directories (symlinks, no copies).

nnU-Net expects one file per case named `<case>_0000.nii.gz` (the `_0000` is the channel index),
and it writes predictions back as `<case>.nii.gz`. Ground truth is left where it is; the
evaluator matches on the prediction name.

Arms, per EVALUATION_PLAN.md:
  rung1_msd_heldout  -- the 9 MSD cases marked `test` in splits/split_assignment.csv
  rung2_amos_ct      -- 300 labelled AMOS CT
  rung3_amos_mri     --  60 labelled AMOS MRI

The held-out 9 are read from the committed split file, never re-derived: re-deriving a split at
inference time is how a held-out set quietly stops being held out.
"""
from __future__ import annotations

import csv
import os
import sys
from pathlib import Path

# Project root defaults to this demo folder (pipeline/..) so the script runs from a clone; override
# with DEMO5_ROOT when the datasets sit elsewhere, which at ~25 GB they usually do.
ROOT = Path(os.environ.get("DEMO5_ROOT", Path(__file__).resolve().parent.parent))
MSD = ROOT / "data/msd_spleen/Task09_Spleen"
VIEWS = ROOT / "data/amos22/views"
INFER = ROOT / "inference"


def link(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.is_symlink() or dst.exists():
        dst.unlink()
    # relative symlink: an absolute target (src.resolve()) does not resolve inside the
    # prediction container, which bind-mounts this tree at /workspace (nnU-Net then sees 0 cases)
    rel = os.path.relpath(src.resolve(), start=dst.parent)
    dst.symlink_to(rel)


def build_arm(name: str, pairs: list[tuple[Path, Path]]) -> int:
    img_dir, gt_dir = INFER / name / "images", INFER / name / "labels"
    for d in (img_dir, gt_dir):
        d.mkdir(parents=True, exist_ok=True)
        for old in d.glob("*.nii.gz"):
            old.unlink()
    for img, gt in pairs:
        case = img.name.replace(".nii.gz", "")
        link(img, img_dir / f"{case}_0000.nii.gz")   # nnU-Net channel-0 convention
        link(gt, gt_dir / f"{case}.nii.gz")          # evaluator matches prediction names
    return len(pairs)


def main() -> int:
    # rung 1 -- the committed held-out set, not a fresh draw
    split_csv = ROOT / "splits/split_assignment.csv"
    held = [r["unit_id"] for r in csv.DictReader(open(split_csv)) if r["split"] == "test"]
    msd_pairs = []
    for case in held:
        img, gt = MSD / "imagesTr" / f"{case}.nii.gz", MSD / "labelsTr" / f"{case}.nii.gz"
        if not img.exists() or not gt.exists():
            print(f"FATAL: held-out case {case} missing image or label", file=sys.stderr)
            return 2
        msd_pairs.append((img, gt))

    def amos_pairs(view: str) -> list[tuple[Path, Path]]:
        out = []
        for img in sorted((VIEWS / view / "images").glob("amos_*.nii.gz")):
            gt = VIEWS / view / "labels" / img.name
            if not gt.exists():
                print(f"FATAL: {view}/{img.name} has no label", file=sys.stderr)
                sys.exit(2)
            out.append((img, gt))
        return out

    counts = {
        "rung1_msd_heldout": build_arm("rung1_msd_heldout", msd_pairs),
        "rung2_amos_ct": build_arm("rung2_amos_ct", amos_pairs("external_ct")),
        "rung3_amos_mri": build_arm("rung3_amos_mri", amos_pairs("external_mri")),
    }
    expected = {"rung1_msd_heldout": 9, "rung2_amos_ct": 300, "rung3_amos_mri": 60}
    for k in sorted(counts):
        flag = "OK" if counts[k] == expected[k] else f"MISMATCH (expected {expected[k]})"
        print(f"  {k}: {counts[k]} case(s)  {flag}")
    bad = {k: counts[k] for k in expected if counts[k] != expected[k]}
    if bad:
        print(f"COUNT MISMATCH vs EVALUATION_PLAN.md: {bad}", file=sys.stderr)
        return 1

    # The held-out 9 must not be among the 32 nnU-Net trained on. Prove it rather than assume it.
    trained = {p.name.replace("_0000.nii.gz", "")
               for p in (ROOT / "work/nnUNet_raw/Dataset009_Spleen/imagesTr").glob("*_0000.nii.gz")}
    overlap = trained & set(held)
    print(f"  nnUNet_raw/imagesTr holds {len(trained)} case(s); "
          f"overlap with the held-out 9 = {len(overlap)} {sorted(overlap)}")
    if overlap:
        print("FATAL: a held-out case is inside the training directory", file=sys.stderr)
        return 1
    print("held-out set is disjoint from the training directory")
    return 0


if __name__ == "__main__":
    sys.exit(main())
