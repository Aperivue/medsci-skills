#!/usr/bin/env python3
"""A skill may not send its user to a skill that does not exist.

`validate_routing_assets.py` already refuses to let a SKILL.md point at a `references/` file that
is not there. This is its sibling, and it exists because the same failure was happening one level up,
where nothing was looking.

`/meta-analysis` carried this row:

    | Co-author circulation (Phase 9) | `/gws` + `/handoff` | Thread-reply send, deadline task registration |

`/gws` and `/handoff` are the maintainer's **local** skills. They are in `~/.claude/skills`. They
have never been in this package. So every person who installed medsci-skills from npm and reached
Phase 9 of a meta-analysis was told to run two commands that do not exist on their machine — and the
instruction quietly advertised a private toolchain besides. `/lit-sync` did the same with
`/obsidian-paper-vault`.

None of this was a hard problem. Nothing was checking.

And the failure mode generalises past skills: `/lit-sync` also announced that `/verify-refs` blocks
downstream work on a `refs_bib_refreshed: false` flag. `verify_refs.py` has never contained that
string. The sentence describing the gate was the only thing standing between a stale `refs.bib` and
a manuscript — which is the whole disease this audit is about:

    A rule that ships as prose is a rule the model reads and disobeys.

Usage:
    check_named_skills_exist.py [--strict] [--root PATH]

Stdlib only.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# A skill invocation as it is written in these files: `/name`, in backticks or parentheses.
NAMED = re.compile(r"[`(]/([a-z][a-z0-9-]{2,})(?=[`)\s,.;])")
FENCE = re.compile(r"```.*?```", re.DOTALL)

# Slash-tokens that are not skill invocations. Each is a decision someone wrote down, not a shrug —
# the regex over-collects, and an allowlist that explains itself is better than a regex nobody can read.
NOT_A_SKILL = {
    "exp": "Emtree explosion operator in an Embase query (`/exp`)",
    "plain": "the tail of `.md`/plain, describing input formats",
    "submission": "a path fragment, `submission/{journal}/...`",
    "unit-of-analysis": "a bolded phrase in prose, not an invocation",
    "tmp": "a filesystem path",
    "usr": "a filesystem path",
    "home": "a filesystem path",
    "dev": "a filesystem path",
    "opt": "a filesystem path",
    "var": "a filesystem path",
    "etc": "a filesystem path",
    "bin": "a filesystem path",
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--root", type=Path, default=ROOT)
    a = ap.parse_args()

    skills_dir = a.root / "skills"
    shipped = {d.name for d in skills_dir.iterdir() if (d / "SKILL.md").is_file()}

    bad: list[tuple[str, int, str, str]] = []
    for md in sorted(skills_dir.glob("*/SKILL.md")):
        text = FENCE.sub(lambda m: "\n" * m.group(0).count("\n"), md.read_text(encoding="utf-8", errors="ignore"))
        for i, line in enumerate(text.splitlines(), 1):
            for m in NAMED.finditer(line):
                name = m.group(1)
                if name in shipped or name in NOT_A_SKILL:
                    continue
                bad.append((md.parts[-2], i, name, line.strip()[:96]))

    if not bad:
        print(f"OK: every skill named by a SKILL.md is one of the {len(shipped)} this package ships.")
        return 0

    print(f"SKILL_DOES_NOT_EXIST: {len(bad)} reference(s) to a skill this package does not ship.\n")
    for skill, line, name, text in bad:
        print(f"  skills/{skill}/SKILL.md:{line}  ->  /{name}")
        print(f"      {text}")
    print(
        "\nA user who installs this package from npm has exactly the skills in `skills/`. They do not\n"
        "have whatever is in the maintainer's `~/.claude/skills`. Telling them to run one is an\n"
        "instruction they cannot follow, and it advertises a private toolchain besides.\n"
        "\nEither ship the skill, name one that exists, or cut the sentence.\n"
        "If the token is not a skill invocation at all — an Embase `/exp`, a path fragment — add it to\n"
        "NOT_A_SKILL in this script WITH THE REASON, so that the exemption is a decision rather than\n"
        "a hole.\n"
    )
    return 1 if a.strict else 0


if __name__ == "__main__":
    sys.exit(main())
