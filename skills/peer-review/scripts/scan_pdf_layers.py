#!/usr/bin/env python3
"""scan_pdf_layers.py — extract a span manifest from a manuscript PDF for
check_pdf_injection.py.

This is the PyMuPDF-backed reader half of the peer-review injection guard. It
turns a PDF into the deterministic JSON the (stdlib-only) detector audits:
every text span with its font size, colour, the background colour under its own
box when that box has one flat background (else the page's), how many of its
glyphs the page render actually shows in its colour (glyphs / glyphs_inked),
its on-page fraction and, when the text trace shows it drawn invisibly or
translucently, its render mode (3) or opacity; plus any text drawn under render
mode 3 (invisible) and the
document metadata. It applies no thresholds and makes no verdict — that is the
detector's job — so all tuning lives in one place and this reader stays a thin,
faithful transcription of what an LLM ingesting the text layer would see.

Named scan_* (not check_*/detect_*) on purpose: it carries the one heavy
dependency (PyMuPDF) and is therefore excluded from the MedSci-Audit detector
catalog and its CI, which run stdlib-only.

Usage:
  python3 scan_pdf_layers.py paper.pdf                      # manifest JSON to stdout
  python3 scan_pdf_layers.py paper.pdf -o paper.manifest.json
  python3 scan_pdf_layers.py paper.pdf | python3 check_pdf_injection.py - --strict

Requires: PyMuPDF  (pip install pymupdf)
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys

try:
    import fitz  # PyMuPDF
except ImportError:  # keep the module importable so the pure helpers stay testable
    fitz = None     # main() re-raises this as a clean CLI error


def _int_to_rgb(c: int) -> list[int]:
    return [(c >> 16) & 0xFF, (c >> 8) & 0xFF, c & 0xFF]


def _xmp_text(doc) -> str:
    """The document's XMP packet, XML tags stripped, or "" if there is none.

    PyMuPDF exposes two similarly named things and only one of them is the
    packet: ``get_xml_metadata()`` returns the XMP as a ``str``, whereas
    ``xref_xml_metadata()`` returns the *xref number* of that object as an
    ``int``. Feeding the latter to ``re.sub`` raises ``TypeError`` — and since a
    document with no XMP yields xref 0, which is falsy and skips the branch, the
    crash fires only on PDFs that actually carry a packet. Those are exactly the
    documents this scan exists to inspect, so the metadata vector was dead on
    every input where it mattered.

    Type is therefore checked rather than trusted, and every failure degrades to
    "no XMP" instead of propagating. This is a security gate run before a model
    reads the manuscript; a traceback here reads to the operator as "nothing
    found", which is the worst possible way to fail.
    """
    getter = getattr(doc, "get_xml_metadata", None)
    if getter is None:
        return ""
    try:
        xmp = getter()
    except Exception:
        return ""
    if not isinstance(xmp, str) or not xmp.strip():
        return ""
    return re.sub(r"<[^>]+>", " ", xmp)


RENDER_DPI = 144  # resolution of the page render that glyph boxes are read from


def _page_pixmap(page: "fitz.Page"):
    """The page as it is drawn: RGB, no alpha, everything painted in paint order."""
    return page.get_pixmap(dpi=RENDER_DPI, colorspace=fitz.csRGB, alpha=False)


def _page_background(page: "fitz.Page") -> list[int]:
    """Most common pixel colour on a low-res render = the page background.

    The fallback for a span whose own box has no single background colour (an
    image, a gradient) or covers no pixel of the render."""
    pix = page.get_pixmap(dpi=36, colorspace=fitz.csRGB, alpha=False)
    counts: dict[tuple[int, int, int], int] = {}
    n = pix.width * pix.height
    step = max(1, n // 4000)  # sample ~4k pixels
    s = pix.samples
    for i in range(0, n, step):
        off = i * 3
        px = (s[off], s[off + 1], s[off + 2])
        counts[px] = counts.get(px, 0) + 1
    return list(max(counts, key=counts.get)) if counts else [255, 255, 255]


def _box_histogram(samples: bytes, width: int, height: int,
                   box: tuple[float, float, float, float]) -> dict:
    """Colour histogram of the rendered RGB pixels under `box` (pixel coordinates),
    clipped to the render. Empty when the box covers no pixel."""
    x0 = max(0, int(math.floor(box[0])))
    y0 = max(0, int(math.floor(box[1])))
    x1 = min(width, int(math.ceil(box[2])))
    y1 = min(height, int(math.ceil(box[3])))
    hist: dict[tuple[int, int, int], int] = {}
    stride = width * 3
    for y in range(y0, y1):
        row = samples[y * stride + x0 * 3: y * stride + x1 * 3]
        for px in zip(row[0::3], row[1::3], row[2::3]):
            hist[px] = hist.get(px, 0) + 1
    return hist


def _d2(a, b) -> int:
    return sum((int(x) - int(y)) ** 2 for x, y in zip(a, b))


def _local_background(hist: dict, text_rgb) -> tuple[tuple | None, tuple | None]:
    """(background the glyphs are tested against, background to report or None).

    The text's own pixels are never counted as background: on an image or a
    gradient no background colour is common, and the mode of the whole box was the
    text colour itself. So:
      - text colour on more than half of the box: the box is a solid block of the
        text's colour (text on its own colour); both backgrounds are that colour;
      - otherwise the candidate is the most common colour that is not the text
        colour. It is reported only when it holds more than half of those pixels
        (a single flat background: paper, a box, a banner); on an image or a
        gradient None is reported and the caller keeps the page background, as
        before this check existed. The glyph test still uses the candidate.
    (None, None) for an empty histogram."""
    if not hist:
        return None, None
    text = tuple(int(v) for v in text_rgb)
    total = sum(hist.values())
    if hist.get(text, 0) * 2 > total:
        return text, text
    rest = {c: n for c, n in hist.items() if c != text}
    cand = max(rest, key=lambda c: (rest[c], c))
    uniform = rest[cand] * 2 > sum(rest.values())
    return cand, (cand if uniform else None)


def _ink_colour(text_rgb, bg, opacity) -> tuple:
    """Colour a glyph painted at `opacity` over `bg` comes out as (opaque = text)."""
    if opacity is None or opacity >= 1.0:
        return tuple(int(v) for v in text_rgb)
    a = max(0.0, float(opacity))
    return tuple(int(round(a * t + (1.0 - a) * b)) for t, b in zip(text_rgb, bg))


def _inked(hist: dict, ink_rgb, bg: tuple) -> bool:
    """True when some pixel under the box is strictly closer to the ink colour than
    to the background: something in the text's colour was actually drawn there."""
    return any(_d2(px, ink_rgb) < _d2(px, bg) for px in hist)


