#!/usr/bin/env bash
# Test scripts/check_checklist_version.py — the A4b checklist-version staleness gate.
# Synthetic, PII-free fixtures: a checklist targeting an older version / a changed
# hash / a different file / no version metadata, vs an in-sync checklist.
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$HERE/../scripts/check_checklist_version.py"
PASS=0
FAIL=0
ok()  { echo "  PASS: $1"; PASS=$((PASS+1)); }
bad() { echo "  FAIL: $1"; FAIL=$((FAIL+1)); }

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

# current manuscript (v8) + its sha256 (first 12)
cat > "$WORK/manuscript_v8.md" <<'EOF'
## Title
A cohort study, version 8.
EOF
SHA=$(python3 -c "import hashlib;print(hashlib.sha256(open('$WORK/manuscript_v8.md','rb').read()).hexdigest()[:12])")

mk_json() {  # file target_manuscript target_version source_sha256
  cat > "$1" <<EOF
{"check_reporting_version":"1.1","manuscript_title":"A cohort study",
 "target_manuscript":"$2","target_version":"$3","source_sha256":"$4",
 "guideline":"STROBE","total_items":22,"present":18}
EOF
}

run() { python3 "$SCRIPT" "$@" 2>/dev/null; }

# 1. in-sync checklist (same file/version/hash) -> exit 0
mk_json "$WORK/ck_ok.json" "manuscript_v8.md" "v8" "$SHA"
run --checklist "$WORK/ck_ok.json" --manuscript "$WORK/manuscript_v8.md" --quiet
[ $? -eq 0 ] && ok "in-sync checklist passes" || bad "in-sync should pass"

# 2. older target_version -> stale (exit 1)
mk_json "$WORK/ck_oldver.json" "manuscript_v6.md" "v6" ""
run --checklist "$WORK/ck_oldver.json" --manuscript "$WORK/manuscript_v8.md" --out "$WORK/r.json" --quiet
[ $? -eq 1 ] && ok "older target_version -> exit 1" || bad "older version should fail"
python3 -c "import json,sys;d=json.load(open('$WORK/r.json'));sys.exit(0 if d['findings'][0]['type']=='checklist_version_stale' else 1)" \
  && ok "reports checklist_version_stale" || bad "wrong finding type for version"

# 3. changed content hash (same version) -> stale
mk_json "$WORK/ck_hash.json" "manuscript_v8.md" "v8" "deadbeef0000"
run --checklist "$WORK/ck_hash.json" --manuscript "$WORK/manuscript_v8.md" --out "$WORK/r2.json" --quiet
python3 -c "import json,sys;d=json.load(open('$WORK/r2.json'));sys.exit(0 if d['findings'][0]['type']=='checklist_content_stale' else 1)" \
  && ok "changed hash -> checklist_content_stale" || bad "hash drift not detected"

# 4. no version metadata (pre-v1.1) -> unverifiable (exit 1)
echo '{"check_reporting_version":"1.0","guideline":"STROBE","present":18}' > "$WORK/ck_old.json"
run --checklist "$WORK/ck_old.json" --manuscript "$WORK/manuscript_v8.md" --out "$WORK/r3.json" --quiet
[ $? -eq 1 ] && ok "no version metadata -> exit 1" || bad "missing metadata should fail"
python3 -c "import json,sys;d=json.load(open('$WORK/r3.json'));sys.exit(0 if d['findings'][0]['type']=='checklist_no_version_metadata' else 1)" \
  && ok "reports checklist_no_version_metadata" || bad "wrong finding for missing metadata"

# 5. markdown report with header fields (no JSON) -> parsed + stale
cat > "$WORK/report_v6.md" <<'EOF'
## Reporting Guideline Compliance Report
Manuscript: A cohort study
Target manuscript file: manuscript_v6.md
Target version: v6
Guideline: STROBE 2007
EOF
run --checklist "$WORK/report_v6.md" --manuscript "$WORK/manuscript_v8.md" --quiet
[ $? -eq 1 ] && ok "markdown header (v6) flagged stale vs v8" || bad "markdown header not parsed"

echo ""
echo "test_checklist_version: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
