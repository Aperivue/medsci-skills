#!/usr/bin/env python3
"""The slide template builds the same thing twice, matches its README, and carries nobody's name.

Claims, each with the case that would refute it:

  1. Two builds from clean folders give the same layout names and the same (idx, type, name) list
     for every layout, and that list is the table printed in the template README. A script fills a
     deck by layout name and idx, so a README that has drifted from the build sends text to the
     wrong slot without an error.
  2. The built files hold no picture, no external relationship, and no relationship or content
     type pointing at a part that is not in the package. Their zip entries carry fixed dates,
     system, mode and order.
  3. No part of the built files, and no file shipped beside them, names a person, an institution
     or a home directory.
  4. The default palette is mono; there is no navy palette; no built-in palette carries a navy or a
     red; a custom colour is accepted, and a malformed value or any colour pair the template draws
     below its WCAG level stops the build before anything is written.
  5. The handout .docx builds the same twice, embeds no picture and names nobody.
  6. The scripts never replace an existing output without --force, and a failed run leaves no file
     at the output path.
  7. The starter decks carry their slides, notes, tables and click effects; fit_picture keeps a
     picture whole inside its slot; post_process keeps what it does not need to change.

Claim 3 would also pass if the scanner looked at nothing. So the scanner is first run on copies of
the built deck with a canary planted in each form a name can take inside OOXML (a comment, a
character reference, a name split across two runs, camel case, a Windows path), and has to find
every one.

Institution names are not listed here, not even as digests: a short name's digest can be reversed by
trying candidates. To scan for them, put their SHA-256 digests (lowercase term, one per line) in a
file outside the repository and point MEDSCI_TEMPLATE_BLOCKLIST at it.
"""
from __future__ import annotations

import hashlib
import html
import os
import re
import sys
import tempfile
import threading
import unicodedata
import unittest
import zipfile
from pathlib import Path

from lxml import etree

SKILL = Path(__file__).resolve().parents[1]
TEMPLATE_DIR = SKILL / "templates" / "slide_template"
sys.path.insert(0, str(TEMPLATE_DIR))

import build_handout_template as h  # noqa: E402
import build_slide_template as t  # noqa: E402
import new_deck  # noqa: E402

CANARY = "zzcanaryhospital"
BLOCKED_DIGESTS = {hashlib.sha256(CANARY.encode()).hexdigest()}
_private = os.environ.get("MEDSCI_TEMPLATE_BLOCKLIST")
if _private:                      # named but unusable is an error, never a quietly narrower scan
    _found = {ln.strip() for ln in Path(_private).read_text().splitlines() if re.fullmatch(r"[0-9a-f]{64}", ln.strip())}
    if not _found:
        raise SystemExit(f"MEDSCI_TEMPLATE_BLOCKLIST={_private} holds no SHA-256 digest")
    BLOCKED_DIGESTS |= _found
MAX_NGRAM = 4                     # a name of up to four words is hashed whole, words joined by one space
# Not identifying by themselves, so kept readable: home-directory paths and a colour-matching trademark.
BLOCKED_LITERALS = ("/users/", "/home/", "pantone")
LATIN = re.compile(r"[A-Za-z]+")
HANGUL = re.compile("[\uac00-\ud7a3]+")
EXPECTED_LAYOUTS = 31
RESEARCH_LAYOUTS = ("Disclosure", "Agenda", "Key Finding", "Study Design", "Result · Figure", "Result · Table",
                    "Comparison", "Limitations", "Take-home", "References · QR")
