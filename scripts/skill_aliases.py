#!/usr/bin/env python3
"""Which `skills/<name>/` directories are compatibility aliases rather than skills.

v6.0 merged twelve imaging skills into seven. The nine retired names still ship, until v7, as
alias stubs — a `SKILL.md` and nothing else — so that `/architecture-zoo` and a namespaced
`/medsci-modeling:architecture-zoo` keep resolving for people whose muscle memory, notes and
CLAUDE.md files still say the old name, and so that an upgrade replaces the old skill instead of
pruning it. A stub is not a skill: it has no contract, no scripts, no docs page, must not be counted
as one, must not be routed to, and must not be named by another skill.

Every gate that enumerates `skills/` asks this module which directories are stubs, so the answer
lives in one place instead of being re-derived per gate.

A directory is an alias stub when its SKILL.md frontmatter has BOTH

    disable-model-invocation: true
    description: Renamed to /<target> in v<N> ...

Anything else is a canonical skill and gets the full set of gates. The shape is then made strict by
`alias_problems()`:

  * SKILL.md is the only file in the directory (no scripts, no skill.yml — a stub that grows a
    script has become a second copy of the skill it points at);
  * `name` equals the directory;
  * the target is a canonical skill, not missing and not itself an alias;
  * the target's `skill.yml` lists the stub under `aliases:` — the canonical side declares what it
    absorbed, so neither side can drift alone.

Usage:
    python3 scripts/skill_aliases.py [--skills-dir DIR]      # print the alias table; exit 1 on a problem
    python3 scripts/skill_aliases.py --is-alias DIR          # exit 0 if DIR is an alias stub, 1 if not

Stdlib only.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / "skills"

RENAMED_RE = re.compile(r"^Renamed to /([a-z0-9]+(?:-[a-z0-9]+)*) in v\d+\b")
BLOCK = {">", "|", ">-", "|-", ">+", "|+"}


def frontmatter(skill_md: Path) -> dict[str, str]:
    """Top-level scalar fields of a SKILL.md frontmatter block (folded blocks joined). Empty on
    a missing or unclosed block — the schema gates own reporting that."""
    try:
        lines = skill_md.read_text(encoding="utf-8").splitlines()
    except OSError:
        return {}
    if not lines or lines[0].strip() != "---":
        return {}
    body: list[str] = []
    for line in lines[1:]:
        if line.strip() == "---":
            break
        body.append(line)
    else:
        return {}
    out: dict[str, str] = {}
    for i, line in enumerate(body):
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*):(.*)$", line)
        if not m:
            continue
        key, rest = m.group(1), m.group(2).strip()
        if rest in BLOCK:
            block = []
            for nxt in body[i + 1:]:
                if nxt.strip() and not nxt[:1].isspace():
                    break
                if nxt.strip():
                    block.append(nxt.strip())
            rest = " ".join(block)
        out[key] = rest.strip().strip('"').strip("'")
    return out


def alias_target(skill_dir: Path) -> str | None:
    """The canonical skill a stub redirects to, or None when `skill_dir` is not an alias stub."""
    fm = frontmatter(skill_dir / "SKILL.md")
    if fm.get("disable-model-invocation", "").lower() != "true":
        return None
    m = RENAMED_RE.match(fm.get("description", ""))
    return m.group(1) if m else None


def partition(skills_dir: Path = SKILLS_DIR) -> tuple[list[str], dict[str, str]]:
    """(canonical skill names, {alias: target}) for every directory carrying a SKILL.md."""
    canonical: list[str] = []
    aliases: dict[str, str] = {}
    for d in sorted(p for p in skills_dir.iterdir() if p.is_dir() and (p / "SKILL.md").is_file()):
        target = alias_target(d)
        if target is None:
            canonical.append(d.name)
        else:
            aliases[d.name] = target
    return canonical, aliases


def is_alias(skill_dir: Path) -> bool:
    return (skill_dir / "SKILL.md").is_file() and alias_target(skill_dir) is not None


def _declared_aliases(skill_yml: Path) -> set[str]:
    """Names listed under a top-level `aliases:` in a skill.yml (block or inline list)."""
    if not skill_yml.is_file():
        return set()
    lines = skill_yml.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines):
        m = re.match(r"^aliases:\s*(.*)$", line)
        if not m:
            continue
        inline = m.group(1).strip()
        if inline.startswith("["):
            return {x.strip().strip("'\"") for x in inline.strip("[]").split(",") if x.strip()}
        out: set[str] = set()
        for nxt in lines[i + 1:]:
            mm = re.match(r"^\s*-\s+(\S+)", nxt)
            if mm:
                out.add(mm.group(1).strip("'\""))
            elif nxt.strip() and not nxt[:1].isspace():
                break
        return out
    return set()


def alias_problems(skills_dir: Path = SKILLS_DIR) -> list[str]:
    canonical, aliases = partition(skills_dir)
    canon = set(canonical)
    problems: list[str] = []
    for alias, target in sorted(aliases.items()):
        d = skills_dir / alias
        extra = sorted(str(p.relative_to(d)) for p in d.rglob("*")
                       if p.is_file() and p.name != "SKILL.md" and "__pycache__" not in p.parts)
        if extra:
            problems.append(f"{alias}: an alias stub ships SKILL.md only, found {', '.join(extra)}")
        name = frontmatter(d / "SKILL.md").get("name")
        if name != alias:
            problems.append(f"{alias}: frontmatter name {name!r} != directory")
        if target in aliases:
            problems.append(f"{alias}: redirects to /{target}, which is itself an alias")
        elif target not in canon:
            problems.append(f"{alias}: redirects to /{target}, which is not a skill in {skills_dir.name}/")
        elif alias not in _declared_aliases(skills_dir / target / "skill.yml"):
            problems.append(f"{alias}: skills/{target}/skill.yml does not list it under aliases:")
    for name in canonical:
        for declared in sorted(_declared_aliases(skills_dir / name / "skill.yml")):
            if aliases.get(declared) != name:
                problems.append(f"{name}: skill.yml declares alias {declared!r}, but "
                                f"skills/{declared}/ is not a stub redirecting to /{name}")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--skills-dir", type=Path, default=SKILLS_DIR)
    ap.add_argument("--is-alias", type=Path, metavar="DIR",
                    help="exit 0 if DIR is an alias stub, 1 otherwise (for shell callers)")
    a = ap.parse_args()
    if a.is_alias is not None:
        return 0 if is_alias(a.is_alias) else 1

    canonical, aliases = partition(a.skills_dir)
    print(f"{len(canonical)} canonical skills, {len(aliases)} compatibility aliases")
    for alias, target in sorted(aliases.items()):
        print(f"  /{alias} -> /{target}")
    problems = alias_problems(a.skills_dir)
    if problems:
        print(f"\nALIAS_STUB_DRIFT: {len(problems)} problem(s)", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
