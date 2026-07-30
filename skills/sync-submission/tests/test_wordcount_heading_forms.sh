#!/usr/bin/env bash
# Regression test: the same manuscript must measure the same length in either heading syntax.
#
# Markdown has two heading forms and pandoc accepts both. `check_wordcount_cap` recognised only ATX,
# and only to depth 3. So under setext —
#
#     References
#     ==========
#
# — the heading was never seen, `in_skip` never turned on, and the ENTIRE References section was
# counted as body prose. Byte-identical prose measured 480 words as ATX and 1,002 as setext. This
# gate blocks a submission against a journal's word cap, so the syntax an author happened to use
# decided whether their paper was over the limit.
#
# `#### References` had the same problem for a different reason: `#{1,3}` stops at three.
set -u

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
W="$REPO_ROOT/skills/sync-submission/scripts/check_wordcount_cap.py"
WORK="$(mktemp -d -t wordcount_heading_test.XXXXXX)"
trap 'rm -rf "$WORK"' EXIT

pass=0
fail=0
ck() {
  local label="$1" expected="$2" actual="$3"
  if [ "$expected" = "$actual" ]; then
    printf '  PASS  %-50s %s\n' "$label" "$actual"
    pass=$((pass + 1))
  else
    printf '  FAIL  %-50s expected=%s actual=%s\n' "$label" "$expected" "$actual"
    fail=$((fail + 1))
  fi
}

words_of() {  # words_of <file> -> body word count as a bare integer
  python3 "$W" --manuscript "$WORK/$1" --limit 100000 2>/dev/null \
    | sed -n 's/.*body words (md)  *: *//p' | tr -d ', '
}

python3 - "$WORK" <<'PY'
import pathlib, sys
w = pathlib.Path(sys.argv[1])
body = "The intervention reduced mortality in the enrolled cohort. " * 60
refs = "Smith J, Doe A. A representative reference title with several words. Journal. 2023. " * 40
fm = "---\ntitle: Example\n---\n\n"

(w / "atx.md").write_text(f"{fm}## Introduction\n\n{body}\n\n## References\n\n{refs}\n")
(w / "setext.md").write_text(
    f"{fm}Introduction\n============\n\n{body}\n\nReferences\n==========\n\n{refs}\n")
(w / "setext_dash.md").write_text(
    f"{fm}Introduction\n------------\n\n{body}\n\nReferences\n----------\n\n{refs}\n")
(w / "deep.md").write_text(f"{fm}## Introduction\n\n{body}\n\n#### References\n\n{refs}\n")
# A horizontal rule is NOT a setext underline: it follows a blank line.
(w / "hrule.md").write_text(f"{fm}## Introduction\n\n{body}\n\n---\n\n{body}\n")
PY

atx="$(words_of atx.md)"

echo "==== the same prose measures the same length in either syntax ===="
ck "ATX baseline is a real number"        yes "$([ "${atx:-0}" -gt 100 ] && echo yes || echo no)"
ck "setext '=' equals ATX"                "$atx" "$(words_of setext.md)"
ck "setext '-' equals ATX"                "$atx" "$(words_of setext_dash.md)"
ck "#### References is skipped too"       "$atx" "$(words_of deep.md)"

echo "==== NEGATIVE CONTROLS ===="
# A horizontal rule after a blank line must not turn the paragraph above it into a heading; both
# paragraphs stay in the body, so the count is twice the Introduction.
hr="$(words_of hrule.md)"
ck "horizontal rule is not a heading"     yes \
   "$([ "$hr" -gt "$atx" ] && echo yes || echo no)"
# The References text must genuinely be excluded, not merely equal by coincidence: a manuscript with
# no References section at all must match too.
python3 - "$WORK" <<'PY'
import pathlib, sys
w = pathlib.Path(sys.argv[1])
body = "The intervention reduced mortality in the enrolled cohort. " * 60
(w / "norefs.md").write_text(f"---\ntitle: Example\n---\n\n## Introduction\n\n{body}\n")
PY
ck "no-References manuscript matches"     "$atx" "$(words_of norefs.md)"

echo
echo "  passed=$pass failed=$fail"
[ "$fail" -eq 0 ] || exit 1
echo "OK: the heading syntax an author chose no longer decides whether they are over the cap."
