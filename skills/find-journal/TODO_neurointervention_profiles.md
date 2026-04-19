# TODO — Neurointervention / Cerebrovascular Journal Profiles

**Created:** 2026-04-19
**Context:** Paper ① FD Occlusion AI SR 작업 중 find-journal 프로파일 집합에서 뉴로인터벤션 및 인접 영역 주요 저널들이 누락되어 있음을 확인. JNIS는 즉시 추가 완료. 나머지는 별도 세션에서 일괄 추가.
**Working dir for the session:** `/Users/eugene/workspace/medsci-skills/skills/find-journal/references/journal_profiles/`

## 이미 존재 (확인 완료)
- `AJNR.md` (diagnostic + interventional neuroradiology)
- `INSI.md` (Interventional Neuroradiology, SAGE/ESMINT)
- `Neuroradiology.md` (Springer, ESNR)
- `Lancet_Neurology.md`
- `JAMA_Neurology.md`
- `Neurology.md`
- `JNIS.md` ✅ **추가 완료 2026-04-19** (Journal of NeuroInterventional Surgery, BMJ/SNIS)
- `Journal_of_Stroke.md` ✅ **추가 완료 2026-04-19** (Korean Stroke Society, Full OA no APC)

## Private (ISSN 공개소스 확보 후 승격 예정)
- `Stroke.md` (AHA/ASA) — 2026-04-19 사용자 제공 PDF 7종 기반으로 프로파일 본문 완성. ISSN 부재 → `$HOME/.claude/private-journal-profiles/{find-journal,write-paper}/Stroke.md`에 저장. 사용자 ISSN 확인 시 공개 라이브러리로 이동.

## 추가 필요 — Tier 1 (핵심 뉴로인터벤션/뇌혈관)
Priority order:

1. **Stroke: Vascular and Interventional Neurology (SVIN)** (AHA) — 최근 창간 (2021), OA. 순수 뇌혈관 intervention 전문. Scope: neurointervention, mechanical thrombectomy, aneurysm intervention, AVM.
2. **International Journal of Stroke (IJS)** (SAGE, World Stroke Organization) — Q1. Global stroke research·clinical trials.
3. **Cerebrovascular Diseases** (Karger) — Q2. Cerebrovascular 전반, diagnostic + interventional.

## 추가 필요 — Tier 2 (신경외과 / 뇌신경 수술)
6. **Neurosurgery** (Congress of Neurological Surgeons, Wolters Kluwer) — Q1. Aneurysm surgery·endovascular·AVM.
7. **Journal of Neurosurgery (JNS)** (AANS) — Q1. Aneurysm·AVM·stroke surgery·endovascular.
8. **World Neurosurgery** (Elsevier) — Q2/Q3, 수용성 높음. Aneurysm AI prediction 논문 빈출지.
9. **Operative Neurosurgery** (Wolters Kluwer) — technical·video-focused.
10. **Acta Neurochirurgica** (Springer, European) — Q2. European neurosurgery, aneurysm 포함.

## 추가 필요 — Tier 3 (subspecialty / adjacent)
11. **Journal of Cerebral Blood Flow & Metabolism** (SAGE) — cerebral hemodynamics, perfusion.
12. **Neurocritical Care** (Springer, Neurocritical Care Society) — ICH·SAH·stroke ICU.
13. **Clinical Neuroradiology** (Springer) — European, diagnostic + interventional neuroradiology.
14. **Frontiers in Neurology** (Frontiers) — OA, SR-friendly, 수용성 중.
15. **Journal of Neuroimaging** (Wiley, ASN) — stroke imaging·neurovascular.

## 작성 체크리스트 (프로파일 당)

각 프로파일은 INSI.md / JNIS.md 포맷을 그대로 따를 것:

- [ ] Identity: abbreviation, publisher, ISSN (print/online), homepage URL, author guidelines URL
- [ ] Scope (3–5 줄, 저널 공식 aim&scope 기반)
- [ ] Scope Keywords (10–20개, comma-separated)
- [ ] Article Types Accepted (Original, Review, Technical Note, Case Report, Letter 등)
- [ ] Classification: Tier (Q1/Q2/Q3), Open Access (Full OA / Hybrid / Subscription), Field
- [ ] Special Notes (1문단):
  - 저널의 포지셔닝·특이 요구사항(key points, summary statement 등)
  - **Choose X over Y when ...** 형태의 decision-rule 1줄 (인접 저널과 구별)
  - AI policy 1줄 (Required/Recommended, language editing only or all tasks, 디스클로저 위치)

## 작성 방법 권장

