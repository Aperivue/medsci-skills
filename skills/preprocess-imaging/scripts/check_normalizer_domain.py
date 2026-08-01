#!/usr/bin/env python3
"""Normaliser-domain gate: is the cohort you are about to predict in the domain the trained
normalisation contract assumes?

`check_preprocessing_leakage.py` asks whether a data-fitted transform was fit on the right SCOPE
(train only, after the split). This asks a different question, at a different moment: at inference,
is the cohort being handed to a trained normaliser in the INTENSITY DOMAIN that normaliser was fit
on? Nothing else in this toolkit asks it, and nothing carries a profiling-stage observation forward
to the moment of use.

**Why this exists.** In demo/05_msd_amos_spleen, a segmentation model trained on CT was applied to
MRI. The training plan carried `CTNormalization` into inference and the inference command had no
argument declaring the incoming modality, so a Hounsfield-unit clip was applied to arbitrary-unit
images. Median Dice was 0.0152. Two independent counterfactual arms — rescale the input, or swap the
normaliser — each recovered it to ~0.29 without retraining, so roughly **0.28 Dice** was the domain
mismatch alone. The run exited 0 and wrote a plausible-looking segmentation for every case.

The profiler had already seen it. `/profile-imaging` flagged `INTENSITY_SCALE_INCONSISTENT` on that
cohort *before training* — as a **Minor**, in a directory no later step reads. The gap this gate
closes is therefore **routing and severity**, not detection: it re-reads an existing profile against
the contract that will actually be applied, at the point where ignoring it costs something.

Reads two JSON files and nothing else — no imaging library, no pixels, no model. stdlib only, so it
travels with the artifacts.

  --profile   a /profile-imaging profile (`profile_imaging_dataset.py` output) with per-case
              `intensity` {min, p01, p50, p99, max} and `split`
  --contract  the normalisation contract that will be applied. Either an nnU-Net-style `plans.json`
              (the scheme and the foreground statistics are read from it) or a small JSON of the
              form {"scheme": "...", "assumes": "hounsfield"|"arbitrary"|"zero_mean",
              "clip": [lo, hi], "mean": m, "std": s}.

Verdicts:

  NORMALIZER_DOMAIN_MISMATCH  (Major)  the contract assumes Hounsfield units and the split contains
                                       no negative voxels — HU is defined by an air floor near
                                       -1000, so a cohort that never goes negative is not in it
  NORMALIZER_SPLIT_DIVERGENCE (Flag)   splits inside one cohort disagree about the intensity domain,
                                       so one contract cannot be right for all of them

**A third check was written and deleted.** `NORMALIZER_CLIP_DESTRUCTIVE` compared each split's 99th
percentile against the contract's clip ceiling. Run against the cohorts this repository already
produces, it fired on **100% of the CT arm and 100% of the MSD training set** — the very data the
plan was fit on. Of course it did: a CT volume's p99 is bone, and clipping bone above a soft-tissue
window is what `CTNormalization` is *for*. A five-number summary cannot distinguish "the window is
doing its job" from "the window is destroying the image", and a check that rejects its own training
data is worse than no check. Deleted rather than tuned.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HU_AIR_CEILING = -500.0     # a genuine HU volume has voxels below this (air is near -1000)


def load(p: str) -> dict:
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception as exc:                                  # noqa: BLE001
        print(f"FATAL: cannot read {p}: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc


def contract_from(obj: dict, channel: str = "0") -> dict:
    """Accept an nnU-Net plans.json or a small hand-written contract."""
    if "configurations" in obj:                                # nnU-Net plans.json
        cfg = obj["configurations"].get("3d_fullres") or next(iter(obj["configurations"].values()))
        schemes = cfg.get("normalization_schemes") or []
        scheme = schemes[0] if schemes else "unknown"
        props = (obj.get("foreground_intensity_properties_per_channel")
                 or obj.get("foreground_intensity_properties_by_modality") or {})
        s = props.get(channel, {})
        return {
            "scheme": scheme,
            "assumes": "hounsfield" if "CT" in scheme else "arbitrary",
            "clip": [s.get("percentile_00_5"), s.get("percentile_99_5")] if s else None,
            "mean": s.get("mean"), "std": s.get("std"),
        }
    c = dict(obj)
    if "scheme" not in c:
        # Fail loudly rather than scoring an unparseable contract as "assumes arbitrary" and
        # returning OK. A gate that passes on input it could not read looks exactly like a gate
        # that passed — this one refuses instead.
        raise SystemExit(
            "FATAL: --contract is neither an nnU-Net plans.json (no 'configurations' key) nor a "
            "contract object (no 'scheme' key). Refusing to evaluate a contract I cannot read; "
            "pass the plans.json the model was trained under, or a JSON with at least "
            '{"scheme": "...", "assumes": "hounsfield"|"arbitrary"}.')
    c.setdefault("assumes", "hounsfield" if "CT" in str(c.get("scheme", "")) else "arbitrary")
    return c


def by_split(profile: dict) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for case in profile.get("cases", []):
        if "intensity" not in case:
            continue
        out.setdefault(case.get("split", "(unsplit)"), []).append(case)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Does the cohort match the normaliser's assumed domain?")
    ap.add_argument("--profile", required=True)
    ap.add_argument("--contract", required=True)
    ap.add_argument("--channel", default="0")
    ap.add_argument("--splits", nargs="*", default=None,
                    help="restrict to these split names (default: every labelled split)")
    ap.add_argument("--out")
    ap.add_argument("--strict", action="store_true", help="exit 1 when a Major is raised")
    a = ap.parse_args()

    profile = load(a.profile)
    contract = contract_from(load(a.contract), a.channel)
    groups = by_split(profile)
    if a.splits:
        groups = {k: v for k, v in groups.items() if k in a.splits}
    if not groups:
        print("FATAL: no per-case intensity found in the profile", file=sys.stderr)
        return 2

    claims, domains = [], {}
    for split, cases in sorted(groups.items()):
        mins = [c["intensity"].get("min") for c in cases if c["intensity"].get("min") is not None]
        if not mins:
            continue
        n_air = sum(1 for m in mins if m <= HU_AIR_CEILING)
        looks_hu = n_air == len(mins)
        domains[split] = "hounsfield" if looks_hu else ("mixed" if n_air else "non-hounsfield")

        if contract.get("assumes") == "hounsfield" and n_air == 0:
            claims.append({
                "verdict": "NORMALIZER_DOMAIN_MISMATCH", "severity": "Major", "split": split,
                "detail": (f"the contract applies {contract.get('scheme')}, which assumes Hounsfield "
                           f"units, but 0 of {len(mins)} case(s) in '{split}' contain a voxel at or "
                           f"below {HU_AIR_CEILING:.0f}. Hounsfield units are defined by an air "
                           f"floor near -1000; a cohort that never goes negative is not in them. "
                           f"Per-case minima range {min(mins):.0f} to {max(mins):.0f}."),
            })
        elif contract.get("assumes") == "hounsfield" and 0 < n_air < len(mins):
            claims.append({
                "verdict": "NORMALIZER_SPLIT_DIVERGENCE", "severity": "Flag", "split": split,
                "detail": (f"{n_air} of {len(mins)} case(s) in '{split}' bottom out near air and the "
                           f"rest do not — mixed modality, or a rescale applied to part of the "
                           f"cohort. One normalisation contract cannot be right for both."),
            })

    if len({d for d in domains.values() if d != "mixed"}) > 1:
        claims.append({
            "verdict": "NORMALIZER_SPLIT_DIVERGENCE", "severity": "Flag", "split": "(cohort)",
            "detail": (f"splits disagree about the intensity domain ({domains}); a single trained "
                       f"contract cannot be correct for all of them."),
        })

    n_major = sum(1 for c in claims if c["severity"] == "Major")
    report = {
        "detector": "check_normalizer_domain",
        "profile": a.profile, "contract": a.contract,
        "contract_read": contract,
        "splits_examined": {k: {"n": len(v), "domain": domains.get(k)} for k, v in groups.items()},
        "claims": claims,
        "summary": {"n_claims": len(claims), "n_major": n_major,
                    "n_flag": len(claims) - n_major,
                    "verdict": "OK" if not claims else ("MAJOR" if n_major else "FLAG")},
    }

    print("=" * 41)
    print(" Normaliser-Domain Gate (preprocess-imaging)")
    print("=" * 41)
    print(f"  contract: {contract.get('scheme')} (assumes {contract.get('assumes')})"
          + (f", clip [{contract['clip'][0]:.0f}, {contract['clip'][1]:.0f}]"
             if contract.get("clip") and None not in contract["clip"] else ""))
    print("| Check | Severity | Detail |")
    print("|---|---|---|")
    if claims:
        for c in claims:
            print(f"| {c['verdict']} | {c['severity']} | {c['detail']} |")
    else:
        print("| (none) | — | every split is in the domain the contract assumes |")
    print()
    print(f"MAJOR candidate: {n_major} domain issue(s)." if n_major
          else ("FLAG: review the divergence above." if claims
                else "OK: every split is in the domain the contract assumes."))

    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(json.dumps(report, indent=2) + "\n")
        print(f"\nwrote {a.out}")
    return 1 if (a.strict and n_major) else 0


if __name__ == "__main__":
    raise SystemExit(main())
