<div align="center">

# MedSci Skills

[English](https://github.com/Aperivue/medsci-skills/blob/v6.0.1/README.md) | 简体中文 | [한국어](https://github.com/Aperivue/medsci-skills/blob/v6.0.1/README.ko.md)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/Aperivue/medsci-skills/blob/v6.0.1/LICENSE)
[![Release](https://img.shields.io/github/v/release/Aperivue/medsci-skills?style=flat-square&color=blue)](https://github.com/Aperivue/medsci-skills/releases/latest)
![Skills](https://img.shields.io/badge/Skills-54-brightgreen?style=flat-square)
[![npm](https://img.shields.io/npm/v/medsci-skills?style=flat-square&label=npm&color=cb3837)](https://www.npmjs.com/package/medsci-skills)
[![DOI](https://img.shields.io/badge/DOI-10.5281%2Fzenodo.20155321-blue?style=flat-square)](https://doi.org/10.5281/zenodo.20155321)

**Created & maintained by [Yoojin Nam, MD](https://orcid.org/0000-0001-8565-1360)**
<br>
<sub>Department of Radiology and Research Institute of Radiology, University of Ulsan College of Medicine, Asan Medical Center, Seoul, Republic of Korea</sub>

</div>

> 本页是英文 [README](https://github.com/Aperivue/medsci-skills/blob/v6.0.1/README.md) 的简短中文摘要。两者不一致时，以英文 README 为准。

## 这是什么，适合谁

MedSci Skills 是一套面向临床研究的 [Agent Skills](https://agentskills.io)：涵盖文献与参考文献、研究设计、统计分析、图表、论文撰写、报告规范核查和期刊投稿，另有一条用于构建和验证医学影像 AI 模型的工作线。
它面向在 Claude Code、Codex、Cursor 或 GitHub Copilot 中工作的医生，以及生物医学和医学工程研究人员。
技能负责起草和核查，随附的脚本会重新计算能够重新计算的内容；所有输出仍须由合格的研究人员审阅。它不是诊断工具，也不是自主撰写论文的作者。

## 安装

**无需终端**（Windows 或 macOS）：下载 [classroom 安装包](https://github.com/Aperivue/medsci-skills/blob/v6.0.1/docs/install.md#classroom-installer-no-terminal)，解压后双击其中的安装程序。它还会开启更新提醒，并在桌面放置 **Update MedSci Skills** 图标。如果还没有安装 Claude Code、Python 或 Node，可按 Mac 和 Windows 的[安装指南](https://github.com/Aperivue/medsci-skills/blob/v6.0.1/docs/setup/README.md)（英文）逐步操作。

**在终端中**运行（需要 Node 18+ 和 Python 3.9+）：

```bash
npx medsci-skills install
```

该命令把所有技能复制到 `~/.claude/skills/`（Claude Code、Cursor 和 VS Code 中的 Copilot 读取）和 `~/.agents/skills/`（Codex、Cursor 和 GitHub Copilot 读取）。
重启 agent，输入 `/orchestrate` 并描述你要做的事，它会把请求转给合适的技能。
如需在新版本发布时收到提醒，可加上 `--enable-update-notify`：Claude Code 会话开始时显示一行通知，默认关闭，没有遥测。

其他安装方式（无需终端的 classroom 安装包、Claude Code 插件、GitHub CLI `gh skill`、git clone）、更新方法，以及个别技能需要的额外工具（pandoc、R、PyTorch），见 [docs/install.md](https://github.com/Aperivue/medsci-skills/blob/v6.0.1/docs/install.md)（英文）。

## 从三个工作流开始

可以直接用名称调用技能，也可以把任务描述给 `/orchestrate`。

- **`/check-reporting`**：按 49 项报告规范和偏倚风险工具（STROBE、STARD、CONSORT、PRISMA 2020、TRIPOD+AI 等）逐条核查稿件，给出 PRESENT / PARTIAL / MISSING / N/A 结果和修改清单。
- **`/analyze-stats`**：读取去标识化的数据文件（CSV、Excel 或 TSV）和研究问题，先给出分析计划供你确认，再运行 Python（或 R）代码，输出表格、图和 manifest。
- **`/verify-refs`**：在 PubMed、CrossRef 和 OpenAlex 中查找每条参考文献，标记为 OK、MISMATCH、UNVERIFIED 或 FABRICATED，写入 `qc/reference_audit.json`；只报告，从不修改你的参考文献。

更长的流程（投稿前审核、从数据到稿件、系统综述）见 [docs/workflows.md](https://github.com/Aperivue/medsci-skills/blob/v6.0.1/docs/workflows.md)；基于公开数据集的五个完整示例见 [docs/demos.md](https://github.com/Aperivue/medsci-skills/blob/v6.0.1/docs/demos.md)。

## 技能列表

全部 54 个技能按研究阶段分组的表格（每个技能名都链接到其说明页）见英文 README 的 [Skills 一节](https://github.com/Aperivue/medsci-skills/blob/v6.0.1/README.md#skills)。在终端中，`npx medsci-skills list` 会列出相同的分组。不确定该用哪个时，从 `/orchestrate` 开始。

v6 中改名的技能（旧名称在 v7 之前仍可使用）：`imaging-data` ← `preprocess-imaging`、`profile-imaging`；`model-assessment` ← `explainability`、`model-evaluation`、`model-validation`、`uncertainty-imaging`；`model-selection` ← `architecture-zoo`、`model-sourcing`。从 v5 升级请看 [MIGRATION-v6.md](https://github.com/Aperivue/medsci-skills/blob/v6.0.1/MIGRATION-v6.md)（英文）。

## 患者数据与安全

不要把可识别身份的患者数据交给 agent。`/deidentify` 在本地运行，不联网，也不调用 AI：它用正则表达式和启发式规则（含十一个国家的 locale 包）检测受保护的健康信息（PHI），经你交互审核后进行假名化；`/analyze-stats` 在使用原始数据文件前会询问其中是否含有患者标识符。这些是科研效率工具，不是临床决策支持：它们未经临床验证，不能替代专家审查，任何输出在用于发表或临床场景之前都必须由合格的研究人员核对。93 个确定性检测器会重新计算或交叉核对特定内容（参考文献元数据、算术、清单条目、数据泄漏）；运行后没有发现问题，只说明这些检查没有找到问题，不代表稿件正确。[MEDSCI_AUDIT.md](https://github.com/Aperivue/medsci-skills/blob/v6.0.1/MEDSCI_AUDIT.md) 列出了每个检测器以及其中哪些经过正式评估；参考文献查询使用 [docs/connectors.md](https://github.com/Aperivue/medsci-skills/blob/v6.0.1/docs/connectors.md) 中列出的公开、无需密钥的 API。

## 引用

如果 MedSci Skills 帮助你完成了稿件、研究方案或分析，请引用它。可以在 Methods 或 Acknowledgements 中写（注明你实际使用的版本）：

> Reporting-guideline compliance, reference verification, and pre-submission integrity checks
> were assisted by MedSci Skills (version X.Y.Z; https://github.com/Aperivue/medsci-skills;
> archived at Zenodo, https://doi.org/10.5281/zenodo.20155321).

BibTeX（软件本身，以及介绍其设计的预印本）：

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

Zenodo concept DOI [10.5281/zenodo.20155321](https://doi.org/10.5281/zenodo.20155321) 始终指向最新版本；[`CITATION.cff`](https://github.com/Aperivue/medsci-skills/blob/v6.0.1/CITATION.cff) 提供机器可读的引用元数据。

## 许可证

MIT 许可证，见 [LICENSE](https://github.com/Aperivue/medsci-skills/blob/v6.0.1/LICENSE)。
部分随附材料不属于本项目，也不适用 MIT：官方规范模板、CSL 引文样式和少数清单摘要有各自的条款，其中包括限制商业使用的 CC BY-NC。它们都列在 [THIRD-PARTY-NOTICES.md](https://github.com/Aperivue/medsci-skills/blob/v6.0.1/THIRD-PARTY-NOTICES.md) 中。
报告规范清单保留其来源的条款；其中几项没有开放许可，因此只以我们自己的话写成摘要收录，逐项记录见 [check-reporting 的 LICENSES.md](https://github.com/Aperivue/medsci-skills/blob/v6.0.1/skills/check-reporting/references/LICENSES.md)。
可选依赖：`pdf_to_md.py` 使用 [pymupdf4llm](https://pymupdf.readthedocs.io)（AGPL-3.0），不随附，需要时由用户自行 `pip install pymupdf4llm`。

Built by [Aperivue](https://aperivue.com).
