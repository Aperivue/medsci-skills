#!/usr/bin/env bash
# Deterministic verifier for the review-request-type challenge card.
# cd HERE so the reported source path is the stable relative "fixture/...".
# Fixtures (synthetic only — no real review, no manuscript, no PII):
#   undisciplined.md — propagate / bootstrap / a second reader / a subset-vs-parent
#                      P value / modelling / a second OPERATOR / re-adjudication, none
#                      justified -> COMPUTATION_HEAVY, COMPUTATION_UNJUSTIFIED,
#                      NEW_DATA_REQUESTED, NESTED_P_REQUESTED, ESTIMATOR_UNNAMED.
#   disciplined.md   — the same review rewritten: disclosure asks, one computation
#                      carrying an explicit "the present tables cannot answer this",
#                      a subset table requested *without* a significance test, and a
#                      cross-table of "adjudicated examinations" the authors' files
#                      already hold -> OK (no false positive on the ask that declines
#                      the invalid test, nor on naming records that already exist).
#   resubmit_mixed.md / canonical_header.md / new_data_only.md / same_line_nested.md — the
#                      recommendation tier (see the block near the end).
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; DET="$HERE/../check_review_request_types.py"; cd "$HERE"
und="$(python3 "$DET" --review fixture/undisciplined.md)"
dis="$(python3 "$DET" --review fixture/disciplined.md)"
pass=1
diff -u expected/undisciplined.txt <(printf '%s\n' "$und") || { echo "FAIL: undisciplined drift" >&2; pass=0; }
diff -u expected/disciplined.txt  <(printf '%s\n' "$dis") || { echo "FAIL: disciplined drift" >&2; pass=0; }
python3 "$DET" --review fixture/undisciplined.md --strict --quiet >/dev/null 2>&1 && ru=0 || ru=$?
python3 "$DET" --review fixture/disciplined.md   --strict --quiet >/dev/null 2>&1 && rd=0 || rd=$?
[ "${ru:-0}" -eq 1 ] || { echo "FAIL: undisciplined should exit 1 (got ${ru:-0})" >&2; pass=0; }
[ "$rd" -eq 0 ]      || { echo "FAIL: disciplined should exit 0 (got $rd)" >&2; pass=0; }
# Domain nouns that share a stem with a computation verb are not requests to compute:
# "computers", "computed tomography", "derivation cohort", "computational resources".
# Every radiology review contains the second one. The verbs themselves must still fire.
nouns="$(python3 "$DET" --review fixture/domain_nouns.md)"
printf '%s\n' "$nouns" | grep "asks=8 disclosure=8 computation=0 " >/dev/null \
  || { echo "FAIL: a domain noun was read as a computation request:" >&2; printf '%s\n' "$nouns" >&2; pass=0; }
python3 "$DET" --review fixture/domain_nouns.md --strict --quiet >/dev/null 2>&1 && rn=0 || rn=$?
[ "$rn" -eq 0 ] || { echo "FAIL: domain_nouns should exit 0 (got $rn)" >&2; pass=0; }
verbs="$(python3 "$DET" --review fixture/computation_verbs.md)"
[ "$(printf '%s\n' "$verbs" | grep -c "COMPUTATION_UNJUSTIFIED")" -eq 5 ] \
  || { echo "FAIL: 'compute', 'derive' and bare 'computing time/power ...' must still be computation requests:" >&2; printf '%s\n' "$verbs" >&2; pass=0; }

# --- Recommendation tier -----------------------------------------------------------------------
# `--recommendation reject-and-resubmit` (the reviewer's explicit statement that the decision
# invites a new submission) changes exactly two finding types, both to INFO under `exempted`:
# NEW_DATA_REQUESTED, and COMPUTATION_HEAVY (its budget guards a revision deadline). Every other
# finding is raised exactly as without the flag. The tier is never read from the draft.
#   resubmit_mixed.md    — header "**Recommendation**: Reject & resubmit" (must be IGNORED); two
#                          new-data asks, a nested P value on its own line, a disclosure ask.
#   canonical_header.md  — header spelled exactly "reject-and-resubmit" (must be IGNORED).
#   new_data_only.md     — new-data asks and the budget they exceed are its only violations.
#   same_line_nested.md  — ONE ask carries both a new-data request and a nested P value.
# expected/tier_blind/ holds text, JSON and --strict exit codes of the PRE-CHANGE script (no tier
# support); every tier-blind run below must match them byte for byte.
GOLD=expected/tier_blind
FIXTURES="undisciplined disciplined domain_nouns computation_verbs resubmit_mixed new_data_only same_line_nested canonical_header"
tmpd="$(mktemp -d)"; trap 'rm -rf "$tmpd"' EXIT
call() {  # call <args...>: run once; stdout/stderr/exit code of THIS call in $tmpd/{out,err}, $code
  python3 "$DET" "$@" >"$tmpd/out" 2>"$tmpd/err" && code=0 || code=$?
}
same() {  # same <golden> <want-exit> <args...>: stdout == golden, stderr empty, exit code == want
  local gold="$1" want="$2"; shift 2
  call "$@"
  cmp -s "$gold" "$tmpd/out" || { echo "FAIL: stdout differs from $gold for: $*" >&2; diff -u "$gold" "$tmpd/out" >&2 || true; pass=0; }
  [ -s "$tmpd/err" ] && { echo "FAIL: stderr not empty for: $*" >&2; cat "$tmpd/err" >&2; pass=0; }
  [ "$code" = "$want" ] || { echo "FAIL: exit $code (want $want) for: $*" >&2; pass=0; }
}
strict_is() {  # strict_is <want-exit> <args...>: --strict --quiet exit code, no output at all
  local want="$1"; shift
  call "$@" --strict --quiet
  [ -s "$tmpd/out" ] || [ -s "$tmpd/err" ] && { echo "FAIL: --quiet printed output for: $*" >&2; pass=0; }
  [ "$code" = "$want" ] || { echo "FAIL: --strict exit $code (want $want) for: $*" >&2; pass=0; }
}