def _render_check(pix, to_px, span: dict, text_rgb: list[int], opacity=None):
    """(reported local background or None, glyphs, glyphs_inked) for one rawdict span.

    See _local_background for how the background under the span's own box is
    chosen, so white text on a dark banner is judged against the banner, black text
    on a black box against the box, and a label over an image or a gradient against
    the page as before. A glyph is inked when its box in the page render holds a
    pixel closer to the span's colour (blended at the span's opacity) than to that
    background. An un-inked glyph was covered by a later shape, painted
    transparent, not painted, or drawn on its own colour. Applies no threshold; the
    detector decides. (None, 0, 0) when the span covers no pixel of the render.
    """
    samples, w, h = pix.samples, pix.width, pix.height
    hist = _box_histogram(samples, w, h, tuple(fitz.Rect(span["bbox"]) * to_px))
    test_bg, report_bg = _local_background(hist, text_rgb)
    if test_bg is None:
        return None, 0, 0
    ink = _ink_colour(text_rgb, test_bg, opacity)
    glyphs = inked = 0
    for ch in span.get("chars", ()):
        if not ch.get("c", "").strip():
            continue
        ch_hist = _box_histogram(samples, w, h, tuple(fitz.Rect(ch["bbox"]) * to_px))
        if not ch_hist:
            continue
        glyphs += 1
        inked += _inked(ch_hist, ink, test_bg)
    return (list(report_bg) if report_bg is not None else None), glyphs, inked


def _text_traces(page: "fitz.Page") -> list[dict]:
    """Text the page draws invisibly or translucently, from PyMuPDF's text trace:
    render mode 3 (trace type 3) or opacity below 1. get_text("dict") reports both
    as ordinary spans, so without this render-mode-3 and opacity-0 text reached the
    sanitized "visible-only" text, and a faint watermark could not be told from
    text that is not drawn."""
    out: list[dict] = []
    try:
        traces = page.get_texttrace()
    except Exception:
        return out
    for t in traces:
        invisible = t.get("type") == 3
        opacity = t.get("opacity")
        if not invisible and not (opacity is not None and float(opacity) < 1.0):
            continue
        text = "".join(chr(c[0]) for c in t.get("chars", ()) if c and c[0] >= 0)
        out.append({"bbox": tuple(t.get("bbox", (0, 0, 0, 0))), "text": text,
                    "invisible": invisible, "opacity": opacity})
    return out


def _match_hidden(bbox: tuple, text: str, hidden: list[dict]) -> dict | None:
    """The invisible or translucent trace that drew this span: an overlapping box
    and shared text."""
    key = "".join(text.split())
    if not key:
        return None
    for h in hidden:
        hb = h["bbox"]
        if hb[0] >= bbox[2] or bbox[0] >= hb[2] or hb[1] >= bbox[3] or bbox[1] >= hb[3]:
            continue
        hkey = "".join(h["text"].split())
        if hkey and (key in hkey or hkey in key):
            return h
    return None


