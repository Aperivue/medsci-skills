#!/usr/bin/env bash
# Deterministic verifier for the citation-keys challenge card.
# Fixtures (synthetic only — no real manuscript, no PII):
#   manuscript.md      — cites [@smith2020] and [@jones2021].
#   refs_undefined.bib — defines ONLY smith2020, so jones2021 is UNDEFINED.
#   refs_clean.bib     — defines both, so every cited key resolves.
# The manuscript is identical for both runs; the two .bib files differ only in
# whether jones2021 exists. That is the point: an UNDEFINED citation key is a
# hard failure (a citation that resolves to nothing), and the clean pair clears.
#
# This card exists because check_citation_keys had a detector and a runtime
# wrapper but NO CI-wired regression, silently violating skills/MAINTENANCE.md's
# rule that every detector must be self-tested (found 2026-07-25).
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
DET="$HERE/../check_citation_keys.py"
cd "$HERE"
pass=1

# UNDEFINED case: jones2021 cited but absent from the .bib -> must exit 1 and name the key.
out_undef="$(python3 "$DET" fixture/manuscript.md fixture/refs_undefined.bib --allow-unused 2>&1)" && ru=0 || ru=$?
[ "${ru:-0}" -eq 1 ] || { echo "FAIL: undefined key should exit 1 (got ${ru:-0})" >&2; pass=0; }
printf '%s\n' "$out_undef" | grep -q "jones2021" || { echo "FAIL: verdict must name the undefined key jones2021" >&2; pass=0; }
printf '%s\n' "$out_undef" | grep -q "UNDEFINED" || { echo "FAIL: verdict must report UNDEFINED" >&2; pass=0; }

# Clean case: every cited key defined -> must exit 0.
python3 "$DET" fixture/manuscript.md fixture/refs_clean.bib --allow-unused >/dev/null 2>&1 && rc=0 || rc=$?
[ "${rc:-1}" -eq 0 ] || { echo "FAIL: clean pair should exit 0 (got ${rc:-1})" >&2; pass=0; }

[ "$pass" -eq 1 ] && echo "PASS: an undefined citation key fails the gate; a fully-resolved bibliography clears it." || exit 1
