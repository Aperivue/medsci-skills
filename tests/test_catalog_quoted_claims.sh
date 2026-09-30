#!/usr/bin/env bash
# Self-test for scripts/validate_catalog_consistency.py: a count inside a double-quoted
# anti-example is a mention, not a claim.
#
# The defect: MEDSCI_AUDIT.md warns that the suite should not be collapsed into a single
# "64 detectors, validated by E1/E7" claim. The gate read the 64 inside that quoted example as
# the live detector total and failed the build; the only way through was to replace the number
# with "N", i.e. to make the document worse to satisfy the checker.
#
#  1) quoted anti-examples (detector total, skills prose, curly quotes) -> NOT claims
#  2) the same stale counts written unquoted                              -> still claims (fire)
# Synthetic docs in a temp ROOT; disk counts are pinned, so the real repo is never read.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT

cat > "$tmp/MEDSCI_AUDIT.md" <<'EOF'
# MedSci-Audit

The suite's size and its evaluation evidence are two separate facts, and should not be collapsed into a single "64 detectors, validated by E1/E7" claim.

A style note: do not write “57 deterministic detectors” from memory; read the catalog.

The stale line: a suite of 57 deterministic detectors.
EOF
cat > "$tmp/README.md" <<'EOF'
# README

Style: never write "All 57 skills" in prose; the count is generated.

All 57 skills, grouped by lifecycle stage.
EOF

python3 - "$ROOT/scripts/validate_catalog_consistency.py" "$tmp" <<'PY'
import importlib.util, sys
from pathlib import Path
spec = importlib.util.spec_from_file_location("vcc", sys.argv[1])
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
m.ROOT = Path(sys.argv[2])
m.disk_counts = lambda: {"skills": 59, "reporting_guidelines": 49, "integrity_detectors": 90,
                         "plugins": 9, "journal_profiles_find": 1, "journal_profiles_write": 1}
claims = m.doc_claims()
drift = [(rel, n, ctx) for rel, n, exp, ctx in claims if n != exp]

# 1) quoted anti-examples are not claims: MEDSCI_AUDIT L3 ("64 detectors, validated"),
#    L5 (curly-quoted "57 deterministic detectors"), README L3 ("All 57 skills").
bad = [d for d in drift if (d[0], d[2].split()[0]) in
       {("MEDSCI_AUDIT.md", "L3"), ("MEDSCI_AUDIT.md", "L5"), ("README.md", "L3")}]
assert not bad, f"a quoted anti-example was read as a live count claim: {bad}"
assert not any(n == 64 for _r, n, _c in drift), f"the quoted 64 was read as a claim: {drift}"

# 2) the same stale counts, unquoted, still fire.
assert ("MEDSCI_AUDIT.md", 57, "L7 detector total") in drift, drift
assert ("README.md", 57, "L5 skills prose") in drift, drift
print(f"  PASS  quoted anti-examples ignored; {len(drift)} unquoted stale count(s) still fire")
PY
echo "test_catalog_quoted_claims: OK"
