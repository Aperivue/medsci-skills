#!/usr/bin/env bash
# Self-test for scripts/check_test_wiring.py.
#
# The defect: four challenge cards — check_review_request_types, check_model_provenance,
# check_citation_keys, check_analysis_definitions — shipped with fixtures, expected output and a
# skill.yml validation_commands entry, and `validate.yml` named none of them. They were green
# because nothing ran them. PR #412 wired those four by hand after a manual sweep; on 2026-07-25
# twelve more were still in the same state. Case 2 restores that defect on the real workflow and
# asserts the gate FAILS.
#
#  1) live repo passes                                    (all twelve are now wired)
#  2) a wired step deleted from the real workflow -> FAILS  <-- THE DEFECT
#  3) declared in skill.yml but not in any workflow -> FAILS (validation_commands is not wiring)
#  4) one hop through a script a run: step invokes -> silent NEGATIVE FIXTURE
#  5) named only in a step `name:` (never executed) -> FAILS (a label is not an invocation)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
GATE="$ROOT/scripts/check_test_wiring.py"

# 1) live repo passes
python3 "$GATE" --quiet || { echo "FAIL: live repo should have every test asset wired" >&2; exit 1; }

tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
real="$tmp/real"; mkdir -p "$real"
cp -R "$ROOT/skills" "$ROOT/scripts" "$ROOT/tests" "$ROOT/.github" "$real/"

python3 "$GATE" --root "$real" --quiet \
  || { echo "FAIL: an untouched copy must pass" >&2; exit 1; }

# 2) THE DEFECT: delete the step that runs one challenge. Its fixtures, its expected output, its
#    skill.yml entry and its manifest row all stay. If any of those counted as wiring, this case
#    would pass — and that is exactly the bug the four of PR #412 had.
victim="skills/manage-refs/scripts/check_citation_keys_challenge/verify.sh"
python3 - "$real/.github/workflows/validate.yml" "$victim" <<'PY'
import re, sys
path, victim = sys.argv[1], sys.argv[2]
text = open(path, encoding="utf-8").read()
# drop the whole `- name: ...` block whose run: names the victim
blocks = re.split(r"(?m)(?=^      - name:)", text)
kept = [b for b in blocks if victim not in b]
assert len(kept) == len(blocks) - 1, f"expected to drop exactly one step, dropped {len(blocks)-len(kept)}"
open(path, "w", encoding="utf-8").write("".join(kept))
PY

if python3 "$GATE" --root "$real" >/dev/null 2>&1; then
  echo "FAIL: a challenge no workflow runs must exit 1 (fixtures and skill.yml must not count)" >&2
  exit 1
fi
report="$(python3 "$GATE" --root "$real" 2>&1 || true)"
grep -q "check_citation_keys_challenge" <<<"$report" \
  || { echo "FAIL: the report must name the unwired challenge" >&2; echo "$report" >&2; exit 1; }
grep -q "validation_commands is not wiring" <<<"$report" \
  || { echo "FAIL: the report should say skill.yml is not wiring" >&2; echo "$report" >&2; exit 1; }
cp "$ROOT/.github/workflows/validate.yml" "$real/.github/workflows/validate.yml"   # restore
python3 "$GATE" --root "$real" --quiet \
  || { echo "FAIL: restore should return the copy to clean" >&2; exit 1; }

# --- synthetic tree: the remaining edges, in isolation ---
syn="$tmp/syn"
mkdir -p "$syn/.github/workflows" "$syn/skills/alpha/scripts/thing_challenge" "$syn/tests" "$syn/scripts"

cat > "$syn/skills/alpha/scripts/thing_challenge/verify.sh" <<'SH'
echo PASS
SH
cat > "$syn/skills/alpha/skill.yml" <<'YML'
name: alpha
validation_commands:
  - bash scripts/thing_challenge/verify.sh
YML
cat > "$syn/tests/test_hopped.sh" <<'SH'
echo hopped
SH
cat > "$syn/scripts/runner.sh" <<'SH'
bash tests/test_hopped.sh
SH

# 3) declared in skill.yml, absent from every workflow
cat > "$syn/.github/workflows/validate.yml" <<'YML'
name: validate
on: [push]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - name: Run the hop runner
        run: bash scripts/runner.sh
YML
if python3 "$GATE" --root "$syn" >/dev/null 2>&1; then
  echo "FAIL: a challenge only skill.yml declares must exit 1" >&2; exit 1
fi
report="$(python3 "$GATE" --root "$syn" 2>&1 || true)"
grep -q "thing_challenge" <<<"$report" || { echo "FAIL: report must name it" >&2; exit 1; }
# 4) NEGATIVE FIXTURE, same run: tests/test_hopped.sh is named only inside scripts/runner.sh.
#    A workflow-text grep would call it unwired; it is wired one hop away, exactly as
#    tests/test_precedent_hashing.sh is by scripts/validate_skills.sh.
grep -q "test_hopped.sh" <<<"$report" \
  && { echo "FAIL: a test invoked one hop away must NOT be reported" >&2; exit 1; }

# 5) a `name:` mentioning the path is a label, not an invocation
cat > "$syn/.github/workflows/validate.yml" <<'YML'
name: validate
on: [push]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - name: "Run skills/alpha/scripts/thing_challenge/verify.sh"
        run: echo "we renamed the step and forgot the command"
      - name: Run the hop runner
        run: bash scripts/runner.sh
YML
if python3 "$GATE" --root "$syn" >/dev/null 2>&1; then
  echo "FAIL: a path named only in a step label must still exit 1" >&2; exit 1
fi

# now wire it for real
cat > "$syn/.github/workflows/validate.yml" <<'YML'
name: validate
on: [push]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - name: Run the alpha challenge
        run: bash skills/alpha/scripts/thing_challenge/verify.sh
      - name: Run the hop runner
        run: bash scripts/runner.sh
YML
python3 "$GATE" --root "$syn" --quiet \
  || { echo "FAIL: a genuinely wired tree must pass" >&2; exit 1; }

echo "PASS: test-wiring gate — live repo clean; a deleted step, a skill.yml-only declaration and a"
echo "      label-without-a-command all fail; a test wired one hop away stays silent."
