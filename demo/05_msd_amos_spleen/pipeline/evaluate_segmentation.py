#!/usr/bin/env python3
"""Per-case Dice + HD95 for a binary segmentation arm, emitted as the CSV /analyze-stats reads.

Implements the rules fixed in EVALUATION_PLAN.md *before* any prediction existed:

  * ground truth is binarised to `== --gt-label` (AMOS ships a 15-organ atlas; the spleen is
    index 1, read from its dataset.json). MSD is already binary and the same rule is a no-op.
  * a case whose reference is empty has no Dice (0/0 is undefined). Those cases are written to
    the CSV with dice/hd95 blank, `gt_empty=1`, and their predicted volume in mL, so the arm's
    denominator and the false-positive check are both on the record instead of a silent drop.
  * HD95 is a *symmetric* surface distance at the 95th percentile, computed with the voxel
    spacing supplied (these volumes are anisotropic: 0.79 x 0.79 x up to 8 mm, so an unscaled
    distance transform would be wrong by up to 10x on the through-plane axis).
  * a non-empty reference with an empty prediction scores Dice 0 and has no HD95 (there is no
    predicted surface to measure from). It is written as blank with `pred_empty=1` rather than
    imputed, because the usual imputation -- the image diagonal -- is a made-up number.

Never fabricates: every row comes from two files on disk.
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import nibabel as nib
import numpy as np
from scipy.ndimage import binary_erosion, distance_transform_edt


def _surface(mask: np.ndarray) -> np.ndarray:
    """Voxels of `mask` that touch the background under 6-connectivity."""
    if not mask.any():
        return np.zeros_like(mask, dtype=bool)
    structure = np.zeros((3, 3, 3), dtype=bool)
    structure[1, 1, :] = structure[1, :, 1] = structure[:, 1, 1] = True
    eroded = binary_erosion(mask, structure=structure, border_value=0)
    return mask & ~eroded


def surface_distances(a: np.ndarray, b: np.ndarray, spacing: tuple[float, float, float]) -> np.ndarray:
    """Symmetric surface distances in mm: a->b concatenated with b->a."""
    sa, sb = _surface(a), _surface(b)
    if not sa.any() or not sb.any():
        return np.array([])
    # EDT of the complement gives, at every voxel, the distance to the nearest surface voxel.
    dt_to_b = distance_transform_edt(~sb, sampling=spacing)
    dt_to_a = distance_transform_edt(~sa, sampling=spacing)
    return np.concatenate([dt_to_b[sa], dt_to_a[sb]])


def dice(a: np.ndarray, b: np.ndarray) -> float:
    denom = int(a.sum()) + int(b.sum())
    if denom == 0:
        return float("nan")
    return 2.0 * float(np.logical_and(a, b).sum()) / denom


def hd95(a: np.ndarray, b: np.ndarray, spacing: tuple[float, float, float]) -> float:
    d = surface_distances(a, b, spacing)
    return float(np.percentile(d, 95)) if d.size else float("nan")


def evaluate_case(gt_path: Path, pred_path: Path, gt_label: int) -> dict:
    gt_img = nib.load(str(gt_path))
    spacing = tuple(float(z) for z in gt_img.header.get_zooms()[:3])
    gt = np.asanyarray(gt_img.dataobj)
    gt_bin = (gt == gt_label)

    pred_img = nib.load(str(pred_path))
    pred = np.asanyarray(pred_img.dataobj)
    pred_bin = (pred > 0)

    if pred_bin.shape != gt_bin.shape:
        raise ValueError(f"shape mismatch {pred_bin.shape} vs {gt_bin.shape} for {gt_path.name}")

    vox_ml = float(np.prod(spacing)) / 1000.0
    row = {
        "case": gt_path.name.replace(".nii.gz", ""),
        "spacing_x": spacing[0], "spacing_y": spacing[1], "spacing_z": spacing[2],
        "gt_ml": round(float(gt_bin.sum()) * vox_ml, 3),
        "pred_ml": round(float(pred_bin.sum()) * vox_ml, 3),
        "gt_empty": int(not gt_bin.any()),
        "pred_empty": int(not pred_bin.any()),
        "dice": "", "hd95_mm": "",
    }
    if row["gt_empty"]:
        return row                       # undefined by construction; see EVALUATION_PLAN.md 4
    row["dice"] = round(dice(gt_bin, pred_bin), 6)
    if not row["pred_empty"]:
        row["hd95_mm"] = round(hd95(gt_bin, pred_bin, spacing), 4)
    return row


def main() -> int:
    ap = argparse.ArgumentParser(description="Per-case Dice/HD95 for one evaluation arm.")
    ap.add_argument("--gt-dir", required=True)
    ap.add_argument("--pred-dir", required=True)
    ap.add_argument("--gt-label", type=int, default=1, help="label index of the target structure")
    ap.add_argument("--arm", required=True, help="arm name written into every row")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    gt_dir, pred_dir = Path(a.gt_dir), Path(a.pred_dir)
    gts = sorted(p for p in gt_dir.glob("*.nii*") if not p.name.startswith("._"))
    if not gts:
        print(f"FATAL: no ground truth in {gt_dir}", file=sys.stderr)
        return 2

    rows, missing = [], []
    for gt in gts:
        pred = pred_dir / gt.name
        if not pred.exists():
            missing.append(gt.name)
            continue
        r = evaluate_case(gt, pred, a.gt_label)
        r["arm"] = a.arm
        rows.append(r)
        print(f"[{a.arm} {len(rows)}/{len(gts)}] {r['case']} dice={r['dice']} hd95={r['hd95_mm']}",
              flush=True)

    if missing:
        # Loud, not silent: a missing prediction changes the denominator.
        print(f"WARNING: {len(missing)} case(s) have ground truth but no prediction: "
              f"{missing[:10]}", file=sys.stderr)

    fields = ["arm", "case", "dice", "hd95_mm", "gt_ml", "pred_ml", "gt_empty", "pred_empty",
              "spacing_x", "spacing_y", "spacing_z"]
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    with open(a.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})

    scored = [r for r in rows if r["dice"] != ""]
    d = np.array([r["dice"] for r in scored], dtype=float)
    print(f"\n{a.arm}: {len(rows)} case(s) evaluated, {len(scored)} scored, "
          f"{sum(r['gt_empty'] for r in rows)} target-free, "
          f"{sum(r['pred_empty'] for r in rows)} with empty prediction")
    if d.size:
        print(f"  Dice median {np.median(d):.4f}  mean {d.mean():.4f}  min {d.min():.4f}")
    print(f"wrote {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
