#!/usr/bin/env bash
# Test scripts/check_checklist_dump_leak.py — the audit-dump leak gate.
# Synthetic, PII-free fixtures: a markdown "checklist" that is actually a
# /check-reporting audit dump (positive), a docx carrying the same tokens, and a
# legitimate official STROBE-style checklist (negative). Stdlib-only; PDF paths
# are exercised only opportunistically (poppler may be absent).
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$HERE/../scripts/check_checklist_dump_leak.py"
PASS=0
FAIL=0
ok()  { echo "  PASS: $1"; PASS=$((PASS+1)); }
bad() { echo "  FAIL: $1"; FAIL=$((FAIL+1)); }

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

mkdir -p "$WORK/leaky" "$WORK/clean" "$WORK/docxleak"

# --- positive: a markdown file that is really a /check-reporting audit dump ---
cat > "$WORK/leaky/STROBE_checklist_v4.md" <<'EOF'
# STROBE Reporting Checklist — Audit

## Action Items
- Item 7 [PARTIAL→auto-fixed]: methods location added.
- Auto-fix: harmonised abbreviation.

```json
{"compliance_pct": 81.8, "fixable_by_ai": 3, "check_reporting_version": "1.2",
 "checked_items": 22, "suggested_fix": "add page refs", "log": "qc/_pipeline_log.md"}
```
EOF

# --- negative: a legitimate official STROBE checklist ---
cat > "$WORK/clean/STROBE_checklist.md" <<'EOF'
# STROBE Statement — Checklist of items for cohort studies

| Item | Recommendation | Reported in (page/section) |
|------|----------------|----------------------------|
| 1 | Indicate the study design in the title or abstract | Title; Abstract |
| 6 | Give eligibility criteria, sources and methods of selection | Methods, Participants |
| 13 | Report numbers of individuals at each stage | Results, Figure 1 |
| 16 | Give unadjusted and adjusted estimates with CIs | Results, Table 2 |
EOF

run() { python3 "$SCRIPT" "$@" 2>/dev/null; }

# 1. dump-as-checklist markdown -> exit 1
run --dir "$WORK/leaky" --quiet
[ $? -eq 1 ] && ok "audit-dump markdown fails" || bad "audit-dump markdown should fail"

# 2. JSON reports dump tokens and submission_safe:false
run --dir "$WORK/leaky" --out "$WORK/r.json" --quiet
python3 -c "
import json,sys
d=json.load(open('$WORK/r.json'))
types={f['type'] for f in d['findings']}
sys.exit(0 if 'checklist_dump_token' in types and d['submission_safe'] is False
         and d['summary']['leak'] >= 3 else 1)
" && ok "JSON: dump tokens flagged, not submission_safe" || bad "JSON findings incomplete"

# 3. legitimate official checklist -> exit 0 (no false positive)
run --dir "$WORK/clean" --quiet
[ $? -eq 0 ] && ok "official STROBE checklist passes (no FP)" || bad "official checklist should pass"

# 4. docx carrying audit-dump tokens -> exit 1
python3 - "$WORK" <<'PY'
import sys, os, zipfile
work = sys.argv[1]
body = ("<w:document><w:body><w:p><w:r><w:t>compliance_pct: 81.8 "
        "fixable_by_ai Auto-fix: stale</w:t></w:r></w:p></w:body></w:document>")
with zipfile.ZipFile(os.path.join(work, "docxleak", "checklist.docx"), "w") as z:
    z.writestr("word/document.xml", body)
PY
run --dir "$WORK/docxleak" --quiet
[ $? -eq 1 ] && ok "docx audit-dump fails" || bad "docx audit-dump should fail"

# 5. empty/clean dir with only an official checklist stays clean under repeat run
run --dir "$WORK/clean" --out "$WORK/r2.json" --quiet
python3 -c "
import json,sys
d=json.load(open('$WORK/r2.json'))
sys.exit(0 if d['submission_safe'] is True and not d['findings'] else 1)
" && ok "clean dir reports no findings" || bad "clean dir should report none"

echo ""
echo "test_checklist_dump_leak: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
