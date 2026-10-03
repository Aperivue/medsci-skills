#!/usr/bin/env bash
# Regression test for the body-word-count vs journal-cap gate (the revision-
# inflation trap). Synthetic, PII-free fixtures. Limits are computed from the
# fixture's own measured count so the test does not hardcode a fragile number.
# Stdlib-only (python3).
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$HERE/../scripts/check_wordcount_cap.py"
FIX="$HERE/fixtures/wc_body.md"
PROFILE="$HERE/fixtures/wc_journal_profile.md"
OUT="$(mktemp -t wc_XXXX).json"
trap 'rm -f "$OUT"' EXIT

fail=0
check() { local label="$1"; shift
    if "$@" >/dev/null 2>&1; then printf '  PASS  %s\n' "$label"
    else printf '  FAIL  %s\n' "$label"; fail=$((fail+1)); fi
}
jget() { python3 -c "import json,sys; print(json.load(open('$OUT'))['$1'])"; }
verdict_is() { python3 -c "import json,sys; sys.exit(0 if json.load(open('$OUT'))['verdict']=='$1' else 1)"; }
limit_is()   { python3 -c "import json,sys; sys.exit(0 if json.load(open('$OUT'))['limit']==$1 else 1)"; }

[[ -f "$SCRIPT" ]] || { echo "ENV-ERR: script missing" >&2; exit 2; }

# Measure the fixture once (report-only) to get the effective rendered estimate.
python3 "$SCRIPT" --manuscript "$FIX" --limit 100000 --out "$OUT" --quiet >/dev/null 2>&1
E=$(jget rendered_words_est)
B=$(jget body_words)
C=$(jget n_inline_citations)
check "body_words > 0"                    test "$B" -gt 0
check "abstract/refs excluded (body < 90)" test "$B" -lt 90
check "2 inline citations counted"        test "$C" -eq 2
check "rendered est > body (citations expand)" test "$E" -gt "$B"

# (1) limit just below the estimate -> OVER cap, exit 1 under --strict
python3 "$SCRIPT" --manuscript "$FIX" --limit "$((E-1))" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "exit 1 over cap" test "$?" -eq 1
check "verdict WORDCOUNT_OVER_CAP" verdict_is WORDCOUNT_OVER_CAP

# (2) limit == estimate -> within cap but above 0.95x -> NEAR (Minor), exit 0
python3 "$SCRIPT" --manuscript "$FIX" --limit "$E" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "exit 0 at near cap (Minor)" test "$?" -eq 0
check "verdict WORDCOUNT_NEAR_CAP" verdict_is WORDCOUNT_NEAR_CAP

# (3) generous limit -> OK
python3 "$SCRIPT" --manuscript "$FIX" --limit "$((E*100))" --out "$OUT" --quiet >/dev/null 2>&1
check "verdict OK under generous limit" verdict_is OK

# (4) cap parsed from a journal profile (Original Article = 4,000 words)
python3 "$SCRIPT" --manuscript "$FIX" --journal-profile "$PROFILE" \
    --article-type "Original Article" --out "$OUT" --quiet >/dev/null 2>&1
check "cap parsed from profile == 4000" limit_is 4000

# (5) neither --limit nor --journal-profile -> usage error (exit 2)
python3 "$SCRIPT" --manuscript "$FIX" --quiet >/dev/null 2>&1
check "exit 2 when no cap source given" test "$?" -eq 2

# (6) subheadings are body words. The rendered DOCX carries every subheading as a line of
#     text and Word counts it; an estimate that skipped them read a real overage as
#     NEAR_CAP and exited 0 under --strict. Fixture: exactly 1,000 prose words (8-word
#     sentence x 125), 3 section headings (1 word each) + 15 four-word subheadings = 63
#     heading words, no citations. Cap 1,040: prose alone is NEAR (>0.95x); prose +
#     headings (1,063) is OVER.
SUBH="$(mktemp -t wc_subh_XXXX).md"
trap 'rm -f "$OUT" "$SUBH"' EXIT
python3 - "$SUBH" <<'PY'
import sys
s = "The intervention reduced mortality in the enrolled cohort. "
parts = ["---", "title: Synthetic subheading fixture", "---", "", "## Abstract", "",
         "Abstract words are excluded from the body count entirely here.", "",
         "## Introduction", "", s * 10, "", "## Methods", ""]
