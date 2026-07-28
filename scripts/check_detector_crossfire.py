#!/usr/bin/env python3
"""A fixture that is clean for ONE detector must be clean for ALL of them.

Every detector in this repo is tested against fixtures built to its own model of the world. That
leaves a gap no existing test can see: two detectors can each be right alone and contradict each
other in the pair.

That is not hypothetical. It shipped:

    check_slide_tells called a text block an "arrow label" only if it was <= 18 pt.
    check_deck_budget demanded >= 20 pt so the back row could read it.

So a legible 20-pt arrow label satisfied the budget check and was INVISIBLE to the arrow check, and
a well-made slide was reported as having unlabelled arrows. Neither detector was wrong on its own.
One detector's advisory threshold had quietly become another's definition of a category, and
nothing in the repo ever looked at the two together.

This gate looks at them together. It takes the fixtures this project already ships as its own
picture of good work -- the three demo manuscripts and the clean decks the challenge cards build --
and runs EVERY detector of the matching family across ALL of them. Any finding is a failure,
because one of two things is true and a human has to say which:

    the detector is over-firing on good work, or
    the demo is defective.

Both are worth a red build. A detector that fires on good work gets switched off, and it takes the
honest detectors down with it.

WHAT THIS DOES NOT DO
    It does not judge a detector's thresholds, and it does not re-test what the challenge cards
    already prove (that each detector FIRES on its own planted defect). It asserts one thing only:
    silence on good work, across the whole family.

HOW IT LEARNS TO INVOKE A DETECTOR
    From the detector's own --help, never from a guess. Two rules, both paid for:

    1. NEVER pass an output flag (--out / --json / --report). Both deck detectors take `--json
       PATH`; four self-review detectors take `--json` as a BOOLEAN. A scanner that guessed at
       these once overwrote 31 fixtures. This gate passes inputs only.
    2. Run with cwd inside a temp dir. Passing no output flag is not enough -- some detectors write
       a DEFAULT report path (`qc/...`) relative to the working directory. Discovered by watching
       one of them create `qc/` in the repo.

    Belt and braces: every fixture is hashed before and after, and a changed fixture fails the run.

THE SEVERITY BAR (why it differs by family, and why that is not a fudge)
    Manuscript detectors encode "is this actually a problem?" in their DEFAULT exit code: an
    advisory (a `warn`, a `soft`) exits 0 on purpose, a blocking finding exits 1. The bar is
    therefore the detector's own default verdict. A demo using Vancouver `[1]` citations draws a
    `bare_numeric_cite` warn and the detector deliberately does not fail -- neither do we.

    Deck detectors are documented to exit 0 EVEN WHEN THEY FIND MARKS ("0 clean (or findings
    without --strict)"). Their exit code is useless as a verdict, so the bar is `--strict`, which
    is exactly the bar the two challenge cards already hold their clean decks to.

    In both cases the bar is the detector's own answer to "is this good work?", not one this gate
    invents.

Usage:
    check_detector_crossfire.py [--verbose]

Exit: 0 all silent, 1 a detector fired on good work (or zero pairs ran), 2 the harness broke.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

REPO = Path(__file__).resolve().parent.parent

# Detectors live here and only here -- the same glob the catalog uses.
DETECTOR_GLOBS = ("check_*.py", "detect_*.py", "derive_*.py")

# The manuscripts this project ships as its own picture of good work.
DEMO_MANUSCRIPTS = (
    "demo/01_wisconsin_bc/manuscript/manuscript.md",
    "demo/02_metafor_bcg/manuscript/manuscript.md",
    "demo/03_nhanes_obesity/manuscript/manuscript.md",
)

# The challenge cards that BUILD decks (they are binaries; they are never committed).
DECK_BUILDERS = (
    "skills/present-paper/scripts/check_slide_tells_challenge/make_fixtures.py",
    "skills/present-paper/scripts/check_deck_budget_challenge/make_fixtures.py",
)

# Only the CLEAN decks belong here. tells / bloated / tiny_type are planted defects -- the positive
# half of their cards -- and a detector is SUPPOSED to fire on them. Naming the clean decks
# explicitly (rather than "everything the builders wrote") is what keeps a planted defect from
# wandering into the negative fixture and training us to expect noise.
#
# The room each deck was built for is ground truth, lifted from the challenge cards' own verify.sh:
#   academic.pptx -> --archetype conference_oral --minutes 10
#   keynote.pptx  -> --archetype keynote --minutes 20
# clean.pptx is not covered by any card. It is built as an academic talk -- its own fixture source
# sizes the arrow label at 20 pt and says so: "check_deck_budget's floor for an academic room is
# 20 pt, and it was right to say so." So it is judged in that room. That pairing -- the budget
# detector against the slide-tells card's deck -- is a pair NOTHING in this repo runs today.
CLEAN_DECKS: Dict[str, Tuple[str, str]] = {
    "clean.pptx": ("conference_oral", "10"),
    "academic.pptx": ("conference_oral", "10"),
    "keynote.pptx": ("keynote", "20"),
}

# Flags that are OUTPUTS. This gate never passes one. See the header: guessing here cost 31
# fixtures. The list is deliberately broad -- a false skip is cheap, a clobbered fixture is not.
OUTPUT_FLAGS = ("--out", "--json", "--report", "--outfile", "--output")


@dataclass
class Detector:
    path: Path
    name: str
    usage: str
    family: str  # "manuscript" | "deck" | "other"


def sh(cmd: List[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, cwd=str(cwd), timeout=120)


def read_usage(p: Path) -> str:
    try:
        r = subprocess.run(["python3", str(p), "--help"], capture_output=True, text=True, timeout=60)
    except Exception:
        return ""
    return r.stdout or r.stderr or ""


def classify(p: Path) -> Detector:
    """Family comes from the detector's own --help, so a new detector is picked up for free."""
    help_text = read_usage(p)
    m = re.search(r"usage:(.*?)(?:\n\n|\npositional|\noptions|\noptional)", help_text, re.S)
    usage = " ".join(m.group(1).split()) if m else ""

    family = "other"
    # A deck detector takes a .pptx as its subject. Both name the positional `deck`.
    if re.search(r"\bdeck\b", usage):
        family = "deck"
    elif "--manuscript" in help_text:
        family = "manuscript"
    return Detector(path=p, name=p.stem, usage=usage, family=family)


