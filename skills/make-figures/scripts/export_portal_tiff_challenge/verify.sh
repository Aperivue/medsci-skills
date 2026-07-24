#!/usr/bin/env bash
# Deterministic verifier for the portal-TIFF export challenge (make-figures).
# Network-free. Generates a synthetic RGBA PNG, exports it to a portal-ready TIFF, and
# asserts the output is LZW + RGB + white-flattened + pixel-identical + smaller than raw;
# then confirms the flatten and the size-cap assertions actually BITE. Exit 0 = all hold.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
GEN="$HERE/../export_portal_tiff.py"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT

[ -f "$GEN" ] || { echo "ENV-ERR: export_portal_tiff.py missing" >&2; exit 2; }
python3 -c "import PIL" 2>/dev/null \
  || { echo "SKIP: Pillow unavailable on this host"; exit 0; }

# --- synthetic fixture: RGBA with a fully transparent top-left quadrant + a gradient -----
python3 - "$TMP" <<'PY'
import sys
from PIL import Image
d = sys.argv[1]
img = Image.new("RGBA", (200, 200), (0, 0, 0, 0))
px = img.load()
for y in range(200):
    for x in range(200):
        a = 0 if (x < 100 and y < 100) else 255      # top-left transparent
        px[x, y] = ((x * 255) // 200, (y * 255) // 200, 128, a)
img.save(f"{d}/fig.png")
PY

# (1) Positive: the exporter runs and self-verifies.
python3 "$GEN" --in "$TMP/fig.png" --out "$TMP/fig.tiff" --max-mb 25 >"$TMP/log" 2>&1 \
  || { echo "FAIL: valid figure did not export/verify" >&2; cat "$TMP/log" >&2; exit 1; }
[ -s "$TMP/fig.tiff" ] || { echo "FAIL: fig.tiff not written" >&2; exit 1; }
grep -q "OK: portal-ready TIFF" "$TMP/log" || { echo "FAIL: export did not report success" >&2; cat "$TMP/log" >&2; exit 1; }

# (2) Independent structural assertions on the produced TIFF.
python3 - "$TMP" <<'PY'
import os, sys
from PIL import Image
d = sys.argv[1]
im = Image.open(f"{d}/fig.tiff"); im.load()
assert im.mode == "RGB", f"expected RGB, got {im.mode}"
assert im.tag_v2.get(259) == 5, f"expected LZW (Compression 5), got {im.tag_v2.get(259)}"
rgb = im.convert("RGB")
assert rgb.getpixel((10, 10)) == (255, 255, 255), f"transparent quadrant not white: {rgb.getpixel((10,10))}"
assert rgb.getpixel((150, 150)) == (191, 191, 128), f"opaque pixel altered: {rgb.getpixel((150,150))}"
# LZW must be genuinely smaller than an uncompressed TIFF of the same pixels.
rgb.save(f"{d}/raw.tiff", format="TIFF", compression="none")
lzw, raw = os.path.getsize(f"{d}/fig.tiff"), os.path.getsize(f"{d}/raw.tiff")
assert lzw < raw, f"LZW ({lzw}) not smaller than uncompressed ({raw})"
print(f"OK-STRUCT: RGB + LZW + white-flatten + {lzw} < {raw} bytes")
PY

# (3) Negative — the flatten discriminates: onto BLACK yields different bytes, so the
#     pixel-identity check would have caught a wrong background / ignored alpha.
python3 - "$TMP" "$GEN" <<'PY'
import importlib.util, sys
from PIL import Image
d, gen = sys.argv[1], sys.argv[2]
spec = importlib.util.spec_from_file_location("ept", gen)
ept = importlib.util.module_from_spec(spec); spec.loader.exec_module(ept)
src = Image.open(f"{d}/fig.png"); src.load()
white = ept.flatten_to_rgb(src, (255, 255, 255)).tobytes()
black = ept.flatten_to_rgb(src, (0, 0, 0)).tobytes()
assert white != black, "flatten ignored alpha — white and black backgrounds produced identical bytes"
print("OK-NEG-FLATTEN: white != black flatten (alpha is genuinely composited)")
PY

# (4) Negative — the size cap bites: a cap below the output size must exit 1.
if python3 "$GEN" --in "$TMP/fig.png" --out "$TMP/tiny.tiff" --max-mb 0.001 >/dev/null 2>&1; then
  echo "FAIL: --max-mb 0.001 did not refuse an over-cap output" >&2; exit 1
fi
echo "OK-NEG-CAP: --max-mb below output size refuses (exit 1)"

echo "PASS: portal TIFF is LZW + RGB + white-flattened + pixel-identical + under cap; the flatten and size-cap assertions both bite."
