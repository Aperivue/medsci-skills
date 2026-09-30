#!/usr/bin/env bash
# Regression test: free-text queries in references/pubmed_eutils.sh are data, never code.
#
# `search` used to URL-encode the query by pasting it into Python source,
# `python3 -c "...quote('${query}')"`. Apostrophes are ordinary in queries (Crohn's disease,
# Alzheimer's, O'Brien[Author]). The first one closed the literal and caused a SyntaxError, the
# substitution came back empty, and the script sent `esearch?term=&retmax=...` and exited 0:
# a silent search for nothing, on the path `cite_lookup` shares. A crafted query could also
# close the literal itself and run its own Python, and `related` pasted `retmax` into source
# the same way.
#
# No network: `curl` is a stub on PATH that records each URL and answers with canned JSON.
# The pre-fix script fails 9 of the 14 assertions. It sends `term=`, runs both breakout payloads
# (their marker files appear) and accepts a non-numeric retmax. Check 5 passes before and after;
# it pins that retmax still truncates once it is passed as an argument.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
EUTILS="$HERE/../references/pubmed_eutils.sh"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

mkdir -p "$TMP/bin"
cat >"$TMP/bin/curl" <<'STUB'
#!/usr/bin/env bash
url="${*: -1}"
echo "$url" >>"$CALLS"
case "$url" in
  *elink.fcgi*) printf '%s' '{"linksets":[{"linksetdbs":[{"linkname":"pubmed_pubmed","links":[{"id":111},{"id":222},{"id":333}]}]}]}' ;;
  *) printf '%s' '{"esearchresult":{"idlist":[]}}' ;;
esac
printf '\n200\n'
STUB
chmod +x "$TMP/bin/curl"

fail=0
ck() { if [ "$2" = "$3" ]; then printf '  PASS  %s\n' "$1"; else printf '  FAIL  %s (want %s got %s)\n' "$1" "$2" "$3"; fail=$((fail+1)); fi; }
run() {  # run <args...> ; prints the exit code, URLs land in $TMP/calls
  : >"$TMP/calls"
  ( cd "$TMP" && PATH="$TMP/bin:$PATH" CALLS="$TMP/calls" NCBI_API_KEY= bash "$EUTILS" "$@" >"$TMP/out" 2>"$TMP/err" )
  echo $?
}
sent() { grep -qF -- "$1" "$TMP/calls" && echo yes || echo no; }

# 1. an apostrophe in a search query
ck "search with an apostrophe exits 0" 0 "$(run search "Crohn's disease[Title] AND MRI" 5)"
ck "  ...sends the whole encoded term" yes "$(sent 'term=Crohn%27s%20disease%5BTitle%5D%20AND%20MRI&retmax=5&')"
ck "  ...never sends an empty term" no "$(sent 'term=&')"

# 2. cite_lookup goes through the same path
ck "cite_lookup with an apostrophe exits 0" 0 "$(run cite_lookup "Crohn's disease: a review")"
ck "  ...sends the whole [Title] term" yes "$(sent 'term=Crohn%27s%20disease%3A%20a%20review%5BTitle%5D&retmax=5&')"

# 3. a query written to break out of the old Python string literal
MARK="$TMP/query-ran-code"
ck "breakout query exits 0" 0 "$(run search "x')); open('$MARK', 'w'); print(('" 5)"
ck "  ...runs no code" no "$([ -e "$MARK" ] && echo yes || echo no)"
ck "  ...is searched as literal text" yes "$(sent 'term=x%27%29%29%3B%20open%28')"

# 4. a related retmax written to break out of the old Python slice
MARK2="$TMP/retmax-ran-code"
rc="$(run related 12345 "1]]; open('$MARK2', 'w'); x=[[0")"
ck "breakout retmax is refused" yes "$([ "$rc" -ne 0 ] && echo yes || echo no)"
ck "  ...runs no code" no "$([ -e "$MARK2" ] && echo yes || echo no)"
ck "  ...before any request" 0 "$(wc -l <"$TMP/calls" | tr -d ' ')"

# 5. related still honours retmax, now passed as an argument
ck "related 12345 2 exits 0" 0 "$(run related 12345 2)"
ck "  ...fetches only the first 2 linked PMIDs" yes "$(sent 'esummary.fcgi?db=pubmed&id=111,222&')"

# 6. a non-numeric search retmax
rc="$(run search "MRI" "5&api_key=x")"
ck "non-numeric search retmax is refused" yes "$([ "$rc" -ne 0 ] && echo yes || echo no)"

if [ "$fail" -eq 0 ]; then
  echo "PASS: pubmed_eutils.sh sends free text as data, never as code."
else
  echo "FAIL: $fail check(s) failed." >&2
  exit 1
fi
