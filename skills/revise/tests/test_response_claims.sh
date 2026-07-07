#!/usr/bin/env bash
# Regression test for skills/revise/scripts/check_response_claims.py — the
# response-letter <-> revised-manuscript verification gate. Confirms an anchored
# claim absent from the body fails under --strict, a present one passes, and the
# false-positive guards (vague claims, reviewer blockquotes) do not fire.
set -u

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
V="$REPO_ROOT/skills/revise/scripts/check_response_claims.py"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

pass=0
fail=0
ck() {
  local label="$1" expected="$2" actual="$3"
  if [ "$expected" = "$actual" ]; then
    printf '  PASS  %-52s exit=%s\n' "$label" "$actual"
    pass=$((pass + 1))
  else
    printf '  FAIL  %-52s expected=%s actual=%s\n' "$label" "$expected" "$actual"
    fail=$((fail + 1))
  fi
}

# --- manuscript that DOES contain the added sentence + citation ---
cat > "$TMP/body_good.md" <<'MD'
## Methods
Diabetes was defined by a fasting glucose of at least 126 mg/dL or medication use.

## Discussion
Dosing errors are a recognized hazard in this setting, as Tariq et al. [15] reported.
MD

# --- manuscript that is MISSING both ---
cat > "$TMP/body_bad.md" <<'MD'
## Methods
Baseline characteristics were summarized descriptively.

## Discussion
The findings are consistent with prior work.
MD

# --- response letter with an anchored quote claim + a citation claim ---
cat > "$TMP/response.md" <<'MD'
**Comment 1.**
> The Methods do not define diabetes.

**Response 1.** Thank you. We added the sentence "Diabetes was defined by a fasting glucose of at least 126 mg/dL or medication use." to the Methods.

**Comment 2.**
> Please acknowledge dosing-error risk.

**Response 2.** We now cite Tariq et al. [15] in the Discussion.
MD

# --- response with only a VAGUE claim (no quote, no citation) ---
cat > "$TMP/response_vague.md" <<'MD'
**Response.** We clarified the Methods and revised the Introduction for readability.
MD

# --- response whose ONLY unverifiable quote is inside a reviewer blockquote ---
cat > "$TMP/response_reviewerquote.md" <<'MD'
**Comment 1.**
> The authors claim "a mortality reduction of ninety percent" without support.

**Response 1.** We have tempered this statement and now report the observed range only.
MD

# 1) anchored claims absent from body -> exit 1 (--strict)
python3 "$V" --response "$TMP/response.md" --manuscript "$TMP/body_bad.md" --strict > /dev/null 2>&1
ck "missing added quote + citation fails (--strict)" 1 "$?"

# 2) same claims present in body -> exit 0
python3 "$V" --response "$TMP/response.md" --manuscript "$TMP/body_good.md" --strict > /dev/null 2>&1
ck "verified quote + citation passes (--strict)" 0 "$?"

# 3) vague claim (no anchor) -> not flagged, exit 0
python3 "$V" --response "$TMP/response_vague.md" --manuscript "$TMP/body_bad.md" --strict > /dev/null 2>&1
ck "vague unanchored claim not flagged" 0 "$?"

# 4) reviewer-blockquote quote (not an author addition) -> not flagged, exit 0
python3 "$V" --response "$TMP/response_reviewerquote.md" --manuscript "$TMP/body_bad.md" --strict > /dev/null 2>&1
ck "reviewer blockquote quote not flagged" 0 "$?"

# 5) drift reported but tolerated without --strict -> exit 0
python3 "$V" --response "$TMP/response.md" --manuscript "$TMP/body_bad.md" > /dev/null 2>&1
ck "drift tolerated without --strict" 0 "$?"

# 6) the flagged verdicts are the expected two
OUT="$(python3 "$V" --response "$TMP/response.md" --manuscript "$TMP/body_bad.md" 2>&1)"
echo "$OUT" | grep -q RESPONSE_QUOTE_UNVERIFIED && echo "$OUT" | grep -q RESPONSE_CITATION_UNVERIFIED
ck "both expected verdicts present" 0 "$?"

echo "----"
echo "test_response_claims: $pass passed, $fail failed"
[ "$fail" -eq 0 ]