NEUTRAL_AUTHORS = {"", "medsci-skills"}        # written out, not read from the builder
NS = {"p": "http://schemas.openxmlformats.org/presentationml/2006/main",
      "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
      "r": "http://schemas.openxmlformats.org/package/2006/relationships",
      "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


def text_forms(text: str) -> list[str]:
    """The text as written, with character references decoded, with tags removed (so a word split across runs
    is whole again), with camel case split, and with backslashes read as path separators."""
    decoded = html.unescape(text)
    joined = re.sub(r"<[^>]+>", "", decoded)
    forms = [text, decoded, joined]
    forms += [re.sub(r"([a-z])([A-Z])", r"\1 \2", f) for f in forms]
    return [f.replace("\\", "/") for f in forms]


def scan_text(text: str) -> list[str]:
    """Blocked things found in one piece of text, as short descriptions (never the match itself for a digest)."""
    hits = set()
    for form in text_forms(text):
        low = form.lower()
        for lit in BLOCKED_LITERALS:
            if lit in low:
                hits.add(f"literal {lit!r}")
        words = [m.group(0).lower() for m in LATIN.finditer(unicodedata.normalize("NFKC", form))]
        grams = {" ".join(words[i:i + n]) for n in range(1, MAX_NGRAM + 1) for i in range(len(words) - n + 1)}
        for run in HANGUL.findall(form):
            grams.update(run[i:i + 2] for i in range(len(run) - 1))
            grams.add(run)
        if any(hashlib.sha256(g.encode("utf-8")).hexdigest() in BLOCKED_DIGESTS for g in grams):
            hits.add("blocked token (digest match)")
    return sorted(hits)


def scan_package(path: Path) -> dict[str, list[str]]:
    """Every part of an OOXML package, by part name. A part that is not text is itself a finding."""
    out: dict[str, list[str]] = {}
    with zipfile.ZipFile(path) as z:
        for name in z.namelist():
            hits = scan_text(name)
            try:
                hits += scan_text(z.read(name).decode("utf-8"))
            except UnicodeDecodeError:
                hits.append("binary part")
            if hits:
                out[name] = hits
    return out


def plant(src: Path, dst: Path, part: str, insert: bytes, at: bytes = b"</") -> None:
    with zipfile.ZipFile(src) as zin, zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout:
        for name in zin.namelist():
            data = zin.read(name)
            if name == part:
                data = data.replace(at, insert + at, 1)
            zout.writestr(name, data)


def drawn_shapes(layout_xml: str) -> list[str]:
    """Names of shapes on a layout or master that are not placeholders and draw something: a fill, an outline
    or a picture. A text label with no fill and no line draws nothing but its words, so it is not counted."""
    root = etree.fromstring(layout_xml.encode("utf-8"))
    out = []
    for sp in root.iter(f"{{{NS['p']}}}sp", f"{{{NS['p']}}}cxnSp", f"{{{NS['p']}}}pic"):
        if sp.find(".//p:nvPr/p:ph", NS) is not None:
            continue
        name = sp.find(".//p:cNvPr", NS).get("name")
        sppr = sp.find("p:spPr", NS)
        filled = sppr is None or sppr.find("a:noFill", NS) is None
        ln = sppr.find("a:ln", NS) if sppr is not None else None
        outlined = ln is not None and ln.find("a:noFill", NS) is None
        if sp.tag.endswith("}sp") and not filled and not outlined:
            continue
        out.append(name)
    return out


def package_problems(path: Path) -> list[str]:
    """External relationships, relationships whose target is not in the package, and content-type overrides
    for parts that are not in it. Read by parsing the XML, so quoting style does not matter."""
    problems = []
    with zipfile.ZipFile(path) as z:
        names = set(z.namelist())
        for rels_name in [n for n in names if n.endswith(".rels")]:
            base = rels_name.replace("_rels/", "").rsplit(".rels", 1)[0]
            folder = base.rsplit("/", 1)[0] if "/" in base else ""
            for rel in etree.fromstring(z.read(rels_name)).iter(f"{{{NS['r']}}}Relationship"):
                if rel.get("TargetMode") == "External":
                    problems.append(f"{rels_name}: external {rel.get('Target')}")
                    continue
                target = rel.get("Target")
                part = target.lstrip("/") if target.startswith("/") else os.path.normpath(
                    os.path.join(folder, target)).replace(os.sep, "/")
                if part not in names:
                    problems.append(f"{rels_name}: dangling {target}")
        for ov in etree.fromstring(z.read("[Content_Types].xml")):
            if ov.tag.endswith("Override") and ov.get("PartName").lstrip("/") not in names:
                problems.append(f"content type for missing {ov.get('PartName')}")
    return problems


def zip_header_problems(path: Path) -> list[str]:
    problems = []
    with zipfile.ZipFile(path) as z:
        infos = z.infolist()
        names = [i.filename for i in infos]
        if names != ["[Content_Types].xml"] + sorted(n for n in names if n != "[Content_Types].xml"):
            problems.append("entry order")
        for i in infos:
            if i.date_time != t.FIXED_DATE or i.create_system != 3 or i.external_attr != 0o644 << 16:
                problems.append(f"{i.filename}: {i.date_time} system {i.create_system} attr {oct(i.external_attr)}")
    return problems


def parts(path: Path) -> dict[str, bytes]:
    with zipfile.ZipFile(path) as z:
        return {n: z.read(n) for n in z.namelist()}


def readme_table() -> list[str]:
    text = (TEMPLATE_DIR / "README.md").read_text(encoding="utf-8")
    block = text.split("<!-- placeholder-table:start -->")[1].split("<!-- placeholder-table:end -->")[0]
    return [ln for ln in block.strip().splitlines()[2:] if ln.startswith("|")]


def tiny_png(path: Path, w: int, h: int) -> Path:
    from PIL import Image
    Image.new("RGB", (w, h), (128, 128, 128)).save(path)
    return path


class SlideTemplate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        root = Path(cls.temp.name)
        cls.builds = []
        for k in (1, 2):
            template, sample = t.build(root / f"build{k}")
            cls.builds.append((template, sample))
        cls.handouts = [h.build(root / f"handout{k}") for k in (1, 2)]
        cls.starters = {kind: new_deck.make_deck(root / f"{kind}.pptx", kind, cls.builds[0][0])
                        for kind in new_deck.STARTERS}
        cls.root = root

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def all_built(self):
        return [*self.builds[0], TEMPLATE_DIR / t.TEMPLATE_NAME, *self.starters.values(),
                self.handouts[0], TEMPLATE_DIR / f"{h.STEM}.docx"]

    # ---------------------------------------------------------------- claim 1
    def test_two_builds_agree_and_match_the_readme(self):
        tables = [t.layout_table(p) for build in self.builds for p in build]
        self.assertEqual(len(tables[0]), EXPECTED_LAYOUTS)
        self.assertEqual([name for name, _ in tables[0]], [name for name, _ in t.LAYOUTS])
        for other in tables[1:]:
            self.assertEqual(tables[0], other)
        self.assertEqual(t.readme_rows(tables[0]), readme_table())

    def test_shipped_template_is_the_default_build_with_no_slides(self):
        shipped = TEMPLATE_DIR / t.TEMPLATE_NAME
        self.assertTrue(shipped.exists(), "run build_slide_template.py --force")
        self.assertEqual(parts(shipped), parts(self.builds[0][0]),
                         "the shipped template is not what the builder writes now; rebuild it")
        with zipfile.ZipFile(shipped) as z:
            self.assertNotIn(b"<p:sldId ", z.read("ppt/presentation.xml"))
            self.assertIn(b"presentationml.presentation.main+xml", z.read("[Content_Types].xml"))
        self.assertEqual(sorted(p.suffix for p in TEMPLATE_DIR.iterdir() if p.suffix in {".pptx", ".potx", ".docx"}),
                         [".docx", ".pptx"], "ship one .pptx template and the handout, nothing else")

    def test_sample_deck_has_one_slide_per_layout(self):
        from pptx import Presentation
        prs = Presentation(self.builds[0][1])
        self.assertEqual([s.slide_layout.name for s in prs.slides], [name for name, _ in t.LAYOUTS])

    def test_section_name_ends_above_the_title(self):
        for path in (self.builds[0][0],):
            with zipfile.ZipFile(path) as z:
                for part in [n for n in z.namelist() if re.fullmatch(r"ppt/slideLayouts/slideLayout\d+\.xml", n)]:
                    root = etree.fromstring(z.read(part))
                    boxes = {}
                    for sp in root.iter(f"{{{NS['p']}}}sp"):
                        ph = sp.find(".//p:nvPr/p:ph", NS)
                        off, ext = sp.find(".//a:xfrm/a:off", NS), sp.find(".//a:xfrm/a:ext", NS)
                        if ph is not None and off is not None:
                            boxes[ph.get("idx", ph.get("type"))] = (int(off.get("y")), int(ext.get("cy")))
                    if "20" in boxes:
                        title_top = boxes.get("title", (t.E(t.TITLE_Y), 0))[0]
                        self.assertLessEqual(sum(boxes["20"]), title_top, part)

    # ---------------------------------------------------------------- claim 2
    def test_two_builds_have_the_same_parts_and_fixed_zip_headers(self):
        for a, b in zip(*self.builds):
            self.assertEqual(parts(a), parts(b), a.name)
        for path in self.all_built():
            self.assertEqual(zip_header_problems(path), [], path.name)

    def test_no_media_and_every_relationship_resolves(self):
        for path in self.all_built():
            with zipfile.ZipFile(path) as z:
                names = z.namelist()
            self.assertFalse([n for n in names if "/media/" in n or "thumbnail" in n], path.name)
            self.assertFalse([n for n in names if not n.endswith((".xml", ".rels"))], path.name)
            self.assertEqual(package_problems(path), [], path.name)

    def test_package_check_finds_a_dangling_and_an_external_relationship(self):
        bad = self.root / "dangling.docx"
        plant(self.handouts[0], bad, "_rels/.rels",
              b"<Relationship Id='rId9' Type='x' Target='docProps/thumbnail.jpeg'/>"
              b"<Relationship Id='rId8' Type='x' Target='http://example.org' TargetMode='External'/>",
              at=b"</Relationships>")
        found = package_problems(bad)
        self.assertTrue(any("dangling" in p for p in found), found)
        self.assertTrue(any("external" in p for p in found), found)

    # ---------------------------------------------------------------- claim 3
    def test_scanner_finds_every_planted_form(self):
        layout = "ppt/slideLayouts/slideLayout3.xml"
        forms = {
            "comment": (layout, f"<!-- {CANARY} -->".encode(), b"</"),
            "core properties": ("docProps/core.xml", f"<!-- {CANARY} -->".encode(), b"</"),
            "character reference": (layout, b"<!-- zzcanary&#104;ospital -->", b"</"),
            "split across runs": (layout, b"zzcanary</a:t></a:r><a:r><a:t>hospital", b"</a:t>"),
            "camel case": (layout, b"<!-- prefixZzcanaryhospitalSuffix -->", b"</"),
            "windows path": (layout, b"<!-- C:\\Users\\someone\\deck -->", b"</"),
        }
        for label, (part, insert, at) in forms.items():
            planted = self.root / f"planted_{label.replace(' ', '_')}.pptx"
            plant(self.builds[0][1], planted, part, insert, at)
            self.assertIn(part, scan_package(planted), label)
        self.assertTrue(scan_text("x/Users/someone/y"))
        self.assertTrue(scan_text(f"prefix_{CANARY}_Template.potx"))
        global BLOCKED_DIGESTS
        saved = set(BLOCKED_DIGESTS)
        BLOCKED_DIGESTS.add(hashlib.sha256(b"zzcanary general hospital").hexdigest())
        try:
            self.assertTrue(scan_text("<a:t>Zzcanary General</a:t><a:t> Hospital</a:t>"), "multi-word name")
        finally:
            BLOCKED_DIGESTS.clear()
            BLOCKED_DIGESTS.update(saved)

    def test_no_person_institution_or_path_in_built_files(self):
        for path in self.all_built():
            self.assertEqual(scan_package(path), {}, path.name)

    def test_no_person_institution_or_path_in_shipped_sources(self):
        for path in sorted([*TEMPLATE_DIR.iterdir(), SKILL / "references" / "slide_template_layouts.md",
                            Path(__file__)]):
            if path.suffix in {".py", ".md"} and path != Path(__file__):
                self.assertEqual(scan_text(path.name + "\n" + path.read_text(encoding="utf-8")), [], path.name)

    def test_document_properties_name_nobody(self):
        """Author and last-modified-by are neutral in every built file. Read from docProps/core.xml directly,
        because python-pptx refuses to open a .potx."""
        for path in self.all_built():
            with zipfile.ZipFile(path) as z:
                core = z.read("docProps/core.xml").decode("utf-8")
            for tag in ("dc:creator", "cp:lastModifiedBy"):
                m = re.search(f"<{tag}>([^<]*)</{tag}>|<{tag}/>", core)
                self.assertIsNotNone(m, f"{path.name}: no {tag}")
                self.assertIn(m.group(1) or "", NEUTRAL_AUTHORS, f"{path.name}: {tag}")

    # ---------------------------------------------------------------- research layouts
    def test_research_layouts_have_no_band_rule_or_box(self):
        """No drawn shape on the research-talk layouts or on the master they inherit from."""
        names = dict(t.layout_table(self.builds[0][0]))
        self.assertTrue(set(RESEARCH_LAYOUTS) <= set(names))
        with zipfile.ZipFile(self.builds[0][0]) as z:
            for part in [n for n in z.namelist() if re.fullmatch(r"ppt/slideLayouts/slideLayout\d+\.xml", n)]:
                xml = z.read(part).decode("utf-8")
                name = re.search(r'<p:cSld name="([^"]+)"', xml).group(1)
                self.assertNotIn("<p:cxnSp", xml, name)
                self.assertNotIn('<a:ln w=', xml, name)
                if name in RESEARCH_LAYOUTS:
                    self.assertEqual(drawn_shapes(xml), [], f"{name} draws a filled or outlined shape")
                    self.assertNotIn(20, [i for i, _, _ in names[name]], f"{name} has a section-name slot")
            self.assertEqual(drawn_shapes(z.read("ppt/slideMasters/slideMaster1.xml").decode("utf-8")), [])

    # ---------------------------------------------------------------- claim 4
    def test_palettes_default_mono_no_navy_or_red(self):
        self.assertEqual(t.DEFAULT_PALETTE, "mono")
        self.assertNotIn("navy", t.PALETTES)
        for name, pal in t.PALETTES.items():
            self.assertEqual(set(pal), set(t.ROLES), name)
            self.assertEqual(t.contrast_failures(pal), [], name)
            for role, value in pal.items():
                r, g, b = (int(value[i:i + 2], 16) for i in (0, 2, 4))
                self.assertFalse(r > 120 and r > 1.8 * g and r > 1.8 * b, f"{name}.{role} {value} reads as red")
                self.assertFalse(b > 1.6 * r and b > 1.3 * g and max(r, g, b) < 110,
                                 f"{name}.{role} {value} reads as navy")
        self.assertEqual(len({p["accent"] for p in t.PALETTES.values()}), len(t.PALETTES))
        potx, _ = t.build(self.root / "pine", "pine")
        self.assertNotEqual(parts(potx), parts(self.builds[0][0]))

    def test_custom_palette_accepted_and_bad_ones_rejected(self):
        pal = t.resolve_palette("mono", {"accent": "#1d6a4f", "ink": "222222"})
        self.assertEqual((pal["accent"], pal["ink"]), ("1D6A4F", "222222"))
        js = self.root / "colours.json"
        js.write_text('{"accent": "7A4E00", "section": "2B2925"}', encoding="utf-8")
        self.assertEqual(t.resolve_palette("mono", t.load_palette_file(js))["section"], "2B2925")
        potx, _ = t.build(self.root / "custom", "mono", {"accent": "1D6A4F"})
        with zipfile.ZipFile(potx) as z:
            self.assertIn(b'<a:accent1><a:srgbClr val="1D6A4F"/>', z.read("ppt/theme/theme1.xml"))
        for bad in ({"accent": "12345"}, {"accent": "GG0000"}, {"ink": "navy"}, {"bogus": "000000"},
                    {"accent": ""}, {"accent": None}, {"ink": 111111}):
            with self.assertRaises(t.PaletteError, msg=str(bad)):
                t.resolve_palette("mono", bad)
        cases = {"accent on white": {"accent": "FF8800"}, "white on section": {"section": "DDDDDD"},
                 "page and section number on section": {"section": "767676"},
                 "bullets (muted) on black": {"muted": "000000"},
                 "lower text levels on white": {"ink": "4C4C4C"}}   # 8.6:1 itself, 4.4:1 lightened
        for pair, override in cases.items():
            with self.assertRaisesRegex(t.PaletteError, re.escape(pair), msg=str(override)):
                t.resolve_palette("mono", override)
        undecodable = self.root / "latin1.json"
        undecodable.write_bytes('{"accent": "1D6A4F", "x": "\u00e9"}'.encode("latin-1"))
        with self.assertRaises(t.PaletteError):
            t.load_palette_file(undecodable)
        with self.assertRaises(t.PaletteError):
            t.build(self.root / "never", "mono", {"muted": "BBBBBB"})
        self.assertFalse((self.root / "never").exists(), "a rejected palette must stop before writing")

    def test_concurrent_builds_do_not_mix_palettes(self):
        solo = {p: parts(t.build(self.root / f"solo_{p}", p)[0]) for p in ("mono", "pine")}
        out, errors = {}, []

        def run(p):
            try:
                out[p] = parts(t.build(self.root / f"thread_{p}", p)[0])
            except Exception as e:      # noqa: BLE001 - reported below
                errors.append(e)
        threads = [threading.Thread(target=run, args=(p,)) for p in ("mono", "pine")]
        for th in threads:
            th.start()
        for th in threads:
            th.join()
        self.assertEqual(errors, [])
        self.assertEqual(out, solo)

    # ---------------------------------------------------------------- claim 5
    def test_handout_is_reproducible_plain_and_shipped(self):
        a, b = self.handouts
        self.assertEqual(a.read_bytes(), b.read_bytes())
        shipped = TEMPLATE_DIR / f"{h.STEM}.docx"
        self.assertTrue(shipped.exists(), "run build_handout_template.py --force")
        self.assertEqual(parts(shipped), parts(a), "the shipped handout is not what the builder writes now")
        with zipfile.ZipFile(a) as z:
            doc = z.read("word/document.xml")
            self.assertNotIn(b"<w:tbl>", doc)
            self.assertIn(b"Malgun Gothic", z.read("word/theme/theme1.xml"))
        for ppr in etree.fromstring(doc).iter(f"{{{NS['w']}}}pPr"):      # schema order: tabs before spacing
            kids = [etree.QName(c).localname for c in ppr]
            if "tabs" in kids and "spacing" in kids:
                self.assertLess(kids.index("tabs"), kids.index("spacing"))
        self.assertEqual(scan_package(a), {})

    # ---------------------------------------------------------------- claim 6
    def test_outputs_are_never_replaced_without_force(self):
        out = self.root / "noclobber"
        t.build(out)
        before = (out / t.TEMPLATE_NAME).read_bytes()
        with self.assertRaises(t.OutputExists):
            t.build(out, "pine")
        self.assertEqual((out / t.TEMPLATE_NAME).read_bytes(), before)
        t.build(out, "pine", force=True)
        self.assertNotEqual((out / t.TEMPLATE_NAME).read_bytes(), before)
        with self.assertRaises(t.OutputExists):
            h.build(self.root / "handout1")
        deck = self.root / "talk.pptx"
        deck.write_bytes(b"keep me")
        with self.assertRaises(t.OutputExists):
            new_deck.make_deck(deck)
        self.assertEqual(deck.read_bytes(), b"keep me")
        new_deck.make_deck(deck, force=True, template=self.builds[0][0])
        self.assertNotEqual(deck.read_bytes(), b"keep me")
        leftovers = [p.name for p in self.root.rglob("*") if p.name.endswith(".part") or p.name.startswith(".build.")
                     or p.name.startswith(".new_deck.")]
        self.assertEqual(leftovers, [])

    def test_a_failed_run_leaves_nothing_at_the_output(self):
        folder = self.root / "failing"
        folder.mkdir()
        with self.assertRaises(KeyError):              # fails after the template is copied, inside the starter
            new_deck.make_deck(folder / "talk.pptx", "no-such-starter", self.builds[0][0])
        self.assertEqual(list(folder.iterdir()), [])

    # ---------------------------------------------------------------- claim 7
    def test_starters_carry_their_slides_notes_tables_and_clicks(self):
        from pptx import Presentation
        for kind, spec in new_deck.STARTERS.items():
            prs = Presentation(self.starters[kind])
            slides = list(prs.slides)
            self.assertGreater(len(spec), 5, kind)
            self.assertEqual([s.slide_layout.name for s in slides], [name for name, _, _ in spec], kind)
            for k, (s, (name, content, opt)) in enumerate(zip(slides, spec)):
                where = f"{kind} slide {k + 1} ({name})"
                slots = {p.placeholder_format.idx: p for p in s.placeholders}
                for idx, value in content.items():
                    first = value if isinstance(value, str) else (value[0] if isinstance(value[0], str) else value[0][1])
                    self.assertIn(first.split("\n")[0], slots[idx].text_frame.text, where)
                if opt.get("notes"):
                    self.assertEqual(s.notes_slide.notes_text_frame.text, opt["notes"], where)
                if "table" in opt:
                    tables = [g for g in s.shapes if g.has_table]
                    self.assertEqual(len(tables), 1, where)
                    self.assertEqual((len(tables[0].table.rows), len(tables[0].table.columns)), opt["table"][:2], where)
                targets = [el.get("spid") for el in s._element.iter(f"{{{NS['p']}}}spTgt")]
                expected = [str(slots[i].shape_id) for i in opt.get("appear", [])]
                self.assertEqual(targets, expected, where)

    def test_fit_picture_keeps_the_whole_picture_inside_the_slot(self):
        from pptx import Presentation
        deck = new_deck.make_deck(self.root / "fit.pptx", template=self.builds[0][0])
        prs = Presentation(deck)
        lay = {l.name: l for l in prs.slide_layouts}
        for w, hgt in ((1600, 400), (400, 1600)):
            s = prs.slides.add_slide(lay["Result · Figure"])
            slot = {p.placeholder_format.idx: p for p in s.placeholders}[30]
            box = (slot.left, slot.top, slot.width, slot.height)
            pic = new_deck.fit_picture(slot, tiny_png(self.root / f"img_{w}x{hgt}.png", w, hgt))
            self.assertEqual((pic.crop_left, pic.crop_right, pic.crop_top, pic.crop_bottom), (0, 0, 0, 0))
            self.assertGreaterEqual(pic.left, box[0])
            self.assertGreaterEqual(pic.top, box[1])
            self.assertLessEqual(pic.left + pic.width, box[0] + box[2] + 1)
            self.assertLessEqual(pic.top + pic.height, box[1] + box[3] + 1)
            self.assertAlmostEqual(pic.width / pic.height, w / hgt, places=2)
            self.assertTrue(pic.width >= box[2] - 2 or pic.height >= box[3] - 2, "not scaled to the slot")

    def test_appear_on_click_refuses_a_second_call_and_keeps_schema_order(self):
        from pptx import Presentation
        from pptx.oxml import parse_xml
        prs = Presentation(self.starters["lecture"])
        quiz = next(s for s in prs.slides if s.slide_layout.name == "Imaging · Quiz")
        with self.assertRaises(ValueError):
            new_deck.appear_on_click(quiz, [quiz.shapes[0]])
        plain = next(s for s in prs.slides if s.slide_layout.name == "Content")
        plain._element.append(parse_xml(f'<p:extLst xmlns:p="{NS["p"]}"/>'))
        new_deck.appear_on_click(plain, [plain.shapes[0]])
        kids = [etree.QName(c).localname for c in plain._element]
        self.assertLess(kids.index("timing"), kids.index("extLst"))

    def test_blank_refuses_a_template_with_slides(self):
        with self.assertRaises(ValueError):
            new_deck.blank(self.builds[0][1], self.root / "from_deck.pptx")

    def test_post_process_on_a_template_with_slides_keeps_counts_and_slide_text(self):
        from pptx import Presentation
        src = self.root / "hidden.pptx"
        new_deck.make_deck(src, "conference-oral", self.builds[0][0])
        prs = Presentation(src)
        prs.slides[1]._element.set("show", "0")
        body = next(p for p in prs.slides[2].placeholders if p.placeholder_format.idx == 1)
        body.text_frame.text = 'example: latinLnBrk="1"'
        prs.save(src)
        potx = self.root / "with_slides.potx"
        potx.write_bytes(src.read_bytes())
        t.post_process(potx, template=True)
        t.post_process(potx, template=False)          # a .potx that has slides, back to a deck
        with zipfile.ZipFile(potx) as z:
            app = z.read("docProps/app.xml").decode("utf-8")
            slide3 = z.read("ppt/slides/slide3.xml").decode("utf-8")
        self.assertIn(f"<Slides>{len(new_deck.CONFERENCE_ORAL)}</Slides>", app)
        self.assertIn("<HiddenSlides>1</HiddenSlides>", app)
        self.assertIn('latinLnBrk="1"', html.unescape(slide3))

    def test_put_lines_replaces_what_was_there(self):
        from pptx import Presentation
        prs = Presentation(self.builds[0][1])
        content = next(s for s in prs.slides if s.slide_layout.name == "Content")
        slot = next(p for p in content.placeholders if p.placeholder_format.idx == 1)
        t.put_lines(slot, ["one", "two", "three"])
        t.put_lines(slot, ["only"])
        self.assertEqual([p.text for p in slot.text_frame.paragraphs], ["only"])

    # ---------------------------------------------------------------- round-2 fixes
    def test_new_deck_output_must_be_a_pptx_and_not_the_template(self):
        tpl = self.root / "own.potx"
        tpl.write_bytes(self.builds[0][0].read_bytes())
        with self.assertRaises(ValueError):
            new_deck.make_deck(tpl, template=tpl, force=True)           # the template itself, even with force
        self.assertEqual(tpl.read_bytes(), self.builds[0][0].read_bytes())
        with self.assertRaises(ValueError):
            new_deck.make_deck(self.root / "talk.ppt", template=tpl)
        link = self.root / "link.pptx"
        link.symlink_to(tpl)
        with self.assertRaises(ValueError):
            new_deck.make_deck(link, template=tpl, force=True)
        self.assertEqual(tpl.read_bytes(), self.builds[0][0].read_bytes())

    def test_blank_refuses_a_file_that_is_not_a_powerpoint_template(self):
        with self.assertRaises(ValueError):
            new_deck.blank(self.handouts[0], self.root / "from_docx.pptx")
        self.assertFalse((self.root / "from_docx.pptx").exists())

    def test_post_process_removes_only_what_it_deleted(self):
        bad = self.root / "unrelated_dangling.pptx"
        plant(self.builds[0][1], bad, "ppt/_rels/presentation.xml.rels",
              b"<Relationship Id='rId99' Type='x' Target='slides/missing.xml'/>", at=b"</Relationships>")
        t.post_process(bad)
        self.assertTrue(any("missing.xml" in p for p in package_problems(bad)), "an unrelated break must stay visible")

    def test_app_xml_names_the_real_theme(self):
        with zipfile.ZipFile(self.builds[0][1]) as z:
            app = z.read("docProps/app.xml").decode("utf-8")
            theme = etree.fromstring(z.read("ppt/theme/theme1.xml")).get("name")
        self.assertIn(f"<vt:lpstr>{theme}</vt:lpstr>", app)

    def test_links_on_black_use_the_dark_ground_accent(self):
        with zipfile.ZipFile(self.builds[0][0]) as z:
            for part in [n for n in z.namelist() if re.fullmatch(r"ppt/slideLayouts/slideLayout\d+\.xml", n)]:
                xml = z.read(part).decode("utf-8")
                if 'bg1="dk1"' in xml:
                    self.assertIn('hlink="accent2"', xml, part)
                    self.assertIn('folHlink="accent6"', xml, part)

    def test_table_text_carries_the_slide_text_colour(self):
        with zipfile.ZipFile(self.builds[0][1]) as z:
            for n in [n for n in z.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)]:
                root = etree.fromstring(z.read(n))
                for tc in root.iter(f"{{{NS['a']}}}tc"):
                    for rpr in tc.iter(f"{{{NS['a']}}}rPr", f"{{{NS['a']}}}endParaRPr"):
                        clr = rpr.find("a:solidFill/a:schemeClr", NS)
                        self.assertIsNotNone(clr, n)
                        self.assertEqual(clr.get("val"), "tx1", n)

    def test_outputs_get_a_readable_mode_and_keep_an_existing_one(self):
        umask = os.umask(0)
        os.umask(umask)
        for path in (*self.builds[0], self.handouts[0], self.starters["lecture"]):
            self.assertEqual(path.stat().st_mode & 0o777, 0o666 & ~umask, path.name)
        out = self.root / "modes"
        potx, _ = t.build(out)
        os.chmod(potx, 0o640)
        t.build(out, force=True)
        self.assertEqual(potx.stat().st_mode & 0o777, 0o640)
        deck = self.root / "shared_deck.pptx"                 # post_process run on someone's existing deck
        deck.write_bytes(self.builds[0][1].read_bytes())
        os.chmod(deck, 0o664)
        t.post_process(deck)
        self.assertEqual(deck.stat().st_mode & 0o777, 0o664)

    def test_appear_on_click_takes_a_generator_and_refuses_other_slides_shapes(self):
        from pptx import Presentation
        prs = Presentation(self.builds[0][1])
        content = next(s for s in prs.slides if s.slide_layout.name == "Content")
        other = next(s for s in prs.slides if s.slide_layout.name == "Agenda")
        with self.assertRaises(ValueError):
            new_deck.appear_on_click(content, [other.shapes[0]])
        shapes = [sh for sh in content.shapes][:2]
        new_deck.appear_on_click(content, (sh for sh in shapes))
        bld = [el.get("spid") for el in content._element.iter(f"{{{NS['p']}}}bldP")]
        self.assertEqual(bld, [str(sh.shape_id) for sh in shapes])

    def test_research_titles_are_custom_prompts(self):
        with zipfile.ZipFile(self.builds[0][0]) as z:
            for part in [n for n in z.namelist() if re.fullmatch(r"ppt/slideLayouts/slideLayout\d+\.xml", n)]:
                xml = z.read(part).decode("utf-8")
                if re.search(r'<p:cSld name="(Disclosure|Key Finding|Limitations)"', xml):
                    self.assertIn('<p:ph type="title" hasCustomPrompt="1"/>', xml, part)

    def test_decomposed_hangul_gets_the_korean_language_tag(self):
        from pptx import Presentation
        prs = Presentation(self.builds[0][1])
        slot = next(p for p in prs.slides[2].placeholders if p.placeholder_format.idx == 1)
        for form in ("NFC", "NFD"):
            slot.text_frame.text = unicodedata.normalize(form, "\ud55c\uad6d\uc5b4")
            new_deck.set_lang(slot.text_frame)
            self.assertEqual(slot.text_frame.paragraphs[0].runs[0]._r.rPr.get("lang"), "ko-KR", form)

    def test_starter_set_and_quiz_clicks_are_fixed_independently(self):
        from pptx import Presentation
        self.assertEqual(sorted(new_deck.STARTERS),
                         ["case-conference", "conference-oral", "journal-club", "lecture", "procedure"])
        for kind in ("lecture", "case-conference"):
            for s in Presentation(self.starters[kind]).slides:
                if s.slide_layout.name == "Imaging · Quiz":
                    answer = next(p for p in s.placeholders if p.placeholder_format.idx == 50)
                    targets = [el.get("spid") for el in s._element.iter(f"{{{NS['p']}}}spTgt")]
                    self.assertEqual(targets, [str(answer.shape_id)], kind)
                    self.assertIn("clickEffect", etree.tostring(s._element).decode())
    def test_a_potx_is_written_when_the_output_name_asks_for_one(self):
        potx = new_deck.make_deck(self.root / "own_template.potx", template=self.builds[0][0])
        with zipfile.ZipFile(potx) as z:
            self.assertIn(b"presentationml.template.main+xml", z.read("[Content_Types].xml"))
            self.assertNotIn(b"<p:sldId ", z.read("ppt/presentation.xml"))
        deck = new_deck.make_deck(self.root / "from_potx.pptx", "conference-oral", potx)
        with zipfile.ZipFile(deck) as z:
            self.assertIn(b"presentationml.presentation.main+xml", z.read("[Content_Types].xml"))

if __name__ == "__main__":
    unittest.main(verbosity=2)
