# Known Pitfalls — Korean Academic PDF via pandoc + xelatex

## 1. 균등 분할 dash separator (`|---|---|---|`)

**증상**: 첫 열에 짧은 라벨만 있어도 데이터 열과 같은 폭 → 데이터 wrap, 가독성 저하.

**해결**: `scripts/infer_colwidths.py` 사용. Header + cell content 최대 display-width(CJK=2)에 비례한 dash count로 separator 행을 교체.

수동 override: `{tbl-colwidths="[20,40,40]"}` 캡션 뒤에 부착 (Quarto 1.4+ HTML만; PDF는 위 스크립트 권장).

## 2. CJKmainfont 미설정 → Hangul fallback

**증상**: Times New Roman 등 라틴 폰트로 fallback. 한글 글자가 빈 □ 또는 깨진 글리프로 출력.

**해결**: frontmatter에 `mainfont` + `CJKmainfont` 모두 명시. macOS는 `Apple SD Gothic Neo`, Linux는 `Noto Sans CJK KR`. xeCJK는 xelatex와 함께 자동 로드.

## 3. CJKmainfont 설정 시 smart quotes 깨짐

**증상**: pandoc issue 7509 — CJKmainfont 활성화 시 `"hello"`의 곧은 따옴표가 CJK 폰트로 렌더되어 `”hello”` 처럼 보임.

**해결**: 본문에 영문 quote 많을 때만 영향. 필요 시 `--smart=off` 또는 본문 quote를 `\enquote{...}`로 명시.

## 4. Em-dash 줄바꿈 깨짐

**증상**: `—` 양쪽 공백 없이 사용 시 xelatex가 줄바꿈 안 함 → 우측 마진 침범.

**해결**: 본문에서는 em-dash 25개 미만 권장 (`~/.claude/rules/manuscript-style-classical.md` §8). 필요 시 양쪽 공백 추가 또는 `\,—\,`.

## 5. 회람 PDF에 변경이력 / 버전번호 / PI attribution 노출

**증상**: 첫 수신자가 "v3.2.2" 같은 내부 버전·작성자 코멘트를 보고 혼란.

**해결**: 회람용 markdown은 별도 파일로 (`anchor_circulation.md` 등). 변경이력 섹션은 supplementary로 분리. frontmatter `redact_internal: true` 옵션은 future work.

## 6. xelatex 미설치 (Linux CI)

```bash
sudo apt-get install -y texlive-xetex texlive-lang-cjk fonts-noto-cjk
```

macOS는 `brew install --cask mactex-no-gui` (~5 GB) 또는 `basictex` + `tlmgr install xecjk` (경량).

## 7. Pipe table 안에 ` | ` 문자

**증상**: 셀 본문에 `|`가 있으면 컬럼이 잘못 분리됨.

**해결**: `\|` escape, 또는 grid table (`+---+---+`) 사용. infer_colwidths.py는 pipe table만 처리.

## 8. Quarto `tbl-colwidths` PDF regression

Quarto 1.4+에서 PDF에서는 무시되는 케이스 보고 (issues 6089, 9200). HTML은 OK. PDF 신뢰 불가 → raw pandoc + infer_colwidths 사용.
