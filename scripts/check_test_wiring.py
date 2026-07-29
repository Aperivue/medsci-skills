#!/usr/bin/env python3
"""A test CI never runs is a test that never runs — the third sibling of the reachability gates.

`check_detector_reachability.py` asks whether a *skill* calls a detector.
`check_script_reachability.py` asks whether a *skill* calls a script.
Both docstrings say the same thing out loud:

    "A test, a challenge card, or a CI step does NOT make a script reachable."

That sentence closes one direction and leaves the other one open, and nothing else was watching it.
The open direction is this: a challenge card can sit on disk, be listed in its skill's
`validation_commands`, be counted in the distribution manifest, be announced in the CHANGELOG — and
never be named in a workflow. It is green because it is never run. On 2026-07-25, with the two
reachability gates in place and 202 `run:` steps hand-listed in `validate.yml`, twelve test assets
were in exactly that state, six of them declared in a `skill.yml` as validation commands. Four more
had been in it until PR #412 wired them by hand, one at a time, after a manual sweep found them.

The manual sweep is the bug. A hand-maintained list of "tests CI should run" has no gate that
catches an omission, so the omission is invisible for as long as nobody happens to look.

A test asset is WIRED if:
  * a `run:` step in any `.github/workflows/*.yml` names its path, or
  * a NON-TEST file that a `run:` step names contains its path (one hop — `validate_skills.sh` runs
    `tests/test_precedent_hashing.sh`, and that counts).

The hop deliberately excludes test assets themselves, and that exclusion is load-bearing rather than
tidy: the first draft let any wired file vouch for a path, and this gate's own self-test — which
names a challenge in a shell variable in order to *delete its step* — thereby certified that
challenge as wired. The gate passed its own regression case by reading its own source. A test that
mentions another test is not running it, which is the sibling gates' doctrine one category over.

Being declared in `skill.yml` does NOT make it wired: `validation_commands` is documentation of how
to run a thing, and CI does not read it. That gap is what this gate exists to close.

Exemptions live in EXEMPT below and each one carries a reason. There is no `--strict`: a violation
exits 1 always, because a gate that reports a failure while exiting 0 is the failure mode this
repository keeps re-learning.

Usage:
    check_test_wiring.py [--root DIR] [--json] [--quiet]

Needs PyYAML (maintainer tool, same as run_ci_mirror.py).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Where test assets live and what they are called.
#
# The last glob is a naming backstop. This gate reads a test's NAME to decide whether it is
# a test, so a real regression test that is not called `test_*` or `verify.sh` is invisible
# to it — and a gate whose job is finding unrun tests must not have a way to be blind. That
# is not hypothetical: `skills/manage-refs/tests/fixtures/pre_submission_gate/run.sh` is the
# end-to-end regression for the master pre-submission chain, and it sat unwired and FAILING
# for two months (2026-05-31 -> 2026-07-29) because it is named `run.sh`. Anything under a
# `tests/` directory is now claimed as a test regardless of its name.
ASSET_GLOBS = (
    "skills/**/verify.sh",
    "skills/**/test_*.py",
    "skills/**/test_*.sh",
    "tests/test_*.py",
    "tests/test_*.sh",
    "skills/**/tests/**/*.sh",
)

# path -> reason. A test that CI genuinely must not run needs a stated reason, not silence.
EXEMPT: dict[str, str] = {
    "skills/manage-refs/tests/fixtures/pre_submission_gate/run.sh": (
        "End-to-end chain test whose verify_refs stage queries live PubMed/CrossRef. Wiring it "
        "into validate.yml would make a green build depend on a third-party API's availability "
        "and rate limits, so CI would go red for reasons no contributor could act on. Run it by "
        "hand before any release that touches the manage-refs chain; it exits 77 when the "
        "network is unreachable. The offline-safe half of its coverage is "
        "skills/verify-refs/tests/test_bibtex_et_al.sh, which IS wired."
    ),
}


def _iter_run_commands(root: Path) -> list[str]:
    try:
        import yaml  # noqa: PLC0415
    except ModuleNotFoundError:
        sys.stderr.write(
            "check_test_wiring needs PyYAML (pip install pyyaml). It is a maintainer tool.\n"
        )
        raise SystemExit(1)

    wf_dir = root / ".github" / "workflows"
    cmds: list[str] = []
    for wf in sorted(wf_dir.glob("*.yml")) + sorted(wf_dir.glob("*.yaml")):
        doc = yaml.safe_load(wf.read_text(encoding="utf-8")) or {}
        for job in (doc.get("jobs") or {}).values():
            for step in (job or {}).get("steps") or []:
                run = (step or {}).get("run")
                if run:
                    cmds.append(run)
    return cmds


def _referenced_repo_files(root: Path, cmds: list[str]) -> list[Path]:
    """Repo files named by a run: command — the one-hop frontier."""
    out: list[Path] = []
    for cmd in cmds:
        for token in cmd.replace("&&", " ").replace("|", " ").replace(";", " ").split():
            token = token.strip("\"'()")
            if "/" not in token or token.startswith("-"):
                continue
            candidate = root / token
            if candidate.is_file():
                out.append(candidate)
    return out


def collect(root: Path = ROOT) -> dict:
    assets = sorted(
        {p.relative_to(root).as_posix() for glob in ASSET_GLOBS for p in root.glob(glob)}
    )
    cmds = _iter_run_commands(root)
    joined = "\n".join(cmds)

    asset_set = set(assets)
    self_path = Path(__file__).resolve()
    hop_text = []
    for f in _referenced_repo_files(root, cmds):
        if f.relative_to(root).as_posix() in asset_set:
            continue  # a test does not wire another test — see the docstring
        if f.resolve() == self_path:
            # This gate must not read ITSELF. CI runs it, so it is a referenced file, so its
            # own source lands in the one-hop text — and then writing a test's path anywhere
            # in here, including inside an EXEMPT reason or a comment, marks that test wired.
            # Observed: adding the sentence "the offline-safe half is <path>, which IS wired"
            # to an exemption reason turned a genuinely unwired test green. EXEMPT is the one
            # sanctioned way to excuse a test; prose must not be a second, silent one.
            continue
        try:
            hop_text.append(f.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            continue
    hop_joined = "\n".join(hop_text)

    unwired = []
    for a in assets:
        if a in EXEMPT or a in joined:
            continue
        if a in hop_joined:  # one hop: a wired script runs it
            continue
        unwired.append(a)

    return {
        "detector": "check_test_wiring",
        "verdict": "TEST_NOT_WIRED" if unwired else "OK",
        "assets": len(assets),
        "exempt": len(EXEMPT),
        "unwired": unwired,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", type=Path, default=ROOT,
                    help="repo root to audit (default: this checkout) — the self-test points it "
                         "at a synthetic tree")
    ap.add_argument("--json", action="store_true", help="emit the report as JSON")
    ap.add_argument("--quiet", action="store_true", help="print nothing when clean")
    a = ap.parse_args()

    report = collect(a.root.resolve())
    if a.json:
        print(json.dumps(report, indent=2))
    elif report["unwired"]:
        print(f"TEST_NOT_WIRED: {len(report['unwired'])} test asset(s) no workflow runs.")
        print("Each of these is green because nothing executes it:\n")
        for u in report["unwired"]:
            print(f"  {u}")
        print(
            "\nWire each one as a step in .github/workflows/validate.yml, or add it to EXEMPT in "
            f"{Path(__file__).name} with a reason.\n"
            "Declaring it in skill.yml validation_commands is not wiring — CI does not read that file."
        )
    elif not a.quiet:
        print(f"OK: all {report['assets']} test assets are run by a workflow "
              f"({report['exempt']} exempt).")

    return 1 if report["unwired"] else 0


if __name__ == "__main__":
    sys.exit(main())
