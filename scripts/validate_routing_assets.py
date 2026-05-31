#!/usr/bin/env python3
"""Routing-asset integrity check for medsci-skills (codex Improvement C).

A SKILL.md may route to a bundled asset (a checklist, a script, a template) by
name. If that file does not exist on disk, the skill silently degrades — at best
a confusing failure, at worst a fabrication path (see /check-reporting, where
SKILL.md advertised CONSORT/CARE/SPIRIT/CLAIM checklists that were never
vendored). This validator enforces the invariant: every asset a SKILL.md
references must exist.

Two scans, deliberately narrow to avoid prose false positives:

  A. ${CLAUDE_SKILL_DIR}/<path>  — every skill-dir-relative asset path in any
     skills/*/SKILL.md must resolve to an existing file (handles ../ cross-skill
     references such as verify-refs -> manage-refs).

  B. check-reporting Reference Files bullets — each ``Name.md`` listed with a
     `-- description` under the checklists block must exist in
     references/checklists/.

Exit 0 when every referenced asset exists. With --strict, exit 1 if any are
missing (CI gate). Stdlib-only.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path


# ${CLAUDE_SKILL_DIR}/<relative path ending in an asset extension>
SKILL_DIR_REF = re.compile(
    r"\$\{CLAUDE_SKILL_DIR\}/([A-Za-z0-9_./\-]+\.[A-Za-z0-9]+)"
)
# A bulleted "`Name.md` -- description" asset declaration (en-dash or --).
BULLET_ASSET = re.compile(r"`([A-Za-z0-9_][A-Za-z0-9_./\-]*\.md)`\s*(?:--|—)")


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def scan_skill_dir_refs(skill_md: Path) -> list[tuple[str, Path]]:
    """Return (referenced_rel_path, resolved_path) for every missing asset."""
    skill_dir = skill_md.parent
    txt = skill_md.read_text(encoding="utf-8")
    missing: list[tuple[str, Path]] = []
    for m in SKILL_DIR_REF.finditer(txt):
        rel = m.group(1)
        resolved = (skill_dir / rel).resolve()
        if not resolved.exists():
            missing.append((f"${{CLAUDE_SKILL_DIR}}/{rel}", resolved))
    return missing


def scan_checkreporting_bullets(root: Path) -> list[tuple[str, Path]]:
    """check-reporting Reference Files checklist bullets must exist."""
    skill_md = root / "skills" / "check-reporting" / "SKILL.md"
    if not skill_md.exists():
        return []
    cdir = root / "skills" / "check-reporting" / "references" / "checklists"
    txt = skill_md.read_text(encoding="utf-8")
    # Restrict to the "Reference Files" section to avoid matching prose elsewhere.
    start = txt.find("## Reference Files")
    end = txt.find("\n## ", start + 1) if start != -1 else -1
    section = txt[start:end] if start != -1 else txt
    missing: list[tuple[str, Path]] = []
    seen: set[str] = set()
    for m in BULLET_ASSET.finditer(section):
        fn = m.group(1)
        if fn in seen:
            continue
        seen.add(fn)
        if not (cdir / fn).exists():
            missing.append((f"checklists/{fn}", cdir / fn))
    return missing


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate that SKILL.md-referenced assets exist.")
    parser.add_argument("--scan", nargs="*", help="Explicit SKILL.md paths to scan (default: skills/*/SKILL.md).")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero if any referenced asset is missing.")
    args = parser.parse_args()

    root = repo_root()
    if args.scan:
        skill_mds = [Path(p).resolve() for p in args.scan]
    else:
        skill_mds = sorted((root / "skills").glob("*/SKILL.md"))

    total_refs = 0
    missing_all: list[tuple[str, str, Path]] = []  # (skill, ref, resolved)

    for skill_md in skill_mds:
        skill_name = skill_md.parent.name
        refs = scan_skill_dir_refs(skill_md)
        # count checked refs for reporting
        total_refs += len(SKILL_DIR_REF.findall(skill_md.read_text(encoding="utf-8")))
        for ref, resolved in refs:
            missing_all.append((skill_name, ref, resolved))

    bullet_missing = scan_checkreporting_bullets(root)
    for ref, resolved in bullet_missing:
        missing_all.append(("check-reporting", ref, resolved))

    print("=" * 41)
    print(" Routing-Asset Integrity")
    print("=" * 41)
    print(f"Scanned {len(skill_mds)} SKILL.md; {total_refs} ${{CLAUDE_SKILL_DIR}} asset refs "
          f"+ check-reporting checklist bullets.")
    if not missing_all:
        print("OK: every referenced asset exists.")
        return 0

    print(f"\nMISSING ({len(missing_all)}):")
    for skill_name, ref, resolved in missing_all:
        try:
            shown = resolved.relative_to(root)
        except ValueError:
            shown = resolved
        print(f"  [{skill_name}] {ref}  ->  {shown} (absent)")

    if args.strict:
        print("\nROUTING_ASSET_INTEGRITY_VIOLATION: referenced assets are missing.", file=sys.stderr)
        return 1
    print("\n(non-strict: reported only; rerun with --strict to fail.)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
