#!/usr/bin/env bash
# Regression test: a Compare that fails must not leave a file where the marked manuscript goes.
#
# `run_compare` seeds `--out` with a copy of the original so Word has something to open. When the
# comparison then dies, that copy stays: a plausible .docx, of plausible size, at exactly the path
# the user asked the marked manuscript to be written to — and carrying zero tracked changes. On an
# AJNR major revision (149 paragraphs and no tables against 193 and two, i.e. a rewrite) Compare
# ran past the then-default 180-second timeout and failed -1712. The run said so, but the artifact
# it left behind could not be told apart by inspection from a revision with nothing to revise.
#
# Two things are pinned here: the failure removes the seed, and the default timeout is no longer
# the one that failed. Word itself is never invoked — `subprocess.run` and `platform.system` are
# both substituted — so this runs on CI's Linux exactly as it does on a Mac.
set -u

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
B="$REPO_ROOT/skills/sync-submission/scripts/build_marked_manuscript.py"

pass=0
fail=0
ck() {
  local label="$1" expected="$2" actual="$3"
  if [ "$expected" = "$actual" ]; then
    printf '  PASS  %-52s %s\n' "$label" "$actual"
    pass=$((pass + 1))
  else
    printf '  FAIL  %-52s expected=%s actual=%s\n' "$label" "$expected" "$actual"
    fail=$((fail + 1))
  fi
}

out="$(python3 - "$B" <<'PY'
import importlib.util, json, re, subprocess, sys, tempfile, types
from pathlib import Path

spec = importlib.util.spec_from_file_location("bmm", sys.argv[1])
m = importlib.util.module_from_spec(spec)
sys.modules["bmm"] = m
spec.loader.exec_module(m)

results = {}

# The default a user gets when they do not pass --timeout. 180 is the value that failed.
src = Path(sys.argv[1]).read_text(encoding="utf-8")
mo = re.search(r'"--timeout",\s*\n?\s*type=int,\s*\n?\s*default=(\d+)', src)
results["default_timeout"] = mo.group(1) if mo else "NOT FOUND"

m.platform = types.SimpleNamespace(system=lambda: "Darwin")


def _run_fake(returncode, stderr):
    def _fake(*a, **k):
        return subprocess.CompletedProcess(a[0] if a else [], returncode, "", stderr)
    return _fake


with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    original = td / "r0.docx"
    revised = td / "r1.docx"
    original.write_bytes(b"PK\x03\x04original")
    revised.write_bytes(b"PK\x03\x04revised")

    # 1. AppleEvent timeout: Compare needed longer than --timeout.
    out1 = td / "marked_timeout.docx"
    m.subprocess = types.SimpleNamespace(
        run=_run_fake(1, "execution error: Microsoft Word got an error: AppleEvent timed out. (-1712)"),
        TimeoutExpired=subprocess.TimeoutExpired,
    )
    try:
        m.run_compare(original, revised, out1, "A Author", 180)
        results["timeout_raised"] = "false"
        results["timeout_message"] = ""
    except SystemExit as e:
        results["timeout_raised"] = "true"
        results["timeout_message"] = str(e)
    results["timeout_left_a_file"] = str(out1.exists()).lower()

    # 2. Any other Compare failure — the seed must go too.
    out2 = td / "marked_other.docx"
    m.subprocess = types.SimpleNamespace(
        run=_run_fake(1, "execution error: Word could not open the document."),
        TimeoutExpired=subprocess.TimeoutExpired,
    )
    try:
        m.run_compare(original, revised, out2, "A Author", 600)
    except SystemExit:
        pass
    results["other_failure_left_a_file"] = str(out2.exists()).lower()

    # 3. NEGATIVE CONTROL — a Compare that SUCCEEDS must leave the file alone.
    out3 = td / "marked_ok.docx"
    m.subprocess = types.SimpleNamespace(
        run=_run_fake(0, ""), TimeoutExpired=subprocess.TimeoutExpired
    )
    m.run_compare(original, revised, out3, "A Author", 600)
    results["success_kept_the_file"] = str(out3.exists()).lower()

print(json.dumps(results))
PY
)"

get() { python3 -c "import json,sys; print(json.loads(sys.argv[1])[sys.argv[2]])" "$out" "$1"; }

echo "==== the default is no longer the one that failed ===="
ck "--timeout default"                       "600"   "$(get default_timeout)"

echo "==== a failed Compare leaves nothing to mistake for a result ===="
ck "AppleEvent timeout raises"               "true"  "$(get timeout_raised)"
ck "timeout left a file at --out"            "false" "$(get timeout_left_a_file)"
ck "other failure left a file at --out"      "false" "$(get other_failure_left_a_file)"

echo "==== NEGATIVE CONTROL — success is untouched ===="
ck "successful Compare kept its output"      "true"  "$(get success_kept_the_file)"

echo "==== the timeout failure says what to do about it ===="
msg="$(get timeout_message)"
case "$msg" in
  *--timeout*) ck "message names --timeout" "yes" "yes" ;;
  *)           ck "message names --timeout" "yes" "no  ($msg)" ;;
esac

echo
echo "  passed=$pass failed=$fail"
[ "$fail" -eq 0 ] || exit 1
echo "OK: a Compare that fails removes its seed, and the default timeout fits a real revision."
