# RESUME — Flow Diagram Final Reflection + CXR Workflow Upgrade + MA-03 P0

**⚠️ 이 파일은 이어서 작업하라는 지시입니다. "마무리할까요?" 질문 금지.**
**진입점**: 아래 `## 즉시 실행` 첫 항목부터.
**작업 디렉토리**: `/Users/eugene/workspace/medsci-skills` (발사대). 실제 작업은 각 프로젝트 repo.

---

## 직전 세션 완료 (2026-04-20~21)

- **Flow diagram retrofit 9/10 완료** — STROBE 2 (CK-5, CAC) / STARD 3 (CXRscoliosis, SkullFx P2, MeducAI P1 병렬) / PRISMA 2 (MA-01, MA-21) / PRISMA-DTA 1 (MA-02) / CONSORT-edu 1 (MeducAI P3 병렬). R+DiagrammeR Graphviz `dot` 엔진, Arial 단색 outline, `\l` bullets, 벡터 PDF + 300/600 dpi PNG.
- **medsci-skills 커밋** (137ee32) — `make-figures/SKILL.md`에 per-project `create_figure1.R` 패턴 + 9 exemplar 경로 + no-HTML-labels 규칙 코드화. CHANGELOG rollout 기록.
- **Figure 참조 경로 전수 검증** — 9/9 프로젝트 다음 rebuild 시 새 figure 자동 반영됨 (아래 §반영 매트릭스).

## 미결 (다음 세션 진입)

1. **최종 산출문에 새 figure 실제 반영** — 각 프로젝트별 DOCX/PDF rebuild 돌려서 **submission-ready 파일에 새 monochrome Fig 1이 들어가 있음을 확인**. 파일은 준비됨, rebuild 트리거만 필요.
2. **CXRscoliosis workflow 업그레이드** — `Document/build_manuscript.py`는 figure caption만 쓰고 실제 그림은 Word 수동 embed. CK-5 `build_unified_docx.py` / CAC `build_manuscript_docx.py` 패턴 참조해 `add_figure()` 호출 추가 → python-docx 기반 full-build로 통일.
3. **MA-03 CBCT_Ablation P0 HALT 해결** — screening log / Methods / Results 3-way 수치 불일치. 핸드오프 `/Users/eugene/workspace/10_Meta_Analysis/03_CBCT_Ablation/HANDOFF_prisma_flow_reconciliation.md` 4단계 (1_Search CSV 원본 재확인 → 3 위치 동시 수정 → v5→v6 DOCX rebuild → flow retrofit 재개).

---

## 즉시 실행

### Step 1. 각 프로젝트 rebuild + 최종 파일 figure 반영 확인

프로젝트별 rebuild 트리거 + 검증:

| # | Project | Rebuild command | 확인 파일 |
|---|---|---|---|
| 1 | CK-5 Emphysema | `cd .../05_Emphysema_COPD_Mortality/manuscript && python3 build_unified_docx.py` | `manuscript_v6_final.docx` Fig 1. Chest submission은 `submission/chest/`에 figure1_flow.{png,pdf} 업로드 파일 직접 사용 — CHECKLIST.md:36 개별 업로드 규약, docx embed 아님. |
| 2 | CAC_Warranty | `cd .../01_CAC_Warranty_Period/manuscript && python3 build_manuscript_docx.py` | 최종 DOCX Fig 1 embed 확인 |
| 3 | CXRscoliosis | **Step 2 선행** (워크플로우 업그레이드 후 rebuild) | — |
| 4 | SkullFx P2 | manuscript DOCX는 Word 편집 기반 — `figures/Figure1_STARD_flowchart.{pdf,png}`가 이미 교체됨. 다음 DOCX 편집 세션에서 Word가 파일 링크 재로드. | 확인: Word에서 Fig 1 업데이트 반영 |
| 5 | MA-01 RFA | `cd .../01_RFA_Adjunct/6_Manuscript/v3_package && pandoc RFA_Meta_v3_combined.md -o RFA_Meta_v3.docx` (또는 기존 빌드 스크립트) | v3 combined DOCX Fig 1 |
| 6 | MA-02 CBCT_Biopsy | `cd .../02_CBCT_Biopsy/7_Manuscript && pandoc manuscript_for_docx.md ...` + submission docx rebuild | `MA1_v12_manuscript.docx` + submission/academic_radiology figures |
| 7 | MA-21 Aneurysm | `cd .../21_.../submission/ryai && bash build_manuscript.sh` | `submission/ryai/manuscript.docx` + `submission/dual_review_request/manuscript.docx` |

**중단 조건**: rebuild 에러, figure 누락, 숫자 불일치 발견 시 해당 프로젝트만 정지하고 나머지는 계속.

### Step 2. CXRscoliosis workflow 업그레이드

현 상태: `Document/build_manuscript.py`는 본문·caption만 write. Fig 1은 Word에서 수동 삽입 → 매 rebuild마다 수작업 → 일관성/재현성 깨짐.

목표: `add_figure(doc, Path, caption)` 호출을 본문 build 과정에 포함 (CK-5 `build_unified_docx.py:413` 패턴). `python-docx` import 이미 됨. 수정 지점:

