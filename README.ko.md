<div align="center">

# MedSci Skills

[English](https://github.com/Aperivue/medsci-skills/blob/v6.0.1/README.md) | [简体中文](https://github.com/Aperivue/medsci-skills/blob/v6.0.1/README.zh-CN.md) | 한국어

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/Aperivue/medsci-skills/blob/v6.0.1/LICENSE)
[![Release](https://img.shields.io/github/v/release/Aperivue/medsci-skills?style=flat-square&color=blue)](https://github.com/Aperivue/medsci-skills/releases/latest)
![Skills](https://img.shields.io/badge/Skills-54-brightgreen?style=flat-square)
[![npm](https://img.shields.io/npm/v/medsci-skills?style=flat-square&label=npm&color=cb3837)](https://www.npmjs.com/package/medsci-skills)
[![DOI](https://img.shields.io/badge/DOI-10.5281%2Fzenodo.20155321-blue?style=flat-square)](https://doi.org/10.5281/zenodo.20155321)

**Created & maintained by [Yoojin Nam, MD](https://orcid.org/0000-0001-8565-1360)**
<br>
<sub>Department of Radiology and Research Institute of Radiology, University of Ulsan College of Medicine, Asan Medical Center, Seoul, Republic of Korea</sub>

</div>

> 이 문서는 영문 [README](https://github.com/Aperivue/medsci-skills/blob/v6.0.1/README.md)를 짧게 요약한 한국어판입니다. 내용이 다르면 영문 README를 따릅니다.

## 무엇이고, 누구를 위한 것인가

MedSci Skills는 임상 연구를 위한 [Agent Skills](https://agentskills.io) 모음입니다. 문헌과 참고문헌, 연구 설계, 통계 분석, figure, 원고 작성, reporting guideline 점검, 저널 투고를 다루고, 의료영상 AI 모델을 만들고 검증하는 작업도 함께 다룹니다.
Claude Code, Codex, Cursor, GitHub Copilot에서 일하는 의사와 의생명·의공학 연구자를 위해 만들었습니다.
스킬은 초안을 쓰고 점검하며, 함께 들어 있는 스크립트는 다시 계산할 수 있는 것을 직접 다시 계산합니다. 그래도 모든 결과물은 자격을 갖춘 연구자가 검토해야 합니다. 진단 도구가 아니며, 스스로 논문을 쓰는 저자도 아닙니다.

## 설치

**터미널 없이**(Windows, macOS): [classroom 설치 파일](https://github.com/Aperivue/medsci-skills/blob/v6.0.1/docs/install.md#classroom-installer-no-terminal)을 내려받아 압축을 풀고 안에 있는 설치 파일을 더블클릭하세요. 업데이트 알림도 함께 켜지고, 바탕화면에 **Update MedSci Skills** 아이콘이 생깁니다. Claude Code, Python, Node를 아직 설치하지 않았다면 Mac·Windows [설치 안내](https://github.com/Aperivue/medsci-skills/blob/v6.0.1/docs/setup/README.md)(영문)를 차례대로 따라 하면 됩니다.

**터미널에서** 실행합니다(Node 18+와 Python 3.9+ 필요).

```bash
npx medsci-skills install
```

모든 스킬이 `~/.claude/skills/`(Claude Code, Cursor, VS Code의 Copilot이 읽는 곳)와 `~/.agents/skills/`(Codex, Cursor, GitHub Copilot이 읽는 곳)에 복사됩니다.
agent를 다시 시작하고 `/orchestrate`를 입력한 뒤 하려는 일을 설명하면 알맞은 스킬로 연결해 줍니다.
새 버전이 나올 때 알림을 받고 싶다면 `--enable-update-notify`를 붙이세요. Claude Code 세션을 시작할 때 한 줄 알림이 뜹니다. 기본값은 꺼짐이고 telemetry는 없습니다.

터미널 없이 쓰는 classroom 설치 파일, Claude Code plugin, GitHub CLI(`gh skill`), git clone 같은 다른 설치 방법과 업데이트 방법, 일부 스킬에 필요한 도구(pandoc, R, PyTorch)는 [docs/install.md](https://github.com/Aperivue/medsci-skills/blob/v6.0.1/docs/install.md)(영문)에 있습니다.

## 처음 써 볼 세 가지 워크플로

스킬 이름으로 바로 부르거나, 하려는 일을 `/orchestrate`에 설명하면 됩니다.

- **`/check-reporting`**: 원고를 49개 reporting guideline과 risk-of-bias 도구(STROBE, STARD, CONSORT, PRISMA 2020, TRIPOD+AI 등)에 비춰 항목별로 점검하고, PRESENT / PARTIAL / MISSING / N/A 판정과 수정 목록을 줍니다.
- **`/analyze-stats`**: 비식별화한 데이터 파일(CSV, Excel, TSV)과 연구 질문을 받아 분석 계획을 먼저 확인받은 뒤, Python(또는 R) 코드를 실행해 표, figure, manifest를 만듭니다.
- **`/verify-refs`**: 참고문헌마다 PubMed, CrossRef, OpenAlex를 조회해 OK, MISMATCH, UNVERIFIED, FABRICATED로 표시하고 `qc/reference_audit.json`에 기록합니다. 보고만 하고 참고문헌을 고치지는 않습니다.

더 긴 흐름(투고 전 점검, 데이터에서 원고까지, systematic review)은 [docs/workflows.md](https://github.com/Aperivue/medsci-skills/blob/v6.0.1/docs/workflows.md)에, 공개 데이터셋으로 처음부터 끝까지 돌려 본 예제 다섯 개는 [docs/demos.md](https://github.com/Aperivue/medsci-skills/blob/v6.0.1/docs/demos.md)에 있습니다.

## 스킬 목록

54개 스킬 전체를 연구 단계별로 묶은 표는 영문 README의 [Skills 절](https://github.com/Aperivue/medsci-skills/blob/v6.0.1/README.md#skills)에 있습니다. 스킬 이름마다 설명 페이지가 연결되어 있습니다. 터미널에서는 `npx medsci-skills list`로 같은 분류를 볼 수 있습니다. 어떤 스킬을 써야 할지 모르겠다면 `/orchestrate`부터 시작하세요.

v6에서 이름이 바뀐 스킬(옛 이름은 v7 전까지 계속 동작): `imaging-data` ← `preprocess-imaging`, `profile-imaging`; `model-assessment` ← `explainability`, `model-evaluation`, `model-validation`, `uncertainty-imaging`; `model-selection` ← `architecture-zoo`, `model-sourcing`. v5에서 업그레이드한다면 [MIGRATION-v6.md](https://github.com/Aperivue/medsci-skills/blob/v6.0.1/MIGRATION-v6.md)(영문)를 보세요.

## 환자 데이터와 안전

식별 가능한 환자 데이터를 agent에 넘기지 마세요. `/deidentify`는 네트워크 연결이나 AI 호출 없이 로컬에서 실행됩니다. 정규식과 휴리스틱(11개국 locale pack)으로 protected health information(PHI)을 찾고, 사용자가 대화형으로 검토한 뒤 가명화합니다. `/analyze-stats`는 원자료 파일을 사용하기 전에 환자 식별정보가 들어 있는지 묻습니다. 이 스킬들은 연구 생산성 도구이지 clinical decision support가 아닙니다. 임상적으로 검증되지 않았고 전문가 검토를 대신하지 못하므로, 논문이나 임상 현장에서 사용하기 전에 자격을 갖춘 연구자가 모든 결과물을 확인해야 합니다. 91개의 deterministic detector는 정해진 항목(참고문헌 메타데이터, 산술, 체크리스트 항목, data leakage)을 다시 계산하거나 교차 확인합니다. 아무것도 걸리지 않았다는 것은 그 점검들이 문제를 찾지 못했다는 뜻일 뿐, 원고가 옳다는 뜻은 아닙니다. detector별 목록과 정식 평가 여부는 [MEDSCI_AUDIT.md](https://github.com/Aperivue/medsci-skills/blob/v6.0.1/MEDSCI_AUDIT.md)에, 참고문헌 조회에 쓰는 API 키 없는 공개 API는 [docs/connectors.md](https://github.com/Aperivue/medsci-skills/blob/v6.0.1/docs/connectors.md)에 정리되어 있습니다.

## 인용

MedSci Skills가 원고, 연구계획서, 분석에 도움이 되었다면 인용해 주세요. Methods나 Acknowledgements에 실제로 사용한 버전과 함께 적으면 됩니다.

> Reporting-guideline compliance, reference verification, and pre-submission integrity checks
> were assisted by MedSci Skills (version X.Y.Z; https://github.com/Aperivue/medsci-skills;
> archived at Zenodo, https://doi.org/10.5281/zenodo.20155321).

BibTeX(소프트웨어 자체, 그리고 설계를 설명한 preprint):

```bibtex
@software{nam_medsci_skills,
  author    = {Nam, Yoojin},
  title     = {{MedSci Skills: Claude Code Skills for the Medical Research Lifecycle}},
  year      = {2026},
  publisher = {Zenodo},
  doi       = {10.5281/zenodo.20155321},
  url       = {https://github.com/Aperivue/medsci-skills}
}

@article{nam2026agentic,
  author  = {Nam, Yoojin and Jeong, Jinhoon and Kim, Namkug},
  title   = {{Deterministic Integrity Gates for LLM-Assisted Clinical Manuscript
             Preparation: An Auditable Biomedical Informatics Architecture}},
  year    = {2026},
  journal = {arXiv preprint arXiv:2606.09500},
  url     = {https://arxiv.org/abs/2606.09500}
}
```

Zenodo concept DOI [10.5281/zenodo.20155321](https://doi.org/10.5281/zenodo.20155321)은 항상 최신 릴리스를 가리키고, [`CITATION.cff`](https://github.com/Aperivue/medsci-skills/blob/v6.0.1/CITATION.cff)에 기계가 읽을 수 있는 인용 정보가 있습니다.

## 라이선스

MIT License입니다. [LICENSE](https://github.com/Aperivue/medsci-skills/blob/v6.0.1/LICENSE)를 보세요.
함께 들어 있는 자료 중 일부는 이 프로젝트의 것이 아니고 MIT도 아닙니다. 공식 guideline 템플릿, CSL 인용 스타일, 몇몇 체크리스트 요약은 각자의 조건을 따르며, 여기에는 상업적 이용을 제한하는 CC BY-NC도 있습니다. 목록은 [THIRD-PARTY-NOTICES.md](https://github.com/Aperivue/medsci-skills/blob/v6.0.1/THIRD-PARTY-NOTICES.md)에 있습니다.
reporting guideline 체크리스트는 원 출처의 조건을 유지합니다. 그중 몇 개는 공개 라이선스가 없어 원문 대신 직접 다시 쓴 요약으로만 넣었고, 항목별 기록은 [check-reporting의 LICENSES.md](https://github.com/Aperivue/medsci-skills/blob/v6.0.1/skills/check-reporting/references/LICENSES.md)에 있습니다.
선택 의존성: `pdf_to_md.py`는 [pymupdf4llm](https://pymupdf.readthedocs.io)(AGPL-3.0)을 씁니다. 함께 배포하지 않으며, 필요하면 `pip install pymupdf4llm`으로 직접 설치합니다.

Built by [Aperivue](https://aperivue.com).
