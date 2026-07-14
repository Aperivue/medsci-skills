#!/usr/bin/env python3
"""SKILL.md phase-budget gate.

A SKILL.md is loaded IN FULL into the context window the moment the skill is
invoked -- before the agent has done anything, before it knows what the user
wants. Its length is a bill the user pays on every invocation, whether or not a
single line of it turns out to be relevant. A 200-line phase buried at the
bottom of a skill is 200 lines of tax on every run that never reaches it.

The project rule (the one that cut /present-paper Phase 0 from ~14,000 tokens to
~6,700) is:

    Any phase over 80 lines gets extracted to references/, leaving a trigger
    table and a load-on-demand pointer.

Nothing enforced it, so twelve sections across five skills drifted over. This
validator enforces it: every `##` / `###` section in every skills/*/SKILL.md must
have a body of at most --max-lines lines (default 80), measured as the lines
between the heading and the next heading of the same or finer granularity.

A section that genuinely cannot be split lives in EXEMPT with a one-line reason,
so that a long section is a decision someone wrote down -- not a rule that
quietly stopped applying.

Top-level `scripts/` validator (not a `skills/*/scripts/` detector) -- it audits
the context budget of the skill surface, not a manuscript, so it is NOT part of
the MedSci-Audit detector count.

Usage:
  python3 scripts/check_phase_budget.py --strict
  python3 scripts/check_phase_budget.py --max-lines 80 --json
  python3 scripts/check_phase_budget.py --skills-dir <dir> --strict
Exit: 0 when every section is within budget (or exempt); with --strict, 1 on any
over-budget section; 2 on a read error.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Sections that are deliberately over budget. Key is "<skill>::<section title>",
# value is the one-line reason. Keep this near-empty: an exemption is a decision
# someone wrote down, and every entry here is context every user pays for.
EXEMPT: dict[str, str] = {}

# A section starts at a level-2 or level-3 ATX heading and ends at the next one.
HEADING_RE = re.compile(r"^(#{2,3})\s+(\S.*?)\s*$")
# Fenced code blocks may contain lines that look like headings (`## comment`).
FENCE_RE = re.compile(r"^\s*(```|~~~)")

# What a compliant fix looks like. Printed on failure -- the gate should teach
# the shape of the fix, not merely name the offender.
TRIGGER_TABLE_SHAPE = """\
  Leave in SKILL.md a short prose lead plus a trigger table, and move the body to
  skills/<skill>/references/<phase-slug>.md:

      Read on demand -- after the ask tells you which one you need:

      | File | Read it when | Cost if read blindly |
      |---|---|---|
      | `references/<phase-slug>.md` | <the condition that makes it relevant> | ~N tokens you will not use |

      **Load-on-demand**: read `${CLAUDE_SKILL_DIR}/references/<phase-slug>.md`
      when <condition>.

  One question decides every one of these reads:

      *** Does the agent need this BEFORE it knows what the user wants, or after? ***

  BEFORE  -> it stays in SKILL.md (control flow, the routing question, the gate
             that must run on every path).
  AFTER   -> it goes to references/ behind a trigger row (the detector table, the
             worked example, the long enumeration, the branch that one ask in ten
             will take).

  A section that genuinely cannot be split goes in EXEMPT in this script with a
  one-line reason -- so it is a decision on the record, not a rule that quietly
  stopped applying."""


def sections(md_path: Path) -> list[tuple[str, int, int]]:
    """Return (title, start_line_1based, body_line_count) for each ##/### section."""
    lines = md_path.read_text(encoding="utf-8").splitlines()
    in_fence = False
    heads: list[tuple[int, str]] = []
    for i, line in enumerate(lines):
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = HEADING_RE.match(line)
        if m:
            heads.append((i, m.group(2)))

    out: list[tuple[str, int, int]] = []
    for n, (i, title) in enumerate(heads):
        end = heads[n + 1][0] if n + 1 < len(heads) else len(lines)
        out.append((title, i + 1, end - i - 1))
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--skills-dir", default=str(ROOT / "skills"))
    ap.add_argument("--max-lines", type=int, default=80,
                    help="maximum body lines per ##/### section (default: 80)")
    ap.add_argument("--strict", action="store_true",
                    help="exit 1 when any section is over budget")
    ap.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = ap.parse_args(argv)

    skills_dir = Path(args.skills_dir)
    try:
        skill_mds = sorted(skills_dir.glob("*/SKILL.md"))
        scanned = 0
        total = 0
        over: list[dict[str, object]] = []
        exempted: list[dict[str, object]] = []
        for md in skill_mds:
            skill = md.parent.name
            scanned += 1
            for title, line, body in sections(md):
                total += 1
                if body <= args.max_lines:
                    continue
                key = f"{skill}::{title}"
                rec: dict[str, object] = {
                    "skill": skill,
                    "section": title,
                    "file": str(md.relative_to(skills_dir.parent))
                    if skills_dir.parent in md.parents else str(md),
                    "line": line,
                    "body_lines": body,
                    "budget": args.max_lines,
                    "over_by": body - args.max_lines,
                }
                if key in EXEMPT:
                    rec["reason"] = EXEMPT[key]
                    exempted.append(rec)
                else:
                    over.append(rec)
    except OSError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    over.sort(key=lambda r: -int(r["body_lines"]))
    verdict = "PHASE_BUDGET_EXCEEDED" if over else "OK"

    if args.json:
        print(json.dumps(
            {
                "verdict": verdict,
                "budget": args.max_lines,
                "skills_scanned": scanned,
                "sections_scanned": total,
                "over_budget": over,
                "exempt": exempted,
            },
            indent=2,
        ))
    else:
        print("=" * 41)
        print(" SKILL.md Phase Budget")
        print("=" * 41)
        print(f"Scanned {scanned} SKILL.md, {total} sections; budget {args.max_lines} lines/section"
              f"; {len(exempted)} exempt.")
        if not over:
            print("OK: every section is within budget.")
            for rec in exempted:
                print(f"  exempt: {rec['skill']}::{rec['section']} "
                      f"({rec['body_lines']} lines) -- {rec['reason']}")
        else:
            print(f"\nOVER BUDGET ({len(over)}) -- each of these is loaded in full, "
                  f"on every invocation of the skill,\nbefore the agent knows whether it "
                  f"is relevant:\n")
            for rec in over:
                print(f"  {int(rec['body_lines']):4} lines (+{rec['over_by']:>3} over)  "
                      f"{rec['skill']}/SKILL.md:{rec['line']}  {rec['section']}")
            print()
            print(TRIGGER_TABLE_SHAPE)
            print(f"\nPHASE_BUDGET_EXCEEDED: {len(over)} section(s) over the "
                  f"{args.max_lines}-line budget.", file=sys.stderr)

    return 1 if (args.strict and over) else 0


if __name__ == "__main__":
    raise SystemExit(main())
