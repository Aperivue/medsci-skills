#!/usr/bin/env bash
# Deterministic verifier for the MLLM-evaluation completeness challenge (mllm-eval).
# Network-free, stdlib-only. The gate flags an n-gram-only, faithfulness-free,
# contamination-unaddressed plan and clears a complete one. Exit 0 = all hold.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
DET="$HERE/../check_mllm_eval_completeness.py"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT

# (1) bad plan -> exit 1 with the core Major gaps
python3 "$DET" --plan "$HERE/fixture/plan_bad.md" --task report_generation --out "$TMP/bad.json" --strict --quiet \
  && { echo "FAIL: the bad plan should exit 1" >&2; exit 1; } || true
python3 - "$TMP/bad.json" <<'PY' || exit 1
import json, sys
v = {c["verdict"] for c in json.load(open(sys.argv[1]))["claims"]}
for need in ("NGRAM_ONLY", "FAITHFULNESS_MISSING", "REFERENCE_STANDARD_MISSING", "CONTAMINATION_UNADDRESSED"):
    assert need in v, f"{need} not flagged"
print("  bad plan flagged: NGRAM_ONLY + FAITHFULNESS + REFERENCE_STANDARD + CONTAMINATION")
PY

# (2) complete plan -> exit 0
python3 "$DET" --plan "$HERE/fixture/plan_good.md" --task report_generation --strict --quiet \
  || { echo "FAIL: the complete plan should pass (exit 0)" >&2; exit 1; }

echo "PASS: MLLM completeness gate flags the n-gram-only/faithfulness-free plan and clears a complete one."
