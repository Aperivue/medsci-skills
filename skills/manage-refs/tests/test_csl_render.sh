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

# 2. Valid bib: pandoc present -> renders and emits JSON. With no expectation given nothing is
#    compared, so the run ends NOT_ASSESSED with exit 2; it used to print PASS and exit 0, which
#    reads exactly like a passed check.
#    pandoc absent (e.g. CI) -> clean 'pandoc not found' error, exit 2.
out="$(python3 "$SCRIPT" --csl "$CSL" --bib "$BIB" 2>&1)"; rc=$?
if command -v pandoc >/dev/null 2>&1; then
  if [[ $rc -eq 2 && "$out" == *'"got"'* && "$out" == *"NOT_ASSESSED"* && "$out" != *"PASS"* \
        && "$out" != *"Traceback"* ]]; then
    pass "valid bib + pandoc, no expectation -> JSON emitted, NOT_ASSESSED, exit 2"
  else
    bad "valid bib + pandoc, no expectation (rc=$rc): $out"
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
  # A full journal title contained in its own abbreviation ("Cancers" in "Cancers (Basel)"): a
  # correct short-form render always contains the full title, so the verdict is NOT_ASSESSED, never
  # FAIL. main cleared these (exit 0) and so must this; the entries are named in a minor note.
  sub_dir="$(mktemp -d)"
  cat > "$sub_dir/refs.bib" <<'BIB'
@article{can2020,
  title        = {A synthetic tumour cohort},
  author       = {Alpha, Ada},
  journal      = {Cancers},
  shortjournal = {Cancers (Basel)},
  year         = {2020},
  doi          = {10.1234/can.2020.001}
}
@article{dia2021,
  title        = {A synthetic imaging cohort},
  author       = {Beta, Boris},
  journal      = {Diagnostics},
  shortjournal = {Diagnostics (Basel)},
  year         = {2021},
  doi          = {10.1234/dia.2021.002}
}
@article{med2022,
  title        = {A synthetic registry},
  author       = {Gamma, Grace},
  journal      = {Medicine},
  shortjournal = {Medicine (Baltimore)},
  year         = {2022},
  doi          = {10.1234/med.2022.003}
}
BIB
  for flags in "--expect-abbrev yes" "--journal radiology"; do
    # shellcheck disable=SC2086
    out="$(python3 "$SCRIPT" --csl "$STYLES/vancouver.csl" --bib "$sub_dir/refs.bib" $flags 2>&1)"; rc=$?
    if [[ $rc -eq 0 && "$out" == *'"abbrev_full_detected": false'* && "$out" == *"NOT_ASSESSED"* \
          && "$out" != *"journal names appear FULL"* ]]; then
      pass "full title inside its own abbreviation -> NOT_ASSESSED, exit 0 ($flags)"
    else
      bad "full title inside its own abbreviation ($flags) (rc=$rc): $out"
    fi
  done
  # The journal name as words of the article title is not the container title: the short-form CSL
  # clears (main: exit 0), and a CSL that does print the long title still fails.
  sed 's/<text form="short" strip-periods="true" variable="container-title"\/>/<text variable="container-title"\/>/' \
    "$STYLES/vancouver.csl" > "$sub_dir/full_title.csl"
  cat > "$sub_dir/title.bib" <<'BIB'
@article{syn2021,
  title        = {Synthetic reports of widget reliability},
  author       = {Beta, Boris},
  journal      = {Synthetic Reports},
  shortjournal = {Synth Rep},
  year         = {2021},
  doi          = {10.1234/sr.2021.002}
}
BIB
  out="$(python3 "$SCRIPT" --csl "$STYLES/vancouver.csl" --bib "$sub_dir/title.bib" --expect-abbrev yes 2>&1)"; rc=$?
  if [[ $rc -eq 0 && "$out" == *'"abbrev_full_detected": false'* ]]; then
    pass "control: journal name in the article title is not a full container title"
  else
    bad "journal name in article title, short-form CSL (rc=$rc): $out"
  fi
  out="$(python3 "$SCRIPT" --csl "$sub_dir/full_title.csl" --bib "$sub_dir/title.bib" --expect-abbrev yes 2>&1)"; rc=$?
  if [[ $rc -eq 1 && "$out" == *'"abbrev_full_detected": true'* ]]; then
    pass "full-title CSL still fails when the journal name is also in the article title"
  else
    bad "journal name in article title, full-title CSL (rc=$rc): $out"
  fi
  # A CSL-JSON bibliography is not BibTeX: there is nothing to sample, so the check says so (exit 2)
  # instead of rendering a sample that cites nothing and printing PASS.
  printf '[{"id":"cj2020","type":"article-journal","title":"A synthetic study","container-title":"Synthetic Reports","issued":{"date-parts":[[2020]]}}]\n' \
    > "$sub_dir/refs.json"
  out="$(python3 "$SCRIPT" --csl "$STYLES/vancouver.csl" --bib "$sub_dir/refs.json" 2>&1)"; rc=$?
  if [[ $rc -eq 2 && "$out" == *"no bibliography entries found"* && "$out" != *"PASS"* ]]; then
    pass "CSL-JSON --bib -> exit 2, nothing to render"
  else
    bad "CSL-JSON --bib (rc=$rc): $out"
  fi
  rm -rf "$sub_dir"
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

