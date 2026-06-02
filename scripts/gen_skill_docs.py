#!/usr/bin/env python3
"""Generate one reference page per skill under docs/skills/ from each SKILL.md.

Why: GitHub Insights shows the repo's discovery is driven by Google search and
LLM-assistant referrals (ChatGPT/Perplexity), not virality — yet only the README and a
handful of SKILL.md files are indexable. One generated page per skill, keyed on the skill
name, description, and trigger phrases, multiplies the long-tail search + LLM-citable
surface. The pages are GENERATED, never hand-maintained (a parallel copy drifts), and
CI-gated with --check, exactly like metadata/catalog_counts.json gates the counts.

Fail loud: a malformed SKILL.md (missing required field, name != directory, unclosed
frontmatter, or an unsupported multiline value shape) aborts generation rather than
emitting a silently wrong page.

Stdlib-only (runs anywhere, incl. the local pre-commit context). Deterministic — sorted,
no timestamps — so --check is meaningful.

Usage:
  python3 scripts/gen_skill_docs.py            # write pages + index (remove stale)
  python3 scripts/gen_skill_docs.py --check    # verify in sync; exit 1 on drift (CI gate)
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / "skills"
DOCS_DIR = ROOT / "docs" / "skills"

REQUIRED = ("name", "description", "triggers", "tools", "model")
RESOURCE_DIRS = ("references", "scripts", "templates")
RESOURCE_LABELS = {"references": "References", "scripts": "Scripts", "templates": "Templates"}

KEY_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*):(.*)$")
BLOCK_INDICATORS = {">", "|", ">-", "|-", ">+", "|+"}


class SkillError(Exception):
    """Raised when a SKILL.md cannot be parsed into a valid, complete page."""


def parse_frontmatter(text: str, skill: str) -> dict[str, str]:
    """Parse the YAML frontmatter block. Supports single-line `key: value` and folded/
    literal block scalars (`key: >` / `key: |`). Any other multiline shape fails loud."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise SkillError(f"{skill}: SKILL.md must open with a '---' frontmatter line")

    fm: list[str] = []
    closed = False
    for line in lines[1:]:
        if line.strip() == "---":
            closed = True
            break
        fm.append(line)
    if not closed:
        raise SkillError(f"{skill}: frontmatter block is not closed by a second '---'")

    data: dict[str, str] = {}
    i, n = 0, len(fm)
    while i < n:
        line = fm[i]
        if not line.strip():
            i += 1
            continue
        m = KEY_RE.match(line)
        if not m or line[:1].isspace():
            raise SkillError(f"{skill}: unsupported frontmatter line: {line!r}")
        key, rest = m.group(1), m.group(2).strip()

        if rest in BLOCK_INDICATORS:  # block scalar — collect indented continuation
            i += 1
            block: list[str] = []
            while i < n:
                nxt = fm[i]
                if nxt.strip() == "":
                    i += 1
                    continue
                if not nxt[:1].isspace():
                    break  # next top-level key
                block.append(nxt.strip())
                i += 1
            data[key] = " ".join(block).strip()
            continue

        if rest == "":  # empty value with indented followers == list/other — unsupported
            j = i + 1
            while j < n and fm[j].strip() == "":
                j += 1
            if j < n and fm[j][:1].isspace():
                raise SkillError(f"{skill}: unsupported multiline/list value for '{key}'")
            data[key] = ""
            i += 1
            continue

        data[key] = rest.strip().strip('"').strip("'")
        i += 1
    return data


def load_skill(skill_dir: Path) -> dict[str, str]:
    name_dir = skill_dir.name
    fm = parse_frontmatter((skill_dir / "SKILL.md").read_text(encoding="utf-8"), name_dir)
    missing = [k for k in REQUIRED if not fm.get(k)]
    if missing:
        raise SkillError(f"{name_dir}: missing/empty frontmatter field(s): {', '.join(missing)}")
    if fm["name"] != name_dir:
        raise SkillError(f"{name_dir}: frontmatter name '{fm['name']}' != directory name")
    return fm


def _ignorable(p: Path) -> bool:
    """Untracked build/OS artifacts that exist locally but not in a clean checkout —
    excluding them keeps counts identical between a working tree and CI (determinism)."""
    if p.suffix == ".pyc":
        return True
    return any(part == "__pycache__" or part.startswith(".") for part in p.parts)


def list_resources(skill_dir: Path) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for cat in RESOURCE_DIRS:
        d = skill_dir / cat
        if not d.is_dir():
            continue
        entries: list[str] = []
        for child in sorted(d.iterdir(), key=lambda p: p.name):
            if child.name.startswith(".") or child.name == "__pycache__":
                continue
            if child.is_dir():
                count = sum(1 for p in child.rglob("*") if p.is_file() and not _ignorable(p))
                entries.append(f"`{child.name}/` ({count} file{'s' if count != 1 else ''})")
            else:
                entries.append(f"`{child.name}`")
        if entries:
            out[cat] = entries
    return out