- `build_manuscript.py` 상단에 `FIGURES_DIR` 상수 + `add_figure()` 헬퍼 추가 (CK-5에서 복사)
- Figure Legends 섹션 직전에 `add_figure(doc, FIGURES_DIR/"figure1_flow.png", "Figure 1. ...")` 삽입. Fig 2, Fig 3도 동일 패턴.
- 기존 Word 수동 embed 과정 폐기 — 매 rebuild가 figure 포함 완전 재구성.

검증: 새 build script로 DOCX 생성 → Word에서 열어 Fig 1 monochrome outline 확인 + 300 dpi density 확인.

### Step 3. MA-03 P0 HALT 해결

별도 세션 권장 (이 세션 안에서도 가능). 순서:

1. `cd /Users/eugene/workspace/10_Meta_Analysis/03_CBCT_Ablation` + HANDOFF_prisma_flow_reconciliation.md §즉시 실행 Step 1부터.
2. `1_Search/*.csv` 로드 → PubMed/Embase 실제 row count + PMID dedup → 단일 truth 확정.
3. 3 위치 동시 수정: `2_Screening/prisma_flow_final.md`, `7_Manuscript/manuscript_for_docx.md` L52-56 + L74.
4. DOCX v5→v6 rebuild, `submission/cvir/` 교체, checklist 기록.
5. retrofit 재개: `5_Figures/create_figure1.R` 작성 (MA-02 패턴 copy) → `fig1_prisma_flow.{pdf,png}` 렌더 → 유진 시각 확인.

---

## 반영 매트릭스 (참고)

| Project | Figure 위치 | submission 경로 관계 | 새 figure 반영 방식 |
|---|---|---|---|
| CK-5 Emphysema | `manuscript/figures/figure1_flow.{png,pdf}` | Chest는 개별 figure 파일 업로드 (CHECKLIST.md:36) — docx 내부 embed 없음 | ✅ 파일 그대로 업로드 |
| CAC_Warranty | `manuscript/figures/figure1_flow.png` | build_manuscript_docx.py가 DOCX에 embed | ✅ rebuild |
| CXRscoliosis | `Analysis/figures/figure1_flow.png` | 현재 Word 수동 embed (Step 2로 자동화) | ⚠️ Step 2 후 rebuild |
| SkullFx P2 | `figures/Figure1_STARD_flowchart.{pdf,png}` | manuscript DOCX 내부 embed (Word 편집) | ✅ 동일 파일명 교체 완료 |
| MA-01 RFA | `5_Figures/v3/` + `6_Manuscript/v3_package/figures/Fig1_PRISMA_flow.{pdf,png}` | pandoc md → docx | ✅ rebuild |
| MA-02 CBCT_Biopsy | `5_Figures/fig1_prisma_flow.*` + `submission/academic_radiology/figures/fig1_prisma_flow.*` | submission figures 폴더 직접 갱신됨 | ✅ 갱신 완료, docx rebuild만 |
| MA-21 Aneurysm | `analysis/figures/f1_prisma_flow.{pdf,png}` | `submission/ryai/_combined.md`에서 절대경로 참조 + build_manuscript.sh | ✅ rebuild |
| MeducAI P1/P3 | `figures/v2_monochrome/` 병렬 only | 현 제출본 `figures/` 불변 원칙 | N/A — 리젝 시 `v2_monochrome/` 승격 |

---

## 주의사항

- **MeducAI P1/P3**: under-review. 병렬 `v2_monochrome/`만 생성된 상태 — Step 1에서 제외. 현 submission 파일 절대 수정 금지.
- **SkullFx P2**: manuscript DOCX를 Word에서 여는 순간 링크된 figure가 자동 업데이트됨. `Figure1_STARD_flowchart.{pdf,png}` 파일명 유지 (이미 교체됨).
- **MA-01 v2_package 아님**: retrofit 결과물은 v3_package에만 있음 (v2는 legacy). 최종 submission-ready 패키지가 v3_package인지 재확인.
- **CK-5 Chest 특수**: docx embed 방식이 아니라 figure individual upload. 따라서 submission/chest/manuscript_anonymized.docx에는 media/ 없음 (`unzip -l` 확인). anonymize 과정은 수동/외부 — 별도 인계 없음.
- **숫자 불일치 발견 시**: 즉시 정지. numerical-safety rule per `~/.claude/rules/numerical-safety.md` — prose 수정 선행, figure는 그 뒤.

---

## 참조 파일

- **Retrofit 커밋**: `medsci-skills` @ 137ee32.
- **Visual convention**: `~/.claude/projects/-Users-eugene-workspace-medsci-skills/memory/feedback_flow_diagram_convention.md` (rule #7 no-HTML-labels).
- **9 exemplar R scripts**: `make-figures/SKILL.md` §Per-project pattern에 경로 inline.
- **MA-03 P0**: `/Users/eugene/workspace/10_Meta_Analysis/03_CBCT_Ablation/HANDOFF_prisma_flow_reconciliation.md`

## Non-goals

- 새로운 flow diagram retrofit (MA-03 외)
- medsci-skills 인프라 재작업 (dispatcher / SKILL.md 추가 편집)
- MeducAI P1/P3 submission docx 수정
- KM / forest / ROC 스타일 통일 — 다음 기획 건
