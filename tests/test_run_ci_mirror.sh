#!/usr/bin/env bash
# Self-test for scripts/run_ci_mirror.py — the local mirror of the CI `validate` job.
# It must (1) enumerate the real gate steps (not drift), (2) include actual gates, and
# (3) exclude `uses:` and dependency-install steps. Fast: only exercises --list (never
# the full run, which would be recursive and slow).
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
S="$ROOT/scripts/run_ci_mirror.py"
fail=0
ck() { if [ "$2" = "$3" ]; then printf '  PASS  %s\n' "$1"; else printf '  FAIL  %s (want %s got %s)\n' "$1" "$2" "$3"; fail=$((fail+1)); fi; }

[ -f "$S" ] || { echo "ENV-ERR: script missing" >&2; exit 2; }

LIST="$(python3 "$S" --list)"; rc=$?
ck "--list exits 0" 0 "$rc"

# (1) enumerates many gates — the validate job has well over 100 run-steps.
n="$(printf '%s\n' "$LIST" | grep -cvE '^\s*$|gate step\(s\) mirrored|^NOT mirrored')"
if [ "$n" -ge 100 ]; then printf '  PASS  --list enumerates >=100 gates (%s)\n' "$n"; else printf '  FAIL  --list only %s gates\n' "$n"; fail=$((fail+1)); fi

# (2) includes a real gate that must always be there.
printf '%s\n' "$LIST" | grep -qi 'validate_skills' && ck "includes the validate_skills gate" yes yes || ck "includes the validate_skills gate" yes no
printf '%s\n' "$LIST" | grep -qi 'catalog' && ck "includes a catalog-consistency gate" yes yes || ck "includes a catalog-consistency gate" yes no

# (3) excludes dependency-install setup steps (e.g. a step named "Install ... poppler").
if printf '%s\n' "$LIST" | grep -qiE '^Install (Python|exiftool|node)'; then
  printf '  FAIL  setup/install step leaked into the mirror\n'; fail=$((fail+1))
else
  printf '  PASS  setup/install steps are excluded\n'
fi

# (4) --only narrows the set and still parses.
python3 "$S" --only 'workflow' --list >/dev/null 2>&1
ck "--only narrows and exits 0" 0 "$?"

# (5) the summary names every workflow job it does NOT mirror. A green mirror was quoted as
#     "CI will be green" while foundation-os (macOS/Windows) went red: the summary never said
#     that job exists. Expected names come from the workflow itself, so this cannot drift.
others="$(python3 -c "
import yaml
d = yaml.safe_load(open('$ROOT/.github/workflows/validate.yml'))
print('\n'.join(j for j in d['jobs'] if j != 'validate'))")"
if [ -z "$others" ]; then
  printf '  PASS  (no other jobs in validate.yml to name)\n'
else
  # the final summary, from one real and fast gate (an empty --only is now an error, below)
  SUMMARY="$(python3 "$S" --only 'Workflow files parse')"
  while IFS= read -r job; do
    printf '%s\n' "$LIST" | grep -q "NOT mirrored.*$job" && ck "--list names unmirrored job $job" yes yes \
      || ck "--list names unmirrored job $job" yes no
    printf '%s\n' "$SUMMARY" | grep -q "NOT mirrored.*$job" && ck "final summary names unmirrored job $job" yes yes \
      || ck "final summary names unmirrored job $job" yes no
  done <<<"$others"
fi

# (6) a run may only report what it executed. Each case runs the real main() against a synthetic
#     workflow (the module's WORKFLOW swapped), so no real gate runs and nothing is recursive.
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
cat >"$TMP/wf.yml" <<'YML'
jobs:
  validate:
    steps:
      - uses: actions/checkout@v4
      - name: gate one fails
        run: exit 1
      - name: gate two
        run: "true"
      - name: gate three
        run: "true"
YML
synth() {  # synth <workflow> <args...> ; stdout+stderr to $TMP/out, prints the exit code
  local wf="$1"; shift
  python3 - "$S" "$wf" "$@" >"$TMP/out" 2>&1 <<'PY'
import importlib.util, sys
from pathlib import Path
spec = importlib.util.spec_from_file_location("run_ci_mirror", sys.argv[1])
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
m.WORKFLOW = Path(sys.argv[2])
sys.argv = ["run_ci_mirror.py", *sys.argv[3:]]
sys.exit(m.main())
PY
  echo $?
}
has() { grep -q -- "$1" "$TMP/out" && echo yes || echo no; }

# an --only that matches nothing ran zero gates: it must not exit 0 or print a green verdict
ck "--only matching nothing exits 2" 2 "$(synth "$TMP/wf.yml" --only zz-no-such-gate-zz)"
ck "  ...and says it matched nothing" yes "$(has 'matched none')"
ck "  ...and prints no OK verdict" no "$(has '^OK')"
ck "--list with an empty --only exits 2" 2 "$(synth "$TMP/wf.yml" --list --only zz-no-such-gate-zz)"

# --fail-fast stops after gate one: gates two and three never ran and are not "passed"
ck "--fail-fast run exits 1" 1 "$(synth "$TMP/wf.yml" --fail-fast)"
ck "  ...reports 0 of 3 passed" yes "$(has '^0/3 gates passed')"
ck "  ...counts the 2 unexecuted gates as not run" yes "$(has '^NOT RUN (2)')"
ck "  ...does not count them as passed" no "$(has '2/3 gates passed')"

# a green --only subset is PARTIAL and must not predict the whole job
ck "--only subset of passing gates exits 0" 0 "$(synth "$TMP/wf.yml" --only 'gate t')"
ck "  ...is labelled PARTIAL" yes "$(has 'PARTIAL run')"
ck "  ...does not claim CI will be green" no "$(has 'will be green')"

# the full-job verdict is still printed when every gate was selected and executed
sed -e 's/run: exit 1/run: "true"/' "$TMP/wf.yml" >"$TMP/green.yml"
ck "full run of passing gates exits 0" 0 "$(synth "$TMP/green.yml")"
ck "  ...reports all 3 executed and passed" yes "$(has 'OK: all 3 validate-job gates passed')"

echo "test_run_ci_mirror: $fail failure(s)"
[ "$fail" -eq 0 ]
