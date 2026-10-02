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

# 4. --expect-abbrev yes must judge EVERY journal entry, not the two the sample renders.
#    The first two keys carry shortjournal (so the rendered sample looks abbreviated); the
#    third names a journal with no shortjournal and would print its full title in the real
#    reference list. The book has no journal and must not be named. This holds with or
#    without pandoc: the scan reads only the .bib.
abbrev_dir="$(mktemp -d)"
cat > "$abbrev_dir/refs.bib" <<'BIB'
@article{alpha2020,
  title        = {A synthetic study of widget reliability},
  author       = {Alpha, Ada},
  journal      = {Synthetic Methods Quarterly},
  shortjournal = {Synth Methods Q},
  year         = {2020}
}

@article{beta2021,
  title        = {Follow-up on widget reliability},
  author       = {Beta, Boris},
  journal      = {Synthetic Reports},
  shortjournal = {Synth Rep},
  year         = {2021}
}

@article{gamma2022,
  title   = {A third synthetic widget report},
  author  = {Gamma, Grace},
  journal = {Journal of Synthetic Widget Engineering},
  year    = {2022}
}

@book{delta2019,
  title     = {A synthetic handbook},
  author    = {Delta, Dan},
  publisher = {Example Press},
  year      = {2019}
}
BIB
out="$(python3 "$SCRIPT" --csl "$CSL" --bib "$abbrev_dir/refs.bib" --expect-abbrev yes 2>&1)"; rc=$?
if [[ $rc -eq 1 && "$out" == *"gamma2022"* && "$out" != *"delta2019"* \
      && "$out" != *"alpha2020,"* && "$out" != *"Traceback"* ]]; then
  pass "--expect-abbrev yes fails on a journal entry outside the render sample, by key"
else
  bad "--expect-abbrev yes missed an unabbreviated journal entry (rc=$rc): $out"
fi
# ...and clears once every journal entry carries shortjournal (pandoc present), so the
# check is not simply failing every bib.
if command -v pandoc >/dev/null 2>&1; then
  python3 - "$abbrev_dir" <<'PY'
import pathlib, sys
d = pathlib.Path(sys.argv[1])
old = "  journal = {Journal of Synthetic Widget Engineering},\n"
text = (d / "refs.bib").read_text()
assert text.count(old) == 1
(d / "refs_filled.bib").write_text(text.replace(old, old + "  shortjournal = {J Synth Widget Eng},\n"))
PY
  out="$(python3 "$SCRIPT" --csl "$CSL" --bib "$abbrev_dir/refs_filled.bib" --expect-abbrev yes 2>&1)"; rc=$?
  if [[ $rc -eq 0 && "$out" == *'"missing_shortjournal": []'* ]]; then
    pass "--expect-abbrev yes clears when every journal entry has shortjournal"
  else
    bad "--expect-abbrev yes did not clear a filled bib (rc=$rc): $out"
  fi
fi
rm -rf "$abbrev_dir"

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

# 5. Unknown --journal key: an empty spec compared nothing and printed PASS. It is an input the
#    script does not recognise, so it exits 2 and names it. Holds without pandoc (checked first).
out="$(python3 "$SCRIPT" --csl "$CSL" --bib "$BIB" --journal jvir 2>&1)"; rc=$?
if [[ $rc -eq 2 && "$out" == *"unknown --journal 'jvir'"* && "$out" != *"PASS"* ]]; then
  pass "unknown --journal -> exit 2, named"
else
  bad "unknown --journal (rc=$rc): $out"
fi

# 6. The sample must actually cite. `"[@A; @B]".replace("@A", key)` dropped the '@', so the
#    render cited nothing: every DOI verdict was 0, every in-text verdict 'unknown'.
STYLES="$HERE/../citation_styles"
csl_check() {  # csl_check <style> [flags...] -> sets rc, out
  out="$(python3 "$SCRIPT" --csl "$STYLES/$1.csl" --bib "$BIB" "${@:2}" 2>&1)"; rc=$?
}
if command -v pandoc >/dev/null 2>&1; then
  csl_check nlm-citation-sequence --expect-doi 0
  if [[ $rc -eq 1 && "$out" == *"DOI 1 != expected 0"* ]]; then
    pass "a DOI-printing CSL fails --expect-doi 0"
  else
    bad "DOI-printing CSL vs --expect-doi 0 (rc=$rc): $out"
  fi
  csl_check vancouver-superscript --expect-intext superscript
  if [[ $rc -eq 0 && "$out" == *'"intext": "superscript"'* ]]; then
    pass "a superscript CSL is read as superscript"
  else
    bad "superscript CSL vs --expect-intext superscript (rc=$rc): $out"
  fi
  csl_check vancouver-superscript --expect-intext paren
  if [[ $rc -eq 1 && "$out" == *"in-text superscript != expected paren"* ]]; then
    pass "a superscript CSL fails --expect-intext paren"
  else
    bad "superscript CSL vs --expect-intext paren (rc=$rc): $out"
  fi
  # Negative controls: a spec the CSL does meet still passes.
  csl_check vancouver --expect-intext paren --expect-doi 1
  if [[ $rc -eq 0 && "$out" == *"PASS"* ]]; then
    pass "control: vancouver meets paren + DOI"
  else
    bad "control vancouver paren + DOI (rc=$rc): $out"
  fi
  csl_check journal-of-korean-medical-science-strict --expect-intext superscript --expect-doi 0
  if [[ $rc -eq 0 && "$out" == *"PASS"* ]]; then
    pass "control: JKMS-strict meets superscript + no DOI"
  else
    bad "control JKMS-strict superscript + no DOI (rc=$rc): $out"
  fi
  # Now that the sample renders, the DOI and full-title verdicts read the sampled entries' own
  # fields, not a word list: a title starting "Doing" is not a DOI, and a journal whose
  # abbreviation IS its title ("Radiology") is abbreviated.
  ctl_dir="$(mktemp -d)"
  cat > "$ctl_dir/refs.bib" <<'BIB'
