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

THE WHOLE FILE IS ALSO A BILL. A per-section budget bounds the parts and says
nothing about the sum: a SKILL.md can hold thirty compliant sections and still
cost twenty thousand tokens on every invocation. On 2026-07-25 self-review was
1,132 lines / ~21,900 tokens and peer-review ~20,200 with every section inside
the 80-line budget. So this gate also enforces a whole-file budget.

It counts TOKENS, not lines, because lines are the wrong unit and the repo has
the counter-example: peer-review at 604 lines cost ~20,200 tokens while
make-figures at 930 lines cost ~11,900. Judged by lines, make-figures looks like
the second-worst file; judged by what the user actually pays, it is fifth, and a
line budget would have sent the work to the wrong file. Dense tables cost 33
tokens per line, prose costs 12.

--max-file-tokens is a RATCHET, not a target: it sits just above the largest
SKILL.md we have accepted after extraction, so nothing can grow past today's
worst without a deliberate decision. It is not a statement that 16,000 tokens is
a reasonable size for a skill -- the median SKILL.md is ~2,800. Tightening it is
its own decision, taken deliberately; it should never loosen.

The estimate is characters/4, the standard English rough count. It is a
proportional measure used against a threshold set with the same measure, so its
absolute error does not matter to the comparison.

Top-level `scripts/` validator (not a `skills/*/scripts/` detector) -- it audits
the context budget of the skill surface, not a manuscript, so it is NOT part of
the MedSci-Audit detector count.

Usage:
  python3 scripts/check_phase_budget.py --strict
  python3 scripts/check_phase_budget.py --max-lines 80 --json
  python3 scripts/check_phase_budget.py --max-file-tokens 16000 --strict
  python3 scripts/check_phase_budget.py --skills-dir <dir> --strict
Exit: 0 when every section AND every file is within budget (or exempt); with
--strict, 1 on any over-budget section or file; 2 on a read error.
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

# Whole-file exemptions. Key is the skill name, value is the reason AND the plan -- an exemption
# without a plan is how a deferral becomes permanent.
FILE_EXEMPT: dict[str, str] = {}

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
    ap.add_argument("--max-file-tokens", type=int, default=16000,
                    help="maximum estimated tokens for a whole SKILL.md (default: 16000, a ratchet "
                         "just above the largest accepted file -- not a target; the median is ~2,800)")
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
        files_over: list[dict[str, object]] = []
        files_exempted: list[dict[str, object]] = []
        for md in skill_mds:
            skill = md.parent.name
            scanned += 1

            text = md.read_text(encoding="utf-8")
            est_tokens = len(text) // 4
            if est_tokens > args.max_file_tokens:
                frec: dict[str, object] = {
                    "skill": skill,
                    "est_tokens": est_tokens,
                    "lines": len(text.splitlines()),
                    "budget": args.max_file_tokens,
                    "over_by": est_tokens - args.max_file_tokens,
                }
                if skill in FILE_EXEMPT:
                    frec["reason"] = FILE_EXEMPT[skill]
                    files_exempted.append(frec)
                else:
                    files_over.append(frec)

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
    files_over.sort(key=lambda r: -int(r["est_tokens"]))
    if over and files_over:
        verdict = "PHASE_AND_FILE_BUDGET_EXCEEDED"
    elif files_over:
        verdict = "FILE_BUDGET_EXCEEDED"
    elif over:
        verdict = "PHASE_BUDGET_EXCEEDED"
    else:
        verdict = "OK"

    if args.json:
        print(json.dumps(
            {
                "verdict": verdict,
                "budget": args.max_lines,
                "file_budget_tokens": args.max_file_tokens,
                "skills_scanned": scanned,
                "sections_scanned": total,
                "over_budget": over,
                "exempt": exempted,
                "files_over_budget": files_over,
                "files_exempt": files_exempted,
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

        print(f"\nWhole-file budget: {args.max_file_tokens} estimated tokens per SKILL.md "
              f"({len(files_exempted)} exempt).")
        for rec in files_exempted:
            print(f"  exempt: {rec['skill']} (~{rec['est_tokens']} tokens) -- {rec['reason']}")
        if files_over:
            print("\nOVER FILE BUDGET -- this is what the user pays to invoke the skill at all,\n"
                  "before a single line of it is known to be relevant:\n")
            for rec in files_over:
                print(f"  ~{int(rec['est_tokens']):6} tokens (+{rec['over_by']} over)  "
                      f"{rec['skill']}/SKILL.md  ({rec['lines']} lines)")
            print("\n  Move the CONDITIONAL blocks to references/ behind a trigger row -- the ones\n"
                  "  needed only after the ask is known (an opt-in flag's phase, a study-type\n"
                  "  branch, an output-format template). Control flow stays. Extract by moving the\n"
                  "  body verbatim; a retyped phase is how a phase quietly changes meaning.\n"
                  "  A file that genuinely cannot be split goes in FILE_EXEMPT with a reason AND a\n"
                  "  plan -- an exemption without a plan is how a deferral becomes permanent.")
            print(f"\nFILE_BUDGET_EXCEEDED: {len(files_over)} SKILL.md over the "
                  f"{args.max_file_tokens}-token budget.", file=sys.stderr)

    return 1 if (args.strict and (over or files_over)) else 0


if __name__ == "__main__":
    raise SystemExit(main())
