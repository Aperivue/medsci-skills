#!/usr/bin/env python3
"""`gh skill` discovery gate -- nothing may look like a skill except a skill.

`gh skill` (GitHub CLI >= 2.90) discovers publishable skills by looking for a
directory literally named `skills` -- at ANY depth -- and treating every
`<name>/SKILL.md` beneath it as a real, installable skill. A test fixture parked
at `tests/fixtures/<x>/skills/<name>/SKILL.md` is therefore not a fixture to
`gh skill`: it is a second skill called `<name>`.

That happened here. The frozen phase-budget regression fixture lived at
`tests/fixtures/phase_budget/skills/self-review/SKILL.md`. It is a deliberate
copy of a shipped defect, so it carries no frontmatter -- which meant:

  * `gh skill publish --dry-run` failed the WHOLE repository on it
    ("error self-review missing required field: name"), and
  * `gh skill install --all Aperivue/medsci-skills` would have offered users a
    broken second `self-review`, colliding by name with the real one.

The reason it survived is the reason this gate exists: no other CI gate runs
`gh skill`, and `gh` is not available in the validate job. The defect was
invisible to a green build. So this gate enforces the same property by path
arithmetic, needing no network and no `gh`:

    every SKILL.md on disk is either canonical (`skills/<name>/SKILL.md` at the
    repo root) or lives outside any directory named `skills`.

Fixing a violation does not mean deleting the fixture. It means renaming the
enclosing `skills/` directory to something `gh` does not look for -- the
phase-budget fixture now sits under `real_defect/` -- and pointing whatever
consumes it at the new path. The fixture keeps doing its job; it just stops
impersonating a skill.

Top-level `scripts/` validator (not a `skills/*/scripts/` detector) -- it audits
the repository layout, so it is deliberately outside the detector catalog.

Usage:
  python3 scripts/check_skill_discovery.py
  python3 scripts/check_skill_discovery.py --strict     # exit 1 on violation
  python3 scripts/check_skill_discovery.py --root <dir> # audit another tree
  python3 scripts/check_skill_discovery.py --json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR_NAME = "skills"
SKILL_FILE = "SKILL.md"


def _skill_files(root: Path) -> list[Path]:
    """Every SKILL.md `gh skill` would see, as repo-relative paths.

    This walks the FILESYSTEM, not `git ls-files`, and the distinction is the whole
    point: `gh skill publish` reads the working tree. An earlier draft of this gate
    read the index instead, so moving the fixture back to `skills/` with a plain
    `mv` left the index untouched and the gate reported OK on the very defect it
    was written for -- a green that meant nothing. Gate what the producer reads.

    Dot-directories are skipped because `gh skill` skips them too: it needs an
    explicit `--allow-hidden-dirs` to look inside `.claude/skills/`, `.github/skills/`
    and friends, so by default they are not discoverable and must not be flagged.
    """
    skipped_names = {"node_modules"}
    found = []
    for p in root.rglob(SKILL_FILE):
        rel = p.relative_to(root)
        parts = rel.parts
        if any(part.startswith(".") or part in skipped_names for part in parts[:-1]):
            continue
        found.append(rel)
    return sorted(found)


def _is_canonical(rel: Path) -> bool:
    """`skills/<name>/SKILL.md` at the repo root -- the one shape that may exist."""
    parts = rel.parts
    return len(parts) == 3 and parts[0] == SKILLS_DIR_NAME and parts[2] == SKILL_FILE


def _is_discoverable(rel: Path) -> bool:
    """Would `gh skill` treat this file as a skill? True if any parent is `skills`."""
    return SKILLS_DIR_NAME in rel.parts[:-1]


def audit(root: Path) -> dict:
    violations = []
    canonical = 0

    for rel in _skill_files(root):
        if _is_canonical(rel):
            canonical += 1
        elif _is_discoverable(rel):
            violations.append(
                {
                    "file": str(rel),
                    "skill_name_it_would_claim": rel.parts[-2],
                    "why": (
                        "sits under a directory named 'skills', so `gh skill` "
                        "discovers it as a publishable skill"
                    ),
                    "fix": (
                        f"rename the enclosing '{SKILLS_DIR_NAME}/' directory "
                        "(e.g. to 'real_defect/') and update whatever reads it"
                    ),
                }
            )

    return {
        "verdict": "SKILL_DISCOVERY_COLLISION" if violations else "ok",
        "canonical_skills": canonical,
        "violations": violations,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--strict", action="store_true", help="exit 1 on violation")
    ap.add_argument("--json", action="store_true", help="machine-readable verdict")
    args = ap.parse_args()

    result = audit(Path(args.root).resolve())

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        for v in result["violations"]:
            print(f"SKILL_DISCOVERY_COLLISION\t{v['file']}")
            print(f"  would be published as the skill: {v['skill_name_it_would_claim']}")
            print(f"  why: {v['why']}")
            print(f"  fix: {v['fix']}")
        if not result["violations"]:
            print(
                f"OK: {result['canonical_skills']} canonical skills; "
                "no other file is discoverable as one."
            )

    if result["violations"] and args.strict:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
