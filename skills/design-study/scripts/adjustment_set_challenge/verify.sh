#!/usr/bin/env bash
# Deterministic verifier for the DAG adjustment-set helper (design-study).
# Network-free, stdlib-only. Confirms the four unambiguous adjustment errors are flagged
# on canonical DAGs, clean designs pass, and an instrument-like ancestor is NOT mis-flagged
# as an omitted confounder (the X-free-path soundness fix). Exit 0 = all expectations hold.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
DET="$HERE/../adjustment_set_helper.py"
FIX="$HERE/fixture"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
[ -f "$DET" ] || { echo "ENV-ERR: adjustment_set_helper.py missing" >&2; exit 2; }

fail=0
has() {  # dag exposure outcome adjust verdict   -> verdict MUST be present
  python3 "$DET" --dag "$FIX/$1" --exposure "$2" --outcome "$3" --adjust "$4" --out "$TMP/o.json" --quiet >/dev/null 2>&1 || true
  python3 - "$TMP/o.json" "$5" <<'PY' && printf '  PASS  %s flagged on %s\n' "$5" "$1" || { printf '  FAIL  %s not flagged on %s\n' "$5" "$1"; fail=$((fail+1)); }
import json, sys
d = json.load(open(sys.argv[1]))
raise SystemExit(0 if any(c["verdict"] == sys.argv[2] for c in d["claims"]) else 1)
PY
}
absent() {  # dag exposure outcome adjust verdict  -> verdict MUST be absent
  python3 "$DET" --dag "$FIX/$1" --exposure "$2" --outcome "$3" --adjust "$4" --out "$TMP/o.json" --quiet >/dev/null 2>&1 || true
  python3 - "$TMP/o.json" "$5" <<'PY' && printf '  PASS  %s absent on %s\n' "$5" "$1" || { printf '  FAIL  %s wrongly flagged on %s\n' "$5" "$1"; fail=$((fail+1)); }
import json, sys
d = json.load(open(sys.argv[1]))
raise SystemExit(0 if not any(c["verdict"] == sys.argv[2] for c in d["claims"]) else 1)
PY
}
clean() {  # dag exposure outcome adjust  -> exit 0 under --strict (no Major)
  python3 "$DET" --dag "$FIX/$1" --exposure "$2" --outcome "$3" --adjust "$4" --strict --quiet >/dev/null 2>&1 \
    && printf '  PASS  clean (no Major) on %s adjust=[%s]\n' "$1" "$4" \
    || { printf '  FAIL  %s adjust=[%s] should be clean\n' "$1" "$4"; fail=$((fail+1)); }
}

clean   confounder.json X Y C                     # adjusting the confounder is correct
has     confounder.json X Y ""  CONFOUNDER_OMITTED # omitting it leaves a backdoor open
has     mediator.json   X Y M   MEDIATOR_ADJUSTMENT
has     mbias.json      X Y C   COLLIDER_ADJUSTMENT
absent  mbias.json      X Y C   CONFOUNDER_OMITTED # M-bias collider has no open-backdoor confounder
clean   instrument.json X Y ""                    # FP guard: A->X->Y instrument is not a confounder
absent  instrument.json X Y ""  CONFOUNDER_OMITTED # omitting an instrument is not a bias

echo "fail=$fail"; [[ "$fail" -eq 0 ]] && echo "ALL PASS" || echo "FAILURES: $fail"
exit "$fail"
