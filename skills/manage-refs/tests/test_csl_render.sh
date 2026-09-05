#!/usr/bin/env bash
# Regression test for the hardened CSL acceptance-check (manage-refs/check_csl_render.py).
# Guards the robustness fixes (no module globals, checked subprocess, no temp leak,
# guarded python-docx import, guarded bib read). Synthetic, PII-free fixtures.
#
# CI-safe: the deepest path (real pandoc render → docx superscript parse) needs
# pandoc, which CI does not install. The error-handling paths this test asserts
# do NOT need pandoc, and the no-pandoc branch is exercised exactly when pandoc is
# absent (i.e. in CI), so fix #2 (clean "pandoc not found") is covered there while
# fixes #1/#3/#4 (the happy path) are covered wherever pandoc is present (locally).
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$HERE/../scripts/check_csl_render.py"
CSL="$HERE/../citation_styles/vancouver.csl"
BIB="$HERE/fixtures/csl_render_sample.bib"

[[ -f "$SCRIPT" ]] || { echo "ENV-ERR: script missing: $SCRIPT" >&2; exit 2; }
[[ -f "$CSL"    ]] || { echo "ENV-ERR: csl missing: $CSL" >&2; exit 2; }
[[ -f "$BIB"    ]] || { echo "ENV-ERR: fixture bib missing: $BIB" >&2; exit 2; }

fail=0
pass() { printf '  PASS  %s\n' "$1"; }
bad()  { printf '  FAIL  %s\n' "$1"; fail=$((fail+1)); }

echo "test_csl_render:"

# 1. Missing bib -> clean error (fix: guarded bib read), exit 2, no traceback.
err="$(python3 "$SCRIPT" --csl "$CSL" --bib /nonexistent_csl_render.bib 2>&1)"; rc=$?
if [[ $rc -eq 2 && "$err" == *"bib file not found"* && "$err" != *"Traceback"* ]]; then
  pass "missing bib -> clean error, exit 2"
else
  bad "missing bib (rc=$rc): $err"
fi

# 2. Valid bib: pandoc present -> happy path renders, exit 0 + JSON.
#    pandoc absent (e.g. CI) -> clean 'pandoc not found' error, exit 2.
out="$(python3 "$SCRIPT" --csl "$CSL" --bib "$BIB" 2>&1)"; rc=$?
if command -v pandoc >/dev/null 2>&1; then
  if [[ $rc -eq 0 && "$out" == *'"got"'* && "$out" != *"Traceback"* ]]; then
    pass "valid bib + pandoc -> renders, exit 0, JSON emitted"
  else
    bad "valid bib + pandoc (rc=$rc): $out"
  fi
else
  if [[ $rc -eq 2 && "$out" == *"pandoc not found"* && "$out" != *"Traceback"* ]]; then
    pass "valid bib, no pandoc -> clean 'pandoc not found', exit 2"
  else
    bad "valid bib, no pandoc (rc=$rc): $out"
  fi
fi

# 3. No leftover temp dirs from this run (fix: TemporaryDirectory cleanup).
if ls -d "${TMPDIR:-/tmp}"/csl_render_* >/dev/null 2>&1; then
  bad "temp dir leak: csl_render_* left behind"
else
  pass "no temp-dir leak"
fi

# The production wrapper must keep citation rendering intact while removing
# source locations from custom Word properties. A real render exercises filter
# ordering: stripping bibliography before citeproc would lose the reference.
if command -v pandoc >/dev/null 2>&1; then
  work="$(mktemp -d)"
  trap 'rm -rf "$work"' EXIT
  printf 'A synthetic citation [@sample2020].\n' > "$work/manuscript.md"
  printf '@article{sample2020, author={Example, A.}, title={Synthetic study}, journal={Example Journal}, year={2020}}\n' > "$work/refs.bib"
  bash "$HERE/../scripts/render_pandoc.sh" -S -j vancouver -i "$work/manuscript.md" \
    -b "$work/refs.bib" -o "$work/manuscript.docx" >/dev/null 2>&1
  python3 - "$work/manuscript.docx" <<'PY'
import sys, zipfile
with zipfile.ZipFile(sys.argv[1]) as z:
    body = z.read("word/document.xml").decode()
    custom = z.read("docProps/custom.xml").decode() if "docProps/custom.xml" in z.namelist() else ""
assert "Synthetic study" in body, "citeproc did not render the reference"
assert 'name="csl"' not in custom and 'name="bibliography"' not in custom
PY
  [[ $? -eq 0 ]] && pass "rendered references survive; source-path properties do not" \
    || bad "source metadata removal broke rendering or missed a property"
else
  echo "  SKIP  source-property render check (pandoc unavailable)"
fi

if [[ $fail -eq 0 ]]; then echo "  OK"; exit 0; else echo "  $fail check(s) failed"; exit 1; fi