def _visible_fraction(bbox: "fitz.Rect", page_rect: "fitz.Rect") -> float:
    area = abs(bbox.get_area())
    if area == 0:
        return 1.0
    return abs((bbox & page_rect).get_area()) / area


def _invisible_render_strings(page: "fitz.Page") -> list[str]:
    """Best-effort: strings shown while text render mode == 3 (invisible).

    Walks the decompressed content stream, tracks the `N Tr` state, and collects
    literal/hex string operands of Tj/TJ/'/" emitted under mode 3. Any parse
    error just yields fewer hits, never a crash.
    """
    out: list[str] = []
    try:
        data = page.read_contents()
    except Exception:
        return out
    tok_re = re.compile(
        rb"\((?:\\.|[^\\()])*\)"   # literal string
        rb"|<[0-9A-Fa-f\s]*>"      # hex string
        rb"|[-+]?[0-9]*\.?[0-9]+"  # number
        rb"|[A-Za-z'\"*]+")        # operator / name
    render_mode = 0
    nums: list[float] = []
    pending: list[str] = []

    def lit(b: bytes) -> str:
        return re.sub(rb"\\([nrtbf()\\])", b"", b[1:-1]).decode("latin-1", "ignore")

    def hx(b: bytes) -> str:
        h = re.sub(rb"[^0-9A-Fa-f]", b"", b[1:-1])
        if len(h) % 2:
            h += b"0"
        try:
            return bytes.fromhex(h.decode()).decode("latin-1", "ignore")
        except Exception:
            return ""

    for m in tok_re.finditer(data):
        t = m.group(0)
        head = t[:1]
        if head == b"(":
            pending.append(lit(t))
        elif head == b"<":
            pending.append(hx(t))
        elif head in b"-+.0123456789":
            try:
                nums.append(float(t))
            except ValueError:
                pass
        else:
            op = t.decode("latin-1", "ignore")
            if op == "Tr" and nums:
                render_mode = int(nums[-1])
            elif op in ("Tj", "'", '"', "TJ") and render_mode == 3 and pending:
                out.append("".join(pending))
            pending.clear()
            nums.clear()
    return [s for s in out if s.strip()]


def extract(path: str) -> dict:
    doc = fitz.open(path)
    manifest: dict = {"source": path, "spans": [], "invisible_strings": [],
                      "metadata": {}}

    meta = {k: v for k, v in (doc.metadata or {}).items() if v}
    xmp = _xmp_text(doc)
    if xmp:
        meta["_xmp"] = xmp
    manifest["metadata"] = meta

    for pno, page in enumerate(doc, start=1):
        pix = _page_pixmap(page)
        page_bg = _page_background(page)
        # text coordinates are unrotated; the render is rotated and scaled
        to_px = page.rotation_matrix * fitz.Matrix(RENDER_DPI / 72.0, RENDER_DPI / 72.0)
        traces = _text_traces(page)
        prect = page.rect
        for block in page.get_text("rawdict").get("blocks", []):
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text = "".join(ch.get("c", "") for ch in span.get("chars", ()))
                    if not text.strip():
                        continue
                    bbox = fitz.Rect(span["bbox"])
                    color = _int_to_rgb(span.get("color", 0))
                    h = _match_hidden(tuple(span["bbox"]), text, traces)
                    opacity = None
                    if h is not None and h["opacity"] is not None:
                        opacity = float(h["opacity"])
                    local_bg, glyphs, inked = _render_check(pix, to_px, span, color, opacity)
                    rec = {
                        "page": pno,
                        "text": text,
                        "size": round(float(span.get("size", 12.0)), 2),
                        "color": color,
                        "bg": local_bg if local_bg is not None else page_bg,
                        "visible_frac": round(_visible_fraction(bbox, prect), 3),
                        "glyphs": glyphs,
                        "glyphs_inked": inked,
                    }
                    if h is not None:
                        if h["invisible"]:
                            rec["render_mode"] = 3
                        if opacity is not None:
                            rec["opacity"] = round(opacity, 3)
                    manifest["spans"].append(rec)
        for s in _invisible_render_strings(page):
            manifest["invisible_strings"].append({"page": pno, "text": s})

    doc.close()
    return manifest


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf", help="manuscript PDF to extract")
    ap.add_argument("-o", "--out", help="write manifest here (default: stdout)")
    args = ap.parse_args(argv)

    if fitz is None:
        sys.exit("scan_pdf_layers.py requires PyMuPDF: pip install pymupdf")

    manifest = extract(args.pdf)
    text = json.dumps(manifest, ensure_ascii=False, indent=2)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
