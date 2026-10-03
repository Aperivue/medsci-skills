#!/usr/bin/env bash
# Regression test for academic-aio/scripts/validate_schema.py.
# Builds synthetic JSON-LD fixtures (no committed data) and asserts the
# validator's contract: a complete ScholarlyArticle passes; wrong @context,
# unknown @type, a missing required field, and a malformed DOI each fail.
# Stdlib-only (json/re), network-free, ASCII-only.
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$HERE/../scripts/validate_schema.py"
TMP="$(mktemp -d -t aio_schema_XXXX)"
trap 'rm -rf "$TMP"' EXIT

fail=0
check() { local label="$1" want="$2"; shift 2
    "$@" >/dev/null 2>&1; local got=$?
    if [[ "$got" -eq "$want" ]]; then printf '  PASS  %s\n' "$label"
    else printf '  FAIL  %s (exit %s, want %s)\n' "$label" "$got" "$want"; fail=$((fail+1)); fi
}

[[ -f "$SCRIPT" ]] || { echo "ENV-ERR: validate_schema.py missing" >&2; exit 2; }

# Valid ScholarlyArticle (all required fields, canonical DOI).
cat > "$TMP/ok.jsonld" <<'JSON'
{
  "@context": "https://schema.org",
  "@type": "ScholarlyArticle",
  "headline": "Synthetic Diagnostic Study",
  "datePublished": "2026-01-01",
  "author": [{"@type": "Person", "name": "Alice Kim"}],
  "identifier": [{"@type": "PropertyValue", "propertyID": "DOI", "value": "10.1000/synthetic.2026.001"}],
  "url": "https://example.org/article"
}
JSON
check "valid ScholarlyArticle -> exit 0" 0 python3 "$SCRIPT" "$TMP/ok.jsonld"

# Wrong @context.
sed 's#https://schema.org#https://example.com#' "$TMP/ok.jsonld" > "$TMP/bad_ctx.jsonld"
check "wrong @context -> exit 1" 1 python3 "$SCRIPT" "$TMP/bad_ctx.jsonld"

# Unknown @type.
sed 's/ScholarlyArticle/UnicornType/' "$TMP/ok.jsonld" > "$TMP/bad_type.jsonld"
check "unknown @type -> exit 1" 1 python3 "$SCRIPT" "$TMP/bad_type.jsonld"

# Missing required field (no "url"; still valid JSON).
cat > "$TMP/missing.jsonld" <<'JSON'
{
  "@context": "https://schema.org",
  "@type": "ScholarlyArticle",
  "headline": "Synthetic Diagnostic Study",
  "datePublished": "2026-01-01",
  "author": [{"@type": "Person", "name": "Alice Kim"}],
  "identifier": [{"@type": "PropertyValue", "propertyID": "DOI", "value": "10.1000/synthetic.2026.001"}]
}
JSON
check "missing required field -> exit 1" 1 python3 "$SCRIPT" "$TMP/missing.jsonld"

# Malformed DOI.
sed 's#10.1000/synthetic.2026.001#not-a-doi#' "$TMP/ok.jsonld" > "$TMP/bad_doi.jsonld"
check "malformed DOI -> exit 1" 1 python3 "$SCRIPT" "$TMP/bad_doi.jsonld"

# Mixed batch (one bad file) still fails overall.
check "batch with one bad file -> exit 1" 1 python3 "$SCRIPT" "$TMP/ok.jsonld" "$TMP/bad_ctx.jsonld"

# --- Placeholders and identifier shapes (regression) --------------------------
TPL="$HERE/../references/schema_markup_templates"
mk_sa() {  # $1 = file, $2 = JSON value of "identifier"
cat > "$1" <<JSON
{"@context": "https://schema.org", "@type": "ScholarlyArticle", "headline": "Synthetic",
 "datePublished": "2026-01-01", "author": [{"@type": "Person", "name": "Alice Kim"}],
 "identifier": $2, "url": "https://example.org/article"}
JSON
}
mk_person() {  # $1 = file, $2 = JSON value of "identifier"
cat > "$1" <<JSON
{"@context": "https://schema.org", "@type": "Person", "name": "Alice Kim", "identifier": $2}
JSON
}

