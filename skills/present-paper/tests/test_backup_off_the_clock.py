#!/usr/bin/env python3
"""Backup slides are not part of the talk, so they are not part of its clock.

Nearly every conference deck carries a backup section — the Q&A slides you do not present
and open only if someone asks. The budget check counted them against the clock, so a
10-minute talk with four backup slides was told to cut, and the honest way to satisfy the
tool was to delete the Q&A preparation. That is the tool being wrong in the one place a
speaker most needs to be prepared.

The clock now stops at the first slide marked "Backup" / "Appendix" / "Q&A" / "백업".
Density and type size still apply past that line — a backup slide is shown *under
questioning*, which is the worst possible moment to find out it is a wall of 11-pt text.

Skips cleanly (exit 0) without python-pptx. Network-free.

    python3 skills/present-paper/tests/test_backup_off_the_clock.py
"""
import sys
import tempfile
from pathlib import Path

try:
    from pptx import Presentation
    from pptx.util import Inches, Pt
except ImportError:
    print("python-pptx not installed — SKIP (compile-only)")
    sys.exit(0)

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import check_deck_budget as budget  # noqa: E402

fails: list[str] = []


def deck(headlines, body_words=8, pt=24):
    """One slide per headline: the headline, plus a little body so it counts as content."""
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    for h in headlines:
        s = prs.slides.add_slide(prs.slide_layouts[6])
        for txt, y in ((h, 0.5), (" ".join(["word"] * body_words), 2.5)):
            if not txt:
                continue
            tb = s.shapes.add_textbox(Inches(0.7), Inches(y), Inches(11), Inches(1.2))
            tb.text_frame.text = txt
            tb.text_frame.paragraphs[0].runs[0].font.size = Pt(pt)
    p = Path(tempfile.mkdtemp()) / "d.pptx"
    prs.save(str(p))
    return p


def verdicts(path, minutes=10, archetype="conference_oral"):
    return [f.verdict for f in budget.audit(path, archetype, minutes)]


# --- the boundary itself ------------------------------------------------------------
CASES = [
    (["Backup"], 0),
    (["Backup — Q&A"], 0),
    (["Appendix"], 0),
    (["Q & A"], 0),
    (["백업"], 0),
    # a sentence that merely contains the word is a sentence, not a signpost
    (["Reserved for the appendix of the guideline"], None),
    (["Supplemental oxygen was given to every patient"], None),
    (["58 tells us nothing — four numbers do"], None),
    # a clinical headline that merely STARTS with a backup word is a finding, not a signpost
    (["Appendix perforation in children"], None),
    (["Supplementary oxygen did not help"], None),
    (["Reserve capacity predicts survival"], None),
    (["예비 연구 결과"], None),
    # ...while the signposts people actually write still are
    (["Backup slides"], 0),
    (["Appendix A: sensitivity analyses"], 0),
    (["Supplementary"], 0),
    (["백업 슬라이드"], 0),
]
for heads, want in CASES:
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    for h in heads:
        s = prs.slides.add_slide(prs.slide_layouts[6])
        tb = s.shapes.add_textbox(Inches(0.7), Inches(0.5), Inches(11), Inches(1))
        tb.text_frame.text = h
    p = Path(tempfile.mkdtemp()) / "b.pptx"
    prs.save(str(p))
    slides, _n, _w, _h = budget.read_deck(p)
    got = budget.find_backup_boundary(slides)
    if got != want:
        fails.append(f"boundary for {heads[0]!r}: want {want}, got {got}")

# A section divider puts its title AND its subtitle in one text frame. So the shape reads
# "Backup\nQ&A — the four questions this design invites", and a guard that measured the whole
# text threw the boundary away for being ten words long. This is the deck that caught it.
prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
s = prs.slides.add_slide(prs.slide_layouts[6])
tb = s.shapes.add_textbox(Inches(1.5), Inches(3.1), Inches(10), Inches(2.5))
tf = tb.text_frame
tf.text = "Backup"
tf.add_paragraph().text = "Q&A — the four questions this design invites"
p = Path(tempfile.mkdtemp()) / "divider.pptx"
prs.save(str(p))
slides, _n, _w, _h = budget.read_deck(p)
if budget.find_backup_boundary(slides) != 0:
    fails.append("a real section divider (title + subtitle in one frame) was not recognised — "
                 "the boundary must be read from the shape's FIRST LINE, not its whole text")


