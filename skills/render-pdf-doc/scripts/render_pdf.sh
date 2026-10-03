#!/usr/bin/env bash
# render_pdf.sh — pandoc + xelatex wrapper for Korean academic markdown.
#
# Usage:
#   render_pdf.sh -i input.md [-o output.pdf] [--infer-colwidths]
#                 [--font "Apple SD Gothic Neo"] [--cjk-font "Apple SD Gothic Neo"]
#                 [--allow-missing-glyphs] [-- <extra pandoc args>]
#
# Defaults:
#   - macOS: mainfont/CJKmainfont = "Apple SD Gothic Neo"
#   - Linux: mainfont = "Noto Serif CJK KR", CJKmainfont = "Noto Sans CJK KR"
#   - Output path = <input>.pdf
#   - geometry = margin=0.85in, fontsize = 11pt (override via frontmatter)
#
# Frontmatter overrides wrapper/OS defaults. Explicit pandoc -V/-M arguments
# after -- retain pandoc's normal precedence over frontmatter.
#
# A fontsize other than 10/11/12pt is ignored by the standard article class; when
# no documentclass is set anywhere, the wrapper uses KOMA-Script's scrartcl
# (pandoc's documented route for other sizes), adds classoption fontsize=<size>
# when no classoption is set, and says so.
#
# xelatex drops a character its font lacks and still succeeds. The wrapper counts
# the "Missing character" warnings in pandoc's JSON --log (kept even under
# --quiet); any at all is exit 4 with the glyphs listed
# (the PDF is written but incomplete) unless --allow-missing-glyphs is given.
#
# Exit: 0 ok, 1 usage, 2 input missing, 3 dependency missing, 4 missing glyphs,
#       otherwise pandoc's own exit code.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

INPUT=""
OUTPUT=""
INFER_COLWIDTHS=0
MAINFONT=""
CJKFONT=""
ALLOW_MISSING_GLYPHS=0
EXTRA=()

usage() {
  cat >&2 <<EOF
Usage: $(basename "$0") -i <input.md> [-o <output.pdf>] [options] [-- <pandoc args>]

Options:
  -i  Input markdown
  -o  Output PDF (default: <input>.pdf)
  --infer-colwidths     Run scripts/infer_colwidths.py on a temp copy first
  --font NAME           mainfont fallback when absent from frontmatter (default: OS-detected)
  --cjk-font NAME       CJKmainfont fallback when absent from frontmatter (default: OS-detected)
  --allow-missing-glyphs
                        Report characters the font lacks but still exit 0 (default: exit 4)
  -h | --help           Help

Pass-through: any args after '--' go directly to pandoc.
EOF
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -i) INPUT="$2"; shift 2 ;;
    -o) OUTPUT="$2"; shift 2 ;;
    --infer-colwidths) INFER_COLWIDTHS=1; shift ;;
    --font) MAINFONT="$2"; shift 2 ;;
    --cjk-font) CJKFONT="$2"; shift 2 ;;
    --allow-missing-glyphs) ALLOW_MISSING_GLYPHS=1; shift ;;
    -h|--help) usage ;;
    --) shift; EXTRA=("$@"); break ;;
    *) EXTRA+=("$1"); shift ;;
  esac
done

[[ -z "$INPUT" ]] && usage
[[ -f "$INPUT" ]] || { echo "ERROR: input not found: $INPUT" >&2; exit 2; }
[[ -z "$OUTPUT" ]] && OUTPUT="${INPUT%.md}.pdf"

# OS-based font defaults
if [[ -z "$MAINFONT" || -z "$CJKFONT" ]]; then
  case "$(uname -s)" in
    Darwin)
      : "${MAINFONT:=Apple SD Gothic Neo}"
      : "${CJKFONT:=Apple SD Gothic Neo}"
      ;;
    MINGW*|MSYS*|CYGWIN*)
      # Windows: Malgun Gothic ships with Windows 7+ (the Korean UI font), so no
      # font download is needed. Noto CJK is NOT preinstalled on Windows.
      : "${MAINFONT:=Malgun Gothic}"
      : "${CJKFONT:=Malgun Gothic}"
      ;;
    *)
      : "${MAINFONT:=Noto Serif CJK KR}"
      : "${CJKFONT:=Noto Sans CJK KR}"
      ;;
  esac
fi

# Windows/Git Bash: MiKTeX's bin directory is frequently absent from the Git Bash
# PATH, so xelatex is not found even after `winget install MiKTeX.MiKTeX`. Prepend
# the known MiKTeX bin locations (best-effort) when xelatex is not already resolvable.
case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*)
    if ! command -v xelatex >/dev/null 2>&1; then
      _la="$(cygpath -u "${LOCALAPPDATA:-}" 2>/dev/null || printf '%s' "${LOCALAPPDATA:-}")"
      _pf="$(cygpath -u "${PROGRAMFILES:-}" 2>/dev/null || printf '%s' "${PROGRAMFILES:-}")"
      for _d in \
        "$_la/Programs/MiKTeX/miktex/bin/x64" \
        "$_la/Programs/MiKTeX/miktex/bin" \
        "$_pf/MiKTeX/miktex/bin/x64"; do
        if [[ -x "$_d/xelatex.exe" ]]; then PATH="$_d:$PATH"; break; fi
      done
    fi
    ;;
