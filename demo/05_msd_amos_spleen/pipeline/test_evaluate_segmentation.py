#!/usr/bin/env python3
"""Tests for evaluate_segmentation.py on synthetic volumes whose answers are known by hand.

A metric implementation that has never been checked against an analytic answer is a number
generator, not a measurement -- and Dice/HD95 are exactly the pair where a plausible-looking
wrong answer survives review. Every assertion below has a value derived on paper, including the
anisotropic case, which is where an unscaled distance transform would silently be wrong by the
slice-thickness ratio.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import nibabel as nib
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evaluate_segmentation import dice, evaluate_case, hd95  # noqa: E402

FAIL = 0


def check(label: str, cond: bool, got=None, want=None) -> None:
    global FAIL
    if cond:
        print(f"  PASS  {label}")
    else:
        FAIL += 1
        print(f"  FAIL  {label}" + (f"   got={got!r} want={want!r}" if got is not None else ""))


def cube(shape, lo, hi):
    m = np.zeros(shape, dtype=bool)
    m[lo[0]:hi[0], lo[1]:hi[1], lo[2]:hi[2]] = True
    return m


def write(mask, spacing, path):
    aff = np.diag([spacing[0], spacing[1], spacing[2], 1.0])
    nib.save(nib.Nifti1Image(mask.astype(np.uint8), aff), str(path))


# ---- Dice ------------------------------------------------------------------
S = (40, 40, 40)
a = cube(S, (10, 10, 10), (20, 20, 20))            # 10^3 = 1000 voxels
check("Dice of identical masks is 1", dice(a, a) == 1.0, dice(a, a), 1.0)

b = cube(S, (25, 25, 25), (35, 35, 35))            # disjoint
check("Dice of disjoint masks is 0", dice(a, b) == 0.0, dice(a, b), 0.0)

# shift by 2 along x: overlap = 8*10*10 = 800; Dice = 2*800/(1000+1000) = 0.8
c = cube(S, (12, 10, 10), (22, 20, 20))
check("Dice of a 2-voxel-shifted 10^3 cube is 0.8", abs(dice(a, c) - 0.8) < 1e-12, dice(a, c), 0.8)

empty = np.zeros(S, dtype=bool)
check("Dice is NaN when both masks are empty", np.isnan(dice(empty, empty)))
check("Dice is 0 when only the prediction is empty", dice(a, empty) == 0.0, dice(a, empty), 0.0)

# ---- HD95 ------------------------------------------------------------------
check("HD95 of identical masks is 0", hd95(a, a, (1.0, 1.0, 1.0)) == 0.0)

# Isotropic 1 mm, cube shifted 2 voxels along x. The two surfaces are never more than
# 2 mm apart along x, so the 95th percentile of symmetric surface distance is <= 2 mm,
# and it is strictly positive because the shift is real.
h = hd95(a, c, (1.0, 1.0, 1.0))
check("HD95 of a 2-voxel shift at 1 mm is in (0, 2]", 0.0 < h <= 2.0 + 1e-9, h, "(0, 2]")

# Anisotropy is the part that breaks when spacing is ignored. Same 2-voxel shift, but along z
# with 5 mm slices: the distance is 5x larger. An unscaled EDT would return the isotropic
# answer and be wrong by exactly that factor.
d_z = cube(S, (10, 10, 12), (20, 20, 22))
h_iso = hd95(a, d_z, (1.0, 1.0, 1.0))
h_ani = hd95(a, d_z, (1.0, 1.0, 5.0))
check("HD95 scales with through-plane spacing (5 mm slices)",
      abs(h_ani - 5.0 * h_iso) < 1e-6, (h_ani, h_iso), "h_ani == 5 * h_iso")
check("the anisotropic answer is not the isotropic one", h_ani != h_iso)

check("HD95 is NaN when one mask is empty", np.isnan(hd95(a, empty, (1.0, 1.0, 1.0))))

# ---- evaluate_case end to end ---------------------------------------------
with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    spacing = (0.8, 0.8, 5.0)

    # multi-organ ground truth: spleen=1 elsewhere 6 (liver). Only label 1 must be scored.
    gt = np.zeros(S, dtype=np.uint8)
    gt[cube(S, (10, 10, 10), (20, 20, 20))] = 1
    gt[cube(S, (25, 25, 25), (35, 35, 35))] = 6
    write(gt, spacing, td / "case_atlas.nii.gz")
    write(cube(S, (10, 10, 10), (20, 20, 20)), spacing, td / "pred_perfect.nii.gz")
    r = evaluate_case(td / "case_atlas.nii.gz", td / "pred_perfect.nii.gz", 1)
    check("binarising to the target label ignores the other organ", r["dice"] == 1.0, r["dice"], 1.0)
    check("gt volume in mL uses voxel spacing",
          abs(r["gt_ml"] - 1000 * 0.8 * 0.8 * 5.0 / 1000.0) < 1e-6,
          r["gt_ml"], 1000 * 0.8 * 0.8 * 5.0 / 1000.0)
    check("HD95 is 0 for a perfect prediction", r["hd95_mm"] == 0.0, r["hd95_mm"], 0.0)

    # a prediction that segments the LIVER instead of the spleen must score 0, not 1 --
    # this is the failure a gt>0 binarisation would hide
    write(cube(S, (25, 25, 25), (35, 35, 35)), spacing, td / "pred_liver.nii.gz")
    r = evaluate_case(td / "case_atlas.nii.gz", td / "pred_liver.nii.gz", 1)
    check("predicting the wrong organ scores Dice 0", r["dice"] == 0.0, r["dice"], 0.0)

    # target-free case: reference has no spleen, only liver
    gt_nospleen = np.zeros(S, dtype=np.uint8)
    gt_nospleen[cube(S, (25, 25, 25), (35, 35, 35))] = 6
    write(gt_nospleen, spacing, td / "case_nospleen.nii.gz")
    write(cube(S, (10, 10, 10), (12, 12, 12)), spacing, td / "pred_fp.nii.gz")
    r = evaluate_case(td / "case_nospleen.nii.gz", td / "pred_fp.nii.gz", 1)
    check("target-free case is flagged, not scored", r["gt_empty"] == 1 and r["dice"] == "",
          (r["gt_empty"], r["dice"]), (1, ""))
    # volumes are rounded to 3 dp for the CSV, so compare against the rounded expectation
    want_fp_ml = round(8 * 0.8 * 0.8 * 5.0 / 1000.0, 3)
    check("target-free case still reports the false-positive volume",
          r["pred_ml"] == want_fp_ml, r["pred_ml"], want_fp_ml)

    # empty prediction on a real target: Dice 0, HD95 withheld rather than imputed
    write(np.zeros(S, dtype=bool), spacing, td / "pred_empty.nii.gz")
    r = evaluate_case(td / "case_atlas.nii.gz", td / "pred_empty.nii.gz", 1)
    check("empty prediction scores Dice 0", r["dice"] == 0.0, r["dice"], 0.0)
    check("empty prediction leaves HD95 blank rather than imputed",
          r["hd95_mm"] == "" and r["pred_empty"] == 1)

print()
print("ALL PASS (evaluate_segmentation)" if FAIL == 0 else f"{FAIL} FAILURE(S)")
sys.exit(1 if FAIL else 0)
