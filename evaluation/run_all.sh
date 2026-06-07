#!/usr/bin/env bash
# Run the MedSci Skills evaluation suite.
#
#   bash evaluation/run_all.sh             # deterministic, self-contained suite
#   bash evaluation/run_all.sh --with-llm  # also run the LLM-loop harnesses (E2, E9)
#   bash evaluation/run_all.sh --online    # enable network citation defects in E1
#
# Deterministic harnesses need no API key and no network. The LLM-loop
# harnesses (E2, E9) gracefully record NOT_RUN unless --with-llm AND a
# runner/API key is configured.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
PY="${PYTHON:-python3}"
WITH_LLM=0
ONLINE=0
for arg in "$@"; do
  case "$arg" in
    --with-llm) WITH_LLM=1 ;;
    --online)   ONLINE=1 ;;
    *) echo "unknown arg: $arg" >&2; exit 2 ;;
  esac
done

run() { echo; echo "=== $* ==="; "$PY" "$@"; }

# Deterministic, self-contained
run "$HERE/h6_inventory_drift/run_e7_inventory.py"
run "$HERE/h6_inventory_drift/run_e8_drift.py"
run "$HERE/h3_fresh_clone/run_h3.py"
E1_ARGS=("$HERE/h1_seeded_defects/run_h1.py")
[ "$ONLINE" -eq 1 ] && E1_ARGS+=(--online)
run "${E1_ARGS[@]}"
run "$HERE/h4_audit_trail/run_h4.py"
run "$HERE/h5_portability/run_h5.py"
run "$HERE/e3_cost_time/aggregate_timing.py"

# LLM-loop harnesses: ship, NOT_RUN by default
if [ "$WITH_LLM" -eq 1 ]; then
  run "$HERE/h2_llm_baseline/run_h2.py" --with-llm
  run "$HERE/h7_selfreview_convergence/run_h7.py" --with-llm
else
  run "$HERE/h2_llm_baseline/run_h2.py"
  run "$HERE/h7_selfreview_convergence/run_h7.py"
fi

echo
echo "=== evaluation suite complete ==="
