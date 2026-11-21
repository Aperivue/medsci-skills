#!/usr/bin/env python3
"""Build a plain handout template for a talk or lecture, as a Word file.

    python3 build_handout_template.py [OUT_DIR] [--palette mono|stone|pine]

Writes OUT_DIR/medsci_handout.docx (default: this folder). Laid out for one page, with
<angle-bracket> text to overwrite:

    title block          talk title, presenter, event and date
    learning objectives  three numbered lines
    key points           one short paragraph per point, its term in bold
    figure and notes     one figure with a caption, then ruled lines for the reader's notes
    references           a numbered list (generate it with a reference manager, not by hand)

Same type and colours as the slide template: Arial for Latin text, Malgun Gothic for Korean, black
headings, the palette's accent used nowhere by default. No table, no box, no picture. A handout is
read after the talk, so it carries the sentences the slides left out.

Dependencies: python-docx, lxml, and python-pptx (the palette and font settings are shared with
build_slide_template.py, which imports it).
"""
import argparse
import datetime
import sys
import tempfile
import zipfile
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from build_slide_template import (AUTHOR, DEFAULT_PALETTE, EA, FIXED_DATE, LATIN, PALETTES,  # noqa: E402
                                  OutputExists, drop_removed, publish, refuse_existing, resolve_palette,
                                  theme_fonts, write_zip)

STEM = "medsci_handout"


def rgb(hexv):
    return RGBColor.from_string(hexv)


def set_fonts(style_or_run_element):
    """Latin and East Asian font on a style's or a run's rPr, with theme font references removed."""
    rpr = style_or_run_element.get_or_add_rPr()
    fonts = rpr.find(qn("w:rFonts"))
    if fonts is None:
        fonts = OxmlElement("w:rFonts")
        rpr.insert(0, fonts)
    for attr in list(fonts.attrib):
        del fonts.attrib[attr]
    for attr, face in (("w:ascii", LATIN), ("w:hAnsi", LATIN), ("w:cs", LATIN), ("w:eastAsia", EA)):
        fonts.set(qn(attr), face)


def style(doc, name, size, bold=False, color="111111", before=0, after=6, italic=False):
    st = doc.styles[name]
    st.font.size = Pt(size)
    st.font.bold = bold
    st.font.italic = italic
    st.font.color.rgb = rgb(color)
    set_fonts(st.element)
    pf = st.paragraph_format
    pf.space_before, pf.space_after = Pt(before), Pt(after)
    return st


def note_line(paragraph, width_cm):
    """One ruled line for handwriting: a right tab across the text width whose leader is a line. (Paragraph
    borders would merge into a single line when several lines follow one another.)"""
    paragraph.paragraph_format.tab_stops.add_tab_stop(Cm(width_cm), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.LINES)
    paragraph.add_run("\t")


def restart_numbering(doc, paragraphs):
    """Number these List Number paragraphs from 1 again, instead of continuing the list above."""
    numbering = doc.part.numbering_part.numbering_definitions._numbering
    style_num = doc.styles["List Number"].element.pPr.numPr.numId.val
    abstract = numbering.num_having_numId(style_num).abstractNumId.val
    num = numbering.add_num(abstract)
    override = num.add_lvlOverride(ilvl=0)
    override.add_startOverride(1)
    for p in paragraphs:
        p._p.get_or_add_pPr().get_or_add_numPr().get_or_add_numId().val = num.numId
        p._p.pPr.numPr.get_or_add_ilvl().val = 0


def no_border(style_obj):
    ppr = style_obj.element.pPr
    if ppr is not None:
        for b in ppr.findall(qn("w:pBdr")):
            ppr.remove(b)


