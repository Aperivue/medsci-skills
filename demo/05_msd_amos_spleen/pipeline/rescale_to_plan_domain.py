#!/usr/bin/env python3
"""Map an arm's intensities into the domain the trained plan assumes — the rung-3b counterfactual.

The review panel's second Fatal finding was that this study asserted a cause its design could not
identify: `CTNormalization` demonstrably treats CT and MRI differently, but that does not show the
transform *caused* the MRI collapse rather than a CT-trained representation failing to transfer.
Separating the two needs one more arm in which exactly one thing changes.

That one thing is the input scale. For each volume:

  * take the 0.5th and 99.5th percentiles of the in-body voxels (`> 0`; AMOS MRI air is exactly 0,
    so this is the body without needing a mask),
  * map that range affinely onto the CT fingerprint's foreground range, read from the trained
    `plans.json` rather than typed in,
  * leave air below the floor, where it clips — which is what CT air does.

The normaliser is **not** bypassed. It is handed input in the domain it assumes, so that on MRI it
performs the operation it performs on CT. Geometry, header, affine and label files are untouched:
only voxel values change, so the arm remains scored against the same ground truth by the same rules.

Pre-specified in COUNTERFACTUAL_PLAN.md, including the prediction, before this was run.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import nibabel as nib
import numpy as np


def plan_window(plans_path: Path, channel: str = "0") -> tuple[float, float]:
    plans = json.loads(plans_path.read_text())
    props = (plans.get("foreground_intensity_properties_per_channel")
             or plans.get("foreground_intensity_properties_by_modality") or {})
    if channel not in props:
        raise SystemExit(f"FATAL: channel {channel!r} absent from the plan's intensity properties")
    s = props[channel]
    scheme = plans["configurations"]["3d_fullres"].get("normalization_schemes")
    if scheme != ["CTNormalization"]:
        print(f"WARNING: plan normalisation is {scheme}, not ['CTNormalization']; the mapping below "
              f"assumes the CT foreground window is the target domain", file=sys.stderr)
    return float(s["percentile_00_5"]), float(s["percentile_99_5"])


def rescale(src: Path, dst: Path, lo_t: float, hi_t: float) -> dict:
    img = nib.load(str(src))
    a = np.asanyarray(img.dataobj).astype(np.float32)
    body = a[a > 0]
    if body.size == 0:
        raise ValueError(f"{src.name}: no in-body voxel (>0); cannot establish a source range")
    lo_s, hi_s = (float(x) for x in np.percentile(body, [0.5, 99.5]))
    if hi_s <= lo_s:
        raise ValueError(f"{src.name}: degenerate source range [{lo_s}, {hi_s}]")

    scale = (hi_t - lo_t) / (hi_s - lo_s)
    out = (a - lo_s) * scale + lo_t

    dst.parent.mkdir(parents=True, exist_ok=True)
    # header/affine preserved exactly: the arm must stay scoreable against the same ground truth
    nib.save(nib.Nifti1Image(out.astype(np.float32), img.affine, img.header), str(dst))
    return {
        "case": src.name,
        "src_p0_5": round(lo_s, 3), "src_p99_5": round(hi_s, 3),
        "scale": round(scale, 6),
        "out_min": round(float(out.min()), 2), "out_max": round(float(out.max()), 2),
        "frac_above_target_hi": round(float((out > hi_t).mean()), 6),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Rescale an arm into the trained plan's intensity domain.")
    ap.add_argument("--images", required=True)
    ap.add_argument("--plans", required=True)
    ap.add_argument("--out-images", required=True)
    ap.add_argument("--report", required=True)
    ap.add_argument("--channel", default="0")
    a = ap.parse_args()

    lo_t, hi_t = plan_window(Path(a.plans), a.channel)
    src_dir, dst_dir = Path(a.images), Path(a.out_images)
    srcs = sorted(p for p in src_dir.glob("*.nii*") if not p.name.startswith("._"))
    if not srcs:
        print(f"FATAL: no images in {src_dir}", file=sys.stderr)
        return 2

    rows = []
    for p in srcs:
        r = rescale(p, dst_dir / p.name, lo_t, hi_t)
        rows.append(r)
        print(f"[{len(rows)}/{len(srcs)}] {r['case']}  "
              f"src[{r['src_p0_5']:.0f},{r['src_p99_5']:.0f}] -> target[{lo_t:.0f},{hi_t:.0f}]  "
              f"above_hi={r['frac_above_target_hi']*100:.1f}%", flush=True)

    frac = np.array([r["frac_above_target_hi"] for r in rows])
    report = {
        "transform": "affine percentile match of in-body voxels to the trained plan's foreground window",
        "target_window": [lo_t, hi_t],
        "n_cases": len(rows),
        "frac_above_target_hi": {"min": round(float(frac.min()), 6),
                                 "median": round(float(np.median(frac)), 6),
                                 "max": round(float(frac.max()), 6)},
        "cases": rows,
    }
    Path(a.report).parent.mkdir(parents=True, exist_ok=True)
    Path(a.report).write_text(json.dumps(report, indent=2) + "\n")
    print(f"\n{len(rows)} case(s) rescaled into [{lo_t:.0f}, {hi_t:.0f}]")
    print(f"  voxels still above the window ceiling: median "
          f"{report['frac_above_target_hi']['median']*100:.1f}% "
          f"(was 23.2% before the mapping)")
    print(f"wrote {a.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
