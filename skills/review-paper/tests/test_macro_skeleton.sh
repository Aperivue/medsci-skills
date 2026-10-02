#!/usr/bin/env bash
# Regression test for review-paper's format-dependent macro skeleton (F1).
# Scoping and systematic reviews must scaffold IMRaD with a Methods/Results slot for every
# applicable PRISMA-ScR / PRISMA 2020 item in check-reporting's bundled checklists; narrative
# reviews keep the 7-part skeleton with no PRISMA slot. Stdlib-only (python3).
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHECK="$HERE/check_skeleton.py"
SKEL="$HERE/../references/macro_skeleton.md"
TMP="$(mktemp -d -t rp_skel_XXXX)"
trap 'rm -rf "$TMP"' EXIT

[[ -f "$CHECK" && -f "$SKEL" ]] || { echo "ENV-ERR: checker or skeleton missing" >&2; exit 2; }

fail=0
expect() { local label="$1" want="$2"; shift 2
    "$@" >"$TMP/out" 2>&1; local got=$?
    if [[ "$got" == "$want" ]]; then printf '  PASS  %s\n' "$label"
    else printf '  FAIL  %s (exit %s, want %s)\n' "$label" "$got" "$want"; sed 's/^/        /' "$TMP/out"; fail=$((fail+1)); fi
}

# (1) NEGATIVE control: the shipped skeleton is clean.
expect "shipped skeleton: every PRISMA Methods/Results slot present" 0 python3 "$CHECK" "$SKEL"

# (2) POSITIVE: the single 7-part skeleton used for every format (the pre-fix shape) has no
#     Methods or Results section for scoping/systematic and must be flagged.
cat > "$TMP/seven_part_only.md" <<'EOF'
# Review macro skeleton (7-part) — reference template
1. Abstract  2. Introduction (scope + non-overlap)  3. Background
4. Thematic body by spine axis (+ summary table per section)
5. Frontiers  6. Challenges/Discussion (+ evaluation-metrics critique)  7. Conclusion
Tables: model-comparison (narrative/scoping) or PRISMA flow + extraction (systematic).
Figures: conceptual schematic; landscape/timeline; PRISMA(-ScR) flow.
EOF
expect "7-part-only skeleton flagged" 1 python3 "$CHECK" "$TMP/seven_part_only.md"

# (3) POSITIVE: a systematic skeleton missing the risk-of-bias Methods slot is flagged.
grep -v '\[PRISMA 2020 11\]' "$SKEL" > "$TMP/no_rob.md"
expect "systematic without PRISMA 2020 item 11 slot flagged" 1 python3 "$CHECK" "$TMP/no_rob.md"
grep -q 'Methods lacks slots for PRISMA 2020 items 11' "$TMP/out" \
    && printf '  PASS  %s\n' "gap names PRISMA 2020 item 11" \
    || { printf '  FAIL  %s\n' "gap names PRISMA 2020 item 11"; fail=$((fail+1)); }

# (4) POSITIVE: a scoping skeleton whose flow-diagram slot sits outside Results is flagged.
python3 - "$SKEL" "$TMP/moved.md" <<'PY'
import sys
lines = open(sys.argv[1], encoding="utf-8").read().splitlines()
row = next(l for l in lines if "[PRISMA-ScR 17]" in l)
lines.remove(row)
i = lines.index("- Funding [PRISMA-ScR 27]")
lines.insert(i + 1, row)
open(sys.argv[2], "w", encoding="utf-8").write("\n".join(lines) + "\n")
PY
expect "scoping item 17 outside Results flagged" 1 python3 "$CHECK" "$TMP/moved.md"

# (5) POSITIVE: PRISMA slots leaking into the narrative skeleton are flagged.
python3 - "$SKEL" "$TMP/narr_prisma.md" <<'PY'
import sys
s = open(sys.argv[1], encoding="utf-8").read()
s = s.replace("Tables: model-comparison summary table per body section.",
              "Tables: model-comparison summary table per body section. [PRISMA 2020 18]", 1)
open(sys.argv[2], "w", encoding="utf-8").write(s)
PY
expect "narrative with a PRISMA slot flagged" 1 python3 "$CHECK" "$TMP/narr_prisma.md"

# (6) Unrecognised input: a missing file exits 2 and names it.
expect "missing skeleton -> exit 2" 2 python3 "$CHECK" "$TMP/does_not_exist.md"

# (7) SKILL.md routes scoping/systematic away from the 7-part skeleton.
grep -q 'Scoping / systematic\*\* — IMRaD' "$HERE/../SKILL.md" \
    && printf '  PASS  %s\n' "SKILL.md Step 1 is format-dependent" \
    || { printf '  FAIL  %s\n' "SKILL.md Step 1 is format-dependent"; fail=$((fail+1)); }

if [[ $fail -gt 0 ]]; then echo "FAILED: $fail check(s)"; exit 1; fi
echo "ALL PASS"
