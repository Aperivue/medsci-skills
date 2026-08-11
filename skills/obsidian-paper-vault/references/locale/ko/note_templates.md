# Korean (ko) locale — vault layout + note templates

> Opt-in Korean variant for `obsidian-paper-vault`. The skill defaults to English folder names
> (`Literature/`, `Concepts/`) and English note headings. Use this layout when the user's vault
> already follows a Korean structure — the skill honors an existing layout — or when the user
> prefers Korean notes. Mirrors the `/lit-sync` ko locale so both skills write the same vault
> the same way.

## 폴더 구조 (한국어 vault)

- 논문 노트: `02_research/논문/{짧은 제목}.md`
- 개념 노트: `02_research/개념노트/{개념 이름}.md`
- 생각 노트: `02_research/생각노트/` — **사용자 전용, 스킬이 쓰지 않는다**

```bash
# 기존 논문 노트 개수 확인
ls "$VAULT/02_research/논문/" | wc -l
```

## 논문 노트 템플릿 (한국어 heading)

```markdown
---
title: "정확한 논문 원제목 (부제 포함)"
authors: [저자1, 저자2, 저자3]
journal: "저널명 또는 arXiv:XXXX.XXXXX"
date_published: YYYY-MM-DD
tags:
  - 📝논문
  - 🤖AI/LLM
  - 🏥ClinicalReasoning
status: 🟢Completed
aliases:
  - 짧은별명
---

# 논문 제목

📎 **옵시디언 내부에서 PDF 원문 열기**: ![[정확한_원본_PDF_파일명.pdf]]

## 📌 한 줄 요약
누가, 무엇을, 어떻게, 얼마나 — 텍스트 근거로 한 문장.

## 🎯 연구 배경 및 목적
* 기존 연구가 남긴 한계
* 이 논문이 풀려는 문제
* 가설 (명시되어 있으면)

## 🔑 주요 내용 및 결과
1. **설계**: n수, 데이터셋, 평가 방법 — 텍스트에 쓰인 그대로
2. **주요 결과**: 수치는 텍스트에 있는 것만 (예: "정확도 91.1%", "p < 0.001", "중앙값 10, IQR 9–10")
3. **비교**: baseline 또는 경쟁 모델 대비
4. **한계**: 저자가 명시한 것

## 💡 내 생각
* 내 연구에 주는 함의 — 저자의 주장이 아니라 읽은 사람의 판단
* 두 번째 함의

---
## 관련 노트
* [[도메인 허브 노트]]
* [[기존 개념 노트]]
* [[새 개념 제안]]
```

## 개념 노트 템플릿 (한국어 heading)

```markdown
---
title: "개념 이름"
type: concept
tags:
  - 🧠개념
  - (도메인 태그)
aliases:
  - AlternativeName
related_papers:
  - "[[논문노트1]]"
  - "[[논문노트2]]"
  - "[[논문노트3]]"
status: 🌱Seedling
---

# 개념 이름

## 📖 정의 (내 말로)
교과서 정의도, 논문에서 옮긴 문장도 아닌 내가 이해한 방식. 이 절이 2층의 전부다.

## 🌐 왜 중요한가
이 도메인에서 왜 주목할 개념인지 — 읽은 사람의 판단.

## 📚 논문별 관점
- **[[논문A]]**: 어떻게 다루는가 (구체적 인용)
- **[[논문B]]**: 다른 각도·방법론
- **[[논문C]]**: 상반되거나 보완하는 입장

## 🔗 관련 개념
- [[다른 개념]] — 어떻게 이어지는가
- [[아직 안 쓴 개념]] — 관련은 있으나 미작성

## ❓ 열린 질문
- 아직 답이 없는 것
- 후속 논문이 보여줘야 할 것

## 📝 업데이트 로그
- YYYY-MM-DD: 초안 ({N}편 기반)
```

## 태그 (한국어 vault)

`📝논문` · `🧠개념` · `💭생각` — 나머지 기술·도메인 태그는 영문
(`references/tag-vocabulary.md`)을 그대로 쓴다. 태그를 두 언어로 이중화하면 Dataview 쿼리가
갈라진다.

## 파일명

- 논문 노트: 핵심어 3~5개. 한글·영문 혼용 가능.
  - ✅ `순차 진단 Microsoft MAI-DxO.md`
  - ❌ PDF 원제목 그대로 / `paper_001.md`
- 개념 노트: 한글 개념명 + 통용 영문이 있으면 괄호 병기.
  - ✅ `순차적 의사결정 (Sequential Decision-Making).md`
  - ❌ `의사결정.md` (너무 일반적) / `SDM.md` (약어만)

## 주의

영문판 규칙은 그대로 적용된다 — 텍스트 파일에 없는 숫자·저자·날짜를 쓰지 않을 것, PDF 파일명을
글자 그대로 옮길 것, frontmatter 필드명을 바꾸지 말 것, 기존 노트를 덮어쓰지 말 것.
