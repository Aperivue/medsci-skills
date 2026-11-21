#!/usr/bin/env python3
"""Start a new deck from the medsci slide template.

    python3 new_deck.py OUT.pptx                          empty deck (no slides), all 31 layouts
    python3 new_deck.py OUT.potx                          the same, saved as a PowerPoint template (.potx)
    python3 new_deck.py OUT.pptx --type conference-oral   research talk, 8-12 minutes
    python3 new_deck.py OUT.pptx --type journal-club      appraisal of one paper, 20-40 minutes
    python3 new_deck.py OUT.pptx --type lecture           didactic lecture, about 30 minutes
    python3 new_deck.py OUT.pptx --type case-conference   case / imaging conference
    python3 new_deck.py OUT.pptx --type procedure         procedure or technique talk
    --template PATH                                       another build, .pptx or .potx, with no slides
                                                          (default: medsci_slides.pptx beside this file)
    --force                                               replace OUT.pptx if it exists (otherwise refused)

A starter is a skeleton, not a talk. Each slide carries <angle-bracket> text to overwrite, and a
speaker note that says what the slide is for; write your own notes over it. Picture placeholders are
left empty. Findings and quiz answers on the imaging slides appear on click (image first, words
after). Fill by hand, or with python-pptx by layout name and placeholder idx (README).
"""
import argparse
import io
import os
import re
import sys
import tempfile
import unicodedata
import zipfile
from pathlib import Path

from pptx import Presentation
from pptx.opc.constants import RELATIONSHIP_TYPE as RT
from pptx.oxml import parse_xml
from pptx.util import Emu

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from build_slide_template import (NSDECL, TEMPLATE_NAME, OutputExists, plain_table, post_process, publish,  # noqa: E402
                                  put_lines, refuse_existing, set_cell, theme_fonts)

NS_P = "http://schemas.openxmlformats.org/presentationml/2006/main"

AFFIL = "<Department>\n<Institution, City, Country>"
# Said on every slide that takes a patient image. Covering a field with a shape, or cropping it in PowerPoint,
# hides it on screen only: the full image stays in the file and anyone given the .pptx can recover it.
DEIDENTIFY = ("Remove names, numbers and dates from the image pixels and from its metadata before inserting it. "
              "A shape laid over them, or a crop in PowerPoint, hides them on screen but leaves them in the file.")
HANGUL = re.compile("[\u1100-\u11ff\u3130-\u318f\uac00-\ud7a3]")   # jamo, compatibility jamo, syllables

# One entry per slide: (layout, {placeholder idx: text | [lines]}, options). idx 0 is the title.
# lines: "text" (level 0) or (level, "text"). options: table=(rows, cols, header), appear=[idx, ...], notes="...".
CONFERENCE_ORAL = [
    ("Cover", {0: "<The finding, or the study title>", 1: "<Presenter>", 14: AFFIL, 13: "<Meeting> · <Session>"},
     dict(notes="Decide the one-sentence summary statement before building anything else. The cover picture and the logo slot are optional; leave them empty and they do not show.")),
    ("Disclosure", {0: "Disclosures", 1: "<None, or one line per relationship>", 13: "<Funder and grant number, or none>"},
     dict(notes="Ten seconds. Say it; do not read it.")),
    ("Content", {0: "<The question, as one sentence>",
                 1: ["<What is known>", "<What is not known>", "<Why it matters to the person in row three>"]},
     dict(notes="The question the room should be asking by the end of this slide. No literature review.")),
    ("Study Design", {0: "<The design, as one sentence>", 13: "<Who, how many, where from>", 14: "<From when to when>",
                      15: "<Reference standard, and who read it>"},
     dict(notes="Methods are here so the finding can be believed. Draw the flow diagram as code and insert the image; after inserting, use Crop > Fit so nothing is cut.")),
    ("Result · Figure", {0: "<What the primary figure shows, as one sentence>", 14: "<Source or footnote, or delete>"},
     dict(notes="One figure. The title says what it shows, so the recording and the person looking at a phone still get it. Say aloud where to look; do not add a line under the title.")),
    ("Key Finding", {0: "<The finding, as one sentence>", 13: "<0.00>", 14: "<what the number measures, with its unit>",
                     15: "<95% CI 0.00 to 0.00 · n = 000>", 16: "<Source or footnote, or delete>"},
     dict(notes="The one number they should leave with. This is the only slide where the accent colour is spent by the template.")),
    ("Result · Table", {0: "<What the secondary result shows, as one sentence>", 13: "<The row or column to read>",
                        14: "<Source or footnote, or delete>"},
     dict(table=(4, 4, ["<Group>", "<Reference>", "<Index>", "<Difference>"]),
          notes="A few rows only. The full table belongs in backup, after the last slide.")),
    ("Comparison", {0: "<How this differs from what was known, as one sentence>", 13: "<Before this study>",
                    14: "<This study>", 1: ["<Line>", "<Line>"], 2: ["<Line>", "<Line>"]},
     dict(notes="Use only if a comparison carries the argument. Delete the slide otherwise.")),
    ("Limitations", {0: "<Why the finding might be wrong>", 13: "<Limitation 1>", 16: "<Direction and rough size of the bias>",
                     14: "<Limitation 2>", 17: "<What was done about it>", 15: "<Limitation 3>", 18: "<What it leaves open>"},
     dict(notes="Three, and the three a reviewer would raise. Naming them first is what survives the questions.")),
    ("Take-home", {0: "<The finding, once more>", 1: ["<The finding>", "<The condition under which it holds>", "<What it changes>"]},
     dict(notes="End here, on the finding. Leave this slide up during questions.")),
    ("References · QR", {0: "References", 1: ["<Reference 1>", "<Reference 2>", "<Reference 3>"],
                         13: "<Where the code leads>"},
     dict(notes="Off the clock: shown only if asked. Generate the reference list with a reference manager, not by hand.")),
]

