#!/usr/bin/env bash
# render_pdf.sh — pandoc + xelatex wrapper for Korean academic markdown.
#
# Usage:
#   render_pdf.sh -i input.md [-o output.pdf] [--infer-colwidths]
#                 [--font "Apple SD Gothic Neo"] [--cjk-font "Apple SD Gothic Neo"]
#                 [-- <extra pandoc args>]
#
# Defaults:
#   - macOS: mainfont/CJKmainfont = "Apple SD Gothic Neo"
#   - Linux: mainfont = "Noto Serif CJK KR", CJKmainfont = "Noto Sans CJK KR"
#   - Output path = <input>.pdf
#   - geometry = margin=0.85in, fontsize = 11pt (override via frontmatter)
#
# The frontmatter in input.md takes precedence over CLI/auto-detected defaults.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

INPUT=""
OUTPUT=""
INFER_COLWIDTHS=0
MAINFONT=""
CJKFONT=""
EXTRA=()

usage() {
  cat >&2 <<EOF
Usage: $(basename "$0") -i <input.md> [-o <output.pdf>] [options] [-- <pandoc args>]

Options:
  -i  Input markdown
  -o  Output PDF (default: <input>.pdf)
  --infer-colwidths     Run scripts/infer_colwidths.py on a temp copy first
  --font NAME           mainfont (default: OS-detected)
  --cjk-font NAME       CJKmainfont (default: OS-detected)
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
  if [[ "$(uname)" == "Darwin" ]]; then
    : "${MAINFONT:=Apple SD Gothic Neo}"
    : "${CJKFONT:=Apple SD Gothic Neo}"
  else
    : "${MAINFONT:=Noto Serif CJK KR}"
    : "${CJKFONT:=Noto Sans CJK KR}"
  fi
fi

command -v pandoc >/dev/null || { echo "ERROR: pandoc not installed" >&2; exit 3; }
command -v xelatex >/dev/null || { echo "ERROR: xelatex not installed (install mactex / texlive-xetex)" >&2; exit 3; }

WORK="$INPUT"
TMPDIR=""
if [[ "$INFER_COLWIDTHS" == "1" ]]; then
  TMPDIR="$(mktemp -d)"
  trap 'rm -rf "$TMPDIR"' EXIT
  WORK="$TMPDIR/$(basename "$INPUT")"
  python3 "$SCRIPT_DIR/infer_colwidths.py" "$INPUT" --out "$WORK"
fi

ARGS=(
  --pdf-engine=xelatex
  -V "mainfont=${MAINFONT}"
  -V "CJKmainfont=${CJKFONT}"
  -V "geometry:margin=0.85in"
  -V "fontsize=11pt"
  -V "linestretch=1.25"
  -V "colorlinks=true"
  -o "$OUTPUT"
)

echo "[render_pdf] in=$INPUT out=$OUTPUT mainfont='$MAINFONT' CJK='$CJKFONT' infer=$INFER_COLWIDTHS" >&2
pandoc "${ARGS[@]}" ${EXTRA[@]+"${EXTRA[@]}"} "$WORK"
echo "[render_pdf] ok → $OUTPUT" >&2
