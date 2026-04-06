#!/bin/bash
# PubMed E-utilities CLI wrapper
# Fallback when PubMed MCP server is unavailable
# Usage: bash pubmed_eutils.sh <command> <args...>
#
# Commands:
#   search <query> [retmax]       -- Search PubMed, return PMIDs
#   fetch <pmid1,pmid2,...>       -- Fetch article metadata (XML)
#   fetch_json <pmid1,pmid2,...>  -- Fetch article summary (JSON, DocSum)
#   related <pmid> [retmax]       -- Find related articles
#   cite_lookup <title>           -- Search by exact title to verify citation
#
# Environment:
#   NCBI_API_KEY  -- Optional. Increases rate limit from 3/sec to 10/sec.
#                    Register at https://www.ncbi.nlm.nih.gov/account/settings/
#
# Rate limiting: 3 requests/second without API key, 10/sec with key.
# This script sleeps 350ms between calls for safety.

set -euo pipefail

BASE="https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
TOOL="claude-code-search-lit"
EMAIL="noreply@example.com"
DB="pubmed"
SLEEP=0.35

# Build API key param if available
API_KEY_PARAM=""
if [ -n "${NCBI_API_KEY:-}" ]; then
  API_KEY_PARAM="&api_key=${NCBI_API_KEY}"
  SLEEP=0.1
fi

_sleep() { sleep "$SLEEP"; }

_curl() {
  curl -sS -A "Mozilla/5.0 (${TOOL})" "$@"
}

cmd_search() {
  local query="${1:?Usage: search <query> [retmax]}"
  local retmax="${2:-20}"
  local url="${BASE}/esearch.fcgi?db=${DB}&term=$(python3 -c "import urllib.parse; print(urllib.parse.quote('${query}'))")&retmax=${retmax}&retmode=json&tool=${TOOL}&email=${EMAIL}${API_KEY_PARAM}"
  _curl "$url"
}

cmd_fetch() {
  local ids="${1:?Usage: fetch <pmid1,pmid2,...>}"
  local url="${BASE}/efetch.fcgi?db=${DB}&id=${ids}&rettype=xml&retmode=xml&tool=${TOOL}&email=${EMAIL}${API_KEY_PARAM}"
  _curl "$url"
}

cmd_fetch_json() {
  local ids="${1:?Usage: fetch_json <pmid1,pmid2,...>}"
  local url="${BASE}/esummary.fcgi?db=${DB}&id=${ids}&retmode=json&tool=${TOOL}&email=${EMAIL}${API_KEY_PARAM}"
  _curl "$url"
}

cmd_related() {
  local pmid="${1:?Usage: related <pmid> [retmax]}"
  local retmax="${2:-10}"
  local url="${BASE}/elink.fcgi?dbfrom=${DB}&db=${DB}&id=${pmid}&cmd=neighbor_score&retmode=json&tool=${TOOL}&email=${EMAIL}${API_KEY_PARAM}"
  local result
  result=$(_curl "$url")
  # Extract linked PMIDs and fetch their summaries
  local linked_ids
  linked_ids=$(echo "$result" | python3 -c "
import sys, json
data = json.load(sys.stdin)
links = data.get('linksets', [{}])[0].get('linksetdbs', [{}])
for db in links:
    if db.get('linkname') == 'pubmed_pubmed':
        ids = [str(l['id']) for l in db.get('links', [])[:${retmax}]]
        print(','.join(ids))
        break
" 2>/dev/null || echo "")
  if [ -n "$linked_ids" ]; then
    _sleep
    cmd_fetch_json "$linked_ids"
  else
    echo '{"error": "No related articles found"}'
  fi
}

cmd_cite_lookup() {
  local title="${1:?Usage: cite_lookup <title>}"
  # Search by title field for exact verification
  cmd_search "${title}[Title]" 5
}

# Dispatch
case "${1:-help}" in
  search)      shift; cmd_search "$@" ;;
  fetch)       shift; cmd_fetch "$@" ;;
  fetch_json)  shift; cmd_fetch_json "$@" ;;
  related)     shift; cmd_related "$@" ;;
  cite_lookup) shift; cmd_cite_lookup "$@" ;;
  help|*)
    echo "Usage: bash pubmed_eutils.sh <command> <args...>"
    echo "Commands: search, fetch, fetch_json, related, cite_lookup"
    ;;
esac