JOURNAL_CLUB = [
    ("Cover", {0: "<Paper title>", 1: "<Presenter>", 14: "<First author, journal, year>", 13: "Journal club · <Date>"},
     dict(notes="The paper is the specimen; the appraisal is yours.")),
    ("Content", {0: "<The claim the paper makes, in one sentence>",
                 1: ["<Who would change practice if it is true>", "<What was believed before>"]},
     dict(notes="State the claim in your words, not the abstract's.")),
    ("Comparison", {0: "<The gap between the design the claim needs and the design used>", 13: "The design this claim needs",
                    14: "The design they used", 1: ["<Population>", "<Comparator>", "<Outcome>"],
                    2: ["<Population>", "<Comparator>", "<Outcome>"]},
     dict(notes="The room is here to learn how to read. Show the ideal design first, then theirs.")),
    ("Study Design", {0: "<Their design, as one sentence>", 13: "<Who, how many, where from>", 14: "<From when to when>",
                      15: "<Reference standard, and who read it>"},
     dict(notes="Their flow diagram, cropped from the paper, with the caption trimmed off.")),
    ("Result · Figure", {0: "<Your reading of the main figure, as one sentence>",
                         14: "<Figure number, first author, journal, year>"},
     dict(notes="The paper's own figure with your headline over it, not the journal's caption.")),
    ("Key Finding", {0: "<The number the paper rests on>", 13: "<0.00>", 14: "<what it measures, with its unit>",
                     15: "<95% CI 0.00 to 0.00 · n = 000>", 16: "<Table or figure it comes from>"},
     dict(notes="Say how wide the interval is and whether the lower end would still matter.")),
    ("Result · Table", {0: "<What the secondary or subgroup result shows, as one sentence>",
                        13: "<The row or column to read>", 14: "<Table number, first author, journal, year>"},
     dict(table=(4, 4, ["<Group>", "<Control>", "<Intervention>", "<Difference>"]),
          notes="Rebuild the rows you need as a table; do not paste a screenshot of the paper's table.")),
    ("Limitations", {0: "<Why the claim might be wrong>", 13: "<Limitation 1>", 16: "<Direction and rough size of the bias>",
                     14: "<Limitation 2>", 17: "<Whether the authors addressed it>", 15: "<Limitation 3>",
                     18: "<What it leaves open>"},
     dict(notes="Yours, not the paper's limitations paragraph. Put the one that matters most first.")),
    ("Content", {0: "<What would change my mind>", 1: ["<The study that would settle it>", "<The result that would reverse the claim>"]},
     dict(notes="This is the slide that shows you had an opinion.")),
    ("Take-home", {0: "<Your verdict, in one sentence>", 1: ["<What to believe>", "<What to doubt>", "<What to do differently>"]},
     dict(notes="Three lines the room can repeat.")),
    ("References · QR", {0: "References", 1: ["<The paper>", "<The paper it should be read against>"],
                         13: "<Link to the paper>"},
     dict(notes="Off the clock.")),
]

