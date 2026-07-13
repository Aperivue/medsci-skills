#!/usr/bin/env bash
# Self-test for scripts/check_detector_envelopes.py — the gate that keeps every detector's
# JSON artifact naming the detector that wrote it.
#
# The live repo must be clean, and each drift shape must fail: a detector whose envelope
# carries no `"detector"` key, and one that carries the WRONG detector's name (a copy-paste
# from the file it was cloned from, which is exactly how this would regress).
set -u

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
G="$REPO_ROOT/scripts/check_detector_envelopes.py"

pass=0
fail=0
ck() {
  local label="$1" expected="$2" actual="$3"
  if [ "$expected" = "$actual" ]; then
    printf '  PASS  %-50s exit=%s\n' "$label" "$actual"
    pass=$((pass + 1))
  else
    printf '  FAIL  %-50s expected=%s actual=%s\n' "$label" "$expected" "$actual"
    fail=$((fail + 1))
  fi
}

# 1) the live repo self-identifies
python3 "$G" --strict > /dev/null 2>&1
ck "live repo: every JSON detector self-identifies" 0 "$?"

# --- drift fixtures: a throwaway skill tree the gate is pointed at ---------------------
# The gate resolves the repo root from its own location, so the fixtures are built as a
# real (temporary) skill inside the repo and removed on exit.
VICTIM="$REPO_ROOT/skills/_envelope_selftest_tmp/scripts"
trap 'rm -rf "$REPO_ROOT/skills/_envelope_selftest_tmp"' EXIT
mkdir -p "$VICTIM"

# a) unlabelled envelope -> must fail
cat > "$VICTIM/check_unlabelled_probe.py" <<'PY'
import json
from pathlib import Path
Path("out.json").write_text(json.dumps({"claims": []}, indent=2))
PY
python3 "$G" --strict > /dev/null 2>&1
ck "unlabelled JSON envelope fails" 1 "$?"

OUT="$(python3 "$G" 2>&1)"
echo "$OUT" | grep -q "check_unlabelled_probe"
ck "the offending detector is named" 0 "$?"

# b) WRONG detector name (a clone that kept its parent's label) -> must fail
cat > "$VICTIM/check_unlabelled_probe.py" <<'PY'
import json
from pathlib import Path
Path("out.json").write_text(json.dumps({"detector": "check_something_else", "claims": []}, indent=2))
PY
python3 "$G" --strict > /dev/null 2>&1
ck "a clone carrying the WRONG detector name fails" 1 "$?"

# c) correctly labelled -> passes again
cat > "$VICTIM/check_unlabelled_probe.py" <<'PY'
import json
from pathlib import Path
Path("out.json").write_text(json.dumps({"detector": "check_unlabelled_probe", "claims": []}, indent=2))
PY
python3 "$G" --strict > /dev/null 2>&1
ck "correctly labelled envelope passes" 0 "$?"

# d) a detector that emits no JSON at all must be declared, not silently tolerated
cat > "$VICTIM/check_unlabelled_probe.py" <<'PY'
print("no json here")
PY
python3 "$G" --strict > /dev/null 2>&1
ck "a detector with no JSON output must be declared" 1 "$?"

rm -rf "$REPO_ROOT/skills/_envelope_selftest_tmp"

# 5) and the repo is clean again once the fixtures are gone
python3 "$G" --strict > /dev/null 2>&1
ck "repo clean after fixtures removed" 0 "$?"

echo "----"
echo "test_detector_envelopes: $pass passed, $fail failed"
[ "$fail" -eq 0 ]
