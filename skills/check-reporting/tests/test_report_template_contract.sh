#!/usr/bin/env bash
# Contract test for the Part D JSON example in references/report_templates.md.
# The worked example is what the model copies, so it must obey the field contract in
# SKILL.md: compliance_pct = present / (total_items - na) * 100 (one decimal), and an
# action item whose suggested_fix still holds a bracketed placeholder ([N], [rationale])
# is never fixable_by_ai: true (write-paper Phase 7 auto-inserts fixable items).
# Stdlib-only (python3); no network.
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE="$HERE/../references/report_templates.md"
[[ -f "$TEMPLATE" ]] || { echo "ENV-ERR: missing $TEMPLATE" >&2; exit 2; }

echo "test_report_template_contract:"
python3 - "$TEMPLATE" <<'PY'
import json, re, sys

def violations(d):
    out = []
    total, na = d["total_items"], d["na"]
    if d["present"] + d["partial"] + d["missing"] + na != total:
        out.append("status counts do not sum to total_items")
    expected = None if total == na else round(d["present"] / (total - na) * 100, 1)
    if d["compliance_pct"] != expected:
        out.append(f"compliance_pct {d['compliance_pct']} != formula {expected}")
    for it in d.get("action_items", []):
        if it.get("fixable_by_ai") and re.search(r"\[[^\]]+\]", it.get("suggested_fix", "")):
            out.append(f"item {it.get('item_number')}: placeholder in suggested_fix but fixable_by_ai true")
    return out

text = open(sys.argv[1], encoding="utf-8").read()
blocks = [b for b in re.findall(r"```json\n(.*?)```", text, flags=re.S) if '"compliance_pct"' in b]
fail = 0
def check(label, ok):
    global fail
    print(f"  {'PASS' if ok else 'FAIL'}  {label}")
    fail += 0 if ok else 1

check("template has one Part D JSON example", len(blocks) == 1)
if blocks:
    d = json.loads(blocks[0])
    v = violations(d)
    check("template example obeys the contract" + (f" ({'; '.join(v)})" if v else ""), not v)
    sample = [i for i in d["action_items"] if "sample size" in i["item_name"].lower()]
    check("sample-size item is fixable_by_ai false", bool(sample) and all(i["fixable_by_ai"] is False for i in sample))

    # Positive controls: the checker must catch the two defects it guards against.
    bad_pct = dict(d, compliance_pct=88.9)
    check("checker flags a compliance_pct off the formula", bool(violations(bad_pct)))
    bad_fix = dict(d, action_items=[{"item_number": 12, "item_name": "Sample size justification",
                                     "suggested_fix": "A minimum of [N] cases was required.",
                                     "fixable_by_ai": True}])
    check("checker flags a placeholder fix marked fixable_by_ai", bool(violations(bad_fix)))
    # Negative control: all items N/A -> compliance_pct null is accepted.
    all_na = dict(d, present=0, partial=0, missing=0, na=d["total_items"], compliance_pct=None, action_items=[])
    check("all-N/A report with compliance_pct null is accepted", not violations(all_na))
sys.exit(1 if fail else 0)
PY
rc=$?
if [[ $rc -eq 0 ]]; then echo "  OK"; else echo "  failed"; fi
exit $rc
