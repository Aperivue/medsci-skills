#!/usr/bin/env bash
# Deterministic verifier for the model-provenance challenge card.
# Runs check_model_provenance.py on three synthetic dossiers and diffs stdout against
# expected/. No network, no repository fetch, no licence resolution — every finding is
# decided by set arithmetic over the dossier JSON. Exit 0 = all match and exit codes correct.
#
# Fixtures (synthetic only — invented model and dataset names, no real artifacts):
#   dossier_defect.json   — facts that CONTRADICT each other: an evaluation arm on the very
#                           benchmark the model was developed on, that same arm inside the
#                           pretraining corpus, a non-commercial licence under commercial
#                           intent, a task that is not the study's task, no version pin, no
#                           reported validation, hardware claimed but never run.
#   dossier_unstated.json — facts that are ABSENT: no licence at all, pretrained weights whose
#                           corpus is not stated, no version pin. A different failure mode from
#                           the first, and the more common one.
#   dossier_clean.json    — the same kind of artifact with every fact stated and consistent.
#                           Note it still declares `developed_on: ExampleBench`; nothing fires,
#                           because no evaluation arm uses ExampleBench. The gate flags the
#                           RELATIONSHIP between provenance and evaluation, not the presence of
#                           a benchmark in a model's history.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
DET="$HERE/../check_model_provenance.py"

ok=1
for f in defect unstated clean; do
  got="$(python3 "$DET" --dossier "$HERE/fixture/dossier_$f.json")"
  if ! diff -u "$HERE/expected/$f.txt" <(printf '%s\n' "$got"); then
    echo "FAIL: $f-fixture output drifted from expected/$f.txt" >&2; ok=0
  fi
done

for f in defect unstated; do
  python3 "$DET" --dossier "$HERE/fixture/dossier_$f.json" --strict --quiet >/dev/null 2>&1 && rc=0 || rc=$?
  [ "${rc:-0}" -eq 1 ] || { echo "FAIL: $f fixture should exit 1 under --strict (got ${rc:-0})" >&2; ok=0; }
done
python3 "$DET" --dossier "$HERE/fixture/dossier_clean.json" --strict --quiet >/dev/null 2>&1 && rc=0 || rc=$?
[ "$rc" -eq 0 ] || { echo "FAIL: clean fixture should exit 0 under --strict (got $rc)" >&2; ok=0; }

if [ "$ok" -eq 1 ]; then
  echo "PASS: model-provenance gate separates contradictory facts from absent ones and clears a fully stated dossier."
fi
[ "$ok" -eq 1 ] || exit 1
