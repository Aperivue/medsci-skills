#!/usr/bin/env bash
# Regression test: every self-contained bundled CSL prints author names family-first.
#
# Six bundled CSLs (vancouver, vancouver-superscript, nlm-citation-sequence,
# american-medical-association, journal-of-korean-medical-science-strict, liver-international)
# declared their name options (initialize-with, name-as-sort-order) only on <style> and gave the
# author <names> no <name> child. pandoc 3.1.3 -- the version CI installs -- did not apply the
# style-level options there, so a reference list rendered "Jong Hyun Kim, Su Min Lee" instead of
# "Kim JH, Lee SM", under the gate's default CSL, and no check noticed. Each of those <names> now
# carries an explicit empty <name/>, which per CSL inherits the same options and which pandoc honours.
#
# A refresh of any of these files from upstream would drop that line again; this test is what
# notices. Dependent CSLs (rel="independent-parent") are skipped: pandoc fetches their parent over
# the network, and the bundled parent is checked under its own name.
#
# POSITIVE: the {Family, Full Given} entry SKILL.md prescribes must not come out given-name-first.
# NEGATIVE control: every CSL still prints both family names (the entry rendered at all).
# The same missing inheritance also switched off et-al truncation (bibliography et-al-min /
# et-al-use-first): an eight-author entry printed all eight names. Every bundled CSL truncates an
# eight-author list, so the eighth author must not appear.
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STYLES="$HERE/../citation_styles"

if ! command -v pandoc >/dev/null 2>&1; then
  echo "SKIP: pandoc unavailable"
  exit 0
fi

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
cat > "$WORK/refs.bib" <<'EOF'
@article{names2022,
  author  = {Kim, Jong Hyun and Lee, Su Min},
  title   = {A synthetic two-author study},
  journal = {Synthetic Reports},
  year    = {2022},
  volume  = {1},
  pages   = {1--2}
}
@article{eight2021,
  author  = {Aalto, Aa and Berg, Bb and Cruz, Cc and Dahl, Dd and Ekman, Ee and Falk, Ff and Gray, Gg and Holm, Hh},
  title   = {A synthetic eight-author study},
  journal = {Synthetic Reports},
  year    = {2021}
}
EOF
printf 'A claim [@names2022]. Another claim [@eight2021].\n' > "$WORK/ms.md"

pass=0
fail=0
checked=0
for csl in "$STYLES"/*.csl; do
  name="$(basename "$csl" .csl)"
  if grep -q 'rel="independent-parent"' "$csl"; then
    continue
  fi
  checked=$((checked + 1))
  out="$(pandoc "$WORK/ms.md" --citeproc --bibliography "$WORK/refs.bib" --csl "$csl" -t plain 2>&1)"
  if [[ "$out" == *"Jong Hyun Kim"* || "$out" == *"Su Min Lee"* ]]; then
    printf '  FAIL  %-46s given-name-first: %s\n' "$name" "$(printf '%s' "$out" | grep -m1 -E 'Kim|Jong')"
    fail=$((fail + 1))
  elif [[ "$out" == *"Holm"* ]]; then
    printf '  FAIL  %-46s eight-author list not truncated: %s\n' "$name" "$(printf '%s' "$out" | grep -m1 -E 'Aalto')"
    fail=$((fail + 1))
  elif [[ "$out" == *"Kim"* && "$out" == *"Lee"* && "$out" == *"Aalto"* ]]; then
    printf '  PASS  %-46s %s\n' "$name" "$(printf '%s' "$out" | grep -m1 -oE 'Kim[^.]*Lee [A-Z.]*')"
    pass=$((pass + 1))
  else
    printf '  FAIL  %-46s entry did not render: %s\n' "$name" "$out"
    fail=$((fail + 1))
  fi
done

echo
echo "  checked=$checked passed=$pass failed=$fail"
if [[ $checked -eq 0 ]]; then echo "ERROR: no self-contained CSL found under $STYLES" >&2; exit 2; fi
[[ $fail -eq 0 ]] || exit 1
echo "OK: every self-contained bundled CSL prints authors family-first and truncates a long list."
