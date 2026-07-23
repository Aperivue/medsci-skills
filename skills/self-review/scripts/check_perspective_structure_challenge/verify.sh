#!/usr/bin/env bash
# Deterministic verifier for the perspective-structure challenge card.
# Runs check_perspective_structure.py on four synthetic manuscripts and diffs stdout against
# expected/. This gate is Minor-only, so it always exits 0 — exit code proves nothing. The
# verdicts live in stdout, so the golden-diff is the real assertion (learned from a Codex design
# review: crossfire cannot observe a Minor manuscript detector). Stdlib-only, network-free.
#
# Fixtures (synthetic only — no real manuscript, no PII):
#   perspective_bad.md   article_type Perspective, "## 1. Introduction" + "## Methods", a flat
#                        declarative abstract -> fires HEADING_NOT_ASSERTION + ABSTRACT_NO_AUTHORIAL_MOVE.
#   perspective_ok.md    argument-move headings + a "Here we argue ..." abstract -> silent.
#   not_perspective.md   article_type Original Article + full IMRAD -> silent (genre gate).
#   edge_hardened.md     Perspective; a commented "## Methods" and "we argue", a "### Box" level-3
#                        heading, and a duplicate "## Abstract" in the notes tail whose FIRST copy
#                        carries the move -> silent findings + a duplicate-abstract warning on stderr.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
DET="$HERE/../check_perspective_structure.py"
cd "$HERE"

pass=1
for f in perspective_bad perspective_ok not_perspective edge_hardened; do
  out="$(python3 "$DET" --manuscript "fixture/$f.md" 2>/dev/null)"
  if ! diff -u "expected/$f.txt" <(printf '%s\n' "$out"); then
    echo "FAIL: $f stdout drifted from expected/$f.txt" >&2; pass=0
  fi
done

# The positive fixture must name both verdicts.
bad="$(python3 "$DET" --manuscript fixture/perspective_bad.md 2>/dev/null)"
printf '%s' "$bad" | grep -q PERSPECTIVE_HEADING_NOT_ASSERTION \
  || { echo "FAIL: perspective_bad missing HEADING_NOT_ASSERTION" >&2; pass=0; }
printf '%s' "$bad" | grep -q PERSPECTIVE_ABSTRACT_NO_AUTHORIAL_MOVE \
  || { echo "FAIL: perspective_bad missing ABSTRACT_NO_AUTHORIAL_MOVE" >&2; pass=0; }

# The genre gate must keep a non-Perspective silent despite IMRAD headings + a flat abstract.
printf '%s' "$(python3 "$DET" --manuscript fixture/not_perspective.md 2>/dev/null)" \
  | grep -q PERSPECTIVE_ && { echo "FAIL: not_perspective should be silent (genre gate)" >&2; pass=0; }

# Findings[] inspection on a known-good Perspective (a Minor detector's exit code is meaningless,
# so assert the JSON directly: active AND empty findings — not silent because misclassified).
python3 "$DET" --manuscript fixture/perspective_ok.md --quiet --out "/tmp/ps_ok.$$" 2>/dev/null
python3 -c "import json,sys; d=json.load(open('/tmp/ps_ok.$$')); sys.exit(0 if d['findings']==[] and d['metrics']['active'] else 1)" \
  || { echo "FAIL: perspective_ok should be an active Perspective with empty findings[]" >&2; pass=0; }
rm -f "/tmp/ps_ok.$$"

# The duplicate-abstract path must warn on stderr (and not crash).
python3 "$DET" --manuscript fixture/edge_hardened.md --quiet >/dev/null 2>/tmp/edge_err.$$ || true
grep -q "2 '## Abstract' sections" /tmp/edge_err.$$ \
  || { echo "FAIL: edge_hardened should warn about a duplicate abstract" >&2; pass=0; }
rm -f /tmp/edge_err.$$

if [ "$pass" -eq 1 ]; then
  echo "PASS: perspective-structure gate flags IMRAD headings + a flat abstract, stays silent on a clean Perspective and on a non-Perspective, and warns on a duplicate abstract."
else
  exit 1
fi
