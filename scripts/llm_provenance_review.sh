#!/usr/bin/env bash
# Ask a model the one question a pattern cannot answer: does this prose identify a real person,
# manuscript, review, or submission?
#
# WHY THIS EXISTS
#   A 2026-08-15 repo-wide PII audit found that a literal blocklist catches literals, and what
#   survives it is never a literal — it is the provenance sentence attached to a lesson. The worst
#   instance described one peer review in three directions (the manuscript, a co-reviewer's report,
#   the editor's decision) without containing a single blocked token. `check_precedent.py` read it
#   as clean because, by its own design, it was.
#
#   Judging that paragraph is a reading task. This script does the reading part; it does not replace
#   the deterministic gates, and it is not a gate itself by default.
#
# HOW IT IS SCOPED
#   `check_provenance_blocks.py` narrows the repository to the paragraphs that ground a rule in a
#   real case — 34 of 1558 skill files at last census, and typically 0-2 in a single diff. Only
#   those paragraphs are sent. The model never sees the repository, and the cost is bounded by how
#   much provenance prose a change actually adds.
#
# FAIL-OPEN, ON PURPOSE
#   Most people who touch this repository cannot run `claude`. A contributor fixing a checklist
#   typo must not be blocked by a tool they do not have, so a missing CLI is reported and exits 0.
#   CI runs the deterministic half only. `--strict` is for the maintainer's own pre-push, where the
#   provenance prose is being written and the judgement is worth blocking on.
#
# Usage:
#   scripts/llm_provenance_review.sh [--strict] [--threshold N] [PATH ...]
#   scripts/llm_provenance_review.sh --changed          # blocks in files changed vs origin/main
#   scripts/llm_provenance_review.sh --diff --strict    # every ADDED line vs origin/main (pre-push)
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ROUTER="$REPO_ROOT/scripts/check_provenance_blocks.py"
STRICT=0
THRESHOLD=1            # broader than the CI gate: the model is the judge, so feed it candidates
PATHS=()
CHANGED=0
DIFFMODE=0

while [ $# -gt 0 ]; do
  case "$1" in
    --strict)    STRICT=1; shift ;;
    --threshold) THRESHOLD="$2"; shift 2 ;;
    --changed)   CHANGED=1; shift ;;
    --diff)      DIFFMODE=1; shift ;;
    -h|--help)   sed -n '2,30p' "$0"; exit 0 ;;
    *)           PATHS+=("$1"); shift ;;
  esac
done

if [ "$CHANGED" -eq 1 ]; then
  base="$(git -C "$REPO_ROOT" merge-base HEAD origin/main 2>/dev/null || echo HEAD)"
  while IFS= read -r f; do
    [ -f "$REPO_ROOT/$f" ] && PATHS+=("$REPO_ROOT/$f")
  done < <(git -C "$REPO_ROOT" diff --name-only "$base" -- 'skills/*' 'docs/*' '*.md' 2>/dev/null)
fi

