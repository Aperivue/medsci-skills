#!/usr/bin/env bash
# Regression test for fill_icmje_coi.py (per-author ICMJE COI form cloning).
# Clones the shipped synthetic seed for two authors and asserts the documented
# contract on each output: 14 checked boxes, 13 "None" disclosures, the new
# title/date substituted, the author name present, and NO leakage of the seed
# placeholder strings. The seed-clone path is stdlib (zipfile) only and
# network-free. Hangul-free (the only non-ASCII char is the checkbox glyph
# U+2612, which the locale-inventory gate does not flag).
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL="$HERE/.."
SCRIPT="$SKILL/scripts/fill_icmje_coi.py"
SEED="$SKILL/templates/icmje_coi_seed_synthetic.docx"
OUTDIR="$(mktemp -d -t icmje_XXXX)"
trap 'rm -rf "$OUTDIR"' EXIT

fail=0
check() { local label="$1"; shift
    if "$@" >/dev/null 2>&1; then printf '  PASS  %s\n' "$label"
    else printf '  FAIL  %s\n' "$label"; fail=$((fail+1)); fi
}

[[ -f "$SCRIPT" ]] || { echo "ENV-ERR: fill_icmje_coi.py missing" >&2; exit 2; }
[[ -f "$SEED" ]]   || { echo "ENV-ERR: synthetic seed missing"   >&2; exit 2; }

NEW_TITLE="Diagnostic Accuracy of Synthetic Test Imaging"
NEW_DATE="June 20, 2026"

python3 "$SCRIPT" \
    --seed "$SEED" \
    --seed-name "Placeholder Author" \
    --seed-title "Placeholder Manuscript Title" \
    --seed-date "January 1, 2000" \
    --new-title "$NEW_TITLE" \
    --new-date "$NEW_DATE" \
    --out-dir "$OUTDIR" \
    --authors '[[1,"Alice Kim"],[2,"Bob Lee"]]' >/dev/null 2>&1
check "CLI exit 0" test "$?" -eq 0

# Two output docx, author names in filenames.
check "two forms written" test "$(ls "$OUTDIR"/*.docx 2>/dev/null | wc -l)" -eq 2
DOC1="$OUTDIR/ICMJE_COI_01_Alice_Kim.docx"
DOC2="$OUTDIR/ICMJE_COI_02_Bob_Lee.docx"
check "author 1 file named" test -f "$DOC1"
check "author 2 file named" test -f "$DOC2"

# Per-document contract checks (read word/document.xml from the zip).
assert_doc() {  # $1=docx  $2=expected author name
    local doc="$1" name="$2"
    python3 - "$doc" "$name" "$NEW_TITLE" "$NEW_DATE" <<'PY'
import sys, zipfile
doc, name, title, date = sys.argv[1:5]
xml = zipfile.ZipFile(doc).read("word/document.xml").decode("utf-8")
checked = xml.count("☒")      # checked box glyph (U+2612)
none = xml.count(">None<") + xml.count(">None ")
assert checked == 14, f"checked boxes={checked} (want 14)"
assert none == 13, f"None disclosures={none} (want 13)"
assert title in xml, "new title not substituted"
assert date in xml, "new date not substituted"
assert name in xml, f"author name {name!r} absent"
for ph in ("Placeholder Author", "Placeholder Manuscript Title", "January 1, 2000"):
    assert ph not in xml, f"placeholder leaked: {ph!r}"
PY
}
check "doc1 contract (14 boxes / 13 None / subst / no leak)" assert_doc "$DOC1" "Alice Kim"
check "doc2 contract (14 boxes / 13 None / subst / no leak)" assert_doc "$DOC2" "Bob Lee"

# --- F1 regression: an empty seed/new string must be refused, never skipped. ---
# Custom seed: the shipped synthetic seed with its author renamed to "J Park".
CSEED="$OUTDIR/custom_seed.docx"
python3 - "$SEED" "$CSEED" <<'PY'
import sys, zipfile
src, dst = sys.argv[1:3]
with zipfile.ZipFile(src) as zin, zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout:
    for it in zin.infolist():
        d = zin.read(it.filename)
        if it.filename == "word/document.xml":
            d = d.decode("utf-8").replace("Placeholder Author", "J Park").encode("utf-8")
        zout.writestr(it, d)
PY

run_custom() {  # $1=out dir  $2=--seed-name  $3=--new-title ; prints exit code
    python3 "$SCRIPT" --seed "$CSEED" --seed-name "$2" \
        --seed-title "Placeholder Manuscript Title" --seed-date "January 1, 2000" \
        --new-title "$3" --new-date "$NEW_DATE" --out-dir "$1" \
        --authors '[[1,"Alice Kim"],[2,"Bob Lee"]]' >/dev/null 2>&1
    echo "$?"
}

# POSITIVE: empty --seed-name used to exit 0 with "J Park" in every form.
E1="$OUTDIR/empty_seed_name"
check "empty --seed-name exits 2" test "$(run_custom "$E1" "" "$NEW_TITLE")" -eq 2
check "empty --seed-name writes no form" test "$(ls "$E1"/*.docx 2>/dev/null | wc -l)" -eq 0

# POSITIVE: empty --new-title used to exit 0 with the title blanked.
E2="$OUTDIR/empty_new_title"
check "empty --new-title exits 2" test "$(run_custom "$E2" "J Park" "")" -eq 2
check "empty --new-title writes no form" test "$(ls "$E2"/*.docx 2>/dev/null | wc -l)" -eq 0

# NEGATIVE control: the same custom seed with its real seed name stays clean.
E3="$OUTDIR/custom_ok"
check "custom seed with seed name exits 0" test "$(run_custom "$E3" "J Park" "$NEW_TITLE")" -eq 0
custom_clean() {
    python3 - "$E3/ICMJE_COI_01_Alice_Kim.docx" "$E3/ICMJE_COI_02_Bob_Lee.docx" <<'PY'
import sys, zipfile
for f, name in zip(sys.argv[1:], ("Alice Kim", "Bob Lee")):
    xml = zipfile.ZipFile(f).read("word/document.xml").decode("utf-8")
    assert "J Park" not in xml and name in xml, f
PY
}
check "custom seed: seed name replaced, author present" custom_clean

echo "fail=$fail"; [[ "$fail" -eq 0 ]] && echo "ALL PASS" || echo "FAILURES: $fail"
exit "$fail"