# Unfilled shipped templates FAIL by default and PASS under --template.
for t in "$TPL"/*.jsonld; do
    check "unfilled template $(basename "$t") -> exit 1" 1 python3 "$SCRIPT" "$t"
done
check "templates under --template -> exit 0" 0 python3 "$SCRIPT" --template "$TPL"/*.jsonld

mk_sa "$TMP/ph_doi.jsonld" '[{"@type": "PropertyValue", "propertyID": "DOI", "value": "10.xxxx/yyyy"}]'
check "placeholder DOI 10.xxxx/yyyy -> exit 1" 1 python3 "$SCRIPT" "$TMP/ph_doi.jsonld"
check "placeholder DOI under --template -> exit 0" 0 python3 "$SCRIPT" --template "$TMP/ph_doi.jsonld"

# DOI checked in every identifier shape.
mk_sa "$TMP/str_bad_doi.jsonld" '"doi: not-a-doi"'
check "string identifier with malformed DOI -> exit 1" 1 python3 "$SCRIPT" "$TMP/str_bad_doi.jsonld"
mk_sa "$TMP/dict_bad_doi.jsonld" '{"@type": "PropertyValue", "propertyID": "DOI", "value": "not-a-doi"}'
check "object identifier with malformed DOI -> exit 1" 1 python3 "$SCRIPT" "$TMP/dict_bad_doi.jsonld"
mk_sa "$TMP/str_ok_doi.jsonld" '"https://doi.org/10.1000/synthetic.2026.001"'
check "string identifier with valid DOI URL -> exit 0" 0 python3 "$SCRIPT" "$TMP/str_ok_doi.jsonld"
mk_sa "$TMP/str_pmid.jsonld" '"PMID:12345678"'
check "string non-DOI identifier left alone -> exit 0" 0 python3 "$SCRIPT" "$TMP/str_pmid.jsonld"
mk_sa "$TMP/sici.jsonld" '[{"propertyID": "DOI", "value": "10.1002/(SICI)1097-0258(19980430)17:8<857::AID-SIM777>3.0.CO;2-E"}]'
check "SICI-style DOI with <...> -> exit 0" 0 python3 "$SCRIPT" "$TMP/sici.jsonld"

# ORCID: list shape checked; check digit (ISO 7064 MOD 11-2) verified.
mk_person "$TMP/orcid_list_bad.jsonld" '[{"@type": "PropertyValue", "propertyID": "ORCID", "value": "orcid-garbage"}]'
check "list ORCID malformed -> exit 1" 1 python3 "$SCRIPT" "$TMP/orcid_list_bad.jsonld"
mk_person "$TMP/orcid_bad_check.jsonld" '"https://orcid.org/0000-0002-1825-0098"'
check "ORCID with wrong check digit -> exit 1" 1 python3 "$SCRIPT" "$TMP/orcid_bad_check.jsonld"
mk_person "$TMP/orcid_ok.jsonld" '"https://orcid.org/0000-0002-1825-0097"'
check "ORCID with valid check digit -> exit 0" 0 python3 "$SCRIPT" "$TMP/orcid_ok.jsonld"
mk_person "$TMP/orcid_list_ok.jsonld" '[{"@type": "PropertyValue", "propertyID": "ORCID", "value": "0000-0002-1825-0097"}]'
check "list ORCID valid -> exit 0" 0 python3 "$SCRIPT" "$TMP/orcid_list_ok.jsonld"

# Person identifier list: other author IDs allowed; ORCID-looking entries checked.
mk_person "$TMP/person_multi.jsonld" '["https://orcid.org/0000-0002-1825-0097", "https://www.scopus.com/authid/detail.uri?authorId=123"]'
check "Person list ORCID + Scopus -> exit 0" 0 python3 "$SCRIPT" "$TMP/person_multi.jsonld"
mk_person "$TMP/person_multi_bad.jsonld" '["https://orcid.org/0000-0002-1825-0098", "https://www.scopus.com/authid/detail.uri?authorId=123"]'
check "Person list with bad ORCID check digit -> exit 1" 1 python3 "$SCRIPT" "$TMP/person_multi_bad.jsonld"
mk_person "$TMP/person_str_scopus.jsonld" '"https://www.scopus.com/authid/detail.uri?authorId=123"'
check "Person single non-ORCID string still fails -> exit 1" 1 python3 "$SCRIPT" "$TMP/person_str_scopus.jsonld"

# DOI URL value handled the same in list and object shape; http ORCID in a list.
mk_sa "$TMP/list_doi_url.jsonld" '[{"propertyID": "doi", "value": "https://doi.org/10.1000/synthetic.2026.001"}]'
check "list DOI with doi.org URL value -> exit 0" 0 python3 "$SCRIPT" "$TMP/list_doi_url.jsonld"
mk_sa "$TMP/obj_doi_url.jsonld" '{"propertyID": "doi", "value": "https://doi.org/10.1000/synthetic.2026.001"}'
check "object DOI with doi.org URL value -> exit 0" 0 python3 "$SCRIPT" "$TMP/obj_doi_url.jsonld"
mk_person "$TMP/orcid_http_list.jsonld" '[{"propertyID": "ORCID", "value": "http://orcid.org/0000-0002-1825-0097"}]'
check "list ORCID http URL -> exit 0" 0 python3 "$SCRIPT" "$TMP/orcid_http_list.jsonld"
mk_sa "$TMP/sici_hash.jsonld" '"10.1002/(SICI)1097-0258(19980430)17:8<857::AID-SIM777>3.0.CO;2-#"'
check "string SICI DOI ending in # -> exit 0" 0 python3 "$SCRIPT" "$TMP/sici_hash.jsonld"

# Reviewer counter-examples origin/main cleared: still clean.
mk_sa "$TMP/str_pct_doi.jsonld" '"https://doi.org/10.1002/%28SICI%291097-0258%2819980430%2917%3A8%3C857%3A%3AAID-SIM777%3E3.0.CO%3B2-E"'
check "string percent-encoded doi.org URL -> exit 0" 0 python3 "$SCRIPT" "$TMP/str_pct_doi.jsonld"
mk_sa "$TMP/list_pct_doi.jsonld" '[{"propertyID": "DOI", "value": "https://doi.org/10.1000/synthetic%2F2026.001"}]'
check "list DOI percent-encoded doi.org URL -> exit 0" 0 python3 "$SCRIPT" "$TMP/list_pct_doi.jsonld"
mk_person "$TMP/person_bare_list.jsonld" '["0000-0002-1825-0097"]'
check "Person list with bare ORCID iD -> exit 0" 0 python3 "$SCRIPT" "$TMP/person_bare_list.jsonld"
mk_person "$TMP/person_http_list.jsonld" '["http://orcid.org/0000-0002-1825-0097", "https://www.scopus.com/authid/detail.uri?authorId=123"]'
check "Person list with http ORCID URL -> exit 0" 0 python3 "$SCRIPT" "$TMP/person_http_list.jsonld"
# The check digit is still enforced on those shapes.
mk_person "$TMP/person_bare_list_bad.jsonld" '["0000-0002-1825-0098"]'
check "Person list bare ORCID bad check digit -> exit 1" 1 python3 "$SCRIPT" "$TMP/person_bare_list_bad.jsonld"
mk_sa "$TMP/str_pct_bad.jsonld" '"https://doi.org/not%2Da%2Ddoi"'
check "string doi.org URL that is not a DOI -> exit 1" 1 python3 "$SCRIPT" "$TMP/str_pct_bad.jsonld"
# A single Person string keeps main's URL-only rule.
mk_person "$TMP/person_bare_str.jsonld" '"0000-0002-1825-0097"'
check "Person single bare ORCID string still fails -> exit 1" 1 python3 "$SCRIPT" "$TMP/person_bare_str.jsonld"

# Prose with "<" is not a placeholder.
python3 - "$TMP/ok.jsonld" "$TMP/prose_lt.jsonld" <<'PY'
import json, sys
d = json.load(open(sys.argv[1])); d["abstract"] = "AUC rose (p<0.05) in <i>vivo</i>."
json.dump(d, open(sys.argv[2], "w"))
PY
check "abstract containing '<' -> exit 0" 0 python3 "$SCRIPT" "$TMP/prose_lt.jsonld"

echo "fail=$fail"; [[ "$fail" -eq 0 ]] && echo "ALL PASS" || echo "FAILURES: $fail"
exit "$fail"