LECTURE = [
    ("Cover", {0: "<Lecture title>", 1: "<Presenter>", 14: AFFIL, 13: "<Course> · <Date>"},
     dict(notes="Cover. The event line carries the course name and the date.")),
    ("Imaging · Case", {20: "Why it matters", 0: "<Age/sex> · <symptom> · <modality>",
                        1: ["<What is wrong here?>", "<Why this lecture matters>"]},
     dict(appear=[1], notes="Open with one case that shows why the topic matters. The image shows first; the question appears on click. " + DEIDENTIFY)),
    ("Table", {20: "Roadmap", 0: "<Roadmap: parts × disease groups>"},
     dict(table=(4, 4, ["<Part>", "<Group 1>", "<Group 2>", "<Group 3>"]),
          notes="The map of the whole lecture; copy the same table into the handout. Say what is covered and what is left out.")),
    ("Section", {13: "01", 0: "<Part 1>", 14: "<What this part covers>"},
     dict(notes="Start of a part. Showing the roadmap table again here is fine.")),
    ("Content", {20: "<Part 1>", 0: "<Disease A>: <key finding in one line>",
                 1: ["Definition: <one line>", "Who: <age, sex, setting>", "CT: <finding>", "MRI: <finding>",
                     "Differential: <Disease B>, told apart by <the one finding>"]},
     dict(notes="Keep the same order for every disease (definition, who, CT, MRI, differential). Say the differentiating point in one sentence, and say aloud what must be memorised and what can be looked up.")),
    ("Imaging · 2×2", {20: "<Part 1>", 0: "<Disease A>: typical findings", 40: "T2WI", 41: "T1WI", 42: "T1CE",
                       43: "DWI", 1: ["<Finding 1>", "<Finding 2>"]},
     dict(appear=[1], notes="Images first, findings on click. Sequence labels sit in the panel corner; keep their order fixed through the deck. Arrows on the key structure stay on the slide.")),
    ("Imaging · Case", {20: "<Part 1>", 0: "<Age/sex> · <symptom>", 1: ["<Diagnosis>", "<Why: one finding>"]},
     dict(appear=[1], notes="A one-line presentation, then the diagnosis and the one finding behind it, in ten to twenty seconds.")),
    ("Table", {20: "<Part 1>", 0: "<Part 1 summary: finding, differential, next step>"},
     dict(table=(4, 3, ["Finding", "Differential", "Next step"]),
          notes="Summary table at the end of the part; copy it into the handout. The next part repeats the same order from its Section slide.")),
    ("Lessons", {20: "<Part 1>", 0: "<A case we missed>", 1: ["<What we saw>", "<What we should have seen>", "<What we do now>"]},
     dict(notes="One missed or difficult case, and what it taught.")),
    ("Imaging · Quiz", {20: "Quiz", 0: "Quiz 1", 1: ["<Question>"], 50: "<Answer and the one finding>"},
     dict(appear=[50], notes="One question per taught item. The answer appears on click and stays on the slide in writing, so it survives in the review copy.")),
    ("Imaging · Quiz", {20: "Quiz", 0: "Quiz 2", 1: ["<Question that combines the parts>"], 50: "<Answer>"},
     dict(appear=[50], notes="The last question combines the parts.")),
    ("Take-home", {0: "<Three things to remember>", 1: ["<1>", "<2>", "<3>"]},
     dict(notes="Three lines, and how to review (the handout tables). Give the handout out before the lecture.")),
    ("Closing", {0: "<The one thing to take away, in one line>", 13: "<Presenter · email · where the slides are>"},
     dict(notes="The last slide stays up during questions, so it carries the conclusion, not a thank-you. Time the rehearsal and check that it ends inside the slot.")),
]