def build(out_dir, palette=DEFAULT_PALETTE, force=False):
    """Write OUT_DIR/medsci_handout.docx. Without force an existing file is not replaced."""
    pal = resolve_palette(palette)
    out_dir = Path(out_dir)
    path = out_dir / f"{STEM}.docx"
    refuse_existing([path], force)
    out_dir.mkdir(parents=True, exist_ok=True)
    doc = Document()
    sec = doc.sections[0]
    sec.page_height, sec.page_width = Cm(29.7), Cm(21.0)          # A4; Letter users change it in Layout
    for side in ("left_margin", "right_margin", "top_margin", "bottom_margin"):
        setattr(sec, side, Cm(2.0))

    style(doc, "Normal", 11, color=pal["ink"], after=4)
    no_border(style(doc, "Title", 20, bold=True, color=pal["ink"], after=4))   # Word's default Title has a blue rule
    style(doc, "Heading 1", 13, bold=True, color=pal["ink"], before=14, after=4)
    style(doc, "Caption", 9.5, color=pal["muted"], after=8)
    for name in ("List Number",):
        style(doc, name, 11, color=pal["ink"], after=2)
    doc.styles["Normal"].paragraph_format.line_spacing = 1.15

    doc.add_paragraph("<Talk or lecture title>", style="Title")
    meta = doc.add_paragraph("<Presenter> · <Event> · <Date>")
    meta.runs[0].font.color.rgb = rgb(pal["muted"])

    doc.add_paragraph("Learning objectives", style="Heading 1")
    doc.add_paragraph("After this talk you should be able to:")
    for line in ("<Do one thing: name, tell apart, decide, or measure>", "<Second objective>", "<Third objective>"):
        doc.add_paragraph(line, style="List Number")

    doc.add_paragraph("Key points", style="Heading 1")
    for term in ("<Term or finding>", "<Second point>", "<Third point>"):
        p = doc.add_paragraph()
        p.add_run(term + ". ").bold = True
        p.add_run("<Two or three sentences: what it is, how to recognise it, and what it changes. "
                  "Write the sentence the slide left out.>")

    doc.add_paragraph("Figure", style="Heading 1")
    fig = doc.add_paragraph("<Insert one figure here: the image the whole talk turns on, with labels on it>")
    fig.alignment = WD_ALIGN_PARAGRAPH.CENTER
    fig.paragraph_format.space_before = Pt(36)
    fig.paragraph_format.space_after = Pt(36)
    fig.runs[0].font.color.rgb = rgb(pal["muted"])
    doc.add_paragraph("Figure 1. <What it shows, and where to look. Source, if it is not yours.>", style="Caption")

    doc.add_paragraph("Notes", style="Heading 1")
    for _ in range(6):
        line = doc.add_paragraph()
        line.paragraph_format.space_before = Pt(10)
        note_line(line, 17.0)

    doc.add_paragraph("References", style="Heading 1")
    refs = [doc.add_paragraph(line, style="List Number")
            for line in ("<Reference 1, from a reference manager>", "<Reference 2>", "<Reference 3>")]
    restart_numbering(doc, refs)

    core = doc.core_properties
    stamp = datetime.datetime(*FIXED_DATE)
    core.title = "Handout template"
    core.author = core.last_modified_by = AUTHOR
    core.subject = core.keywords = core.comments = core.category = ""
    core.created = core.modified = stamp
    core.revision = 1

    with tempfile.TemporaryDirectory(prefix=".build.", dir=out_dir) as work:
        tmp = Path(work) / path.name
        doc.save(tmp)
        normalise(tmp)
        publish(tmp, path)
    return path


def normalise(path):
    """Theme fonts; no thumbnail and no relationship or content type left pointing at it; fixed zip entries,
    so rebuilding does not change the file."""
    with zipfile.ZipFile(path) as z:
        items = {n: z.read(n) for n in z.namelist()}
    removed = [n for n in items if n.startswith("docProps/thumbnail")]
    for n in removed:
        del items[n]
    # The theme's own fonts too, so a style this script does not touch (Heading 2, a table) is not Calibri.
    items["word/theme/theme1.xml"] = theme_fonts(items["word/theme/theme1.xml"])
    drop_removed(items, removed)
    write_zip(path, items)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("out_dir", nargs="?", default=str(HERE))
    ap.add_argument("--palette", choices=sorted(PALETTES), default=DEFAULT_PALETTE)
    ap.add_argument("--force", action="store_true", help="replace medsci_handout.docx if it exists")
    a = ap.parse_args()
    try:
        print("built", build(a.out_dir, a.palette, a.force).name)
    except OutputExists as e:
        raise SystemExit(str(e))


if __name__ == "__main__":
    main()
