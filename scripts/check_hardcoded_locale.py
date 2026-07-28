#!/usr/bin/env python3
"""No skill gets to decide what language its user speaks.

This toolkit is downloaded from npm, installed from a classroom ZIP, and starred by people in
countries its maintainer has never been to. And two of its skills opened by telling the model:

    skills/humanize/SKILL.md:17         "Communicate with the user in Korean."
    skills/polish-language/SKILL.md:20  "Conversation with the user may be in Korean."

Every user of `/humanize`, anywhere, was being addressed in a language chosen for them by a file
they never read. The correct sentence was already in the repo — `/publish-skill` says
*"Communicate with the user in their preferred language"* — so this was not a hard problem anyone
had failed to solve. It was a rule nobody was checking.

And here is the part worth sitting with. `/publish-skill`, the skill whose entire job is to scrub a
personal skill before it goes public, **lists this exact defect**:

    6. **Language hardcoding** ("in Korean", "한국어로", "in Japanese", "in Chinese")

The rule existed. It was written down. It was written down *in the skill responsible for enforcing
it*. And the repository shipped two violations of it for months, because the rule was a **sentence**
and nothing executed it.

    A rule that ships as prose is a rule the model reads and disobeys.
    The difference between the rules that held and the one that did not was not importance.
    It was executability.

So this is that sentence, executed.

What is allowed: naming a language as the *subject* of the work — "manuscript edits are in English",
"medical terminology stays in English", the locale inventory, a translated `_ko` reference file. The
defect is narrow and specific: **instructing the model which human language to address the USER in.**

Usage:
    check_hardcoded_locale.py [--strict] [--root PATH]

Stdlib only.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# "talk to the user" + a named language. Both halves are required: a skill may certainly say that
# the MANUSCRIPT is in English. It may not say which language the PERSON gets.
ADDRESSING_USER = r"(communicat\w*|convers\w*|speak\w*|respond\w*|repl\w*|talk\w*|address\w*|answer\w*|interact\w*|report\w*)"
NAMED_LANGUAGE = (r"(korean|한국어|japanese|일본어|chinese|중국어|mandarin|spanish|french|german|"
                  r"portuguese|italian|russian|arabic|hindi|vietnamese|thai)")

# The whole sentence, so that "in their preferred language" is visibly a different thing.
HARDCODE = re.compile(
    rf"\b{ADDRESSING_USER}\b[^.\n]{{0,60}}?\b(?:with|to|the)?\s*(?:the\s+)?user[^.\n]{{0,40}}?\bin\s+{NAMED_LANGUAGE}\b",
    re.IGNORECASE,
)
# ...and the terser form, "- Communicate in Korean."
HARDCODE_TERSE = re.compile(
    rf"^\s*[-*]?\s*{ADDRESSING_USER}\b[^.\n]{{0,30}}?\bin\s+{NAMED_LANGUAGE}\b",
    re.IGNORECASE | re.MULTILINE,
)

# A skill may quote the defect in order to TEACH it. `/publish-skill` does exactly that — it lists
# "Language hardcoding" among the things to scrub, and it prints the replacement:
#
#     - Replace: `"in Korean"` / `"한국어로"` → `"in the user's preferred language"`
#
# The first draft of this gate fired on that line. It flagged the one file in the repository that
# had already got this right, for the crime of saying so. A gate that fires on good work gets
# switched off, and it takes the honest gates with it.
#
# So: a line that names the defect alongside its cure is naming it, not committing it. The tell is
# that the correct form appears on the same line.
TEACHING = re.compile(
    r"(language hardcoding|do not hardcode|never hardcode|scrub|PII audit|forbidden"
    r"|preferred language|user's language|→|->|Replace:|instead of)",
    re.IGNORECASE,
)

FENCE = re.compile(r"```.*?```", re.DOTALL)


def offences(md: Path) -> list[tuple[int, str]]:
    text = FENCE.sub(lambda m: "\n" * m.group(0).count("\n"), md.read_text(encoding="utf-8", errors="ignore"))
    out: list[tuple[int, str]] = []
    for i, line in enumerate(text.splitlines(), 1):
        if not (HARDCODE.search(line) or HARDCODE_TERSE.search(line)):
            continue
        if TEACHING.search(line):
            continue                       # this line is naming the defect, not committing it
        out.append((i, line.strip()))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--root", type=Path, default=ROOT)
    a = ap.parse_args()

    skills = sorted((a.root / "skills").glob("*/SKILL.md"))
    bad: list[tuple[Path, int, str]] = []
    for md in skills:
        for line, text in offences(md):
            bad.append((md, line, text))

    if not bad:
        print(f"OK: none of the {len(skills)} skills picks a human language for its user.")
        return 0

    print(f"HARDCODED_LOCALE: {len(bad)} skill line(s) choose the user's language for them.\n")
    for md, line, text in bad:
        print(f"  {md.relative_to(a.root)}:{line}")
        print(f"      {text}")
    print(
        "\nThis toolkit ships on npm and is used by people the maintainer has never met. A skill does\n"
        "not get to decide what language they speak.\n"
        "\nThe sentence that works is already in the repo — /publish-skill uses it:\n"
        "\n    - Communicate with the user in their preferred language.\n"
        "\nNaming a language as the SUBJECT of the work is fine and stays fine: \"manuscript edits are\n"
        "in English\", \"medical terminology stays in English\". The defect is narrow — telling the model\n"
        "which language to address the PERSON in.\n"
    )
    return 1 if a.strict else 0


if __name__ == "__main__":
    sys.exit(main())