CASE_CONFERENCE = [
    ("Cover", {0: "<Conference title>", 1: "<Presenter>", 14: AFFIL, 13: "Imaging conference · <Date>"},
     dict(notes="Cover.")),
    ("Imaging · Case", {20: "Case 1", 0: "<Age/sex> · <symptom> · <modality>", 1: ["<What do you see?>"]},
     dict(appear=[1], notes="One-line presentation, the image, then the question. " + DEIDENTIFY)),
    ("Imaging · 2×2", {20: "Case 1", 0: "<Initial images>", 40: "T2WI", 41: "T1WI", 42: "T1CE", 43: "DWI",
                       1: ["<Finding 1>", "<Finding 2>"]},
     dict(appear=[1], notes="Keep sequence labels and their order fixed. Findings appear on click.")),
    ("Imaging · Quiz", {20: "Case 1", 0: "What is your diagnosis?", 1: ["<Two or three choices, or an open question>"],
                        50: "<Diagnosis>"},
     dict(appear=[50], notes="The answer appears on click and stays on the slide.")),
    ("Imaging · 1×3", {20: "Case 1", 0: "<Diagnosis>: key images", 40: "DWI", 41: "ADC", 42: "T1CE",
                       1: ["<One line per image>"]},
     dict(appear=[1], notes="Three key images, one line each. Keep DWI and ADC side by side.")),
    ("Content", {20: "Case 1", 0: "<Diagnosis>: <the finding that makes it>",
                 1: ["Key finding: <...>", "Differential: <Disease B>, told apart by <...>", "Pitfall: <...>"]},
     dict(notes="Say the differentiating point in one sentence.")),
    ("Lessons", {20: "Case 1", 0: "<What this case teaches>", 1: ["<Lesson 1>", "<Lesson 2>"]},
     dict(notes="For more cases, duplicate the run from the Case slide to this one.")),
    ("Closing", {0: "<What this case teaches, in one line>", 13: "<Presenter · email>"},
     dict(notes="The conclusion stays up during the discussion.")),
]

PROCEDURE = [
    ("Cover", {0: "<Lecture title>", 1: "<Presenter>", 14: AFFIL, 13: "<Course> · <Date>"},
     dict(notes="Cover.")),
    ("Content", {20: "Principle", 0: "<One-sentence treatment principle>",
                 1: ["Treat or observe: <criteria>", "Route: <options>", "Risk by route: <...>"]},
     dict(notes="In the first three minutes, set out the decision frame (whether to treat, by which route) and the risk of each route; the later slides on technique choice refer back to it.")),
    ("Table", {20: "Roadmap", 0: "<Roadmap: problem, technique, device>"},
     dict(table=(4, 3, ["Problem", "Technique", "Device"]),
          notes="Group the techniques by the problem each one solves. Order them from simple to difficult, the same order in which one escalates during a procedure.")),
    ("Section", {13: "01", 0: "<Technique 1>", 14: "<The problem it solves>"}, dict(notes="Start of a technique.")),
    ("Imaging · Case", {20: "<Technique 1>", 0: "<Age/sex> · <presentation> · <lesion, size>",
                        1: ["<Why treat>", "<Plan>"]},
     dict(appear=[1], notes="One-line case presentation. Angiography screen captures carry the patient fields. " + DEIDENTIFY)),
    ("Imaging · DSA Pair", {20: "<Technique 1>", 0: "<Vessel injected · working projection>",
                            40: "<Projection · phase>", 41: "<3D / working view>"},
     dict(notes="Name the projection in the title. Put arrows on the landmarks. Labels sit under the panels so they stay readable over a white subtracted image.")),
    ("Imaging · 4 Steps", {20: "<Technique 1>", 0: "<Technique 1> in four steps", 40: "1  Access", 41: "2  Confirm",
                           42: "3  Deploy", 43: "4  Result", 1: ["<What changes at each step>"]},
     dict(notes="Break the procedure into four still frames. If a video is used, keep it under twenty seconds and caption the step names. Arrow and name on the key frame only.")),
    ("Content", {20: "<Technique 1>", 0: "<Complications: incidence, management, prevention>",
                 1: ["Incidence: <%>, risk factors: <...>", "Management: <...>", "Prevention: <...>"]},
     dict(notes="Repeat the same frame for every complication. Say plainly where no accepted criterion exists.")),
    ("Table", {20: "<Technique 1>", 0: "<Technique table: problem, method, devices, cautions>"},
     dict(table=(4, 4, ["Problem", "Method", "Devices", "Cautions"]),
          notes="Comparison table of techniques; copy it into the handout.")),
    ("Lessons", {20: "<Technique 1>", 0: "<When it did not go as planned>",
                 1: ["<What happened>", "<What we changed>"]},
     dict(notes="A case that went badly is evidence for the conclusion. Use it.")),
    ("Take-home", {0: "<Three things to remember>", 1: ["<1>", "<2>", "<3>"]},
     dict(notes="Three lines, then the papers to read and in which order.")),
    ("Closing", {0: "<The one thing to take away, in one line>", 13: "<Presenter · email>"},
     dict(notes="The conclusion stays up during questions.")),
]

