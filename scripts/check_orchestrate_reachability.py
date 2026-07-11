#!/usr/bin/env python3
"""Orchestrate reachability gate (audit finding F2).

`/orchestrate` is documented as the single entry point for the whole bundle, but it
routes from a hand-maintained "Available Skills" table in
`skills/orchestrate/SKILL.md`. When a new skill ships without a table row, the
single entry point cannot route to it — a silent discoverability regression that no
existing check caught (20 skills, most of the model-engineering lane, drifted out of
reach before this gate existed).

This validator asserts every skill directory is reachable from the router: its name
appears as a bolded first-column entry in the Available Skills table. The router
itself (`orchestrate`) is exempt, and a skill may be intentionally direct-only by
listing it in DIRECT_ONLY below with a one-line reason.

Top-level `scripts/` validator (not a `skills/*/scripts/` detector) — it audits the
routing surface, not a manuscript, so it is not part of the MedSci-Audit detector
count.

Usage:
  python3 scripts/check_orchestrate_reachability.py --strict
  python3 scripts/check_orchestrate_reachability.py --skill-md <f> --skills-dir <d> --strict
Exit: 0 when every skill is reachable (or exempt); with --strict, 1 on any gap; 2 on read error.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# The router itself is never a route target. A skill that is genuinely not meant to
# be reached through /orchestrate goes here with a reason (keep this near-empty).
DIRECT_ONLY: dict[str, str] = {
    "orchestrate": "the router itself",
}

ROW_RE = re.compile(r"^\|\s*\*\*([a-z0-9-]+)\*\*\s*\|", re.M)


def table_skills(skill_md: Path) -> set[str]:
    text = skill_md.read_text(encoding="utf-8")
    if "## Available Skills" not in text:
        raise ValueError(f"{skill_md}: no '## Available Skills' section")
    section = text.split("## Available Skills", 1)[1].split("## Classification Logic", 1)[0]
    return set(ROW_RE.findall(section))


def skill_dirs(skills_dir: Path) -> set[str]:
    return {p.name for p in skills_dir.iterdir() if p.is_dir() and (p / "SKILL.md").exists()}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--skill-md", default=str(ROOT / "skills/orchestrate/SKILL.md"))
    ap.add_argument("--skills-dir", default=str(ROOT / "skills"))
    ap.add_argument("--strict", action="store_true", help="exit 1 on any unreachable skill")
    args = ap.parse_args(argv)

    try:
        routed = table_skills(Path(args.skill_md))
        dirs = skill_dirs(Path(args.skills_dir))
    except (OSError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    required = dirs - set(DIRECT_ONLY)
    unreachable = sorted(required - routed)
    # a table row naming a skill that no longer exists is also drift
    ghost = sorted(routed - dirs - set(DIRECT_ONLY))

    print(f"orchestrate reachability: {len(routed)} routed / {len(dirs)} skills "
          f"({len(DIRECT_ONLY) - 1} direct-only exempt)")
    if unreachable:
        print(f"  UNREACHABLE ({len(unreachable)}) — not in the Available Skills table:")
        for s in unreachable:
            print(f"    - {s}")
    if ghost:
        print(f"  GHOST ({len(ghost)}) — routed to a skill directory that does not exist:")
        for s in ghost:
            print(f"    - {s}")
    if not unreachable and not ghost:
        print("  OK: every skill is reachable from /orchestrate.")

    return 1 if (args.strict and (unreachable or ghost)) else 0


if __name__ == "__main__":
    raise SystemExit(main())
