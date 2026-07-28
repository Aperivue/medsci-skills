#!/usr/bin/env bash
# Self-test for scripts/check_workflow_yaml.py — the gate that keeps a broken workflow from
# VANISHING instead of failing. It shipped in #333 with no self-test of its own, and on 2026-07-15
# a defect walked straight past it: a merge left a `- name:` step whose `run:` had been dropped. The
# file was valid YAML, the gate passed, and GitHub ran zero jobs while the branch looked quiet.
#
# So this test does not check that the gate passes. It rebuilds each disappearing-failure shape and
# demands the gate FAIL — and holds it silent on a well-formed workflow, because a gate that fires on
# good work gets switched off.
set -u

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
G="$REPO_ROOT/scripts/check_workflow_yaml.py"

pass=0
fail=0
ck() {
  local label="$1" expected="$2" actual="$3"
  if [ "$expected" = "$actual" ]; then
    printf '  PASS  %-56s exit=%s\n' "$label" "$actual"
    pass=$((pass + 1))
  else
    printf '  FAIL  %-56s expected=%s actual=%s\n' "$label" "$expected" "$actual"
    fail=$((fail + 1))
  fi
}

# 1) the live repo is well-formed
python3 "$G" --strict >/dev/null 2>&1
ck "live repo: all workflows load and every step runs" 0 "$?"

# The gate reads .github/workflows relative to its own parent, so point it at a fixture tree by
# running a copy from there. Simplest: build a throwaway repo root with just the gate + a workflow.
FIX="$(mktemp -d)"
trap 'rm -rf "$FIX"' EXIT
mkdir -p "$FIX/scripts" "$FIX/.github/workflows"
cp "$G" "$FIX/scripts/check_workflow_yaml.py"
run_fixture() { python3 "$FIX/scripts/check_workflow_yaml.py" --strict >/dev/null 2>&1; }

# 2) REGRESSION — the 2026-07-15 defect: a step with a name but no run/uses
cat > "$FIX/.github/workflows/w.yml" <<'YML'
name: t
on: [push]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - name: has a name but its run was dropped in a merge
      - name: fine
        run: echo ok
YML
run_fixture
ck "REGRESSION: a step with no run/uses (the merge-drop bug)" 1 "$?"

# 3) REGRESSION — the original #333 trap: unquoted ': ' turns a scalar into a mapping
cat > "$FIX/.github/workflows/w.yml" <<'YML'
name: t
on: [push]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - name: Run deck-budget (same deck: fits an oral, too dense for a keynote)
        run: echo ok
YML
run_fixture
ck "REGRESSION: unquoted ': ' in a step name (the #333 trap)" 1 "$?"

# 4) REGRESSION — parses but declares no jobs
cat > "$FIX/.github/workflows/w.yml" <<'YML'
name: t
on: [push]
YML
run_fixture
ck "REGRESSION: valid YAML with no jobs" 1 "$?"

# 5) NEGATIVE — a `uses:` step (no run) is legitimate and must stay silent
cat > "$FIX/.github/workflows/w.yml" <<'YML'
name: t
on: [push]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: build
        run: echo ok
YML
run_fixture
ck "NEGATIVE: a uses-only step is not runless" 0 "$?"

# 6) NEGATIVE — a properly quoted name with ': ' inside must stay silent
cat > "$FIX/.github/workflows/w.yml" <<'YML'
name: t
on: [push]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - name: "Run deck-budget (same deck: fits an oral)"
        run: echo ok
YML
run_fixture
ck "NEGATIVE: a quoted name containing ': ' is fine" 0 "$?"

echo
echo "  $pass passed, $fail failed"
[ "$fail" -eq 0 ] || exit 1
