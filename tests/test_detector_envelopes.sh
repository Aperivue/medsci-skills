#!/usr/bin/env bash
# Self-test for scripts/check_detector_envelopes.py — the gate that keeps every detector's
# JSON artifact naming the detector that wrote it.
#
# The live repo must be clean, and each drift shape must fail: a detector whose envelope
# carries no `"detector"` key, and one that carries the WRONG detector's name (a copy-paste
# from the file it was cloned from, which is exactly how this would regress).
#
# The same gate ratchets summary.verdict onto {OK, MAJOR_CANDIDATE, NOT_ASSESSED}: a new
# detector outside it fails, and the grandfather list may only shrink (a stale entry fails).
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

# c) correctly labelled, conforming summary.verdict -> passes again
cat > "$VICTIM/check_unlabelled_probe.py" <<'PY'
import json
from pathlib import Path
n_major = 0
Path("out.json").write_text(json.dumps({"detector": "check_unlabelled_probe", "claims": [],
    "summary": {"n_major": n_major, "verdict": "MAJOR_CANDIDATE" if n_major else "OK"}}, indent=2))
PY
python3 "$G" --strict > /dev/null 2>&1
ck "correctly labelled envelope passes" 0 "$?"

# d) a detector that emits no JSON at all must be declared, not silently tolerated
cat > "$VICTIM/check_unlabelled_probe.py" <<'PY'
print("no json here")
PY
python3 "$G" --strict > /dev/null 2>&1
ck "a detector with no JSON output must be declared" 1 "$?"

# --- verdict vocabulary ---------------------------------------------------------------
probe() {  # $1 = python expression for summary.verdict
  cat > "$VICTIM/check_unlabelled_probe.py" <<EOF
import json
from pathlib import Path
n_major, unchecked = 0, False
Path("out.json").write_text(json.dumps({"detector": "check_unlabelled_probe", "claims": [],
    "summary": {"n_major": n_major, "verdict": $1}}, indent=2))
EOF
}

# e) NOT_ASSESSED is in the vocabulary
probe '"MAJOR_CANDIDATE" if n_major else ("NOT_ASSESSED" if unchecked else "OK")'
python3 "$G" --strict > /dev/null 2>&1
ck "verdict OK / MAJOR_CANDIDATE / NOT_ASSESSED passes" 0 "$?"

# f) a value outside the vocabulary (a Minor-only synonym) fails, and is named
probe '"MAJOR_CANDIDATE" if n_major else "REVIEW"'
python3 "$G" --strict > /dev/null 2>&1
ck "verdict outside the vocabulary fails" 1 "$?"
python3 "$G" 2>&1 | grep -q "check_unlabelled_probe.py: summary.verdict uses \['REVIEW'\]"
ck "the out-of-vocabulary value is named" 0 "$?"

# g) labelled envelope with a top-level verdict but no summary.verdict fails
cat > "$VICTIM/check_unlabelled_probe.py" <<'PY'
import json
from pathlib import Path
Path("out.json").write_text(json.dumps({"detector": "check_unlabelled_probe", "verdict": "OK"}, indent=2))
PY
python3 "$G" --strict > /dev/null 2>&1
ck "no readable summary.verdict fails" 1 "$?"

# h) a verdict the gate cannot read statically fails rather than counting as conforming
probe 'compute_verdict()'
python3 "$G" --strict > /dev/null 2>&1
ck "unreadable summary.verdict fails" 1 "$?"

# --- grandfather ratchet: a copy of the gate with one extra entry for the probe -------
# The copy sits beside the real gate so it resolves the same ROOT; removed on exit.
G2="$REPO_ROOT/scripts/_check_detector_envelopes_selftest_tmp.py"
trap 'rm -rf "$REPO_ROOT/skills/_envelope_selftest_tmp" "$G2"' EXIT
with_entry() {  # $1 = python literal for the recorded values (None or a frozenset)
  python3 -c '
import sys
src, dst, rec = sys.argv[1:4]
s = open(src, encoding="utf-8").read()
entry = ("GRANDFATHERED[\"skills/_envelope_selftest_tmp/scripts/check_unlabelled_probe.py\"] = "
         "(" + rec + ", \"self-test\")\n\n\ndef main(")
open(dst, "w", encoding="utf-8").write(s.replace("\ndef main(", "\n" + entry, 1))
' "$G" "$G2" "$1"
}

with_entry 'frozenset({"REVIEW"})'
probe '"MAJOR_CANDIDATE" if n_major else "REVIEW"'
python3 "$G2" --strict > /dev/null 2>&1
ck "grandfathered detector, unchanged values, passes" 0 "$?"

probe '"FLAG" if n_major else "REVIEW"'
python3 "$G2" --strict > /dev/null 2>&1
ck "grandfathered detector adding a new value fails" 1 "$?"

probe '"MAJOR_CANDIDATE" if n_major else "OK"'
python3 "$G2" --strict > /dev/null 2>&1
ck "stale entry (detector now conforms) fails" 1 "$?"
python3 "$G2" 2>&1 | grep -q "remove its stale GRANDFATHERED entry"
ck "the stale entry is reported as stale" 0 "$?"

with_entry 'frozenset({"REVIEW", "FLAG"})'
probe '"MAJOR_CANDIDATE" if n_major else "REVIEW"'
python3 "$G2" --strict > /dev/null 2>&1
ck "stale entry (fewer outliers than recorded) fails" 1 "$?"

with_entry 'None'
python3 "$G2" --strict > /dev/null 2>&1
ck "entry recorded unreadable, now readable, fails" 1 "$?"

rm -rf "$REPO_ROOT/skills/_envelope_selftest_tmp"
python3 "$G2" --strict > /dev/null 2>&1
ck "entry naming a removed detector fails" 1 "$?"
rm -f "$G2"

# 5) and the repo is clean again once the fixtures are gone
python3 "$G" --strict > /dev/null 2>&1
ck "repo clean after fixtures removed" 0 "$?"

echo "----"
echo "test_detector_envelopes: $pass passed, $fail failed"
[ "$fail" -eq 0 ]
