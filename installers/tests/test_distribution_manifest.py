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
    # Named exclusions, mirrored deliberately from gen_distribution_manifest.EXCLUDE_RELPATHS.
    #
    # `skills/MAINTENANCE.md` is a maintainer document at the skills/ root. install.py places
    # skill DIRECTORIES, so it was inventoried and never installed — the ZIP and a local install
    # disagreed and nothing compared them. Narrowing the payload is a scope change, so per the
    # note below it is made in BOTH places on purpose; this test failing on the one-sided edit is
    # the mechanism working, not an obstacle to route around by importing the generator.
    exclrel = {"skills/MAINTENANCE.md"}
    payload: set[str] = set()
    # Deliberately re-derived here rather than imported: this is the independent oracle that
    # catches the payload scope widening by accident. Widening it on purpose means editing
    # this tuple too. LICENSE + THIRD-PARTY-NOTICES.md ship so the MIT notice and the
    # CC BY-NC terms travel with every classroom copy.
    for root in ("README_FIRST.md", "LICENSE", "THIRD-PARTY-NOTICES.md", "installers", "skills"):
        p = ROOT / root
        if p.is_file():
            payload.add(p.relative_to(ROOT).as_posix())
        else:
            for f in p.rglob("*"):
                rel = f.relative_to(ROOT)
                if (f.is_file() and not (set(rel.parts) & excl)
                        and f.name not in exclf and rel.as_posix() not in exclrel
                        and not f.name.endswith(".pyc")):
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

    # regression: the inventory must describe a payload install.py can actually reproduce.
    #
    # install.py places skill DIRECTORIES — `p.is_dir() and (p / "SKILL.md").exists()`. Anything
    # else under skills/ is inventoried but never installed, so the ZIP and a local install
    # diverge and nothing compares them. `skills/MAINTENANCE.md` sat that way: a maintainer
    # document shipped to every classroom, absent from every install. Assert the two agree by
    # construction rather than by anyone remembering to look.
    skills_root = ROOT / "skills"
    installable = {p.name for p in skills_root.iterdir() if p.is_dir() and (p / "SKILL.md").is_file()}
    orphans = sorted(
        e for e in inv
        if e.startswith("skills/")
        and (len(e.split("/")) < 3 or e.split("/")[1] not in installable)
    )
    check(f"every skills/ inventory entry lands in an installed skill dir (orphans: {orphans})",
          not orphans)
    # negative control: the rule must be about installability, not about the count. A real skill
    # file has to still be in the inventory, or "0 orphans" would also be true of an empty one.
    sample = next((e for e in sorted(inv) if e.startswith("skills/") and e.endswith("/SKILL.md")), None)
    check("a real skill's SKILL.md is still inventoried", sample is not None)

    print("----")
    print(f"test_distribution_manifest: {PASS} passed, {FAIL} failed")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
