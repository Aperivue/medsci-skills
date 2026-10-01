#!/usr/bin/env bash
# Self-test for Layer 5 of scripts/validate_catalog_consistency.py: the translated READMEs.
#
# The defect: the Italian locale pack (#544) moved README.md to "locale packs for eleven
# countries" while README.ko.md kept "10개국" and README.zh-CN.md kept "十个国家". Only the
# shields badge was gated in the translations, so nothing failed.
#
#  1) translations that agree (digits, Chinese numerals)        -> no failure
#  2) the #544 drift: English says eleven, translations say ten -> fires for both files
#  3) a skill/detector/guideline count off from disk            -> fires
#  4) a reworded sentence the pattern no longer matches         -> fires (no silent retirement)
#  5) no English locale claim                                   -> locale parity is not asserted
# Synthetic docs in a temp ROOT; disk counts are pinned, so the real repo is never read.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT

python3 - "$ROOT/scripts/validate_catalog_consistency.py" "$tmp" <<'PY'
import importlib.util, sys
from pathlib import Path
spec = importlib.util.spec_from_file_location("vcc", sys.argv[1])
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
root = Path(sys.argv[2])
m.ROOT = root
m.disk_counts = lambda: {"skills": 54, "reporting_guidelines": 49, "integrity_detectors": 90,
                         "plugins": 9, "journal_profiles_find": 1, "journal_profiles_write": 1}

def write(en_locale, ko, zh):
    (root / "README.md").write_text(
        f"# README\n\nIt uses regex (locale packs for {en_locale} countries).\n" if en_locale
        else "# README\n\nNo locale sentence.\n", encoding="utf-8")
    (root / "README.ko.md").write_text(ko, encoding="utf-8")
    (root / "README.zh-CN.md").write_text(zh, encoding="utf-8")

def ko(loc="11", g="49", s="54", d="90"):
    return (f"- 원고를 {g}개 reporting guideline과 비교\n{s}개 스킬 전체를 묶은 표\n"
            f"휴리스틱({loc}개국 locale pack)으로 찾습니다. {d}개의 deterministic detector는\n")

def zh(loc="十一", g="49", s="54", d="90"):
    return (f"- 按 {g} 项报告规范核对\n全部 {s} 个技能按阶段分组\n"
            f"规则（含{loc}个国家的 locale 包）检测。{d} 个确定性检测器会\n")

# 1) agreement, including Chinese numerals in both forms
write("eleven", ko(), zh())
assert m.translated_claim_failures() == [], m.translated_claim_failures()
write("twenty", ko(loc="20"), zh(loc="二十"))
assert m.translated_claim_failures() == [], m.translated_claim_failures()
assert [m._parse_count(t) for t in ("十", "十一", "二十", "二十三", "九", "eleven", "7")] == \
       [10, 11, 20, 23, 9, 11, 7]
print("  PASS  translations that agree are silent (digits and Chinese numerals)")

# 2) the #544 drift
write("eleven", ko(loc="10"), zh(loc="十"))
f = m.translated_claim_failures()
assert any(x.startswith("README.ko.md") and "locale_packs: claims 10" in x for x in f), f
assert any(x.startswith("README.zh-CN.md") and "locale_packs: claims 十" in x for x in f), f
assert len(f) == 2, f
print("  PASS  the #544 drift (English eleven, translations ten) fires in both files")

# 3) counts against disk
write("eleven", ko(s="53"), zh(d="89", g="48"))
f = m.translated_claim_failures()
assert any("README.ko.md" in x and "skills: claims 53" in x for x in f), f
assert any("README.zh-CN.md" in x and "integrity_detectors: claims 89" in x for x in f), f
assert any("README.zh-CN.md" in x and "reporting_guidelines: claims 48" in x for x in f), f
assert len(f) == 3, f
print("  PASS  a stale skill, detector or guideline count fires")

# 4) a reworded sentence must not retire its gate silently
write("eleven", ko().replace("개 스킬 전체", "개의 스킬"), zh())
f = m.translated_claim_failures()
assert len(f) == 1 and f[0].startswith("README.ko.md: no skills claim matched"), f
print("  PASS  a reworded claim fails loudly instead of going unchecked")

# 5) no English locale claim -> parity is not asserted (nothing to hold the translation to)
write(None, ko(loc="3"), zh(loc="三"))
assert m.translated_claim_failures() == [], m.translated_claim_failures()
print("  PASS  without an English locale claim, locale parity is not asserted")
PY
echo "test_catalog_translated_claims: OK"