def short_desc(desc: str, cap: int = 200) -> str:
    end = len(desc)
    p = desc.find(". ")
    if p != -1:
        end = p + 1
    end = min(end, cap)
    s = desc[:end].rstrip()
    if end < len(desc) and not s.endswith("."):
        s += "…"
    return s


def render_page(name: str, fm: dict[str, str], resources: dict[str, list[str]]) -> str:
    triggers = ", ".join(t.strip() for t in fm["triggers"].split(",") if t.strip())
    out = [
        f"<!-- AUTO-GENERATED from skills/{name}/SKILL.md by scripts/gen_skill_docs.py. Do not edit by hand. -->",
        "",
        f"# {name}",
        "",
        f"> {fm['description']}",
        "",
        f"**Invoke:** `/{name}` · **Tools:** {fm['tools']} · **Model:** {fm['model']}",
        "",
        "## When to use",
        "",
        f"`{name}` activates on requests such as: {triggers}.",
        "",
    ]
    if resources:
        out += ["## Bundled resources", ""]
        for cat in RESOURCE_DIRS:
            if cat in resources:
                out.append(f"**{RESOURCE_LABELS[cat]}** (`skills/{name}/{cat}/`):")
                out.append("")
                out += [f"- {e}" for e in resources[cat]]
                out.append("")
    out += [
        "## Source",
        "",
        f"Canonical definition: [`skills/{name}/SKILL.md`](../../skills/{name}/SKILL.md)",
        "",
        "---",
        "",
        "*Part of [MedSci Skills](../../README.md) — Claude Code skills for the medical "
        "research lifecycle. This page is generated from the skill's `SKILL.md`; edit that "
        "file and re-run `scripts/gen_skill_docs.py`.*",
        "",
    ]
    return "\n".join(out)


def render_index(skills: list[tuple[str, dict[str, str]]]) -> str:
    out = [
        "<!-- AUTO-GENERATED by scripts/gen_skill_docs.py. Do not edit by hand. -->",
        "",
        "# MedSci Skills — Skill Reference",
        "",
        "One reference page per skill, generated from each skill's `SKILL.md`. Each page "
        "describes what the skill does, when it activates, and its bundled resources, and "
        "links to the canonical definition. See the [main README](../../README.md) for "
        "installation and live demos.",
        "",
    ]
    out += [f"- [{name}]({name}.md) — {short_desc(fm['description'])}" for name, fm in skills]
    out.append("")
    return "\n".join(out)


def build() -> dict[Path, str]:
    if not SKILLS_DIR.is_dir():
        raise SkillError("skills/ directory not found")
    skill_dirs = sorted(
        (p for p in SKILLS_DIR.iterdir() if p.is_dir() and (p / "SKILL.md").exists()),
        key=lambda p: p.name,
    )
    if not skill_dirs:
        raise SkillError("no skills with a SKILL.md found")
    expected: dict[Path, str] = {}
    loaded: list[tuple[str, dict[str, str]]] = []
    for sd in skill_dirs:
        fm = load_skill(sd)
        expected[DOCS_DIR / f"{sd.name}.md"] = render_page(sd.name, fm, list_resources(sd))
        loaded.append((sd.name, fm))
    expected[DOCS_DIR / "README.md"] = render_index(loaded)
    return expected


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate per-skill docs under docs/skills/.")
    ap.add_argument("--check", action="store_true",
                    help="verify docs/skills/ matches the skills; exit 1 on drift (no writes)")
    args = ap.parse_args()

    try:
        expected = build()
    except SkillError as e:
        print(f"FAIL: {e}", file=sys.stderr)
        return 1

    existing = set(DOCS_DIR.glob("*.md")) if DOCS_DIR.is_dir() else set()
    stale = sorted(existing - set(expected))

    if args.check:
        problems: list[str] = []
        for path, content in sorted(expected.items()):
            rel = path.relative_to(ROOT)
            if not path.exists():
                problems.append(f"MISSING {rel}")
            elif path.read_text(encoding="utf-8") != content:
                problems.append(f"CHANGED {rel}")
        problems += [f"EXTRA   {p.relative_to(ROOT)}" for p in stale]
        if problems:
            print("SKILL_DOCS_DRIFT — run `python3 scripts/gen_skill_docs.py`:", file=sys.stderr)
            for p in problems:
                print(f"  {p}", file=sys.stderr)
            return 1
        print(f"OK: docs/skills/ in sync ({len(expected) - 1} skill pages + index).")
        return 0

    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    written = 0
    for path, content in sorted(expected.items()):
        if not path.exists() or path.read_text(encoding="utf-8") != content:
            path.write_text(content, encoding="utf-8")
            written += 1
    for path in stale:
        path.unlink()
    print(f"OK: wrote/updated {written}, removed {len(stale)} stale; "
          f"docs/skills/ now has {len(expected) - 1} skill pages + index.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
