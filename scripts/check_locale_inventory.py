#!/usr/bin/env python3
"""Locale-inventory coverage gate for medsci-skills.

medsci-skills is English-canonical: skill mechanics and prose are English, and
non-English (currently Korean) text is allowed only as a labeled locale feature,
a locale-jurisdiction mode, a bilingual trigger, or an opt-in `*_ko` variant.
Every such file must be justified in `docs/locale_inventory.md`.

This is the auditable allowlist gate (the real anti-drift guard), independent of
the WARN-only Korean-prose check in validate_skills.sh (which scans only SKILL.md
and skips code/tables/blockquotes). It enforces the invariant:

  every file matched by `grep -rl '[가-힣]' skills/` MUST appear as a row in
  docs/locale_inventory.md.

A Korean-bearing file that is *missing* from the inventory fails the check (a leak
slipped past review). An inventory row whose file no longer contains Korean is
*stale* (a translated/redesigned file whose row should be removed) — reported as a
warning by default, and as a failure under --strict.

Exit 0 when coverage is clean. Exit 1 on findings (missing always; stale under
--strict). Exit 2 on operational error. Stdlib-only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Same Hangul range as validate_skills.sh check #9 (syllables + isolated jamo).
HANGUL = re.compile(r"[가-힣ㄱ-ㆎ]")
# Any skills/-relative path token mentioned in the inventory prose/tables.
SKILLS_PATH = re.compile(r"skills/[A-Za-z0-9_./\-]+")
# Files we never scan for content (binary-ish); kept small and explicit.
SKIP_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".docx", ".xlsx", ".zip", ".pptx"}


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def korean_files(skills_dir: Path, base: Path) -> set[str]:
    """Posix paths (relative to `base`, i.e. `skills/...`) of files under skills/ containing Hangul."""
    found: set[str] = set()
    for p in sorted(skills_dir.rglob("*")):
        if not p.is_file() or p.suffix.lower() in SKIP_SUFFIXES:
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except (OSError, ValueError):
            continue
        if HANGUL.search(text):
            found.add(p.relative_to(base).as_posix())
    return found


def inventory_paths(inventory: Path, base: Path) -> set[str]:
    """`skills/...` path tokens listed in the inventory that resolve to real files under `base`."""
    text = inventory.read_text(encoding="utf-8", errors="ignore")
    listed: set[str] = set()
    for tok in SKILLS_PATH.findall(text):
        if (base / tok).is_file():
            listed.add(tok)
    return listed


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--skills-dir", default=None, help="skills/ directory (default: <repo>/skills)")
    ap.add_argument("--inventory", default=None, help="inventory file (default: <repo>/docs/locale_inventory.md)")
    ap.add_argument("--strict", action="store_true", help="treat stale inventory rows as failures too")
    ap.add_argument("--quiet", action="store_true", help="suppress the per-file listing")
    ap.add_argument("--json", action="store_true", help="emit a JSON summary instead of text")
    args = ap.parse_args()

    root = repo_root()
    skills_dir = Path(args.skills_dir).resolve() if args.skills_dir else root / "skills"
    inventory = Path(args.inventory).resolve() if args.inventory else root / "docs" / "locale_inventory.md"

    if not skills_dir.is_dir():
        print(f"ERROR: skills dir not found: {skills_dir}", file=sys.stderr)
        return 2
    if not inventory.is_file():
        print(f"ERROR: inventory not found: {inventory}", file=sys.stderr)
        return 2

    base = skills_dir.parent  # so file paths read as "skills/..." regardless of --skills-dir
    korean = korean_files(skills_dir, base)
    listed = inventory_paths(inventory, base)

    missing = sorted(korean - listed)   # Korean files not in the inventory -> leak (FAIL)
    stale = sorted(listed - korean)     # inventoried files no longer Korean -> remove row (WARN/strict-FAIL)

    summary = {
        "korean_files": len(korean),
        "inventoried_files": len(listed),
        "missing": missing,
        "stale": stale,
        "strict": args.strict,
        "ok": not missing and (not stale or not args.strict),
    }

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(f"Locale inventory: {len(korean)} Korean-bearing file(s) under skills/; "
              f"{len(listed)} inventoried.")
        if missing:
            print(f"\nMISSING from docs/locale_inventory.md ({len(missing)}) — leak, FAIL:")
            if not args.quiet:
                for m in missing:
                    print(f"  - {m}")
        if stale:
            tag = "FAIL (--strict)" if args.strict else "warning"
            print(f"\nSTALE inventory rows ({len(stale)}) — file no longer contains Korean, remove row [{tag}]:")
            if not args.quiet:
                for s in stale:
                    print(f"  - {s}")
        if summary["ok"]:
            print("\nOK: every Korean-bearing file is inventory-justified.")

    if missing:
        return 1
    if stale and args.strict:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
