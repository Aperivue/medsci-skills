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

echo "fail=$fail"; [[ "$fail" -eq 0 ]] && echo "ALL PASS" || echo "FAILURES: $fail"
exit "$fail"
