#!/usr/bin/env bash
# Regression test for ma-scout: an unknown count is never "0", and an unchecked PROSPERO is never "clear".
#
# 1. ma-scout's Phase 1 pipes `pubmed_eutils.sh search` into `parse_pubmed.py esearch`. The parser
#    used to default a missing `esearchresult.count` to "0", so an error body printed
#    "Total results: 0" and exited 0. The skill's best gap verdict is "MA = 0", so a search that did
#    not run could read as a gap. The parser now exits 2 and names the problem.
# 2. The README templates hard-coded `PROSPERO: ✅` while every other source was ✅/❌, so a generated
#    README always claimed PROSPERO had been searched. The row now carries a three-way status
#    (searched with a match / searched with no match / not checked) plus the query and date.
# 3. The Phase 6 gate said "after the 15-30% discount", which read literally keeps 70-85% of raw hits
#    and contradicts §2g's `raw × 0.15–0.30`. The gate now states the multiplier.
#
# No network. On origin/main this fails 14 checks: 1a-1f (parser), 2a-2d (templates, gate) and 3a-3b.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
SKILL="$HERE/.."
PARSER="$SKILL/../search-lit/references/parse_pubmed.py"

fail=0
ck() { if [ "$2" = "$3" ]; then printf '  PASS  %s\n' "$1"; else printf '  FAIL  %s (want %s got %s)\n' "$1" "$2" "$3"; fail=$((fail+1)); fi; }
rc_of() { printf '%s' "$1" | python3 "$PARSER" esearch >/dev/null 2>&1; echo $?; }
out_of() { printf '%s' "$1" | python3 "$PARSER" esearch 2>/dev/null; }

# --- 1. positive cases: bodies that are not a search result must not print a count
ck "1a top-level error body exits 2" 2 "$(rc_of '{"error":"API rate limit exceeded"}')"
ck "1b esearchresult.ERROR exits 2" 2 "$(rc_of '{"esearchresult":{"ERROR":"Invalid query"}}')"
ck "1c esearchresult without count exits 2" 2 "$(rc_of '{"esearchresult":{"idlist":[]}}')"
ck "1d ERROR beside a count exits 2" 2 "$(rc_of '{"esearchresult":{"count":"0","idlist":[],"ERROR":"bad"}}')"
ck "1e error body prints no 'Total results: 0'" no \
  "$(out_of '{"error":"x"}' | grep -qF 'Total results: 0' && echo yes || echo no)"
ck "1f error is named on stderr" yes \
  "$(printf '%s' '{"error":"API rate limit exceeded"}' | python3 "$PARSER" esearch 2>&1 >/dev/null | grep -qF 'API rate limit exceeded' && echo yes || echo no)"

# --- 1. negative controls: real search results still parse, including a genuine zero
ck "1g normal result exits 0" 0 "$(rc_of '{"esearchresult":{"count":"3","retmax":"3","idlist":["1","2","3"]}}')"
ck "1h normal result prints its count" yes \
  "$(out_of '{"esearchresult":{"count":"3","idlist":["1","2","3"]}}' | grep -qxF 'Total results: 3' && echo yes || echo no)"
ck "1i genuine zero (phrase not found) exits 0" 0 \
  "$(rc_of '{"esearchresult":{"count":"0","retmax":"0","idlist":[],"errorlist":{"phrasesnotfound":["zzqx"]}}}')"
ck "1j genuine zero prints 'Total results: 0'" yes \
  "$(out_of '{"esearchresult":{"count":"0","idlist":[]}}' | grep -qxF 'Total results: 0' && echo yes || echo no)"

# --- 2. PROSPERO provenance in the README templates and the gate
for t in project_readme_template.md project_readme_template_ko.md; do
  f="$SKILL/references/$t"
  ck "2a $t has no hard-coded 'PROSPERO: ✅'" 0 "$(grep -cxF -- '- PROSPERO: ✅' "$f")"
  ck "2b $t PROSPERO row records query and date" 1 "$(grep -E -- '^- PROSPERO: .*\{query\}.*\{YYYY-MM-DD\}' "$f" | wc -l | tr -d ' ')"
done
ck "2c gate treats a failed PROSPERO search as not checked" yes \
  "$(grep -qF '"not checked", never "none found"' "$SKILL/SKILL.md" && echo yes || echo no)"
ck "2d §2f defines the three PROSPERO statuses" yes \
  "$(grep -qF '`searched (match found)`, `searched (no match)`, or `not checked (unavailable/failed)`' "$SKILL/SKILL.md" && echo yes || echo no)"

# --- 3. the k_realistic gate states the same multiplier as §2g
ck "3a gate no longer says 'after the 15-30% discount'" 0 "$(grep -cF 'after the 15-30% discount' "$SKILL/SKILL.md")"
ck "3b gate states raw count × 0.15–0.30" yes \
  "$(grep -qF 'k_realistic = raw count × 0.15–0.30' "$SKILL/SKILL.md" && echo yes || echo no)"

if [ "$fail" -eq 0 ]; then
  echo "PASS: ma-scout never reads an unknown count as 0 or an unchecked PROSPERO as clear."
else
  echo "FAIL: $fail check(s) failed." >&2
  exit 1
fi
