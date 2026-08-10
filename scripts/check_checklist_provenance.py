#!/usr/bin/env python3
"""Every vendored checklist must declare what it is, where it came from, and what was checked.

This gate exists because of an audit in which 11 of 15 vendored checklists needed correction.
Four of them were structurally wrong — one was not the instrument it named, one had dropped all
30 of its sub-items, one had renumbered the guideline, one carried a section that exists in no
version of the tool. Two of those four carried a dated **"Verified"** line.

What that taught: a verification claim asserts nothing unless it records *what it was compared
against*. So this gate does not check content — it cannot, because the sources are copyrighted and
cannot ship here (see LICENSES.md). It checks that each file makes four declarations honestly:

  1. VERSION      which edition of the instrument this is
  2. SOURCE       a citation, with a DOI where one exists
  3. LICENCE      the source's licence, or an explicit statement that none was found
  4. VERIFICATION either what it was compared against, or an explicit NOT VERIFIED

A file that says "not verified" passes. A file that says "verified" without naming what it was
compared against FAILS — that is the exact shape that failed twice.

Stdlib only. Usage:
    python3 scripts/check_checklist_provenance.py [--strict] [--dir DIR]

Exit 0 when every file declares all four (or with --strict, exit 1 on any violation).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DIR = ROOT / "skills" / "check-reporting" / "references" / "checklists"

# Header region: declarations must be near the top, where a reader meets them before the items.
HEADER_LINES = 40

# A label may be written "Version:", "**Version:**", "- **Version:**" — accept the notation the
# repository actually uses rather than one canonical spelling. (A checker that accepts only its own
# generator's output is this repository's dominant historical defect.)
def _label(field: str) -> re.Pattern[str]:
    return re.compile(rf"^[-*\s>]*\**\s*{field}\s*\**\s*[:—-]", re.I | re.M)


VERSION_RE = _label("version")
SOURCE_RE = _label("source|citation|reference")
LICENCE_RE = _label("licen[cs]e|licensing|fidelity and licen[cs]e")
DOI_RE = re.compile(r"\b10\.\d{4,9}/\S+", re.I)
# Some instruments genuinely have no DOI — the Newcastle-Ottawa Scale is distributed from an
# institute web page and was never issued one. The requirement is a DOI *or* a statement of why
# there is none; demanding a DOI unconditionally would push someone to invent one.
NO_DOI_EXPLAINED_RE = re.compile(r"no\s+DOI\b|never\s+been\s+issued\s+one|has\s+no\s+DOI", re.I)

# Licence may also be stated inline in a fidelity paragraph rather than as a labelled field.
LICENCE_INLINE_RE = re.compile(
    r"\bCC[ -]?BY(?:[ -]?NC)?(?:[ -]?SA)?\b|\bCC0\b|public domain|no open licence|"
    r"no open license|no Creative Commons|©",
    re.I,
)

# Markdown emphasis lands inside these phrases in real files ("has **not** been compared"),
# so match against a de-emphasised copy. A checker that only accepts its own preferred notation
# is this repository's dominant historical defect — and the first draft of this gate rejected
# four files whose wording was correct, for exactly that reason.
EMPHASIS_RE = re.compile(r"[*_`]+")


def deemphasise(s: str) -> str:
    return re.sub(r"\s+", " ", EMPHASIS_RE.sub("", s))


# A verification CLAIM is the word itself. Bare "compared"/"checked" are ordinary prose — an item
# description reading "when groups are compared" is not a claim about this file, and an earlier
# draft of this gate flagged exactly that. Those verbs count only inside the object pattern below.
VERIFIED_CLAIM_RE = re.compile(r"\bverif(?:ied|ication|y)\b", re.I)
# What makes a claim answerable: it names the artifact compared against.
VERIFIED_OBJECT_RE = re.compile(
    r"\b(?:verif\w*|compared|checked)\b[^.\n]{0,160}?\b(?:against|with|from)\b[^.\n]{0,200}?"
    r"(statement|checklist|table|article|supplement|supplements|PDF|PMC|XML|official|published|source)",
    re.I,
)
NOT_VERIFIED_RE = re.compile(
    r"\bnot\s+been\s+(?:compared|verified|checked)\b|\bnot\s+verified\b|\bunverified\b|"
    r"\bhas\s+not\s+been\s+checked\b|\bneither\s+confirmed\s+nor\s+corrected\b",
    re.I,
)


class Finding:
    __slots__ = ("path", "code", "message")

    def __init__(self, path: Path, code: str, message: str) -> None:
        self.path, self.code, self.message = path, code, message

    def __str__(self) -> str:
        return f"  {self.code:22} {self.path.name}\n{' ' * 26}{self.message}"


def check_file(path: Path) -> list[Finding]:
    text = path.read_text(encoding="utf-8")
    head = "\n".join(text.splitlines()[:HEADER_LINES])
    out: list[Finding] = []

    if not VERSION_RE.search(head):
        out.append(Finding(path, "NO_VERSION", "no Version: declaration in the first "
                                               f"{HEADER_LINES} lines — which edition is this?"))
    if not SOURCE_RE.search(head):
        out.append(Finding(path, "NO_SOURCE", "no Source:/Citation:/Reference: declaration — "
                                              "a file with no named source cannot be audited."))
    elif not DOI_RE.search(head) and not NO_DOI_EXPLAINED_RE.search(deemphasise(head)):
        out.append(Finding(path, "NO_DOI", "a source is cited but carries no DOI. Add one, or state "
                                           "why the instrument has none (e.g. a web-only tool)."))

    if not (LICENCE_RE.search(head) or LICENCE_INLINE_RE.search(head)):
        out.append(Finding(path, "NO_LICENCE", "no licence statement. 'Free to read' is not 'free to "
                                               "reuse'; say which it is, or that none was found."))

    flat = deemphasise(text)
    claims = VERIFIED_CLAIM_RE.search(flat)
    stated = VERIFIED_OBJECT_RE.search(flat)
    disclaims = NOT_VERIFIED_RE.search(flat)
    if not claims and not stated and not disclaims:
        out.append(Finding(path, "NO_VERIFICATION", "says nothing about whether it was ever compared "
                                                    "against the published source. Silence reads as "
                                                    "'verified'. State it either way."))
    elif claims and not disclaims and not stated:
        out.append(Finding(path, "BARE_VERIFIED_CLAIM",
                           "claims verification without naming what it was compared against. Two "
                           "files carried exactly this and were wrong in ten ways between them. "
                           "Write 'verified against <the artifact>'."))
    return out


# ---------------------------------------------------------------------------
# Backlog ratchet.
#
# 46 of 48 files predate this gate and cannot be brought into compliance by
# editing alone: several need a DOI that must be read off the actual article.
# Resolving them automatically was tried and abandoned — a Crossref
# bibliographic query returned a Who's Who biography for NOS, a Letter to the
# Editor for ROBIS, and a code listing for QUADAS-C, all above the similarity
# threshold. Writing those in would have mass-produced the exact defect this
# audit exists to remove.
#
# So the backlog is named here instead. The rules:
#   * a file NOT in this list must satisfy every declaration (new files included)
#   * a file in this list is reported but does not fail the build
#   * the list may only SHRINK — `--audit-backlog` fails if an entry has become
#     compliant and was not removed, so it cannot quietly become a rubber stamp
# ---------------------------------------------------------------------------
BACKLOG: set[str] = set()  # emptied: every checklist now declares itself


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--strict", action="store_true",
                    help="exit 1 on any violation (CI uses this; without it the gate reports only)")
    ap.add_argument("--dir", default=str(DEFAULT_DIR), help="directory of checklist .md files")
    ap.add_argument("--audit-backlog", action="store_true",
                    help="fail if a backlogged file is now compliant and was not removed from the "
                         "list, or if the list names a file that does not exist")
    args = ap.parse_args()

    d = Path(args.dir)
    if not d.is_dir():
        print(f"ERROR: not a directory: {d}", file=sys.stderr)
        return 2

    files = sorted(p for p in d.glob("*.md") if p.name != "README.md")
    if not files:
        # An empty input set is the classic way a gate passes while checking nothing.
        print(f"ERROR: no checklist files found under {d} — refusing to report success.",
              file=sys.stderr)
        return 2

    per_file: dict[str, list[Finding]] = {}
    for p in files:
        per_file[p.name] = check_file(p)

    names = {p.name for p in files}
    stale = sorted(BACKLOG - names)
    cleared = sorted(n for n in BACKLOG & names if not per_file[n])
    if args.audit_backlog:
        problems = []
        if stale:
            problems.append(f"BACKLOG names {len(stale)} file(s) that do not exist: {stale}")
        if cleared:
            problems.append(f"{len(cleared)} backlogged file(s) now comply and must be removed from "
                            f"BACKLOG so the ratchet holds: {cleared}")
        if problems:
            print("BACKLOG_DRIFT")
            for pr in problems:
                print("  " + pr)
            return 1
        print(f"OK: backlog is {len(BACKLOG & names)} file(s); none has silently become compliant.")
        return 0

    findings: list[Finding] = [f for n in sorted(per_file) for f in per_file[n]]
    blocking = [f for f in findings if f.path.name not in BACKLOG]

    print("=" * 41)
    print(" Checklist Provenance")
    print("=" * 41)
    print(f"  scanned: {len(files)} checklist file(s) in {d.relative_to(ROOT) if d.is_relative_to(ROOT) else d}")

    print(f"  backlog: {len(BACKLOG & names)} file(s) predate this gate (reported, not blocking)")

    if not findings:
        print(f"\nOK: all {len(files)} files declare version, source, licence and verification status.")
        return 0

    by_code: dict[str, int] = {}
    for f in findings:
        by_code[f.code] = by_code.get(f.code, 0) + 1
    bad_files = {f.path for f in findings}

    print(f"\n{len(findings)} undeclared item(s) across {len(bad_files)} file(s):\n")
    for f in findings:
        print(f)
    print("\n  " + "  ".join(f"{k}={v}" for k, v in sorted(by_code.items())))
    print("\nThis gate does not read the instrument — the sources are copyrighted and cannot ship")
    print("here. It only requires each file to say what it is and what was checked.")

    if blocking:
        print(f"\n{len(blocking)} of these are in files NOT on the backlog and must be fixed.")
    else:
        print("\nEvery finding is in a backlogged file. No non-backlogged file is undeclared.")
    return 1 if (args.strict and blocking) else 0


if __name__ == "__main__":
    sys.exit(main())
