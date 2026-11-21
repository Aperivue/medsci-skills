#!/usr/bin/env python3
"""Build the medsci slide template: one master, 31 layouts, no pictures.

    python3 build_slide_template.py [OUT_DIR] [--palette mono|stone|pine]
                                    [--palette-file colours.json] [--ink HEX] [--accent HEX] ... [--force]

Writes into OUT_DIR (default: this folder); an existing output is replaced only with --force:

    medsci_slides.pptx          the template: 31 layouts and no slides (new_deck.py starts a deck from it)
    medsci_slides_sample.pptx   the same with one sample slide per layout (synthetic text), for previewing

The template ships as a .pptx, not a .potx: PowerPoint opens either, and the repository's content
checks read .pptx. `new_deck.py my_template.potx` writes a .potx when one is wanted.

What is in it

  * White ground, near-black text, one accent colour. No band, no rule and no panel on the
    research-talk layouts: space and type size separate the parts of a slide. The page number sits
    bottom right. The master carries no logo and the file embeds no picture.
  * Cover and Closing stand on their own. Each has an optional picture placeholder and an optional
    logo placeholder; an empty placeholder does not show in a slide show or in an exported PDF.
    Closing carries a one-line conclusion and a contact line.
  * Ten research-talk layouts (Disclosure ... References · QR) with real placeholders, so a deck can
    be filled by layout name and placeholder idx (README, "Filling a deck from a script").
  * Teaching layouts carry an optional section name above the title, in small grey type; left
    empty, it does not show.
  * Black "Imaging" layouts for image-heavy talks. They flip the colour map (clrMapOvr), so text
    typed on them comes out white.

Colours: three palettes (PALETTES), or your own through --palette-file and the per-role options.
Every palette is checked for contrast before anything is written (WCAG AA, 4.5:1, for each text
role against the ground it is set on); a palette that fails stops the build with the pairs that
failed.

The XML is written by hand through python-pptx because python-pptx cannot create layouts or
placeholders. Dependencies: python-pptx, lxml.
"""
import argparse
import colorsys
import copy
import datetime
import io
import json
import os
import re
import tempfile
import threading
import zipfile
from pathlib import Path

from lxml import etree
from pptx import Presentation
from pptx.opc.constants import RELATIONSHIP_TYPE as RT
from pptx.oxml import parse_xml
from pptx.parts.slide import SlideLayoutPart
from pptx.util import Emu

HERE = Path(__file__).resolve().parent
STEM = "medsci_slides"
TEMPLATE_NAME = f"{STEM}.pptx"           # the shipped template: no slides
SAMPLE_NAME = f"{STEM}_sample.pptx"      # one slide per layout, not shipped
THEME_NAME = "medsci slides"
AUTHOR = "medsci-skills"   # neutral document author, so a saved copy carries nobody's name until its owner adds it
SW, SH = 13.333, 7.5

# role -> hex.
#   ink        text on white                 section     ground of the Section divider (white text on it)
#   accent     the one emphasis on white      accent_dk   the one emphasis on black
#   muted      captions, sources, labels,     paper       a light ground, offered in the colour picker
#              bullets, page number
# None of them is navy or red. The accent is spent by the template in one place (the number on Key
# Finding); elsewhere it is the speaker's, once per slide.
ROLES = ("ink", "section", "accent", "accent_dk", "muted", "paper")
PALETTES = {
    "mono": dict(        # editorial_mono.md: near-black ink, grey, one blue accent
        ink="111111", section="111111", accent="0050C8", accent_dk="4DA3FF", muted="6E6E6E", paper="FAFAF7"),
    "stone": dict(       # warm greys, a dark ochre accent; prints well in greyscale
        ink="1C1B19", section="2B2925", accent="7A4E00", accent_dk="E0B25A", muted="66615A", paper="F7F5F0"),
    "pine": dict(        # cool greys, a deep green accent
        ink="15191A", section="1E2B27", accent="1D6A4F", accent_dk="7FD1AE", muted="5B6763", paper="F4F7F5"),
}
DEFAULT_PALETTE = "mono"
FIXED = dict(white="FFFFFF", black="000000",
             num_dark="A3A3A3",   # page number, section name and prompts on black
             label="FFD400")      # annotation yellow for labels laid over an image
C = {}
AA = 4.5   # WCAG 2.x AA contrast for body-size text

NS_A = "http://schemas.openxmlformats.org/drawingml/2006/main"
NS_P = "http://schemas.openxmlformats.org/presentationml/2006/main"
NS_R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NSDECL = f'xmlns:a="{NS_A}" xmlns:p="{NS_P}" xmlns:r="{NS_R}"'
LATIN, EA = "Arial", "Malgun Gothic"   # both ship with Windows; Arial ships with macOS too

SECTION_Y, SECTION_H = 0.20, 0.38   # section name, above the title, teaching layouts only; ends where the title starts
TITLE_Y, TITLE_H = 0.58, 0.92
MARGIN = 0.55
EDGE = 0.25            # page number distance from the slide edge
NUM_W = 0.45
CW = SW - 2 * MARGIN   # content width
BODY_TOP, BODY_H = 1.68, 5.1
SOURCE_Y = 6.93        # one small source line, level with the page number


# ---------------------------------------------------------------- colours
class PaletteError(ValueError):
    pass


HEX = re.compile(r"#?([0-9A-Fa-f]{6})")


def norm_hex(value, role="colour"):
    if not isinstance(value, str):
        raise PaletteError(f"{role}: {value!r} is not a hex colour string (write it in quotes, e.g. \"1A1A1A\")")
    m = HEX.fullmatch(value.strip())
    if not m:
        raise PaletteError(f"{role}: {value!r} is not a six-digit hex colour (e.g. 1A1A1A or #1A1A1A)")
    return m.group(1).upper()