for i in range(1, 16):
    parts += [f"### Synthetic subsection heading {i}", "", s * 5, ""]
parts += ["## Discussion", "", s * 40, "", "## References", "",
          "1. Alpha QZ. A synthetic reference entry. J Synth. 2020;1:1-2.", ""]
open(sys.argv[1], "w").write("\n".join(parts))
PY
python3 "$SCRIPT" --manuscript "$SUBH" --limit 1040 --out "$OUT" --strict --quiet >/dev/null 2>&1
check "exit 1 under --strict when subheadings push the body over the cap" test "$?" -eq 1
check "verdict WORDCOUNT_OVER_CAP (not NEAR) with subheadings counted" verdict_is WORDCOUNT_OVER_CAP
check "heading_words == 63 (3 sections + 15 x 4-word subheadings; skipped headings excluded)" \
    python3 -c "import json,sys; d=json.load(open('$OUT')); sys.exit(0 if d['heading_words']==63 and d['body_words']==1063 else 1)"

# (7) F3: the cap comes from a STRUCTURED profile field, never from prose that mentions the
#     article type. The shipped profiles carry either a table with a body-limit column (whose
#     cells hold the number without "words") or prose like "abstract of 250 words required for
#     Original Articles"; the old parser returned that abstract limit as the body cap.
PROF="$(mktemp -d -t wc_prof_XXXX)"
trap 'rm -f "$OUT" "$SUBH"; rm -rf "$PROF"' EXIT
cat > "$PROF/table.md" <<'EOF'
# Synthetic Journal A

| Type | Body Word Limit | Abstract | References |
|------|----------------|----------|------------|
| Original Article | 4,500 (excluding abstract and references) | Structured, 300 words or fewer | 40 |
| Brief Report | 1,500 | 150 words | 15 |

Original Articles require a structured abstract of 300 words or fewer.
EOF
cat > "$PROF/prose.md" <<'EOF'
# Synthetic Journal B

## Scope Keywords

- Original Article

Synthetic society journal. Structured abstract of 250 words required for Original Articles.
EOF
cat > "$PROF/ambiguous.md" <<'EOF'
# Synthetic Journal C

| Type | Body | Abstract |
|------|------|----------|
| Original Article | 3,000 words (systematic review: 5,000) | 250 words |
EOF
python3 "$SCRIPT" --manuscript "$FIX" --journal-profile "$PROF/table.md" \
    --article-type "Original Article" --out "$OUT" --quiet >/dev/null 2>&1
check "table profile: cap read from the body column (4500), not the abstract (300)" limit_is 4500
python3 "$SCRIPT" --manuscript "$FIX" --journal-profile "$PROF/prose.md" \
    --article-type "Original Article" --quiet >/dev/null 2>&1
check "prose-only profile: exit 2 (asks for --limit), never the abstract limit" test "$?" -eq 2
python3 "$SCRIPT" --manuscript "$FIX" --journal-profile "$PROF/ambiguous.md" \
    --article-type "Original Article" --quiet >/dev/null 2>&1
check "two numbers in the body cell: exit 2 (ambiguous)" test "$?" -eq 2
# NEGATIVE control: the list-item form (fixture) still parses; covered by (4), re-asserted
# here next to the table case so the fallback order is explicit.
python3 "$SCRIPT" --manuscript "$FIX" --journal-profile "$PROFILE" \
    --article-type "Original Article" --out "$OUT" --quiet >/dev/null 2>&1
check "list-item profile still parses (4000)" limit_is 4000

echo "fail=$fail"; [[ "$fail" -eq 0 ]] && echo "ALL PASS" || echo "FAILURES: $fail"
exit "$fail"
