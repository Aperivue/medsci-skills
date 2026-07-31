#!/usr/bin/env python3
"""Stage 0 EDA for a 3-D imaging segmentation dataset (NIfTI, MSD/AMOS layout).

Profiles what actually decides the research plan: how heterogeneous the acquisition is
(spacing, shape, orientation), what the intensity domain looks like (do we window?),
how big and how rare the target is (class imbalance, organ volume), and which cases are
defective (empty label, unexpected label values, missing pair).

Nothing here is a modelling decision — it is the evidence a modelling decision needs.
Every number is computed from the files; none is assumed.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import nibabel as nib
import numpy as np


def case_profile(img_p: Path, lab_p: Path | None) -> dict:
    img = nib.load(str(img_p))
    hdr = img.header
    zooms = tuple(float(z) for z in hdr.get_zooms()[:3])
    shape = tuple(int(s) for s in img.shape[:3])
    orient = "".join(nib.aff2axcodes(img.affine))
    rec: dict = {
        "case": img_p.name.replace(".nii.gz", ""),
        "shape": shape,
        "spacing_mm": zooms,
        "orientation": orient,
        "voxel_volume_mm3": float(np.prod(zooms)),
        "flags": [],
    }

    data = np.asanyarray(img.dataobj, dtype=np.float32)
    rec["intensity"] = {
        "min": float(data.min()),
        "p01": float(np.percentile(data, 1)),
        "p50": float(np.percentile(data, 50)),
        "p99": float(np.percentile(data, 99)),
        "max": float(data.max()),
    }

    if lab_p is None or not lab_p.exists():
        rec["flags"].append("LABEL_MISSING")
        return rec

    lab = np.asanyarray(nib.load(str(lab_p)).dataobj)
    vals = np.unique(lab)
    rec["label_values"] = [int(v) for v in vals]
    if lab.shape[:3] != shape:
        rec["flags"].append("LABEL_SHAPE_MISMATCH")

    n_fg = int((lab > 0).sum())
    n_tot = int(lab.size)
    rec["foreground_voxels"] = n_fg
    rec["foreground_fraction"] = n_fg / n_tot
    rec["target_volume_ml"] = n_fg * rec["voxel_volume_mm3"] / 1000.0
    if n_fg == 0:
        rec["flags"].append("LABEL_EMPTY")
    return rec


def summarise(recs: list[dict]) -> dict:
    def col(key, sub=None):
        out = []
        for r in recs:
            v = r.get(key)
            if v is None:
                continue
            out.append(v[sub] if sub is not None else v)
        return np.array(out, dtype=float) if out else np.array([])

    def stats(a):
        if a.size == 0:
            return None
        return {
            "min": float(a.min()), "p25": float(np.percentile(a, 25)),
            "median": float(np.median(a)), "p75": float(np.percentile(a, 75)),
            "max": float(a.max()), "mean": float(a.mean()), "sd": float(a.std(ddof=1)) if a.size > 1 else 0.0,
        }

    spac = np.array([r["spacing_mm"] for r in recs], dtype=float)
    shp = np.array([r["shape"] for r in recs], dtype=float)
    flags: dict[str, int] = {}
    for r in recs:
        for f in r["flags"]:
            flags[f] = flags.get(f, 0) + 1

    return {
        "n_cases": len(recs),
        "orientations": sorted({r["orientation"] for r in recs}),
        "spacing_mm": {ax: stats(spac[:, i]) for i, ax in enumerate("xyz")},
        "shape_voxels": {ax: stats(shp[:, i]) for i, ax in enumerate("xyz")},
        "intensity_p01": stats(col("intensity", "p01")),
        "intensity_p99": stats(col("intensity", "p99")),
        "foreground_fraction": stats(col("foreground_fraction")),
        "target_volume_ml": stats(col("target_volume_ml")),
        "label_values_union": sorted({v for r in recs for v in r.get("label_values", [])}),
        "flag_counts": flags,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--images", required=True, help="directory of image NIfTIs")
    ap.add_argument("--labels", help="directory of label NIfTIs (same filenames)")
    ap.add_argument("--out", required=True, help="output JSON path")
    ap.add_argument("--limit", type=int, default=0, help="profile at most N cases (0 = all)")
    a = ap.parse_args()

    imgs = sorted(p for p in Path(a.images).glob("*.nii.gz") if not p.name.startswith("._"))
    if a.limit:
        imgs = imgs[: a.limit]
    labdir = Path(a.labels) if a.labels else None

    recs = []
    for i, p in enumerate(imgs, 1):
        recs.append(case_profile(p, (labdir / p.name) if labdir else None))
        print(f"[{i}/{len(imgs)}] {p.name}", flush=True)

    out = {"images_dir": str(a.images), "labels_dir": str(a.labels), "cases": recs,
           "summary": summarise(recs)}
    Path(a.out).write_text(json.dumps(out, indent=1), encoding="utf-8")
    print("\n=== SUMMARY ===")
    print(json.dumps(out["summary"], indent=1))


if __name__ == "__main__":
    main()