# 8. Scope and preprints. A real .bib holds entries the manuscript no longer cites, and preprints whose
#    "journal" is a server with no abbreviation. Counting either as a missing shortjournal kept the
#    check red on a bib whose cited journal entries were all abbreviated, and a red that cannot go
#    green is a check nobody runs. --md reads the citations through pandoc, so those checks need it;
#    without pandoc, --md must refuse (exit 2) rather than guess the scope.
scope_dir="$(mktemp -d)"
cat > "$scope_dir/refs.bib" <<'BIB'
@article{citedA2020,
  title   = {A cited synthetic study},
  author  = {Alpha, Ada},
  journal = {Journal of Synthetic Methods},
  year    = {2020},
  doi     = {10.1234/jsm.2020.001}
}
@article{uncitedB2021,
  title   = {An uncited synthetic study},
  author  = {Beta, Boris},
  journal = {Synthetic Reports},
  year    = {2021}
}
@article{preprintC2026,
  title   = {A synthetic preprint},
  author  = {Gamma, Grace},
  journal = {arXiv},
  date    = {2026-04-22},
  doi     = {10.48550/arXiv.0000.00000}
}
BIB
printf 'Cited [@citedA2020; @preprintC2026].\n' > "$scope_dir/ms.md"
# The verdict is read from the FAIL line alone: the JSON above it lists the sampled keys.
out="$(python3 "$SCRIPT" --csl "$STYLES/elsevier-vancouver.csl" --bib "$scope_dir/refs.bib" \
         --md "$scope_dir/ms.md" --expect-abbrev yes 2>&1)"; rc=$?
failline="$(printf '%s\n' "$out" | grep '^FAIL:')"
if ! command -v pandoc >/dev/null 2>&1; then
  if [[ $rc -eq 2 && "$out" == *"--md needs pandoc"* ]]; then
    pass "--md without pandoc -> refuses, exit 2"
  else
    bad "--md without pandoc (rc=$rc): $out"
  fi
elif [[ $rc -eq 1 && "$failline" == *"1 journal entry without shortjournal"*"citedA2020"* \
      && "$failline" != *"uncitedB2021"* && "$failline" != *"preprintC2026"* ]]; then
  pass "--md: a cited journal entry is named; uncited and arXiv entries are not"
else
  bad "--md scope / preprint exemption (rc=$rc): $out"
fi
# Without --md the whole bib is judged, so the uncited entry is named too (the old behaviour, kept).
out="$(python3 "$SCRIPT" --csl "$STYLES/elsevier-vancouver.csl" --bib "$scope_dir/refs.bib" \
         --expect-abbrev yes 2>&1)"; rc=$?
failline="$(printf '%s\n' "$out" | grep '^FAIL:')"
if [[ $rc -eq 1 && "$failline" == *"uncitedB2021"* && "$failline" == *"citedA2020"* \
      && "$failline" != *"preprintC2026"* ]]; then
  pass "no --md: the whole bib is judged; the arXiv entry is still exempt"
else
  bad "whole-bib scope (rc=$rc): $out"
fi
# What counts as cited is what pandoc cites: a key inside an HTML comment is not cited, and a key
# with internal punctuation (`smith?2020`) is cited whole. A regex over the raw text got both wrong.
cat >> "$scope_dir/refs.bib" <<'BIB'
@article{smith?2020,
  title   = {A synthetic study with an unusual key},
  author  = {Smith, Sam},
  journal = {Synthetic Letters},
  year    = {2020}
}
@article{commented2019,
  title   = {A study mentioned only in a comment},
  author  = {Delta, Dan},
  journal = {Synthetic Notes},
  year    = {2019}
}
BIB
printf 'Cited [@smith?2020]. Literal: `[@commented2019]`.\n\n<!-- [@commented2019] -->\n' > "$scope_dir/ms_keys.md"
if command -v pandoc >/dev/null 2>&1; then
  out="$(python3 "$SCRIPT" --csl "$STYLES/elsevier-vancouver.csl" --bib "$scope_dir/refs.bib" \
           --md "$scope_dir/ms_keys.md" --expect-abbrev yes 2>&1)"; rc=$?
  failline="$(printf '%s\n' "$out" | grep '^FAIL:')"
  if [[ $rc -eq 1 && "$failline" == *"smith?2020"* && "$failline" != *"commented2019"* ]]; then
    pass "--md: a key with internal punctuation is cited; one in a comment or inline code is not"
  else
    bad "--md citation parsing (rc=$rc): $out"
  fi
  # nocite '@*' puts every entry into the reference list, so the whole bib is judged.
  printf -- '---\nnocite: |\n  @*\n---\nCited [@smith?2020].\n' > "$scope_dir/ms_nocite.md"
  out="$(python3 "$SCRIPT" --csl "$STYLES/elsevier-vancouver.csl" --bib "$scope_dir/refs.bib" \
           --md "$scope_dir/ms_nocite.md" --expect-abbrev yes 2>&1)"; rc=$?
  failline="$(printf '%s\n' "$out" | grep '^FAIL:')"
  if [[ $rc -eq 1 && "$failline" == *"uncitedB2021"* && "$failline" == *"commented2019"* \
        && "$out" == *"nocite"* ]]; then
    pass "--md with nocite '@*' judges the whole bib"
  else
    bad "--md with nocite '@*' (rc=$rc): $out"
  fi
