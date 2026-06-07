#!/usr/bin/env python3
"""E4 - Fresh-clone reproducibility test.

Archive a ref (release-candidate SHA pre-tag, or the v3.8.0 tag post-tag) into a
clean temp tree and run `version_dataset.py verify --strict` on all three demo
manifests. Records pass/fail, file count, wall-clock, and manual-intervention
notes. Tests the "reproducible" claim from a clean checkout, not the working
tree.

Breaks the tag circularity: --ref defaults to HEAD (use the RC SHA before
tagging; re-run against the v3.8.0 tag after tagging as a confirmation pass).

Deterministic (the verify itself is deterministic); wall-clock is recorded but
excluded from the reproducibility hash.
"""

from __future__ import annotations

import argparse
import csv
import re
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness.runlog import RunLogger  # noqa: E402
from _harness.workspace import REPO_ROOT, temp_dir, DEMOS  # noqa: E402

VD_REL = "skills/version-dataset/scripts/version_dataset.py"


def _archive(ref: str, dst: Path) -> None:
    dst.mkdir(parents=True, exist_ok=True)
    ps = subprocess.Popen(
        ["git", "-C", str(REPO_ROOT), "archive", ref], stdout=subprocess.PIPE
    )
    subprocess.run(["tar", "-x", "-C", str(dst)], stdin=ps.stdout, check=True)
    ps.stdout.close()
    ps.wait()


def _resolve(ref: str) -> str:
    return subprocess.run(
        ["git", "-C", str(REPO_ROOT), "rev-parse", ref],
        capture_output=True, text=True,
    ).stdout.strip()


def main() -> int:
    ap = argparse.ArgumentParser(description="E4 fresh-clone reproducibility")
    ap.add_argument("--ref", default="HEAD",
                    help="git ref to archive+verify (RC SHA pre-tag, v3.8.0 tag post-tag)")
    ap.add_argument("--python", default=sys.executable,
                    help="interpreter to run version_dataset with (default: current)")
    args = ap.parse_args()

    resolved = _resolve(args.ref)
    log = RunLogger.start("E4")
    rows = []
    with temp_dir("freshclone") as t:
        clone = t / "clone"
        _archive(args.ref, clone)
        vd = clone / VD_REL
        if not vd.is_file():
            print(f"ERROR: {VD_REL} absent in archived ref {args.ref}", file=sys.stderr)
            return 2
        for demo in DEMOS:
            base = clone / "demo" / demo
            manifest = base / "manifest.lock.json"
            if not manifest.is_file():
                rows.append({"demo": demo, "ref": args.ref, "ref_sha": resolved,
                             "pass": "n/a", "hash_match": "n/a", "files_checked": 0,
                             "wall_clock_s": 0.0, "manual_intervention": "manifest absent in ref"})
                continue
            t0 = time.monotonic()
            proc = subprocess.run(
                [args.python, str(vd), "verify", "--manifest", str(manifest),
                 "--base", str(base), "--strict"],
                cwd=str(clone), capture_output=True, text=True,
            )
            dt = time.monotonic() - t0
            ok = proc.returncode == 0
            m = re.search(r"(\d+) file\(s\) match", proc.stdout)
            files = int(m.group(1)) if m else 0
            rows.append({
                "demo": demo, "ref": args.ref, "ref_sha": resolved[:12],
                "pass": "yes" if ok else "no",
                "hash_match": "yes" if ok else "no",
                "files_checked": files,
                "wall_clock_s": round(dt, 3),
                "manual_intervention": "none (pandas preinstalled; verify is stdlib+pandas)",
            })

    out = log.run_dir / "metrics.csv"
    cols = ["demo", "ref", "ref_sha", "pass", "hash_match", "files_checked",
            "wall_clock_s", "manual_intervention"]
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)

    npass = sum(1 for r in rows if r["pass"] == "yes")
    print(f"ref: {args.ref} ({resolved[:12]})")
    print(f"demos verified clean: {npass}/{len(rows)}")
    for r in rows:
        print(f"  {r['demo']:22s} pass={r['pass']} files={r['files_checked']} {r['wall_clock_s']}s")

    log.add_input(REPO_ROOT / VD_REL)
    log.log_component(
        component_type="deterministic_script",
        script_path=str(Path(__file__).relative_to(REPO_ROOT)),
        command_args=["--ref", args.ref],
        expected_reproducibility="exact",
        rerun_policy="rerun against RC SHA pre-tag and against v3.8.0 tag post-tag",
        input_paths=[REPO_ROOT / VD_REL],
        output_path=out,
    )
    limitations = (
        f"Verified ref={args.ref} ({resolved[:12]}). The archive is a clean "
        "committed tree (no working-tree state). pandas was preinstalled in the "
        "running interpreter; a true cold-start would `pip install pandas` "
        "first. Pass/fail is deterministic; wall-clock varies and is excluded "
        "from the reproducibility hash."
    )
    log.finalize(metrics_path=out, limitations=limitations, repro_hash_extra=[out])
    print(f"\nwrote {out}")
    print(f"run dir: {log.run_dir}")
    return 0 if npass == len([r for r in rows if r["pass"] != "n/a"]) else 1


if __name__ == "__main__":
    sys.exit(main())
