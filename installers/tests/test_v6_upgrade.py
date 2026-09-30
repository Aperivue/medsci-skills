#!/usr/bin/env python3
"""v5 -> v6 upgrade: renamed skills are replaced by their alias stubs, never lost.

v6.0 merged twelve imaging skills into seven and kept the eight retired names as SKILL.md-only alias
stubs until v7. The installer prunes a skill that the new release no longer owns (after backing up
a user-modified copy). Because every retired name still ships — as a stub — nothing is pruned in
v6; each old directory is *replaced*. This test drives the real installer end to end to prove it:

  1. a synthetic v5-style install into a temp HOME — the twelve v5 imaging skills as full skills
     (SKILL.md + scripts), installed by this checkout's own installer from a v5-shaped source tree;
  2. the user edits one of the retired skills in place (a clinician adapting it to their department);
  3. the candidate tree (this repository) is installed into the same HOME with installers/install.py.

Asserted: the three new skills are installed; every retired name is now the stub the candidate ships
(its scripts are gone, not merged); the user's modified copy is in the permanent backup, byte for
byte; nothing was pruned; and a second run is idempotent (no new backup, identical tree and manifest).

Deterministic, network-free, touches only a temp HOME. Run: python3 installers/tests/test_v6_upgrade.py
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
INSTALL = REPO / "installers" / "install.py"

NEW = ["model-selection", "imaging-data", "model-assessment"]
RETIRED = {
    "architecture-zoo": "model-selection", "model-sourcing": "model-selection",
    "profile-imaging": "imaging-data", "preprocess-imaging": "imaging-data",
    "model-validation": "model-assessment", "model-evaluation": "model-assessment",
    "uncertainty-imaging": "model-assessment", "explainability": "model-assessment",
}
UNCHANGED = ["model-scaffold", "model-card", "radiomics-ml", "mllm-eval"]
EDITED = "model-evaluation"
USER_LINE = "\n<!-- local edit: our department reports NSD at 2 mm, not 1 mm -->\n"

PASS = 0
FAIL = 0


def check(label: str, cond: bool) -> None:
    global PASS, FAIL
    print(f"  {'PASS' if cond else 'FAIL'}  {label}")
    if cond:
        PASS += 1
    else:
        FAIL += 1


def tree(root: Path) -> dict[str, bytes]:
    return {str(p.relative_to(root)): p.read_bytes()
            for p in sorted(root.rglob("*")) if p.is_file() and "__pycache__" not in p.parts}


def make_v5_repo(root: Path) -> None:
    """A v5-shaped source checkout: this repo's installers, and the twelve v5 imaging skills as
    full skills (SKILL.md + a script), which is what a v5 user has on disk."""
    shutil.copytree(REPO / "installers", root / "installers",
                    ignore=shutil.ignore_patterns("tests", "__pycache__"))
    for name in list(RETIRED) + UNCHANGED:
        d = root / "skills" / name
        (d / "scripts").mkdir(parents=True)
        (d / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: v5 {name}.\ntriggers: {name}\ntools: Read\nmodel: inherit\n---\n\n"
            f"# {name} (v5)\n", encoding="utf-8")
        (d / "scripts" / "check_v5.py").write_text("print('v5')\n", encoding="utf-8")
    (root / "metadata").mkdir()
    (root / "metadata" / "distribution_manifest.json").write_text(json.dumps(
        {"schema_version": 1, "version": "5.29.0", "owned_skills": sorted(list(RETIRED) + UNCHANGED)}
    ) + "\n", encoding="utf-8")


def run_install(installer: Path, home: Path) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env.pop("MEDSCI_HOME", None)  # default state home under the temp HOME, as a real user has
    env.update({"HOME": str(home), "USERPROFILE": str(home), "PYTHONDONTWRITEBYTECODE": "1"})
    return subprocess.run([sys.executable, str(installer), "--target", "claude"],
                          env=env, capture_output=True, text=True, timeout=600)


def backups(home: Path) -> list[Path]:
    root = home / ".medsci-skills" / "backups"
    return sorted(p for p in root.glob("*/claude/*") if p.is_dir()) if root.is_dir() else []


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="medsci-v6-upgrade-") as tmp:
        base = Path(tmp)
        home = base / "home"
        home.mkdir()
        dest = home / ".claude" / "skills"
        manifest = home / ".medsci-skills" / "targets" / "claude" / "installed-manifest.json"

        # 1. v5 install
        v5 = base / "v5"
        make_v5_repo(v5)
        r = run_install(v5 / "installers" / "install.py", home)
        check("v5 install exits 0", r.returncode == 0)
        check("v5 install placed the twelve imaging skills",
              all((dest / n / "scripts" / "check_v5.py").is_file() for n in list(RETIRED) + UNCHANGED))

        # 2. the user edits a retired skill in place
        edited = dest / EDITED / "SKILL.md"
        user_text = edited.read_text(encoding="utf-8") + USER_LINE
        edited.write_text(user_text, encoding="utf-8")

        # 3. the candidate (this checkout) into the same HOME
        r = run_install(INSTALL, home)
        check("v6 install exits 0", r.returncode == 0)
        if r.returncode != 0:
            print(r.stdout[-3000:], r.stderr[-3000:], sep="\n")

        for n in NEW:
            check(f"new skill installed: {n}",
                  (dest / n / "SKILL.md").is_file()
                  and tree(dest / n) == tree(REPO / "skills" / n))
        for old, new in sorted(RETIRED.items()):
            d = dest / old
            check(f"{old}: replaced by the shipped stub (-> /{new}), v5 scripts gone",
                  tree(d) == tree(REPO / "skills" / old) and list(tree(d)) == ["SKILL.md"]
                  and f"Renamed to /{new} in v6" in (d / "SKILL.md").read_text(encoding="utf-8"))
        for n in UNCHANGED:
            check(f"unchanged skill replaced by the v6 copy: {n}", tree(dest / n) == tree(REPO / "skills" / n))

        b = backups(home)
        saved = [p for p in b if p.name == EDITED]
        check("the user-modified retired skill was backed up, not lost",
              len(saved) == 1 and (saved[0] / "SKILL.md").read_text(encoding="utf-8") == user_text
              and (saved[0] / "scripts" / "check_v5.py").is_file())
        check("only the modified skill was backed up", [p.name for p in b] == [EDITED])

        owned = json.loads(manifest.read_text(encoding="utf-8"))["skills"]
        check("nothing pruned: every v5 name is still owned",
              set(RETIRED) | set(UNCHANGED) <= set(owned))
        shipped = sorted(p.name for p in (REPO / "skills").iterdir() if (p / "SKILL.md").is_file())
        check("installed set == the candidate's skills", sorted(owned) == shipped)

        # 4. idempotent re-run
        before_tree, before_manifest, before_backups = tree(dest), manifest.read_text(encoding="utf-8"), backups(home)
        r = run_install(INSTALL, home)
        check("second v6 install exits 0", r.returncode == 0)
        check("second run: installed tree unchanged", tree(dest) == before_tree)
        check("second run: manifest unchanged", manifest.read_text(encoding="utf-8") == before_manifest)
        check("second run: no new backup", backups(home) == before_backups)
        check("no transaction left behind", not (dest / ".medsci-txn").exists())

    print(f"\ntest_v6_upgrade: {PASS} passed, {FAIL} failed")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