fi
# `--expect-abbrev no` ("full names acceptable") asks for no check: alone, it compares nothing.
out="$(python3 "$SCRIPT" --csl "$CSL" --bib "$BIB" --expect-abbrev no 2>&1)"; rc=$?
if [[ $rc -eq 2 && "$out" != *"PASS"* ]] && { ! command -v pandoc >/dev/null 2>&1 || [[ "$out" == *"NOT_ASSESSED"* ]]; }; then
  pass "--expect-abbrev no alone -> nothing compared, not PASS"
else
  bad "--expect-abbrev no alone (rc=$rc): $out"
fi
if command -v pandoc >/dev/null 2>&1; then
  # With the cited entry abbreviated, the render sample holds it and the arXiv entry: "arXiv" printed
  # in full is correct and must not read as an unabbreviated journal.
  python3 - "$scope_dir" <<'PY'
import pathlib, sys
d = pathlib.Path(sys.argv[1])
old = "  journal = {Journal of Synthetic Methods},\n"
text = (d / "refs.bib").read_text()
assert text.count(old) == 1
(d / "refs.bib").write_text(text.replace(old, old + "  shortjournal = {J Synth Methods},\n"))
PY
  out="$(python3 "$SCRIPT" --csl "$STYLES/elsevier-vancouver.csl" --bib "$scope_dir/refs.bib" \
           --md "$scope_dir/ms.md" --expect-abbrev yes 2>&1)"; rc=$?
  if [[ $rc -eq 0 && "$out" == *'"abbrev_full_detected": false'* && "$out" == *'"preprintC2026"'* \
        && "$out" == *'"scope": "cited keys"'* ]]; then
    pass "an arXiv entry in the render sample is not an unabbreviated journal"
  else
    bad "arXiv entry in the render sample (rc=$rc): $out"
  fi

  # 9. The JMIR spec: bracketed numbers and abbreviated journal names. JMIR accepts a PMID *or* a DOI,
  #    so a PMID-only entry must not fail on DOI (a spec asserting DOI did exactly that).
  cat > "$scope_dir/pmid.bib" <<'BIB'
@article{pmidOnly2019,
  title        = {A synthetic PubMed-indexed study},
  author       = {Delta, Dan},
  journal      = {Journal of Synthetic Methods},
  shortjournal = {J Synth Methods},
  year         = {2019},
  pmid         = {10000000}
}
BIB
  out="$(python3 "$SCRIPT" --csl "$STYLES/elsevier-vancouver.csl" --bib "$scope_dir/pmid.bib" --journal jmir 2>&1)"; rc=$?
  if [[ $rc -eq 0 && "$out" == *"PASS"* && "$out" != *"DOI 0 != expected"* ]]; then
    pass "--journal jmir: a PMID-only entry passes (DOI not asserted)"
  else
    bad "--journal jmir, PMID-only entry (rc=$rc): $out"
  fi
  # ...and the same spec still fails a full journal name, and a parenthesised in-text style.
  sed 's/  shortjournal = {J Synth Methods},//' "$scope_dir/pmid.bib" > "$scope_dir/pmid_full.bib"
  out="$(python3 "$SCRIPT" --csl "$STYLES/elsevier-vancouver.csl" --bib "$scope_dir/pmid_full.bib" --journal jmir 2>&1)"; rc=$?
  if [[ $rc -eq 1 && "$out" == *"pmidOnly2019"* ]]; then
    pass "--journal jmir fails an entry without shortjournal"
  else
    bad "--journal jmir, missing shortjournal (rc=$rc): $out"
  fi
  out="$(python3 "$SCRIPT" --csl "$STYLES/vancouver.csl" --bib "$scope_dir/pmid.bib" --journal jmir 2>&1)"; rc=$?
  if [[ $rc -eq 1 && "$out" == *"in-text paren != expected bracket"* ]]; then
    pass "--journal jmir fails a parenthesised in-text style"
  else
    bad "--journal jmir, parenthesised style (rc=$rc): $out"
  fi
else
  echo "  SKIP  render-sample preprint and JMIR spec checks (pandoc unavailable)"
fi
rm -rf "$scope_dir"

if [[ $fail -eq 0 ]]; then echo "  OK"; exit 0; else echo "  $fail check(s) failed"; exit 1; fi
