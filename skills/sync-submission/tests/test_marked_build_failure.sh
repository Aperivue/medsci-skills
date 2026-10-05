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
#
# Word is sandboxed, and seeding --out cured only the write: `compare ... path` still made Word READ
# the revised manuscript from a folder it was never granted, so a 300-second run sat behind a
# "Grant File Access" sheet and was then told to raise --timeout. So the build now stages BOTH files
# inside Word's own container, and this test pins that Word is never handed a path outside it, that
# the staged copies are removed on success and on failure alike, that a file an earlier run left at
# --out does not survive a failed one, and that a timeout names the dialog as well as --timeout.
# `WORD_DOCUMENTS` is pointed at a temporary folder throughout, so the real container is untouched.
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
import importlib.util, json, os, re, subprocess, sys, tempfile, types
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

STAGED = re.compile(r'open POSIX file "([^"]+)".*?path "([^"]+)"', re.S)


def _run_fake(returncode, stderr):
    def _fake(*a, **k):
        return subprocess.CompletedProcess(a[0] if a else [], returncode, "", stderr)
    return _fake


with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    container = td / "container"
    container.mkdir()
    m.WORD_DOCUMENTS = container
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

    # 4. What Word is handed. A fake Word records the two paths in the script, checks the staged
    #    copies are what they should be, and "saves" the comparison into the file it opened.
    seen = {}

    def _word(*a, **k):
        script = a[0][2]
        mo = STAGED.search(script)
        opened, compared = Path(mo.group(1)), Path(mo.group(2))
        seen["opened_in_container"] = container in opened.parents
        seen["compared_in_container"] = container in compared.parents
        seen["originals_named"] = str(original) in script or str(revised) in script
        seen["seed_is_original"] = opened.read_bytes() == original.read_bytes()
        seen["staged_is_revised"] = compared.read_bytes() == revised.read_bytes()
        opened.write_bytes(b"PK\x03\x04marked")
        return subprocess.CompletedProcess(a[0], 0, "ok", "")

    out4 = td / "marked_staged.docx"
    m.subprocess = types.SimpleNamespace(run=_word, TimeoutExpired=subprocess.TimeoutExpired)
    m.run_compare(original, revised, out4, "A Author", 600)
    for k, v in seen.items():
        results[k] = str(v).lower()
    results["out_is_word_output"] = str(out4.read_bytes() == b"PK\x03\x04marked").lower()
    results["container_empty_after_success"] = str(not any(container.iterdir())).lower()

    # 5. A failed run: the staging goes, a file an earlier run left at --out goes, and the timeout
    #    message names a waiting dialog as well as --timeout.
    out5 = td / "marked_stale.docx"
    out5.write_bytes(b"PK\x03\x04from-an-earlier-run")
    m.subprocess = types.SimpleNamespace(
        run=_run_fake(1, "execution error: Microsoft Word got an error: AppleEvent timed out. (-1712)"),
        TimeoutExpired=subprocess.TimeoutExpired,
    )
    try:
        m.run_compare(original, revised, out5, "A Author", 300)
        msg5 = ""
    except SystemExit as e:
        msg5 = str(e)
    results["stale_out_survived_failure"] = str(out5.exists()).lower()
    results["container_empty_after_failure"] = str(not any(container.iterdir())).lower()
    results["timeout_names_dialog"] = str("dialog" in msg5).lower()

    # 6. No container (Word never launched): stage beside --out, warn, and still clean up.
    m.WORD_DOCUMENTS = td / "no-such-container"
    side = td / "side"
    side.mkdir()
    out6 = side / "marked_fallback.docx"
    m.subprocess = types.SimpleNamespace(run=_run_fake(0, ""), TimeoutExpired=subprocess.TimeoutExpired)
    m.run_compare(original, revised, out6, "A Author", 600)
    results["fallback_kept_the_file"] = str(out6.exists()).lower()
    results["fallback_left_staging"] = str(any(p.name.startswith(".medsci-marked-") for p in side.iterdir())).lower()

    # 7. --out that IS an input is refused before anything is deleted — by path, via a symlink,
    #    and via a hard link. The input must survive byte for byte.
    m.WORD_DOCUMENTS = container
    m.subprocess = types.SimpleNamespace(run=_run_fake(0, ""), TimeoutExpired=subprocess.TimeoutExpired)
    link_sym = td / "link_sym.docx"
    link_sym.symlink_to(original)
    link_hard = td / "link_hard.docx"
    os.link(revised, link_hard)
    for key, target in (("out_is_original", original), ("out_is_revised", revised),
                        ("out_symlinks_original", link_sym), ("out_hardlinks_revised", link_hard)):
        before_o, before_r = original.read_bytes(), revised.read_bytes()
        try:
            m.run_compare(original, revised, target, "A Author", 600)
            refused = False
        except SystemExit:
            refused = True
        except Exception:          # a crash is not a refusal (the old script raised SameFileError)
            refused = False
        intact = (original.exists() and original.read_bytes() == before_o
                  and revised.exists() and revised.read_bytes() == before_r)
        results[key] = str(refused and intact).lower()

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

case "$msg" in
  *Grant\ File\ Access*|*dialog*) ck "message names a waiting dialog" "yes" "yes" ;;
  *)                               ck "message names a waiting dialog" "yes" "no  ($msg)" ;;
esac

echo "==== Word is handed only paths inside its own container ===="
ck "opened file is inside the container"     "true"  "$(get opened_in_container)"
ck "compared file is inside the container"   "true"  "$(get compared_in_container)"
ck "script names an original input path"     "false" "$(get originals_named)"
ck "seed is a copy of --original"            "true"  "$(get seed_is_original)"
ck "staged copy is --revised"                "true"  "$(get staged_is_revised)"
ck "--out holds what Word saved"             "true"  "$(get out_is_word_output)"

echo "==== the staged manuscript copies do not outlive the run ===="
ck "container empty after success"           "true"  "$(get container_empty_after_success)"
ck "container empty after failure"           "true"  "$(get container_empty_after_failure)"
ck "earlier run's --out survived a failure"  "false" "$(get stale_out_survived_failure)"
ck "300s timeout message names the dialog"   "true"  "$(get timeout_names_dialog)"

echo "==== --out that is an input is refused, inputs intact ===="
ck "--out == --original"                     "true"  "$(get out_is_original)"
ck "--out == --revised"                      "true"  "$(get out_is_revised)"
ck "--out symlinks --original"               "true"  "$(get out_symlinks_original)"
ck "--out hard-links --revised"              "true"  "$(get out_hardlinks_revised)"

echo "==== no container: fall back beside --out, still clean ===="
ck "fallback produced --out"                 "true"  "$(get fallback_kept_the_file)"
ck "fallback left a staging folder"          "false" "$(get fallback_left_staging)"

echo
echo "  passed=$pass failed=$fail"
[ "$fail" -eq 0 ] || exit 1
echo "OK: a Compare that fails removes its seed, Word only sees its own container, and the timeout names both causes."
