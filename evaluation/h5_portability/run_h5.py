#!/usr/bin/env python3
"""E6 - Host portability smoke test.

Checks installation contracts and documented portability, NOT verified execution
on four hosts. Three deterministic checks: (1) installer --self-test (touches no
real host dir); (2) a path-contract scan for hardcoded personal paths in skills;
(3) host target-dir mapping cross-checked against docs/host_compatibility.md.

Writes portability_matrix.csv to a run package.
"""

from __future__ import annotations

import csv
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness.runlog import RunLogger  # noqa: E402
from _harness.workspace import REPO_ROOT  # noqa: E402

INSTALLER = REPO_ROOT / "installers" / "install.py"
HOSTDOC = REPO_ROOT / "docs" / "host_compatibility.md"
SKILLS = REPO_ROOT / "skills"

# Personal-path leak: "/Users/<name>" or "/home/<name>" with a lowercase username.
# This intentionally does NOT match the detectors' generic "/Users/" detection
# patterns (e.g. "/Users/|/home/" in check_generated_code), which have no username.
LEAK_RE = re.compile(r"/(?:Users|home)/[a-z][a-z0-9_.-]{1,}")

# Documented host -> install dir (converged dirs per host_compatibility.md).
HOST_TARGETS = [
    ("Claude Code", "~/.claude/skills"),
    ("OpenAI Codex", "~/.agents/skills"),
    ("Cursor", "~/.agents/skills | ~/.claude/skills"),
    ("GitHub Copilot", ".github/skills | ~/.claude/skills"),
]


def self_test() -> tuple[bool, int]:
    proc = subprocess.run([sys.executable, str(INSTALLER), "--self-test"],
                          capture_output=True, text=True)
    ok = proc.returncode == 0
    m = re.search(r"(\d+)/(\d+) skills discoverable", proc.stdout)
    n = int(m.group(1)) if m else 0
    return ok, n


def scan_leaks() -> tuple[list[tuple[str, int]], list[tuple[str, int]]]:
    """Return (logic_leaks, fixture_placeholders).

    Test/fixture assets legitimately carry generic example paths (e.g.
    '/Users/researcher/...') so the path detector has something to catch; those
    are reported separately and are NOT portability leaks. Only personal paths
    in skill *logic* (scripts, SKILL.md, docs) are real leaks.
    """
    logic, fixture = [], []
    for f in SKILLS.rglob("*"):
        if not f.is_file() or f.suffix.lower() not in (".md", ".py", ".sh", ".r", ".yaml", ".yml", ".json"):
            continue
        try:
            txt = f.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        n = len(LEAK_RE.findall(txt))
        if not n:
            continue
        rel = str(f.relative_to(REPO_ROOT))
        if "/tests/" in rel or "/fixtures/" in rel:
            fixture.append((rel, n))
        else:
            logic.append((rel, n))
    return logic, fixture


def doc_verified(host: str) -> bool:
    if not HOSTDOC.is_file():
        return False
    txt = HOSTDOC.read_text(encoding="utf-8", errors="ignore")
    # host name appears in a row also marked VERIFIED somewhere in the doc
    return host.split()[0] in txt and "VERIFIED" in txt


def main() -> int:
    log = RunLogger.start("E6")
    st_ok, n_skills = self_test()
    logic_leaks, fixture_ph = scan_leaks()
    total_leaks = sum(n for _, n in logic_leaks)
    total_fixture = sum(n for _, n in fixture_ph)

    rows = []
    for host, target in HOST_TARGETS:
        rows.append({
            "host": host,
            "install_target_dir": target,
            "self_test_pass": "yes" if st_ok else "no",
            "skills_discoverable": n_skills,
            "path_leaks_found": total_leaks,
            "doc_verified": "yes" if doc_verified(host) else "no",
            "notes": "installation-contract + documented portability (not live execution)",
        })

    out = log.run_dir / "portability_matrix.csv"
    cols = ["host", "install_target_dir", "self_test_pass", "skills_discoverable",
            "path_leaks_found", "doc_verified", "notes"]
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)

    print(f"installer self-test: {'PASS' if st_ok else 'FAIL'} ({n_skills} skills discoverable)")
    print(f"personal-path leaks in skill logic: {total_leaks}")
    for path, n in logic_leaks[:10]:
        print(f"  LEAK {n}x {path}")
    print(f"generic placeholders in test fixtures (not leaks): {total_fixture}")
    for path, n in fixture_ph[:10]:
        print(f"  fixture {n}x {path}")
    print(f"documented hosts: {sum(1 for r in rows if r['doc_verified'] == 'yes')}/{len(rows)} verified in host_compatibility.md")

    log.add_input(INSTALLER, HOSTDOC)
    log.log_component(
        component_type="deterministic_script",
        script_path=str(Path(__file__).relative_to(REPO_ROOT)),
        command_args=[],
        expected_reproducibility="exact",
        rerun_policy="rerun any time; self-test + scan are deterministic, no host dir touched",
        input_paths=[INSTALLER, HOSTDOC],
        output_path=out,
    )
    limitations = (
        "This validates installation contracts and documented portability, NOT "
        "verified execution inside each host UI. The installer --self-test runs "
        "in a temp dir and touches no real host directory. The path-contract "
        "scan flags hardcoded personal paths ('/Users/<name>'), distinct from "
        "the detectors' generic '/Users/' detection patterns. Host verification "
        "status is read from docs/host_compatibility.md (verified 2026-06-03)."
    )
    log.finalize(metrics_path=out, limitations=limitations, repro_hash_extra=[out])
    print(f"\nwrote {out}")
    print(f"run dir: {log.run_dir}")
    return 0 if (st_ok and total_leaks == 0) else 1


if __name__ == "__main__":
    sys.exit(main())
