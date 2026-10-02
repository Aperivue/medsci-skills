#!/usr/bin/env python3
"""Regression test for scripts/critic_figure.py: a check that could not run is never a PASS.

Synthetic blank PNGs (Pillow; no OCR needed). The spec is 600 dpi at 7.0 in, i.e. 4200 px wide:

  * no DPI tag, 1000 px wide  -> 1000 / 7.0 dpi at the spec width: flagged, exit 1
    (before the fix the DPI and width checks were skipped and the summary read PASS, exit 0)
  * no DPI tag, 4200 px wide  -> meets the spec at the spec width: no flag, exit 0; the physical
    width is unknown, so the summary is INCOMPLETE, and --strict exits 3
  * DPI tag 720, 5040 px wide (7.0 in) -> DPI and width both checked from metadata: no flag, exit 0
  * no DPI tag, --spec-min-dpi only -> the DPI check cannot run: INCOMPLETE, --strict exits 3
  * missing image -> exit 2
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
CRITIC = HERE.parent / "scripts" / "critic_figure.py"
SPEC = ["--spec-min-dpi", "600", "--spec-width-in", "7.0"]

_fail = 0


def ck(label: str, ok: bool, detail: object = "") -> None:
    global _fail
    if ok:
        print(f"  PASS  {label}")
    else:
        print(f"  FAIL  {label} {detail}")
        _fail += 1


def run(img: Path, *extra: str) -> tuple[int, dict]:
    out = img.with_suffix(".json")
    if out.exists():
        out.unlink()
    p = subprocess.run([sys.executable, str(CRITIC), str(img), "--type", "other", "--out", str(out), *extra],
                       capture_output=True, text=True)
    return p.returncode, (json.loads(out.read_text()) if out.exists() else {})


def blank(path: Path, width: int, dpi: int | None = None) -> Path:
    im = Image.new("RGB", (width, 300), "white")
    if dpi:
        im.save(path, dpi=(dpi, dpi))
    else:
        im.save(path)
    return path


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        t = Path(td)

        # POSITIVE: low resolution with no DPI tag is flagged from width_px / spec width.
        rc, rep = run(blank(t / "low.png", 1000), *SPEC)
        ck("no DPI tag, 1000 px at 7.0 in: exit 1", rc == 1, rc)
        ck("no DPI tag, 1000 px at 7.0 in: DPI flag raised",
           any("DPI below journal spec" in f for f in rep.get("flags", [])), rep.get("flags"))
        ck("summary is not PASS", rep.get("summary") != "PASS", rep.get("summary"))

        # NEGATIVE control: enough pixels for the spec, no DPI tag -> no flag.
        rc, rep = run(blank(t / "ok_untagged.png", 4200), *SPEC)
        ck("no DPI tag, 4200 px at 7.0 in: exit 0 (no flag)", rc == 0 and rep.get("flags") == [], (rc, rep.get("flags")))
        ck("unknown physical width reported under not_run",
           any(n.startswith("width:") for n in rep.get("not_run", [])), rep.get("not_run"))
        ck("summary INCOMPLETE, not PASS", str(rep.get("summary", "")).startswith("INCOMPLETE"), rep.get("summary"))
        rc, _ = run(t / "ok_untagged.png", *SPEC, "--strict")
        ck("INCOMPLETE under --strict exits 3", rc == 3, rc)

        # NEGATIVE control: DPI-tagged, meets spec -> no flag, dimensions fully checked.
        rc, rep = run(blank(t / "ok_tagged.png", 5040, dpi=720), *SPEC)
        dims = rep.get("checks", {}).get("dimensions", {})
        ck("DPI 720 tag, 5040 px (7.0 in): exit 0 (no flag)", rc == 0 and rep.get("flags") == [], (rc, rep.get("flags")))
        ck("DPI and width both checked from metadata",
           dims.get("dpi_meets_spec") is True and dims.get("width_matches_spec") is True and "not_run" not in dims, dims)

        # A requested DPI check that cannot run is reported, never passed.
        rc, rep = run(t / "ok_untagged.png", "--spec-min-dpi", "600")
        ck("min DPI without tag or spec width: exit 0, DPI under not_run",
           rc == 0 and any(n.startswith("DPI:") for n in rep.get("not_run", [])), (rc, rep.get("not_run")))
        rc, _ = run(t / "ok_untagged.png", "--spec-min-dpi", "600", "--strict")
        ck("... and --strict exits 3", rc == 3, rc)

        rc, _ = run(t / "missing.png", *SPEC)
        ck("missing image exits 2", rc == 2, rc)

    print(f"fail={_fail}")
    print("ALL PASS" if _fail == 0 else f"FAILURES: {_fail}")
    return 1 if _fail else 0


if __name__ == "__main__":
    sys.exit(main())