def discover() -> List[Detector]:
    seen = {
        p
        for g in DETECTOR_GLOBS
        for p in (REPO / "skills").glob(f"*/scripts/{g}")
        if "_challenge" not in str(p)
    }
    return sorted((classify(p) for p in seen), key=lambda d: d.name)


def missing_flag_from(stderr: str, stdout: str, supplied: Tuple[str, ...]) -> str:
    """Let the detector name its own missing input. We do not guess it.

    Anything we already handed it is not what it is missing -- naming `--manuscript` as the missing
    flag when we just passed `--manuscript` would make the skip line a lie.
    """
    blob = (stderr or "") + "\n" + (stdout or "")
    ignore = set(OUTPUT_FLAGS) | {"--strict", "--quiet", "--help"} | set(supplied)
    out: List[str] = []
    for f in re.findall(r"(--[a-z][a-z0-9-]+)", blob):
        if f not in ignore and f not in out:
            out.append(f)
    return " / ".join(out[:3]) if out else "an input this fixture cannot supply"


def hash_tree(paths: List[Path]) -> Dict[str, str]:
    return {
        str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths if p.is_file()
    }


def build_decks(into: Path) -> List[Path]:
    for b in DECK_BUILDERS:
        r = subprocess.run(
            ["python3", str(REPO / b), str(into)], capture_output=True, text=True, timeout=180
        )
        if r.returncode != 0:
            print(f"harness: deck builder failed: {b}\n{r.stderr}", file=sys.stderr)
            raise SystemExit(2)
    decks = []
    for name in CLEAN_DECKS:
        d = into / name
        if not d.is_file():
            print(f"harness: challenge card did not produce {name}", file=sys.stderr)
            raise SystemExit(2)
        decks.append(d)
    return decks


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--verbose", action="store_true", help="print every pair, not just failures")
    a = ap.parse_args(argv)

    dets = discover()
    if not dets:
        print("harness: found no detectors at all", file=sys.stderr)
        return 2

    manuscripts = [REPO / m for m in DEMO_MANUSCRIPTS]
    for m in manuscripts:
        if not m.is_file():
            print(f"harness: missing demo manuscript {m}", file=sys.stderr)
            return 2

    work = Path(tempfile.mkdtemp(prefix="crossfire-"))
    try:
        deck_dir = work / "decks"
        deck_dir.mkdir()
        decks = build_decks(deck_dir)

        # Everything the detectors are about to read. If any byte of it changes, a detector wrote
        # into a fixture and the run is void regardless of verdicts.
        guarded = manuscripts + decks
        before = hash_tree(guarded)

        fired: List[str] = []
        skipped: List[str] = []
        ran = 0

        print("=" * 78)
        print(" Detector crossfire -- every detector against every clean fixture of its family")
        print("=" * 78)

        # ---- manuscript family -------------------------------------------------------------
        for d in [x for x in dets if x.family == "manuscript"]:
            for ms in manuscripts:
                sandbox = Path(tempfile.mkdtemp(dir=work))  # default `qc/...` lands HERE
                # Inputs only. No output flag, ever.
                cmd = ["python3", str(d.path), "--manuscript", str(ms)]
                r = sh(cmd, cwd=sandbox)
                label = f"{d.name} x {ms.parent.parent.name}"

                if r.returncode == 2:
                    # The detector refused to run: it needs a companion input the fixture has not
                    # got. Say so BY NAME -- a silent no-op is worse than no test.
                    need = missing_flag_from(r.stderr, r.stdout, ("--manuscript",))
                    skipped.append(f"{d.name} (needs {need})")
                    break  # same verdict for all three; do not repeat it
                ran += 1
                if r.returncode == 0:
                    if a.verbose:
                        print(f"  ok    {label}")
                else:
                    fired.append(label)
                    print(f"  FIRED {label}")
                    for line in (r.stdout or r.stderr).strip().splitlines()[-6:]:
                        print(f"          | {line}")

        # ---- deck family -------------------------------------------------------------------
        for d in [x for x in dets if x.family == "deck"]:
            for deck in decks:
                archetype, minutes = CLEAN_DECKS[deck.name]
                sandbox = Path(tempfile.mkdtemp(dir=work))
                cmd = ["python3", str(d.path), str(deck)]
                # Only pass a flag the detector actually declares. Learned from --help, not guessed.
                if "--archetype" in d.usage:
                    cmd += ["--archetype", archetype]
                if "--minutes" in d.usage:
                    cmd += ["--minutes", minutes]
                # Deck detectors exit 0 even when they find marks; --strict is their verdict.
                cmd += ["--strict"]
                r = sh(cmd, cwd=sandbox)
                label = f"{d.name} x {deck.name}"

                if r.returncode == 2:
                    need = missing_flag_from(r.stderr, r.stdout,
                                             ("--archetype", "--minutes"))
                    skipped.append(f"{d.name} (needs {need})")
                    break
                ran += 1
                if r.returncode == 0:
                    if a.verbose:
                        print(f"  ok    {label}")
                else:
                    fired.append(label)
                    print(f"  FIRED {label}")
                    for line in (r.stdout or r.stderr).strip().splitlines()[:8]:
                        print(f"          | {line}")

        after = hash_tree(guarded)
        changed = [k for k in before if before[k] != after.get(k)]

        # ---- the accounting has to be honest ------------------------------------------------
        print("-" * 78)
        for s in sorted(set(skipped)):
            print(f"  SKIPPED: {s}")
        others = [x.name for x in dets if x.family == "other"]
        if others:
            print(
                f"  OUT-OF-FAMILY ({len(others)}): these take neither a manuscript nor a deck "
                f"(data / manifest / code / bib inputs) and are not in scope for this gate:"
            )
            print("    " + ", ".join(sorted(others)))
        print("-" * 78)
        print(f"  pairs run: {ran}")

        if changed:
            print("\nFAIL: a detector WROTE INTO A FIXTURE. The run is void.", file=sys.stderr)
            for c in changed:
                print(f"  modified: {c}", file=sys.stderr)
            return 1

        if ran == 0:
            print(
                "\nFAIL: zero (detector x fixture) pairs ran. A test that silently exercises "
                "nothing is worse than no test at all.",
                file=sys.stderr,
            )
            return 1

        if fired:
            print(
                f"\nFAIL: {len(fired)} pair(s) fired on this project's own picture of good work.\n"
                "Either the detector is over-firing, or the demo is defective. A human must say\n"
                "which -- do not silence the detector to make this green.",
                file=sys.stderr,
            )
            return 1

        print(f"\nOK: {ran} pairs, no detector fired on good work.")
        print(
            "\n  What this does NOT prove. Silence here means no detector CONTRADICTS another's\n"
            "  picture of good work. It does not mean a detector was exercised: a check that only\n"
            "  fires on a Cox model whose outcome is declared pages away will be silent on a corpus\n"
            "  of short papers with compact Methods — and that silence looks exactly like a pass.\n"
            "  Detector #66 shipped on that reading: it matched three reviewer comments on the\n"
            "  manuscript that motivated it, and then flagged a well-written paper for the same\n"
            "  reason, because it was reading LAYOUT, not defect. It had to be corrected hours later.\n"
            "\n  So this gate is a FALSE-POSITIVE GUARD, not a coverage guarantee. A new detector\n"
            "  still owes what no shippable corpus can supply: **two real manuscripts, at least one\n"
            "  of them known-good**, and a PR body saying what the false-positive hunt found. Finding\n"
            "  none is a claim to be suspicious of, not a badge."
        )
        return 0
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
