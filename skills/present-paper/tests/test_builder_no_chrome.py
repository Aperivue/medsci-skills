#!/usr/bin/env python3
"""The shipped builder must not manufacture the tell it is supposed to prevent.

This project's own house style used to require an all-caps eyebrow on *every* slide and a
"2026 · COURSE" footer on *every* slide. That is the first thing reviewers name when they say they
can spot an AI-made deck at a glance — "슬라이드 상단과 하단에 자잘한 글자들" — and it was not an
accident of generation. It was in our style guide, and `build_pptx_nature_lancet.py` took `eyebrow`
as a *required* argument, so every content slide got one whether or not it meant anything.

Editing the style guide would have been a fix that changed nothing. The builder is what makes the
deck.

So this test does both halves:

  1. Build with the shipped builder as documented -> `check_slide_tells.py` must find NOTHING.
  2. Rebuild the SAME deck the old way (eyebrow on every content slide) -> the detector must FIRE.

Half 2 is the one that makes half 1 mean something. A test that only asserts "the current build is
clean" would also pass if the detector were broken, or if it never looked at chrome at all.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
sys.path.insert(0, str(SKILL / "templates"))

from build_pptx_nature_lancet import (  # noqa: E402
    add_closing_slide,
    add_content_slide,
    add_section_divider,
    add_title_slide,
    new_presentation,
)

DETECTOR = SKILL / "scripts" / "check_slide_tells.py"

# A real deck's worth of content slides, not three. The earlier version of this test built
# three, and three is below every threshold in the detector — so it certified a builder that
# tripped SHAPE_MONOTONY the moment anyone built a normal-length deck with it. A gate whose
# fixture is smaller than the thing it guards is not a gate.
TITLES = [
    "Seeding followed the catheter tract in 9 of 11 cases",
    "Recurrence halved with adjunctive ablation (12% vs 26%)",
    "The effect did not depend on tumour size",
    "Ablation added 40 minutes to the procedure",
    "Two centres accounted for most of the variance",
    "The learning curve flattened after 20 cases",
    "Grade 3 complications were unchanged",
    "Cost per avoided recurrence was $4,100",
    "The benefit persisted at three years",
    "Operator experience predicted success better than device",
    "No seeding occurred where the tract was ablated",
    "The registry under-reports minor complications",
]


def build(path: Path, chrome_on_every_slide: bool, figure: Path | None = None) -> None:
    prs = new_presentation()
    # The title slide and the dividers keep their eyebrow: there it orients someone who just
    # walked in. That is the whole distinction being tested.
    add_title_slide(prs, eyebrow="REVIEW LECTURE", title="Tract seeding after pleural catheters",
                    subtitle="What the registry shows", meta_top="Journal club",
                    meta_bottom="Presenter", notes="notes")
    add_section_divider(prs, num="01", title="Findings", subtitle="registry", time_min=5)
    for i, t in enumerate(TITLES):
        kwargs = {}
        if chrome_on_every_slide:  # the old, wrong default
            kwargs = {"eyebrow": "TRACT SEEDING", "page_brand": "2026 · JOURNAL CLUB"}
        if figure is not None and i % 4 == 0:
            kwargs |= {"figure_path": figure, "fig_caption": "Registry cohort",
                       "footnote": "Source 2024"}
        add_content_slide(prs, title=t, subtitle="n = 412",
                          bullets=["Median follow-up 3.2 years", "  Consistent across centres"],
                          notes="notes", **kwargs)
    add_closing_slide(prs, title="Take-home", bullets=["Ablate the tract."],
                      contact="a@b.c", notes="notes")
    prs.save(str(path))


def verdicts(deck: Path) -> set:
    out = subprocess.run([sys.executable, str(DETECTOR), str(deck)],
                         capture_output=True, text=True).stdout
    return {line.strip().split("]")[0].lstrip("[")
            for line in out.splitlines() if line.strip().startswith("[")}


def main() -> int:
    ok = True
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)

        # 1. As shipped: no chrome on content slides.
        clean = tmp / "shipped.pptx"
        build(clean, chrome_on_every_slide=False)
        found = verdicts(clean)
        if found:
            print(f"  FAIL  the shipped builder produces a deck with tells: {sorted(found)}")
            ok = False
        else:
            print("  PASS  the shipped builder produces a deck with no tells")

        # 2. The defect, deliberately restored. If this does NOT fire, the fix above proves
        #    nothing — the detector would be blind to the very thing we just removed.
        old = tmp / "old_way.pptx"
        build(old, chrome_on_every_slide=True)
        found = verdicts(old)
        if "CHROME_ON_EVERY_SLIDE" in found:
            print("  PASS  restoring the old eyebrow-everywhere default is CAUGHT")
        else:
            print("  FAIL  the old default was NOT caught — this gate is decorative "
                  f"(found: {sorted(found) or 'nothing'})")
            ok = False

        # 3. The rule under the title is a LINE. Draw it as a thin rectangle instead — which
        #    looks identical and is what the builder used to do — and the deck becomes a stack
        #    of one repeated box. This is not hypothetical: it shipped.
        import build_pptx_nature_lancet as b  # noqa: PLC0415
        from pptx.enum.shapes import MSO_SHAPE  # noqa: PLC0415
        from pptx.util import Emu, Inches  # noqa: PLC0415

        real_rule = b._rule

        def rule_as_rectangle(s, *, x, y, w, color, pt=2.0):
            r = s.shapes.add_shape(MSO_SHAPE.RECTANGLE,
                                   Inches(x), Inches(y), Inches(w), Emu(20000))
            r.fill.solid(); r.fill.fore_color.rgb = color
            r.line.fill.background()
            return r

        b._rule = rule_as_rectangle
        try:
            regressed = tmp / "rule_as_rect.pptx"
            build(regressed, chrome_on_every_slide=False)
        finally:
            b._rule = real_rule
        found = verdicts(regressed)
        if "SHAPE_MONOTONY" in found:
            print("  PASS  drawing the rule as a rectangle is CAUGHT (SHAPE_MONOTONY)")
        else:
            print("  FAIL  a deck of identical thin rectangles was NOT caught "
                  f"(found: {sorted(found) or 'nothing'})")
            ok = False

        # 4. The builder must also clear the OTHER gate. Its eyebrow, its meta line, its
        #    "SECTION 01" label, its "5 MIN" badge, its figure caption and its contact line
        #    were all set below the 20-pt floor every academic archetype declares — so a deck
        #    built exactly as documented failed check_deck_budget. The style guide said one
        #    thing and the gate said another; the gate is the one that is right, because a
        #    caption nobody in the back row can read is decoration whatever the guide calls it.
        from PIL import Image  # noqa: PLC0415  (python-pptx already requires Pillow)

        fig = tmp / "fig.png"
        Image.new("RGB", (400, 300), "white").save(fig)
        full = tmp / "kitchen_sink.pptx"
        build(full, chrome_on_every_slide=False, figure=fig)

        budget = SKILL / "scripts" / "check_deck_budget.py"
        out = subprocess.run(
            [sys.executable, str(budget), str(full),
             "--archetype", "conference_oral", "--minutes", "14"],
            capture_output=True, text=True).stdout
        if "TYPE_TOO_SMALL" in out:
            small = [ln.strip() for ln in out.splitlines() if " pt — " in ln]
            print("  FAIL  the builder's own type falls below the floor it is checked against:")
            for ln in small[:6]:
                print("          ", ln)
            ok = False
        else:
            print("  PASS  the shipped builder clears the type floor (figures, meta, dividers)")

    print("----")
    print("test_builder_no_chrome:", "passed" if ok else "FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
