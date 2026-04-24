# Classroom Distribution Plan

This document records the operating plan for distributing MedSci Skills to
non-programmer workshop participants who mainly use desktop agent apps.

## Decision Summary

Use a full skill-set install, but teach small single-skill tasks first.

- Install the full `skills/` directory to avoid repeated follow-up installs.
- Keep classroom tasks narrow: one table, one figure, one section, or 5-10 references.
- Do not teach `orchestrate --e2e` as the first workflow.
- Treat WSL as an advanced option, not the default Windows path.
- Distribute through GitHub Releases with direct ZIP links.

## Why Not WSL by Default

Many students will use Windows and desktop apps. Requiring WSL adds avoidable
support burden: Linux folder paths, Windows-vs-WSL file locations, Python/R
toolchain differences, and permission confusion.

Default classroom path:

1. Install Claude Code Desktop, Codex Desktop, or Cursor.
2. Install Git for Windows only if the chosen desktop app requires it.
3. Download the classroom ZIP.
4. Double-click the installer.
5. Restart the desktop app.

WSL remains useful for advanced reproducible analysis environments, Linux
sandboxing, and heavier R/Python toolchains.

## Distribution Model

Keep installer source files in the repository:

```text
installers/
├── install.py
├── install-windows.cmd
├── install-windows.ps1
└── install-macos.command
```

Publish student-facing ZIP files through GitHub Releases:

```text
medsci-skills-classroom-windows.zip
medsci-skills-classroom-macos.zip
```

Use direct download links in email and lecture material:

```text
https://github.com/Aperivue/medsci-skills/releases/latest/download/medsci-skills-classroom-windows.zip
https://github.com/Aperivue/medsci-skills/releases/latest/download/medsci-skills-classroom-macos.zip
```

This avoids asking students to find the green Code button, Releases tab, or
Assets list.

## Classroom ZIP Contents

Recommended ZIP layout:

```text
medsci-skills-classroom/
├── README_FIRST.md
├── installers/
│   ├── install-windows.cmd
│   ├── install-windows.ps1
│   ├── install-macos.command
│   └── install.py
├── skills/
└── adapters/
```

The repository can contain more developer documentation, demos, tests, and
schemas. The classroom ZIP should contain only what students need.

## Installer Behavior

The installer should:

1. Detect the operating system.
2. Copy all skills into local agent skill folders.
3. Create a Cursor project rule when a project path is supplied.
4. Write a human-readable install log.
5. Show a first test prompt.

Default local destinations:

```text
Claude Code: ~/.claude/skills/
Codex:       ~/.agents/skills/
Cursor:      .cursor/rules/medsci-skills.mdc inside a chosen project
```

Cursor is project-oriented, so its adapter should be a small rule that points
the agent to the canonical `skills/<name>/SKILL.md` files rather than copying
all skill text into one large rule.

## Token Budget Guidance

`git clone` or ZIP download does not meaningfully spend model tokens. Token
cost rises when a model is asked to inspect the whole repository.

Bad classroom prompt:

```text
이 레포를 전부 보고 설치해줘.
```

Better classroom prompt:

```text
설치 파일만 실행해줘. 레포 전체를 읽지 말고, 설치가 끝나면 로그와 테스트 프롬프트만 보여줘.
```

Best classroom path:

Students run the installer directly and ask the model only to verify one skill.

## Expected Capability on $20-Class Plans

Small tasks should work on Sonnet-medium or comparable desktop-agent models:

| Task | Classroom suitability | Notes |
|---|---|---|
| Baseline table | High | Use one CSV/Excel file and a short variable list. |
| Simple figure | High | Specify figure type and variables. |
| Manuscript section | High | Ask for one section or 2-3 paragraphs. |
| Reference search | High | Limit to 5-10 verified references. |
| Reporting checklist | Medium-high | Provide manuscript or section text. |
| Full manuscript pipeline | Low for first class | Too much context and validation burden. |

## Release Checklist

- [ ] `installers/install.py` runs on macOS and Windows.
- [ ] Windows `.cmd` works with `py -3` and `python` fallback.
- [ ] macOS `.command` is executable in the release ZIP.
- [ ] Classroom ZIP contains `README_FIRST.md`.
- [ ] Direct GitHub Release download links are tested.
- [ ] First test prompt succeeds in Claude Code Desktop.
- [ ] First test prompt succeeds in Codex Desktop if supported.
- [ ] Cursor project rule can be generated for a sample project.
- [ ] Email announcement uses direct download links, not GitHub navigation.
- [ ] Lecture material tells students not to run full E2E first.
