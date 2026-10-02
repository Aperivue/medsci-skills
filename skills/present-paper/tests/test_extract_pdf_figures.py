#!/usr/bin/env python3
"""A figure labelled with paper A must be cut from paper A — and a skipped item is not a success.

extract_pdf_figures.py rendered every PDF in a batch to the same temp prefix, `page_<n>`. Paper B's
page 1 overwrote paper A's page 1 while the cache still pointed at that file, so the second crop
of A came out of B and was logged "OK ... A.pdf page 1". A missing PDF printed SKIP and the run
exited 0.

  POSITIVE  A (red) p1, B (blue) p1, A p1 again with another crop: every crop is its own paper's
            colour. A config with a missing PDF exits non-zero and names the item.
  NEGATIVE  the same config without the missing PDF exits 0 and writes all three figures.

Needs Pillow, PyYAML and pdftoppm (poppler); skips cleanly (exit 0) without them. Network-free.

    python3 skills/present-paper/tests/test_extract_pdf_figures.py
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    from PIL import Image
    import yaml  # noqa: F401
except ImportError:
    print("Pillow / PyYAML not installed — SKIP")
    sys.exit(0)
if not shutil.which("pdftoppm"):
    print("pdftoppm not on PATH — SKIP")
    sys.exit(0)

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "extract_pdf_figures.py"
TMP = Path(tempfile.mkdtemp())
fails = []

RED, BLUE = (255, 0, 0), (0, 0, 255)
Image.new("RGB", (200, 200), RED).save(TMP / "A.pdf", "PDF", resolution=72)
Image.new("RGB", (200, 200), BLUE).save(TMP / "B.pdf", "PDF", resolution=72)

ITEMS = """\
  - {name: A_fig1, pdf: A.pdf, page: 1, crop: [0.1, 0.1, 0.9, 0.9]}
  - {name: B_fig1, pdf: B.pdf, page: 1, crop: [0.1, 0.1, 0.9, 0.9]}
  - {name: A_fig2, pdf: A.pdf, page: 1, crop: [0.2, 0.2, 0.8, 0.8]}
"""


def run(cfg_text: str, out: Path):
    cfg = TMP / f"{out.name}.yaml"
    cfg.write_text(f"dpi: 36\npdf_dir: {TMP}\nitems:\n{cfg_text}")
    return subprocess.run([sys.executable, str(SCRIPT), "--config", str(cfg),
                           "--out-dir", str(out)], capture_output=True, text=True)


def dominant(png: Path):
    img = Image.open(png).convert("RGB")
    r, g, b = img.getpixel((img.width // 2, img.height // 2))
    return "red" if r > 200 and b < 60 else "blue" if b > 200 and r < 60 else f"{(r, g, b)}"


# --- NEGATIVE control + the cache defect -----------------------------------------------------
good = TMP / "good"
r = run(ITEMS, good)
if r.returncode != 0:
    fails.append(f"a complete batch must exit 0; got {r.returncode}: {r.stdout}{r.stderr}")
want = {"A_fig1": "red", "B_fig1": "blue", "A_fig2": "red"}
for name, colour in want.items():
    png = good / f"{name}.png"
    if not png.is_file():
        fails.append(f"{name}.png was not written")
        continue
    got = dominant(png)
    if got != colour:
        fails.append(f"{name} is labelled with its own paper but is {got}, not {colour} — "
                     "another PDF's render was cropped")

# --- POSITIVE: a skipped item is a failed batch -----------------------------------------------
partial = TMP / "partial"
r = run(ITEMS + "  - {name: C_fig1, pdf: missing.pdf, page: 1, crop: [0.1, 0.1, 0.9, 0.9]}\n",
        partial)
if r.returncode == 0:
    fails.append(f"a batch with a missing PDF exited 0: {r.stdout}")
elif "C_fig1" not in r.stderr:
    fails.append(f"the failing batch must name the item it skipped: {r.stderr}")

if fails:
    print("FAIL — extract_pdf_figures")
    for f in fails:
        print("  ·", f)
    sys.exit(1)
print("PASS — each crop comes from its own PDF; a skipped item fails the batch")
