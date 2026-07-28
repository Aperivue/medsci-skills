#!/usr/bin/env bash
# Self-test for scripts/check_detector_crossfire.py -- the gate that makes a fixture which is clean
# for ONE detector be clean for ALL of them.
#
# The live repo must pass. But a gate that only ever proves "clean input stays clean" proves
# nothing: it would pass just as happily if it silently exercised zero pairs, or if it were blind to
# the very bug it exists to prevent. So the real work here is the REGRESSION -- we put the actual
# shipped bug back and require the gate to go red.
#
# THE BUG (it was real, in PR #333/#334):
#     check_slide_tells treated a text block as an "arrow label" only if it was <= 18 pt.
#     check_deck_budget demanded >= 20 pt so the back row could read it.
# A legible 20-pt arrow label therefore satisfied the budget check and was INVISIBLE to the arrow
# check, so a well-made slide was reported as having unlabelled arrows. Neither detector was wrong
# alone. One detector's advisory threshold had become another's definition of a category.
#
# Each sub-test below builds a SEALED tree (a temp copy of the skills + demos it needs, with the
# gate copied in beside them, so the gate's REPO root resolves to the temp tree). Nothing here
# mutates the real repo.
set -u

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
GATE="$REPO_ROOT/scripts/check_detector_crossfire.py"

pass=0
fail=0
ck() {
  local label="$1" expected="$2" actual="$3"
  if [ "$expected" = "$actual" ]; then
    printf '  PASS  %-58s exit=%s\n' "$label" "$actual"
    pass=$((pass + 1))
  else
    printf '  FAIL  %-58s expected=%s actual=%s\n' "$label" "$expected" "$actual"
    fail=$((fail + 1))
  fi
}

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

# Build a sealed tree containing the gate + the named skills + the demo manuscripts.
# present-paper is always included: it carries both deck detectors AND the two challenge cards that
# BUILD the clean decks, which the gate requires.
seal() {
  local tree="$1"; shift
  mkdir -p "$tree/scripts" "$tree/skills"
  cp "$GATE" "$tree/scripts/"
  cp -R "$REPO_ROOT/skills/present-paper" "$tree/skills/"
  for s in "$@"; do cp -R "$REPO_ROOT/skills/$s" "$tree/skills/"; done
  # only the manuscripts -- the rest of demo/ is 6 MB the gate never reads
  for d in 01_wisconsin_bc 02_metafor_bcg 03_nhanes_obesity; do
    mkdir -p "$tree/demo/$d/manuscript"
    cp "$REPO_ROOT/demo/$d/manuscript/manuscript.md" "$tree/demo/$d/manuscript/"
  done
}

echo "== 1. the live repo: no detector may fire on our own picture of good work =="
out="$(python3 "$GATE" 2>&1)"; rc=$?
ck "live repo: every detector silent on every clean fixture" 0 "$rc"
[ "$rc" -ne 0 ] && echo "$out"

# The count guards against the worst outcome: a green gate that ran nothing.
pairs="$(printf '%s\n' "$out" | sed -n 's/^ *pairs run: \([0-9]*\)$/\1/p')"
if [ -n "${pairs:-}" ] && [ "$pairs" -gt 0 ] 2>/dev/null; then
  printf '  PASS  %-58s pairs=%s\n' "live repo: actually exercised something" "$pairs"
  pass=$((pass + 1))
else
  printf '  FAIL  %-58s pairs=%s\n' "live repo: ran ZERO pairs (silent no-op)" "${pairs:-none}"
  fail=$((fail + 1))
fi

# Coverage must be declared, not implied. A skip nobody can see is a hole nobody can audit.
if printf '%s\n' "$out" | grep -q '^  SKIPPED: '; then
  printf '  PASS  %-58s\n' "skips are named out loud (honest coverage)"
  pass=$((pass + 1))
else
  printf '  FAIL  %-58s\n' "no SKIPPED lines -- coverage is not being declared"
  fail=$((fail + 1))
fi

echo
echo "== 2. REGRESSION: restore the real bug and require the gate to CATCH it =="
# This is the whole point of the file. If this sub-test cannot be made to fail, the gate is
# decoration.
BUG="$WORK/bug"; seal "$BUG"
TELLS="$BUG/skills/present-paper/scripts/check_slide_tells.py"

# Sanity: the sealed tree is green BEFORE we break it. Without this, a red result below could just
# mean "the sealed tree was broken all along" and would prove nothing about the patch.
python3 "$BUG/scripts/check_detector_crossfire.py" > /dev/null 2>&1
ck "sealed tree, detector intact: green" 0 "$?"

# Put the contradiction back: a label is a label only if it is <= 18 pt -- while check_deck_budget
# goes on demanding >= 20 pt in the same room, on the same deck.
python3 - "$TELLS" <<'PY'
import pathlib, sys
p = pathlib.Path(sys.argv[1]); s = p.read_text()
old = "    labels = [s for s in texts if head_pt == 0.0 or s.max_pt < head_pt]"
new = "    labels = [s for s in texts if s.max_pt <= 18]  # the shipped bug, restored"
assert old in s, "regression anchor not found -- the detector was refactored; re-point this patch"
p.write_text(s.replace(old, new))
PY
ck "regression patch applied to the sealed copy" 0 "$?"

out="$(python3 "$BUG/scripts/check_detector_crossfire.py" 2>&1)"; rc=$?
ck "gate FAILS once the <=18pt / >=20pt contradiction is back" 1 "$rc"

if printf '%s\n' "$out" | grep -q 'ARROW_NO_SEMANTICS'; then
  printf '  PASS  %-58s\n' "...and it names the arrow verdict on a well-made deck"
  pass=$((pass + 1))
