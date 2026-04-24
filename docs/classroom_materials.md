# Classroom Materials: Vibe-Coding Medical Research

Use this file as the source for slides, handouts, LMS notices, and email
announcements.

## Student Setup Handout

### Before Class

Install one desktop agent app:

- Claude Code Desktop with a paid Claude plan
- Codex Desktop with a ChatGPT plan that supports Codex
- Cursor if you already use it

Windows users should install Git for Windows if their desktop app asks for Git.
Do not install WSL unless you already know why you need it.

### Download

Windows:

```text
https://github.com/Aperivue/medsci-skills/releases/latest/download/medsci-skills-classroom-windows.zip
```

macOS:

```text
https://github.com/Aperivue/medsci-skills/releases/latest/download/medsci-skills-classroom-macos.zip
```

### Install

Windows:

1. Download the Windows ZIP.
2. Unzip it.
3. Double-click `installers/install-windows.cmd`.
4. Restart your desktop agent app.

macOS:

1. Download the macOS ZIP.
2. Unzip it.
3. Double-click `installers/install-macos.command`.
4. Restart your desktop agent app.

First test prompt:

```text
MedSci Skills가 설치됐는지 확인하고, 오늘 실습에 쓸 대표 스킬 5개만 보여줘.
```

## First-Class Teaching Scope

Install the full skill set, but teach only five entry skills:

| Skill | First task |
|---|---|
| `search-lit` | Find 5-10 verified references. |
| `analyze-stats` | Make a simple baseline or result table. |
| `make-figures` | Create one publication-ready figure. |
| `write-paper` | Draft one manuscript section. |
| `check-reporting` | Check one draft against a reporting guideline. |

Avoid `orchestrate --e2e` during the first session.

## Safe First Prompts

Reference search:

```text
search-lit을 사용해서 PubMed에서 diabetic nephropathy CT radiomics 관련 논문 8개만 찾아줘. PMID/DOI가 확인된 것만 표로 정리하고, 검색식도 같이 보여줘.
```

Baseline table:

```text
analyze-stats를 사용해서 이 CSV로 baseline table을 만들어줘. group 변수는 treatment이고 age, sex, BMI, diabetes를 비교해줘. 먼저 분석 계획을 5줄로 요약하고 내 확인을 받은 뒤 진행해줘.
```

Figure:

```text
make-figures를 사용해서 이 결과표에서 forest plot 하나를 만들어줘. 저널 제출용으로 300 dpi PNG와 캡션 초안을 같이 만들어줘.
```

Results section:

```text
write-paper를 사용해서 아래 결과를 바탕으로 Results 섹션 2문단만 작성해줘. Discussion 해석은 넣지 말고 숫자와 방향성만 정확히 써줘.
```

Reporting check:

```text
check-reporting을 사용해서 이 초안이 STROBE 항목을 얼마나 충족하는지 PRESENT/PARTIAL/MISSING 표로 확인해줘. 수정 가능한 항목만 따로 표시해줘.
```

## Token-Saving Rules for Students

- Ask for one task at a time.
- Limit reference searches to 5-10 papers at first.
- Ask the model to read only the relevant file or skill.
- Do not ask it to inspect the entire repository.
- Do not start with full paper automation.
- Stop after each output and review before continuing.

## Instructor Troubleshooting

| Symptom | Likely cause | Quick fix |
|---|---|---|
| Windows blocks installer | Downloaded script warning | More info -> Run anyway. |
| Installer says Python missing | Python not installed or not on PATH | Install Python 3, then rerun. |
| Claude/Codex does not see skills | App was not restarted | Quit fully and reopen. |
| Cursor does not see skills | No project rule installed | Run installer with `--cursor-project` or add `.cursor/rules/medsci-skills.mdc`. |
| Model reads too much | Prompt too broad | Ask for one skill and one task only. |
| Full pipeline stalls | Task too large for plan | Split into table -> figure -> section -> check. |

## Announcement Email

Subject:

```text
[바이브코딩으로 연구하기] MedSci Skills 설치 안내
```

Body:

```text
안녕하세요.

다음 수업에서는 MedSci Skills를 이용해 표 만들기, 그림 만들기, 본문 작성,
레퍼런스 검색을 실습합니다. 수업 전 아래 파일을 설치해 주세요.

Windows:
https://github.com/Aperivue/medsci-skills/releases/latest/download/medsci-skills-classroom-windows.zip

macOS:
https://github.com/Aperivue/medsci-skills/releases/latest/download/medsci-skills-classroom-macos.zip

설치 방법:
1. 본인 OS에 맞는 ZIP 파일을 다운로드합니다.
2. 압축을 풉니다.
3. Windows는 installers/install-windows.cmd를 더블클릭합니다.
   macOS는 installers/install-macos.command를 더블클릭합니다.
4. Claude Code Desktop, Codex Desktop, 또는 Cursor를 완전히 종료한 뒤 다시 실행합니다.
5. 아래 문장을 붙여넣어 설치를 확인합니다.

MedSci Skills가 설치됐는지 확인하고, 오늘 실습에 쓸 대표 스킬 5개만 보여줘.

Windows 보안 경고가 뜨면 "추가 정보" -> "실행"을 선택하면 됩니다.
설치가 어려운 분은 수업 시작 10분 전에 오시면 같이 확인하겠습니다.

감사합니다.
```

## Short LMS Notice

```text
수업 전 MedSci Skills 설치가 필요합니다.

Windows:
https://github.com/Aperivue/medsci-skills/releases/latest/download/medsci-skills-classroom-windows.zip

macOS:
https://github.com/Aperivue/medsci-skills/releases/latest/download/medsci-skills-classroom-macos.zip

압축을 푼 뒤 Windows는 installers/install-windows.cmd,
macOS는 installers/install-macos.command를 더블클릭하세요.
설치 후 Claude Code/Codex/Cursor를 재시작하면 됩니다.
```

## Slide Outline

1. What MedSci Skills adds to a desktop agent
2. Why we install the full set but practice small tasks
3. Setup check
4. Task 1: verified references
5. Task 2: table
6. Task 3: figure
7. Task 4: Results paragraph
8. Task 5: reporting checklist
9. How to split large research work into safe small prompts
10. Common failure modes and how to recover