# The golden table must list every fixture above exactly once, and nothing else.
listed="$(cut -d' ' -f1 "$GOLD/strict_exit_codes.txt" | sort | tr '\n' ' ')"
wanted="$(printf '%s\n' $FIXTURES | sort | tr '\n' ' ')"
[ "$listed" = "$wanted" ] || { echo "FAIL: $GOLD/strict_exit_codes.txt lists [$listed], want [$wanted]" >&2; pass=0; }

# (b) no flag, and every non-exempt tier, are byte-identical to the pre-change script: text and
#     JSON (stdout, empty stderr, exit 0 of the same call) and the --strict exit code.
#     resubmit_mixed.md and canonical_header.md prove a header naming the tier is not read.
for fx in $FIXTURES; do
  want="$(awk -v f="$fx" '$1 == f {print $2}' "$GOLD/strict_exit_codes.txt")"
  [ -n "$want" ] || { echo "FAIL: no strict exit code recorded for $fx" >&2; pass=0; continue; }
  for t in "" reject major-revision minor-revision accept; do
    tf=(); [ -n "$t" ] && tf=(--recommendation "$t")
    same "$GOLD/$fx.txt"  0 --review "fixture/$fx.md" ${tf[@]+"${tf[@]}"}
    same "$GOLD/$fx.json" 0 --review "fixture/$fx.md" ${tf[@]+"${tf[@]}"} --json
    strict_is "$want" --review "fixture/$fx.md" ${tf[@]+"${tf[@]}"}
  done
done

# (a) the exempt tier: text goldens for two drafts, then JSON against the pre-change JSON for all.
same expected/undisciplined_resubmit.txt  0 --review fixture/undisciplined.md  --recommendation reject-and-resubmit
same expected/resubmit_mixed_resubmit.txt 0 --review fixture/resubmit_mixed.md --recommendation reject-and-resubmit
python3 - "$DET" "$GOLD" $FIXTURES <<'PY' || pass=0
import json, subprocess, sys
det, gold, fixtures = sys.argv[1], sys.argv[2], sys.argv[3:]
EXEMPT = ("NEW_DATA_REQUESTED", "COMPUTATION_HEAVY")
ok = True
def bad(msg):
    global ok
    print("FAIL: " + msg, file=sys.stderr); ok = False
key = lambda f: (f["kind"], f["line"], f["severity"], f["detail"])
for fx in fixtures:
    blind = json.load(open(f"{gold}/{fx}.json"))          # pre-change output
    r = subprocess.run([sys.executable, det, "--review", f"fixture/{fx}.md", "--json",
                        "--recommendation", "reject-and-resubmit"], capture_output=True, text=True)
    if r.returncode != 0 or r.stderr:
        bad(f"{fx}: exit {r.returncode}, stderr {r.stderr!r}"); continue
    t = json.loads(r.stdout)
    # every other finding: same multiset, same details (sorted lists keep duplicates)
    if sorted(key(f) for f in blind["findings"] if f["kind"] not in EXEMPT) != sorted(key(f) for f in t["findings"]):
        bad(f"{fx}: findings other than NEW_DATA/HEAVY changed under the exempt tier")
    # exactly the two exempt kinds move, line for line, to INFO
    moved = sorted((f["kind"], f["line"]) for f in blind["findings"] if f["kind"] in EXEMPT)
    if sorted((f["kind"], f["line"]) for f in t["exempted"]) != moved or any(f["severity"] != "INFO" for f in t["exempted"]):
        bad(f"{fx}: exempted is not exactly the pre-change {moved} as INFO")
    for k in ("asks", "disclosure", "computation", "new_data", "descriptive"):
        if t[k] != blind[k]:
            bad(f"{fx}: count {k} changed {blind[k]} -> {t[k]}")
    want_verdict = "REQUEST-TYPE VIOLATIONS" if any(f["severity"] == "MAJOR" for f in t["findings"]) else "OK"
    if t["verdict"] != want_verdict or t.get("recommendation") != "reject-and-resubmit":
        bad(f"{fx}: verdict {t['verdict']!r} / recommendation {t.get('recommendation')!r}")