esac

command -v pandoc >/dev/null || { echo "ERROR: pandoc not installed" >&2; exit 3; }
command -v xelatex >/dev/null || { echo "ERROR: xelatex not installed (install mactex / texlive-xetex / MiKTeX)" >&2; exit 3; }
command -v python3 >/dev/null || { echo "ERROR: python3 not installed" >&2; exit 3; }

WORK="$INPUT"
RENDER_TMP="$(mktemp -d)"
trap 'rm -rf "$RENDER_TMP"' EXIT
if [[ "$INFER_COLWIDTHS" == "1" ]]; then
  WORK="$RENDER_TMP/$(basename "$INPUT")"
  python3 "$SCRIPT_DIR/infer_colwidths.py" "$INPUT" --out "$WORK"
fi

# --metadata-file supplies defaults that document metadata can override. -V,
# -M, and a --defaults file's metadata would override the document instead.
# JSON is accepted by pandoc; serialize arguments without interpolating code.
write_metadata() {  # $1: documentclass default, $2: classoption default (empty = none)
  python3 - "$MAINFONT" "$CJKFONT" "$1" "$2" > "$RENDER_TMP/metadata.json" <<'PY'
import json
import sys

meta = {
    "mainfont": sys.argv[1],
    "CJKmainfont": sys.argv[2],
    "geometry": "margin=0.85in",
    "fontsize": "11pt",
    "linestretch": "1.25",
    "colorlinks": True,
}
if sys.argv[3]:
    meta["documentclass"] = sys.argv[3]
if sys.argv[4]:
    meta["classoption"] = [sys.argv[4]]
json.dump(meta, sys.stdout)
PY
}

# The standard article class accepts only 10pt, 11pt and 12pt and silently
# ignores any other fontsize. Ask pandoc for the effective values (frontmatter,
# -V/-M and defaults files all applied) through a small template. A sentinel
# default shows through only when nothing else sets the value; pandoc would
# otherwise report its own built-in "article" either way.
# KOMA-Script reads a whole-point size (9pt) from the bare class option but a
# fractional one (8.5pt) only as fontsize=8.5pt, so that is added too.
UNSET="render-pdf-unset"
DOCCLASS=""
CLASSOPT=""
write_metadata "$UNSET" "$UNSET"
printf '%s\n' 'fontsize=$fontsize$' 'documentclass=$documentclass$' \
  'classoption=$for(classoption)$$classoption$$sep$,$endfor$' > "$RENDER_TMP/probe.tpl"
if pandoc --metadata-file "$RENDER_TMP/metadata.json" ${EXTRA[@]+"${EXTRA[@]}"} "$WORK" \
     -t latex --template "$RENDER_TMP/probe.tpl" -o "$RENDER_TMP/probe.txt" 2>/dev/null; then
  EFF_SIZE="$(sed -n 's/^fontsize=//p' "$RENDER_TMP/probe.txt" | tr -d '[:space:]')"
  EFF_CLASS="$(sed -n 's/^documentclass=//p' "$RENDER_TMP/probe.txt" | tr -d '[:space:]')"
  EFF_OPTS="$(sed -n 's/^classoption=//p' "$RENDER_TMP/probe.txt" | tr -d '[:space:]')"
  case "$EFF_SIZE" in
    ""|10pt|11pt|12pt) ;;
    *)
      if [[ "$EFF_CLASS" == "$UNSET" ]]; then
        DOCCLASS="scrartcl"
        MSG="[render_pdf] fontsize=$EFF_SIZE is not one of 10pt/11pt/12pt, which the standard article class ignores; using documentclass=scrartcl (KOMA-Script)"
        if [[ "$EFF_OPTS" == "$UNSET" ]]; then
          CLASSOPT="fontsize=$EFF_SIZE"
          echo "$MSG with classoption $CLASSOPT (LaTeX may still call the bare [$EFF_SIZE] option unused). Set documentclass to override." >&2
        else
          echo "$MSG. Your classoption is kept: if the size is not a whole number of points, add fontsize=$EFF_SIZE to it." >&2
        fi
      fi
      ;;
  esac
fi
write_metadata "$DOCCLASS" "$CLASSOPT"

ARGS=(
  --pdf-engine=xelatex
  --metadata-file "$RENDER_TMP/metadata.json"
  -o "$OUTPUT"
)

