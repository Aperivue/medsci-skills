#!/usr/bin/env python3
"""Exercise wrapper precedence through real pandoc LaTeX output, without TeX.

A failing xelatex stub satisfies the wrapper's dependency lookup. It must never
execute: these tests stop at LaTeX generation; they do not certify a rendered PDF.

MissingGlyphs goes one step further with a different stub: real pandoc runs it
as the PDF engine, and it writes the log xelatex writes when a font has no glyph
for a character. That exercises pandoc's relay of the warning and the wrapper's
verdict on it; it does not typeset anything.
"""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/render_pdf.sh"
FRONTMATTER = '''---
mainfont: Frontmatter Body
CJKmainfont: Frontmatter CJK
geometry:
  - paperwidth=180mm
  - paperheight=240mm
  - margin=30mm
fontsize: 12pt
linestretch: 1.6
colorlinks: false
---

Body text.

| Label | Longer description |
|-------|--------------------|
| A | Some example content |
'''


class RenderPrecedence(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(shutil.which("pandoc"), "Install pandoc to run render regressions")
        self.temp = tempfile.TemporaryDirectory(prefix="render test ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        stub = self.bin / "xelatex"
        stub.write_text("#!/bin/sh\necho 'ERROR: TeX must not execute in this test' >&2\nexit 93\n")
        stub.chmod(0o755)
        self.transient = self.root / "transient"
        self.transient.mkdir()
        self.env = dict(os.environ, PATH=str(self.bin) + os.pathsep + os.environ["PATH"],
                        TMPDIR=str(self.transient))

    def render(self, text, wrapper=(), extra=()):
        source = self.root / "input file.md"
        source.write_text(text, encoding="utf-8")
        original = source.read_bytes()
        output = self.root / "output file.tex"
        result = subprocess.run(["bash", str(SCRIPT), "-i", str(source), "-o", str(output),
                                 *wrapper, "--", "-s", "-t", "latex", *extra],
                                env=self.env, capture_output=True, text=True)
        self.assertEqual(source.read_bytes(), original, "Source bytes must be preserved")
        self.assertEqual(list(self.transient.iterdir()), [], "Temporary files must be removed")
        return result, output.read_text() if output.exists() else ""

    def assert_frontmatter(self, tex):
        self.assertIn("12pt,", tex)
        self.assertIn(r"\setmainfont[]{Frontmatter Body}", tex)
        self.assertIn(r"\setCJKmainfont[]{Frontmatter CJK}", tex)
        self.assertIn(r"\usepackage[paperwidth=180mm,paperheight=240mm,margin=30mm]{geometry}", tex)
        self.assertIn(r"\setstretch{1.6}", tex)
        self.assertNotIn("colorlinks=true", tex)
        self.assertNotIn("margin=0.85in", tex)
        self.assertNotIn("Fallback Body", tex)

    def test_frontmatter_beats_wrapper_and_os_defaults(self):
        for wrapper in [(), ("--font", "Fallback Body", "--cjk-font", "Fallback CJK")]:
            with self.subTest(wrapper=wrapper):
                result, tex = self.render(FRONTMATTER, wrapper)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assert_frontmatter(tex)
                self.assertIn("font fallbacks:", result.stderr)

    def test_defaults_fill_missing_metadata(self):
        result, tex = self.render("Body text.\n", ("--font", "Fallback Body", "--cjk-font", "Fallback CJK"))
        self.assertEqual(result.returncode, 0, result.stderr)
        for value in ("11pt,", r"\setmainfont[]{Fallback Body}",
                      r"\setCJKmainfont[]{Fallback CJK}", "margin=0.85in",
                      r"\setstretch{1.25}", "colorlinks=true"):
            self.assertIn(value, tex)

    def test_partial_frontmatter_keeps_other_defaults(self):
        result, tex = self.render("---\nfontsize: 12pt\n---\n\nBody.\n",
                                  ("--font", "Fallback Body", "--cjk-font", "Fallback CJK"))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("12pt,", tex)
        self.assertIn(r"\setmainfont[]{Fallback Body}", tex)
        self.assertIn("margin=0.85in", tex)

    def test_explicit_pandoc_arguments_still_override(self):
        result, tex = self.render(FRONTMATTER, extra=("-V", "mainfont=Explicit Body",
            "-V", "CJKmainfont=Explicit CJK", "-V", "fontsize=10pt",
            "-V", "geometry=margin=20mm", "-M", "linestretch=1.1"))
        self.assertEqual(result.returncode, 0, result.stderr)
        for value in (r"\setmainfont[]{Explicit Body}", r"\setCJKmainfont[]{Explicit CJK}",
                      "10pt,", r"\usepackage[margin=20mm]{geometry}", r"\setstretch{1.1}"):
            self.assertIn(value, tex)
        self.assertNotIn("Frontmatter Body", tex)

    def test_inferred_table_preserves_frontmatter_and_source(self):
        result, tex = self.render(FRONTMATTER, ("--infer-colwidths", "--font", "Fallback Body"))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_frontmatter(tex)
        self.assertIn(r"\begin{longtable}", tex)

    def test_nonstandard_fontsize_switches_to_koma(self):
        # article honours only 10/11/12pt; 8.5pt would be dropped without a word.
        result, tex = self.render("---\nfontsize: 8.5pt\n---\n\nBody.\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("]{scrartcl}", tex)
        self.assertIn("fontsize=8.5pt", tex)  # KOMA reads a fractional size only this way
        self.assertIn("scrartcl", result.stderr)

    def test_cli_fontsize_switches_to_koma(self):
        result, tex = self.render("Body.\n", extra=("-V", "fontsize=9pt"))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("]{scrartcl}", tex)

    def test_explicit_documentclass_and_standard_sizes_are_left_alone(self):
        result, tex = self.render("---\nfontsize: 9pt\ndocumentclass: extarticle\n---\n\nBody.\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("]{extarticle}", tex)
        self.assertNotIn("scrartcl", result.stderr)
        self.assertNotIn("fontsize=9pt", tex)
        for text in ("Body.\n", FRONTMATTER):
            with self.subTest(text=text[:12]):
                result, tex = self.render(text)
                self.assertIn("]{article}", tex)
                self.assertNotIn("scrartcl", result.stderr)

    def test_failed_pandoc_propagates_failure_and_cleans_temp(self):
        result, _ = self.render(FRONTMATTER, ("--infer-colwidths",), ("--invalid-render-test-option",))
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("[render_pdf] ok", result.stderr)


# Writes what xelatex writes when the font lacks a character: the PDF, and a log
# line pandoc turns into a "Missing character" warning. STUB_MISSING=0 is a clean run.
ENGINE_STUB = r"""#!/bin/sh
outdir=""; tex=""; prev=""
for a in "$@"; do
  case "$prev" in -output-directory) outdir="$a" ;; esac
  case "$a" in -output-directory=*) outdir="${a#-output-directory=}" ;; *.tex) tex="$a" ;; esac
  prev="$a"
done
job=$(basename "$tex" .tex)
[ -n "$outdir" ] || outdir=$(dirname "$tex")
{
  echo "This is a xelatex stub"
  if [ "$STUB_MISSING" = "1" ]; then
    printf 'Missing character: There is no \342\232\240 (U+26A0) in font Stub Sans/OT!\n'
    printf 'Missing character: There is no \342\232\240 (U+26A0) in font Stub Sans/OT!\n'
  fi
  echo "Output written on $job.pdf (1 page)."
} > "$outdir/$job.log"
cat "$outdir/$job.log"
printf '%%PDF-1.4\n%%stub\n' > "$outdir/$job.pdf"
"""


class MissingGlyphs(unittest.TestCase):
    """xelatex drops a character its font lacks and still exits 0."""

    def setUp(self):
        self.assertIsNotNone(shutil.which("pandoc"), "Install pandoc to run render regressions")
        self.temp = tempfile.TemporaryDirectory(prefix="render glyph test ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        bindir = self.root / "bin"
        bindir.mkdir()
        stub = bindir / "xelatex"
        stub.write_text(ENGINE_STUB)
        stub.chmod(0o755)
        self.source = self.root / "input.md"
        self.source.write_text("Status \u26a0 pending.\n", encoding="utf-8")
        self.output = self.root / "out.pdf"
        self.env = dict(os.environ, PATH=str(bindir) + os.pathsep + os.environ["PATH"])

    def render(self, missing, *wrapper):
        env = dict(self.env, STUB_MISSING="1" if missing else "0")
        return subprocess.run(["bash", str(SCRIPT), "-i", str(self.source), "-o", str(self.output),
                               *wrapper], env=env, capture_output=True, text=True)

    def test_missing_glyph_fails_and_names_it(self):
        result = self.render(True)
        self.assertEqual(result.returncode, 4, result.stderr)
        self.assertNotIn("[render_pdf] ok", result.stderr)
        self.assertIn("U+26A0", result.stderr)
        self.assertIn("x2", result.stderr)          # counted, not just noticed
        self.assertIn("Missing character", result.stderr)  # pandoc's own warning is re-emitted
        self.assertTrue(self.output.exists())        # written, but reported incomplete

    def test_allow_missing_glyphs_reports_and_exits_zero(self):
        result = self.render(True, "--allow-missing-glyphs")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("U+26A0", result.stderr)
        self.assertIn("--allow-missing-glyphs", result.stderr)

    def test_clean_render_is_ok(self):
        result = self.render(False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("[render_pdf] ok", result.stderr)
        self.assertNotIn("not drawn", result.stderr)


if __name__ == "__main__":
    unittest.main()