@article{rad2020,
  title        = {Doing more with fewer contrast doses},
  author       = {Alpha, Ada},
  journal      = {Radiology},
  shortjournal = {Radiology},
  year         = {2020}
}
@article{syn2021,
  title        = {A synthetic follow-up},
  author       = {Beta, Boris},
  journal      = {Synthetic Reports},
  shortjournal = {Synth Rep},
  year         = {2021}
}
BIB
  out="$(python3 "$SCRIPT" --csl "$STYLES/journal-of-korean-medical-science-strict.csl" \
           --bib "$ctl_dir/refs.bib" --expect-doi 0 --expect-abbrev yes 2>&1)"; rc=$?
  if [[ $rc -eq 0 && "$out" == *"PASS"* ]]; then
    pass "control: 'Doing ...' is no DOI; 'Radiology' abbreviates to itself"
  else
    bad "control title/abbreviation word list (rc=$rc): $out"
  fi
  rm -rf "$ctl_dir"
  # A LaTeX-escaped '&' in the journal field: pandoc prints '&', so the full title must be compared
  # unescaped. A CSL printing the long container-title fails --expect-abbrev yes with '{\&}' exactly
  # as it does with 'and'; vancouver (short form) clears both.
  esc_dir="$(mktemp -d)"
  sed 's/<text form="short" strip-periods="true" variable="container-title"\/>/<text variable="container-title"\/>/' \
    "$STYLES/vancouver.csl" > "$esc_dir/full_title.csl"
  for jt in '{\&}' 'and'; do
    cat > "$esc_dir/refs.bib" <<BIB
@article{jv2020,
  title        = {A synthetic interventional study},
  author       = {Alpha, Ada},
  journal      = {Journal of Vascular $jt Interventional Radiology},
  shortjournal = {J Vasc Interv Radiol},
  year         = {2020}
}
BIB
    out="$(python3 "$SCRIPT" --csl "$esc_dir/full_title.csl" --bib "$esc_dir/refs.bib" --expect-abbrev yes 2>&1)"; rc=$?
    if [[ $rc -eq 1 && "$out" == *'"abbrev_full_detected": true'* ]]; then
      pass "full-title CSL fails --expect-abbrev yes (journal with '$jt')"
    else
      bad "full-title CSL with '$jt' in journal (rc=$rc): $out"
    fi
    out="$(python3 "$SCRIPT" --csl "$STYLES/vancouver.csl" --bib "$esc_dir/refs.bib" --expect-abbrev yes 2>&1)"; rc=$?
    if [[ $rc -eq 0 ]]; then
      pass "control: short-form CSL clears (journal with '$jt')"
    else
      bad "control short-form CSL with '$jt' in journal (rc=$rc): $out"
    fi
  done
  rm -rf "$esc_dir"
  csl_check vancouver --journal JKMS
  if [[ $rc -ne 2 && "$out" != *"unknown --journal"* ]]; then
    pass "--journal is matched case-insensitively"
  else
    bad "--journal JKMS (rc=$rc): $out"
  fi

  # 7. render_pandoc.sh: a key missing from the .bib renders as '(key?)'. citeproc only warns,
  #    so the wrapper used to print "[render] ok" and exit 0. It now exits 5 and names the key —
  #    including keys that start with a digit or an underscore.
  rwork="$(mktemp -d)"
  printf 'A guideline [@2019who] and [@_anon2018] and [@sample2020].\n' > "$rwork/ms.md"
  printf '@article{sample2020, author={Example, A.}, title={Synthetic study}, journal={Example Journal}, year={2020}}\n' > "$rwork/refs.bib"
  err="$(bash "$HERE/../scripts/render_pandoc.sh" -S -j vancouver -i "$rwork/ms.md" \
           -b "$rwork/refs.bib" -o "$rwork/ms.docx" 2>&1 >/dev/null)"; rc=$?
  if [[ $rc -eq 5 && "$err" == *"[@2019who]"* && "$err" == *"[@_anon2018]"* \
        && "$err" != *"[render] ok"* ]]; then
    pass "render_pandoc: unresolved citations -> exit 5, keys named"
  else
    bad "render_pandoc unresolved citations (rc=$rc): $err"
  fi
  printf '@misc{2019who, author={{Example Organization}}, title={A guideline}, year={2019}}\n@misc{_anon2018, author={Anon, A.}, title={A report}, year={2018}}\n' >> "$rwork/refs.bib"
  err="$(bash "$HERE/../scripts/render_pandoc.sh" -S -j vancouver -i "$rwork/ms.md" \
           -b "$rwork/refs.bib" -o "$rwork/ms.docx" 2>&1 >/dev/null)"; rc=$?
  if [[ $rc -eq 0 && "$err" == *"[render] ok"* ]]; then
    pass "render_pandoc control: every key defined -> exit 0"
  else
    bad "render_pandoc control (rc=$rc): $err"
  fi
  rm -rf "$rwork"
else
  echo "  SKIP  sample-citation and unresolved-citation render checks (pandoc unavailable)"
fi

if [[ $fail -eq 0 ]]; then echo "  OK"; exit 0; else echo "  $fail check(s) failed"; exit 1; fi