echo "[render_pdf] in=$INPUT out=$OUTPUT infer=$INFER_COLWIDTHS" >&2
echo "[render_pdf] font fallbacks: mainfont='$MAINFONT' CJK='$CJKFONT'; frontmatter overrides fallbacks, explicit pandoc -V/-M overrides frontmatter" >&2
# The missing-glyph verdict reads pandoc's JSON --log, which records every
# warning whatever the verbosity: a pass-through --quiet hides the warnings from
# stderr but not from the log. A --log the caller passes is kept and read; else
# the wrapper's own --log goes last, so a defaults file's log-file cannot replace it.
JSON_LOG=""
_prev=""
for _a in ${EXTRA[@]+"${EXTRA[@]}"}; do
  case "$_prev" in --log) JSON_LOG="$_a" ;; esac
  case "$_a" in --log=*) JSON_LOG="${_a#--log=}" ;; esac
  _prev="$_a"
done
LOG_ARGS=()
if [[ -z "$JSON_LOG" ]]; then
  JSON_LOG="$RENDER_TMP/pandoc.log.json"
  LOG_ARGS=(--log "$JSON_LOG")
fi
rm -f "$JSON_LOG"
# stderr goes to a file, not a pipe, so pandoc's exit status is kept as is.
PANDOC_LOG="$RENDER_TMP/pandoc.stderr"
if pandoc "${ARGS[@]}" ${EXTRA[@]+"${EXTRA[@]}"} ${LOG_ARGS[@]+"${LOG_ARGS[@]}"} "$WORK" 2>"$PANDOC_LOG"; then
  PANDOC_RC=0
else
  PANDOC_RC=$?
fi
cat "$PANDOC_LOG" >&2
if [[ "$PANDOC_RC" -ne 0 ]]; then
  echo "[render_pdf] pandoc failed (exit $PANDOC_RC)" >&2
  exit "$PANDOC_RC"
fi

# xelatex succeeds when the font lacks a character; the character is just not
# drawn. pandoc records each drop as a MissingCharacter entry in its JSON log
# (and, unless --quiet, as a "Missing character" warning on stderr). If the log
# cannot be read, the check falls back to stderr and says so.
GLYPH_SRC="$RENDER_TMP/missing.txt"
if ! python3 - "$JSON_LOG" > "$GLYPH_SRC" <<'PY'
import json
import sys

try:
    with open(sys.argv[1], encoding="utf-8") as fh:
        entries = json.load(fh)
except (OSError, ValueError):
    sys.exit(1)
if not isinstance(entries, list):
    sys.exit(1)
for entry in entries:
    if isinstance(entry, dict) and entry.get("type") == "MissingCharacter":
        print("Missing character: " + str(entry.get("message", "")))
PY
then
  echo "[render_pdf] WARN: could not read pandoc's JSON log ($JSON_LOG); the missing-glyph check falls back to stderr, which --quiet empties" >&2
  grep 'Missing character' "$PANDOC_LOG" > "$GLYPH_SRC" || true
fi
MISSING="$(grep -c 'Missing character' "$GLYPH_SRC" || true)"
if [[ "$MISSING" -gt 0 ]]; then
  echo "[render_pdf] $MISSING character(s) not drawn — the font has no glyph for:" >&2
  python3 - "$GLYPH_SRC" >&2 <<'PY'
import re
import sys
from collections import Counter, OrderedDict

seen = OrderedDict()
counts = Counter()
pat = re.compile(r"Missing character: There is no (.+?) ((?:\(U\+[0-9A-Fa-f]+\) ?)*)in font ([^/!]+)")
with open(sys.argv[1], encoding="utf-8", errors="replace") as fh:
    for line in fh:
        m = pat.search(line)
        if not m:
            continue
        glyph, codes, font = m.group(1), m.group(2), m.group(3).strip()
        code = re.search(r"U\+[0-9A-Fa-f]+", codes)
        key = (glyph, code.group(0) if code else "U+%04X" % ord(glyph[0]))
        counts[key] += 1
        seen.setdefault(key, set()).add(font)
for (glyph, code), fonts in seen.items():
    print(f"  {code} {glyph}  x{counts[(glyph, code)]}  ({', '.join(sorted(fonts))})")
PY
  if [[ "$ALLOW_MISSING_GLYPHS" == "1" ]]; then
    echo "[render_pdf] ok (--allow-missing-glyphs: those characters are absent from the PDF) → $OUTPUT" >&2
    exit 0
  fi
  echo "[render_pdf] FAIL: the PDF was written but is missing those characters: $OUTPUT" >&2
  echo "[render_pdf] Use a mainfont/CJKmainfont that has them (scripts/scan_glyph_coverage.py --font), replace them, or pass --allow-missing-glyphs." >&2
  exit 4
fi
echo "[render_pdf] ok → $OUTPUT" >&2
