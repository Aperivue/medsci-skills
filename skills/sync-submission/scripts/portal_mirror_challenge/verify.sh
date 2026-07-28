#!/usr/bin/env bash
# Deterministic verifier for the portal-mirror challenge card.
#
# The contract this gate enforces is printed on the submission form itself. SNAPP says, at
# Author Contributions, Competing Interests, Data Availability and Acknowledgements:
#
#     "This replaces any statement written within the manuscript and is the one that we will
#      publish."
#
# So the manuscript is the copy reviewers read and the portal box is the copy the world gets,
# and a sentence that never reaches the box is never published. Nothing warns you, because
# nothing is wrong with either document on its own.
#
# The positive fixture reproduces the two real near-losses:
#   an Acknowledgements box pasted without "The funder had no role in study design…"
#     -> PORTAL_FIELD_NOT_MIRRORED
#   a title-page dagger footnote naming two co-first authors, and an Author Contributions box
#     that does not repeat it. There is no equal-contribution checkbox anywhere in the portal.
#     -> EQUAL_CONTRIBUTION_NOT_IN_PORTAL
#   plus a replacing field with no paste artifact at all
#     -> PORTAL_FIELD_MISSING
#
# The negatives are what decide whether the gate is usable:
#   a complete paste                            -> silent
#   a RE-FLOWED paste (same sentences, rewrapped, blank lines moved) -> silent. This is the
#     one that matters: authors re-wrap when they paste, and a substring test would report
#     text the author DID paste as dropped.
#   a journal whose portal contract was never recorded -> asserts nothing, exits 2. The gate
#     may not invent a contract it was not told.
#   --emit -> check must come out CLEAN, which is the whole point: the author never
#     hand-composes the box, and hand-composition is how both sentences above were lost.
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
DET="$HERE/../check_portal_mirror.py"
FIX="$HERE/fixture"
PROFILE="$HERE/../../../write-paper/references/journal_profiles/npj_Digital_Medicine.md"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

pass=0; fail=0
ck() { if [ "$2" = "$3" ]; then printf '  PASS  %-56s exit=%s\n' "$1" "$3"; pass=$((pass+1));
       else printf '  FAIL  %-56s want=%s got=%s\n' "$1" "$2" "$3"; fail=$((fail+1)); fi; }
has() { if echo "$2" | grep -q "$3"; then ck "$1" 0 0; else ck "$1" 0 1; fi; }
hasnt() { if echo "$2" | grep -q "$3"; then ck "$1" 0 1; else ck "$1" 0 0; fi; }
run() { python3 "$DET" --manuscript "$FIX/manuscript.md" --profile "$PROFILE" "$@" 2>&1; }

echo "== the journal contract is read from the profile, not guessed =="
OUT="$(run --portal-dir "$FIX/portal_complete")"
has "all four replacing fields are found" "$OUT" "4 replacing field(s)"

echo "== positive: declarations that never reach the box that replaces them =="
python3 "$DET" --manuscript "$FIX/manuscript.md" --profile "$PROFILE" \
  --portal-dir "$FIX/portal_dropped" --strict >/dev/null 2>&1
ck "a dropped declaration -> --strict fails" 1 "$?"
# ...and WITHOUT --strict too. preflight_gate reads this exit code and never passes --strict,
# so a --strict-gated exit reports a dropped declaration as a clean check. It did, once.
python3 "$DET" --manuscript "$FIX/manuscript.md" --profile "$PROFILE" \
  --portal-dir "$FIX/portal_dropped" --quiet >/dev/null 2>&1
ck "and fails WITHOUT --strict (preflight reads this)" 1 "$?"
OUT="$(run --portal-dir "$FIX/portal_dropped")"
has "the funder-role sentence is named"    "$OUT" "PORTAL_FIELD_NOT_MIRRORED"
has "the missing field is named"           "$OUT" "PORTAL_FIELD_MISSING"
has "co-first authorship is named"         "$OUT" "EQUAL_CONTRIBUTION_NOT_IN_PORTAL"
# the whole sentence, not a clause: a hard-wrapped sentence must not be reported in halves
has "the sentence is quoted intact"        "$OUT" "decision to submit"
hasnt "and is reported once, not per line" "$OUT" "\"The funder had no role in study\"\."