def luminance(hexv):
    def ch(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (int(hexv[i:i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)


def contrast(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def lightened(hexv, mod=0.75, off=0.25):
    """The colour DrawingML draws for schemeClr with lumMod/lumOff (HSL lightness L*mod + off): the
    second to fifth text levels on white slides are the ink lightened this way."""
    r, g, b = (int(hexv[i:i + 2], 16) / 255 for i in (0, 2, 4))
    h, lum, sat = colorsys.rgb_to_hls(r, g, b)
    r, g, b = colorsys.hls_to_rgb(h, min(1.0, lum * mod + off), sat)
    return "".join(f"{round(v * 255):02X}" for v in (r, g, b))


NON_TEXT = 3.0   # WCAG 2.x 1.4.11 for a graphic such as a bullet glyph


def contrast_failures(pal):
    """[(description, ratio, required), ...] for every colour pair the template draws below its WCAG level.

    The pairs are the ones on the slides, not only the obvious ones: the page number and section number on
    the Section ground, the lightened lower text levels on white, and the bullets (muted) on the black
    Imaging layouts."""
    w, k = FIXED["white"], FIXED["black"]
    pairs = [("ink on white", pal["ink"], w, AA), ("muted on white", pal["muted"], w, AA),
             ("accent on white", pal["accent"], w, AA), ("lower text levels on white", lightened(pal["ink"]), w, AA),
             ("white on section", w, pal["section"], AA),
             ("page and section number on section", FIXED["num_dark"], pal["section"], AA),
             ("accent_dk on black", pal["accent_dk"], k, AA), ("ink on paper", pal["ink"], pal["paper"], AA),
             ("muted on paper", pal["muted"], pal["paper"], AA), ("bullets (muted) on black", pal["muted"], k, NON_TEXT)]
    return [(name, contrast(a, b), need) for name, a, b, need in pairs if contrast(a, b) < need]


def resolve_palette(name=DEFAULT_PALETTE, overrides=None):
    """A complete, validated palette: a named one with any roles replaced. Raises PaletteError."""
    if name not in PALETTES:
        raise PaletteError(f"unknown palette {name!r}; choose one of {', '.join(sorted(PALETTES))}")
    pal = dict(PALETTES[name])
    for role, value in (overrides or {}).items():
        if role not in ROLES:
            raise PaletteError(f"unknown colour role {role!r}; roles are {', '.join(ROLES)}")
        pal[role] = norm_hex(value, role)
    bad = contrast_failures(pal)
    if bad:
        lines = "; ".join(f"{d} is {r:.2f}:1 (needs {need}:1)" for d, r, need in bad)
        raise PaletteError(f"contrast below WCAG AA: {lines}. Change the colours named so the pair separates.")
    return pal


def load_palette_file(path):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as e:
        raise PaletteError(f"{path}: cannot read a JSON object of colours ({e})") from None
    if not isinstance(data, dict):
        raise PaletteError(f"{path}: expected a JSON object such as {{\"accent\": \"1D6A4F\"}}")
    return data


def set_palette(name=DEFAULT_PALETTE, overrides=None):
    pal = resolve_palette(name, overrides)
    C.clear()
    C.update(FIXED)
    C.update(pal)
    return pal


def E(inches):
    return int(round(inches * 914400))


def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


class Ids:
    def __init__(self, start=1):
        self.n = start

    def __call__(self):
        self.n += 1
        return self.n


# ---------------------------------------------------------------- XML snippets
def xfrm(x, y, w, h):
    return f'<a:xfrm><a:off x="{E(x)}" y="{E(y)}"/><a:ext cx="{E(w)}" cy="{E(h)}"/></a:xfrm>'


def fill(hexv):
    if hexv is None:
        return "<a:noFill/>"
    return f'<a:solidFill><a:srgbClr val="{hexv}"/></a:solidFill>'


def rpr(size=None, color=None, bold=None, caps=False, spc=None, font="+mn", tag="a:rPr"):
    attrs = ['lang="en-US"'] if tag == "a:rPr" else []
    if size:
        attrs.append(f'sz="{int(size * 100)}"')
    if bold is not None:
        attrs.append(f'b="{1 if bold else 0}"')
    if caps:
        attrs.append('cap="all"')
    if spc is not None:
        attrs.append(f'spc="{spc}"')
    if tag == "a:rPr":
        attrs.append('dirty="0"')
    inner = fill(color) if color else ""
    inner += f'<a:latin typeface="{font}-lt"/><a:ea typeface="{font}-ea"/>'
    a = (" " + " ".join(attrs)) if attrs else ""
    return f"<{tag}{a}>{inner}</{tag}>"


def body_pr(anchor="t", shrink=False):
    fit = "<a:normAutofit/>" if shrink else "<a:noAutofit/>"
    return f'<a:bodyPr wrap="square" lIns="0" tIns="0" rIns="0" bIns="0" rtlCol="0" anchor="{anchor}">{fit}</a:bodyPr>'


def nv_sp(ids, name, txbox=False):
    c = '<p:cNvSpPr txBox="1"/>' if txbox else "<p:cNvSpPr/>"
    return f'<p:nvSpPr><p:cNvPr id="{ids()}" name="{esc(name)}"/>{c}<p:nvPr userDrawn="1"/></p:nvSpPr>'


def textbox(ids, name, x, y, w, h, runs_xml, algn="l", anchor="t"):
    return (f"<p:sp>{nv_sp(ids, name, txbox=True)}<p:spPr>{xfrm(x, y, w, h)}"
            f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/></p:spPr>'
            f'<p:txBody>{body_pr(anchor)}<a:lstStyle/><a:p><a:pPr algn="{algn}"/>{runs_xml}</a:p></p:txBody></p:sp>')


def static_label(ids, text, x, y, w):
    """A fixed word naming the slot under it: small and light, so it reads as a label, not as content."""
    return textbox(ids, f"Label: {text}", x, y, w, 0.34, f"<a:r>{rpr(18, C['muted'])}<a:t>{esc(text)}</a:t></a:r>")


def page_number(ids, color, size=13):
    fld = (f'<a:fld id="{{B6F15528-21DE-4FAA-801E-634DDDAF4B2B}}" type="slidenum">'
           f"{rpr(size, color)}<a:t>‹#›</a:t></a:fld>")
    return textbox(ids, "Page number", SW - EDGE - NUM_W, SH - 0.43, NUM_W, 0.32, fld, algn="r", anchor="ctr")


def lvl1(algn="l", size=None, color=None, bold=None, caps=False, spc=None, font="+mn", lnspc=None, before=0,
         numbered=False):
    """First-level paragraph style of a placeholder. numbered=True gives a plain 1. 2. 3. list."""
    ls = f'<a:lnSpc><a:spcPct val="{lnspc * 1000}"/></a:lnSpc>' if lnspc else ""
    if numbered:
        head = f'<a:lvl1pPr marL="{E(0.55)}" indent="{-E(0.55)}" algn="{algn}">'
        bullet = (f'<a:buClr><a:srgbClr val="{C["muted"]}"/></a:buClr><a:buFont typeface="Arial"/>'
                  '<a:buAutoNum type="arabicPeriod"/>')
    else:
        head = f'<a:lvl1pPr marL="0" indent="0" algn="{algn}">'
        bullet = "<a:buNone/>"
    return (f'{head}{ls}<a:spcBef><a:spcPts val="{int(before * 100)}"/></a:spcBef>{bullet}'
            f"{rpr(size, color, bold, caps, spc, font, tag='a:defRPr')}</a:lvl1pPr>")


def placeholder(ids, name, ph, x, y, w, h, prompt, lst="", anchor="t", shrink=False):
    custom = ' hasCustomPrompt="1"' if prompt else ""
    para = (f"<a:p><a:r>{rpr()}<a:t>{esc(prompt)}</a:t></a:r></a:p>" if prompt
            else '<a:p><a:endParaRPr lang="en-US"/></a:p>')
    # A picture placeholder needs its own geometry: PowerPoint draws nothing for a pic that inherits an xfrm but no prstGeom.
    shape = '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>' if 'type="pic"' in ph else ""
    geo = f"<p:spPr>{xfrm(x, y, w, h)}{shape}</p:spPr>" if x is not None else "<p:spPr/>"
    return (f'<p:sp><p:nvSpPr><p:cNvPr id="{ids()}" name="{esc(name)}"/><p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr>'
            f"<p:nvPr><p:ph {ph}{custom}/></p:nvPr></p:nvSpPr>{geo}"
            f"<p:txBody>{body_pr(anchor, shrink)}<a:lstStyle>{lst}</a:lstStyle>{para}</p:txBody></p:sp>")


def inherited(ids, kind, prompt="Click to edit title"):
    """Title / body placeholders that take position and format from the master."""
    if kind == "title":
        custom = ' hasCustomPrompt="1"' if prompt != "Click to edit title" else ""
        return (f'<p:sp><p:nvSpPr><p:cNvPr id="{ids()}" name="Title"/><p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr>'
                f'<p:nvPr><p:ph type="title"{custom}/></p:nvPr>'
                f'</p:nvSpPr><p:spPr/><p:txBody><a:bodyPr/><a:lstStyle/>'
                f'<a:p><a:r>{rpr()}<a:t>{esc(prompt)}</a:t></a:r></a:p></p:txBody></p:sp>')
    levels = "".join(f'<a:p><a:pPr lvl="{k}"/><a:r>{rpr()}<a:t>{t}</a:t></a:r></a:p>'
                     for k, t in enumerate(["First level", "Second level", "Third level"]))
    return (f'<p:sp><p:nvSpPr><p:cNvPr id="{ids()}" name="Content"/><p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr>'
            f'<p:nvPr><p:ph idx="1"/></p:nvPr></p:nvSpPr><p:spPr/><p:txBody><a:bodyPr/><a:lstStyle/>{levels}</p:txBody></p:sp>')


def section_label(ids, color=None):
    """The section name above the title: plain grey text, no band. Left empty, it does not show."""
    return placeholder(ids, "Section name", 'type="body" sz="quarter" idx="20"', MARGIN, SECTION_Y, 8.0, SECTION_H,
                       "Section name (optional)", lvl1("l", 16, color or C["muted"]), anchor="b")


def sp_tree(shapes):
    return ('<p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
            '<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/>'
            f'<a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>{"".join(shapes)}</p:spTree>')


def bg_solid(hexv):
    return f'<p:bg><p:bgPr><a:solidFill><a:srgbClr val="{hexv}"/></a:solidFill><a:effectLst/></p:bgPr></p:bg>'


# On black, links take the dark-ground accent (accent2) and the grey checked on black (accent6), not the
# white-ground accent, which may be too dark to read there.
DARK_MAP = ('<a:overrideClrMapping bg1="dk1" tx1="lt1" bg2="dk2" tx2="lt2" accent1="accent1" accent2="accent2" '
            'accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="accent2" '
            'folHlink="accent6"/>')


def layout_xml(name, ltype, shapes, show_master=True, bg=None, dark=False):
    sm = "" if show_master else ' showMasterSp="0"'
    cm = DARK_MAP if dark else "<a:masterClrMapping/>"
    return (f'<p:sldLayout {NSDECL} type="{ltype}" preserve="1"{sm}><p:cSld name="{esc(name)}">'
            f'{bg_solid(bg) if bg else ""}{sp_tree(shapes)}</p:cSld><p:clrMapOvr>{cm}</p:clrMapOvr></p:sldLayout>')


# ---------------------------------------------------------------- theme / master styles
def theme_xml(base_blob):
    root = etree.fromstring(base_blob)
    ns = {"a": NS_A}
    root.set("name", THEME_NAME)
    cs = root.find(".//a:clrScheme", ns)
    cs.set("name", THEME_NAME)
    # accent1 = emphasis on white, accent2 = emphasis on black: the first two swatches in the colour picker.
    scheme = dict(dk1=C["ink"], lt1=C["white"], dk2=C["section"], lt2=C["paper"], accent1=C["accent"],
                  accent2=C["accent_dk"], accent3=C["muted"], accent4=C["section"], accent5=C["muted"],
                  accent6=C["num_dark"], hlink=C["accent"], folHlink=C["muted"])
    for child in list(cs):
        cs.remove(child)
    for k, v in scheme.items():
        el = etree.SubElement(cs, f"{{{NS_A}}}{k}")
        etree.SubElement(el, f"{{{NS_A}}}srgbClr").set("val", v)
    return theme_fonts(etree.tostring(root))


def theme_fonts(blob):
    """Arial + Malgun Gothic as a theme's major and minor fonts, with every other script entry removed.
    Also used on the notes master's theme, which python-pptx creates with Calibri."""
    root = etree.fromstring(blob)
    ns = {"a": NS_A}
    fs = root.find(".//a:fontScheme", ns)
    fs.set("name", THEME_NAME)
    for tag in ("majorFont", "minorFont"):
        f = fs.find(f"a:{tag}", ns)
        for child in list(f):
            f.remove(child)
        etree.SubElement(f, f"{{{NS_A}}}latin").set("typeface", LATIN)
        etree.SubElement(f, f"{{{NS_A}}}ea").set("typeface", EA)
        etree.SubElement(f, f"{{{NS_A}}}cs").set("typeface", "")
        hang = etree.SubElement(f, f"{{{NS_A}}}font")
        hang.set("script", "Hang")
        hang.set("typeface", EA)
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)


def tx1(gray=False):
    mod = '<a:lumMod val="75000"/><a:lumOff val="25000"/>' if gray else ""
    return f'<a:solidFill><a:schemeClr val="tx1">{mod}</a:schemeClr></a:solidFill>'


def txstyles():
    def lv(n, marl, ind, size, bu, before, gray):
        return (f'<a:lvl{n}pPr marL="{E(marl)}" indent="{E(ind)}" algn="l" defTabSz="914400" rtl="0" eaLnBrk="1" '
                f'latinLnBrk="0" hangingPunct="1"><a:lnSpc><a:spcPct val="100000"/></a:lnSpc>'
                f'<a:spcBef><a:spcPts val="{before}"/></a:spcBef>'
                f'<a:buClr><a:schemeClr val="accent3"/></a:buClr><a:buFont typeface="Arial"/><a:buChar char="{bu}"/>'
                f'<a:defRPr sz="{size * 100}" kern="1200">{tx1(gray)}'
                f'<a:latin typeface="+mn-lt"/><a:ea typeface="+mn-ea"/><a:cs typeface="+mn-cs"/></a:defRPr></a:lvl{n}pPr>')
    title = ('<p:titleStyle><a:lvl1pPr algn="l" defTabSz="914400" rtl="0" eaLnBrk="1" latinLnBrk="0" hangingPunct="1">'
             '<a:lnSpc><a:spcPct val="95000"/></a:lnSpc><a:spcBef><a:spcPct val="0"/></a:spcBef><a:buNone/>'
             f'<a:defRPr sz="2800" b="1" kern="1200">{tx1()}'
             '<a:latin typeface="+mj-lt"/><a:ea typeface="+mj-ea"/><a:cs typeface="+mj-cs"/></a:defRPr></a:lvl1pPr></p:titleStyle>')
    body = ("<p:bodyStyle>" + lv(1, 0.30, -0.30, 22, "•", 1200, False) + lv(2, 0.64, -0.28, 20, "–", 600, True)
            + lv(3, 0.98, -0.26, 18, "·", 400, True) + lv(4, 1.28, -0.24, 18, "·", 400, True)
            + lv(5, 1.58, -0.24, 18, "·", 400, True) + "</p:bodyStyle>")
    other = ('<p:otherStyle><a:defPPr><a:defRPr lang="en-US"/></a:defPPr>'
             '<a:lvl1pPr marL="0" algn="l" defTabSz="914400" rtl="0" eaLnBrk="1" latinLnBrk="0" hangingPunct="1">'
             f'<a:defRPr sz="1800" kern="1200">{tx1()}'
             '<a:latin typeface="+mn-lt"/><a:ea typeface="+mn-ea"/><a:cs typeface="+mn-cs"/></a:defRPr></a:lvl1pPr>'
             '</p:otherStyle>')
    return f"<p:txStyles {NSDECL}>{title}{body}{other}</p:txStyles>"


# ---------------------------------------------------------------- shared pieces
def pic_ph(ids, name, idx, x, y, w, h, prompt="Image", color=None):
    return placeholder(ids, name, f'type="pic" sz="quarter" idx="{idx}"', x, y, w, h, prompt,
                       lvl1("ctr", 14, color or C["num_dark"]))


def text_ph(ids, name, idx, x, y, w, h, prompt, size=20, color=None, bold=None, anchor="t", before=0, font="+mn",
            numbered=False):
    """A plain text slot: no bullet, one size, left-aligned."""
    kind = 'type="body"' if idx == 1 else 'type="body" sz="quarter"'
    return placeholder(ids, name, f'{kind} idx="{idx}"', x, y, w, h, prompt,
                       lvl1("l", size, color, bold, font=font, before=before, numbered=numbered), anchor=anchor)


def body_ph(ids, name, x, y, w, h, prompt, idx=1):
    """A body slot that keeps the master's bullet levels."""
    return placeholder(ids, name, f'type="body" idx="{idx}"', x, y, w, h, prompt)


def source_ph(ids, idx):
    return text_ph(ids, "Source", idx, MARGIN, SOURCE_Y, 10.8, 0.32, "Source or footnote (optional)", 14, C["muted"],
                   anchor="ctr")


def research_layout(ids, name, shapes, title_prompt, ltype="cust"):
    """White ground, the master's page number and an inherited title. No section name: a ten-minute talk has no
    sections to name, and a label above every title is the first thing that makes a deck look generated."""
    return layout_xml(name, ltype, [inherited(ids, "title", title_prompt)] + shapes)


# ---------------------------------------------------------------- general layouts
OPT_PIC_X = 8.2    # Cover / Closing: the optional picture takes the right part of the slide, full height


def cover_layout(ids):
    x, w = 0.8, 6.9
    shapes = [
        pic_ph(ids, "Cover picture (optional)", 16, OPT_PIC_X, 0, SW - OPT_PIC_X, SH,
               "Cover picture (optional)", C["muted"]),
        pic_ph(ids, "Logo (optional)", 15, x, 0.6, 2.2, 0.62, "Logo (optional)", C["muted"]),
        placeholder(ids, "Event", 'type="body" sz="quarter" idx="13"', x, 1.55, w, 0.45, "Meeting · Session",
                    lvl1("l", 18, C["muted"]), anchor="b"),
        placeholder(ids, "Title", 'type="ctrTitle"', x, 2.16, w, 2.5, "Presentation title",
                    lvl1("l", 36, C["ink"], True, font="+mj", lnspc=95), anchor="t", shrink=True),
        placeholder(ids, "Presenter", 'type="subTitle" idx="1"', x, 4.85, w, 0.6, "Presenter",
                    lvl1("l", 22, C["ink"], True), anchor="b"),
        placeholder(ids, "Affiliation", 'type="body" sz="quarter" idx="14"', x, 5.55, w, 1.1, "Affiliation",
                    lvl1("l", 18, C["muted"])),
    ]
    return layout_xml("Cover", "title", shapes, show_master=False, bg=C["white"])


def section_layout(ids):
    """A plain divider: the section colour as ground, a number, a title, one optional line. Nothing drawn."""
    shapes = [
        placeholder(ids, "Section number", 'type="body" sz="quarter" idx="13"', 0.8, 1.70, 3.0, 1.05, "01",
                    lvl1("l", 44, C["num_dark"], font="+mj"), anchor="b"),
        placeholder(ids, "Section title", 'type="title"', 0.8, 2.85, 10.0, 1.35, "Section title",
                    lvl1("l", 40, C["white"], True, font="+mj", lnspc=95)),
        placeholder(ids, "Section subtitle", 'type="body" sz="quarter" idx="14"', 0.8, 4.30, 10.0, 0.9,
                    "One line on what this part covers (optional)", lvl1("l", 22, C["white"])),
        page_number(ids, C["num_dark"]),
    ]
    return layout_xml("Section", "secHead", shapes, show_master=False, bg=C["section"])


def closing_layout(ids):
    """The last slide: the conclusion in one line, and how to reach the speaker. Not a thank-you slide."""
    x, w = 0.8, 6.9
    shapes = [
        pic_ph(ids, "Closing picture (optional)", 16, OPT_PIC_X, 0, SW - OPT_PIC_X, SH,
               "Closing picture (optional)", C["muted"]),
        pic_ph(ids, "Logo (optional)", 15, x, 0.6, 2.2, 0.62, "Logo (optional)", C["muted"]),
        placeholder(ids, "Conclusion", 'type="title"', x, 2.2, w, 2.4, "The one-line conclusion",
                    lvl1("l", 32, C["ink"], True, font="+mj", lnspc=100), anchor="b", shrink=True),
        placeholder(ids, "Contact", 'type="body" sz="quarter" idx="13"', x, 4.85, w, 1.0,
                    "Name · email or handle · where the slides are", lvl1("l", 20, C["muted"])),
    ]
    return layout_xml("Closing", "cust", shapes, show_master=False, bg=C["white"])


def content_layout(ids, name, with_body):
    shapes = [section_label(ids), inherited(ids, "title")]
    if with_body:
        shapes.append(inherited(ids, "body"))
    return layout_xml(name, "obj" if with_body else "titleOnly", shapes)


def blank_layout(ids):
    return layout_xml("Blank", "blank", [page_number(ids, C["muted"])], show_master=False, bg=C["white"])


# ---------------------------------------------------------------- research-talk layouts
# Each is a title that states the point, then one arrangement that suits what the slide carries. No panels, no
# boxes, no icons: only text and one figure or table. The accent colour appears on Key Finding alone; elsewhere it
# is the speaker's to spend, once per slide.
def disclosure_layout(ids):
    w = 9.0
    return research_layout(ids, "Disclosure", [
        static_label(ids, "Conflicts of interest", MARGIN, 1.86, w),
        text_ph(ids, "Conflicts of interest", 1, MARGIN, 2.22, w, 1.9, "None, or one line per relationship", before=6),
        static_label(ids, "Funding", MARGIN, 4.42, w),
        text_ph(ids, "Funding", 13, MARGIN, 4.78, w, 1.5, "Funder and grant number, or none", before=6),
    ], "Disclosures")


def agenda_layout(ids):
    return research_layout(ids, "Agenda", [
        text_ph(ids, "Agenda items", 1, MARGIN, 1.95, 8.2, 4.7, "Three to five parts, in the order you will speak",
                24, before=16, numbered=True),
    ], "What the next minutes cover")


def key_finding_layout(ids):
    return research_layout(ids, "Key Finding", [
        text_ph(ids, "Number", 13, MARGIN, 1.75, 9.5, 2.35, "0.00", 115, C["accent"], True, anchor="b", font="+mj"),
        text_ph(ids, "Unit", 14, MARGIN, 4.28, 9.5, 0.55, "What the number measures, with its unit", 24, None, True),
        text_ph(ids, "Interval", 15, MARGIN, 4.95, 9.5, 0.5, "95% CI, lower to upper · n", 20, C["muted"]),
        source_ph(ids, 16),
    ], "The finding, as one sentence")


def study_design_layout(ids):
    fw = 8.2
    cx = MARGIN + fw + 0.45
    cw = SW - MARGIN - cx
    rows = [("Population", 13, 1.68, 1.25, "Who, how many, where from"),
            ("Period", 14, 3.38, 0.95, "From when to when"),
            ("Reference standard", 15, 4.78, 1.6, "What counted as the truth, and who read it")]
    shapes = [pic_ph(ids, "Flow diagram", 30, MARGIN, BODY_TOP, fw, BODY_H, "Flow diagram (drawn as code, inserted as an image)",
                     C["muted"])]
    for label, idx, y, h, prompt in rows:
        shapes += [static_label(ids, label, cx, y, cw), text_ph(ids, label, idx, cx, y + 0.36, cw, h - 0.36, prompt)]
    return research_layout(ids, "Study Design", shapes, "The design, as one sentence")


def result_figure_layout(ids):
    # No line under the title: the title says what the figure shows, and where to look is said aloud.
    top = BODY_TOP - 0.1
    return research_layout(ids, "Result · Figure", [
        pic_ph(ids, "Figure", 30, MARGIN, top, CW, 6.82 - top, "Figure (one per slide)", C["muted"]),
        source_ph(ids, 14),
    ], "What the figure shows, as one sentence")


def result_table_layout(ids):
    return research_layout(ids, "Result · Table", [
        placeholder(ids, "Table", 'type="tbl" sz="quarter" idx="21"', MARGIN, BODY_TOP, CW, 4.0,
                    "Table (a few rows; the full table goes in backup)", lvl1("ctr", 14, C["muted"])),
        text_ph(ids, "Takeaway", 13, MARGIN, 5.92, CW, 0.8, "One line: the row or column to read"),
        source_ph(ids, 14),
    ], "What the table shows, as one sentence", "tbl")


def comparison_layout(ids):
    gap = 0.65
    w = (CW - gap) / 2
    x2 = MARGIN + w + gap
    return research_layout(ids, "Comparison", [
        text_ph(ids, "Left header", 13, MARGIN, 1.78, w, 0.5, "Left column", 22, None, True, anchor="b"),
        text_ph(ids, "Right header", 14, x2, 1.78, w, 0.5, "Right column", 22, None, True, anchor="b"),
        body_ph(ids, "Left text", MARGIN, 2.48, w, 4.3, "Two or three lines"),
        body_ph(ids, "Right text", x2, 2.48, w, 4.3, "Two or three lines", idx=2),
    ], "How the two differ, as one sentence")


def limitations_layout(ids):
    lw = 4.9
    rx = MARGIN + lw + 0.5
    rw = SW - MARGIN - rx
    shapes = [static_label(ids, "Limitation", MARGIN, 1.74, lw),
              static_label(ids, "What it does to the result", rx, 1.74, rw)]
    for k in range(3):
        y = 2.16 + k * 1.55
        shapes += [text_ph(ids, f"Limitation {k + 1}", 13 + k, MARGIN, y, lw, 1.35, f"Limitation {k + 1}", 22, None, True),
                   text_ph(ids, f"Consequence {k + 1}", 16 + k, rx, y, rw, 1.35,
                           "Direction and rough size of the bias, or what was done about it")]
    return research_layout(ids, "Limitations", shapes, "Why the finding might be wrong")


def take_home_layout(ids):
    return research_layout(ids, "Take-home", [
        text_ph(ids, "Take-home lines", 1, MARGIN, 1.95, 10.6, 4.7, "Three lines the room should be able to repeat",
                30, before=24),
    ], "The finding, once more")


def references_qr_layout(ids):
    q = 2.85
    qx = SW - MARGIN - q
    return research_layout(ids, "References · QR", [
        text_ph(ids, "References", 1, MARGIN, BODY_TOP, qx - MARGIN - 0.6, BODY_H,
                "The few references the talk rests on", 20, before=8, numbered=True),
        pic_ph(ids, "QR code", 30, qx, BODY_TOP, q, q, "QR code", C["muted"]),
        text_ph(ids, "QR caption", 13, qx, BODY_TOP + q + 0.15, q, 0.9, "Where the code leads", 18, C["muted"]),
    ], "References")


# ---------------------------------------------------------------- teaching layouts
TOP = 1.30          # top of the image area under a one-line title on the black layouts
BOTTOM = 6.92       # stays clear of the page number
GAP = 0.12
LABEL_H = 0.42


def label_ph(ids, name, idx, x, y, w, prompt, algn="l"):
    # 20 pt: the floor for projected text. White on the black layouts through the colour-map flip.
    return placeholder(ids, name, f'type="body" sz="quarter" idx="{idx}"', x, y, w, LABEL_H, prompt,
                       lvl1(algn, 20, None, True), anchor="t")


def grid_title(ids, prompt):
    return placeholder(ids, "Title", 'type="title"', MARGIN, 0.58, CW, 0.62, prompt,
                       lvl1("l", 24, None, True, font="+mj"), anchor="ctr")


def dark_layout(ids, name, shapes):
    shapes = [section_label(ids, C["num_dark"])] + shapes + [page_number(ids, C["num_dark"])]
    return layout_xml(name, "cust", shapes, show_master=False, bg=C["black"], dark=True)


def table_layout(ids):
    shapes = [section_label(ids), inherited(ids, "title"),
              placeholder(ids, "Table", 'type="tbl" sz="quarter" idx="21"', MARGIN, BODY_TOP, CW, BODY_H,
                          "Roadmap or section summary table (click the icon to insert)", lvl1("ctr", 14, C["muted"]))]
    return layout_xml("Table", "tbl", shapes)


# Picture slots are square wherever one image fills them: CT, MR and DSA frames are mostly square, and a picture
# placeholder crops to fill, so a wide slot cuts the top and bottom of the anatomy.
def lessons_layout(ids):
    s = BODY_H
    bx = MARGIN + s + 0.35
    bw = SW - MARGIN - bx
    shapes = [section_label(ids), inherited(ids, "title"),
              pic_ph(ids, "Image", 30, MARGIN, BODY_TOP, s, s, color=C["muted"]),
              body_ph(ids, "Lessons text", bx, BODY_TOP + 0.1, bw, s - 0.1, "Two or three lines: what we learned")]
    return layout_xml("Lessons", "cust", shapes)


def imaging_layout(ids, name, with_body):
    shapes = [section_label(ids, C["num_dark"]), inherited(ids, "title")]
    if with_body:
        shapes.append(inherited(ids, "body"))
    shapes.append(page_number(ids, C["num_dark"]))
    return layout_xml(name, "obj" if with_body else "titleOnly", shapes, show_master=False, bg=C["black"], dark=True)


def imaging_blank(ids):
    return layout_xml("Imaging · Blank", "blank", [page_number(ids, C["num_dark"])], show_master=False,
                      bg=C["black"], dark=True)


def case_layout(ids):
    s = BOTTOM - TOP
    rx = MARGIN + s + 0.4
    return dark_layout(ids, "Imaging · Case", [
        grid_title(ids, "Age/sex · presentation · modality"),
        pic_ph(ids, "Image", 30, MARGIN, TOP, s, s),
        body_ph(ids, "Findings", rx, TOP, SW - MARGIN - rx, s, "Findings (appear on click)")])


def grid2x2_layout(ids):
    s = (BOTTOM - TOP - GAP) / 2
    shapes = [grid_title(ids, "Disease: typical findings")]
    seqs = ["T2WI", "T1WI", "T1CE", "DWI"]
    for k in range(4):
        x, y = MARGIN + (k % 2) * (s + GAP), TOP + (k // 2) * (s + GAP)
        shapes.append(pic_ph(ids, f"Image {k + 1}", 30 + k, x, y, s, s))
    for k in range(4):   # labels after the pictures so they stay on top
        x, y = MARGIN + (k % 2) * (s + GAP), TOP + (k // 2) * (s + GAP)
        shapes.append(label_ph(ids, f"Sequence {k + 1}", 40 + k, x + 0.08, y + 0.05, s - 0.16, seqs[k]))
    fx = MARGIN + 2 * s + GAP + 0.45
    shapes.append(body_ph(ids, "Findings", fx, TOP, SW - MARGIN - fx, BOTTOM - TOP, "Key findings (appear on click)"))
    return dark_layout(ids, "Imaging · 2×2", shapes)


def grid1x3_layout(ids):
    s = (CW - 2 * GAP) / 3
    shapes = [grid_title(ids, "Disease: key images")]
    seqs = ["DWI", "ADC", "T1CE"]
    for k in range(3):
        shapes.append(pic_ph(ids, f"Image {k + 1}", 30 + k, MARGIN + k * (s + GAP), TOP, s, s))
    for k in range(3):
        shapes.append(label_ph(ids, f"Sequence {k + 1}", 40 + k, MARGIN + k * (s + GAP) + 0.08, TOP + 0.05, s - 0.16, seqs[k]))
    y = TOP + s + 0.18
    shapes.append(body_ph(ids, "Findings", MARGIN, y, CW, BOTTOM - y, "One line per image (appear on click)"))
    return dark_layout(ids, "Imaging · 1×3", shapes)


def dsa_pair_layout(ids):
    s = BOTTOM - TOP - LABEL_H - 0.12
    gap = 0.3
    x0 = (SW - 2 * s - gap) / 2
    shapes = [grid_title(ids, "Vessel injected · working projection")]
    for k in range(2):
        shapes.append(pic_ph(ids, f"DSA {k + 1}", 30 + k, x0 + k * (s + gap), TOP, s, s))
    for k in range(2):   # under the panel: subtracted DSA is white, a white label inside would vanish
        shapes.append(label_ph(ids, f"Label {k + 1}", 40 + k, x0 + k * (s + gap), TOP + s + 0.1, s, "Projection · phase"))
    return dark_layout(ids, "Imaging · DSA Pair", shapes)


def steps4_layout(ids):
    s = (CW - 3 * GAP) / 4
    shapes = [grid_title(ids, "Procedure in four steps")]
    steps = ["1  Access", "2  Confirm", "3  Deploy", "4  Result"]
    for k in range(4):
        shapes.append(pic_ph(ids, f"Step {k + 1}", 30 + k, MARGIN + k * (s + GAP), TOP, s, s))
    for k in range(4):
        shapes.append(label_ph(ids, f"Step label {k + 1}", 40 + k, MARGIN + k * (s + GAP), TOP + s + 0.1, s, steps[k]))
    y = TOP + s + 0.1 + LABEL_H + 0.2
    shapes.append(body_ph(ids, "Note", MARGIN, y, CW, BOTTOM - y, "What changes at each step"))
    return dark_layout(ids, "Imaging · 4 Steps", shapes)


def quiz_layout(ids):
    s = BOTTOM - TOP
    rx = MARGIN + s + 0.4
    rw = SW - MARGIN - rx
    return dark_layout(ids, "Imaging · Quiz", [
        grid_title(ids, "Quiz 1"),
        pic_ph(ids, "Image", 30, MARGIN, TOP, s, s),
        body_ph(ids, "Question", rx, TOP, rw, 2.6, "Question"),
        placeholder(ids, "Answer", 'type="body" sz="quarter" idx="50"', rx, TOP + 2.9, rw, BOTTOM - TOP - 2.9,
                    "Answer (appears on click)", lvl1("l", 24, C["accent_dk"], True))])


# Full-screen image and dimmed-image summary. No band: the image is the slide. The title sits in the top-left corner.
# Dimming cannot live in the layout: layout shapes draw under the slide's picture, so a veil there would sit behind
# it. Give the picture itself transparency over the black ground (Picture Format > Transparency, about 55%).
def corner_title(ids, prompt, size=24):
    return placeholder(ids, "Title", 'type="title"', 0.35, 0.22, 8.5, 0.62, prompt,
                       lvl1("l", size, None, True, font="+mj"), anchor="t")


def free_label(ids, idx, x, y, w, prompt):
    return placeholder(ids, f"Label {idx - 39}", f'type="body" sz="quarter" idx="{idx}"', x, y, w, LABEL_H, prompt,
                       lvl1("l", 20, C["label"], True), anchor="t")


def full_layout(ids):
    return layout_xml("Imaging · Full", "cust", [
        pic_ph(ids, "Image", 30, 0, 0, SW, SH, "Image: crop to the region (Picture Format > Crop)"),
        corner_title(ids, "Structure or finding"),
        free_label(ids, 40, 0.35, SH - 1.35, 4.0, "Label (move next to the arrow)"),
        free_label(ids, 41, 0.35, SH - 0.85, 4.0, "Label"),
        page_number(ids, C["num_dark"])], show_master=False, bg=C["black"], dark=True)


def full_center_layout(ids):
    x0 = (SW - SH) / 2
    side = x0 - 0.5
    return layout_xml("Imaging · Full Center", "cust", [
        pic_ph(ids, "Image", 30, x0, 0, SH, SH, "Square image, full height"),
        corner_title(ids, "Structure or finding", 22),
        free_label(ids, 40, 0.35, 2.4, side, "Label left"),
        free_label(ids, 41, x0 + SH + 0.15, 2.4, side, "Label right"),
        page_number(ids, C["num_dark"])], show_master=False, bg=C["black"], dark=True)


def overlay_layout(ids, table):
    shapes = [pic_ph(ids, "Image (dimmed)", 30, 0, 0, SW, SH, "Background image: set transparency to about 55%"),
              placeholder(ids, "Title", 'type="title"', MARGIN, 0.45, CW, 0.8, "Summary",
                          lvl1("l", 30, None, True, font="+mj"), anchor="ctr")]
    if table:
        shapes.append(placeholder(ids, "Table", 'type="tbl" sz="quarter" idx="21"', MARGIN, 1.55, CW,
                                  5.3, "Summary table", lvl1("ctr", 14, C["num_dark"])))
    else:
        shapes.append(body_ph(ids, "Text", MARGIN, 1.55, 7.2, 5.3, "Two to four lines"))
    shapes.append(page_number(ids, C["num_dark"]))
    return layout_xml("Imaging · Overlay Table" if table else "Imaging · Overlay", "cust", shapes,
                      show_master=False, bg=C["black"], dark=True)


LAYOUTS = [
    ("Cover", cover_layout),
    ("Section", section_layout),
    ("Content", lambda ids: content_layout(ids, "Content", True)),
    ("Title Only", lambda ids: content_layout(ids, "Title Only", False)),
    ("Blank", blank_layout),
    ("Closing", closing_layout),
    ("Disclosure", disclosure_layout),
    ("Agenda", agenda_layout),
    ("Key Finding", key_finding_layout),
    ("Study Design", study_design_layout),
    ("Result · Figure", result_figure_layout),
    ("Result · Table", result_table_layout),
    ("Comparison", comparison_layout),
    ("Limitations", limitations_layout),
    ("Take-home", take_home_layout),
    ("References · QR", references_qr_layout),
    ("Table", table_layout),
    ("Lessons", lessons_layout),
    ("Imaging · Content", lambda ids: imaging_layout(ids, "Imaging · Content", True)),
    ("Imaging · Title Only", lambda ids: imaging_layout(ids, "Imaging · Title Only", False)),
    ("Imaging · Blank", imaging_blank),
    ("Imaging · Case", case_layout),
    ("Imaging · 2×2", grid2x2_layout),
    ("Imaging · 1×3", grid1x3_layout),
    ("Imaging · DSA Pair", dsa_pair_layout),
    ("Imaging · 4 Steps", steps4_layout),
    ("Imaging · Quiz", quiz_layout),
    ("Imaging · Full", full_layout),
    ("Imaging · Full Center", full_center_layout),
    ("Imaging · Overlay", lambda ids: overlay_layout(ids, False)),
    ("Imaging · Overlay Table", lambda ids: overlay_layout(ids, True)),
]


def add_layout_part(prs, src):
    """python-pptx cannot add layouts; clone a layout part and register it on the master (its XML is replaced next)."""
    master = prs.slide_master
    package = prs.part.package
    partname = package.next_partname("/ppt/slideLayouts/slideLayout%d.xml")
    part = SlideLayoutPart(partname, src.part.content_type, package, copy.deepcopy(src.part._element))
    part.relate_to(master.part, RT.SLIDE_MASTER)
    rid = master.part.relate_to(part, RT.SLIDE_LAYOUT)
    lst = master._element.find(f"{{{NS_P}}}sldLayoutIdLst")
    used = [int(e.get("id")) for e in lst] + [int(e.get("id")) for e in prs.part._element.iter(f"{{{NS_P}}}sldMasterId")]
    el = etree.SubElement(lst, f"{{{NS_P}}}sldLayoutId")
    el.set("id", str(max(used) + 1))
    el.set(f"{{{NS_R}}}id", rid)
    return part


def master_shapes(ids):
    shapes = [page_number(ids, C["muted"])]
    levels = "".join(f'<a:p><a:pPr lvl="{k}"/><a:r>{rpr()}<a:t>{t} level</a:t></a:r></a:p>'
                     for k, t in enumerate(["First", "Second", "Third", "Fourth", "Fifth"]))
    shapes += [
        f'<p:sp><p:nvSpPr><p:cNvPr id="{ids()}" name="Title"/><p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr>'
        f'<p:nvPr><p:ph type="title"/></p:nvPr></p:nvSpPr><p:spPr>{xfrm(MARGIN, TITLE_Y, CW, TITLE_H)}</p:spPr>'
        f'<p:txBody>{body_pr("ctr")}<a:lstStyle/><a:p><a:r>{rpr()}<a:t>Click to edit title</a:t></a:r></a:p></p:txBody></p:sp>',
        f'<p:sp><p:nvSpPr><p:cNvPr id="{ids()}" name="Text"/><p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr>'
        f'<p:nvPr><p:ph type="body" idx="1"/></p:nvPr></p:nvSpPr><p:spPr>{xfrm(MARGIN, BODY_TOP, CW, BODY_H)}</p:spPr>'
        f'<p:txBody>{body_pr("t")}<a:lstStyle/>{levels}</p:txBody></p:sp>',
    ]
    return shapes


# ---------------------------------------------------------------- helpers shared with new_deck.py
def layout_table(path):
    """[(layout name, [(idx, type, shape name), ...]), ...] read from a built file. The README table is this."""
    out = []
    with zipfile.ZipFile(path) as z:
        rels = etree.fromstring(z.read("ppt/slideMasters/_rels/slideMaster1.xml.rels"))
        target = {r.get("Id"): r.get("Target") for r in rels}
        master = etree.fromstring(z.read("ppt/slideMasters/slideMaster1.xml"))
        for lid in master.find(f"{{{NS_P}}}sldLayoutIdLst"):
            part = "ppt/slideLayouts/" + target[lid.get(f"{{{NS_R}}}id")].split("/")[-1]
            root = etree.fromstring(z.read(part))
            phs = []
            for sp in root.iter(f"{{{NS_P}}}sp"):
                ph = sp.find(f".//{{{NS_P}}}ph")
                if ph is not None:
                    name = sp.find(f".//{{{NS_P}}}cNvPr").get("name")
                    phs.append((int(ph.get("idx", "0")), ph.get("type", "obj"), name))
            out.append((root.find(f"{{{NS_P}}}cSld").get("name"), sorted(phs)))
    return out


def readme_rows(table):
    return [f"| {name} | " + (" · ".join(f"{i} {t} `{n}`" for i, t, n in phs) or "none") + " |" for name, phs in table]


def plain_table(placeholder_shape, rows, cols, header=None, size=20, row_h=0.6):
    """Insert a table with no fill and three rules (above the header, under it, under the last row).

    python-pptx's default is a table style with a filled header row and banded rows. Line and text colour follow
    the slide's text colour, so the same table is white on the black layouts.
    """
    slot_h = placeholder_shape.height
    frame = placeholder_shape.insert_table(rows, cols)
    tbl = frame.table
    pr = tbl._tbl.tblPr
    for child in list(pr):
        pr.remove(child)
    pr.set("firstRow", "1")
    pr.set("bandRow", "0")
    h = min(slot_h, E(row_h) * rows)
    for r in tbl.rows:
        r.height = int(h / rows)
    frame.height = int(h / rows) * rows

    def line(tag, w):
        if not w:
            return f'<a:{tag} xmlns:a="{NS_A}" w="0"><a:noFill/></a:{tag}>'
        return (f'<a:{tag} xmlns:a="{NS_A}" w="{w}" cap="flat" cmpd="sng" algn="ctr">'
                f'<a:solidFill><a:schemeClr val="tx1"/></a:solidFill><a:prstDash val="solid"/></a:{tag}>')

    for r in range(rows):
        for c in range(cols):
            cell = tbl.cell(r, c)
            tcpr = cell._tc.get_or_add_tcPr()
            for child in list(tcpr):
                tcpr.remove(child)
            top = 19050 if r == 0 else 0
            bottom = 19050 if r == rows - 1 else (9525 if r == 0 else 0)
            for xml in (line("lnL", 0), line("lnR", 0), line("lnT", top), line("lnB", bottom)):
                tcpr.append(etree.fromstring(xml))
            tcpr.append(etree.fromstring(f'<a:noFill xmlns:a="{NS_A}"/>'))
            cell.text = header[c] if (header and r == 0 and c < len(header)) else ""
            set_cell_font(cell, size, bold=(r == 0))
    return tbl


def set_cell_font(cell, size=20, bold=False):
    """Size, weight and the slide's text colour (tx1) on every run, set explicitly: without a table style a
    header row can otherwise take a light text colour from the presentation's default table style."""
    for p in cell.text_frame.paragraphs:
        for run in p.runs:
            run.font.size = Emu(int(size * 12700))
            run.font.bold = bold
            _text_colour(run._r.get_or_add_rPr())
        end = p._p.get_or_add_endParaRPr()
        end.set("sz", str(int(size * 100)))
        _text_colour(end)


def _text_colour(rpr):
    for old in rpr.findall(f"{{{NS_A}}}solidFill"):
        rpr.remove(old)
    fill_el = etree.fromstring(f'<a:solidFill xmlns:a="{NS_A}"><a:schemeClr val="tx1"/></a:solidFill>')
    rpr.insert(0, fill_el)


def set_cell(tbl, r, c, text, size=20, bold=False):
    cell = tbl.cell(r, c)
    cell.text = text
    set_cell_font(cell, size, bold)


FIXED_DATE = (2026, 1, 1, 0, 0, 0)   # zip entry time, so two builds of the same source are the same bytes
ZIP_SYSTEM = 3                        # "made on Unix" in every entry header, whichever system builds it
FILE_MODE = 0o644 << 16


class OutputExists(FileExistsError):
    pass


def write_zip(path, items):
    """Write {part name: bytes} as a zip at path: fixed entry dates, system and mode, [Content_Types].xml first,
    the rest sorted. Written to a unique temporary file in the same folder and moved over path when complete,
    so a failure never leaves a half-written file at path."""
    path = Path(path)
    fd, tmp = tempfile.mkstemp(prefix=f".{path.stem}.", suffix=".part", dir=path.parent)
    os.close(fd)
    os.chmod(tmp, file_mode(path))
    try:
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
            for n in sorted(items, key=lambda n: (n != "[Content_Types].xml", n)):
                info = zipfile.ZipInfo(n, FIXED_DATE)
                info.compress_type = zipfile.ZIP_DEFLATED
                info.create_system = ZIP_SYSTEM
                info.external_attr = FILE_MODE
                z.writestr(info, items[n])
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def file_mode(path):
    """The permission an output should end with: that of the file it replaces, else the usual default for a new
    file (0666 less the umask). mkstemp creates 0600, which would hide a shared deck from its readers."""
    try:
        return os.stat(path).st_mode & 0o777
    except FileNotFoundError:
        umask = os.umask(0)
        os.umask(umask)
        return 0o666 & ~umask


def refuse_existing(paths, force):
    """Stop before any work if an output exists and force is not given. Checked once, when the run starts."""
    existing = [str(p) for p in paths if Path(p).exists()]
    if existing and not force:
        raise OutputExists(f"{', '.join(existing)} already exists; not overwriting (pass --force to replace)")


def publish(tmp, final):
    """Move a finished file to its final name in one step (os.replace), keeping the mode of what it replaces."""
    tmp, final = Path(tmp), Path(final)
    os.chmod(tmp, file_mode(final))
    os.replace(tmp, final)
    return final


def drop_removed(items, removed):
    """Remove the relationships and content-type overrides that point at parts this script deleted (the
    thumbnail, printer settings). Any other broken reference is left as it is, for a check to report."""
    removed = set(removed)
    for rels_name in [n for n in items if n.endswith(".rels")]:
        rels = etree.fromstring(items[rels_name])
        base = rels_name.replace("_rels/", "").rsplit(".rels", 1)[0]
        folder = base.rsplit("/", 1)[0] if "/" in base else ""
        changed = False
        for rel in list(rels):
            if rel.get("TargetMode") == "External":
                continue
            target = rel.get("Target")
            part = target.lstrip("/") if target.startswith("/") else os.path.normpath(
                os.path.join(folder, target)).replace(os.sep, "/")
            if part in removed:
                rels.remove(rel)
                changed = True
        if changed:
            items[rels_name] = etree.tostring(rels, xml_declaration=True, encoding="UTF-8", standalone=True)
    ct = etree.fromstring(items["[Content_Types].xml"])
    for ov in list(ct):
        if ov.tag.endswith("Override") and ov.get("PartName").lstrip("/") in removed:
            ct.remove(ov)
    items["[Content_Types].xml"] = etree.tostring(ct, xml_declaration=True, encoding="UTF-8", standalone=True)


NS_EP = "http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"
NS_VT = "http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes"
MASTER_PARTS = re.compile(r"ppt/(presentation|slideMasters/[^/]+|slideLayouts/[^/]+|notesMasters/[^/]+|"
                          r"handoutMasters/[^/]+)\.xml")


def theme_names(items):
    """The name of each slide master's theme, in master order, as PowerPoint lists them under 'Theme'."""
    names = []
    for n in sorted(n for n in items if re.fullmatch(r"ppt/slideMasters/_rels/slideMaster\d+\.xml\.rels", n)):
        for rel in etree.fromstring(items[n]):
            if rel.get("Type", "").endswith("/theme"):
                part = os.path.normpath(os.path.join("ppt/slideMasters", rel.get("Target"))).replace(os.sep, "/")
                if part in items:
                    names.append(etree.fromstring(items[part]).get("name") or THEME_NAME)
    return names or [THEME_NAME]


def app_xml(old, n_slides, n_notes, n_hidden, titles, themes=(THEME_NAME,)):
    """docProps/app.xml with the counts PowerPoint for Mac checks (it offers to repair the file when they are
    wrong). Every other property already in the file is kept as it was."""
    try:
        root = etree.fromstring(old) if old else None
    except etree.XMLSyntaxError:
        root = None
    if root is None or root.tag != f"{{{NS_EP}}}Properties":
        root = etree.Element(f"{{{NS_EP}}}Properties", nsmap={None: NS_EP, "vt": NS_VT})

    def setel(tag, text=None):
        el = root.find(f"{{{NS_EP}}}{tag}")
        if el is None:
            el = etree.SubElement(root, f"{{{NS_EP}}}{tag}")
        for child in list(el):
            el.remove(child)
        el.text = text
        return el

    setel("Slides", str(n_slides))
    setel("Notes", str(n_notes))
    setel("HiddenSlides", str(n_hidden))
    pairs = etree.SubElement(setel("HeadingPairs"), f"{{{NS_VT}}}vector", size="4", baseType="variant")
    for kind, value in (("lpstr", "Theme"), ("i4", str(len(themes))), ("lpstr", "Slide Titles"), ("i4", str(n_slides))):
        etree.SubElement(etree.SubElement(pairs, f"{{{NS_VT}}}variant"), f"{{{NS_VT}}}{kind}").text = value
    vec = etree.SubElement(setel("TitlesOfParts"), f"{{{NS_VT}}}vector", size=str(len(themes) + n_slides),
                           baseType="lpstr")
    for t in list(themes) + titles:
        etree.SubElement(vec, f"{{{NS_VT}}}lpstr").text = t
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)


def post_process(path, template=False):
    """Rewrite the package: app.xml counts, latinLnBrk=0 in the masters and layouts, no thumbnail or printer
    settings (and no relationship left pointing at them), fixed zip entries, and the content type of a .potx
    (template=True) or a .pptx. Works on a deck with slides in either form."""
    path = Path(path)
    with zipfile.ZipFile(path) as z:
        items = {n: z.read(n) for n in z.namelist()}
    main = (b"presentationml.presentation.main+xml", b"presentationml.template.main+xml")
    ct = items["[Content_Types].xml"]
    as_pptx = ct.replace(main[1], main[0])
    items["[Content_Types].xml"] = as_pptx.replace(main[0], main[1]) if template else as_pptx

    slide_parts = [n for n in items if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)]
    n_notes = sum(1 for n in items if re.fullmatch(r"ppt/notesSlides/notesSlide\d+\.xml", n))
    titles, n_hidden = [], 0
    if slide_parts:
        buf = io.BytesIO()                      # python-pptx opens only the .pptx content type; read a copy as one
        with zipfile.ZipFile(buf, "w") as z:
            for n, d in items.items():
                z.writestr(n, as_pptx if n == "[Content_Types].xml" else d)
        for slide in Presentation(buf).slides:
            t = slide.shapes.title.text.split("\n")[0][:60] if slide.shapes.title is not None else ""
            titles.append(re.sub(r"[\x00-\x1f]", " ", t) or "Untitled")
            n_hidden += slide._element.get("show") in ("0", "false")
    items["docProps/app.xml"] = app_xml(items.get("docProps/app.xml"), len(titles), n_notes, n_hidden, titles,
                                        theme_names(items))

    # python-pptx's blank deck brings a thumbnail picture and a binary printer-settings part; neither belongs here.
    removed = [n for n in items if n.startswith(("docProps/thumbnail", "ppt/printerSettings/"))]
    for n in removed:
        del items[n]
    drop_removed(items, removed)
    for n in [n for n in items if MASTER_PARTS.fullmatch(n)]:   # not slides: their text is the author's
        items[n] = items[n].replace(b'latinLnBrk="1"', b'latinLnBrk="0"')
    write_zip(path, items)


def clean_properties(prs, title):
    core = prs.core_properties
    stamp = datetime.datetime(*FIXED_DATE)
    core.title = title
    core.author = AUTHOR
    core.last_modified_by = AUTHOR
    core.subject = ""
    core.keywords = ""
    core.comments = ""
    core.category = ""
    core.created = stamp
    core.modified = stamp
    core.revision = 1


def ph(slide, idx):
    for p in slide.placeholders:
        if p.placeholder_format.idx == idx:
            return p
    raise KeyError(idx)


def put_lines(shape, lines):
    """Text into a placeholder: a string, or a list of "text" / (level, "text")."""
    tf = shape.text_frame
    if isinstance(lines, str):
        tf.text = lines
        return
    tf.clear()                                   # a list replaces what was there, it does not add to it
    for k, item in enumerate(lines):
        lvl, text = item if isinstance(item, tuple) else (0, item)
        p = tf.paragraphs[0] if k == 0 else tf.add_paragraph()
        p.text, p.level = text, lvl


# ---------------------------------------------------------------- sample slides (synthetic text only)
SAMPLES = [
    ("Cover", {0: "Presentation title in one or two lines", 1: "Presenter", 13: "Meeting name · Session",
               14: "Department\nInstitution, City, Country"}),
    ("Section", {13: "01", 0: "Section title", 14: "One line on what this part covers"}),
    ("Content", {20: "Section", 0: "A title that states the point of the slide",
                 1: ["The section name sits above the title, or stays empty", (1, "An empty slot does not show in the slide show"),
                     "Emphasis: bold, or the accent colour, once per slide",
                     "Image-heavy slides: use the black Imaging layouts"]}),
    ("Title Only", {20: "Section", 0: "A title over a figure you place yourself"}),
    ("Blank", {}),
    ("Closing", {0: "The finding, said once more in one line", 13: "Presenter · name@example.org"}),
    ("Disclosure", {0: "Disclosures", 1: "None", 13: "Example Foundation, grant 00-0000"}),
    ("Agenda", {0: "Four parts in ten minutes", 1: ["The question", "What was done", "The finding", "Why it might be wrong"]}),
    ("Key Finding", {0: "The finding, as one sentence (synthetic example)",
                     13: "0.00", 14: "sensitivity per patient (synthetic number)", 15: "95% CI 0.00 to 0.00 · n = 000",
                     16: "Synthetic example, not a real result"}),
    ("Study Design", {0: "Consecutive patients, one reader set, one reference standard",
                      13: "000 adults referred for the example examination", 14: "Month 20XX to month 20XX",
                      15: "Example reference test, read without knowledge of the index test"}),
    ("Result · Figure", {0: "Accuracy held in the external set", 14: "Synthetic example"}),
    ("Result · Table", {0: "What the table shows, as one sentence", 13: "One line: the row or column to read",
                        14: "Synthetic example"}),
    ("Comparison", {0: "The two readings differ in one step", 13: "Standard reading", 14: "Assisted reading",
                    1: ["Reader sees the images alone", "Reports, then checks"],
                    2: ["Reader sees the images and the mark", "Checks, then reports"]}),
    ("Limitations", {0: "Three reasons the finding might be wrong",
                     13: "Single centre", 16: "Case mix may not travel; an external set is the next step",
                     14: "Retrospective reference standard", 17: "Missed cases without follow-up would raise sensitivity",
                     15: "Readers knew a study was running", 18: "Likely more careful than in routine work"}),
    ("Take-home", {0: "What to remember", 1: ["The finding, in the words of the title slide",
                                               "The condition under which it holds", "What it changes on Monday"]}),
    ("References · QR", {0: "References", 1: ["Author A, Author B. Example title one. Journal. Year.",
                                               "Author C, Author D. Example title two. Journal. Year.",
                                               "Author E. Example title three. Journal. Year."],
                         13: "Slides and the full reference list"}),
    ("Table", {20: "Roadmap", 0: "The lecture in one table"}),
    ("Lessons", {20: "Section", 0: "A case that did not go as planned", 1: ["What we saw", "What we should have seen", "What we do now"]}),
    ("Imaging · Content", {20: "Case 1", 0: "Text on black", 1: ["Text typed here comes out white", "Emphasis: bold, or the second accent colour"]}),
    ("Imaging · Title Only", {20: "Case 1", 0: "A title over images you place yourself"}),
    ("Imaging · Blank", {}),
    ("Imaging · Case", {20: "Case 1", 0: "Age/sex · presentation · modality", 1: ["Finding one", "Finding two"]}),
    ("Imaging · 2×2", {20: "Case 1", 0: "Disease: typical findings", 40: "T2WI", 41: "T1WI", 42: "T1CE", 43: "DWI",
                       1: ["Finding one", "Finding two"]}),
    ("Imaging · 1×3", {20: "Case 1", 0: "Disease: key images", 40: "DWI", 41: "ADC", 42: "T1CE", 1: ["One line per image"]}),
    ("Imaging · DSA Pair", {20: "Technique", 0: "Vessel injected · working projection", 40: "Projection · phase",
                            41: "Projection · phase"}),
    ("Imaging · 4 Steps", {20: "Technique", 0: "The procedure in four steps", 40: "1  Access", 41: "2  Confirm",
                           42: "3  Deploy", 43: "4  Result", 1: ["What changes at each step"]}),
    ("Imaging · Quiz", {20: "Quiz", 0: "Quiz 1", 1: ["What is the diagnosis?"], 50: "The answer and the one finding"}),
    ("Imaging · Full", {0: "Structure or finding", 40: "Label one", 41: "Label two"}),
    ("Imaging · Full Center", {0: "Structure or finding", 40: "Label left", 41: "Label right"}),
    ("Imaging · Overlay", {0: "Summary over a dimmed image", 1: ["Line one", "Line two", "Line three"]}),
    ("Imaging · Overlay Table", {0: "Summary table over a dimmed image"}),
]
SAMPLE_TABLE = [["Group", "Reference", "Index", "Difference"], ["Small lesions", "0.00", "0.00", "0.00"],
                ["Large lesions", "0.00", "0.00", "0.00"], ["All", "0.00", "0.00", "0.00"]]


def add_samples(prs):
    lay = {l.name: l for l in prs.slide_layouts}
    for name, content in SAMPLES:
        s = prs.slides.add_slide(lay[name])
        for idx, value in content.items():
            put_lines(ph(s, idx), value)
        if any(p.placeholder_format.idx == 21 for p in s.placeholders):
            tbl = plain_table(ph(s, 21), len(SAMPLE_TABLE), len(SAMPLE_TABLE[0]))
            for r, row in enumerate(SAMPLE_TABLE):
                for c, text in enumerate(row):
                    set_cell(tbl, r, c, text, bold=(r == 0))


_BUILD_LOCK = threading.Lock()   # the palette lives in the module-level C; one build at a time per process


def build(out_dir, palette=DEFAULT_PALETTE, overrides=None, force=False):
    """Write the template and the sample deck into out_dir and return (template path, sample path).

    Raises PaletteError or OutputExists before writing anything; without force an existing output stops the run
    at the start. Both files are built in a temporary folder inside out_dir and each is moved into place when
    complete, the template first, then the sample."""
    out_dir = Path(out_dir)
    template_path, sample_path = out_dir / TEMPLATE_NAME, out_dir / SAMPLE_NAME
    resolve_palette(palette, overrides)
    refuse_existing((template_path, sample_path), force)
    out_dir.mkdir(parents=True, exist_ok=True)
    with _BUILD_LOCK, tempfile.TemporaryDirectory(prefix=".build.", dir=out_dir) as work:
        work_template, work_sample = Path(work) / template_path.name, Path(work) / sample_path.name
        _build_into(work_sample, work_template, palette, overrides)
        publish(work_template, template_path)
        publish(work_sample, sample_path)
    return template_path, sample_path


def _build_into(pptx_path, template_path, palette, overrides):
    set_palette(palette, overrides)
    prs = Presentation()
    prs.slide_width, prs.slide_height = Emu(E(SW)), Emu(E(SH))
    master = prs.slide_master
    base = list(prs.slide_layouts)

    tpart = master.part.part_related_by(RT.THEME)
    tpart._blob = theme_xml(tpart.blob)

    m = master._element
    m.replace(m.find(f"{{{NS_P}}}cSld"), parse_xml(
        f'<p:cSld {NSDECL}>{bg_solid(C["white"])}{sp_tree(master_shapes(Ids()))}</p:cSld>'))
    m.replace(m.find(f"{{{NS_P}}}clrMap"), parse_xml(
        f'<p:clrMap {NSDECL} bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" '
        'accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>'))
    m.replace(m.find(f"{{{NS_P}}}txStyles"), parse_xml(txstyles()))

    for k, (name, fn) in enumerate(LAYOUTS):
        part = base[k].part if k < len(base) else add_layout_part(prs, base[0])
        part._element = parse_xml(fn(Ids()))
    clean_properties(prs, "Slide template")

    prs.save(pptx_path)                       # layouts only for now
    template_path.write_bytes(pptx_path.read_bytes())
    post_process(template_path)

    prs = Presentation(pptx_path)             # reopened: proxies made before the XML swap would show stale names
    names = [l.name for l in prs.slide_layouts]
    assert names == [n for n, _ in LAYOUTS], names
    add_samples(prs)
    prs.save(pptx_path)
    post_process(pptx_path)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("out_dir", nargs="?", default=str(HERE))
    ap.add_argument("--palette", choices=sorted(PALETTES), default=DEFAULT_PALETTE)
    ap.add_argument("--palette-file", help="JSON object of role: hex, applied over --palette "
                                           "(roles: " + ", ".join(ROLES) + ")")
    for role in ROLES:
        ap.add_argument("--" + role.replace("_", "-"), dest=role, metavar="HEX", help=f"colour for the {role} role")
    ap.add_argument("--force", action="store_true", help=f"replace {TEMPLATE_NAME} / {SAMPLE_NAME} if they exist")
    ap.add_argument("--print-table", action="store_true", help="print the README placeholder table and stop")
    a = ap.parse_args()
    if a.print_table:
        print("\n".join(readme_rows(layout_table(Path(a.out_dir) / TEMPLATE_NAME))))
        return
    try:
        overrides = load_palette_file(a.palette_file) if a.palette_file else {}
        overrides.update({r: getattr(a, r) for r in ROLES if getattr(a, r) is not None})
        template, sample = build(a.out_dir, a.palette, overrides, a.force)
    except PaletteError as e:
        raise SystemExit(f"palette rejected: {e}")
    except OutputExists as e:
        raise SystemExit(str(e))
    custom = f" + {len(overrides)} custom colour(s)" if overrides else ""
    print("built", template.name, "+", sample.name, f"(palette {a.palette}{custom}, {len(LAYOUTS)} layouts)")


if __name__ == "__main__":
    main()
