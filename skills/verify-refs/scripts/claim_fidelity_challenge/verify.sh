#!/usr/bin/env bash
# Deterministic verifier for the claim-fidelity challenge card.
#
# The failure this gate exists to catch was found by a human co-author, not by the toolkit. A
# manuscript sentence read "the field has begun to offer the chair [41]". The cited work uses
# "chair" zero times and "advocate" four times, twice in the sense the sentence was reaching
# for. Every existing gate passed: the DOI resolved, the authors matched, the reference list
# rendered. Nothing checked whether the source says what the sentence says it says.
#
# So the positive fixtures reproduce that shape across all three probes:
#   an attributed concept the source never uses          -> ATTRIBUTION_UNSUPPORTED
#   a quotation the source does not contain              -> CITED_QUOTE_ABSENT
#   a count the source never states beside that noun     -> ORDINAL_CLAIM_UNSUPPORTED
#
# And — the half that decides whether this gate is usable at all — the negative fixtures are
# the cases where firing would be WRONG:
#   a real paraphrase, worded nothing like the source, that keeps one of its terms
#   a correct quote read through a DIRTY EXTRACTION (line numbers and a bled reference wedged
#     mid-sentence). A contiguous substring test calls that absent; that assumption produced
#     thirteen false absences in one day and came one step from having two accurate quotes
#     deleted. This gate inherits _quote_match.py precisely so it cannot repeat that, and the
#     test below is what proves the inheritance is live rather than nominal.
#   a source whose extracted text is an abstract — absence proves nothing against it
#   a citation with no full text at all — counted as unchecked, never guessed at
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
DET="$HERE/../check_claim_fidelity.py"
FIX="$HERE/fixture"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

pass=0; fail=0
ck() { if [ "$2" = "$3" ]; then printf '  PASS  %-56s exit=%s\n' "$1" "$3"; pass=$((pass+1));
       else printf '  FAIL  %-56s want=%s got=%s\n' "$1" "$2" "$3"; fail=$((fail+1)); fi; }
has() { if echo "$2" | grep -q "$3"; then ck "$1" 0 0; else ck "$1" 0 1; fi; }
hasnt() { if echo "$2" | grep -q "$3"; then ck "$1" 0 1; else ck "$1" 0 0; fi; }

run() { python3 "$DET" "$@" 2>&1; }

echo "== positive: claims the cited source does not support =="
run --manuscript "$FIX/manuscript_unsupported.md" --fulltext-dir "$FIX/fulltext" \
    --bib "$FIX/refs.bib" --strict >/dev/null 2>&1
ck "unsupported manuscript -> --strict fails" 1 "$?"

OUT="$(run --manuscript "$FIX/manuscript_unsupported.md" --fulltext-dir "$FIX/fulltext" --bib "$FIX/refs.bib")"
has "the fabricated quotation is named"        "$OUT" "CITED_QUOTE_ABSENT"
has "the unsupported concept is named"         "$OUT" "ATTRIBUTION_UNSUPPORTED"
has "the miscounted claim is named"            "$OUT" "ORDINAL_CLAIM_UNSUPPORTED"
has "the offending term is quoted back"        "$OUT" "chair"

echo "== negative: supported claims, including a genuine paraphrase =="
run --manuscript "$FIX/manuscript_supported.md" --fulltext-dir "$FIX/fulltext" \
    --bib "$FIX/refs.bib" --strict >/dev/null 2>&1
ck "supported manuscript -> silent" 0 "$?"
OUT="$(run --manuscript "$FIX/manuscript_supported.md" --fulltext-dir "$FIX/fulltext" --bib "$FIX/refs.bib")"
hasnt "a paraphrase does not fire"              "$OUT" "ATTRIBUTION_UNSUPPORTED"
hasnt "a correct count does not fire"           "$OUT" "ORDINAL_CLAIM"
has   "the claims were actually examined"       "$OUT" "checked 1 quote"

echo "== the hand-numbered path: [N] resolved from a wrapped reference list, no .bib =="
OUT="$(run --manuscript "$FIX/manuscript_numbered.md" --fulltext-dir "$FIX/fulltext")"
has "a wrapped [N] entry still resolves"        "$OUT" "1 source(s) resolved"
has "and the same claim is caught"              "$OUT" "ATTRIBUTION_UNSUPPORTED"

echo "== negative: absence against an abstract-only extraction proves nothing =="
run --manuscript "$FIX/manuscript_shortsource.md" --fulltext-dir "$FIX/fulltext" \
    --bib "$FIX/refs.bib" --strict >/dev/null 2>&1
ck "abstract-only source -> silent" 0 "$?"
OUT="$(run --manuscript "$FIX/manuscript_shortsource.md" --fulltext-dir "$FIX/fulltext" --bib "$FIX/refs.bib")"
hasnt "and does not accuse on that evidence"    "$OUT" "ATTRIBUTION_UNSUPPORTED"
has   "it says why it stayed silent"            "$OUT" "too short to judge absence"

