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
# et-al-use-first): an eight-author entry printed all eight names. A style whose bibliography declares
# et-al-min at or below 8 must therefore drop the eighth author; one with a higher threshold or no
# et-al rule (the JMIR style, matching journals that list every author) must print all eight.
# EDITORS: a book with editors and no author falls back to the one-line <names variable="editor"/>
# inside the author <substitute>, which inherits the author <name>. An explicit <name/> there drops
# that inheritance, and the editors print given-name-first; this happened once in a contributed
# style, with the author entries above still passing. Some styles (nature) substitute the title and
# print no editors, so the editors are checked only for order, not for presence.
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
@book{edited2020,
  editor    = {Park, Ji Won and Choi, Min Seo},
  title     = {A synthetic edited book},
  publisher = {Synthetic Press},
  address   = {Seoul},
  year      = {2020}
}
EOF
printf 'A claim [@names2022]. Another claim [@eight2021]. A third claim [@edited2020].\n' > "$WORK/ms.md"

pass=0
fail=0
checked=0
for csl in "$STYLES"/*.csl; do
  name="$(basename "$csl" .csl)"
  if grep -q 'rel="independent-parent"' "$csl"; then
    continue
  fi
  checked=$((checked + 1))
  # A style must apply the et-al rule its bibliography declares (the pandoc inheritance bug above
  # dropped it): with et-al-min at or below 8 the eight-author entry is shortened; with a higher one,
  # or none at all (the JMIR style lists every author on purpose), all eight print.
  etal_min="$(python3 -c 'import sys, xml.etree.ElementTree as ET
root = ET.parse(sys.argv[1]).getroot()
bib = next((e for e in root.iter() if e.tag.rsplit("}", 1)[-1] == "bibliography"), None)
print((bib.get("et-al-min") if bib is not None else None) or root.get("et-al-min") or "")' "$csl")"
  if [[ -n "$etal_min" && "$etal_min" -le 8 ]]; then truncates=yes; else truncates=no; fi
  out="$(pandoc "$WORK/ms.md" --citeproc --bibliography "$WORK/refs.bib" --csl "$csl" -t plain --wrap=none 2>&1)"
  if [[ "$out" == *"Jong Hyun Kim"* || "$out" == *"Su Min Lee"* ]]; then
    printf '  FAIL  %-46s given-name-first: %s\n' "$name" "$(printf '%s' "$out" | grep -m1 -E 'Kim|Jong')"
    fail=$((fail + 1))
  elif [[ "$out" == *"Ji Won Park"* || "$out" == *"Min Seo Choi"* ]]; then
    printf '  FAIL  %-46s editors given-name-first: %s\n' "$name" "$(printf '%s' "$out" | grep -m1 -E 'Park')"
    fail=$((fail + 1))
  elif [[ "$truncates" == yes && "$out" == *"Holm"* ]]; then
    printf '  FAIL  %-46s declares et-al but did not truncate: %s\n' "$name" "$(printf '%s' "$out" | grep -m1 -E 'Aalto')"
    fail=$((fail + 1))
  elif [[ "$truncates" == no && "$out" != *"Holm"* ]]; then
    printf '  FAIL  %-46s declares no et-al but dropped an author: %s\n' "$name" "$(printf '%s' "$out" | grep -m1 -E 'Aalto')"
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
echo "OK: every self-contained bundled CSL prints authors and editors family-first and applies the et-al rule it declares."
