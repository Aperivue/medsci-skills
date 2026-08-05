#!/usr/bin/env bash
# Regression test: --only must narrow the WORK without narrowing the honesty of the verdict.
#
# The flag exists for speed — the two validator self-tests each re-ran the whole scan, so CI paid
# for it three times per push. But a scope flag is the classic way to manufacture a meaningless
# green: run less, print the same words, and every downstream reader concludes the same thing from
# a weaker fact. #435 was already that shape once, from the other direction — a `find` glob that
# matched zero files while the validator printed PASS for every rule.
#
# So this test asserts both halves:
#   the flag WORKS      — one skill is scanned, the repo-wide gates do not run, it is fast
#   the flag is HONEST  — the scoped verdict is a different string, the scope is announced, and a
#                         name matching nothing is an error rather than an empty loop
#
# The last one is the load-bearing case. `--only typo` running zero skills and exiting 0 would
# reproduce #435 exactly, inside the fix for its cost.
set -u

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
V="$REPO_ROOT/scripts/validate_skills.sh"

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

# A real skill, chosen from disk rather than hardcoded so this does not rot when skills are renamed.
TARGET="$(basename "$(find "$REPO_ROOT/skills" -mindepth 2 -maxdepth 2 -name SKILL.md | sort | head -1 | xargs dirname)")"
OTHER="$(basename "$(find "$REPO_ROOT/skills" -mindepth 2 -maxdepth 2 -name SKILL.md | sort | tail -1 | xargs dirname)")"
[ -n "$TARGET" ] && [ "$TARGET" != "$OTHER" ] || { echo "ENV-ERR: need two skills on disk" >&2; exit 2; }

OUT="$(bash "$V" --only "$TARGET" 2>&1)"
rc=$?

echo "==== the flag works ===="
ck "scoped run exit code"                    "0"  "$rc"
printf '%s\n' "$OUT" | grep -q "^\[$TARGET\]"
ck "the named skill was scanned"             "0"  "$?"
printf '%s\n' "$OUT" | grep -q "^\[$OTHER\]"
ck "another skill was NOT scanned"           "1"  "$?"
ck "exactly one skill counted"               "1"  "$(printf '%s\n' "$OUT" | sed -n 's/^ Skills checked: \([0-9]*\)$/\1/p')"

echo "==== the repo-wide gates did not run ===="
# Each of the three prints a distinctive line; their absence is what makes the run cheap, and is
# exactly what the verdict must therefore not paper over.
#
# Match a line the scan emits only when it RUNS, not its name. The first draft of this assertion
# grepped for "Public-surface PII scan" and failed — against correct code — because the scoped
# banner announces that very phrase in its list of what it is skipping. A test that cannot tell
# "did the thing" from "named the thing" is measuring the wrong noun.
printf '%s\n' "$OUT" | grep -qE 'Scanned [0-9]+ tracked non-skills text files'
ck "public-surface scan skipped"             "1"  "$?"
printf '%s\n' "$OUT" | grep -qi 'vendored\|domain probe'
ck "vendoring-drift gate skipped"            "1"  "$?"
printf '%s\n' "$OUT" | grep -qi 'reachable from a SKILL.md'
ck "script-reachability gate skipped"        "1"  "$?"

echo "==== the verdict is honest about its scope ===="
printf '%s\n' "$OUT" | grep -q 'ALL CHECKS PASSED'
ck "does NOT print the full-run verdict"     "1"  "$?"
printf '%s\n' "$OUT" | grep -q 'SCOPED PASS'
ck "prints a scoped verdict instead"         "0"  "$?"
printf '%s\n' "$OUT" | grep -qi 'SCOPED to'
ck "announces the scope in the banner"       "0"  "$?"
printf '%s\n' "$OUT" | grep -qi 'repo-wide gates NOT run'
ck "names what it did not do"                "0"  "$?"

echo "==== a name matching nothing is an error, not an empty pass ===="
bad_out="$(bash "$V" --only definitely-not-a-skill 2>&1)"; bad_rc=$?
ck "unknown skill exit code"                 "2"  "$bad_rc"
printf '%s\n' "$bad_out" | grep -q 'ALL CHECKS PASSED\|SCOPED PASS'
ck "unknown skill prints no pass verdict"    "1"  "$?"
bash "$V" --only >/dev/null 2>&1
ck "--only with no argument exits 2"         "2"  "$?"
bash "$V" --bogus-flag >/dev/null 2>&1
ck "an unknown flag exits 2"                 "2"  "$?"

echo "==== the unscoped run is still what CI actually runs ===="
# This test deliberately does NOT invoke the full validator. That would take ~3 minutes and put
# back the third full scan this whole change exists to remove — a regression test that reproduces
# the cost it is testing the fix for is not a regression test, it is the bug with an assertion on
# top. CI already runs the unscoped validator as its own step, and that step failing IS the
# assertion that the full path still works.
#
# What is checkable here, and cheap, is that the step exists — i.e. that the coverage claim above
# is true of the workflow rather than merely believed. If someone ever "optimises" CI by adding
# --only to that step, the full scan silently stops happening and this fails.
WF="$REPO_ROOT/.github/workflows/validate.yml"
grep -qE 'bash scripts/validate_skills\.sh[[:space:]]*$' "$WF"
ck "validate.yml runs the validator unscoped"  "0"  "$?"
grep -qE 'scripts/validate_skills\.sh.*--only' "$WF"
ck "no CI step scopes the release gate"        "1"  "$?"

echo
echo "  passed=$pass failed=$fail"
[ "$fail" -eq 0 ] || exit 1
echo "OK: --only narrows the work, says so, and refuses to narrow itself to nothing."