else
  printf '  FAIL  %-58s\n' "...but ARROW_NO_SEMANTICS was never reported"
  fail=$((fail + 1))
  echo "$out"
fi

echo
echo "== 3. the OTHER jaw: the pair nothing in this repo runs today =="
# Suppose someone had "fixed" the arrow bug the lazy way -- by shrinking the label to 16 pt so the
# <=18 test could see it. slide_tells would go quiet. check_deck_budget would start failing that
# same deck on its 20-pt floor -- and NOTHING in this repo runs check_deck_budget against the
# slide-tells card's clean.pptx. That pair exists only here.
SHRINK="$WORK/shrink"; seal "$SHRINK"
MK="$SHRINK/skills/present-paper/scripts/check_slide_tells_challenge/make_fixtures.py"
python3 - "$MK" <<'PY'
import pathlib, sys
p = pathlib.Path(sys.argv[1]); s = p.read_text()
old = 'textbox(s, "seeds along", x0 + 0.05, 2.95, 1.6, 0.45, 20)'
new = 'textbox(s, "seeds along", x0 + 0.05, 2.95, 1.6, 0.45, 16)'
assert old in s, "shrink anchor not found"
p.write_text(s.replace(old, new))
PY
out="$(python3 "$SHRINK/scripts/check_detector_crossfire.py" 2>&1)"; rc=$?
ck "a 16pt 'fix' to the arrow label is caught by the budget floor" 1 "$rc"
if printf '%s\n' "$out" | grep -q 'TYPE_TOO_SMALL'; then
  printf '  PASS  %-58s\n' "...via check_deck_budget x clean.pptx (the uncovered pair)"
  pass=$((pass + 1))
else
  printf '  FAIL  %-58s\n' "...but TYPE_TOO_SMALL never fired"
  fail=$((fail + 1))
fi

echo
echo "== 4. the other half of the verdict: a DEFECTIVE DEMO must also go red =="
# When a pair fires, one of two things is true -- the detector over-fires, or the demo is broken.
# The gate must be able to say the second one too, or it is only half a test.
BADDEMO="$WORK/baddemo"; seal "$BADDEMO" sync-submission
python3 - "$BADDEMO/demo/02_metafor_bcg/manuscript/manuscript.md" <<'PY'
import pathlib, sys
p = pathlib.Path(sys.argv[1]); lines = p.read_text().splitlines(keepends=True)
out, drop = [], False
for ln in lines:
    if ln.startswith("## Data Availability"):
        drop = True; continue
    if drop and ln.startswith("## "):
        drop = False
    if not drop:
        out.append(ln)
p.write_text("".join(out))
PY
out="$(python3 "$BADDEMO/scripts/check_detector_crossfire.py" 2>&1)"; rc=$?
ck "a demo stripped of its Data Availability statement fails" 1 "$rc"
if printf '%s\n' "$out" | grep -q 'check_disclosure_availability'; then
  printf '  PASS  %-58s\n' "...and the firing detector is named"
  pass=$((pass + 1))
else
  printf '  FAIL  %-58s\n' "...but check_disclosure_availability was not named"
  fail=$((fail + 1))
fi

echo
echo "== 5. a detector that WRITES INTO a fixture voids the run =="
# The reason this guard exists: a scanner that guessed at output flags once overwrote 31 fixtures.
# A gate whose own fixtures can be silently rewritten underneath it is not measuring anything.
EVIL="$WORK/evil"; seal "$EVIL"
mkdir -p "$EVIL/skills/evil/scripts"
cat > "$EVIL/skills/evil/scripts/check_evil.py" <<'PY'
#!/usr/bin/env python3
"""A detector that scribbles on the fixture it was asked to read."""
import argparse
ap = argparse.ArgumentParser()
ap.add_argument("--manuscript", required=True)
a = ap.parse_args()
open(a.manuscript, "a", encoding="utf-8").write("\nscribble\n")
print("OK")
PY
out="$(python3 "$EVIL/scripts/check_detector_crossfire.py" 2>&1)"; rc=$?
ck "a fixture-clobbering detector fails the run" 1 "$rc"
if printf '%s\n' "$out" | grep -q 'WROTE INTO A FIXTURE'; then
  printf '  PASS  %-58s\n' "...and the run is declared void, not merely 'firing'"
  pass=$((pass + 1))
else
  printf '  FAIL  %-58s\n' "...but the fixture-write guard stayed silent"
  fail=$((fail + 1))
fi

echo
echo "== 6. zero pairs is a FAILURE, not a pass =="
# A test that silently exercises nothing is worse than no test: it is a green light over a hole.
NOPAIRS="$WORK/nopairs"; seal "$NOPAIRS" model-card
# Remove both deck detectors but KEEP the challenge cards, so the decks still build and the only
# detector left (check_model_card_complete) belongs to neither family. Nothing can pair.
rm -f "$NOPAIRS/skills/present-paper/scripts/check_slide_tells.py" \
      "$NOPAIRS/skills/present-paper/scripts/check_deck_budget.py"
out="$(python3 "$NOPAIRS/scripts/check_detector_crossfire.py" 2>&1)"; rc=$?
ck "a run with no runnable pairs fails" 1 "$rc"
if printf '%s\n' "$out" | grep -q 'zero (detector x fixture) pairs'; then
  printf '  PASS  %-58s\n' "...and says so, rather than reporting a hollow OK"
  pass=$((pass + 1))
else
  printf '  FAIL  %-58s\n' "...but the zero-pairs guard stayed silent"
  fail=$((fail + 1))
fi

echo
echo "----"
echo "detector-crossfire self-test: $pass passed, $fail failed"
[ "$fail" -eq 0 ] || exit 1