echo "== negative: a correct quote read through a DIRTY extraction (substrate inheritance) =="
# Rebuild the source the way an extractor mangles it: a PDF line number and a bled two-column
# reference land inside the quoted sentence. The words are all there, in order, interrupted.
mkdir -p "$TMP/fulltext"
cp "$FIX/fulltext/"*.md "$TMP/fulltext/"
python3 - "$FIX/fulltext/10.1000_synthetic.oversight.md" "$TMP/fulltext/10.1000_synthetic.dirty.md" <<'PY'
import sys
src, dst = sys.argv[1], sys.argv[2]
text = open(src, encoding="utf-8").read()
clean = "Automated advice should be withheld so long as the reader has not recorded an initial\nimpression."
dirty = ("Automated advice should be withheld so long as 86 the reader has not\n"
         "J Synth Workflow Res. 2025;1:10-11.\nrecorded an initial impression.")
assert clean in text, "fixture drifted: the quoted sentence is no longer in the source"
open(dst, "w", encoding="utf-8").write(text.replace(clean, dirty))
PY
cat > "$TMP/manuscript_dirty.md" <<'EOF'
# Reader independence in automated reporting workflows

Doe and colleagues state that "Automated advice should be withheld so long as the reader has
not recorded an initial impression" [1].

## References

1. Doe J, Roe A. Preserving reader independence when an automated second opinion is available.
   J Synth Workflow Res. 2025;1:1-9. doi:10.1000/synthetic.dirty
EOF
python3 "$DET" --manuscript "$TMP/manuscript_dirty.md" --fulltext-dir "$TMP/fulltext" --strict >/dev/null 2>&1
ck "a correct quote through a dirty extraction -> silent" 0 "$?"
OUT="$(run --manuscript "$TMP/manuscript_dirty.md" --fulltext-dir "$TMP/fulltext")"
hasnt "and is NOT called a fabrication"          "$OUT" "CITED_QUOTE_ABSENT"
has   "the quote was genuinely examined"         "$OUT" "checked 1 quote"

echo "== a rewritten quotation, at both sides of the tolerance boundary =="
# The boundary is a real property of the substrate, not an accident, so it is pinned here.
# _quote_match tolerates up to 20% of a quote's tokens going missing, because that is what a
# dirty extraction looks like. A heavily rewritten quotation falls outside that and is a
# fabrication (major); a two-word operator flip falls inside it and is indistinguishable from
# an extractor dropping two words, so it is surfaced as a prompt (minor) instead of an
# accusation. Surfaced either way — which is the point. Only the severity differs.
cat > "$TMP/manuscript_inverted.md" <<'EOF'
# Reader independence in automated reporting workflows

Doe and colleagues state that "Automated advice should be withheld only if the reader has
recorded no initial impression whatsoever, and never otherwise" [1].

## References

1. Doe J, Roe A. Preserving reader independence when an automated second opinion is available.
   J Synth Workflow Res. 2025;1:1-9. doi:10.1000/synthetic.oversight
EOF
OUT="$(run --manuscript "$TMP/manuscript_inverted.md" --fulltext-dir "$FIX/fulltext")"
has "a rewritten quotation is a fabrication"     "$OUT" "CITED_QUOTE_ABSENT"
python3 "$DET" --manuscript "$TMP/manuscript_inverted.md" --fulltext-dir "$FIX/fulltext" --strict >/dev/null 2>&1
ck "and it fails --strict" 1 "$?"

sed 's/withheld only if the reader has$/released only if the reader has/; s/^recorded no initial impression whatsoever, and never otherwise/not recorded an initial impression/' \
  "$TMP/manuscript_inverted.md" > "$TMP/manuscript_flip.md"
OUT="$(run --manuscript "$TMP/manuscript_flip.md" --fulltext-dir "$FIX/fulltext")"
has   "a two-word operator flip is still surfaced" "$OUT" "CITED_QUOTE_UNRESOLVED"
hasnt "but is not called a fabrication"            "$OUT" "CITED_QUOTE_ABSENT"
python3 "$DET" --manuscript "$TMP/manuscript_flip.md" --fulltext-dir "$FIX/fulltext" --strict >/dev/null 2>&1
ck "and does not fail --strict on extraction-scale doubt" 0 "$?"

echo "== a citation with no full text is counted, never guessed at =="
cat > "$TMP/manuscript_missing.md" <<'EOF'
# Reader independence in automated reporting workflows

Recent work has begun to offer the chair [@nobody2025missing].
EOF
python3 "$DET" --manuscript "$TMP/manuscript_missing.md" --fulltext-dir "$FIX/fulltext" --strict >/dev/null 2>&1
ck "unresolvable citation -> silent" 0 "$?"
OUT="$(run --manuscript "$TMP/manuscript_missing.md" --fulltext-dir "$FIX/fulltext")"
has   "it reports what it could not check"       "$OUT" "not resolved to a full text"
hasnt "and invents no verdict about it"          "$OUT" "ATTRIBUTION_UNSUPPORTED"

echo "== the artifact names its own author =="
python3 "$DET" --manuscript "$FIX/manuscript_unsupported.md" --fulltext-dir "$FIX/fulltext" \
  --bib "$FIX/refs.bib" --out "$TMP/report.json" >/dev/null 2>&1
OUT="$(cat "$TMP/report.json")"
has "qc JSON carries the detector key"           "$OUT" '"detector": "check_claim_fidelity"'

echo
printf 'claim-fidelity challenge: %d passed, %d failed\n' "$pass" "$fail"
[ "$fail" -eq 0 ] || exit 1
