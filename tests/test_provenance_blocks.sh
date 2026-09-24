#!/usr/bin/env bash
# Regression for the provenance router.
#
# The positive case is the real one. On 2026-08-15 a repo-wide PII audit found a calibration file
# describing one peer review in three directions — the manuscript, a co-reviewer's report, the
# editor's decision — with no name, no email and no submission ID anywhere in it. Every literal
# gate in this repository read it as clean, correctly, because by their design it was. The fixture
# below is that block's shape. If this test stops failing against a router that has been broken,
# the router is decorative.
#
# The negatives matter at least as much. This repository's own files are full of provenance that is
# working as intended: a vendored checklist citing the DOI it was verified against, a journal
# profile carrying a fetch date. The first version of this script fired on all of them — a DOI is
# a submission ID's shape and a decimal's shape at once — and a checker that rejects the notation
# the world already uses is one people switch off.
set -u

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
S="$REPO_ROOT/scripts/check_provenance_blocks.py"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

pass=0; fail=0
ck() {
  local label="$1" expected="$2" actual="$3"
  if [ "$expected" = "$actual" ]; then
    printf '  PASS  %-58s %s\n' "$label" "$actual"; pass=$((pass + 1))
  else
    printf '  FAIL  %-58s expected=%s actual=%s\n' "$label" "$expected" "$actual"; fail=$((fail + 1))
  fi
}

n_findings() {  # file, threshold [, mode] -> count
  python3 "$S" "$1" --threshold "$2" --mode "${3:-route}" --quiet --json "$TMP/out.json" >/dev/null 2>&1
  python3 -c "import json;print(len(json.load(open('$TMP/out.json'))['findings']))"
}

# ---- POSITIVE: the shapes the audit actually found -------------------------------------------
#
# Every value below is INVENTED. That sentence is here because the first draft of this file was
# not: it reproduced a real submission ID and a real unpublished pair of C-index values — the exact
# two things the audit had just removed from the repository — inside the test written to prevent
# them. The precedent gate caught the ID. Nothing caught the numbers, because numbers are not
# literals on any blocklist, which is the whole reason this router exists.
#
# A fixture is prose someone will copy. Write it as if it ships, because it does.
cat > "$TMP/leak.md" <<'MD'
# Calibration

**Why this is here.** A review recorded, four lines apart, an audit finding and a contradicting
answer. The co-reviewer wrote ~180 words, all on priority, and the editor rejected outright, two
tiers below the recommendation.
MD
ck "confidential-review block: CI refuses it outright" 1 "$(n_findings "$TMP/leak.md" 1 block)"

# The submission ID is ASSEMBLED, never written out — the convention this repository already
# reached in skills/contribute/tests/test_contribution_safety.sh. A file whose job is to carry
# identifier-shaped strings must not carry one as a literal, or the repo's own precedent gate
# flags the test that proves the gate works. The journal code is not a real journal's.
J=ZZZZ; Y=99
printf '**Precedent:** verified 2099-01-02 against the R1 confirmation PDF for %s-D-%s-00001R1.\n' \
  "$J" "$Y" > "$TMP/leak2.md"
ck "submission ID: CI refuses it outright" 1 "$(n_findings "$TMP/leak2.md" 1 block)"

cat > "$TMP/leak3.md" <<'MD'
**Precedent failure pattern:** the composite-index C-statistic read 0.7771 in one table and
0.7779 in another, recorded 2099-01-03.
MD
ck "unpublished result: routed for judgement, NOT refused" 1 "$(n_findings "$TMP/leak3.md" 1)"

# ---- NEGATIVE: provenance that is working exactly as intended -------------------------------
cat > "$TMP/doi.md" <<'MD'
**Source:** this checklist was verified against the published statement
(*Ann Intern Med* 2026;179(4):548-555, DOI 10.7326/ANNALS-25-02104) and its Explanation &
Elaboration paper at https://doi.org/10.7326/ANNALS-25-04943. Verified 2026-06-29.
MD
ck "a public DOI is not a submission ID (world's notation)" 0 "$(n_findings "$TMP/doi.md" 1 block)"

cat > "$TMP/profile.md" <<'MD'
**Source (compact harvest):** local profile library (2026-05 fetch from the public author guide).
Key constraints: body 3,500 words, abstract 300 words, references 30.
MD
ck "month-precision profile provenance is never refused" 0 "$(n_findings "$TMP/profile.md" 1 block)"

cat > "$TMP/generic.md" <<'MD'
**Precedent failure pattern:** a single-centre retrospective cohort reported its exclusion cascade
in prose that did not close against the flow diagram. Treat as a lived failure, not hypothetical.
MD
ck "generic grounded precedent is never refused" 0 "$(n_findings "$TMP/generic.md" 1 block)"

cat > "$TMP/nonprov.md" <<'MD'
## Methods
Inter-rater agreement was substantial. The editor of this journal requires a structured abstract.
MD
ck "ordinary prose is not a provenance block" 0 "$(n_findings "$TMP/nonprov.md" 1)"

# ---- the repository's own shipped files must not be noisy -----------------------------------
own=0
while IFS= read -r f; do
  [ -f "$REPO_ROOT/$f" ] || continue
  c=$(n_findings "$REPO_ROOT/$f" 1 block)
  own=$((own + c))
done < <(git -C "$REPO_ROOT" ls-files 'skills/*/references/*.md' 'skills/*/references/**/*.md')
ck "zero REFUSALS on shipped reference prose (CI tier)" 0 "$own"

# ---- --strict is what makes it a gate --------------------------------------------------------
python3 "$S" "$TMP/leak.md" --mode block --threshold 1 --strict --quiet >/dev/null 2>&1
ck "--strict exits 1 on a refused block" 1 "$?"
python3 "$S" "$TMP/generic.md" --mode block --threshold 1 --strict --quiet >/dev/null 2>&1
ck "--strict exits 0 when nothing is refused" 0 "$?"

# The failure that made this rewrite necessary: a tier tuned for zero standing hits caught zero of
# the six real findings. The routing tier must SEE an own-submission log that carries no blocked
# token at all — if this ever returns 0, the router has gone quiet again.
cat > "$TMP/ownsub.md" <<'MD'
## Submission verification log (verified 2099-01-04, Original Article)

End-to-end submission learnings — use as the submission checklist.
MD
ck "own-submission log reaches the routing tier" 1 "$(n_findings "$TMP/ownsub.md" 1)"
ck "...and is NOT refused outright by CI"       0 "$(n_findings "$TMP/ownsub.md" 1 block)"

echo
echo "test_provenance_blocks: $pass passed, $fail failed"
[ "$fail" -eq 0 ] || exit 1
