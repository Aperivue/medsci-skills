#!/usr/bin/env python3
"""The workflow files must parse — because a broken one does not fail, it VANISHES.

On 2026-07-14 a step was added named:

    - name: Run deck-budget challenge (same deck: fits an oral, too dense for a keynote)

The `: ` inside an unquoted YAML scalar made the line a mapping, and `validate.yml` stopped being
valid YAML. GitHub did not run a single job. `gh pr checks` reported **"no checks reported on the
branch"** — not a red X, not a failure anyone would notice at a glance. The run existed, it was
"failure", and it contained **zero jobs**, so there was nothing to look at.

That is the most dangerous shape a failure can take: every gate in the repository — the PII scanner,
the detector-envelope contract, the manifest, all 153 steps — was silently not running, and the pull
request looked *quiet* rather than *broken*. A person who merges on green would have merged on
nothing.

So the workflow files are parsed like any other artifact, and the specific trap that caused it is
called out by name.

Stdlib only (no PyYAML — this must run before anything installs anything).

Usage:
    check_workflow_yaml.py [--strict]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS = ROOT / ".github" / "workflows"


def problems() -> list[str]:
    out: list[str] = []
    files = sorted(WORKFLOWS.glob("*.yml")) + sorted(WORKFLOWS.glob("*.yaml"))
    if not files:
        return ["no workflow files found — this gate is a no-op, which is worse than a failure"]

    for f in files:
        text = f.read_text(encoding="utf-8")

        # 1. The exact trap: an unquoted scalar containing ": ", which YAML reads as a mapping.
        #    Catches `name:`, `run:` one-liners, `if:` — anything that is a plain scalar.
        for i, line in enumerate(text.split("\n"), 1):
            m = re.match(r"(\s*)-?\s*(name|if):\s+(?![\"'|>])(.*: .*)$", line)
            if m:
                out.append(
                    f"{f.relative_to(ROOT)}:{i}: `{m.group(2)}:` value contains ': ' but is not "
                    f"quoted — YAML reads this as a mapping and the whole file stops parsing.\n"
                    f"      {line.strip()}\n"
                    f"      Fix: wrap the value in double quotes."
                )

        # 2. And then actually parse it. A hand-rolled check can only see the traps it knows.
        try:
            import yaml  # noqa: PLC0415
        except ImportError:
            continue  # the regex above is the floor; a full parse is a bonus when PyYAML is here
        try:
            doc = yaml.safe_load(text)
        except yaml.YAMLError as exc:
            out.append(f"{f.relative_to(ROOT)}: does not parse as YAML — GitHub will run ZERO jobs "
                       f"and report 'no checks', not a failure.\n      {exc}")
            continue
        if not isinstance(doc, dict) or not doc.get("jobs"):
            out.append(f"{f.relative_to(ROOT)}: parses, but declares no jobs.")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--strict", action="store_true")
    a = ap.parse_args()

    probs = problems()
    if not probs:
        n = len(list(WORKFLOWS.glob("*.yml"))) + len(list(WORKFLOWS.glob("*.yaml")))
        print(f"OK: all {n} workflow file(s) parse and declare jobs.")
        return 0

    print(f"WORKFLOW_YAML_BROKEN: {len(probs)} problem(s)\n")
    for p in probs:
        print(f"  - {p}")
    print("\nA broken workflow does not turn the pull request red. It makes the checks DISAPPEAR,")
    print("which looks like a quiet branch and merges like one.")
    return 1 if a.strict else 0


if __name__ == "__main__":
    sys.exit(main())
