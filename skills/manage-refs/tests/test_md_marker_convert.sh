#!/usr/bin/env bash
# Regression test: md_marker_convert.py reports every [N] marker it leaves, expands ranges, and
# picks its pattern by direction.
#
# Three defects, each of which let a partially converted manuscript leave with exit 0 and no word:
#
# 1. A number with no mapping was dropped before it was recorded (it also fell outside the default
#    active set), so "[5]" with a four-entry map stayed "[5]" with no WARNING, contrary to the
#    docstring and SKILL.md ("reported on stderr").
# 2. A range ("[1-3]", "[1–3]") did not match the marker pattern at all: not converted, not counted,
#    not reported.
# 3. The pattern was guessed from the content ("[@" present -> key pattern), so re-running --to-keys
#    on a partially converted file fed "@KEY" to int() and crashed with a traceback.
#
# Markers left for a number outside an explicit --active-ns are the staged workflow working as
# asked: reported as a NOTE, never a failure (negative control).
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONV="$HERE/../scripts/md_marker_convert.py"
[[ -f "$CONV" ]] || { echo "ENV-ERR: md_marker_convert.py missing" >&2; exit 2; }
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

pass=0
fail=0
ck() {
  local label="$1" expected="$2" actual="$3"
  if [ "$expected" = "$actual" ]; then
    printf '  PASS  %-58s %s\n' "$label" "$actual"
    pass=$((pass + 1))
  else
    printf '  FAIL  %-58s expected=%s actual=%s\n' "$label" "$expected" "$actual"
    fail=$((fail + 1))
  fi
}
conv() {  # conv <in> <out> [flags...] -> exit code; stderr in $WORK/<out>.err
  local in="$1" out="$2"; shift 2
  python3 "$CONV" --input "$WORK/$in" --output "$WORK/$out" --map "$WORK/map.json" "$@" \
    2> "$WORK/$out.err"
  echo $?
}

echo '{"1":"AAA","2":"BBB","3":"CCC","4":"DDD"}' > "$WORK/map.json"
printf 'Prior studies [1-3] and [4] agree; see also [5].\n' > "$WORK/unmapped.md"
printf 'Earlier work [1\xe2\x80\x933] and [2, 4] agree.\n' > "$WORK/ranges.md"
printf 'Prior studies [1] and [2-4] agree.\n' > "$WORK/clean.md"
printf 'A backwards range [3-1] here.\n' > "$WORK/backwards.md"

echo "==== 1. an unmapped number is reported and fails ===="
ck "[5] with a 4-entry map: exit 1"            1 "$(conv unmapped.md unmapped_out.md --to-keys)"
ck "  [5] named as UNMAPPED"                   1 "$(grep -c 'UNMAPPED.*\[5\]' "$WORK/unmapped_out.md.err")"
ck "  the rest is still converted"             "Prior studies [@AAA, @BBB, @CCC] and [@DDD] agree; see also [5]." \
   "$(cat "$WORK/unmapped_out.md")"
ck "  --allow-partial accepts it: exit 0"       0 "$(conv unmapped.md unmapped_ok.md --to-keys --allow-partial)"
ck "  ... and still reports [5]"               1 "$(grep -c 'UNMAPPED.*\[5\]' "$WORK/unmapped_ok.md.err")"

echo "==== 2. ranges are expanded ===="
ck "[1–3] (en dash) and [2, 4]: exit 0"        0 "$(conv ranges.md ranges_out.md --to-keys)"
ck "  converted"                               "Earlier work [@AAA, @BBB, @CCC] and [@BBB, @DDD] agree." \
   "$(cat "$WORK/ranges_out.md")"
ck "a backwards range [3-1]: exit 1"           1 "$(conv backwards.md backwards_out.md --to-keys)"
ck "  named as MALFORMED"                      1 "$(grep -c 'MALFORMED.*\[3-1\]' "$WORK/backwards_out.md.err")"

echo "==== 3. re-running --to-keys on partial output does not crash ===="
ck "re-run on partially converted file: exit 1" 1 "$(conv unmapped_out.md rerun.md --to-keys)"
ck "  no traceback"                            0 "$(grep -c 'Traceback' "$WORK/rerun.md.err")"
ck "  [5] still reported"                      1 "$(grep -c 'UNMAPPED.*\[5\]' "$WORK/rerun.md.err")"
ck "  converted keys untouched"                "Prior studies [@AAA, @BBB, @CCC] and [@DDD] agree; see also [5]." \
   "$(cat "$WORK/rerun.md")"

echo "==== NEGATIVE CONTROLS ===="
ck "a fully mapped manuscript: exit 0"         0 "$(conv clean.md clean_out.md --to-keys)"
ck "  no WARNING"                              0 "$(grep -c 'WARNING' "$WORK/clean_out.md.err")"
ck "  converted"                               "Prior studies [@AAA] and [@BBB, @CCC, @DDD] agree." \
   "$(cat "$WORK/clean_out.md")"
ck "staged --active-ns 1,4: exit 0"            0 "$(conv unmapped.md staged_out.md --to-keys --active-ns 1,4)"
ck "  outside markers reported as NOTE"        1 "$(grep -c 'NOTE.*INACTIVE' "$WORK/staged_out.md.err")"
ck "  [4] converted, [1-3] and [5] left"       "Prior studies [1-3] and [@DDD] agree; see also [5]." \
   "$(cat "$WORK/staged_out.md")"
ck "round trip --to-numbers: exit 0"           0 "$(conv clean_out.md back.md --to-numbers)"
ck "  back to numbers"                         "Prior studies [1] and [2, 3, 4] agree." \
   "$(cat "$WORK/back.md")"

echo
echo "  passed=$pass failed=$fail"
[ "$fail" -eq 0 ] || { for f in "$WORK"/*.err; do echo "--- $f"; cat "$f"; done; exit 1; }
echo "OK: every marker left behind is reported, ranges convert, and a re-run is safe."
