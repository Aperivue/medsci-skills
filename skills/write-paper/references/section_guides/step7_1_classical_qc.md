# Step 7.1 Extension — Classical Manuscript Style QC

Senior MA reviewer 대비 글로벌 룰 `~/.claude/rules/manuscript-style-classical.md` (11항목)을 자동 검증하는 grep-based 체크리스트. Step 7.1 AI Pattern Scan과 함께 실행.

**Why**: Senior MA mentors routinely flag § 기호, AI Disclosure boilerplate, 산문 형 eligibility, em-dash 남용, AI-style heading을 "AI 패턴"으로 지적. Manuscript-level 자동 grep으로 사전 차단.

## 자동 점검 7건 (Phase 7.1 진입 시 일괄 실행)

```bash
MD=manuscript/manuscript.md

# 1. § 기호 0건 강제
N=$(grep -c "§" "$MD" || true)
[ "$N" -eq 0 ] || echo "FAIL: § 기호 ${N}건 — 모두 제거 또는 (Methods)/(Results)로 대체"

# 2. AI Disclosure 단락 본문 미존재 (저널 양식·cover letter에만)
grep -inE "artificial intelligence disclosure|generative ai was not used|ai acknowledg(e)?ment" "$MD" \
    && echo "FAIL: AI Disclosure 단락이 본문에 존재 — cover letter / submission form으로 이동"

# 3. Heading style — 5개 메인 섹션 대문자+bold
for H in METHODS RESULTS DISCUSSION INTRODUCTION CONCLUSION; do
    grep -qE "^## \*\*${H}\*\*" "$MD" || echo "WARN: '## **${H}**' heading 부재 (또는 변형)"
done

# 4. Eligibility / Inclusion criteria — numbered list 권장
grep -A 3 -inE "^#{2,4}.*(eligibility|inclusion criteria|exclusion criteria)" "$MD" \
    | grep -qE "\([0-9]+\)|^[0-9]+\." \
    || echo "WARN: Eligibility/Inclusion criteria 산문 가능성 — '(1)... (2)...' numbered list로 변환 검토"

# 5. Funding 섹션에 grant ID placeholder 미존재
grep -inE "grant\s*(id|number)?\s*[:#]\s*(TBD|TODO|XXX|\[insert\]|\[grant)" "$MD" \
    && echo "FAIL: Funding grant ID placeholder 잔존 — senior author에게 직접 입력 요청"

# 6. PROSPERO chronology 본문 미존재 (등록번호 1줄만 허용)
grep -inE "prospero.*(amendment|chronology|lodged|registered on \d{4}-\d{2}-\d{2}.*amended)" "$MD" \
    && echo "FAIL: PROSPERO chronology / amendment lodging 본문에 존재 — supplementary로 위임"

# 7. Em-dash 남용 (manuscript당 < 25 권장)
N=$(grep -o "—" "$MD" | wc -l | tr -d ' ')
[ "$N" -lt 25 ] || echo "WARN: em-dash ${N}건 (>=25) — AI generation 시그널, 콤마/콜론으로 분산"

# 8. Reference list 손-타이핑 0건
# manuscript-references.md 룰에 따라 본문 인용은 [@bibkey] 또는 [N] 만 허용.
# References 섹션에 hand-typed 항목이 있으면 빌드 산출물(.docx) verify 필요 — Step 7.6a로 위임.
```

## 통과 기준

- FAIL = 0 (반드시 수정).
- WARN ≤ 2 (사용자 검토 후 ack 가능).
- 결과는 `qc/_pipeline_log.md`에 timestamp + raw output 기록.

## 책임 경계

이 단계는 **자동 grep**만 수행. 다음은 별도 단계:
- Pattern 19–21 (§, self-reference, AI Disclosure boilerplate) 본문 rewrite → `/humanize`
- Reference 손-타이핑 검증 → Step 7.6a `check_xref.py` (DOCX 빌드 후)
- PRISMA 산수 일관성 → `/check-reporting prisma` Step 4d
- Funding grant ID 실제 값 입력 → senior author 직접 회람

## 관련

- 글로벌 룰: `~/.claude/rules/manuscript-style-classical.md` (11항목 motivation)
- 회람 워크플로우: `~/.claude/rules/senior-mentor-circulation.md`
- AI-draft 처리: `~/.claude/rules/ai-drafted-document-policy.md`
- Reference 손-타이핑 금지: `~/.claude/rules/manuscript-references.md`
- 관련 스킬: `/humanize` (Pattern 19–21), `/check-reporting prisma` (Step 4d)
