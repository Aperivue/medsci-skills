#!/usr/bin/env python3
"""Frontmatter schema gate for Agent Skills cross-platform portability.

The repo's own generators parse SKILL.md frontmatter with a tolerant line-based
reader (`gen_skills_catalog_json._frontmatter_field`), so a frontmatter block that
is NOT valid YAML can still pass every existing gate — but a strict-YAML consumer
(the agentskills.io directory validator, or another agent platform that loads the
skill) would reject it. This check enforces the published Agent Skills spec
(https://agentskills.io/specification) so skills stay portable:

  - the frontmatter block is **valid YAML** (strict `yaml.safe_load`);
  - `name`: present, string, <= 64 chars, lowercase alphanumeric + single hyphens
    (no leading/trailing/consecutive hyphen), and free of the reserved tokens
    `claude` / `anthropic`;
  - `description`: present, non-empty string, <= 1024 chars, with no XML angle
    brackets in the value (injection-surface hardening).

This is a repo-CI validator (it lives in `scripts/`, not `skills/*/scripts/`), so it
is NOT counted as an analysis-integrity detector. Exit 0 when every skill conforms;
non-zero with a per-skill report on any violation. Requires PyYAML.

Usage:
  python3 scripts/check_frontmatter_schema.py            # scans skills/
  python3 scripts/check_frontmatter_schema.py --root DIR  # scans DIR/*/SKILL.md (tests)
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
RESERVED_TOKENS = ("claude", "anthropic")
NAME_MAX = 64
DESC_MAX = 1024
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---", re.S)


def parse_frontmatter(text: str):
    """Return (mapping, error). error is a string when the block is missing/invalid."""
    m = FRONTMATTER_RE.match(text)
    if not m:
        return None, "no '---' frontmatter block at top of file"
    try:
        fm = yaml.safe_load(m.group(1))
    except yaml.YAMLError as exc:
        first = str(exc).splitlines()[0]
        return None, f"frontmatter is not valid YAML ({first})"
    if not isinstance(fm, dict):
        return None, "frontmatter does not parse to a YAML mapping"
    return fm, None


def check_skill(sk: Path) -> list[str]:
    errs: list[str] = []
    fm, err = parse_frontmatter(sk.read_text(encoding="utf-8"))
    if err:
        return [err]

    name = fm.get("name")
    if not isinstance(name, str) or not name.strip():
        errs.append("missing or empty 'name'")
    else:
        if len(name) > NAME_MAX:
            errs.append(f"name is {len(name)} chars (> {NAME_MAX})")
        if not NAME_RE.match(name):
            errs.append(f"name must be lowercase alphanumeric + single hyphens: {name!r}")
        low = name.lower()
        for tok in RESERVED_TOKENS:
            if tok in low:
                errs.append(f"name contains reserved token {tok!r}")

    desc = fm.get("description")
    if not isinstance(desc, str) or not desc.strip():
        errs.append("missing or empty 'description'")
    else:
        if len(desc) > DESC_MAX:
            errs.append(f"description is {len(desc)} chars (> {DESC_MAX})")
        if "<" in desc or ">" in desc:
            errs.append("description contains an XML angle bracket ('<' or '>')")

    return errs


def main() -> int:
    ap = argparse.ArgumentParser(description="Agent Skills frontmatter schema gate.")
    ap.add_argument("--root", default="skills",
                    help="directory of <skill>/SKILL.md folders (default: skills)")
    args = ap.parse_args()

    root = Path(args.root)
    if not root.is_dir():
        print(f"ERROR: not a directory: {root}", file=sys.stderr)
        return 2

    print("=" * 41)
    print(" Frontmatter Schema (Agent Skills spec)")
    print("=" * 41)

    n = 0
    fails = 0
    for d in sorted(root.iterdir()):
        sk = d / "SKILL.md"
        if not (d.is_dir() and sk.exists()):
            continue
        n += 1
        for e in check_skill(sk):
            print(f"  FAIL  {d.name}: {e}", file=sys.stderr)
            fails += 1

    print(f"\nchecked {n} SKILL.md frontmatter block(s)")
    if fails:
        print(f"\nFRONTMATTER_SCHEMA_VIOLATION: {fails} issue(s).", file=sys.stderr)
        return 1
    print("OK: all frontmatter valid YAML and spec-conformant (name, description).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
