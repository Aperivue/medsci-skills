#!/usr/bin/env bash
# Deterministic verifier for the reported-P-from-counts challenge card. cd HERE for
# a stable relative source path. Pure stdlib (math.comb / math.erfc) — no scipy.
# Fixtures (synthetic only — no real manuscript, no PII):
#   p_bad.md — a 2-group baseline table; the Male row reproduces at 0.237
#              (uncorrected Pearson, so the family calibrates) while the
#              Adenocarcinoma row claims P<0.001 whose true value is ~0.06 under
#              every family -> 1x P_NOT_REPRODUCIBLE.
#   p_ok.md  — same table with the Adenocarcinoma P corrected to 0.060 -> OK.
#   p_cross.md    — P 0.04 vs true ~0.18 (alpha crossing: MINOR advisory only),
#                   <0.001 vs true ~0.005 (bound exceeded), single-row table 0.90 vs
#                   ~3e-05 -> 2 Major flags + 1 MINOR.
#   p_cross_ok.md — the same rows corrected, a straddling 0.05, a one-family 0.046
#                   and an r x c omnibus P -> OK.
#   p_none.md     — no table -> OK with an explicit NOT CHECKED line.
#   p_adjusted.md — adjusted / multivariable P or an OR column: the crude 2x2 is not the
#                   model, so only the order-of-magnitude rule applies -> OK + LIMITED.
#   p_missing_denom.md — printed % implies a smaller denominator than the header n
#                   (missing data) -> not judged on the 2x2 boundary rules -> OK + LIMITED.
#   p_adjusted_context.md — adjustment / regression / weighting stated only in a footnote
#                   or in the caption, with a plain or footnoted P header -> OK + LIMITED.
#   p_alpha_only.md — the only disagreement is an alpha crossing (0.04 vs ~0.18) ->
#                   OK with a MINOR P_ALPHA_CROSSING; never fails --strict.
#   p_footnote_crude.md — a footnoted P header whose footnote names a crude test, and
#                   prose below the footnote that mentions an adjusted analysis -> the
#                   bound rule still fires (1 Major).
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; DET="$HERE/../check_reported_p_from_counts.py"; cd "$HERE"
bad="$(python3 "$DET" --manuscript fixture/p_bad.md)"; ok="$(python3 "$DET" --manuscript fixture/p_ok.md)"
pass=1
diff -u expected/bad.txt <(printf '%s\n' "$bad") || { echo "FAIL: bad drift" >&2; pass=0; }
diff -u expected/ok.txt  <(printf '%s\n' "$ok")  || { echo "FAIL: ok drift" >&2; pass=0; }
for c in cross cross_ok none adjusted missing_denom adjusted_context alpha_only footnote_crude; do
  out="$(python3 "$DET" --manuscript "fixture/p_$c.md")"
  diff -u "expected/$c.txt" <(printf '%s\n' "$out") || { echo "FAIL: $c drift" >&2; pass=0; }
done
python3 "$DET" --manuscript fixture/p_cross.md --strict --quiet >/dev/null 2>&1 && rx=0 || rx=$?
python3 "$DET" --manuscript fixture/p_cross_ok.md --strict --quiet >/dev/null 2>&1 && rxo=0 || rxo=$?
python3 "$DET" --manuscript fixture/p_none.md --strict --quiet >/dev/null 2>&1 && rn=0 || rn=$?
for c in adjusted missing_denom adjusted_context alpha_only; do
  python3 "$DET" --manuscript "fixture/p_$c.md" --strict --quiet >/dev/null 2>&1 && rc=0 || rc=$?
  [ "$rc" -eq 0 ] || { echo "FAIL: $c should exit 0 (got $rc)" >&2; pass=0; }
done
python3 "$DET" --manuscript fixture/p_footnote_crude.md --strict --quiet >/dev/null 2>&1 && rfc=0 || rfc=$?
[ "${rfc:-0}" -eq 1 ] || { echo "FAIL: footnote_crude should exit 1 (got ${rfc:-0})" >&2; pass=0; }
[ "${rx:-0}" -eq 1 ] || { echo "FAIL: cross should exit 1 (got ${rx:-0})" >&2; pass=0; }
[ "$rxo" -eq 0 ]     || { echo "FAIL: cross_ok should exit 0 (got $rxo)" >&2; pass=0; }
[ "$rn" -eq 0 ]      || { echo "FAIL: none should exit 0 (got $rn)" >&2; pass=0; }
python3 "$DET" --manuscript fixture/p_bad.md --strict --quiet >/dev/null 2>&1 && rb=0 || rb=$?
python3 "$DET" --manuscript fixture/p_ok.md  --strict --quiet >/dev/null 2>&1 && ro=0 || ro=$?
[ "${rb:-0}" -eq 1 ] || { echo "FAIL: bad should exit 1 (got ${rb:-0})" >&2; pass=0; }
[ "$ro" -eq 0 ]      || { echo "FAIL: ok should exit 0 (got $ro)" >&2; pass=0; }
[ "$pass" -eq 1 ] && echo "PASS: reported-P gate flags the non-reproducible p<0.001 and clears the corrected table." || exit 1
