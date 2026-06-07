#!/usr/bin/env python3
"""E8 - Claim-drift resistance.

Inject public-metadata drift (README skill badge/tagline, catalog_counts.json
SSOT) into a clean `git archive` copy of the repo, run the existing
validate_catalog_consistency.py against that copy, and record whether each drift
is caught. The real repo is never mutated; everything happens in a temp tree.

Deterministic, stdlib-only. Writes drift_matrix.csv to a run package.
"""

from __future__ import annotations

import csv
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness.runlog import RunLogger  # noqa: E402
from _harness.workspace import REPO_ROOT, temp_dir  # noqa: E402

VALIDATOR_REL = "scripts/validate_catalog_consistency.py"


def _archive_repo(dst: Path) -> None:
    """git archive HEAD | tar -x into dst (clean committed tree, no .git)."""
    dst.mkdir(parents=True, exist_ok=True)
    ps = subprocess.Popen(
        ["git", "-C", str(REPO_ROOT), "archive", "HEAD"], stdout=subprocess.PIPE
    )
    subprocess.run(["tar", "-x", "-C", str(dst)], stdin=ps.stdout, check=True)
    ps.stdout.close()
    ps.wait()


def _run_validator(repo: Path) -> int:
    return subprocess.run(
        [sys.executable, str(repo / VALIDATOR_REL)],
        cwd=str(repo), capture_output=True, text=True,
    ).returncode


# Each drift returns (applied: bool). If the target string is absent it is a
# SKIP (we never report a false "not caught" for a missing target).
def drift_badge(readme: str) -> tuple[str, bool]:
    new = re.sub(r"(img\.shields\.io/badge/Skills-)(\d+)(-)",
                 lambda m: f"{m.group(1)}{int(m.group(2)) + 1}{m.group(3)}",
                 readme, count=1)
    return new, (new != readme)


def drift_tagline(readme: str) -> tuple[str, bool]:
    new = re.sub(r"(\*\*)(\d+)( skills that actually work)",
                 lambda m: f"{m.group(1)}{int(m.group(2)) + 1}{m.group(3)}",
                 readme, count=1)
    return new, (new != readme)


def main() -> int:
    log = RunLogger.start("E8")
    rows = []
    with temp_dir("e8") as t:
        repo = t / "repo"
        _archive_repo(repo)
        readme_p = repo / "README.md"
        ssot_p = repo / "metadata" / "catalog_counts.json"
        validator_p = repo / VALIDATOR_REL
        if not validator_p.is_file():
            print("ERROR: validator not present in archived tree", file=sys.stderr)
            return 2

        orig_readme = readme_p.read_text(encoding="utf-8")
        orig_ssot = ssot_p.read_text(encoding="utf-8")

        # Baseline: clean tree must pass.
        baseline_rc = _run_validator(repo)
        rows.append({
            "drift_id": "BASELINE_clean", "layer": "-",
            "injected_change": "(none)", "validator_exit": baseline_rc,
            "caught": "n/a", "status": "PASS" if baseline_rc == 0 else "UNEXPECTED",
        })

        def restore():
            readme_p.write_text(orig_readme, encoding="utf-8")
            ssot_p.write_text(orig_ssot, encoding="utf-8")

        # Drift definitions: (id, layer, kind)
        drifts = [
            ("README_skill_badge_+1", "L3-doc", "badge"),
            ("README_skill_tagline_+1", "L3-doc", "tagline"),
            ("SSOT_skills_+1", "L2-ssot", "ssot:skills"),
            ("SSOT_reporting_guidelines_+1", "L2-ssot", "ssot:reporting_guidelines"),
        ]
        for did, layer, kind in drifts:
            restore()
            applied = True
            change = ""
            if kind == "badge":
                new, applied = drift_badge(orig_readme)
                if applied:
                    readme_p.write_text(new, encoding="utf-8")
                change = "Skills badge count +1"
            elif kind == "tagline":
                new, applied = drift_tagline(orig_readme)
                if applied:
                    readme_p.write_text(new, encoding="utf-8")
                change = "'N skills that actually work' +1"
            elif kind.startswith("ssot:"):
                key = kind.split(":", 1)[1]
                import json
                d = json.loads(orig_ssot)
                if key in d and isinstance(d[key], int):
                    d[key] = d[key] + 1
                    ssot_p.write_text(json.dumps(d, indent=2) + "\n", encoding="utf-8")
                    change = f"catalog_counts.json::{key} +1"
                else:
                    applied = False
            if not applied:
                rows.append({
                    "drift_id": did, "layer": layer, "injected_change": change or kind,
                    "validator_exit": "", "caught": "", "status": "SKIPPED_target_absent",
                })
                continue
            rc = _run_validator(repo)
            rows.append({
                "drift_id": did, "layer": layer, "injected_change": change,
                "validator_exit": rc, "caught": "yes" if rc != 0 else "no",
                "status": "OK" if rc != 0 else "MISSED",
            })
        restore()

    out = log.run_dir / "drift_matrix.csv"
    cols = ["drift_id", "layer", "injected_change", "validator_exit", "caught", "status"]
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)

    inj = [r for r in rows if r["drift_id"] != "BASELINE_clean" and r["status"] != "SKIPPED_target_absent"]
    caught = sum(1 for r in inj if r["caught"] == "yes")
    print(f"baseline validator exit: {baseline_rc} (expect 0)")
    print(f"drifts caught: {caught}/{len(inj)}")
    for r in rows:
        print(f"  {r['drift_id']:32s} exit={r['validator_exit']!s:>3} caught={r['caught']} [{r['status']}]")

    log.add_input(REPO_ROOT / VALIDATOR_REL, REPO_ROOT / "README.md",
                  REPO_ROOT / "metadata" / "catalog_counts.json")
    log.log_component(
        component_type="deterministic_script",
        script_path=str(Path(__file__).relative_to(REPO_ROOT)),
        command_args=[],
        expected_reproducibility="exact",
        rerun_policy="rerun any time; operates on a fresh git-archive temp copy, real repo untouched",
        input_paths=[REPO_ROOT / VALIDATOR_REL, REPO_ROOT / "README.md",
                     REPO_ROOT / "metadata" / "catalog_counts.json"],
        output_path=out,
    )
    limitations = (
        "Drift is injected into a git-archive copy of HEAD; the live repo is "
        "never modified. A SKIPPED_target_absent row means the drift's target "
        "string was not present in the archived README (e.g. badge format "
        "changed) and is not a validator miss."
    )
    log.finalize(metrics_path=out, limitations=limitations, repro_hash_extra=[out])
    print(f"\nwrote {out}")
    print(f"run dir: {log.run_dir}")
    # Non-zero only if a drift was MISSED (validator failed to catch it).
    return 1 if any(r["status"] == "MISSED" for r in rows) else 0


if __name__ == "__main__":
    sys.exit(main())
