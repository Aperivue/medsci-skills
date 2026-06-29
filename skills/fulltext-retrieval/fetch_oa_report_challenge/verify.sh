#!/usr/bin/env bash
# Network-free challenge: fetch_oa report builder + title-match tri-state.
# Mirrors CI usage: `bash skills/fulltext-retrieval/fetch_oa_report_challenge/verify.sh`
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$DIR/run_challenge.py"