echo "== negative: a complete paste, and a RE-FLOWED one =="
python3 "$DET" --manuscript "$FIX/manuscript.md" --profile "$PROFILE" \
  --portal-dir "$FIX/portal_complete" --strict >/dev/null 2>&1
ck "a complete paste -> silent" 0 "$?"
python3 "$DET" --manuscript "$FIX/manuscript.md" --profile "$PROFILE" \
  --portal-dir "$FIX/portal_reflowed" --strict >/dev/null 2>&1
ck "a re-flowed paste -> silent (the FP that would kill it)" 0 "$?"
OUT="$(run --portal-dir "$FIX/portal_reflowed")"
has   "and it really did examine them"     "$OUT" "checked 10 sentence"
hasnt "with no invented loss"              "$OUT" "NOT_MIRRORED"

echo "== author initials are not sentence ends =="
# Author Contributions is the one section guaranteed to be written in initials. If "J.D." ends
# a sentence, the section splits into fragments too short to judge and a real omission is
# reported against a clause with no subject.
OUT="$(python3 - "$HERE/.." "$FIX/manuscript.md" <<'PY_EOF'
import sys, pathlib
sys.path.insert(0, sys.argv[1])
from check_portal_mirror import find_section, statements
md = pathlib.Path(sys.argv[2]).read_text(encoding="utf-8")
for s in statements(find_section(md, "author_contributions")):
    print(s)
PY_EOF
)"
ck "the contributions section is 3 sentences" 3 "$(echo "$OUT" | grep -c .)"
has "and initials stay with their clause"    "$OUT" "^J.D. and A.R. designed"

echo "== a journal with no recorded portal contract asserts nothing =="
cat > "$TMP/no_mechanics.md" <<'EOF'
# Journal of Synthetic Submissions

## Special Notes

- Nothing about the portal has been recorded yet.
EOF
python3 "$DET" --manuscript "$FIX/manuscript.md" --profile "$TMP/no_mechanics.md" \
  --portal-dir "$FIX/portal_dropped" --strict >/dev/null 2>&1
ck "no Portal Mechanics block -> skipped, not invented" 2 "$?"

echo "== --emit produces a scaffold that passes its own gate =="
python3 "$DET" --manuscript "$FIX/manuscript.md" --profile "$PROFILE" --emit "$TMP/emitted" >/dev/null 2>&1
ck "--emit succeeds" 0 "$?"
OUT="$(cat "$TMP/emitted/author_contributions.txt")"
has "the title-page equal-contribution line is lifted in" "$OUT" "contributed equally"
python3 "$DET" --manuscript "$FIX/manuscript.md" --profile "$PROFILE" \
  --portal-dir "$TMP/emitted" --strict >/dev/null 2>&1
ck "emit -> check round-trips clean" 0 "$?"
python3 "$DET" --manuscript "$FIX/manuscript.md" --profile "$PROFILE" --emit "$TMP/emitted" 2>&1 \
  | grep -q "left alone" && ck "--emit will not clobber an edited file" 0 0 \
  || ck "--emit will not clobber an edited file" 0 1

echo "== the artifact names its own author =="
python3 "$DET" --manuscript "$FIX/manuscript.md" --profile "$PROFILE" \
  --portal-dir "$FIX/portal_dropped" --out "$TMP/report.json" >/dev/null 2>&1
has "qc JSON carries the detector key" "$(cat "$TMP/report.json")" '"detector": "check_portal_mirror"'

echo
printf 'portal-mirror challenge: %d passed, %d failed\n' "$pass" "$fail"
[ "$fail" -eq 0 ] || exit 1
