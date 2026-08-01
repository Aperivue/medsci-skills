#!/usr/bin/env python3
"""Measure what the *trained* normalisation contract does to an inference cohort.

Rung 3's Dice collapsed to 0.015. A number that extreme has to be explained before it is
believed, and the explanation has to be measured rather than asserted. This script reads the
normalisation scheme nnU-Net recorded in `plans.json` at fingerprint time -- the one that
travels with the checkpoint and is applied to whatever is handed to `nnUNetv2_predict` -- and
replays it over every image in an inference arm.

It answers three questions per case, on the pixels:

  * Is this cohort even in the intensity domain the plan assumes? A CT plan assumes Hounsfield
    units, whose defining feature is an air floor near -1000. A volume whose minimum is 0 and
    which never goes negative is not in HU, whatever any metadata field claims.
  * How much of the volume does the plan's clip destroy? Voxels above the training foreground's
    99.5th percentile are flattened to one value; the fraction is the share of the image the
    network can no longer distinguish.
  * How much dynamic range survives? The count of distinct intensity levels left after the clip
    is the resolution the first convolution actually sees.

Nothing here runs a model or reads a prediction. It reads images and one JSON, and every number
in the write-up's mechanism paragraph comes from the file this emits.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import nibabel as nib
import numpy as np


def plan_normalisation(plans_path: Path, channel: str = "0") -> dict:
    """The clip bounds and z-score parameters the trained plan will apply at inference."""
    plans = json.loads(plans_path.read_text())
    cfg = plans["configurations"]["3d_fullres"]
    props = (plans.get("foreground_intensity_properties_per_channel")
             or plans.get("foreground_intensity_properties_by_modality") or {})
    if channel not in props:
        raise SystemExit(f"FATAL: channel {channel!r} absent from the plan's intensity properties")
    s = props[channel]
    return {
        "scheme": cfg.get("normalization_schemes"),
        "use_mask_for_norm": cfg.get("use_mask_for_norm"),
        "clip_lo": float(s["percentile_00_5"]),
        "clip_hi": float(s["percentile_99_5"]),
        "mean": float(s["mean"]),
        "std": float(s["std"]),
        "fingerprint_min": float(s["min"]),
        "fingerprint_max": float(s["max"]),
    }


def measure_case(path: Path, norm: dict) -> dict:
    a = np.asanyarray(nib.load(str(path)).dataobj).astype(np.float32)
    lo, hi, mean, std = norm["clip_lo"], norm["clip_hi"], norm["mean"], norm["std"]
    clipped = np.clip(a, lo, hi)
    z = (clipped - mean) / max(std, 1e-8)
    return {
        "case": path.name.replace("_0000.nii.gz", "").replace(".nii.gz", ""),
        "raw_min": round(float(a.min()), 2),
        "raw_max": round(float(a.max()), 2),
        "raw_p99": round(float(np.percentile(a, 99)), 2),
        "has_negative_voxel": bool((a < 0).any()),
        "frac_above_clip_hi": round(float((a > hi).mean()), 6),
        "frac_below_clip_lo": round(float((a < lo).mean()), 6),
        "levels_surviving_clip": int(np.unique(clipped).size),
        "z_min": round(float(z.min()), 4),
        "z_max": round(float(z.max()), 4),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Replay a trained plan's normalisation over an arm.")
    ap.add_argument("--images", required=True, help="directory of inference images (*.nii.gz)")
    ap.add_argument("--plans", required=True, help="plans.json written beside the predictions")
    ap.add_argument("--arm", required=True)
    ap.add_argument("--channel", default="0")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    norm = plan_normalisation(Path(a.plans), a.channel)
    images = sorted(p for p in Path(a.images).glob("*.nii*") if not p.name.startswith("._"))
    if not images:
        print(f"FATAL: no images in {a.images}", file=sys.stderr)
        return 2

    cases = []
    for p in images:
        row = measure_case(p, norm)
        cases.append(row)
        print(f"[{a.arm} {len(cases)}/{len(images)}] {row['case']} "
              f"raw[{row['raw_min']},{row['raw_max']}] "
              f"above_hi={row['frac_above_clip_hi']:.3f} levels={row['levels_surviving_clip']}",
              flush=True)

    def agg(key):
        v = np.array([c[key] for c in cases], dtype=float)
        return {"min": round(float(v.min()), 6),
                "median": round(float(np.median(v)), 6),
                "max": round(float(v.max()), 6)}

    out = {
        "measurement": "normalizer_modality_evidence",
        "arm": a.arm,
        "n_cases": len(cases),
        "plan_normalisation": norm,
        "cohort": {
            "cases_with_any_negative_voxel": sum(c["has_negative_voxel"] for c in cases),
            "raw_min": agg("raw_min"),
            "raw_max": agg("raw_max"),
            "frac_above_clip_hi": agg("frac_above_clip_hi"),
            "frac_below_clip_lo": agg("frac_below_clip_lo"),
            "levels_surviving_clip": agg("levels_surviving_clip"),
            "z_min": agg("z_min"),
            "z_max": agg("z_max"),
        },
        "cases": cases,
    }
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(out, indent=2) + "\n")

    c = out["cohort"]
    print(f"\n{a.arm}: {len(cases)} case(s)")
    print(f"  plan applies {norm['scheme']}: clip [{norm['clip_lo']:.0f}, {norm['clip_hi']:.0f}], "
          f"z-score mean {norm['mean']:.1f} / sd {norm['std']:.1f}")
    print(f"  cases with any negative voxel: {c['cases_with_any_negative_voxel']}/{len(cases)}")
    print(f"  fraction above the clip ceiling: median {c['frac_above_clip_hi']['median']*100:.1f}% "
          f"(range {c['frac_above_clip_hi']['min']*100:.1f}-{c['frac_above_clip_hi']['max']*100:.1f}%)")
    print(f"  intensity levels surviving the clip: median {c['levels_surviving_clip']['median']:.0f} "
          f"(range {c['levels_surviving_clip']['min']:.0f}-{c['levels_surviving_clip']['max']:.0f})")
    print(f"wrote {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
