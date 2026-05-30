# Pandoc Korean PDF Cheatsheet

## 검증된 frontmatter 패턴

```yaml
---
title: "문서 제목"
author: "작성자"
date: "2026-05-01"
mainfont: "Apple SD Gothic Neo"     # macOS / Linux: "Noto Serif CJK KR"
CJKmainfont: "Apple SD Gothic Neo"  # macOS / Linux: "Noto Sans CJK KR"
geometry: "margin=0.85in"            # cover/proposal: 1in / briefing: 0.75in
fontsize: 11pt                       # briefing: 10pt
linestretch: 1.25                    # cover: 1.5 / briefing: 1.2
colorlinks: true
---
```

## 명령어 (raw pandoc)

```bash
pandoc input.md \
  --pdf-engine=xelatex \
  -o output.pdf
```

OS-detect 자동화는 `scripts/render_pdf.sh` 참고.

## 표 폭 자동 추론

```bash
# 1) 분리행 dash 비율을 content-proportional로 교체
python3 scripts/infer_colwidths.py input.md --out input.cw.md

# 2) 렌더
pandoc input.cw.md --pdf-engine=xelatex -o output.pdf
```

또는 wrapper 한 번에:
```bash
bash scripts/render_pdf.sh -i input.md -o output.pdf --infer-colwidths
```

## Per-document 폰트 커스터마이즈

frontmatter > `--font` CLI > OS default (낮은 우선순위).

```bash
bash scripts/render_pdf.sh -i input.md --font "Nanum Myeongjo" --cjk-font "Nanum Myeongjo"
```

## 폰트 후보 (한글 학술용)

| 폰트 | 비고 |
|------|------|
| Apple SD Gothic Neo | macOS 기본, sans, 가장 깔끔 |
| Noto Sans CJK KR | Linux 기본 |
| Noto Serif CJK KR | 본문 serif |
| Nanum Myeongjo | 명조계 (전통적) |
| Nanum Gothic | 고딕계 sans |
| Pretendard | 모던 sans, 별도 설치 |

## 추가 옵션

- `--toc` — 목차 생성 (긴 proposal에 유용)
- `--number-sections` — 자동 섹션 번호
- `-V documentclass=article` (default) / `report` / `book`
- `-V papersize=a4` — A4 (default: letter)

## 참고 링크

- [Pandoc User Guide](https://pandoc.org/MANUAL.html)
- [Pandoc with Chinese (CJK applies)](https://github.com/jgm/pandoc/wiki/Pandoc-with-Chinese)
- [Quarto tbl-colwidths](https://quarto.org/docs/authoring/tables.html#column-widths) (HTML 신뢰; PDF regression 주의)
- [Issue 7509 — CJKmainfont smart quotes](https://github.com/jgm/pandoc/issues/7509)
