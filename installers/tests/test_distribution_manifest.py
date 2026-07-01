#!/usr/bin/env python3
"""Tests for the distribution manifests + version consistency + profile/scope pinning.

Deterministic, network-free. Asserts:
  * gen_distribution_manifest.py --check passes on the committed files (in sync + deterministic),
  * version consistency (CITATION == package.json == distribution_manifest),
  * the distribution_files.json inventory exactly equals the classroom ZIP payload (the
    scope is the common install payload, with tests/ excluded),
  * channel-difference guard: npm-only extras (bin/, package.json) are NOT in the inventory,
    so a classroom ZIP missing them is never misread as "missing".
Run: python3 installers/tests/test_distribution_manifest.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PASS = 0
FAIL = 0


def check(label: str, cond: bool) -> None:
    global PASS, FAIL
    print(f"  {'PASS' if cond else 'FAIL'}  {label}")
    if cond:
        PASS += 1
    else:
        FAIL += 1


def run(*args: str) -> int:
    return subprocess.run([sys.executable, *args], cwd=ROOT,
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode


def classroom_payload() -> set[str]:
    excl = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", "node_modules", ".git", "tests", ".logs"}
    exclf = {".DS_Store"}
    payload: set[str] = set()
    for root in ("README_FIRST.md", "installers", "skills"):
        p = ROOT / root
        if p.is_file():
            payload.add(p.relative_to(ROOT).as_posix())
        else:
            for f in p.rglob("*"):
                rel = f.relative_to(ROOT)
                if (f.is_file() and not (set(rel.parts) & excl)
                        and f.name not in exclf and not f.name.endswith(".pyc")):
                    payload.add(rel.as_posix())
    return payload


def main() -> int:
    check("gen_distribution_manifest.py --check passes (in sync + deterministic)",
          run("scripts/gen_distribution_manifest.py", "--check") == 0)
    check("check_version_consistency.py passes",
          run("scripts/check_version_consistency.py") == 0)

    inv = {e["path"] for e in json.loads((ROOT / "metadata" / "distribution_files.json").read_text())["files"]}
    payload = classroom_payload()
    check("distribution_files.json == classroom payload (scope pinned)", inv == payload)

    # channel guard: npm-only files must NOT be in the inventory.
    for npm_only in ("bin/medsci-skills.js", "package.json", "metadata/skills_catalog.json"):
        check(f"npm-only '{npm_only}' is not in the inventory", npm_only not in inv)
    # the inventory must NOT list itself or the manifest (self-reference guard)
    check("inventory excludes the two metadata manifests",
          "metadata/distribution_files.json" not in inv and "metadata/distribution_manifest.json" not in inv)
    # the transactional installer module must be in the payload (install.py imports it)
    check("installers/medsci_txn.py is in the inventory", "installers/medsci_txn.py" in inv)

    # regression (durable fix): gitignored installer logs under installers/.logs/ are
    # excluded from the inventory, so running install.py locally never drifts the manifest.
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "gdm_under_test", ROOT / "scripts" / "gen_distribution_manifest.py")
    gdm = importlib.util.module_from_spec(spec)
    sys.modules["gdm_under_test"] = gdm
    spec.loader.exec_module(gdm)
    log_name = "20260101-000000-medsci-skills-install-log.txt"
    check("installer .logs/ path is excluded from the inventory",
          gdm._included(f"installers/.logs/{log_name}", log_name) is False)
    check("a normal installer file is still included",
          gdm._included("installers/install.py", "install.py") is True)

    print("----")
    print(f"test_distribution_manifest: {PASS} passed, {FAIL} failed")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
