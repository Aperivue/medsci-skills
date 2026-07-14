#!/usr/bin/env bash
# Self-test for scripts/check_script_reachability.py.
#
# The defect: skills/sync-submission/scripts/assemble_supplement.py shipped for months — tested,
# manifested, announced in the CHANGELOG — and no SKILL.md ever invoked it. Case 2 restores that
# defect (drop the SKILL.md step) and asserts the gate FAILS.
#
#  1) live repo passes                              (assemble_supplement.py is now wired)
#  2) SKILL.md step removed -> FAILS                <-- THE DEFECT
#  3) allowlisted but undocumented -> FAILS         (the escape hatch cannot hide dead code)
#  4) import-only helper stays silent               NEGATIVE FIXTURE — no phantom orphans
#  5) shell-out from a reachable script stays silent NEGATIVE FIXTURE
#  6) a genuine orphan FAILS
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
GATE="$ROOT/scripts/check_script_reachability.py"

# 1) live repo passes
python3 "$GATE" --strict >/dev/null || { echo "FAIL: live repo should be fully reachable" >&2; exit 1; }

tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
cp -R "$ROOT/skills" "$tmp/skills"

python3 "$GATE" --skills-dir "$tmp/skills" --strict >/dev/null \
  || { echo "FAIL: an untouched copy must pass" >&2; exit 1; }

# 2) THE DEFECT: remove the SKILL.md step that invokes assemble_supplement.py.
#    Every other signal it has — its test, its CI step, its manifest entry — stays in place. If
#    those made it "reachable", this case would pass, and that is precisely the bug.
grep -v 'assemble_supplement.py' "$tmp/skills/sync-submission/SKILL.md" > "$tmp/stripped.md"
mv "$tmp/stripped.md" "$tmp/skills/sync-submission/SKILL.md"
if python3 "$GATE" --skills-dir "$tmp/skills" --strict >/dev/null 2>&1; then
  echo "FAIL: a script no SKILL.md invokes must exit 1 (its test must not count as a caller)" >&2
  exit 1
fi
report="$(python3 "$GATE" --skills-dir "$tmp/skills" --strict 2>&1 || true)"
grep -q "assemble_supplement.py" <<<"$report" \
  || { echo "FAIL: the report must name the orphan" >&2; echo "$report" >&2; exit 1; }
grep -q "do not make it RUN" <<<"$report" \
  || { echo "FAIL: the report should say a test is not a caller" >&2; exit 1; }
cp "$ROOT/skills/sync-submission/SKILL.md" "$tmp/skills/sync-submission/SKILL.md"   # restore

# 3) the escape hatch must not hide dead code: allowlisted, but the doc no longer mentions it
grep -v 'build_jacc_template.py' "$tmp/skills/MAINTENANCE.md" > "$tmp/m.md"
mv "$tmp/m.md" "$tmp/skills/MAINTENANCE.md"
if python3 "$GATE" --skills-dir "$tmp/skills" --strict >/dev/null 2>&1; then
  echo "FAIL: an allowlisted tool its own doc never mentions must exit 1" >&2; exit 1
fi
cp "$ROOT/skills/MAINTENANCE.md" "$tmp/skills/MAINTENANCE.md"                       # restore
python3 "$GATE" --skills-dir "$tmp/skills" --strict >/dev/null \
  || { echo "FAIL: restore should return the copy to clean" >&2; exit 1; }

# --- synthetic tree: the edge cases, in isolation ---
syn="$tmp/syn/skills"; mkdir -p "$syn/alpha/scripts" "$syn/beta/scripts"

# alpha: SKILL.md invokes runner.py; runner.py imports _helper (NO filename string anywhere) and
# shells out to beta's script by filename.
cat > "$syn/alpha/SKILL.md" <<'MD'
# Alpha
Run `python3 scripts/runner.py --strict` before freeze.
MD
cat > "$syn/alpha/scripts/runner.py" <<'PY'
from _helper import thing
import subprocess
subprocess.run(["python3", "../../beta/scripts/worker.py"])
PY
cat > "$syn/alpha/scripts/_helper.py" <<'PY'
thing = 1
PY
cat > "$syn/beta/SKILL.md" <<'MD'
# Beta
MD
cat > "$syn/beta/scripts/worker.py" <<'PY'
print("worker")
PY

# 4+5) NEGATIVE FIXTURE: _helper.py is reached ONLY by `from _helper import thing` and worker.py
#      ONLY by a shell-out from a reachable script. A filename grep would call both dead.
python3 "$GATE" --skills-dir "$syn" --strict >/dev/null || {
  echo "FAIL: import-resolved helper and shelled-out script must NOT be reported as orphans" >&2
  python3 "$GATE" --skills-dir "$syn" --strict >&2 || true
  exit 1
}

# 6) a genuine orphan
cat > "$syn/beta/scripts/orphan.py" <<'PY'
print("nobody calls me")
PY
if python3 "$GATE" --skills-dir "$syn" --strict >/dev/null 2>&1; then
  echo "FAIL: a genuine orphan must exit 1" >&2; exit 1
fi

echo "PASS: script reachability gate — live repo clean; a de-wired script, an undocumented allowlist"
echo "      entry and a genuine orphan all fail; import-only and shell-out targets stay silent."
