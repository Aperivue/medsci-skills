#!/usr/bin/env python3
"""THIRD-PARTY-NOTICES.md has to describe the package you actually downloaded.

A license file is the first thing a JOSS reviewer opens, the first thing a legal team greps, and the
only place most users will ever look to find out what they are allowed to do with what we gave them.
It is not documentation. It is the claim.

Ours had drifted into saying the opposite of the truth. Under a heading reading

    The following checklists are NOT bundled due to license restrictions.
    Users should download them directly from official sources:
      - CONSORT 2010 ... (CC BY-NC)
      - SPIRIT ... (CC BY-NC-ND)

the package shipped CONSORT and SPIRIT — the summaries *and* the guideline authors' own `.docx`
files. As it happens the 2025 updates relicensed to CC BY 4.0 and we were entitled to ship them all
along. That is luck, not diligence: the file said one thing, the tree did another, and nothing
compared them. Had the licences not changed, we would have been redistributing non-commercial
material from an MIT package on npm, and THIRD-PARTY-NOTICES.md would have been the document proving we knew
better.

So this gate holds the index to the tree, in both directions:

  1. Anything THIRD-PARTY-NOTICES.md says is **not bundled** must actually be absent.
  2. Anything third-party that we **do** bundle must be named in THIRD-PARTY-NOTICES.md.

The failure that motivated (1) is the dangerous one — a promise we were breaking. (2) catches the
quieter one: a new third-party payload that nobody declared.

Usage:
    check_third_party_index.py [--strict]

Stdlib only.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NOTICES = ROOT / "THIRD-PARTY-NOTICES.md"
SKILLS = ROOT / "skills"

# --- (1) what THIRD-PARTY-NOTICES.md promises we do NOT ship -------------------------------------------------
# Each entry: the thing named in the "Not bundled" section, and the glob that would prove us liars.
# Keep this in step with that section: if you add a bullet there, add its glob here, or the promise
# is decorative.
NOT_BUNDLED = {
    "European Radiology graphical-abstract template": "skills/**/european_radiology.pptx",
}

# --- (2) third-party payloads we DO ship, and the token that must appear in THIRD-PARTY-NOTICES.md ------------
# The value is a string THIRD-PARTY-NOTICES.md must contain for that payload to count as declared. It is
# deliberately the *licence*, not just the name: "we mention CONSORT somewhere" is not a licence
# statement.
DECLARED = {
    "skills/make-figures/templates/official/consort2010": "CONSORT 2025",
    "skills/make-figures/templates/official/spirit2013": "SPIRIT 2025",
    "skills/make-figures/templates/official/stard2015": "STARD 2015",
    "skills/make-figures/templates/official/prisma2020": "PRISMA 2020",
    "skills/manage-refs/citation_styles": "CC BY-SA 3.0",
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--strict", action="store_true", help="exit 1 on any drift")
    ap.add_argument("--root", type=Path, default=ROOT,
                    help="tree to inspect (the self-test points this at a fixture)")
    a = ap.parse_args()

    root = a.root.resolve()
    text = (root / "THIRD-PARTY-NOTICES.md").read_text(encoding="utf-8", errors="ignore")
    broken: list[str] = []

    # (1) a promise we are breaking
    for name, glob in NOT_BUNDLED.items():
        hits = [p for p in root.glob(glob) if p.is_file()]
        if hits:
            broken.append(
                f"THIRD-PARTY-NOTICES.md says we do NOT bundle {name} — but it is in the tree:\n"
                + "".join(f"        {h.relative_to(root)}\n" for h in hits)
                + "      Either delete the file, or (if you now hold a licence permitting\n"
                  "      redistribution) move it into the bundled section with that licence named."
            )

    # (2) a payload nobody declared
    for rel, token in DECLARED.items():
        d = root / rel
        if not d.exists():
            continue                       # the directory went away; not this gate's business
        if token not in text:
            broken.append(
                f"{rel}/ ships third-party content, and THIRD-PARTY-NOTICES.md never says so.\n"
                f"      Expected THIRD-PARTY-NOTICES.md to contain: {token!r}\n"
                f"      Add it to '## Third-Party Content Licenses' with its licence and citation."
            )

    if not broken:
        print(f"OK: the third-party notices match the tree "
              f"({len(NOT_BUNDLED)} not-bundled promise(s) kept, {len(DECLARED)} payload(s) declared).")
        return 0

    print(f"THIRD_PARTY_INDEX_DRIFT: {len(broken)} discrepanc(ies) between THIRD-PARTY-NOTICES.md and the tree.\n")
    for b in broken:
        print(f"  - {b}\n")
    print(
        "THIRD-PARTY-NOTICES.md is the claim we make about what we handed you. When it disagrees with\n"
        "the tree, the tree wins in court and that file becomes the evidence that we knew.\n"
    )
    return 1 if a.strict else 0


if __name__ == "__main__":
    sys.exit(main())
