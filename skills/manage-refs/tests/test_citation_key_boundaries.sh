#!/usr/bin/env bash
# Regression test: where a citation key ENDS, and what an `@` is not.
#
# Two defects, both of which made the checker fail correct manuscripts.
#
# 1. A citation that ends a sentence swallowed the full stop. The key pattern allowed `.` anywhere,
#    but pandoc counts internal punctuation as part of a key only when a letter or digit follows it.
#    So "...as previously reported @Smith2023." parsed as key `Smith2023.` — and the tool then
#    reported the SAME reference as UNDEFINED (no `Smith2023.` in the .bib) and as UNUSED (nothing
#    cited `Smith2023`) in one run. A citation ending a sentence is most of them.
#
# 2. Quarto / pandoc-crossref cross-references were read as bibliography keys. `@fig-flow`,
#    `@tbl-baseline`, `@sec-methods` resolve against the document's own labels; `quarto render`
#    compiles them without complaint. This checker called every one an undefined reference and
#    exited 1 — on a manuscript in the shape the repo's own `init_project.py` scaffolds.
#
# They are excluded from the verdict but REPORTED, so nothing is silently dropped, and a .bib entry
# that genuinely happens to be named `fig-...` resolves before the exclusion is ever consulted.
set -u

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
K="$REPO_ROOT/skills/manage-refs/scripts/check_citation_keys.py"
WORK="$(mktemp -d -t citekey_test.XXXXXX)"
trap 'rm -rf "$WORK"' EXIT

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

cat > "$WORK/refs.bib" <<'EOF'
@article{Smith2023,
  author = {Smith, John},
  title  = {A title},
  year   = {2023}
}
EOF

cat > "$WORK/figkey.bib" <<'EOF'
@article{fig-consort,
  author = {Real, Author},
  title  = {A paper someone keyed as fig-consort},
  year   = {2024}
}
EOF

run() {  # run <md> <bib> [flags...] -> exit code, output at $WORK/<md>.out
  local md="$1" bib="$2"; shift 2
  python3 "$K" "$WORK/$md" "$WORK/$bib" "$@" > "$WORK/$md.out" 2>&1
  echo $?
}
section_count() {  # section_count <md> <SECTION WORD>
  grep -oE "^$2 \([0-9]+\)" "$WORK/$1.out" | grep -oE '[0-9]+' || echo 0
}

# --- fixtures ---------------------------------------------------------------------------------
printf 'Prior work established this [@Smith2023].\n\nAnother sentence cites @Smith2023.\n' \
  > "$WORK/sentence_end.md"

printf 'A key with internal punctuation: @Sec.2a is one key.\n' > "$WORK/internal_punct.md"

cat > "$WORK/quarto.qmd" <<'EOF'
---
title: Example
---

Prior work established this @Smith2023.

![Study flow](flow.png){#fig-flow}

As shown in @fig-flow, enrolment proceeded. See also @tbl-baseline and @sec-methods.
EOF

printf 'Cites [@Smith2023] and [@Ghost2024].\n' > "$WORK/undefined.md"
printf 'Cites [@fig-consort].\n' > "$WORK/figkey.md"

echo "==== 1. a citation ending a sentence is the same citation ===="
ck "sentence-final @key: exit 0"        0 "$(run sentence_end.md refs.bib)"
ck "  no UNDEFINED"                     0 "$(section_count sentence_end.md UNDEFINED)"
ck "  no UNUSED"                        0 "$(section_count sentence_end.md UNUSED)"
ck "  counted once, not twice"          "cited=1" \
   "$(grep -oE 'cited=[0-9]+' "$WORK/sentence_end.md.out")"

echo "==== 2. pandoc's actual rule: internal punctuation followed by alphanumeric stays ===="
run internal_punct.md refs.bib > /dev/null
ck "@Sec.2a is ONE key, not truncated"  "[@Sec.2a]" \
   "$(grep -oE '\[@Sec\.2a\]' "$WORK/internal_punct.md.out" | head -1)"

echo "==== 3. Quarto cross-references are not bibliography keys ===="
ck "Quarto manuscript: exit 0"          0 "$(run quarto.qmd refs.bib)"
ck "  3 cross-references REPORTED"      3 "$(section_count quarto.qmd CROSS-REFERENCES)"
ck "  0 undefined"                      0 "$(section_count quarto.qmd UNDEFINED)"

echo "==== NEGATIVE CONTROLS ===="
ck "a genuinely undefined key still fails" 1 "$(run undefined.md refs.bib)"
ck "  and it is named"                  "[@Ghost2024]" \
   "$(grep -oE '\[@Ghost2024\]' "$WORK/undefined.md.out" | head -1)"
ck "a real .bib key named fig-* resolves" 0 "$(run figkey.md figkey.bib)"
ck "  not diverted to CROSS-REFERENCES" 0 "$(section_count figkey.md CROSS-REFERENCES)"
ck "UNUSED detection still works"       1 "$(run undefined.md refs.bib --strict-unused)"

echo
echo "  passed=$pass failed=$fail"
[ "$fail" -eq 0 ] || { for f in sentence_end.md quarto.qmd undefined.md figkey.md; do
    echo "--- $f"; cat "$WORK/$f.out"; done; exit 1; }
echo "OK: the full stop is punctuation, a cross-reference is not a citation, and a ghost key still fails."
