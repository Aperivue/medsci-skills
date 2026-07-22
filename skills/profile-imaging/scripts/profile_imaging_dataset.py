#!/usr/bin/env python3
"""Profile a 3-D medical-imaging dataset (NIfTI) into the JSON the gate audits.

This is the *describe* half of profile-imaging: it opens every image (and its label,
when there is one) and records the facts that decide a study — the acquisition grid
and spacing, orientation, intensity domain, which label values are actually present,
how much of the volume the target occupies, and how big the target is in millilitres.
It draws no conclusion; `check_dataset_profile.py` does that, from this file.

Requires nibabel + numpy (it has to read images). The gate that consumes its output is
stdlib-only, so an audit can be re-run anywhere the JSON travels.

Layout: images and labels in separate directories, matched by filename — the MSD /
nnU-Net / AMOS convention (`imagesTr/case.nii.gz` <-> `labelsTr/case.nii.gz`).

Usage
  python3 profile_imaging_dataset.py \
      --split train:imagesTr:labelsTr --split test:imagesTs \
      --dataset "MSD Task09 Spleen" --declared-labels 0=background,1=spleen \
      --plan resample=true,reorient=false,loss=dice_ce,metrics=dice+hd95 \
      --out profile.json

A --split with no label directory is recorded as unlabelled, which is itself a
finding: a split named `test` with no labels cannot produce a held-out metric.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import nibabel as nib
import numpy as np


def profile_case(img_p: Path, lab_p: Path | None, split: str) -> dict:
    img = nib.load(str(img_p))
    zooms = tuple(float(z) for z in img.header.get_zooms()[:3])
    shape = tuple(int(s) for s in img.shape[:3])
    rec: dict = {
        "case": img_p.name.replace(".nii.gz", "").replace(".nii", ""),
        "split": split,
        "shape": list(shape),
        "spacing_mm": list(zooms),
        "orientation": "".join(nib.aff2axcodes(img.affine)),
        "voxel_volume_mm3": float(np.prod(zooms)),
        "label_values": None,
        "foreground_fraction": None,
        "target_volume_ml": None,
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

    if lab_p is None:
        return rec
    if not lab_p.exists():
        rec["flags"].append("LABEL_MISSING")
        return rec

    lab_img = nib.load(str(lab_p))
    lab = np.asanyarray(lab_img.dataobj)
    if tuple(int(s) for s in lab.shape[:3]) != shape:
        rec["flags"].append("LABEL_SHAPE_MISMATCH")
    rec["label_values"] = [int(v) for v in np.unique(lab)]
    n_fg = int((lab > 0).sum())
    rec["foreground_fraction"] = n_fg / int(lab.size)
    rec["target_volume_ml"] = n_fg * rec["voxel_volume_mm3"] / 1000.0
    return rec


def parse_kv(s: str | None, sep: str = ",") -> dict:
    out: dict = {}
    if not s:
        return out
    for part in s.split(sep):
        if not part.strip():
            continue
        k, _, v = part.partition("=")
        k, v = k.strip(), v.strip()
        if v.lower() in ("true", "false"):
            out[k] = v.lower() == "true"
        elif "+" in v:
            out[k] = [x for x in v.split("+") if x]
        else:
            out[k] = v
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Profile a NIfTI imaging dataset.")
    ap.add_argument("--split", action="append", required=True,
                    help="name:imagedir[:labeldir] — repeatable; omit labeldir if unlabelled")
    ap.add_argument("--dataset", default="", help="dataset name for the record")
    ap.add_argument("--declared-labels", default="",
                    help="comma list, e.g. 0=background,1=spleen")
    ap.add_argument("--plan", default="",
                    help="comma list, e.g. resample=true,reorient=false,loss=dice_ce,metrics=dice+hd95")
    ap.add_argument("--limit", type=int, default=0, help="profile at most N cases per split (0 = all)")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    splits, cases = [], []
    for spec in a.split:
        parts = spec.split(":")
        name, img_dir = parts[0], parts[1]
        lab_dir = parts[2] if len(parts) > 2 and parts[2] else None
        splits.append({"name": name, "labelled": lab_dir is not None})

        imgs = sorted(p for p in Path(img_dir).glob("*.nii*") if not p.name.startswith("._"))
        if a.limit:
            imgs = imgs[: a.limit]
        for i, p in enumerate(imgs, 1):
            cases.append(profile_case(p, (Path(lab_dir) / p.name) if lab_dir else None, name))
            print(f"[{name} {i}/{len(imgs)}] {p.name}", flush=True)

    labels_raw = parse_kv(a.declared_labels)
    profile = {
        "dataset": a.dataset,
        "declared_labels": {str(k): v for k, v in labels_raw.items()},
        "plan": parse_kv(a.plan),
        "splits": splits,
        "cases": cases,
    }
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(profile, indent=1), encoding="utf-8")
    print(f"\nwrote {a.out}  ({len(cases)} case(s) across {len(splits)} split(s))")
    print("Now audit it:  python3 check_dataset_profile.py --profile "
          f"{a.out} --strict")


if __name__ == "__main__":
    main()
