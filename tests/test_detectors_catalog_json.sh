#!/usr/bin/env bash
# Test scripts/gen_detectors_catalog_json.py — the MedSci-Audit detector registry
# generator/gate. Uses synthetic, PII-free fixtures via --skills-dir / --out. Also
# asserts the committed metadata/detectors_catalog.json is in sync AND that its
# detector_count equals metadata/catalog_counts.json::integrity_detectors.
set -u

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SCRIPT="$REPO_ROOT/scripts/gen_detectors_catalog_json.py"
PASS=0
FAIL=0

ok()  { echo "  PASS: $1"; PASS=$((PASS+1)); }
bad() { echo "  FAIL: $1"; FAIL=$((FAIL+1)); }

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

mk_detector() {  # skill detector_id
  local d="$WORK/skills/$1/scripts"
  mkdir -p "$d"
  printf -- '"""A synthetic %s detector for testing. Second sentence ignored."""\n' "$2" > "$d/$2.py"
}

# --- 1. happy path: mapped detector ids generate + round-trip on --check ---
rm -rf "$WORK/skills"
mk_detector foo check_scope_coherence   # -> confounding_scope_estimand
mk_detector bar verify_refs             # -> citation_reference
python3 "$SCRIPT" --skills-dir "$WORK/skills" --out "$WORK/det.json" >/dev/null 2>&1
if [ $? -eq 0 ] && [ -f "$WORK/det.json" ]; then ok "generates catalog for mapped detectors"; else bad "generate failed"; fi

python3 "$SCRIPT" --skills-dir "$WORK/skills" --out "$WORK/det.json" --check >/dev/null 2>&1
[ $? -eq 0 ] && ok "--check round-trips on fresh output" || bad "--check should pass right after generate"

python3 -c "
import json,sys
d=json.load(open('$WORK/det.json'))
ids={x['id'] for x in d['detectors']}
fams={x['family'] for x in d['detectors']}
first=next(x for x in d['detectors'] if x['id']=='verify_refs')
sys.exit(0 if d['detector_count']==2 and ids=={'check_scope_coherence','verify_refs'}
         and fams=={'confounding_scope_estimand','citation_reference'}
         and first['skill']=='bar' and first['description'].endswith('.') else 1)
" && ok "JSON shape: count + ids + family mapping + skill + 1-sentence desc" || bad "JSON shape wrong"

# --- 2. drift: editing the file makes --check fail ---
printf '{"tampered":true}\n' > "$WORK/det.json"
python3 "$SCRIPT" --skills-dir "$WORK/skills" --out "$WORK/det.json" --check >/dev/null 2>&1
[ $? -eq 1 ] && ok "--check detects drift (exit 1)" || bad "--check should fail on drift"

# --- 3. fail-loud: an UNMAPPED detector id aborts generation ---
mk_detector baz check_brand_new_detector
python3 "$SCRIPT" --skills-dir "$WORK/skills" --out "$WORK/det2.json" >/dev/null 2>&1
[ $? -eq 1 ] && ok "unmapped detector id aborts (exit 1)" || bad "unmapped detector id must fail loud"

# --- 4. the committed repo catalog is in sync (the actual CI gate) ---
python3 "$SCRIPT" --check >/dev/null 2>&1
[ $? -eq 0 ] && ok "committed metadata/detectors_catalog.json in sync" || bad "repo detector catalog drifted — run the generator"

# --- 5. detector_count == catalog_counts.json::integrity_detectors (cross-SSOT) ---
python3 -c "
import json,sys
det=json.load(open('$REPO_ROOT/metadata/detectors_catalog.json'))
cnt=json.load(open('$REPO_ROOT/metadata/catalog_counts.json'))
sys.exit(0 if det['detector_count']==cnt['integrity_detectors'] else 1)
" && ok "detector_count == catalog_counts.integrity_detectors" || bad "detector enumeration != counted integrity_detectors"

echo ""
echo "test_detectors_catalog_json: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