STARTERS = {"conference-oral": CONFERENCE_ORAL, "journal-club": JOURNAL_CLUB, "lecture": LECTURE,
            "case-conference": CASE_CONFERENCE, "procedure": PROCEDURE}


def blank(src, out):
    """A .potx is the same package as a .pptx under another content type. The template must be empty: a starter
    adds its slides after whatever is there, and a template's own sample slides are not the user's talk."""
    data = Path(src).read_bytes()                       # read once; every check below is on these bytes
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            types = z.read("[Content_Types].xml")
            pres = z.read("ppt/presentation.xml") if "ppt/presentation.xml" in z.namelist() else b""
    except (zipfile.BadZipFile, KeyError):
        raise ValueError(f"{src} is not a PowerPoint template") from None
    if not any(t in types for t in (b"presentationml.template.main+xml", b"presentationml.presentation.main+xml")) \
            or not pres:
        raise ValueError(f"{src} is not a PowerPoint file (.pptx or .potx)")
    n_slides = len(re.findall(rb"<p:sldId\b", pres))
    if n_slides:
        raise ValueError(f"{src} has {n_slides} slide(s); use an empty template, not a deck")
    Path(out).write_bytes(data)
    post_process(out, template=False)


def set_lang(tf):
    """Hangul runs need lang="ko-KR", or PowerPoint breaks lines in the middle of a word."""
    for p in tf.paragraphs:
        for r in p.runs:
            if HANGUL.search(unicodedata.normalize("NFC", r.text)):
                r._r.get_or_add_rPr().set("lang", "ko-KR")


def fill(shape, value):
    put_lines(shape, value)
    set_lang(shape.text_frame)


