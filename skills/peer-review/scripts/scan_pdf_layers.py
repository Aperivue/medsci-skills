#!/usr/bin/env python3
"""scan_pdf_layers.py — extract a span manifest from a manuscript PDF for
check_pdf_injection.py.

This is the PyMuPDF-backed reader half of the peer-review injection guard. It
turns a PDF into the deterministic JSON the (stdlib-only) detector audits:
every text span with its font size, colour, local page-background colour, and
on-page fraction, plus any text drawn under render mode 3 (invisible) and the
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
import re
import sys

try:
    import fitz  # PyMuPDF
except ImportError:
    sys.exit("scan_pdf_layers.py requires PyMuPDF: pip install pymupdf")


def _int_to_rgb(c: int) -> list[int]:
    return [(c >> 16) & 0xFF, (c >> 8) & 0xFF, c & 0xFF]


def _page_background(page: "fitz.Page") -> list[int]:
    """Most common pixel colour on a low-res render = the page background."""
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
    try:
        xmp = doc.xref_xml_metadata() if hasattr(doc, "xref_xml_metadata") else ""
    except Exception:
        xmp = ""
    if xmp:
        meta["_xmp"] = re.sub(r"<[^>]+>", " ", xmp)  # strip XML tags, keep text
    manifest["metadata"] = meta

    for pno, page in enumerate(doc, start=1):
        bg = _page_background(page)
        prect = page.rect
        for block in page.get_text("dict").get("blocks", []):
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    if not span.get("text", "").strip():
                        continue
                    bbox = fitz.Rect(span["bbox"])
                    manifest["spans"].append({
                        "page": pno,
                        "text": span["text"],
                        "size": round(float(span.get("size", 12.0)), 2),
                        "color": _int_to_rgb(span.get("color", 0)),
                        "bg": bg,
                        "visible_frac": round(_visible_fraction(bbox, prect), 3),
                    })
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
