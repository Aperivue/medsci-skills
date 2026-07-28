#!/usr/bin/env python3
"""Run the CI `validate` job's gates locally, in order — the mirror that cannot drift.

The pre-push "CI mirror" was described in prose (CONTRIBUTING, a global rule) as a short
list of commands. `.github/workflows/validate.yml` actually has ~170 `run:` steps. A
hand-copied list drifts silently and is only caught by a red CI *after* a push — the exact
failure this repo keeps hitting (a gate added to the workflow, or a `--strict` flag, that
the prose list never learned about; a gate that prints its violation but exits 0, so a
`cmd >/dev/null && echo OK` reads a real failure as a pass).

This parses validate.yml, extracts the `validate` job's `run:` steps IN ORDER, and executes
each one exactly as CI does (`bash -e -c`, from the repo root). The list can therefore never
drift from CI, and each gate's flags (`--strict`, `--check`) come along for free. Run it
before every push; if it is green, CI's `validate` job will be too (modulo the OS-specific
`foundation-os` job, which installs nothing this repo builds).

SKIPPED (not gates):
  - `uses:` steps (actions/checkout, setup-python, setup-node) — no local equivalent.
  - dependency-install steps whose command starts with pip / apt-get / brew / npm / sudo —
    assumed already present locally. A gate that then needs a missing tool (exiftool,
    poppler) FAILS loudly here, which is the honest signal, not a silent skip.

Usage:
    scripts/run_ci_mirror.py [--fail-fast] [--list] [--only SUBSTR]
Exit: 0 = every gate passed, 1 = one or more failed (or PyYAML is missing).
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = ROOT / ".github" / "workflows" / "validate.yml"

# A step whose command STARTS with one of these is environment setup, not a gate.
_SETUP_PREFIXES = ("pip ", "pip3 ", "python -m pip", "python3 -m pip",
                   "apt-get", "sudo", "brew ", "npm ci", "npm install", "npm i ")


def _is_setup(run: str) -> bool:
    first = run.strip().splitlines()[0].strip() if run.strip() else ""
    return any(first.startswith(p) for p in _SETUP_PREFIXES)


def gate_steps() -> list[tuple[str, str]]:
    try:
        import yaml  # noqa: PLC0415
    except ModuleNotFoundError:
        sys.stderr.write("run_ci_mirror needs PyYAML (pip install pyyaml). It is a maintainer tool.\n")
        raise SystemExit(1)
    doc = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    steps = (doc.get("jobs", {}).get("validate", {}) or {}).get("steps", []) or []
    out: list[tuple[str, str]] = []
    for s in steps:
        run = s.get("run")
        if not run or _is_setup(run):
            continue
        out.append((s.get("name", "(unnamed)"), run))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--fail-fast", action="store_true", help="stop at the first failing gate")
    ap.add_argument("--list", action="store_true", help="list the gate steps in order and exit")
    ap.add_argument("--only", metavar="SUBSTR", help="run only gates whose name contains SUBSTR")
    a = ap.parse_args()

    steps = gate_steps()
    if a.only:
        steps = [(n, r) for (n, r) in steps if a.only.lower() in n.lower()]
    if a.list:
        for n, _ in steps:
            print(n)
        print(f"\n{len(steps)} gate step(s) mirrored from validate.yml.")
        return 0

    fails: list[str] = []
    for i, (name, run) in enumerate(steps, 1):
        p = subprocess.run(["bash", "-e", "-c", run], cwd=ROOT, capture_output=True, text=True)
        ok = p.returncode == 0
        print(f"{'PASS' if ok else 'FAIL'} [{i:>3}/{len(steps)}] {name[:82]}", flush=True)
        if not ok:
            fails.append(name)
            tail = (p.stdout or "")[-1600:] + (p.stderr or "")[-1600:]
            sys.stdout.write(tail.rstrip() + "\n")
            if a.fail_fast:
                break

    if fails:
        print(f"\n{len(steps) - len(fails)}/{len(steps)} gates passed; FAILED ({len(fails)}): "
              + "; ".join(fails))
        return 1
    print(f"\nOK: all {len(steps)} validate-job gates passed — CI's validate job will be green.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