- 각 저널 공식 홈페이지 author guidelines에서 원문 확인 (절대 환각 금지)
- IF 수치는 프로파일에 넣지 않음 (변동 + 저작권)
- APC 액수도 프로파일에 넣지 않음 (변동)
- 애매한 필드는 "Not specified" 또는 항목 생략

## 진행 방법

세션 시작 시 지시:
> "medsci-skills find-journal 프로파일 추가 작업 이어서. TODO_neurointervention_profiles.md Tier 1부터 시작해줘."

## 추가 후 필요 작업

- `/Users/eugene/workspace/medsci-skills/CHANGELOG.md`에 프로파일 추가 항목 기록
- 개수 업데이트: `SKILL.md`의 "93 compact journal scope profiles" 수치 조정
- 선택사항: `/Users/eugene/.claude/skills/write-paper/references/journal_profiles/`에도 detail profile 추가 (top-5 enrichment용, 필요시)

---

## 📮 v2.3.0 세션(2026-04-19 later, opus)에서 남긴 메모 — 공개 vs 개인 프로파일 분리 전략

사용자 질문: "신규 저널 프로파일이 개인용이면 공개 레포에 안 올려도 되는데, 어떻게 관리하는 게 좋을까? 레포 다운받은 사람들은 어떻게 작용되는가?"

### 핵심 구분

이 TODO의 Tier 1~3 15개 저널은 **사실상 공용 자산**(Stroke, JNS, Neurosurgery 등 뉴로인터벤션 연구자 누구나 유용). 사용자가 "개인용"이라고 느끼는 이유는 본인 FD Occlusion 프로젝트용이라는 맥락 때문인데, 프로파일 내용 자체는 universal. 따라서 **15개 모두 공개 커밋 권장**.

다만 **진짜 개인적인 프로파일**이 미래에 생길 수 있음:
- "SMC_internal_radiology_only.md" (삼성서울병원 내부 선호 저널 리스트)
- "HRP_Rhim_preferred.md" (임현철 교수님이 선호하는 저널 집합)
- "_submission_blacklist.md" (reject 이력 있는 저널)

이런 건 공개 레포에 올릴 이유가 없음.

### 권장 구조: 2-tier 분리 + 자동 merge

```
medsci-skills/skills/find-journal/references/journal_profiles/   ← 공개 (현재)
~/.claude/private-journal-profiles/                                ← 개인 (신규, gitignore)
```

SKILL.md에 "프로파일은 공개 디렉토리 + 사용자 홈의 private 디렉토리에서 모두 로드" 명시. 두 경로에 동명 파일 있으면 private이 override.

### 구현 (다음 세션 작업 항목)

1. **`.gitignore`에 패턴 추가:**
   ```
   # Personal-use journal profiles (local override directory)
   skills/find-journal/references/journal_profiles/_private/
   ```
   `_private/` 하위는 gitignored → 같은 디렉토리 안에서 관리 가능, 리눅스/맥/윈도우 동일 작동.

2. **SKILL.md 업데이트:**
   - "Profile discovery order: (1) `_private/` override (2) main directory (3) `~/.claude/private-journal-profiles/` optional" 1단락
   - 사용자가 `_private/` 안에 파일 두면 공개 레포에 커밋되지 않음을 명시

3. **README 업데이트:**
   - "Extending with your own profiles" 섹션 신설
   - 예시: "copy Stroke.md to _private/Stroke.md, customize for your institution's preferences, it won't be committed"

### 레포 다운받은 사람에게 미치는 영향

**현재 상태(우려점):** 사용자가 실수로 `SMC_internal_*.md` 같은 개인 파일을 공개 커밋하면 다운로더가 맥락 없이 받아 혼란. 지금까지는 없었음(TODO 15개는 전부 universal).

**2-tier 구현 후:** 다운로더는 공개 93+15 프로파일만 받음. 본인 것은 `_private/`에 추가. 업그레이드 `git pull` 시 `_private/`는 로컬 보존. 이게 vim/nvim 커뮤니티가 쓰는 "user-local config override" 패턴과 동일.

**추가 아이디어 (향후):** 공개 레포에 `_private/TEMPLATE.md` 예시 파일 1개 두면 다운로더가 패턴을 즉시 이해. `_private/TEMPLATE.md`는 추적하지만 `_private/*.md`는 gitignore (negation pattern).

### 결론 (다음 세션에 전달)

- Tier 1~3 15개는 **공개 커밋 OK** (universal 콘텐츠)
- 구조만 `_private/` 서브디렉토리 + gitignore 패턴 사전 세팅
- TEMPLATE.md 예시 파일 1개 둬서 다운로더 온보딩
- SKILL.md + README에 extension 가이드 1단락

이렇게 하면 현재/미래 모두 깨끗히 분리되고 레포 사용자 경험도 개선됨.
