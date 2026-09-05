#!/usr/bin/env python3
"""Synthetic TTF, CFF/OTF and TTC regressions; no system fonts or network needed."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.ttLib import TTCollection, TTFont

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/scan_glyph_coverage.py"


def build_font(path, chars, name, cff=False):
    builder = FontBuilder(1000, isTTF=not cff)
    mapping = {ord(c): f"uni{ord(c):04X}" for c in chars}
    order = [".notdef", *mapping.values()]
    builder.setupGlyphOrder(order)
    builder.setupCharacterMap(mapping)
    glyphs = {}
    for glyph in order:
        pen = T2CharStringPen(600, None) if cff else TTGlyphPen(None)
        pen.moveTo((50, 0))
        pen.lineTo((550, 0))
        pen.lineTo((550, 700))
        pen.closePath()
        glyphs[glyph] = pen.getCharString() if cff else pen.glyph()
    if cff:
        builder.setupCFF(name, {"FullName": name, "FamilyName": name,
                               "Weight": "Regular"}, glyphs, {})
    else:
        builder.setupGlyf(glyphs)
    builder.setupHorizontalMetrics({g: (600, 50) for g in order})
    builder.setupHorizontalHeader(ascent=800, descent=-200)
    builder.setupNameTable({"familyName": name, "styleName": "Regular",
                            "psName": name, "fullName": name})
    builder.setupOS2(sTypoAscender=800, sTypoDescender=-200,
                    usWinAscent=800, usWinDescent=200)
    builder.setupPost()
    builder.setupMaxp()
    builder.save(path)


class FontFaces(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        build_font(self.root / "greek.ttf", "κ", "SyntheticGreek")
        build_font(self.root / "cjk.ttf", "가", "SyntheticCJK")
        build_font(self.root / "both.otf", "κ가", "SyntheticBoth", cff=True)
        with TTCollection() as collection:
            collection.fonts = [TTFont(self.root / "greek.ttf"),
                                TTFont(self.root / "cjk.ttf")]
            collection.save(self.root / "faces.ttc")

    def run_scan(self, font=None, index=None, text="κ가", strict=True, no_site=False):
        source = self.root / "source.md"
        source.write_text(text, encoding="utf-8")
        report = self.root / "report.json"
        args = [sys.executable, *(["-S"] if no_site else []), str(SCRIPT),
                str(source), "--json", str(report), "--quiet"]
        if strict:
            args += ["--strict"]
        if font:
            args += ["--font", str(self.root / font)]
        if index is not None:
            args += ["--font-index", str(index)]
        result = subprocess.run(args, capture_output=True, text=True)
        return result, json.loads(report.read_text())

    def test_standalone_ttf_missing_and_covered(self):
        result, report = self.run_scan("greek.ttf")
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertTrue(report["font_checked"])
        self.assertEqual(report["missing_in_font"], ["가"])
        self.assertEqual(report["font_check"]["face_name"], "SyntheticGreek")
        self.assertEqual(self.run_scan("greek.ttf", text="κ")[0].returncode, 0)

    def test_real_cff_otf(self):
        self.assertEqual((self.root / "both.otf").read_bytes()[:4], b"OTTO")
        result, report = self.run_scan("both.otf")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(report["font_checked"])
        self.assertEqual(report["missing_in_font"], [])

    def test_collection_never_unions_faces(self):
        for index, missing, name in [(0, "가", "SyntheticGreek"), (1, "κ", "SyntheticCJK")]:
            with self.subTest(index=index):
                result, report = self.run_scan("faces.ttc", index)
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertTrue(report["font_checked"])
                self.assertEqual(report["missing_in_font"], [missing])
                self.assertEqual(report["font_check"]["face_index"], index)
                self.assertEqual(report["font_check"]["face_name"], name)
                self.assertEqual(report["font_check"]["n_faces"], 2)
        self.assertEqual(self.run_scan("faces.ttc", 0, text="κ")[0].returncode, 0)
        self.assertEqual(self.run_scan("faces.ttc", 1, text="κ")[0].returncode, 1)

    def test_face_selection_required_even_if_file_renamed(self):
        (self.root / "renamed.bin").write_bytes((self.root / "faces.ttc").read_bytes())
        for filename in ("faces.ttc", "renamed.bin"):
            result, report = self.run_scan(filename)
            self.assertEqual(result.returncode, 1)
            self.assertFalse(report["font_checked"])
            self.assertEqual(report["font_check"]["reason"], "face_selection_required")
            self.assertIn("font_checked=false", result.stderr)
            self.assertIn("--font-index 0..1", result.stderr)

    def test_bad_index_cannot_silently_select_another_face(self):
        for filename, index in [("faces.ttc", 2), ("greek.ttf", 1)]:
            result, report = self.run_scan(filename, index)
            self.assertEqual(result.returncode, 1)
            self.assertFalse(report["font_checked"])
            self.assertEqual(report["font_check"]["reason"], "font_index_out_of_range")

    def test_missing_corrupt_and_truncated_fonts(self):
        (self.root / "corrupt.ttf").write_bytes(b"not a font")
        (self.root / "truncated.ttc").write_bytes(b"ttcf")
        for filename, reason in [("absent.ttf", "font_not_found"),
                                 ("corrupt.ttf", "font_unreadable"),
                                 ("truncated.ttc", "font_unreadable")]:
            result, report = self.run_scan(filename)
            self.assertEqual(result.returncode, 1)
            self.assertFalse(report["font_checked"])
            self.assertEqual(report["font_check"]["reason"], reason)

    def test_missing_fonttools_has_machine_readable_reason(self):
        result, report = self.run_scan("greek.ttf", no_site=True)
        self.assertEqual(result.returncode, 1)
        self.assertFalse(report["font_checked"])
        self.assertEqual(report["font_check"]["reason"], "fonttools_unavailable")

    def test_no_unicode_cmap_is_unavailable(self):
        with TTFont(self.root / "greek.ttf") as font:
            font["cmap"].tables = []
            font.save(self.root / "no-cmap.ttf")
        result, report = self.run_scan("no-cmap.ttf")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(report["font_check"]["reason"], "unicode_cmap_unavailable")
        self.assertFalse(report["font_checked"])

    def test_preferred_unicode_cmap_not_union_of_subtables(self):
        with TTFont(self.root / "greek.ttf") as font:
            for table in font["cmap"].tables:
                if table.platformID == 3:
                    table.cmap = {}
            font.save(self.root / "conflicting-cmaps.ttf")
        result, report = self.run_scan("conflicting-cmaps.ttf", text="κ")
        self.assertEqual(result.returncode, 1)
        self.assertTrue(report["font_checked"])
        self.assertEqual(report["missing_in_font"], ["κ"])

    def test_advisory_and_plain_ascii_exit_contract(self):
        self.assertEqual(self.run_scan()[0].returncode, 1)
        self.assertEqual(self.run_scan(text="ASCII only")[0].returncode, 0)
        result, report = self.run_scan("faces.ttc", strict=False)
        self.assertEqual(result.returncode, 0)
        self.assertFalse(report["font_checked"])
        result, report = self.run_scan("faces.ttc", text="ASCII only")
        self.assertEqual(result.returncode, 0)
        self.assertFalse(report["font_checked"])

    def test_index_usage_errors(self):
        for args in [("--font-index", "0"),
                     ("--font", "unused.ttf", "--font-index", "-1")]:
            result = subprocess.run([sys.executable, str(SCRIPT), "unused.md", *args],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn("--font-index requires", result.stderr)


if __name__ == "__main__":
    unittest.main()