if [ "$DIFFMODE" -eq 0 ] && [ ${#PATHS[@]} -eq 0 ]; then
  echo "llm_provenance_review: nothing to review (no paths, no changed files)."
  exit 0
fi

TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT

if [ "$DIFFMODE" -eq 1 ]; then
  # The router recognises PARAGRAPHS. A table row and a bullet list are neither, and two of the six
  # findings that motivated all of this were exactly those shapes — a study-specific variable name
  # in a table cell, and a name-to-topic mapping in a list. At pre-push the diff is small, so the
  # model can read every added line and the blind spot closes.
  base="$(git -C "$REPO_ROOT" merge-base HEAD origin/main 2>/dev/null || echo HEAD~1)"
  git -C "$REPO_ROOT" diff "$base" -- 'skills/**' 'docs/**' '*.md' \
    | grep -E '^\+' | grep -vE '^\+\+\+' | sed 's/^+//' \
    | grep -vE '^\s*$' > "$TMP/added.txt" 2>/dev/null || true
  ADDED_N="$(wc -l < "$TMP/added.txt" | tr -d ' ')"
  if [ "${ADDED_N:-0}" -eq 0 ]; then
    echo "llm_provenance_review: no added prose in this push."
    exit 0
  fi
  if ! command -v claude >/dev/null 2>&1; then
    echo "llm_provenance_review: $ADDED_N added line(s) unreviewed — the \`claude\` CLI is not on PATH."
    echo "  Not a failure. Read them yourself, or install the CLI to have this checked."
    exit 0
  fi
  {
    cat <<'HDR'
You are auditing lines about to be pushed to a PUBLIC repository. For each line that would let a
reader identify a real person, manuscript, peer review, submission, institution or dataset, print:

  IDENTIFIES | <the line> | <what could be worked out>

Print nothing for lines that are fine. If no line qualifies, print exactly: CLEAN

Weigh especially, because a pattern cannot:
  - peer review is confidential in THREE directions: the manuscript, any co-reviewer's report, and
    the editor's decision. Describing any of them is disclosure even with no ID present.
  - an author's own submission history — target journal, month, article type, and above all a
    cascade after a decline elsewhere — is not public.
  - a study-specific variable name, or an unpublished result quoted precisely, fingerprints one
    dataset. This includes values inside a table row.
  - a name paired with a research topic identifies a collaborator.
  - a topic plus a venue can identify one in-flight paper even when neither alone would.
Do not flag public DOIs, citations, vendored instrument provenance, or generic study descriptors.

LINES:
HDR
    cat "$TMP/added.txt"
  } > "$TMP/prompt.txt"
  echo "llm_provenance_review: asking a model about $ADDED_N added line(s)..."
  if ! claude -p < "$TMP/prompt.txt" > "$TMP/v.txt" 2>"$TMP/e.txt"; then
    echo "  model call failed; treating as advisory:"; sed 's/^/    /' "$TMP/e.txt" | head -3; exit 0
  fi
  cat "$TMP/v.txt"; echo
  if grep -qi '\bIDENTIFIES\b' "$TMP/v.txt"; then
    echo "A model judged at least one added line identifying. It is an opinion, not a finding —"
    echo "read it yourself before acting, and before dismissing it."
    [ "$STRICT" -eq 1 ] && exit 1
  fi
  exit 0
fi

# --- 1. deterministic narrowing -------------------------------------------------------------
python3 "$ROUTER" "${PATHS[@]}" --threshold "$THRESHOLD" --quiet --json "$TMP/blocks.json" >/dev/null 2>&1
COUNT="$(python3 -c "import json;print(len(json.load(open('$TMP/blocks.json'))['findings']))" 2>/dev/null || echo 0)"

if [ "$COUNT" -eq 0 ]; then
  echo "llm_provenance_review: no grounded-in-a-real-case block in scope; nothing to ask."
  exit 0
fi

# --- 2. is a model available? ----------------------------------------------------------------
if ! command -v claude >/dev/null 2>&1; then
  echo "llm_provenance_review: $COUNT block(s) need a judgement, but the \`claude\` CLI is not on PATH."
  echo "  This is not a failure — CI runs the deterministic half and does not need a model."
  echo "  To read them yourself:  python3 scripts/check_provenance_blocks.py <paths> --threshold $THRESHOLD"
  exit 0
fi

# --- 3. ask the one question ------------------------------------------------------------------
python3 - "$TMP/blocks.json" > "$TMP/prompt.txt" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
print("""You are auditing an open-source repository before publication. Below are paragraphs that
ground a rule in a real case. Grounding is intended and good; the risk is that the case stays
identifiable.

For EACH block answer on one line:

  <n>. VERDICT | the exact span that identifies | one sentence on what a reader could work out

VERDICT is one of:
  IDENTIFIES  a reader could work out the real person, manuscript, peer review, submission,
              institution or dataset behind this — including by combining it with a public
              author byline, or with a commit message in the same repository.
  GENERIC     the lesson survives without anyone being identifiable.
  UNSURE      you cannot tell from the text alone.

Weigh these especially, because a pattern cannot:
  - peer review is confidential in THREE directions: the manuscript, any co-reviewer's report,
    and the editor's decision. Describing any of the three is disclosure even with no ID present.
  - an author's own submission history — target journal, month, article type, and above all a
    cascade after a decline elsewhere — is not public.
  - an unpublished result quoted precisely (a metric to 3+ decimals, an exact N) fingerprints one
    dataset.
  - a topic plus a venue can identify one in-flight paper even when neither alone would.
  - a shared exact date across several files can reveal a batch, and a batch can be a shortlist.

Do not flag: public DOIs and citations, vendored instrument provenance against a published
document, generic study descriptors ("a single-centre retrospective cohort"), or a month-precision
date used for staleness.

Answer only with the numbered lines. No preamble.
""")
for i, f in enumerate(d["findings"], 1):
    print(f"--- BLOCK {i} ({f['file']}:{f['line']}, signals: {', '.join(f['signals'])}) ---")
    print(f["excerpt"])
    print()
PY

echo "llm_provenance_review: asking a model about $COUNT block(s)..."
if ! claude -p < "$TMP/prompt.txt" > "$TMP/verdicts.txt" 2>"$TMP/err.txt"; then
  echo "  the model call failed (network, auth, or rate limit); treating as advisory:"
  sed 's/^/    /' "$TMP/err.txt" | head -5
  exit 0
fi

cat "$TMP/verdicts.txt"
echo

if grep -qi '\bIDENTIFIES\b' "$TMP/verdicts.txt"; then
  echo "At least one block was judged IDENTIFIES."
  echo "Keep the lesson; drop the identifying half. A model's verdict is an opinion, not a finding —"
  echo "read the block yourself before acting, and read it again before dismissing it."
  [ "$STRICT" -eq 1 ] && exit 1
fi
exit 0
