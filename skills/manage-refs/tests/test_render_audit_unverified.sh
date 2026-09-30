#!/usr/bin/env bash
# Regression test: the pre-render reference audit does not call UNVERIFIED references "clean".
#
# render_pandoc.sh runs verify-refs without --strict, so an audit whose rows are all UNVERIFIED
# (nothing confirmed them: a made-up DOI CrossRef does not know, a title no index holds, or no
# network at all) exits 0, and the render printed "[render] reference audit: clean". It still
# renders — UNVERIFIED must not block a render made without network — but it now says how many
# references are unverified instead of calling the list clean.
#
# Cases: the real verify_refs.py run offline (so the count is parsed from the real output
# format, not a stub's), a stub with only OK rows (still clean), and a stub reporting FABRICATED
# (still blocks, exit 3). Network-free.
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RENDER="$HERE/../scripts/render_pandoc.sh"
VR_REAL="$(cd "$HERE/../../verify-refs/scripts" && pwd)/verify_refs.py"
[[ -f "$RENDER" ]] || { echo "ENV-ERR: render_pandoc.sh missing" >&2; exit 2; }
[[ -f "$VR_REAL" ]] || { echo "ENV-ERR: verify_refs.py missing" >&2; exit 2; }

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

cat > "$TMP/refs.bib" <<'EOF'
@article{synthetic2024a,
  author = {Nobody, Alpha},
  title = {A synthetic title used only by this test},
  year = {2024},
  doi = {10.0000/synthetic.0001}
}
@article{synthetic2024b,
  author = {Noone, Beta},
  title = {Another synthetic title used only by this test},
  year = {2024},
  doi = {10.0000/synthetic.0002}
}
EOF
printf '# Synthetic\n\nA sentence [@synthetic2024a; @synthetic2024b].\n' > "$TMP/ms.md"

# The real script, forced offline: every row is UNVERIFIED and it exits 0.
cat > "$TMP/vr_offline.py" <<EOF
import runpy, sys
sys.argv = ["$VR_REAL", sys.argv[1], "--offline", "--project-root", "$TMP"]
runpy.run_path("$VR_REAL", run_name="__main__")
EOF
# Stubs: print what verify_refs prints, exit as it would.
printf 'import json, sys\nprint(json.dumps({"total": 2, "counts": {"OK": 2}, "duplicate_findings_count": 0}, indent=2))\n' \
  > "$TMP/vr_ok.py"
printf 'import json, sys\nprint(json.dumps({"total": 2, "counts": {"FABRICATED": 1, "OK": 1}, "duplicate_findings_count": 0}, indent=2))\nsys.exit(1)\n' \
  > "$TMP/vr_fabricated.py"

fail=0
pass() { printf '  PASS  %s\n' "$1"; }
bad()  { printf '  FAIL  %s\n' "$1"; fail=$((fail+1)); }

render() {  # $1 = verify-refs script; prints stderr, sets rc
  err="$(cd "$TMP" && MEDSCI_VERIFY_REFS="$1" bash "$RENDER" -j vancouver -i ms.md -b refs.bib \
           -o "$TMP/out.html" 2>&1 >/dev/null)"
  rc=$?
}

echo "test_render_audit_unverified:"

render "$TMP/vr_offline.py"
if [[ "$err" == *"reference audit: NOT clean — 2 reference(s) UNVERIFIED"* \
      && "$err" != *"reference audit: clean"* ]]; then
  pass "all rows UNVERIFIED -> 'NOT clean', with the count"
else
  bad "all rows UNVERIFIED (rc=$rc): $err"
fi

render "$TMP/vr_ok.py"
if [[ "$err" == *"reference audit: clean"* && "$err" != *"NOT clean"* ]]; then
  pass "only OK rows -> clean (control)"
else
  bad "only OK rows (rc=$rc): $err"
fi

render "$TMP/vr_fabricated.py"
if [[ $rc -eq 3 && "$err" == *"ERROR: reference audit found FABRICATED"* ]]; then
  pass "FABRICATED -> render blocked, exit 3 (control)"
else
  bad "FABRICATED (rc=$rc): $err"
fi

echo
[[ $fail -eq 0 ]] && echo "ALL PASS" || echo "FAILURES: $fail"
exit "$fail"