# --- the clock stops there ----------------------------------------------------------
TALK = [f"Finding {i} changed what we do" for i in range(11)]      # 11 presented slides
BACKUP = ["Backup"] + [f"Answer to question {i}" for i in range(6)]  # 7 more, off the clock

# 11 presented slides for a 10-min conference oral: allowed 10, slack to 12.5 -> fits.
if "DECK_OVER_BUDGET" in verdicts(deck(TALK)):
    fails.append("11 presented slides for a 10-min oral should fit (budget 10, +25% slack)")

# The same talk with a backup section must STILL fit -- that is the whole fix.
if "DECK_OVER_BUDGET" in verdicts(deck(TALK + BACKUP)):
    fails.append("backup slides were counted against the clock — the bug this test exists for")

# ...but a genuinely over-long talk must still be caught, backup section or not.
if "DECK_OVER_BUDGET" not in verdicts(deck([f"Point {i} matters here" for i in range(20)] + BACKUP)):
    fails.append("20 presented slides for a 10-min oral must still be caught")


# A clinical headline at slide 2 must not stop the clock (it used to: exit 0, "OK").
for head in ("Appendix perforation in children", "Supplementary oxygen did not help",
             "Reserve capacity predicts survival", "예비 연구 결과"):
    talk = [f"Point {i} matters here" for i in range(20)]
    talk[1] = head
    if "DECK_OVER_BUDGET" not in verdicts(deck(talk)):
        fails.append(f"headline {head!r} stopped the clock on a 20-slide, 10-min oral")

# An explicit --backup-from overrides detection, and the CLI says where the clock stopped.
import subprocess  # noqa: E402
SCRIPT = Path(budget.__file__)
long_talk = deck([f"Point {i} matters here" for i in range(20)])
if [f.verdict for f in budget.audit(long_talk, "conference_oral", 10, backup_from=11)
        if f.verdict == "DECK_OVER_BUDGET"]:
    fails.append("--backup-from 11 should leave 10 presented slides, within budget")
r = subprocess.run([sys.executable, str(SCRIPT), str(long_talk), "--archetype", "conference_oral",
                    "--minutes", "10", "--backup-from", "11"], capture_output=True, text=True)
if r.returncode != 0 or "clock: stops at slide 11" not in r.stdout:
    fails.append(f"--backup-from 11: want exit 0 and the boundary printed, got {r.returncode}: "
                 f"{r.stdout}{r.stderr}")
r = subprocess.run([sys.executable, str(SCRIPT), str(long_talk), "--archetype", "conference_oral",
                    "--minutes", "10", "--backup-from", "99"], capture_output=True, text=True)
if r.returncode != 2:
    fails.append(f"--backup-from past the last slide must exit 2, got {r.returncode}")


# --- legibility does NOT stop there -------------------------------------------------
# A dense, tiny backup slide is shown under questioning. It still has to be readable.
dense = deck(TALK + ["Backup"] + ["Answer"], body_words=0)
prs = Presentation(str(dense))
s = prs.slides[-1]
tb = s.shapes.add_textbox(Inches(0.7), Inches(2.5), Inches(11), Inches(4))
tb.text_frame.word_wrap = True
tb.text_frame.text = " ".join(["word"] * 90)              # over the 60-word ceiling
tb.text_frame.paragraphs[0].runs[0].font.size = Pt(9)     # under the 20 pt floor
prs.save(str(dense))
v = verdicts(dense)
if "SLIDE_TOO_DENSE" not in v:
    fails.append("a 90-word backup slide escaped the density check — backups get shown too")
if "TYPE_TOO_SMALL" not in v:
    fails.append("a 9-pt backup slide escaped the type floor — backups get shown too")
if "DECK_OVER_BUDGET" in v:
    fails.append("the backup section was still on the clock")


if fails:
    print("FAIL — backup section")
    for f in fails:
        print("  ·", f)
    sys.exit(1)
print(f"PASS — boundary ({len(CASES)} cases), clock stops at backup, legibility does not")
