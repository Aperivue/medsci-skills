#!/usr/bin/env bash
# Self-test for the two gates that decide what this package is allowed to contain:
#   scripts/check_bundled_media_license.py  — every image we ship, INCLUDING the ones inside a zip
#   scripts/check_third_party_index.py      — the LICENSE must describe the package you downloaded
#
# The gate added in PR #335 shipped with no self-test at all, which is how it came to spend a day
# printing "OK: all 8 bundled image(s) may be shipped" while 239 KB of someone else's images —
# a society's wordmark and a published paper's patient CT figure — rode past it inside a .pptx.
# A passing gate proves the gate RAN. It does not prove it would CATCH anything.
#
# So this file does not merely check that the live tree is clean. It rebuilds each defect and
# demands the gate FAIL on it:
#
#   1. an image inside a container that nothing declares      -> BUNDLED_MEDIA_UNLICENSED
#   2. a loose image with no provenance                        -> BUNDLED_MEDIA_UNLICENSED
#   3. a file present that the LICENSE swears is not bundled   -> THIRD_PARTY_INDEX_DRIFT
#   4. a third-party payload the LICENSE never mentions        -> THIRD_PARTY_INDEX_DRIFT
#
# and — the half that keeps a gate alive — that it stays SILENT on work that is genuinely ours.
# A gate that fires on good work gets switched off, and it takes the honest gates with it.
set -u

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MEDIA="$REPO_ROOT/scripts/check_bundled_media_license.py"
INDEX="$REPO_ROOT/scripts/check_third_party_index.py"

pass=0
fail=0
ck() {
  local label="$1" expected="$2" actual="$3"
  if [ "$expected" = "$actual" ]; then
    printf '  PASS  %-56s exit=%s\n' "$label" "$actual"
    pass=$((pass + 1))
  else
    printf '  FAIL  %-56s expected=%s actual=%s\n' "$label" "$expected" "$actual"
    fail=$((fail + 1))
  fi
}

if ! python3 -c "import pptx" 2>/dev/null; then
  echo "SKIP: python-pptx not installed (CI installs it); container fixtures cannot be built."
  exit 0
fi

# ---------------------------------------------------------------- the live tree must be clean
python3 "$MEDIA" --strict >/dev/null 2>&1
ck "live repo: every shipped image is one we may ship" 0 "$?"
python3 "$INDEX" --strict >/dev/null 2>&1
ck "live repo: the LICENSE describes the actual tree" 0 "$?"

# ---------------------------------------------------------------- fixture tree
FIX="$(mktemp -d)"
trap 'rm -rf "$FIX"' EXIT
mkdir -p "$FIX/skills/demo-skill/templates"
cp "$REPO_ROOT/LICENSE" "$FIX/LICENSE"

# A .pptx carrying an image. This is the shape the real defect had: on the filesystem it is one
# opaque binary, and the image is only visible if you open the zip.
python3 - "$FIX/skills/demo-skill/templates/borrowed.pptx" <<'PY'
import sys, zlib, struct
from pptx import Presentation
from pptx.util import Inches

def tiny_png(path):
    def chunk(t, d):
        c = t + d
        return struct.pack(">I", len(d)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)
    ihdr = struct.pack(">IIBBBBB", 4, 4, 8, 2, 0, 0, 0)
    raw = b"".join(b"\x00" + b"\xff\x00\x00" * 4 for _ in range(4))
    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
           + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))
    path.write_bytes(png)

from pathlib import Path
import tempfile
img = Path(tempfile.mkdtemp()) / "borrowed.png"
tiny_png(img)
prs = Presentation()
s = prs.slides.add_slide(prs.slide_layouts[6])
s.shapes.add_picture(str(img), Inches(1), Inches(1), Inches(1), Inches(1))
prs.save(sys.argv[1])
PY

# 1) an image inside a container that nothing declares
python3 "$MEDIA" --root "$FIX" --strict >/dev/null 2>&1
ck "REGRESSION: image hidden inside an undeclared .pptx" 1 "$?"

# ...and the gate must SAY it is inside the container, not merely that something is wrong
python3 "$MEDIA" --root "$FIX" 2>&1 | grep -q "embedded image" \
  && ck "the message names the container as the hiding place" 0 0 \
  || ck "the message names the container as the hiding place" 0 1

# 2) a loose image with no provenance (the PR #335 defect, unchanged)
rm -f "$FIX/skills/demo-skill/templates/borrowed.pptx"
python3 - "$FIX/skills/demo-skill/templates/cropped_from_a_paper.png" <<'PY'
import sys, zlib, struct
from pathlib import Path
def chunk(t, d):
    c = t + d
    return struct.pack(">I", len(d)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)
ihdr = struct.pack(">IIBBBBB", 4, 4, 8, 2, 0, 0, 0)
raw = b"".join(b"\x00" + b"\xff\x00\x00" * 4 for _ in range(4))
Path(sys.argv[1]).write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
                              + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))
PY
python3 "$MEDIA" --root "$FIX" --strict >/dev/null 2>&1
ck "REGRESSION: loose image with no sidecar (the PR #335 bug)" 1 "$?"

# 3) NEGATIVE FIXTURE — a container with no images at all is fine, and must stay fine.
rm -f "$FIX/skills/demo-skill/templates/cropped_from_a_paper.png"
python3 - "$FIX/skills/demo-skill/templates/ours.pptx" <<'PY'
import sys
from pptx import Presentation
from pptx.util import Inches, Pt
prs = Presentation()
s = prs.slides.add_slide(prs.slide_layouts[6])
tb = s.shapes.add_textbox(Inches(1), Inches(1), Inches(6), Inches(1))
tb.text_frame.text = "Text is not an image. This ships."
prs.save(sys.argv[1])
PY
python3 "$MEDIA" --root "$FIX" --strict >/dev/null 2>&1
ck "NEGATIVE: an image-free container does not fire" 0 "$?"

# 4) the LICENSE's promise, broken
mkdir -p "$FIX/skills/make-figures/references/visual_abstract_templates"
: > "$FIX/skills/make-figures/references/visual_abstract_templates/european_radiology.pptx"
python3 "$INDEX" --root "$FIX" --strict >/dev/null 2>&1
ck "REGRESSION: a file the LICENSE swears we do not bundle" 1 "$?"
rm -f "$FIX/skills/make-figures/references/visual_abstract_templates/european_radiology.pptx"

# 5) a third-party payload the LICENSE never mentions
mkdir -p "$FIX/skills/manage-refs/citation_styles"
: > "$FIX/skills/manage-refs/citation_styles/some.csl"
python3 - "$FIX/LICENSE" <<'PY'
import sys, pathlib
p = pathlib.Path(sys.argv[1])
p.write_text(p.read_text().replace("CC BY-SA 3.0", "(licence unstated)"))
PY
python3 "$INDEX" --root "$FIX" --strict >/dev/null 2>&1
ck "REGRESSION: shipped payload the LICENSE never declares" 1 "$?"

echo
echo "  $pass passed, $fail failed"
[ "$fail" -eq 0 ] || exit 1