sys.exit(0 if ok else 1)
PY

# One ask with a new-data request AND a nested P value: before the change both were MAJOR on that
# line; under the exempt tier the new-data one is INFO and the nested P value stays MAJOR.
grep -c "^\[MAJOR\] NEW_DATA_REQUESTED L5\|^\[MAJOR\] NESTED_P_REQUESTED L5" "$GOLD/same_line_nested.txt" | grep -x 2 >/dev/null \
  || { echo "FAIL: same_line_nested golden should hold both MAJORs on L5" >&2; pass=0; }
call --review fixture/same_line_nested.md --recommendation reject-and-resubmit
grep "^\[MAJOR\] NESTED_P_REQUESTED L5" "$tmpd/out" >/dev/null && grep "^\[INFO\] NEW_DATA_REQUESTED L5" "$tmpd/out" >/dev/null \
  || { echo "FAIL: same_line_nested: NESTED_P must stay MAJOR and NEW_DATA become INFO on L5" >&2; pass=0; }
strict_is 1 --review fixture/same_line_nested.md --recommendation reject-and-resubmit

# The verdict flip and its limit, text + JSON + --strict.
strict_is 0 --review fixture/new_data_only.md --recommendation reject-and-resubmit
call --review fixture/new_data_only.md --recommendation reject-and-resubmit
head -1 "$tmpd/out" | grep "^== OK ==" >/dev/null || { echo "FAIL: new_data_only text verdict should be OK" >&2; pass=0; }
call --review fixture/new_data_only.md --recommendation reject-and-resubmit --json
python3 -c 'import json,sys; sys.exit(json.load(open(sys.argv[1]))["verdict"] != "OK")' "$tmpd/out" \
  || { echo "FAIL: new_data_only JSON verdict should be OK" >&2; pass=0; }
strict_is 1 --review fixture/resubmit_mixed.md --recommendation reject-and-resubmit
call --review fixture/resubmit_mixed.md --recommendation reject-and-resubmit --json
python3 -c 'import json,sys; sys.exit(json.load(open(sys.argv[1]))["verdict"] != "REQUEST-TYPE VIOLATIONS")' "$tmpd/out" \
  || { echo "FAIL: resubmit_mixed JSON verdict should be REQUEST-TYPE VIOLATIONS" >&2; pass=0; }
# the --recommendation=VALUE spelling works too
strict_is 0 --review fixture/new_data_only.md --recommendation=reject-and-resubmit

# (c)/(d) only the five enumerated values, spelled out in full. Free text ("Reject & resubmit",
# "resubmit") and an abbreviated flag ("--rec", which was an unknown option before) exit 2.
for v in 'Reject & resubmit' resubmit 'reject and resubmit' maybe; do
  call --review fixture/new_data_only.md --recommendation "$v"
  [ "$code" -eq 2 ] || { echo "FAIL: --recommendation '$v' should exit 2 (got $code)" >&2; pass=0; }
  grep "reject-and-resubmit" "$tmpd/err" >/dev/null || { echo "FAIL: usage error for '$v' must list the choices" >&2; pass=0; }
done
for ab in --rec --recommend --rec=reject-and-resubmit; do
  if [ "$ab" = "--rec=reject-and-resubmit" ]; then call --review fixture/new_data_only.md "$ab" --strict
  else call --review fixture/new_data_only.md "$ab" reject-and-resubmit --strict; fi
  [ "$code" -eq 2 ] || { echo "FAIL: abbreviated '$ab' should exit 2 (got $code)" >&2; pass=0; }
  [ -s "$tmpd/out" ] && { echo "FAIL: abbreviated '$ab' must not print an audit" >&2; pass=0; }
done
# The abbreviations argparse accepted for --review before --recommendation existed still work.
for ab in --re --r --rev; do
  same "$GOLD/undisciplined.txt" 0 "$ab" fixture/undisciplined.md
done

# (e) the domain-noun fix holds under the exempt tier too.
call --review fixture/domain_nouns.md --recommendation reject-and-resubmit
grep "asks=8 disclosure=8 computation=0 " "$tmpd/out" >/dev/null \
  || { echo "FAIL: domain nouns read as computation under reject-and-resubmit" >&2; pass=0; }
call --review fixture/computation_verbs.md --recommendation reject-and-resubmit
[ "$(grep -c "COMPUTATION_UNJUSTIFIED" "$tmpd/out")" -eq 5 ] \
  || { echo "FAIL: computation verbs must still fire under reject-and-resubmit" >&2; pass=0; }

[ "$pass" -eq 1 ] && echo "PASS: request-type gate flags unjustified computation and clears a disclosure-led review; --recommendation reject-and-resubmit turns only NEW_DATA_REQUESTED and COMPUTATION_HEAVY into INFO." || exit 1
