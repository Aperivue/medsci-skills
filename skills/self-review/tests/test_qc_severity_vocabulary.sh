#!/usr/bin/env bash
# Regression test: a gate that says "cannot submit" must not be counted as an optional Minor.
#
# `_qc_findings._MAJOR` knew two words, `MAJOR` and `FATAL`. The detectors were written
# independently and each picked its own vocabulary, so a severity outside those two fell into the
# `else` branch and was counted Minor. `check_placeholders` marks a leftover `TODO` as `blocker` and
# exits 1 on it unconditionally — and the stop controller read the same artifact and answered:
#
#     STOP_MINOR_OPTIONAL — "No required edits ... do not treat them as blocking and do not loop"
#
# Membership in the Major set is derived from each detector's own exit contract, so this test asserts
# behaviour per word, and — the part that closes the class — asserts that EVERY severity literal
# shipped anywhere in skills/*/scripts/*.py is classified deliberately. A newly invented word must
# fail this test rather than silently become an optional Minor.
set -u

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
R="$REPO_ROOT/skills/self-review/scripts/refinement_stop.py"
Q="$REPO_ROOT/skills/self-review/scripts/_qc_findings.py"
WORK="$(mktemp -d -t qc_severity_test.XXXXXX)"
trap 'rm -rf "$WORK"' EXIT

pass=0
fail=0
ck() {
  local label="$1" expected="$2" actual="$3"
  if [ "$expected" = "$actual" ]; then
    printf '  PASS  %-50s %s\n' "$label" "$actual"
    pass=$((pass + 1))
  else
    printf '  FAIL  %-50s expected=%s actual=%s\n' "$label" "$expected" "$actual"
    fail=$((fail + 1))
  fi
}

verdict_for() {  # verdict_for <severity> -> the controller's terminal-state word
  local sev="$1" d="$WORK/qc_$RANDOM"
  mkdir -p "$d"
  python3 - "$d/gate.json" "$sev" <<'PY'
import json, sys
json.dump({"detector": "check_placeholders",
           "findings": [{"verdict": "PLACEHOLDER_LEFT", "severity": sys.argv[2], "line": 42}]},
          open(sys.argv[1], "w"), indent=1)
PY
  python3 "$R" --qc-dir "$d" 2>/dev/null | sed -n '1s/.*: //p'
}

echo "==== words whose own detector exits 1: the loop must CONTINUE ===="
for sev in blocker hard stale FAIL MAJOR FATAL Major major; do
  ck "severity '$sev' -> CONTINUE" CONTINUE "$(verdict_for "$sev")"
done

echo "==== NEGATIVE CONTROLS — advisory words must stay optional ===="
# check_generated_code computes n_flag = len(claims) - n_major and exits only on n_major, so its own
# contract says Flag is advisory. Widening indiscriminately would break this.
for sev in Flag Minor minor soft warn INFO; do
  ck "severity '$sev' -> STOP_MINOR_OPTIONAL" STOP_MINOR_OPTIONAL "$(verdict_for "$sev")"
done

echo "==== an unrecognised word fails toward the loop CONTINUING, and is named ===="
ck "unknown 'urgent' -> CONTINUE" CONTINUE "$(verdict_for urgent)"
d="$WORK/qc_unknown"; mkdir -p "$d"
python3 - "$d/gate.json" <<'PY'
import json, sys
json.dump({"detector": "check_x",
           "findings": [{"verdict": "V", "severity": "urgent", "line": 1}]},
          open(sys.argv[1], "w"), indent=1)
PY
ck "  and reported by name" "urgent" \
   "$(python3 "$R" --qc-dir "$d" --out "$d/stop.json" >/dev/null 2>&1; \
      python3 -c 'import json,sys; print(",".join(json.load(open(sys.argv[1])).get("unknown_severities",[])))' "$d/stop.json" 2>/dev/null || echo MISSING)"

echo "==== the class-closing assertion: every shipped severity word is classified ===="
unclassified="$(python3 - "$REPO_ROOT" "$Q" <<'PY'
import importlib.util, pathlib, re, sys
root = pathlib.Path(sys.argv[1])
spec = importlib.util.spec_from_file_location("q", sys.argv[2])
m = importlib.util.module_from_spec(spec)
sys.modules["q"] = m
spec.loader.exec_module(m)
pat = re.compile(r'"severity"\s*:\s*"([A-Za-z_][A-Za-z_ ]*)"')
words = set()
for p in root.glob("skills/*/scripts/*.py"):
    words |= set(pat.findall(p.read_text(encoding="utf-8", errors="replace")))
bad = sorted(w for w in words if m._classify(w) == "unknown")
print(",".join(bad))
PY
)"
ck "severity words no controller classifies" "" "$unclassified"

echo
echo "  passed=$pass failed=$fail"
[ "$fail" -eq 0 ] || exit 1
echo "OK: a blocker blocks, an advisory stays advisory, and a new word cannot join silently."
