#!/usr/bin/env python3
"""Is this deck the right shape for the room it is going into?

Forty words on a slide is a normal academic slide and a catastrophic keynote slide. Thirty slides is
right for a fifty-minute lecture and fatal for a ten-minute oral abstract. There is no universal
threshold for "too much text" — there is only too much text *for this podium*, which is why this
takes an archetype instead of pretending one number fits every room.

It checks the things about a deck that are mechanical, and therefore checkable:

  DECK_OVER_BUDGET    slides against the clock. A 40-slide deck for a 10-minute oral is not a
                      style choice; it is a talk that will be cut off at the microphone.
  SLIDE_TOO_DENSE     words on a slide, against what this archetype's audience can absorb while
                      also listening to you. A keynote audience is not reading.
  TYPE_TOO_SMALL      the back row exists. Below the floor, the slide is decoration.
  ZERO_AREA_TEXT      text sitting in a box with no width or no height. Nothing below can measure
                      it, so the three checks above are unreliable until it is fixed — and a deck
                      in this state passes them by being unreadable rather than by being right.

The clock stops at the backup section. Nearly every conference deck carries one — the slides you
do not present, and open only if someone asks. Counting them against the clock told people to
delete their Q&A preparation, so the check was wrong in the one place a speaker most needs to be
prepared. A slide whose headline IS "Backup", "Appendix", "Q&A", "Reserve" or "Supplementary" (the
whole first line: "Backup slides" and "Backup — Q&A" count, "Appendix perforation in children"
does not) ends the talk: everything from there on is off the clock. Slides are taken in the order
they are shown (presentation.xml), and the output says where the clock stopped; --backup-from N
sets the boundary explicitly when a divider says something else.

Density and type size still apply to those slides. Anything you might put on a screen has to be
readable when it gets there; a backup slide is shown under questioning, which is the worst possible
moment to discover it is a wall of 11-point text.

Everything else about an archetype — whether the argument opens with its answer, whether the case is
a pretext, whether the limitation is the one that matters — is judgment, and is in
`references/presentation_archetypes.md` where a person can act on it.

Stdlib only. Reads the .pptx as the ZIP of XML it is.

Usage:
    check_deck_budget.py deck.pptx --archetype conference_oral --minutes 10 [--backup-from N]
                         [--json out.json] [--strict]
    check_deck_budget.py --list
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional
from xml.etree import ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_slide_tells import is_page_number, read_deck, unmeasurable_text_shapes  # noqa: E402

DETECTOR = "check_deck_budget"


@dataclass(frozen=True)
class Budget:
    label: str
    slides_per_minute: float  # the pace the room can take
    words_median: int  # typical content slide
    words_max: int  # the worst slide you are allowed
    min_pt: int  # the back row
    note: str


# The table at the top of references/presentation_archetypes.md, made executable.
BUDGETS: Dict[str, Budget] = {
    "conference_oral": Budget(
        "Conference oral (society meeting, oral abstract)", 1.0, 40, 60, 20,
        "One finding, defensibly, in the time you were given. Roughly a slide a minute."),
    "critique": Budget(
        "Journal club / critique", 1.0, 50, 70, 20,
        "The paper is the specimen; the appraisal is yours."),
    "case_anchored": Budget(
        "Grand rounds / tumour board", 1.0, 45, 65, 20,
        "The patient carries the argument."),
    "didactic": Budget(
        "Lecture / didactic", 0.7, 40, 70, 20,
        "A slide should survive several minutes of talking. They will study from it."),
    "defence": Budget(
        "Thesis defence / job talk", 1.0, 45, 65, 20,
        "They are deciding about you. The limitations slide is your best slide."),
    "keynote": Budget(
        "Keynote / big idea", 3.0, 12, 20, 40,
        "They came to be moved, and they are not taking notes. The slide is punctuation."),
    "lay_talk": Budget(
        "Public / lay audience", 2.0, 12, 20, 32,
        "One true idea they can repeat to someone tonight."),
    "decision_brief": Budget(
        "Investors / grant panel / steering committee", 1.0, 25, 40, 30,
        "Answer first. The deck read as titles alone must be the whole argument."),
}


# The boundary the last audit() used (0-based index or None), so main() can say where the clock
# stopped instead of leaving the user to guess why a long deck passed.
LAST_BOUNDARY: List[Optional[int]] = [None]


@dataclass
class Finding:
    detector: str
    verdict: str
    slide: Optional[int]
    summary: str
    evidence: List[str]


def words_on(shapes) -> int:
    n = 0
    for s in shapes:
        if s.is_chrome or is_page_number(s.text) or not s.text:
            continue
        n += len(s.text.split())
    return n


_BACKUP_KW = (r"(?:back[\s-]?up|appendix|q\s*&\s*a|q\s*and\s*a|reserve|supplement(?:ary)?"
              r"|백업|부록|예비)")
_BACKUP_TAIL = r"(?:slides?|section|materials?|자료|슬라이드)"
# The WHOLE first line must be a signpost: the keyword, optionally a section word ("Backup
# slides", "백업 슬라이드") or a designator ("Appendix A"), then either nothing but punctuation or a
# separator and a subtitle ("Backup — Q&A"). Matching only the start made every headline that
# opens with one of these words a boundary — "Appendix perforation in children", "Supplementary
# oxygen did not help", "Reserve capacity predicts survival", "예비 연구 결과" — and the clock
# stopped at slide 2.
_BACKUP_RE = re.compile(
    rf"^\W*{_BACKUP_KW}(?:\s+{_BACKUP_TAIL})?(?:\s+(?:[A-Z]|\d{{1,2}}|[IVX]{{1,4}}))?"
    r"(?:\W*$|\s*[:|·/–—(&-].*$)",
    re.I)


def is_backup_signpost(line: str) -> bool:
    head = line.strip()
    return bool(head) and len(head.split()) <= 6 and bool(_BACKUP_RE.match(head))


def find_backup_boundary(slides) -> Optional[int]:
    """Index of the first backup slide, or None. Everything from there on is off the clock.

    A backup section opens with a marker slide -- a divider or a heading that says "Backup",
    "Appendix", "Q&A". We look for that *headline*, and we require the whole headline to be the
    signpost: a slide whose body happens to discuss "the appendix of the guideline" is not a
    boundary, and neither is a finding that merely starts with the word ("Appendix perforation in
    children", "Supplementary oxygen did not help").

    Headline means the shape's FIRST LINE, not its whole text. A section divider normally carries
    its title and its subtitle in one text frame, so the shape reads

        "Backup\nQ&A -- the four questions this design invites"

    and a guard that measured the whole text threw the boundary away for being ten words long.
    That is not hypothetical: it is how this check failed the first real deck it met.

    When a deck's divider says something else, pass --backup-from N instead of renaming it.
    """
    for i, shapes in enumerate(slides):
        for s in shapes:
            head = next((ln.strip() for ln in (s.text or "").splitlines() if ln.strip()), "")
            if is_backup_signpost(head):
                return i
    return None


def audit(deck: Path, archetype: str, minutes: float,
          backup_from: Optional[int] = None) -> List[Finding]:
    from check_slide_tells import mark_chrome  # noqa: PLC0415

    b = BUDGETS[archetype]
    slides, _notes, _w, h = read_deck(deck)
    mark_chrome(slides, h)
    out: List[Finding] = []

    # --- text nothing can measure ------------------------------------------------------------
    # Reported first, and deliberately so: everything after it is computed from the shapes that
    # survived parsing, and these did not. A deck with one of these is not a deck that passed.
    hidden = unmeasurable_text_shapes(deck)
    if hidden:
        out.append(Finding(
            DETECTOR, "ZERO_AREA_TEXT", None,
            f"{len(hidden)} text block(s) sit in a shape with no measurable geometry. They are in "
            "the file and not on the slide, and every other verdict below was computed without "
            "them.",
            [f"slide {i}: {why} — {txt[:44]!r}" for i, why, txt in hidden[:6]]
            + ["A placeholder inherits its position and size. Assign one of them and python-pptx "
               "writes an <a:xfrm> for the whole shape and records the rest as zero or absent — so "
               "set left, top, width and height together, or none of them.",
               "Re-run this check after fixing the coordinates. The findings it reports then were "
               "always there; the silence was the defect talking."],
        ))

    # --- the clock -------------------------------------------------------------------------
    # Backup slides are not part of the talk, so they are not part of its clock.
    if backup_from is not None:
        if not 1 <= backup_from <= len(slides):
            raise ValueError(f"--backup-from {backup_from} is outside the deck's "
                             f"{len(slides)} slide(s)")
        backup_at: Optional[int] = backup_from - 1
    else:
        backup_at = find_backup_boundary(slides)
    LAST_BOUNDARY[0] = backup_at
    n = backup_at if backup_at is not None else len(slides)
    allowed = max(1, round(minutes * b.slides_per_minute))
    if n > allowed * 1.25:  # 25% of slack: some slides are a divider, some are a single number
        held = "" if backup_at is None else (
            f" ({len(slides) - backup_at} more are held in backup from slide {backup_at + 1}, "
            "off the clock.)")
        out.append(Finding(
            DETECTOR, "DECK_OVER_BUDGET", None,
            f"{n} presented slides for a {minutes:g}-minute {b.label.lower()}. At this archetype's "
            f"pace (~{b.slides_per_minute:g} slide/min) that is a talk of about "
            f"{n / b.slides_per_minute:.0f} minutes.{held}",
            [f"Budget: ~{allowed} slides.",
             "Cutting is the work. A talk that runs over is not a talk with more content in it — "
             "it is a talk whose ending was taken away at the microphone."],
        ))

    # --- what one slide can hold ------------------------------------------------------------
    counts = [(i, words_on(sh)) for i, sh in enumerate(slides, start=1)]
    content = [(i, c) for i, c in counts if c > 0]
    for i, c in content:
        if c > b.words_max:
            out.append(Finding(
                DETECTOR, "SLIDE_TOO_DENSE", i,
                f"Slide {i} carries {c} words; this archetype's ceiling is {b.words_max}.",
                [b.note,
                 "They cannot read this and listen to you at the same time. One of the two is "
                 "going to lose, and it will be you."],
            ))
    if content:
        ranked = sorted(c for _i, c in content)
        median = ranked[len(ranked) // 2]
        p75 = ranked[math.ceil(0.75 * len(ranked)) - 1]  # nearest-rank 75th percentile
        if median > b.words_median:
            # Report what was measured, not a cause. The median is over the slides that carry
            # words, so deleting sparse slides (dividers, a title card) raises it while no slide
            # got any denser — "the deck's habit" was then a wrong diagnosis to act on.
            out.append(Finding(
                DETECTOR, "SLIDE_TOO_DENSE", None,
                f"Median {median} words per slide, 75th percentile {p75}, over the "
                f"{len(ranked)} slides that carry words. For {b.label.lower()} the working "
                f"figure is {b.words_median}.",
                [b.note,
                 f"Measured over these {len(ranked)} slides only: removing sparse slides raises "
                 "the median without making any slide denser. Before cutting, check which "
                 "slides are above the working figure."],
            ))

    # --- the back row -----------------------------------------------------------------------
    small: List[str] = []
    for i, shapes in enumerate(slides, start=1):
        for s in shapes:
            if s.is_chrome or is_page_number(s.text) or not s.text or not s.max_pt:
                continue
            if s.max_pt < b.min_pt:
                small.append(f"slide {i}: {s.max_pt:g} pt — {s.text[:44]!r}")
    if small:
        out.append(Finding(
            DETECTOR, "TYPE_TOO_SMALL", None,
            f"{len(small)} text block(s) fall below this archetype's {b.min_pt} pt floor.",
            small[:6] + ["Below the floor the text is not being read — it is being *seen*, which is "
                         "another way of saying it is decoration."],
        ))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("deck", nargs="?", type=Path)
    ap.add_argument("--archetype", choices=sorted(BUDGETS))
    ap.add_argument("--minutes", type=float)
    ap.add_argument("--list", action="store_true", help="show the archetypes and their budgets")
    ap.add_argument("--json", type=Path)
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--backup-from", type=int, metavar="N",
                    help="slide N (1-based, presentation order) opens the backup section; "
                         "overrides the detected divider")
    a = ap.parse_args()

    if a.list:
        print(f"{'archetype':<16} {'slides/min':>10} {'words':>10} {'min pt':>7}  what the room is")
        for k, b in BUDGETS.items():
            print(f"{k:<16} {b.slides_per_minute:>10g} {b.words_median:>7}–{b.words_max:<3} "
                  f"{b.min_pt:>6}  {b.note}")
        print("\nSee references/presentation_archetypes.md for the skeletons themselves.")
        return 0

    if not (a.deck and a.archetype and a.minutes):
        ap.error("give a deck, --archetype and --minutes (or --list)")
    if not a.deck.is_file():
        print(f"cannot read {a.deck}", file=sys.stderr)
        return 2

    try:
        findings = audit(a.deck, a.archetype, a.minutes, a.backup_from)
    except (zipfile.BadZipFile, ET.ParseError, KeyError) as exc:
        print(f"{a.deck} is not a readable .pptx ({exc})", file=sys.stderr)
        return 2
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if a.json:
        a.json.parent.mkdir(parents=True, exist_ok=True)
        a.json.write_text(json.dumps(
            {"detector": DETECTOR, "deck": str(a.deck), "archetype": a.archetype,
             "minutes": a.minutes,
             "backup_from": None if LAST_BOUNDARY[0] is None else LAST_BOUNDARY[0] + 1,
             "findings": [f.__dict__ for f in findings]},
            indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    b = BUDGETS[a.archetype]
    if LAST_BOUNDARY[0] is None:
        print("clock: every slide counts (no backup divider found; --backup-from N sets one)")
    else:
        how = "given by --backup-from" if a.backup_from is not None else "detected divider"
        print(f"clock: stops at slide {LAST_BOUNDARY[0] + 1} ({how}); "
              "slides from there on are backup, off the clock")
    if not findings:
        print(f"OK: the deck fits {b.label} at {a.minutes:g} minutes.")
        return 0

    print(f"{len(findings)} finding(s) — {b.label}, {a.minutes:g} min\n")
    for f in findings:
        where = f"slide {f.slide}" if f.slide else "deck"
        print(f"  [{f.verdict}] ({where})")
        print(f"      {f.summary}")
        for e in f.evidence:
            print(f"      - {e}")
        print()
    return 1 if a.strict else 0


if __name__ == "__main__":
    sys.exit(main())
