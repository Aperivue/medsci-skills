#!/usr/bin/env python3
"""E7 - Gate coverage inventory.

For each deterministic detector (same glob the catalog validator uses), record
which supporting assets ship with it: a synthetic fixture, a regression test, a
demo QC output, a manuscript-facing QC artifact contract (--out), and a
doc/skill reference. This is a *coverage inventory*, not a claim that every
detector has every asset; gaps are reported honestly and become a backlog.

Deterministic, stdlib-only. Writes coverage_matrix.csv to a run package.
"""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import hashing  # noqa: E402
from _harness.runlog import RunLogger  # noqa: E402
from _harness.workspace import REPO_ROOT  # noqa: E402

SKILLS = REPO_ROOT / "skills"
DEMOS = REPO_ROOT / "demo"
DETECTOR_GLOBS = ("check_*.py", "detect_*.py", "derive_*.py", "verify_refs.py")


def detector_scripts() -> list[Path]:
    seen: dict[str, Path] = {}
    for g in DETECTOR_GLOBS:
        for p in SKILLS.glob(f"*/scripts/{g}"):
            seen[str(p)] = p
    return [seen[k] for k in sorted(seen)]


def _core(stem: str) -> str:
    for pre in ("check_", "detect_", "derive_"):
        if stem.startswith(pre):
            stem = stem[len(pre):]
            break
    return stem.removesuffix("_audit")


def _tokens(core: str) -> set[str]:
    stop = {"check", "audit", "json", "py"}
    return {t for t in core.split("_") if len(t) > 2 and t not in stop}


def skill_of(script: Path) -> Path:
    # skills/<skill>/scripts/<file>.py
    return script.parents[1]


def has_fixture(skill: Path, core: str, tokens: set[str]) -> bool:
    for base in (skill / "tests", skill / "tests" / "fixtures"):
        if not base.is_dir():
            continue
        for f in base.rglob("*"):
            if not f.is_file():
                continue
            name = f.name.lower()
            if core in name or any(t in name for t in tokens):
                return True
    return False


def has_regression_test(skill: Path, script_name: str, core: str) -> bool:
    tdir = skill / "tests"
    if not tdir.is_dir():
        return False
    for f in tdir.rglob("test_*"):
        if not f.is_file():
            continue
        try:
            txt = f.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if script_name in txt or core in f.name.lower():
            return True
    return False


def emits_qc_artifact(script: Path) -> bool:
    txt = script.read_text(encoding="utf-8", errors="ignore")
    return "--out" in txt or "reference_audit.json" in txt


def demo_uses_it(core: str, tokens: set[str], script_name: str) -> bool:
    for qc in DEMOS.glob("*/qc/*"):
        name = qc.name.lower()
        if qc.suffix in (".json", ".md"):
            if core in name or any(t in name for t in tokens):
                return True
    # mentioned in the per-demo detector findings / pipeline log
    for log in DEMOS.glob("*/qc/_*.md"):
        try:
            t = log.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if script_name in t or core in t:
            return True
    return False


def doc_reference(skill: Path, script_name: str, core: str) -> bool:
    skillmd = skill / "SKILL.md"
    if skillmd.is_file():
        t = skillmd.read_text(encoding="utf-8", errors="ignore")
        if script_name in t or core in t:
            return True
    for doc in (REPO_ROOT / "docs").glob("*.md") if (REPO_ROOT / "docs").is_dir() else []:
        t = doc.read_text(encoding="utf-8", errors="ignore")
        if script_name in t:
            return True
    return False


def main() -> int:
    log = RunLogger.start("E7")
    scripts = detector_scripts()
    rows = []
    for sp in scripts:
        stem = sp.stem
        core = _core(stem)
        toks = _tokens(core)
        skill = skill_of(sp)
        rows.append({
            "detector": stem,
            "skill": skill.name,
            "script_exists": "yes",
            "fixture_exists": "yes" if has_fixture(skill, core, toks) else "no",
            "regression_test_exists": "yes" if has_regression_test(skill, sp.name, core) else "no",
            "demo_output_uses_it": "yes" if demo_uses_it(core, toks, sp.name) else "no",
            "qc_artifact_contract": "yes" if emits_qc_artifact(sp) else "no",
            "doc_reference_exists": "yes" if doc_reference(skill, sp.name, core) else "no",
        })
        log.add_input(sp)

    rows.sort(key=lambda r: (r["skill"], r["detector"]))
    out = log.run_dir / "coverage_matrix.csv"
    cols = ["detector", "skill", "script_exists", "fixture_exists",
            "regression_test_exists", "demo_output_uses_it",
            "qc_artifact_contract", "doc_reference_exists"]
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)

    n = len(rows)
    def pct(key):
        c = sum(1 for r in rows if r[key] == "yes")
        return f"{c}/{n}"
    print(f"detectors inventoried: {n} (catalog SSOT integrity_detectors should match)")
    for key in cols[3:]:
        print(f"  {key}: {pct(key)}")

    log.log_component(
        component_type="deterministic_script",
        script_path=str(Path(__file__).relative_to(REPO_ROOT)),
        command_args=[],
        expected_reproducibility="exact",
        rerun_policy="rerun any time; coverage_matrix.csv hash stable for a fixed tree",
        input_paths=[sp for sp in scripts],
        output_path=out,
    )
    limitations = (
        "E7 is a coverage INVENTORY, not a guarantee that every detector ships "
        "every asset. Fixture/test/demo/doc detection uses filename + content "
        "heuristics (token matching); a 'no' means the heuristic found no link "
        "and is a backlog candidate, not necessarily a true absence. "
        "Detector enumeration mirrors validate_catalog_consistency.py "
        f"(globs: {DETECTOR_GLOBS}); n={n} should equal "
        "metadata/catalog_counts.json::integrity_detectors."
    )
    log.finalize(metrics_path=out, limitations=limitations,
                 repro_hash_extra=[out])
    print(f"\nwrote {out}")
    print(f"run dir: {log.run_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
