#!/usr/bin/env python3
"""A script no skill runs is a script that never runs — the non-detector sibling of
check_detector_reachability.py.

That gate closed the hole for scripts matching the detector glob (`check_*`, `detect_*`, `derive_*`).
It closed it for exactly those. Everything else under `skills/*/scripts/` — build helpers, assemblers,
validators that were deliberately named so the catalog would NOT count them — walked straight through.

`skills/sync-submission/scripts/assemble_supplement.py` (199 lines) is what walked through: shipped,
CI-tested, listed in the distribution manifest, announced in the CHANGELOG and the README — and
invoked by no SKILL.md. Its only caller was its own test. That is the same disease as the five
dormant detectors of PR #334, one category over: the gate was verifying the tool instead of the
*use* of the tool, and the "not a detector" naming convention that keeps the count honest had
quietly become a way to be exempt from being used at all.

A script is REACHABLE if:
  * a SKILL.md names it (any skill's — a SKILL.md may shell out to another skill's script via
    MEDSCI_SKILLS_ROOT, and six of them do), or
  * a reachable script names it (a bundle runner shelling out), or
  * a reachable Python script IMPORTS it from its own directory.

That last edge is not optional. `from _yaml_frontmatter import split_yaml_front_matter` does not
contain the string "_yaml_frontmatter.py", so a filename grep reports `_yaml_frontmatter.py` as
dead code when two scripts depend on it. A gate that invents phantom orphans gets switched off, and
takes the honest gates with it. Imports resolve within the script's own directory only — skills are
self-contained and cross-skill imports are forbidden.

A test, a challenge card, or a CI step does NOT make a script reachable. Those prove it works in a
laboratory. They are exactly what assemble_supplement.py had.

The escape hatch is MAINTAINER_TOOLS: a run-once authoring tool a maintainer invokes by hand is
legitimately not user-facing, but it must be *documented as such*. Each entry names the file that
documents it, and this gate verifies that file actually mentions it — otherwise the allowlist
becomes the place dead code goes to hide.

Usage:
    check_script_reachability.py [--strict] [--skills-dir DIR]

Stdlib only.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SCRIPT_SUFFIXES = {".py", ".sh", ".R"}

# Files that prove a script WORKS but never cause it to RUN for a user.
TEST_MARKERS = ("/tests/", "_challenge/", "/challenge/")

# Run-once authoring tools (skills/MAINTENANCE.md §3): invoked by a maintainer, never at skill
# invocation. Value = the file that documents the tool. The gate asserts the doc names it, so an
# entry here is a decision, not a hiding place.
MAINTAINER_TOOLS: dict[str, str] = {
    "make-figures/scripts/build_jacc_template.py": "skills/MAINTENANCE.md",
    "make-figures/scripts/extract_exemplar_from_pdf.py": "skills/MAINTENANCE.md",
    "check-reporting/scripts/verify_checklist_fidelity.py": "skills/MAINTENANCE.md",
}

IMPORT_RE = re.compile(r"^\s*(?:from|import)\s+([A-Za-z_][\w]*)", re.MULTILINE)


def is_test_path(p: Path) -> bool:
    return any(m in "/" + p.as_posix() for m in TEST_MARKERS)


def scripts_of(skills: Path) -> list[Path]:
    return sorted(
        p
        for p in skills.glob("*/scripts/*")
        if p.is_file() and p.suffix in SCRIPT_SUFFIXES and not is_test_path(p)
    )


def reachable_set(skills: Path, all_scripts: list[Path]) -> set[Path]:
    text = {p: p.read_text(encoding="utf-8", errors="ignore") for p in all_scripts}

    def edges(p: Path) -> set[Path]:
        out: set[Path] = set()
        body = text[p]
        # Shell-out by filename — repo-wide: preflight_gate.py (sync-submission) runs
        # check_placeholders.py (write-paper).
        for q in all_scripts:
            if q is not p and q.name in body:
                out.add(q)
        # Python import — same directory only (skills are self-contained).
        if p.suffix == ".py":
            for mod in IMPORT_RE.findall(body):
                cand = p.parent / f"{mod}.py"
                if cand.is_file() and cand != p:
                    out.add(cand)
        return out

    reach: set[Path] = set()
    frontier: list[Path] = []
    for skill_md in sorted(skills.glob("*/SKILL.md")):
        body = skill_md.read_text(encoding="utf-8", errors="ignore")
        for q in all_scripts:
            if q.name in body and q not in reach:
                reach.add(q)
                frontier.append(q)
    while frontier:
        for q in edges(frontier.pop()):
            if q not in reach:
                reach.add(q)
                frontier.append(q)
    return reach


def mentions(root: Path, doc_rel: str, name: str) -> bool:
    doc = root / doc_rel
    return doc.is_file() and name in doc.read_text(encoding="utf-8", errors="ignore")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--strict", action="store_true", help="exit 1 if any script is unreachable")
    ap.add_argument("--skills-dir", default=None, help="alternate skills/ tree (tests)")
    a = ap.parse_args()

    skills = Path(a.skills_dir).resolve() if a.skills_dir else ROOT / "skills"
    root = skills.parent
    if not skills.is_dir():
        print(f"ERROR: skills dir missing: {skills}", file=sys.stderr)
        return 2

    all_scripts = scripts_of(skills)
    reach = reachable_set(skills, all_scripts)

    problems: list[str] = []
    orphans: list[Path] = []
    for p in all_scripts:
        if p in reach:
            continue
        rel = p.relative_to(skills).as_posix()
        doc = MAINTAINER_TOOLS.get(rel)
        if doc is None:
            orphans.append(p)
        elif not mentions(root, doc, p.name):
            problems.append(
                f"{rel} is allowlisted as a maintainer tool but {doc} never mentions it "
                "— an undocumented allowlist entry is just dead code with permission"
            )

    # An allowlist entry for a file that no longer exists is stale bookkeeping; say so. Only
    # meaningful against the real tree — MAINTAINER_TOOLS is keyed to this repo's layout, and a
    # synthetic --skills-dir legitimately has none of those paths. Firing there would make the gate
    # cry wolf on good work.
    if a.skills_dir is None:
        for rel, doc in MAINTAINER_TOOLS.items():
            if not (skills / rel).is_file():
                problems.append(
                    f"MAINTAINER_TOOLS names {rel}, which does not exist (stale entry; doc={doc})"
                )

    total = len(all_scripts)
    if not orphans and not problems:
        print(
            f"OK: all {total} skill scripts are reachable from a SKILL.md "
            f"(directly, via a shell-out, or via a same-dir import); "
            f"{len(MAINTAINER_TOOLS)} documented maintainer tool(s) exempt."
        )
        return 0

    if orphans:
        print(f"SCRIPT_UNREACHABLE: {len(orphans)} of {total} skill scripts are never invoked by any skill.\n")
        for p in orphans:
            rel = p.relative_to(skills).as_posix()
            where = [
                str(q.relative_to(root))
                for q in skills.rglob("*")
                if q.is_file() and q != p and q.suffix in {".md", ".sh", ".py", ".yml", ".yaml"}
                and p.name in q.read_text(encoding="utf-8", errors="ignore")
            ]
            lab = [w for w in where if any(m in "/" + w for m in TEST_MARKERS)]
            print(f"  {rel}")
            if lab:
                print(f"      mentioned only in: {', '.join(lab[:3])}")
                print("      — a test and a CI step prove it WORKS. They do not make it RUN.")
            elif where:
                print(f"      mentioned in: {', '.join(where[:3])}")
            else:
                print("      — not mentioned anywhere. Dead code.")
        print()

    for m in problems:
        print(f"  ALLOWLIST: {m}")
    if problems:
        print()

    print("Fix: invoke it from the SKILL.md step it belongs to (see skills/MAINTENANCE.md §1-2), or")
    print("— if it is a run-once authoring tool — add it to MAINTAINER_TOOLS here AND document it")
    print("in skills/MAINTENANCE.md §3.")
    return 1 if a.strict else 0


if __name__ == "__main__":
    sys.exit(main())
