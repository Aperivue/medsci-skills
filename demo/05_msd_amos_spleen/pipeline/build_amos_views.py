#!/usr/bin/env python3
"""Build modality-separated symlink views of AMOS22.

AMOS ships CT and MRI *in the same directory*, distinguished only by the case number.
readme.md says "id numbers less than 500 belong to CT data, otherwise they belong to MRI" AND
"500 CT and 100 MRI scans". With ids running 1-600 with no gaps those cannot both be true, and
the voxels settle it: amos_0500 is min -1024 HU on a 512x512x246 grid (CT), amos_0501 is min 0 /
max 186451 on 1024x1024x48 (MRI). The boundary is id <= 500 = CT; the readme's prose rule is
off by one.
Every tool downstream -- including our own /profile-imaging -- takes directories, so the
modality split has to be materialised before anything can look at CT and MRI separately.

Labelled data = imagesTr+labelsTr (240) and imagesVa+labelsVa (120). imagesTs (240) ships
with an empty labelsTs/, so it carries no ground truth.

Views built (all symlinks, no copies):
  views/external_ct/{images,labels}   -- 300 labelled CT   (rung 2, genuine external)
  views/external_mri/{images,labels}  --  60 labelled MRI  (rung 3, modality shift)
  views/amos_test/images              -- 240 unlabelled    (shipped test, no GT)
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

# Project root defaults to this demo folder (pipeline/..) so the script runs from a clone; override
# with DEMO5_ROOT when the datasets sit elsewhere, which at ~25 GB they usually do.
PROJECT = Path(os.environ.get("DEMO5_ROOT", Path(__file__).resolve().parent.parent))
ROOT = PROJECT / "data/amos22/amos22"
VIEWS = ROOT.parent / "views"
CASE_RE = re.compile(r"^amos_(\d+)\.nii\.gz$")
CT_ID_MAX = 500  # from the voxels, not from the readme sentence (see docstring)


def modality(name: str) -> str | None:
    m = CASE_RE.match(name)
    if not m:
        return None
    return "CT" if int(m.group(1)) <= CT_ID_MAX else "MRI"


def link_into(dst: Path, src_files: list[Path]) -> int:
    dst.mkdir(parents=True, exist_ok=True)
    n = 0
    for f in src_files:
        target = dst / f.name
        if target.is_symlink() or target.exists():
            target.unlink()
        target.symlink_to(f.resolve())
        n += 1
    return n


def main() -> int:
    pairs = {"CT": {"images": [], "labels": []}, "MRI": {"images": [], "labels": []}}
    unlabelled: list[Path] = []
    orphans: list[str] = []

    for split in ("Tr", "Va"):
        img_dir, lab_dir = ROOT / f"images{split}", ROOT / f"labels{split}"
        for img in sorted(img_dir.glob("amos_*.nii.gz")):
            mod = modality(img.name)
            if mod is None:
                orphans.append(str(img))
                continue
            lab = lab_dir / img.name
            if not lab.exists():
                orphans.append(f"{img.name}: no label in labels{split}")
                continue
            pairs[mod]["images"].append(img)
            pairs[mod]["labels"].append(lab)

    for img in sorted((ROOT / "imagesTs").glob("amos_*.nii.gz")):
        unlabelled.append(img)

    counts = {}
    counts["external_ct/images"] = link_into(VIEWS / "external_ct" / "images", pairs["CT"]["images"])
    counts["external_ct/labels"] = link_into(VIEWS / "external_ct" / "labels", pairs["CT"]["labels"])
    counts["external_mri/images"] = link_into(VIEWS / "external_mri" / "images", pairs["MRI"]["images"])
    counts["external_mri/labels"] = link_into(VIEWS / "external_mri" / "labels", pairs["MRI"]["labels"])
    counts["amos_test/images"] = link_into(VIEWS / "amos_test" / "images", unlabelled)

    for k in sorted(counts):
        print(f"{k}: {counts[k]}")
    n_lab_ts = len(list((ROOT / "labelsTs").glob("*.nii.gz")))
    print(f"labelsTs actual files: {n_lab_ts}  (0 => shipped test set has no ground truth)")
    if orphans:
        print(f"ORPHANS ({len(orphans)}):")
        for o in orphans[:20]:
            print("  ", o)
    else:
        print("orphans: none (every labelled image has a matching label)")

    expected = {"external_ct/images": 300, "external_ct/labels": 300,
                "external_mri/images": 60, "external_mri/labels": 60,
                "amos_test/images": 240}
    bad = {k: (counts[k], v) for k, v in expected.items() if counts[k] != v}
    if bad:
        print("COUNT MISMATCH vs readme-derived expectation:", bad)
        return 1
    print("counts match the readme-derived expectation")
    return 0


if __name__ == "__main__":
    sys.exit(main())