def fit_picture(placeholder, image_path, align="l"):
    """Insert a picture into a picture placeholder WITHOUT cropping it.

    A picture placeholder crops to fill its slot, which is right for a CT slice and wrong for a plot, a flow
    diagram or a QR code. This inserts, removes the crop, and scales the whole image into the slot, at the
    left (align="l") or centred (align="ctr").
    """
    x, y, w, h = placeholder.left, placeholder.top, placeholder.width, placeholder.height
    pic = placeholder.insert_picture(str(image_path))
    pic.crop_left = pic.crop_right = pic.crop_top = pic.crop_bottom = 0
    iw, ih = pic.image.size
    scale = min(w / iw, h / ih)
    pw, ph_ = int(iw * scale), int(ih * scale)
    pic.left = Emu(x if align == "l" else x + (w - pw) // 2)
    pic.top = Emu(y + (h - ph_) // 2)
    pic.width, pic.height = Emu(pw), Emu(ph_)
    return pic


def appear_on_click(slide, shapes):
    """Each shape appears on its own click, in order (PowerPoint 'Appear' entrance).

    Call once per slide with every shape: a slide that already has animation is refused rather than given a
    second timing tree, which PowerPoint does not accept."""
    if slide._element.find(f"{{{NS_P}}}timing") is not None:
        raise ValueError("this slide already has animation; call appear_on_click once with all its shapes")
    shapes = list(shapes)                              # a generator would be spent by the first loop
    # by element, not by id: shape ids repeat from slide to slide
    if not shapes or any(slide._element not in sh._element.iterancestors() for sh in shapes):
        raise ValueError("appear_on_click needs one or more shapes from this slide")
    pars, n = "", 3
    for sh in shapes:
        sid = sh.shape_id
        pars += (f'<p:par><p:cTn id="{n}" fill="hold"><p:stCondLst><p:cond delay="indefinite"/></p:stCondLst><p:childTnLst>'
                 f'<p:par><p:cTn id="{n + 1}" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst>'
                 f'<p:par><p:cTn id="{n + 2}" presetID="1" presetClass="entr" presetSubtype="0" fill="hold" grpId="0" '
                 f'nodeType="clickEffect"><p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst>'
                 f'<p:set><p:cBhvr><p:cTn id="{n + 3}" dur="1" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst></p:cTn>'
                 f'<p:tgtEl><p:spTgt spid="{sid}"/></p:tgtEl><p:attrNameLst><p:attrName>style.visibility</p:attrName>'
                 f'</p:attrNameLst></p:cBhvr><p:to><p:strVal val="visible"/></p:to></p:set>'
                 f'</p:childTnLst></p:cTn></p:par></p:childTnLst></p:cTn></p:par></p:childTnLst></p:cTn></p:par>')
        n += 4
    bld = "".join(f'<p:bldP spid="{sh.shape_id}" grpId="0"/>' for sh in shapes)
    timing = parse_xml(
        f'<p:timing {NSDECL}><p:tnLst><p:par><p:cTn id="1" dur="indefinite" restart="never" nodeType="tmRoot">'
        f'<p:childTnLst><p:seq concurrent="1" nextAc="seek"><p:cTn id="2" dur="indefinite" nodeType="mainSeq">'
        f'<p:childTnLst>{pars}</p:childTnLst></p:cTn>'
        '<p:prevCondLst><p:cond evt="onPrev" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst>'
        '<p:nextCondLst><p:cond evt="onNext" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst></p:seq>'
        f'</p:childTnLst></p:cTn></p:par></p:tnLst><p:bldLst>{bld}</p:bldLst></p:timing>')
    ext = slide._element.find(f"{{{NS_P}}}extLst")      # p:timing comes before p:extLst in the schema
    if ext is not None:
        ext.addprevious(timing)
    else:
        slide._element.append(timing)


def starter(out, spec):
    prs = Presentation(out)
    lay = {l.name: l for l in prs.slide_layouts}
    for name, content, opt in spec:
        s = prs.slides.add_slide(lay[name])
        phs = {p.placeholder_format.idx: p for p in s.placeholders}
        for idx, value in content.items():
            fill(phs[idx], value)
        if "table" in opt:
            rows, cols, header = opt["table"]
            tbl = plain_table(phs[21], rows, cols, header)
            for r in range(1, rows):
                set_cell(tbl, r, 0, f"<row {r}>")
        if opt.get("appear"):
            appear_on_click(s, [phs[i] for i in opt["appear"]])
        if opt.get("notes"):
            tf = s.notes_slide.notes_text_frame
            tf.text = opt["notes"]
            set_lang(tf)
    if any(opt.get("notes") for _, _, opt in spec):
        # python-pptx creates the notes master with its own theme (Calibri); give it the deck's fonts.
        theme = prs.notes_master.part.part_related_by(RT.THEME)
        fixed = theme_fonts(theme.blob)
        if hasattr(theme, "_element"):      # an XML part is saved from its element, a plain part from its blob
            theme._element = parse_xml(fixed)
        else:
            theme._blob = fixed
    prs.save(out)
    post_process(out)


def make_deck(out, kind="blank", template=HERE / TEMPLATE_NAME, force=False):
    """Write a new deck to out: a .pptx, or a PowerPoint template if out ends in .potx. It is built under a temporary name in the same folder and moved into
    place when complete. An existing out stops the run unless force is given; the template itself is never
    replaced. A symbolic link at out is replaced by the deck, not followed."""
    out = Path(out)
    out = out.parent.resolve() / out.name               # resolve the folder, not a link at the final name
    if out.suffix.lower() not in (".pptx", ".potx"):
        raise ValueError(f"{out.name}: the output must be a .pptx (or .potx) file")
    if out.exists() and os.path.samefile(out, template):
        raise ValueError(f"{out} is the template itself; choose another output name")
    refuse_existing([out], force)
    with tempfile.TemporaryDirectory(prefix=".new_deck.", dir=out.parent) as work:
        tmp = Path(work) / out.name
        blank(Path(template), tmp)
        if kind != "blank":
            starter(tmp, STARTERS[kind])
        if out.suffix.lower() == ".potx":
            post_process(tmp, template=True)
        publish(tmp, out)
    return out


def main():
    ap = argparse.ArgumentParser(description="Start a new deck from the medsci slide template.")
    ap.add_argument("out")
    ap.add_argument("--type", choices=["blank"] + list(STARTERS), default="blank")
    ap.add_argument("--template", default=str(HERE / TEMPLATE_NAME))
    ap.add_argument("--force", action="store_true", help="replace OUT if it exists")
    a = ap.parse_args()
    try:
        print(make_deck(a.out, a.type, a.template, a.force))
    except (OutputExists, ValueError) as e:
        raise SystemExit(str(e))


if __name__ == "__main__":
    main()
