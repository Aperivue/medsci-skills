<div align="center">

# 医学科学技能

[English](README.md) | [简体中文](README.zh-CN.md)

**58 项实际有效的技能。** 由医生兼研究员构建，并在真实出版物上进行了测试。

*MedSci Skills 是一款为医生和医学工程研究人员提供的端到端研究工具——设计→支架→验证→发布——用于临床手稿及其背后的医疗人工智能模型。它的护城河是合规层——47 条报告指南和偏差风险工具、参考/引文验证以及同行评审之前的确定性完整性门——现在通过模型工程通道进行扩展，该通道支持可重复、防泄漏的培训存储库并审核模型验证。临床AI模型研究工程在范围内；通用人工智能科学家平台则不然。它的竞争重点是临床提交的可靠性，而不是技能数量。*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Release](https://img.shields.io/github/v/release/Aperivue/medsci-skills?style=flat-square&color=blue)](https://github.com/Aperivue/medsci-skills/releases/latest)
[![CI](https://img.shields.io/github/actions/workflow/status/Aperivue/medsci-skills/validate.yml?branch=main&style=flat-square&label=CI)](https://github.com/Aperivue/medsci-skills/actions/workflows/validate.yml)
![Skills](https://img.shields.io/badge/Skills-58-brightgreen?style=flat-square)
[![npm](https://img.shields.io/npm/v/medsci-skills?style=flat-square&label=npm&color=cb3837)](https://www.npmjs.com/package/medsci-skills)
[![npm downloads](https://img.shields.io/npm/dw/medsci-skills?style=flat-square&label=npm%20downloads&color=cb3837)](https://www.npmjs.com/package/medsci-skills)
[![Watch the 2-min intro](https://img.shields.io/badge/▶_Watch-2--min_intro-FF0000?style=flat-square&logo=youtube&logoColor=white)](https://youtu.be/MclQ_RIofpE)
[![good first issues](https://img.shields.io/github/issues/Aperivue/medsci-skills/good%20first%20issue?style=flat-square&label=good%20first%20issues&color=7057ff)](https://github.com/Aperivue/medsci-skills/contribute)

[![Agent Skills](https://img.shields.io/badge/Agent_Skills-standard-blue?style=flat-square)](https://agentskills.io)
[![Claude Code](https://img.shields.io/badge/Claude_Code-supported-success?style=flat-square)](docs/host_compatibility.md)
[![Codex](https://img.shields.io/badge/Codex-supported-success?style=flat-square)](docs/host_compatibility.md)
[![Cursor](https://img.shields.io/badge/Cursor-supported-success?style=flat-square)](docs/host_compatibility.md)
[![GitHub Copilot](https://img.shields.io/badge/GitHub_Copilot-supported-success?style=flat-square)](docs/host_compatibility.md)

[![DOI](https://img.shields.io/badge/DOI-10.5281%2Fzenodo.20155321-blue?style=flat-square)](https://doi.org/10.5281/zenodo.20155321)
[![arXiv](https://img.shields.io/badge/arXiv-2606.09500-b31b1b?style=flat-square)](https://arxiv.org/abs/2606.09500)
[![Citation](https://img.shields.io/badge/Cite-CITATION.cff-blue?style=flat-square)](CITATION.cff)
![Built by](https://img.shields.io/badge/Built_by-Physician--Researcher-blue?style=flat-square)

![MedSci Skills](https://raw.githubusercontent.com/Aperivue/medsci-skills/main/assets/social-preview.png)

*主题发现→文献检索→全文检索→研究设计→样本量→方案→去识别化→数据清理→统计→图表→写作→人性化→合规性→期刊选择→同行评审→修订→演示*

**Created & maintained by [Yoojin Nam, MD](https://orcid.org/0000-0001-8565-1360)**
<br>
<sub>韩国首尔蔚山大学医学院放射科和放射学研究所，峨山医疗中心</sub>

</div>

![check-reporting demo](demo.gif)

---

## 什么是医学科学技能？

MedSci Skills 是一个开源 **Agent Skills** 集合，用于 **临床
研究——手稿和类似的医疗人工智能模型**——旨在驱动
直接由 AI 编码代理（Claude Code、Codex、Cursor 和 GitHub Copilot）执行。它有帮助
医生研究人员和生物医学/医学工程研究人员从
文献检索、研究设计、统计数据和报告指南的数据
合规性、引文/参考文献审核、数字一致性检查，以及
回复审稿人的工作流程——将代理写作与**确定性相结合
提交级生物医学研究的完整性门**。从 **v5.0** 开始，它添加了
**模型工程车道**：选择纸接地架构，脚手架a
可重现、防泄漏的 PyTorch 培训存储库，并进行验证、记录和
评估医学影像或 LLM/MLLM 模型，以便工作达到论文 — 它
为前向传递烟雾测试提供了一个最小的可运行默认模型
**集成** MONAI / nnU-Net / timm / torchvision 用于生产级模型，
而不是重新构建生态系统。临床AI模型研究
工程属于范围；它**不是**诊断工具、自主作者或
通用人工智能科学家平台，每个输出都需要人类专家验证。
New here? See the [3 workflows below](#start-here-3-workflows), the
[FAQ](docs/faq.md), the
[research connectors it calls](docs/connectors.md) (keyless public APIs — nothing to set
在常见情况下），并且
[scope boundary](ROADMAP.md#not-planned--explicitly-out-of-scope).

---

## 快速入门

**No terminal?** Use the classroom installer ZIP — download, unzip, double-click the installer, then restart your agent app (see [Installation](#installation)).

**有终端吗？** 最快的路径 - 一个命令，无需克隆：

```bash
npx medsci-skills install        # copies every skill into your agent's folder
```

**推荐（特别是对于临床医生）：** 添加 `--enable-update-notify`，以便 Claude Code 在新版本发布时显示一行 *“更新可用”* 通知 - 否则您将停留在已安装的版本上，并且永远不会被告知。 （根本没有终端？下面的教室安装程序会为您打开此功能。）

```bash
npx medsci-skills install --enable-update-notify        # install + in-app update reminders
```

**有 git 吗？** 通过三个命令安装每项技能：

```bash
git clone https://github.com/Aperivue/medsci-skills.git
mkdir -p ~/.claude/skills
cp -r medsci-skills/skills/* ~/.claude/skills/
```

Restart Claude Code, then start with **`/orchestrate`** — it classifies your request and routes you to the right skill. Full install options (Codex, Cursor, individual skills) are in [Installation](#installation).

### 使用`gh skill`安装

MedSci Skills follows the [Agent Skills standard](https://agentskills.io), so GitHub CLI ≥ 2.90 can search, preview, and install any skill straight from this repo — no clone (a `gh` preview feature):

```bash
gh skill search medsci                                   # list the whole collection
gh skill preview Aperivue/medsci-skills check-reporting  # read a skill before installing
gh skill install Aperivue/medsci-skills check-reporting  # install just that one
gh skill install --all Aperivue/medsci-skills            # or install every skill
```

按技能本身的名称（`check-reporting`、`verify-refs`、`meta-analysis`）或按 `medsci` 搜索以列出所有技能 - 两者都直接返回此存储库。像 `systematic review` 这样的广泛主题词已被 GitHub 上的数百个技能共享，因此添加 `--owner Aperivue` 即可仅查看我们的技能。

### 作为 Claude Code 插件安装

更喜欢插件？一条线增加了市场； `/plugin` 然后让您浏览九个类别插件并启用您想要的插件：

```text
/plugin marketplace add Aperivue/medsci-skills
/plugin            # browse nine category plugins; enable the ones you want
```

|插件 |封面|
|--------|--------|
| `medsci-literature` |文献检索、全文检索、Zotero 同步、参考文献完整性审核 |
| `medsci-data` |研究设计、变量操作化、样本量、数据清理、去识别化、密码本、数据集版本控制 |
| `medsci-modeling` |架构选择、可重复的模型支架存储库、模型验证审核、模型卡/数据表、模型和 LLM/MLLM 评估 |
| `medsci-analysis` |统计数据、数字、批量/跨国/重复分析、荟萃分析 |
| `medsci-writing` | IMRAD 和协议起草、AI 模式删除、AI 搜索优化、审稿人回复 |
| `medsci-review` |自我审查、同行审查、报告指南合规性 |
| `medsci-submission` |提交包装、期刊选择、ICMJE/IRB 表格填写、资助提案 |
| `medsci-project` |编排、项目接收/管理、差距和主题发现、作者策略 |
| `medsci-presentation` |演示/PPTX、PDF/文档渲染、环境搭建、技能发布 |

安装单个类别并在该命名空间下调用其技能：

```text
/plugin install medsci-analysis@medsci-skills
/medsci-analysis:analyze-stats
```

所有九个插件共享相同的存储库源，因此该插件按类别分组并启用技能 - 它不是部分下载。市场跟踪 `main`，因此插件的版本是其 git 提交。

**只想要一种功能？** 两项技能也作为重点独立存储库发布（生成的镜像；此存储库保留事实来源），每项都可以通过 `/plugin marketplace add Aperivue/QZK68VXM` 单独安装：

- [`Aperivue/verify-refs`](https://github.com/Aperivue/verify-refs) — catch fabricated/mismatched citations (PubMed + CrossRef).
- [`Aperivue/check-reporting`](https://github.com/Aperivue/check-reporting) — audit a manuscript against the bundled EQUATOR reporting guidelines and risk-of-bias tools.

---

## 从这里开始：3 个工作流程

新用户不需要立即掌握所有技能。大多数工作都是从以下三个之一开始的
工作流程。每个都通过 `/orchestrate` 运行或通过调用中的指定技能来运行
订单；所有输出都需要人工专家审查。

**工作流程 A — 稿件提交前审核。** *当*稿件即将完成时使用
准备就绪，并且您希望在审阅者看到它之前对其进行检查。 *技能：* `/self-review` →
`/check-reporting`→`/verify-refs`→`/sync-submission`。 *在：*您的手稿
（+ `refs.bib`，表格/数字）。 *输出：*预期的审稿人评论，逐项
报告指南审核、引文完整性报告和提交包
漂移检查。 *安全：*它标记问题；您修复并验证它们。

**工作流程 B — 数据到手稿包。** *当*您拥有清理过的数据集时使用
并且需要一份完整的草稿。 *技能：* `/clean-data` → `/analyze-stats` → `/make-figures` →
`/write-paper`→`/check-reporting`→`/find-journal`。 *在：*已清理的 CSV/镶木地板中
+ 一个研究问题。 *输出：*可重复的分析代码，可出版的数据，
IMRaD 草稿、报告清单和期刊候选清单。 *安全：*统计数据
并且索赔必须根据您的数据进行验证；该工具包从不捏造数字
或参考文献。

**工作流程 C — 系统审查/荟萃分析。** *当*您正在运行一个项目时使用
SR/MA。 *技能：* `/meta-analysis`（与`/search-lit`、`/make-figures`、
`/check-reporting`）。 *在：*一个研究问题+搜索策略。 *输出：*普洛斯彼罗风格
协议支架、筛选/提取结构、PRISMA 一致计数和
图表、汇总估算数据和手稿。 *安全：*筛选和
提取决策由人工审核团队负责。

## 现场演示：五种研究类型，五个完整的管道

五个公共数据集。五种学习类型。演示 1-3 每个都生成完整的手稿、可供出版的数据以及报告合规性审核；演示 4 端到端运行医疗人工智能**模型工程通道**（支架 → 门 → 训练 → 评估 → 可解释性）；演示 5 将该通道带到 GPU 集群上，然后发送到**真正的外部队列**，然后报告其损坏的位置。

|演示 |数据集 |学习类型 |合规|
|------|---------|------------|------------|
| [演示 1：Wisconsin 乳腺癌](demo/01_wisconsin_bc/) | `sklearn` 内置数据集 | 诊断准确性 | STARD 2015 |
| [演示 2：卡介苗疫苗](demo/02_metafor_bcg/) | `metafor::dat.bcg`（13 项 RCT） | 荟萃分析 | PRISMA 2020 |
| [演示 3：NHANES 肥胖](demo/03_nhanes_obesity/) | CDC NHANES 2017-18 | 流行病学（抽样调查） | STROBE |
| [Demo 4: PneumoniaMNIST CNN](demo/04_pneumoniamnist_cnn/) | `medmnist` (CC BY 4.0) | Medical-AI model engineering (CNN) | CLAIM / TRIPOD+AI |
| [Demo 5: MSD → AMOS spleen](demo/05_msd_amos_spleen/) | MSD Task09 + AMOS22 (CC BY 4.0) | 3-D segmentation, external validation + modality shift | CLAIM / Metrics Reloaded |

### 演示 1：诊断准确性 — 威斯康星州乳腺癌

```python
from sklearn.datasets import load_breast_cancer
data = load_breast_cancer()  # 569 samples, zero download
```

**`orchestrate --e2e` 的产出**（[查看完整演示](demo/01_wisconsin_bc/)）：

<details>
<summary>完整输出列表 - 手稿、图表、STARD流程、清单（点击展开）</summary>

|输出|描述 |
|--------|-------------|
| [稿件](demo/01_wisconsin_bc/manuscript/manuscript.md) | IMRAD 草稿，约 1,800 词 |
| [扉页](demo/01_wisconsin_bc/manuscript/title_page.md) | 含要点的 STARD 扉页 |
| [DOCX](demo/01_wisconsin_bc/manuscript/manuscript_final.docx) | 可直接投稿的 Word 文档 |
| [ROC 曲线](demo/01_wisconsin_bc/analysis/figures/roc_curve.png) | 三模型比较，含 DeLong 95% CI |
| [混淆矩阵](demo/01_wisconsin_bc/analysis/figures/confusion_matrices.png) | 阈值 0.5 下各模型的混淆矩阵 |
| [STARD 流程图](demo/01_wisconsin_bc/figures/stard_flow.svg) | 由 D2 生成的 STARD 2015 流程图 |
| [报告清单](demo/01_wisconsin_bc/qc/reporting_checklist.md) | STARD 2015 — 合规率 60.9%（适用条目 14/23） |
| [Self-Review](demo/01_wisconsin_bc/qc/self_review.md) | Initial 82 (REVISE) → 88 (PASS) after 1 fix iteration; final 0 major / 1 minor |
| [流水线日志](demo/01_wisconsin_bc/qc/_pipeline_log.md) | 7 步端到端执行记录 |

</details>

**管道：** `analyze-stats` → `make-figures` → `write-paper` → AI 模式扫描 → `check-reporting` (STARD) → `self-review` → DOCX 构建 → `present-paper`

### 演示 2：荟萃分析 — 卡介苗疫苗功效

```r
library(metafor)
data(dat.bcg)  # 13 RCTs, 357,347 participants (Colditz et al. 1994)
```

**`orchestrate --e2e` 的产出**（[查看完整演示](demo/02_metafor_bcg/)）：

<details>
<summary>完整输出列表 - 手稿、森林/漏斗图、PRISMA 流程、清单（点击展开）</summary>

|输出|描述 |
|--------|-------------|
| [稿件](demo/02_metafor_bcg/manuscript/manuscript.md) | 合并 RR = 0.489（95% CI：0.344–0.696），约 2,200 词 |
| [扉页](demo/02_metafor_bcg/manuscript/title_page.md) | 含要点的 PRISMA 扉页 |
| [DOCX](demo/02_metafor_bcg/manuscript/manuscript_final.docx) | 可直接投稿的 Word 文档 |
| [森林图](demo/02_metafor_bcg/analysis/figures/forest.png) | 13 项研究，随机效应模型（REML），300 dpi |
| [漏斗图](demo/02_metafor_bcg/analysis/figures/funnel.png) | 小样本效应／发表偏倚的可视化 |
| [PRISMA 流程图](demo/02_metafor_bcg/analysis/figures/prisma_flow.svg) | 由 D2 生成的 PRISMA 2020 流程图 |
| [Reporting Checklist](demo/02_metafor_bcg/qc/reporting_checklist.md) | PRISMA 2020 — 57.1% (24/42) at check-reporting → 61.9% (26/42) after self-review fix |
| [Self-Review](demo/02_metafor_bcg/qc/self_review.md) | Initial 78 → 82 (REVISE) after 1 fix iteration; 3 major / 4 minor (majors are out-of-scope RoB/GRADE/references) |
| [流水线日志](demo/02_metafor_bcg/qc/_pipeline_log.md) | 7 步端到端执行记录 |

</details>

**管道：** `analyze-stats` (R Metafor) → `make-figures` → `write-paper` → AI 模式扫描 → `check-reporting` (PRISMA 2020) → `self-review` → DOCX 构建 → `present-paper`

### 演示 3：流行病学 — NHANES 肥胖与糖尿病

```python
# Pre-processed NHANES 2017-2018 CSV included
# 5,010 US adults after exclusions
```

**`orchestrate --e2e` 的产出**（[查看完整演示](demo/03_nhanes_obesity/)）：

<details>
<summary>完整输出列表 - 手稿、OR 森林图、STROBE 流、清单（点击展开）</summary>

|输出|描述 |
|--------|-------------|
| [稿件](demo/03_nhanes_obesity/manuscript/manuscript.md) | 校正后 OR = 3.03（95% CI：2.29–4.02），约 1,850 词 |
| [扉页](demo/03_nhanes_obesity/manuscript/title_page.md) | 含要点的 STROBE 扉页 |
| [DOCX](demo/03_nhanes_obesity/manuscript/manuscript_final.docx) | 可直接投稿的 Word 文档 |
| [OR 森林图](demo/03_nhanes_obesity/analysis/figures/forest_or.png) | 7 个变量的校正后比值比 |
| [研究流程图](demo/03_nhanes_obesity/analysis/figures/strobe_flow.svg) | 由 D2 生成的受试者流程图 |
| [报告清单](demo/03_nhanes_obesity/qc/reporting_checklist.md) | STROBE — 合规率 83.3%（适用条目 25/30） |
| [Self-Review](demo/03_nhanes_obesity/qc/self_review.md) | ACCEPT-WITH-NOTES after 1 fix iteration; 0 genuine majors remaining |
| [流水线日志](demo/03_nhanes_obesity/qc/_pipeline_log.md) | 7 步端到端执行记录 |

</details>

**流程：** `analyze-stats` → `make-figures` → `write-paper` → AI 模式扫描 → `check-reporting` (STROBE) → `self-review` → DOCX 构建 → `present-paper`

### 演示 5：外部验证 — MSD → AMOS 脾分割

离开笔记本电脑的唯一演示，也是唯一报告**故障**的演示。它询问是否
临床医生可以在没有工程师的情况下进行深度学习研究以获得可靠的结果，然后通过
在 GPU 集群上运行三级外部验证阶梯并记录每个点
答案是否定的。

|横档|队列| n 得分 |骰子中位数 [95% CI] |
|---|---|---:|---|
| 1 内部 |默沙东坚守| 9 | **0.9595** [0.9367–0.9734] |
| 2正品外置|阿莫斯 **CT** | 298 / 300 | **0.8932** [0.8633–0.9108] |
| 3 形态转变 |阿莫斯 **MRI** | 59 / 60 | 59 / 60 **0.0152** [0.0000–0.0626] |
| 3b 反事实 | AMOS MRI，**重新调整** | 59 / 60 | 59 / 60 **0.3016** [0.1744–0.4048] |

第 3 级是一个**构建的**测试，演示中是这样说的：评估计划名为标准化
合约并在推理运行“之前”预测崩溃。训练计划搭载`CTNormalization`
进行推理，并且没有标记显示“这是 MRI”，因此将 Hounsfield 单位剪辑应用于
任意单位图像：**60 个 MRI 病例中的 0 个包含阴性体素**（相对于 CT 上 300 个病例中的 300 个），以及
中位数 **23.2 %** 的体素在剪辑上限处变平（相对于 2.7 %）。运行退出 0 且
返回所有 60 个案例的文件，其中 20 个为空。只有事实真相才能让它响亮。

第四臂改变**仅输入强度等级** - 相同的检查点，无需重新训练 - 并且
将 Dice 中位数恢复至 **0.3016** (+0.2864 [+0.1204, +0.4048])，同时保持 **−0.5916** 低于
CT 手臂。所以这两种机制都是真实的并且大小不同：大约 **0.29 Dice 是预处理
合同，0.59 表示不转让**。手臂和它的预测被写下来
在它跑之前就下来了。

`/profile-imaging` **在训练前已经标记了混合强度量表 - 作为
次要**，它在 `qc/` 中停留了九天。所以这个演示发现的差距不是检测；而是检测。是的
**路由和严重性**。正确触发到目录且后续步骤不读取的门是，
operationally, a gate that did not fire. See [the full demo](demo/05_msd_amos_spleen/) — including
[`FRICTION.md`](demo/05_msd_amos_spleen/FRICTION.md), which lists every point that needed engineering
知识，因为如果没有它，标题问题就无法诚实回答。

**管路：** `profile-imaging` → `model-sourcing` → `preprocess-imaging`（漏栅，加上
必须失败的反事实）→ `model-validation`（分裂门）→ nnU-Net 训练→
`model-evaluation` → `make-figures` → 写入。 `bash reproduce.sh`重新运行门和整个
在笔记本电脑上进行跨队列分析；训练需要大约 50 个 GPU 小时，并且是这样说的。

### 项目文件夹结构

每个演示（和实际项目）都遵循以下基于角色的文件夹布局：

```
project/
├── data/                          # Input data
│   └── raw_data.csv
├── analysis/                      # /analyze-stats + /make-figures outputs
│   ├── tables/
│   ├── figures/
│   │   └── _figure_manifest.md
│   ├── _analysis_outputs.md
│   └── analyze.py
├── manuscript/                    # /write-paper outputs
│   ├── manuscript.md
│   ├── manuscript_final.docx
│   └── title_page.md
├── qc/                            # Quality verification
│   ├── reporting_checklist.md     # /check-reporting
│   ├── self_review.md             # /self-review
│   └── _pipeline_log.md
├── submission/                    # Post-journal-selection (manual trigger)
│   └── {journal_short}/
│       ├── cover_letter.md
│       ├── checklist.md
│       └── peer_review.md
└── presentation/
    └── presentation.pptx
```

E2E 管道 (`orchestrate --e2e`) 生产直至 `qc/` 的所有产品。 `submission/` 目录是在通过 `/find-journal` 选择期刊后创建的。

---

## 什么是新的

**v5.24.0** — a precision release: the gates were wrong about correct work. Fourteen shipped detectors were telling users something false, and the pattern behind most of them is one thing — a checker that accepts only its own generator's output and rejects the notation the world actually uses. `check_xref` did not recognise **"Figures 1 and 2"**, so a float cited the ordinary way scored `UNCITED` and the submission blocker **turned itself off** (`submission_safe: true` on a package missing a figure). `verify_refs` read BibTeX's own **`and others`** — the et-al. every reference manager writes — as `AUTHOR MISMATCH`, the render-aborting verdict, on correct consortium references; and an entry whose **last** field was the DOI parsed as having none, silently disabling the CrossRef and author cross-checks that skill exists to perform. `check_table_percentages` **invented a denominator** for the most common table in clinical research and printed specific wrong replacement percentages at MAJOR. `lint_consistency` advised writing **"type two diabetes"**. `check_asset_anonymization` passed a **double-blind institution leak** because it sat in a `.yaml`. `check_slide_tells` flagged the page numbers **this repository's own template generator** writes. `fill_journal_abbrev.py` had **never run** — it raised on its first entry, for every input, while another gate named it to the user as the remedy. And `refinement_stop` called a leftover `TODO` an *optional Minor* and told the loop to stop. Also: the release job's own failure had left v5.23.0 with **zero assets** and npm a version behind, with no way to retry a pushed tag — now create-or-update, outcome-asserted, and dispatchable; two of the four documented install paths were broken, and the worse one **succeeded** while making `~/.claude/skills` itself the skill; and the front page said **36** detectors while the catalog, the audit document and the paper said 84. Every fix ships a regression test that goes red against the previous behaviour. No new skill or detector; **58 skills / 47 guidelines / 84 integrity detectors / 23 domain-probe modules**. (See the [CHANGELOG](CHANGELOG.md) for v5.0–v5.23.)

**v5.21** — verification-layer batch, mostly promoted from real submission failures. A **marked (tracked-changes) manuscript** is now built by driving Word's Compare from the command line and proved by a **round trip** — accepting every revision must reproduce the revised paper exactly, rejecting every revision must reproduce the original — and the gate is **move-aware**, because Word encodes a relocated paragraph as `w:moveFrom`/`w:moveTo` and an insert-and-delete-only verifier calls a good file corrupt. Every detector's `qc/*.json` now **names the detector that wrote it**, so an artifact can be traced back to the check that produced it (a CI-enforced contract). Two `/verify-refs` precision defects: a Unicode hyphen in a surname fired `MISMATCH` — the verdict that means *fabricated author* — on a correct reference, and a Better BibTeX brace-protected surname was read as a corporate author, **silently skipping** the author check the tool exists to perform. New gates: publisher markup in a `.bib` title (`<scp>WHO</scp>` renders as garbage and no gate looked at the printed title), **complete/quasi separation** before a logistic model is fitted (a pathognomonic sign has an empty cell by construction; `glm` returns OR = 0.00, *p* = 0.99, and an AUC that gets reported), and a probe + gate for manuscripts claiming a system **improved itself** (which rung of the verification hierarchy said so?). `/find-cohort-gap` now accepts a **local codebook** — an institutional registry or EMR export, not only a named public cohort — enumerating variables verbatim with provenance rather than letting a model summarise them. Additive and backward-compatible; **55 skills / 46 guidelines / 61 integrity detectors / 23 domain-probe modules**. (See the [CHANGELOG](CHANGELOG.md) for v5.0–v5.20.)

**v5.20.1** — 审计驱动的一致性修复。一个真正的 `/orchestrate --e2e` 状态转换错误（管道在步骤 3 停止，因为它需要仅在步骤 7 渲染的 DOCX），所有 55 种技能都可以通过 CI 可达性门从单个入口点路由，以及从市场 SSOT 漂移的 README 插件计数（现已门控）。没有技能/探测器变化。

**v5.20** — reviewer-arithmetic gates. Five deterministic `self-review` detectors promoted from a peer-review cycle, each recomputing what a manuscript already prints: `check_table_percentages` (an `n (%)` cell vs its column denominator), `check_nested_group_comparison` (a P value comparing an analysed subset against the parent cohort that **contains** it — nested, invalid), `check_reported_p_from_counts` (rebuilds each 2×2 row and recomputes Fisher / Pearson χ² ± Yates in **pure stdlib**, calibrating the family on rows that reproduce), `check_dta_denominators` (sensitivity/specificity denominators vs the reference-standard category counts, behind a matching grand total), and `check_paired_difference_estimator` (an odd-n integer-scale median cannot be non-integer; a zero-width CI; an unnamed estimator). Plus `/peer-review` request-type discipline (disclosure vs computation) and impossibility-claim verification. Additive and backward-compatible; **55 skills / 46 guidelines / 57 integrity detectors / 22 domain-probe modules**. (See the [CHANGELOG](CHANGELOG.md) for v5.0–v5.19.)

**v5.19** — reviewer-safety + reporting-checklist batch. A **PDF hidden-text / prompt-injection guard** for `/peer-review` — a PyMuPDF extractor plus a stdlib detector that catch a review-steering instruction hidden in a submitted PDF (white-on-white text, sub-visible fonts, off-page glyphs, invisible render mode, or a document-metadata field) before an LLM ingesting the text layer can be steered by it, and emit visible-only text to feed a model instead of the raw PDF; plus the **TARGET** (target-trial emulation; Cashin et al., *JAMA* 2025) and **REMARK** (prognostic tumour-marker; McShane et al.) reporting checklists. Additive and backward-compatible; **55 skills / 46 guidelines / 52 integrity detectors / 22 domain-probe modules**. (See the [CHANGELOG](CHANGELOG.md) for v5.0–v5.18.)

**v5.18** — reliability & workflow-integrity batch. A new deterministic **response-claim gate** for `/revise` and `/peer-review` (verifies a response letter's "we added / we now cite X" against the *revised manuscript body* — a claimed-but-absent edit is caught before it reaches a reviewer; **detectors 50 → 51**), a **reframe / headline-change survivor scan** (`--retired-term` / `--old-value`, finds stale framing or superseded values left in the body, supplement, and figure legends after a reframe), a pre-drafting **backbone full-text readiness gate** for `/write-paper` (the backbone article is *used*, not merely detected), a **skill-registry consistency validator** (`capabilities.yml` ⇄ `skill.yml`, CI-enforced), AI-tool **citation-framing** guidance for `/academic-aio`, and **Demo 4** (PneumoniaMNIST CNN, the model-engineering lane end to end). Additive and backward-compatible; **55 skills / 46 guidelines / 51 integrity detectors / 22 domain-probe modules**. (See the [CHANGELOG](CHANGELOG.md) for v5.0–v5.17.)

**v5.17** — model-engineering produce-side depth, **completion**. Deployment safety + the final roadmap/candidate items: a new **`uncertainty-imaging`** skill + `check_uncertainty_reporting` gate (calibrated per-case uncertainty / OOD guard on a held-out set / abstention at a pre-specified target / calibration-under-shift — for a deployment-framed model), an **MLOps wiring reference** for `model-scaffold` (experiment tracking, config/data/environment versioning, CI-for-ML — pointing to W&B / MLflow / nnU-Net, reimplementing nothing), and an **`architecture-zoo` graph-neural-net family card** (GCN / GraphSAGE / GAT / GIN / BrainGNN for brain connectomes) that closes the last candidate gap. The six-item produce-side depth roadmap and its candidate list are now complete. Additive and backward-compatible; **55 skills / 46 guidelines / 50 integrity detectors / 22 domain-probe modules**. (See the [CHANGELOG](CHANGELOG.md) for v5.0–v5.16.)

**v5.16** — model-engineering produce-side depth, clinical fine-tuning focus (Items 3–4 of the [produce-side depth roadmap](docs/roadmap_model_engineering_depth.md)). A new **`radiomics-ml`** skill + `check_radiomics_ml` gate for the most common solo-doable clinical-ML workflow — radiomics / tabular features → any classical learner (LASSO / SVM / random forest / XGBoost / …) → a clinical outcome, no GPU — with a learner-agnostic nested-CV / calibration / stability gate; plus a **`model-scaffold` fine-tuning mode** (`--task finetune` + `--from-pretrained`) that adapts a pretrained backbone on collected clinical data with a frozen→unfrozen schedule, discriminative learning rates, and a pretrained-weight provenance record (`PRETRAINED.md` + a `PRETRAINED_PROVENANCE_MISSING` verdict on the existing `check_training_hygiene`, plus a MedSAM-adaptation + train-only diffusion-augmentation guide). Additive and backward-compatible; **54 skills / 46 guidelines / 49 integrity detectors / 22 domain-probe modules**. (See the [CHANGELOG](CHANGELOG.md) for v5.0–v5.15.)

**v5.15** — model-engineering produce-side depth. Two new skills that *produce* what the review lane previously only audited: **`preprocess-imaging`** (DICOM/NIfTI data prep + a `check_preprocessing_leakage` gate that extends the split-leakage moat upstream to the data stage) and **`explainability`** (Grad-CAM / saliency held to the reviewer bar — Adebayo sanity checks, quantitative localisation vs ground truth, attribution-not-validation framing, via `check_explainability_report`). Plus a by-stage skill index, multi-host README/About (Claude Code · Codex · Cursor · Copilot), copy-paste citation ergonomics, and a real-project precision fix. Additive and backward-compatible; **53 skills / 46 guidelines / 48 integrity detectors / 22 domain-probe modules**. (See the [CHANGELOG](CHANGELOG.md) for v5.0–v5.14.)

**v4.10** — 从高 IF、CC-BY 论文（仅在 `reverse_engineer/` 许可证防火墙下学习）进行逆向工程的审稿人覆盖范围扩展，以及临床医生友好的更新路径。附加和向后兼容； 45 项技能 / **46 条指南** / 36 个检测器 / **15 个域探测模块**（原为 12 个）：

- **三个新的审阅者域探针模块**（`/peer-review` + `/self-review`，供应商字节相同）：**孟德尔随机化**（MR1–MR8 - IV假设，多效性鲁棒敏感性套件，Steiger，样本重叠，NLMR，药物靶标共定位），**多基因风险评分**（PG1–PG8 - 祖先可移植性，基础/目标泄漏、临床模型的增量值、筛选与歧视、校准）和**网络荟萃分析**（NM1-NM8 - 传递性、不连贯性、SUCRA 过度解释、CINeMA/GRADE-NMA、组件 NMA 可加性）。加上观察**O17**（不可知的多次曝光扫描多重性：ExWAS/EWAS/MWAS）。
- **两个报告指南清单** (36 → 38)：**STROBE-MR** 和 **PGS-RS / PRS-RS**，具有研究型路由。四个新的 `/analyze-stats` 分析指南（多重性、MR、PRS、NMA）和 `/clean-data` 难以置信的值 + 跨领域有效性参考。
- **临床医生友好的更新提醒** — 教室安装程序默认启用应用内“可用更新”通知 + 一键桌面更新程序； `npx`/手动路径打印如何打开它；安装指南推荐`npx medsci-skills install --enable-update-notify`。

**v4.9** — 从真实的审阅周期中提升分析完整性强化，以及期刊机制的补充。附加和向后兼容；还有 45 项技能/46 条指南，分析完整性检测器 **32 → 36**：

- **四个新门** - 针对混合 `[@key]` + 手动输入 `## References` 构建的 **重复参考书目** 检查 (`check_reference_duplication.py`)，该构建会渲染列表两次；针对跨分析脚本定义不一致的派生分类或复合指标进行**跨脚本分箱/复合指标**一致性检查（`check_binning_consistency.py`、`BINNING_DRIFT` / `DERIVED_DEF_DRIFT`）； **浮动引用顺序**检查（`check_citation_order.py`），用于检查每个系列中未首先按升序引用的编号表/图；以及一个**审核转储泄漏**门（`/sync-submission`），它阻止错误地附加为提交文件的 `/check-reporting` 输出。
- **KJR 技术检查约定 + 百分比小数风格**、读者分配下负担和生成图像作为研究对象报告（`/design-ai-benchmarking`、`/check-reporting`），以及 **Liver International** CSL 以及该期刊的提交机制（`/manage-refs`）。

**v4.8** 是 **评审-收获批次** - 从真实手稿评审周期中提升的确定性检测器强化。附加和向后兼容；还有 45 项技能/46 项指南，分析完整性检测器 **30 → 32**：

- **两个新的门** - `check_supplement_hygiene.py` lint 渲染的补充/表格/标题文件（不仅仅是手稿），用于§-标签、占位符、构建标记、响应字母框架和未解决的正文↔补充交叉引用； `check_null_calibration.py` 标记了没有最小可检测效果/功效/等效声明的标题负面/等效声明。
- **四个探测器误报修复** - 门不再在推荐的色盲安全调色板、作者脚注 `§` 匕首、正确对冲的免责声明或等级标签数字上触发；每个都有一个回归夹具和三个新的 CI 连线测试套件。
- **九个审阅者端域探针**（SR/MA、观察、诊断、AI-overclaim、生存）加上用于感知/读者-AI研究的`/design-study`设计阶段天花板门和可重复使用的置信加权评级→AUC单调性模板。

**v4.7** 是**自我更新基础** - 医生研究人员无需 GitHub、git 或终端即可保持最新状态。附加和向后兼容；还有45个技能/46个指南/30个探测器：

- **事务性、崩溃可恢复的安装程序。** 每次安装都通过持久日志状态机运行，并在下次运行时恢复（回滚/前向清理/故障关闭），并带有每个目标 SHA-256 清单 - 您修改的或第三方技能都会得到备份，并且永远不会被破坏或自动删除。
- **一键式自我更新**（`~/.medsci-skills/updater/`、`install.py --check-update`）。根据 github.com API 摘要验证下载，**从不使用 `extractall()`**（每个条目拒绝遍历/符号链接/重复/zip 炸弹 + 允许列表和每个文件哈希）。发布管道注入经过验证的 `provenance.json`，证明构建来源，在受保护的 `release` 环境上运行，并在发布之前通过更新程序自己的安全提取验证每个 ZIP 往返。
- **选择加入更新通知（默认情况下关闭）：** `install.py --enable-update-notify` 在 Claude Code 会话启动时显示一行“更新可用”消息 — 没有遥测，不会读取任何有关会话的信息，也不会安装任何内容。 `--disable-update-notify` / `MEDSCI_NO_UPDATE_CHECK=1` 将其关闭。 *（诚实范围：摘要/证明检测传输篡改，而不是受损的发布者帐户 - 请参阅 `SECURITY.md`。）*

**v4.6** 是一个可维护性、治理和审查深度的版本 - 仍然有 45 项技能/46 条指南；分析完整性检测器 **28 → 30**，域探针 11 → 12：

- **公平/公正/亚组绩效探针 (EQ0–EQ6)**，用于声称跨群体绩效的人工智能/预测/诊断研究，以及两个新检测器：**人工智能披露 + 数据/代码可用性**检查 (`/sync-submission`) 和 **结构化摘要框一致性**检查 (`/academic-aio`)。
- **治理 + 答案引擎层：** `ROADMAP.md`、`MAINTAINERS.md`、`SECURITY.md`、维护人员工作流程 + 发布清单、AEO/GEO `docs/faq.md`、本自述文件中的“从这里开始：3 个工作流程”+“验证状态”部分，以及关于每项技能的新 `maturity` 字段（官方/实验/社区）。
- **令牌饮食（试点）：** `write-paper` 第 7 阶段完整性审核已移至按需加载参考（每次调用保存约 2,559 个令牌）。现在，定位以合规护城河而不是技能计数为主导。

**v4.5** 加深了审查+提交表面，没有新技能或报告指南计数（仍然是 45 项技能/46 项指南）；分析完整性检测器 **27 → 28**：

- **`/clean-data` + `/analyze-stats` — 反向编码项目/负 alpha 检测器。** 具有负面措辞项目的多项目李克特量表必须在计算量表总计或 Cronbach's alpha 之前重新编码 `(min+max) − x`；如果不重新编码，该项目与量表的其余部分呈负相关，并且 alpha 崩溃（通常为负）。负阿尔法是一个编码错误，而不是“多维构造”。新的仅 stdlib `check_reverse_coding.py` 从每项项剩余相关性 + 原始 alpha 返回 `REVERSE_CODING_LIKELY` / `REVERSE_CODING_SUSPECT` / `OK`； Likert 摘要模板获得 `--reverse-items` 重新编码标志。
- **`/peer-review` + `/self-review` — SR/MA + DTA + 预测模型探测批次。** `sr_ma.md` **P12** 偏差风险表行总和 ↔ 交通灯图形矩阵协调和 **P13** 包含研究 ↔ 参考列表完整性； `diagnostic_accuracy.md` **D7** 索引测试作为注册标准的循环性； `clinical_prediction_model.md` **CP5** 预期用途范围泄漏和 **CP6** 开发/CV 与保留/外部验证命名法合并。 `/self-review` 中的字节相同。
- **`/sync-submission` — 嵌入式绝对路径泄漏扫描。** 携带绝对主目录路径（`/Users/…`、`/home/…`）的 `word/*.xml` 属性（例如 pandoc 嵌入图像的 `QZK286VXM`）是渲染文本扫描不可见的用户名泄漏；现在在 `check_asset_anonymization.py` 下标记为 `docx_embedded_abs_path`。

**v4.4** 增加了审阅者/分析深度，没有新技能或报告指南计数（仍然是 45 项技能/46 项指南/27 种检测器）：

- **`/author-strategy` — 轨迹原型分类（可选）。** 将查询作者的 PubMed 轨迹分类为抽象职业原型（A1 基础设施构建者、A2 方法论规则制定者、A3 临床 → AI 混合、A4 SR/MA 卷引擎、A5 大联盟参与、A6 设备/技术深度 + 计算组合）作为 **可解释、多标签、置信评分启发式 — 而非客观的判决**。该标题是一个规范的 YAML（叙述性文档是从它生成的）；分数不包括 `unavailable` 信号（h 索引/引文/场地层 → `[VERIFY]`，从未捏造）； **消歧门**将批准的 `corpus_manifest.json` 绑定到 CSV（csv + PMID 集哈希），因此姓氏永远不会单独分类，并且目标作者归属永远不会借用共同作者的 ORCID/隶属关系。
- **`/peer-review` + `/self-review` — 图像合成/跨模态探针 (IS1–IS4)** 用于将一种成像模态与另一种成像模态合成并声称输出携带目标信息的研究，以及审阅者端参考完整性抽查。
- **`/verify-refs` — OpenAlex 三级索引** 恢复 PubMed 和 CrossRef（门户网站第二索引的免费类似物）中的会议记录/非 DOI 引文 (NeurIPS/ICLR/ACL)。

**v4.3** 强化了 **横断面/观察队列** 端到端的审查表面，其中大部分是根据真实的 CC-BY 队列论文进行逆向工程的（仅在许可证防火墙下学习）——没有新技能或报告指南计数（仍然是 45 项技能/46 条指南）；分析完整性检测器 **25 → 27**：

- **观察探针 O1 → O14**（`/peer-review` + `/self-review`，已供货）——过度调整/分析单元聚类/结果结构有效性 (O7–O9)，重叠子集梯度 (O10)，**NHANES/KNHANES (O11) 的复杂调查设计和加权**，**数据驱动阈值/“拐点”挖掘**（O12），**横截面中介**时间顺序和顺序可忽略性（O13），以及**交互规模** - 加法 RERI/AP/S 与乘法（O14）。加上新的**临床预测模型**探针模块**CP1–CP4**和生存**S9**（面板数据/多状态方差）。
- **两个新检测器 (25 → 27)** — `check_wordcount_cap.py`（修订膨胀陷阱：正文 vs 日记帽）和 `check_paren_spans.py`（em-dash→paren 转换，包裹整个句子）。加上 `check_confounding_completeness.py` 升级（DB 代码↔散文别名映射、SMD-from-mean±SD、曝光定义协变量豁免）、`check_cohort_arithmetic.py` `ANALYSIS_UNIT_UNDISCLOSED` 检查、`check_scope_coherence.py` 横截面产量词典以及验证引用公司/集体作者渲染中止修复。
- **分析和提交工具** - `/analyze-stats` 获得**调解**和**交互和效果修改**指南； `/sync-submission` 获得 `assemble_supplement.py`（S{N} 索引↔文件完整性）和 `/revise` 正文字数出口门； `/render-pdf-doc` 获得 `scan_glyph_coverage.py` xelatex 静默字形下降扫描。

**v4.2** 构建了端到端的案例报告功能，以真实的 CC-BY 案例报告为基础（仅在许可证防火墙下学习）——没有新技能或报告指南计数（仍然是 45 项技能/46 项指南）；期刊简介 **68 → 73**：

- **病例报告 + 病例系列写作** — `/write-paper` 获得 CARE 叙述 + 150 字摘要病例报告范例、**病例系列** 论文类型（方法-轻型迷你队列、所有病例汇总表、计数而非比率）和 **不良事件/药物警戒**（Naranjo/WHO-UMC 因果关系）和**诊断陷阱/模仿**亚型。
- **放射学/影像主导的轨道** — 专用的 `exemplar_case_report_radiology.md`（按模态技术→结果→印象、结构化报告词典 BI-RADS/LI-RADS/PI-RADS/TI-RADS/Lung-RADS/O-RADS、定量阈值诚实、介入放射学手术/并发症亚型、DICOM 去识别）加上 `/make-figures`带注释的多模态成像面板示例。
- **病例报告审查探针** — `/peer-review` + `/self-review` 提供供应的病例报告域探针 **CR1–CR9**（新颖性/同意/n=1 因果关系、病例系列设计、不良事件因果关系、成像主导学科）。
- **在哪里提交** — 用于《Journal of Medical Case Reports》、Cureus、Radiology Case Reports、BMJ Case Reports 和 BJR Case Reports 的紧凑 `/find-journal` 配置文件，以及用于不良事件和病例系列亚型的 `/check-reporting` CARE 注释。

**v4.1** 附带分配杠杆和提交飞行前门 - 分析完整性检测器 **24 → 25**（仍然有 43 种技能）：

- **Claude Code 插件市场** — `/plugin marketplace add Aperivue/medsci-skills`，然后 `/plugin` 发现从目录 SSOT (`.claude-plugin/marketplace.json`) 生成的九个 `medsci-*` 类别插件。
- **MedSci-Audit detector registry** — the deterministic verification layer is now a named, enumerated, citable suite ([`MEDSCI_AUDIT.md`](MEDSCI_AUDIT.md) + generated `metadata/detectors_catalog.json`, six audit families).
- **Hero-skill standalone mirrors** — `scripts/sync_hero_skill.py` mirrors a focused skill to its own star-funnel repo; first two live: [`Aperivue/verify-refs`](https://github.com/Aperivue/verify-refs) and [`Aperivue/check-reporting`](https://github.com/Aperivue/check-reporting).
- **占位符/标记门** — `check_placeholders.py` 在提交之前标记剩余的 `[@NEW:]` / `[version]` / `TODO` / 模板 URL 标记（第 25 个检测器）。
- **提交飞行前门** - `preflight_gate.py` 将现有探测器 + `/verify-refs` 捆绑到一个故障停止命令中（`qc/preflight_gate_report.json`，任何阻止程序上的非零退出） - 冻结之前的最后一步。

**v4.0** 将项目自身的确定性、无漂移 SSOT 规则扩展到公共店面，并完成检测器积压工作 — 将 `skills/` 中的分析完整性检测器计数增加到 **24**（仍为 43 项技能）：

- **SSOT to the storefront** — a generated, machine-readable `metadata/skills_catalog.json` (slug + research-lifecycle category + one-line description per skill) is now the source the [aperivue.com](https://aperivue.com/en/skills) storefront vendors, gated offline so the public site can never silently drift behind the repo (`gen_skills_catalog_json.py --check`).
- **资产/图形匿名化** — `/sync-submission` 扫描图形生成脚本、图形 PDF 渲染文本和 docx/PDF 元数据作者，以防止机构/作者泄漏正文文本扫描遗漏 (`check_asset_anonymization.py`)。
- **跨工件陈旧性** - 标记与更正正文不一致的补充值，并报告针对旧手稿版本构建的清单（`check_cross_artifact_stale.py`；带有 `target_manuscript`/`source_sha256` 清单合同的 `check_checklist_version.py`）。
- **生存报告** — `/analyze-stats` 以其 95% CI、每个变量的 Cox 事件门和嵌套观察单元的集群鲁棒性 SE 发出中位生存率。

**v3.8.0** 添加了一个 `evaluation/` 套件，用于验证仪器本身 - 对以编程方式播种的缺陷 (E1) 的确定性检测器召回、新克隆清单再现性 (E4)、索赔审计跟踪完整性 (E5)、主机可移植性和元数据漂移检查 (E6/E7/E8) 以及成本/时间表 (E3) - 每个都编写一个自描述的、可重现的运行包。 LLM 比较器 (E2) 和自我审查收敛工具 (E9) 可以运行，但在此版本中未执行。此版本还使 README Live-Demos 数量与 v3.7.0 洁净室演示工件保持一致。目录不变（仍然是 43 个技能，21 个探测器）。

**v3.7.0** 在 v3.6.0 面板衍生门的基础上添加了三个确定性的、仅限 stdlib 的检测器 - 将 `skills/` 中的分析完整性检测器计数增加到 **21** - 无需扩大目录（仍为 43 种技能）：

- **参考充足性** - `/self-review` 和 `/write-paper` 现在检查草案是否在*右侧*部分引用了*足够的*参考文献，并且*每个命名方法*（竞争风险模型、多重插补、E 值、eGFR 方程）都带有引用 - 补充 `/verify-refs` 完整性层的充分性层（`check_reference_adequacy.py`）。
- **面板镜头多样性** - `/self-review --panel` 对其审阅者进行后处理，因此成本购买的是广度，而不是更大的回声（`check_panel_diversity.py`）。
- **生成代码质量** — `/analyze-stats` lints 发出的分析脚本可重现性问题（缺少种子、硬编码数据文字、绝对路径、就地源覆盖）(`check_generated_code.py`)。

加上发布时技能价值门（`/publish-skill`）和公众采用/影响跟踪（`IMPACT.md`）。

**v3.6.0** 从 13 个项目小组自我审查中获得 18 个关卡（158 个痕迹→ 12 个重复出现的缺陷模式），而没有扩大目录（仍然是 43 个技能）。六个新的 stdlib 检测器加入了现有的三重奏——确定性的 grep 是干净的，散文/探针的调用需要人类：

- **队列和池算术** — `/self-review` 根据事件 ÷ 人年重新计算发病率，平衡 STROBE 排除级联，并检查序数层/层分区的不相交性 (`check_cohort_arithmetic.py`)； `/meta-analysis` 锁定患者/病变总计，并要求重新运行任何“固定”审核记录的证据。
- **声明↔工件↔范围** - 方法↔结果↔磁盘覆盖（标记运行但未报告的分析），端点↔结论范围门（横断面设计不能许可监视声明；二进制替代不是护理指令），以及使LLM作为审稿人致命的审稿人团队3路。
- **统计和报告合同** - CI/估计输出合同（分位数/比例/sHR必须带有95％CI；Cox EPV门；比例-MA Egger禁令+预测区间），区间审查/PH违反/CIF水平生存规则，报告框架基础+扩展命名，经典风格的body lint，PROSPERO ID格式门和分页占位符引用门。

本系列的前面部分：分析完整性防护（混淆完整性、声明与工件、结构零处理）、多代理 `/self-review --panel` 模式以及通过 CI 漂移门以字节相同方式供应到 `/peer-review` 和 `/self-review` 的共享域探测模块。

---

## 为什么选择这个仓库？

| |医学技能 |广泛的技能聚合器|
|---|---|---|
| **引文质量** |每个参考文献在纳入之前都会通过参考文献验证门（PubMed / Semantic Sc​​holar / CrossRef）和引文审核工作流程。 |没有验证——从模型内存生成的引文|
| **管道集成** |技能在定义的链中相互调用。 `design-study` -> `calc-sample-size` -> `write-protocol`。 |没有跨技能交互的独立存根 |
| **端到端覆盖** |从 IRB 协议到期刊提交：样本大小、数据清理、分析、写作、合规性、期刊选择、求职信。 |每次转变时的差距——没有协议、没有期刊匹配、没有求职信|
| **久经考验** |用于执业医师研究员提交的真实手稿 |来源和验证未知 |
| **每项技能的深度** | 150-600 行文档 + 捆绑的参考文件（精选期刊资料库、清单、公式表、代码模板）|通常很薄的 SKILL.md 模板 |

**MedSci-Audit** — 上方前几行中的验证优势来自一套具名的**确定性检测器**套件（引文与参考文献完整性、队列与合并样本量算术、范围/估计量契约、报告合规等），用于在稿件送达审稿人之前捕获虚构或漂移的内容。该套件、其六个族系及评估证据见 **[`MEDSCI_AUDIT.md`](MEDSCI_AUDIT.md)**。

---

## 这不是什么

This is **not** a broad scientific-tooling library — for cheminformatics, structural biology, or genomics pipelines, see [K-Dense scientific-agent-skills](https://github.com/K-Dense-AI/scientific-agent-skills). It is **not** a biomedical-skill aggregator — for a broad curated collection, see [OpenClaw Medical Skills](https://github.com/FreedomIntelligence/OpenClaw-Medical-Skills). For how MedSci Skills compares to these catalogs, see [`docs/competitive_positioning.md`](docs/competitive_positioning.md). For verified cross-agent install paths (Claude Code, Codex, Cursor, GitHub Copilot), see [`docs/host_compatibility.md`](docs/host_compatibility.md).

MedSci Skills **固执己见，目的狭隘**：单一医师研究人员的医学手稿管道，偏向放射学、诊断准确性、观察性 EMR 研究和系统评价/荟萃分析。如果您为临床期刊撰写 IMRAD 稿件、根据 EQUATOR 指南审核报告合规性或端到端运行 SR/MA 工作流程，那么这就是为您打造的。对于湿实验室方案、药物发现或单细胞基因组学，上面的存储库更适合。

---

## 技能

📖 **Per-skill reference:** [`docs/skills/`](docs/skills/) — one page per skill (what it does, when it activates, its Quality Card — purpose, safety boundaries, known limitations, validation, evidence — and bundled resources), generated from each `SKILL.md` + `skill.yml`. See [`docs/skills/AUDIT.md`](docs/skills/AUDIT.md) for how the skills are validated.

🧠 **ML / DL method coverage:** [`docs/method_coverage_map.md`](docs/method_coverage_map.md) — which machine-learning and deep-learning method families (CNN / transformer / segmentation / detection / foundation / diffusion / SSL for imaging; the full classical family — penalised regression, SVM, k-NN, trees, boosting [XGBoost / LightGBM / CatBoost], MLP, ensembles, clustering — for radiomics/tabular; LLM/MLLM) map to which skills for selection, production, validation, interpretation, and reporting.

```
                              ┌─────────────────────────────────┐
                              │  orchestrate: single entry point │
                              │  classifies intent, routes to    │
                              │  the right skill or chains them  │
                              └───────────────┬─────────────────┘
                                              │
                  ┌───────────────────────────┼───────────────────────────┐
                  │                           │                           │
            intake-project              (main pipeline)             grant-builder
            (new/messy projects)              │                    (proposals)
                  │                           │
                  ▼                           ▼
                                    ┌── calc-sample-size ──┐
                                    │                      ▼
ma-scout -> search-lit -> fulltext-retrieval -> design-study ──> write-protocol -> manage-project
   │            │
   │            └── find-cohort-gap (DB variables → literature gap → ranked topic proposals)
   │                                    │
   │                                    ▼
   │                         deidentify -> clean-data -> analyze-stats -> make-figures -> write-paper
   │                                                        │                                │
   │                                           replicate-study (paper → new DB)         humanize
   │                                           cross-national (parallel survey)              │
   │                                           batch-cohort (N × M matrix)                   ▼
   │                                                                          find-journal <── self-review
   │                                                                               │                    │
   │                                                                               │                    ▼
   │                                                                               │          humanize -> academic-aio (AI-search visibility)
   │                                                                               ▼
   │                                                    [cover-letter] -> check-reporting -> revise -> present-paper
   │                                                                                                       │
   └── meta-analysis                                                                                  peer-review
                         lit-sync (Zotero + Obsidian sync)     author-strategy (PubMed profile analysis)

                              ┌─────────────────────────────────────────────┐
                              │  publish-skill: package any skill above for │
                              │  open-source distribution (PII audit,       │
                              │  license check, generalization)             │
                              └─────────────────────────────────────────────┘
                              ┌─────────────────────────────────────────────┐
                              │  add-journal: add new journal profiles to   │
                              │  the database (write-paper + find-journal   │
                              │  dual profile generation with quality gates)│
                              └─────────────────────────────────────────────┘
```

### 按研究阶段

全部技能，按其在临床稿件与医学 AI 生命周期中的位置分组。完整说明见下表；每个技能的单独页面位于[逐技能参考](docs/skills/)。

|舞台|技能 |
|--------|--------|
| 🔭 **发现和范围** | `ma-scout` · `find-cohort-gap` · `search-lit` · `fulltext-retrieval` · `lit-sync` · `author-strategy` |
| 📐 **设计与规划** | `design-study` · `calc-sample-size` · `define-variables` · `write-protocol` · `fill-protocol` · `design-ai-benchmarking` |
| 🧹 **数据与分析** | `deidentify` · `clean-data` · `generate-codebook` · `version-dataset` · `analyze-stats` · `batch-cohort` · `cross-national` · `replicate-study` |
| 🤖 **医疗人工智能模型工程** | `profile-imaging` · `preprocess-imaging` · `architecture-zoo` · `model-scaffold` · `model-validation` · `model-evaluation` · `uncertainty-imaging` · `explainability` · `radiomics-ml` · `model-card` · `mllm-eval` |
| ✍️ **书写和可视化** | `write-paper` · `make-figures` · `review-paper` · `present-paper` · `humanize` · `polish-language` · `academic-aio` |
| ✅ **遵守并验证** | `check-reporting` · `self-review` · `verify-refs` · `manage-refs` |
| 📤 **提交并回复** | `find-journal` · `add-journal` · `sync-submission` · `revise` · `peer-review` · `fill-icmje-coi` |
| 🧭 **编排和管理** | `orchestrate` · `intake-project` · `manage-project` · `meta-analysis` · `grant-builder` · `publish-skill` · `render-pdf-doc` · `setup-medsci` |

### 现已上市

|技能|它有什么作用 |
|--------|-------------|
| **编排** |完整捆绑包的单一入口点。对您的请求进行分类并路由到正确的技能，或者链接多个技能以实现多步骤工作流程。全流水线模式端到端运行 `analyze-stats` → `make-figures` → `write-paper` → `check-reporting` → `self-review`。 `--e2e` 标志用于完全自主执行，具有后技能验证和故障停止功能。 |
| **查找队列差距** |纵向队列数据库的研究差距查找器。分析群组优势、匹配 PI 专业知识、通过 6 模式评分扫描文献饱和度，并通过比较表和单页器输出排名主题提案。适用于任何人群：NHIS、英国生物银行、机构 EMR、健康检查登记处。 |
| **搜索点燃** | PubMed + Semantic Sc​​holar + bioRxiv 搜索，具有抗幻觉引文验证。令牌高效的错误处理——CrossRef 失败会以静默方式进行批处理，不会重复。 BibTeX 输出用 `verified`/`verified_by`/`verified_on` 字段标记每个条目，以便下游技能可以信任引文来源。 |
| **验证参考** |针对 `.md`、`.docx`、`.bib` 或 `.tsv` 输入的提交前参考审核。提取参考文献，通过 CrossRef/PubMed 验证 DOI/PMID（如果可用），并将 `qc/reference_audit.json` 作为唯一输出写入 — 行级状态（OK / MISMATCH / UNVERIFIED / FABRICATED）位于 JSON `records[]` 块内。 `/search-lit` 产生候选 BibTeX； `/lit-sync`拥有`manuscript/_src/refs.bib`。 |
| **fulltext-retrieval** | Batch open-access PDF downloader. Unpaywall → PMC → OpenAlex → CrossRef pipeline. OA-only -- no paywall bypass. Input: DOI list or TSV. Optional PDF→Markdown conversion via [pymupdf4llm](https://pymupdf.readthedocs.io/en/latest/pymupdf4llm/) for token-efficient LLM analysis of academic papers. |
| **检查报告** |针对 47 种报告指南和偏见风险工具（STROBE、STROBE-MR、RECORD、GATHER、STARD、STARD-AI、TRIPOD、TRIPOD+AI、TRIPOD-LLM、PGS-RS、CHEERS 2022、CROSS、SRQR、COREQ、PRISMA、PRISMA-DTA、PRISMA-P、PRISMA-ScR、MOOSE、到达、CONSORT、CONSORT-AI、CARE、SPIRIT、SPIRIT-AI、CLAIM、DECIDE-AI、SQUIRE 2.0、CLEAR、GRRAS、MI-CLEAR-LLM、SWiM、AMSTAR 2、QUADAS-2、QUADAS-C、Rob 2、ROBINS-I、ROBINS-E、ROBIS、ROB-ME、PROBAST、 PROBAST+AI、NOS、COSMIN、Rob NMA）。机器可读的 JSON 摘要，带有用于自动管道集成的 `compliance_pct` 和 `fixable_by_ai` 标志。 |
| **分析统计** |用于诊断准确性的统计分析代码生成 (Python/R)、DTA 荟萃分析（双变量/HSROC）、评估者间一致性、生存分析、人口统计表、回归（逻辑/线性）、倾向评分（匹配/IPTW/重叠加权）和重复测量（RM ANOVA/GEE/混合模型）。预测模型必须进行校准。 |
| **荟萃分析** |完整的系统评价和荟萃分析流程（8 个阶段）。 DTA（双变量/HSROC）和干预荟萃分析。符合 PRISMA-DTA 要求的可提交手稿协议。 |
| **制作人物** |可供出版的图形和视觉摘要：ROC 曲线、森林图、PRISMA/CONSORT/STARD 流程图、Kaplan-Meier 曲线、Bland-Altman 图、混淆矩阵和期刊特定的视觉/图形摘要（基于 python-pptx 模板）。沟通优先的设计原则（Nat Hum Behav 2026 - 关键信息、受众、认知负荷、图与表决策）和五个流程图制作课程（官方模板保真度、VML 后备 PDF 导出、docx XML 转义、顺序占位符映射、版本冻结）；评论家标题 G 部分添加了 5 项沟通优先检查。 `--study-type`自动生成所需的全部图形集；结构化`_figure_manifest.md`输出用于下游管道消耗； D2 强制作为流程图的默认值。 |
| **设计研究** |研究设计审查：确定分析单位、队列逻辑、数据泄漏风险、比较器设计、验证策略和报告指南拟合度。 |
| **设计人工智能基准测试** |针对人类专家小组对人工智能系统进行基准测试的设计和有效性审查：评估问题和手臂定义、带有锚点的解耦多维规则、植入的校准探针（阳性控制/已知不良/不稳定/机制矛盾）、每个审阅者随机化的审阅者小组构建、具有单独控制项可靠性的评估者间可靠性目标、法学硕士作为法官与人类作为法官的裁决、构造独立性守卫和结构化 JSON 评级导出模式。在数据收集之前锁定标题。 |
| **模型验证** |设计或审核工程师构建的医学影像模型的临床验证研究（分割/分类/检测）：患者级别的分割不相交和数据泄漏分类、测试调整、内部与真实外部验证、比较器设计、单次运行与多种子方差、任务正确指标选择（指标重新加载）、测试集大小调整和 CLAIM 2024 / TRIPOD+AI / STARD-AI 报告适合。提供一个确定性的分裂泄漏门，通过在发出的分裂表上设置算术来证明患者的不相交性。与 MONAI / nnU-Net 集成 — 不会取代它们。 |
| **轮廓成像** |在做出任何建模决策之前对医学成像数据集进行概要分析（采集网格、体素间距和方向扩展、强度域、实际存在的标签值、前景分数和目标体积），然后根据声明的计划对该概要进行门控。虽然它仍然很便宜，但在训练运行后会出现其他情况：没有地面实况的“测试集”（`TEST_SET_UNLABELLED`）、与其图像不匹配的标签网格（`LABEL_SHAPE_MISMATCH`）、杂散标签索引（`LABEL_VALUE_UNEXPECTED`）、针对条子大小的目标规划的精度（`ACCURACY_UNDER_IMBALANCE`）以及没有声明重采样决策的采集异质性（`SPACING_HETEROGENEOUS`）。该门标记的是“未声明的”决定，而不是可变性本身。 |
| **预处理成像** |设计或审核医学成像模型的数据准备阶段（DICOM/NIfTI 摄入、重采样、强度标准化和增强计划），以便在 `model-scaffold` 构建训练存储库之前管道是安全的。发出声明性预处理清单和确定性数据阶段泄漏门 (`check_preprocessing_leakage`)，捕获分割表无法看到的内容：数据集级标准化器拟合非训练数据 (`NORMALIZATION_LEAKAGE`)、分割之前运行的数据拟合变换 (`PREPROCESS_BEFORE_SPLIT`) 以及跨越分割的患者切片 (`PATIENT_CROSS_SPLIT`)。集成 MONAI / TorchIO 转换；永远不会重新实现它们或接触真实的患者数据。 |
| **模型脚手架** |为医学成像任务生成可重复、可运行的 PyTorch 训练存储库 — 分割 (U-Net)、分类、检测、图像到图像合成、自监督预训练或微调预训练主干（迁移学习） — 选择架构和验证训练模型之间缺少的中间环节。发出患者级种子锁定分割作为可审核工件、适合任务的模型、训练/评估为每个 RNG 播种并在评估模式下进行推断的脚本、配置、要求、再现性记录以及带有 VERIFY 占位符的方法存根（无捏造数字）。微调模式 (`--task finetune`) 增加了冻结→解冻时间表、判别性学习率和预训练权重来源记录 (`PRETRAINED.md`)，以及 MedSAM 适应 + 仅训练扩散增强指南。通过构建保持再现性；提供 `check_training_hygiene` AST 门（RNG 播种、评估模式推理、仅训练分割加载器、预训练来源）+ 无网络构建→验证挑战。与 MONAI / nnU-Net / TorchIO / timm / torchvision 集成，用于生产级模型。 |
| **建筑动物园** | “哪个架构适合哪个研究问题”决策工具：将任务（分类/分割/检测/转移）、模式、数据规模和类别不平衡映射到基于论文的架构候选列表。策划基础课程（ResNet / DenseNet / EfficientNet / ViT / Swin；U-Net / 3-D U-Net / Attention & Residual U-Net / nnU-Net / Mask R-CNN；SAM/MedSAM / TotalSegmentator / BiomedCLIP / DINO / MAE / SimCLR）——每个课程都有核心思想、何时使用、医学成像使用、参考实现、验证设置和匹配模型支架模板。咨询;教授的是原型，而不是实时的 SOTA 排行榜。 |
| **模型卡** |生成工程师构建的医学成像模型必须携带的文档 - 模型卡（Mitchell 等人，2019 年）、其数据集的数据表（Gebru 等人，2021 年）和 METRIC 通知的数据质量通行证 - 由用户提供的事实（从未捏造）填充，然后使用确定性完整性门 (`check_model_card_complete`) 验证每个所需部分是否存在且非空。模型卡/数据表是作为模板提供的文档标准，不计入报告清单。 |
| **模型评估** |计算并报告训练有素的医学成像模型的任务正确保留指标 - 分割（Dice + 每个结构的边界指标 HD95/NSD）、分类（AUROC + AUPRC + 在部署流行情况下使用引导 CI 的敏感性/特异性）或检测（具有规定 IoU 标准的 FROC/mAP） - 加上校准和子组切片。发出每个案例的分析统计表，并根据 Metrics Reloaded / CLAIM 2024 (`check_metric_reporting`) 选择指标。数字仅来自执行的代码。 |
| **可解释性** |生成或审核医学成像模型的可解释性/可解释性分析 - Grad-CAM / Grad-CAM++ / 注意力滚动 / 显着性 / 集成梯度 - 因此它清除了严格性：强制性 Adebayo 健全性检查（模型和数据随机化）、针对地面事实的定量定位指标（IoU / 指点游戏 / 骰子）而不是目测示例、队列级别结果和归因框架而不是“证明模型是正确的”。发出可解释性报告清单+确定性门（`check_explainability_report`）：`SALIENCY_AS_VALIDATION`、`NO_SANITY_CHECK`、`NO_LOCALIZATION_METRIC`（主要）； `INSUFFICIENT_SANITY`、`CHERRY_PICKED_EXAMPLES`、`MISSING_METHOD`（次要）。集成captum/pytorch-grad-cam；永远不会重新实现它们或接触真实的患者数据。 |
| **放射组学-ml** |生成或审核放射组学/表格临床 ML 研究 — 特征 → 随机森林/XGBoost/正则化逻辑 → 临床结果 — 最常见的单独可行的临床 ML 工作流程（无 GPU，无工程师）。发出管道清单+确定性严格门（`check_radiomics_ml`）：`NO_NESTED_CV`、`HIGH_DIM_LOW_EVENTS`、`SELECTION_OUTSIDE_CV`（主要）； `NO_FEATURE_STABILITY`、`NO_CALIBRATION`、`NO_EXTERNAL_VALIDATION`（次要）。 Pyradiomics/IBSI 设置、带折叠选择的嵌套 CV、ICC 稳定性、SHAP、校准 + 决策曲线、CLEAR/TRIPOD+AI/PROBAST-AI 报告。集成 scikit-learn/xgboost/pyradiomics；从不重新实现它们。 |
| **不确定性成像** |设计或审核部署框架医学成像模型的不确定性/分布外/选择性预测层 - 因此临床使用声明包含校准的每个案例不确定性（MC-dropout/深度集成/保形/贝叶斯）、在保留的 OOD 集上验证的 OOD 防护、预先指定操作点的弃权规则以及在分布偏移下检查的校准。发出不确定性清单+确定性门（`check_uncertainty_reporting`）：`POINT_PREDICTION_NO_UNCERTAINTY`、`CONFORMAL_NO_COVERAGE_VALIDATION`、`OOD_NO_HELDOUT_SET`（主要）； `ENSEMBLE_NOT_INDEPENDENT`、`MCDROPOUT_DISABLED_AT_INFERENCE`、`SELECTIVE_NO_TARGET`、`NO_CALIBRATION_UNDER_SHIFT`（次要）。集成 MAPIE / captum / OOD 评分器；永远不会重新实现它们或接触真实的患者数据。 |
| **mllm-评估** |针对临床任务（放射学报告生成、VQA、临床文本提取）的 LLM/MLLM 的模型不可知评估工具（封闭 API 或开放权重），涵盖裁定的参考标准、临床疗效指标（超出 BLEU/ROUGE 的 RadGraph-F1 / CheXbert-F1）、忠实度/幻觉、训练前污染、提示敏感性和读者研究；使用 `check_mllm_eval_completeness` 控制计划并将审核者审核路由至 MLLM 探针。 |
| **摄入项目** |对新的研究项目进行分类，总结当前状态，识别缺失的输入，并建议后续步骤。 |
| **资助建设者** |结构拨款提案：重要性、创新、方法、里程碑和联盟角色。 |
| **当前论文** |学术演讲准备：论文分析、支持研究、演讲稿、幻灯片注释以及问答准备。 |
| **发布技能** |将个人 Claude Code 技能转换为可分发的开源就绪包。 PII 审核、许可证兼容性检查、概括和打包工作流程。 |
| **写论文** |完整的 IMRAD 稿件流程（8 个阶段）。概述可提交的手稿，包括评论家修正循环、人工智能模式避免和期刊合规性。结果中的反解释护栏；使用锚文件输入进行交互式讨论计划。病例报告模式（CARE 2016，1000字简写）。可选的求职信生成（第 8 阶段+）。 LLM 披露：自动生成方法、致谢和求职信中的披露声明（通过 `--no-llm-disclosure` 选择退出）。 `--autonomous` 标志跳过所有用户门以实现全自动原稿生成；第 2 阶段自动调用 `/make-figures --study-type` 并进行清单验证；第 7 阶段强制执行严格的顺序 QC 链（检查报告→搜索照明→自我审查修复循环→DOCX 构建）。 |
| **评论论文** |搭建并起草文献综述——叙述性 (SANRA)、范围界定 (PRISMA-ScR + JBI) 或系统性 (PRISMA 2020)。请求脊柱轴（模态/任务/生命周期），构建一个由 7 部分组成的骨架，其中包含所需的介绍范围/非重叠块、每个部分的摘要表存根和评估指标批判小部分，然后连接报告/注册并移交给 `/self-review` (RV1-RV8) → `/check-reporting` → `/verify-refs` → `/humanize`。从不发明引用。 |
| **自我审查** |从审稿人的角度进行提交前自我审查。 10 个具有研究类型分支的类别（人工智能、观察、教育、荟萃分析、病例报告、外科）。预期的主要/次要格式，具有严重性框架和 `/revise` 管道的可选 R0 编号。 `--json` 结构化输出，带 `fixable_by_ai` 标志； `--fix` 模式自动应用文本修复（最多 2 次迭代）。 |
| **修改** |回复审阅者并跟踪更改。解析决策信，将评论分类为主要/次要/反驳，生成逐点回复和求职信。 |
| **同步提交** | SSOT 到提交偏差审核和期刊包帮助程序。将 `submission/{journal}/` 视为派生输出，在 `.journal_meta.json` 中记录源哈希值，并阻止冻结漂移的包。 |
| **管理项目** |研究项目脚手架和进度跟踪。命令：init、status、sync-memory、checklist、timeline。向后提交时间表和预提交清单。 `init --zotero-collection NAME` 通过 pyzotero 自动创建 Zotero 集合，并将 `library_id`/`collection_key` 连接到项目合同中。 |
| **计算样本大小** |具有决策树引导测试选择的交互式样本量计算器。涵盖 11 种设计（诊断准确性、t 检验、ANOVA、卡方、McNemar、逻辑回归、Cox 回归 EPV、生存、ICC、kappa、非劣效性/等效性）。生成可重现的 R/Python 代码和 IRB 就绪的理由文本。 |
| **查找期刊** |期刊推荐引擎。 2 遍匹配：用于评分的紧凑配置文件、用于前 5 名丰富的写纸配置文件。涵盖 30 多个医学专业，并具有用于个人使用配置文件的用户本地私有层。没有缓存的 IF/APC——您可以验证期刊网站上的当前指标。拒绝后重新定位模式。 |
| **添加日记** |将新的期刊概况添加到数据库中。从作者指南中提取元数据，以规范格式和质量门生成撰写论文（详细）和查找期刊（紧凑）配置文件。用于在一个会话中添加多个期刊的批处理模式。 |
| **去识别化** |在法学硕士辅助分析之前对临床研究数据进行去标识化。独立的 Python CLI（无法学硕士），带有 10 个国家/地区语言环境包（韩、美、日、中、德、英国、法国、加拿大、澳大利亚、中）。通过正则表达式 + 启发式检测 PHI。交互式终端审查、假名化、日期移动、映射文件生成。通过 `--locale-file` 的自定义区域设置支持。 |
| **干净数据** |交互式数据分析和清理助手。三阶段工作流程：分析您的 CSV/Excel 数据，标记问题（缺失值、异常值、重复、类型不匹配），然后仅为批准的操作生成清理代码。内置 PHI/PII 安全警告。 |
| **写协议** | IRB/道德协议生成器。生成 4 个核心部分（背景、研究设计、样本量论证、统计计划）以及完整的散文。其余 6 个部分作为结构化骨架提供，并带有针对机构特定内容的 TODO 标记。韩国/美国/欧盟监管指导。 |
| **重复研究** |在不同的数据库上复制现有的队列研究。从源论文中提取方法，通过协调表映射变量，生成分析代码，并生成复制差异报告。经 KNHANES/NHANES 跨国复制验证。 |
| **跨国** |端到端跨国比较研究。变量协调、平行加权调查分析（无数据合并）和国家分层比较表。内置 KNHANES + NHANES 编码参考。 |
| **批次队列** |从一个经过验证的模板 × 多种曝光/结果组合生成 N 个分析脚本。 “80人团队”模式：方法相同，只是交换变量。自我调整预防、EPV 检查、Bonferroni 校正和汇总热图。在 KNHANES 2018 上通过 18 种组合进行验证。
| **人性化** |检测并删除学术手稿中的人工智能写作模式。扫描 18 种常见模式（重要性膨胀、AI 词汇、系词回避等）并重写标记的段落，同时保持技术准确性。密度目标：每 1000 个单词 <2.0 个实例。 |
| **作者策略** | PubMed 作者概况分析。通过电子实用程序获取出版物数据，对研究类型（GBD、SR/MA、NHIS、AI/ML 等）进行分类，生成 7 个可视化效果，并生成具有复制机会的策略报告。 |
| **同行评审** |医学期刊的结构化同行评审起草。系统的稿件分析、期刊特定格式（RYAI、INSI、EURE、AJR、KJR）、简洁性目标（500-800 字）和提交前质量控制检查表。建设性的发展基调。 |
| **马侦察兵** |荟萃分析主题发现和可行性评估。两种模式：（A）教授优先——简介→支柱分析→MA差距，（B）主题优先——问题→景观扫描→合著者匹配。多源验证（PubMed、PROSPERO、bioRxiv），具有实际的 k 估计（15-30% 折扣）。 |
| **点亮同步** |将 .bib 文件中的研究参考文献同步到 Zotero 库 + Obsidian 文献笔记。从 10 多个文献笔记中提取概念并发现跨领域的主题。可在 `/search-lit` 后工作或独立工作。 |
| **学术-aio** | AI 搜索引擎（Perplexity / ChatGPT web / Elicit / Consensus / SciSpace）和医学 AI 论文的 RAG 可见性清单。将 TRIPOD+AI、CLAIM、STARD-AI、TRIPOD-LLM、DECIDE-AI 报告锚点与生成引擎优化 (GEO) 原则相集成。涵盖标题、摘要、结构化摘要框（要点/上下文研究/简单语言摘要）、预印本、GitHub README、`CITATION.cff`、Zenodo 和 Hugging Face 模型/数据集卡。明确防御法学硕士引文捏造（Agarwal 2025，Nat Commun）。生成可见的通过/部分/失败检查表；永远不会默默地应用编辑。与 `write-paper` 第 4/6/7 相配对，在 `self-review` + `humanize` 之后运行。 |
| **波兰语** |学术英语一致性检查和非母语 (ESL) 清晰度润色。确定性 linter (`lint_consistency.py`) 标记缩写定义一次违规、美国/英国拼写漂移、连字符与破折号数字范围、`P`/`p` 大小写和不可能的 `P = 0.000`、连字符变体、小数字样式和值/单位间距 - 然后，门控、仅样式清晰传递修复措辞而无需更改数字、引文或科学意义。与`humanize`（AI-tell清除）和`check-reporting`（指导项目）不同；捆绑一张可复制的挑战卡。 |
| **管理参考** |参考生命周期作为单一技能：citekey ↔ `.bib` 验证、期刊-CSL pandoc 渲染 (`render_pandoc.sh`)、手稿 ↔ 渲染的 DOCX 交叉引用 QC（`check_xref.py --strict` 是提交门）、`[N]` ↔ `[@key]` 标记转换以及合著者 Word 的本机 Zotero CWYW 字段代码注入工作流程。混合 3 阶段策略（pandoc 草案 → CWYW 过渡 → Zotero CWYW 进行流通/修订/提交）。独家编写`manuscript_final.docx`和`qc/xref_audit.json`。从 `write-paper` Phase 7.6 中分离出来，因此 `revise`、`peer-review`、`sync-submission` 和 `find-journal` 可以直接渲染，而无需依赖同级技能。 |
| **渲染 pdf-doc** |通过 `pandoc + xelatex` 将非书目学术降价（提案、简报讲义、锚文档、IRB 封面、参考表）渲染为出版质量的 PDF，并使用 CJK 字体回退（macOS 上的 Apple SD Gothic Neo，Linux 上的 Noto Sans CJK KR）和内容比例的管道表列宽。与 `manage-refs`（参考书目驱动）相反的边界。从 `write-paper` 7.6 期中分离出来。 |
| **定义变量** |用于观察研究的基于文献的变量操作化。将数据字典和研究问题转化为引用支持的暴露/结果/协变量定义、截止值和数据库变量映射表。第 0 层字典优先规则可防止导致审稿人拒绝的临时表型定义。将 `/search-lit` 输出桥接至 `/write-protocol` 方法。 |
| **生成密码本** |从表格数据集 (CSV/TSV/Excel/Parquet/Stata/SAS) 生成可引用的数据字典/密码本。将每个变量（角色、类型、级别频率、范围/分位数、缺失）分析到 `codebook.md` + `codebook.json` 中。将级别含义未知的编码变量标记为 `[NEEDS DICTIONARY]`，而不是猜测它们，为 `/define-variables` 和字典优先工作流程提供支持。 |
| **版本数据集** |数据集版本控制以实现可重复性。构建确定性内容哈希清单（文件 SHA-256 + 表格架构 + 每列值哈希），验证后续副本以检测偏差（架构/行计数/值更改），并比较两个清单。锁定“结果来自哪个版本的数据”；还可以重现性锁定捆绑的演示。 |
| **填充协议** |填写 IRB 协议、伦理申请、资助提案和其他结构化研究文档的机构 Word 表单模板 (`.doc` / `.docx`)，同时保留原始样式、表格布局、字体和页面几何形状。韩语感知（CJK eastAsia 字体强制，表格 cantSplit），但适用于任何语言模板。与 `write-protocol`（内容）配对 — fill-protocol 将内容呈现到机构模板中。 |
| **填充-icmje-coi** |批量生成每位作者 ICMJE 利益冲突披露表 (`coi_disclosure.docx`)，用于稿件提交。将所有 13 个披露项目预先填写为“☒无”，加上使用合成种子模板的最终认证，然后克隆每个作者的种子，并替换日期/姓名/稿件标题。专为医院观察研究的常见情况而设计，其中作者没有真正的财务冲突；对于大多数作者来说，传阅的表格变成“回复변경 없음 + 符号”，并且只标记那些需要修改的人。 |
| **设置-medsci** | MedSci Skills 运行时的诊断清单。验证 Python、R、Node、代理主机、Git、Zotero 和配置的 MCP 服务器，然后打印通过/失败表，其中包含指向任何缺失组件的正确设置文档的链接。只读 — 不安装任何内容。 |

## 安装

> **没有终端？** 使用教室安装程序 ZIP。下载、解压缩、双击安装程序，然后重新启动桌面代理应用程序。

### 选项 1：课堂安装程序（推荐非程序员使用）

视窗：

```text
https://github.com/Aperivue/medsci-skills/releases/latest/download/medsci-skills-classroom-windows.zip
```

苹果系统：

```text
https://github.com/Aperivue/medsci-skills/releases/latest/download/medsci-skills-classroom-macos.zip
```

解压后：

- Windows：双击`installers/install-windows.cmd`
- macOS：双击`installers/install-macos.command`

This turnkey install also **turns on in-app update reminders** and adds an **"Update MedSci Skills"** Desktop icon, so you are told when a new version ships and can update with one click — no terminal needed (see [Updating](#updating)).

然后重新启动 Claude Code Desktop、Codex Desktop 或 Cursor 并使用以下命令进行测试：

```text
MedSci Skills가 설치됐는지 확인하고, 오늘 실습에 쓸 대표 스킬 5개만 보여줘.
```

### 选项 2：手动安装所有技能

```bash
git clone https://github.com/Aperivue/medsci-skills.git
mkdir -p ~/.claude/skills
cp -r medsci-skills/skills/* ~/.claude/skills/
```

### 选项 3：手动安装个人技能

```bash
git clone https://github.com/Aperivue/medsci-skills.git
mkdir -p ~/.claude/skills
cp -r medsci-skills/skills/check-reporting ~/.claude/skills/
```

### 选项 4：npm / npx（终端友好的快捷方式）

终端用户的便捷包装器 - 它通过以下方式复制相同的技能
无依赖的 Python 安装程序。规范安装路径仍然是插件
Marketplace（上面选项 1 的同级）和上面的 git 克隆； npm 只是一个快捷方式。

```bash
npx medsci-skills install            # all hosts (Claude, Codex, Cursor)
npx medsci-skills install --target claude
npx medsci-skills list               # list bundled skills
npx medsci-skills doctor             # quick Node/Python/skill-folder check
```

需要 PATH 上的节点 18+ 和（对于 `install`/`doctor`）`python3`。

### 选项 5：GitHub CLI (`gh skill`)

If you use [GitHub CLI](https://cli.github.com/) ≥ 2.90, `gh skill` installs skills from any Agent-Skills repo — this one included — without cloning. It is a `gh` **preview** feature, so the exact flags may change.

```bash
gh skill search medsci                                   # list every MedSci skill
gh skill preview Aperivue/medsci-skills check-reporting  # inspect one first
gh skill install Aperivue/medsci-skills check-reporting  # install a single skill
gh skill install --all Aperivue/medsci-skills            # or install all of them
```

`gh skill install` 将技能放置在您使用 `--agent` 选择的代理的主机特定文件夹中（`claude-code` → `~/.claude/skills/`、`codex` → `~/.agents/skills/` 等）、用户或项目 `--scope` — 与上面的 npx 和 git 路径填充的文件夹相同。通过技能的确切名称或 `medsci` 进行发现效果最佳；对于广泛的主题词，范围为 `--owner Aperivue`。

### 平台说明

- Claude Code：技能复制到 `~/.claude/skills/`（也可通过 GitHub Copilot 和 Cursor 读取）。
- Codex：技能被复制到 `~/.agents/skills/`（也可以由 Cursor 和 GitHub Copilot 读取）。
- 光标：无需单独的步骤 - 光标直接读取 `~/.claude/skills/` 和 `~/.agents/skills/`。安装人员仍然可以使用 `--cursor-project` 编写可选的 `.cursor/rules/` 转向规则。
- See [`docs/host_compatibility.md`](docs/host_compatibility.md) for the verified per-host install paths and their official sources.
- Windows 用户不需要 WSL 来执行基本的课堂工作流程。仅将 WSL 用于高级可复制 Linux 工具链。

See [docs/classroom_distribution_plan.md](docs/classroom_distribution_plan.md) and [docs/classroom_materials.md](docs/classroom_materials.md) for instructor distribution, email templates, and first-class exercises.

> **提示：** 不确定使用哪个技能？从 `/orchestrate` 开始——它将对您的请求进行分类，并将您引导至正确的工具。

## 更新中

MedSci 技能经常更新。您**不需要**需要 GitHub、git 或命令行来保持最新状态。

- **一键点击（建议用于课堂安装）。** 现在课堂安装程序（选项 1）
  自动为您设置 — 它在 `~/.medsci-skills/updater/` 放置一个更新程序，删除一个
  **桌面上的“更新 MedSci 技能”** 图标 (`--desktop-launcher`)，并且 ** 打开应用程序内
  更新提醒**（如下）。双击图标：它会从 GitHub 下载最新版本，
  验证它，并以事务方式重新安装，因此中断的更新永远不会破坏您的安装。
- **已经安装了旧版本？** 重新下载最新的教室 ZIP **一次**并双击
  安装人员；从那时起，一键更新程序将适用于未来的每次更新。
- **终端用户：** `npx medsci-skills@latest install` 始终安装最新版本。
- **仅检查：** `python3 installers/install.py --check-update` 报告是否有更新版本
  可用且未安装任何内容。
- **获得提醒（克劳德代码）：** `python3 installers/install.py --enable-update-notify`（或
  `npx medsci-skills install --enable-update-notify`) 显示一行 *“更新可用”* 通知
  当克劳德代码会话开始时。 **教室安装程序可以为您实现此目的；**对于
  `npx`/手动路径**默认情况下**关闭**（安装程序打印如何打开它）。它检查在
  大多数情况下每天一次，不会读取任何有关您的会话的信息，也不会安装任何东西。将其关闭
  `--disable-update-notify`，或使用 `MEDSCI_NO_UPDATE_CHECK=1` 使其静音。
- **Claude Code 插件市场：** 第三方市场 **自动更新默认关闭** —
  在 Claude Code 中启用它或运行手动插件更新。

更新仅连接到 GitHub，不发送有关您的计算机或工作的信息，并且不创建
遥测或跟踪。修改后的技能会在更新前进行备份，并且不会自动删除。参见
the [update privacy & data notice](docs/update_privacy.md).

## 主要特点

### 自主端到端管道

`orchestrate --e2e` 或 `write-paper --autonomous` 运行从数据到可提交的 DOCX 的完整管道，并具有有限验证。技能通过结构化清单（`_analysis_outputs.md`、`_figure_manifest.md`）和项目工件（`project.yaml`、`artifact_manifest.json`、`qc/status.json`）传递输出。如果一项技能未能产生预期输出，管道将停止，而不是继续处理丢失的数据。第 7 阶段实施严格的 QC 链：AI 模式删除 → 报告合规性检查 → `/verify-refs` 引文审计 → 数字声明审计 → 带自动修复的自我审查（最多 2 次迭代）→ DOCX/提交构建。

### 反幻觉引文
`search-lit` 生成的每个参考文献都经过 PubMed、Semantic Scholar 或 CrossRef API 的验证。然后，现有的手稿应该运行 `/verify-refs`，它会在提交之前编写可见的参考文献审核并阻止伪造的参考文献。任何引文都不是仅凭记忆生成的。 API 错误以静默方式进行批处理——不会因重复的失败消息而浪费令牌。

### 抗幻觉数字声明

`/meta-analysis` 6b 相、`/self-review` 2.5a 相、`/revise` 步骤 2.5 和 `/write-paper`
步骤 7.3a 强制执行常见的 3 层审核（CSV ↔ 分析脚本 ↔ 手稿），主要包括：
对汇总估计值和修订时代数字进行源回溯检查。手写数字
没有 CSV 坐标注释的矩阵被标记为结构风险，即使值
目前是正确的，因为下一个版本将重新引入相同的故障模式。

### 参考安全（第一阶段）
项目在 `SSOT.yaml` 中声明其真实来源布局，并且 `qc/migration_complete` 标记门严格执行。 `/verify-refs`是`qc/reference_audit.json`的独家编写者。 `MEDSCI_VERIFY_REFS_MODE` 环境变量（`auto` 默认值、`warn`、`enforce`、`off`）控制行为 - 仅当 SSOT.yaml 和迁移标记都存在时，`auto` 才会阻塞，否则会发出警告。遗留项目冻结为仅警告；新项目选择通过 `scripts/migrate_project_to_ssot.py` 加入。对于在 `~/.claude/hooks/verify-refs-guard.sh` 本地安装它的用户来说，可选的 PostToolUse 挂钩（未在此存储库中提供 - 仅文档）可以在手稿保存时自动调用 `/verify-refs`；仅当本地挂钩存在时，回归套件 (`tests/test_phase1c_hooks.sh`) 才会端到端运行，否则会被跳过。挂钩门在 `*/submission/*/manuscript/*.{docx,md}` 和 `*/revision/R*/…circulation….docx`（强制执行资格）下进行保存，并且（为第 14 期添加）还对之前完全跳过审核的预提交和导师流通草稿进行“仅警告”：`*/outgoing/*.{docx,md}`、`*/8_Review_Comments/*/outgoing/*.{docx,md}` 和任何 `*/circulation/*.{docx,md}`。仅警告模式会显示缺失的审核，而不会阻止快速迭代，并且无论 SSOT/迁移状态如何，都不会强制执行。

### 元分析失效模式
`/meta-analysis` 通过四个自动化挂钩提供经验故障模式参考（数据完整性、审核编排、提交包漂移、提交后发布操作）：`scripts/prisma_5way_consistency.py`（DI-6 PRISMA 编号一致性）、`scripts/extraction_consensus_log_init.py`（DI-1 双提取支架）、`scripts/tag_cleanup_gate.sh`（DI-8 占位符标签门）和 `scripts/verify_package_integrity.py`（SPD）提交包的 SHA-256 清单）。

### 47 报告指南和内置 RoB 工具
`check-reporting` 包括 47 种指南和偏差风险工具的捆绑清单：STROBE、STROBE-MR、RECORD、GATHER、STARD、STARD-AI、TRIPOD、TRIPOD+AI、TRIPOD-LLM、PGS-RS、CHEERS 2022、CROSS、SRQR、COREQ、PRISMA 2020、PRISMA-DTA、 PRISMA-P、PRISMA-ScR、MOOSE、ARRIVE、CONSORT、CONSORT-AI、CARE、SPIRIT、SPIRIT-AI、CLAIM、DECIDE-AI、SQUIRE 2.0、CLEAR、GRRAS、MI-CLEAR-LLM、SWiM、AMSTAR 2、QUADAS-2、QUADAS-C、Rob 2、ROBINS-I、ROBINS-E、 ROBIS、ROB-ME、PROBAST、PROBAST+AI、NOS、COSMIN、Rob NMA。包括结果/讨论部分边界检查和用于管道集成的机器可读 JSON 摘要。

### 可供出版的输出
`analyze-stats` 为 13 种分析类型（包括回归、倾向评分和重复测量）生成可重复的 Python/R 代码，并对预测模型进行强制校准。 `make-figures` 生成期刊规格的图形（300 DPI、色盲安全调色板、适当的尺寸）、视觉/图形摘要和工具选择指南（D2 用于流程图，matplotlib 用于数据图）。 `--study-type` 自动生成每个研究设计的完整图形集。

### 结果/讨论边界执行
`write-paper` 强制执行严格的分离：结果仅包含事实发现（没有解释，没有“为什么”），讨论使用交互式锚纸脚手架。批评者标题包括一个专用的部分边界通过/失败门。

### 在一个管道中提交的 IRB 协议
`design-study` -> `calc-sample-size` -> `write-protocol` 为您提供 IRB 就绪协议。数据收集后：`clean-data` -> `analyze-stats` -> `write-paper` -> `self-review` -> `find-journal` -> 求职信。每次转变都是一次明确的技能交接。

### 技能协同工作
技能互相调用。 `check-reporting` 为 PRISMA 图调用 `make-figures`。 `write-paper`调用`search-lit`进行引用验证。 `self-review` 委托向 `check-reporting` 报告合规性。 `calc-sample-size` 输出直接馈入 `write-protocol` 的 IRB 调整部分。

### 技能边界 - 使用哪些以及按什么顺序
技能集是故意“专门化的，而不是统一的”——每个技能都拥有一个独特的工件或生命周期步骤，因此路由保持精确。容易混淆的界限：

- **参考管道** — `search-lit`（发现候选者）→ `lit-sync`（`refs.bib` 的唯一编写者，同步 Zotero/Obsidian）→ `manage-refs`（渲染 CSL / 注入 CWYW / 交叉引用 QC，渲染的 DOCX 的唯一编写者）→ `verify-refs`（只读审核；从不编辑） `refs.bib`）。它们是一个管道，而不是四个重叠的工具。
- **语言通行证按顺序运行** — `humanize`（删除 AI 写作提示）→ `polish-language`（确定性 ESL/house 风格一致性：缩写、拼写、破折号、p 值大小写）→ `academic-aio`（AI 搜索/GEO 可见性）。具有不重叠作业的三个连续通道。
- **稿件类型选择技能** — `write-paper`（原创/IMRAD 文章、案例报告、MA）与 `review-paper`（叙述/范围界定/系统文献综述）与 `revise`（审稿人回复 + 跟踪更改）。不同的结构和报告准则。
- **作者与外部审稿人** — `self-review` 是您自己的提交前检查（预期评论）； `peer-review` 作为外部审稿人起草面向期刊的审稿。相同的域探测，不同的用户和输出。
- **项目条目** — `intake-project` 对*新的或混乱的文件夹*进行分类和搭建； `orchestrate` 确定*目标或任务*（“帮我写一篇论文”）。当您有文件但没有结构时从 `intake-project` 开始，当您有任务但没有计划时从 `orchestrate` 开始。
- **研究设计** — `design-study` 涵盖一般有效性（分析单元、泄漏、比较器、验证）**并且**带有用于感知/观察者/阅读器/视觉图灵测试/图像来源研究的设计阶段天花板门； `design-ai-benchmarking` 专门从事人工智能与人类专家评估（评分标准、校准探针、法学硕士作为法官）。
- **内容与模板** — `write-protocol` 起草 IRB/道德科学内容； `fill-protocol` 将该内容呈现为机构 Word 模板，而不会破坏其格式。

### 验证状态 — 可用 vs CI 门控 vs 评估
请准确理解“已验证”在这里的含义 - 这三个层次是不同的事实：
- **Available** — every bundled skill and deterministic detector. The current totals are the single source of truth in [`metadata/catalog_counts.json`](metadata/catalog_counts.json) and [`MEDSCI_AUDIT.md`](MEDSCI_AUDIT.md).
- **CI-gated** — detectors with a committed challenge/regression test that runs on every push via [`validate.yml`](.github/workflows/validate.yml).
- **Formally evaluated** — the subset measured by the canonical evaluation harness **E1** in [`evaluation/`](evaluation/), which is v3.8-era and validates the then-current detector subset; detectors added since are **CI-tested, not yet E1-evaluated** (the size of the catalog and the size of the evaluated subset are deliberately reported as separate facts — see `MEDSCI_AUDIT.md`).

该工具包*旨在减少常见的稿件准备错误*；它**不**保证正确性，并且**未**经过临床验证。

## 设置

**New to Python, R, or the command line?** The full step-by-step guide for clinicians is in [`docs/setup/`](docs/setup/README.md):

- [Mac 安装](docs/setup/mac.md) — Homebrew → Python 3.11 → R → Node → Claude Code（约 30 分钟）
- [Windows 安装](docs/setup/windows.md) — 基于 winget，无需 WSL
- [MCP 服务器配置](docs/setup/mcp-setup.md) — Zotero、Google Drive、PubMed 集成
- [常见问题](docs/setup/common-issues.md) — 十大修复（PATH、Apple Silicon、杀毒软件、JSON 语法）

**使用诊断技能验证您的环境**（只读，不安装任何内容）：
```
/setup-medsci
```
打印一份清单，显示哪些组件存在、哪些组件缺失，以及针对任何差距应遵循哪个文档。

## 要求

**Python 3.9+ 和代理主机。这就是整个硬性要求。** 每个完整性检测器都是
仅限 stdlib，起草、审阅和审核手稿也是如此。如果你没有Python，
双击安装程序将提示为您安装（Windows 上的 `winget`，或官方
下载页面）而不是让您陷入死胡同。

- An [Agent Skills](https://agentskills.io)-compatible host — [Claude Code](https://claude.ai/code) (primary), or Codex / Cursor / GitHub Copilot (see [`docs/host_compatibility.md`](docs/host_compatibility.md); some live-data workflows rely on Claude MCP servers)
- Python 3.9+ — 该底线是 CI 强制执行的 (`scripts/check_python_floor.py`)。越新越好；如果您今天要安装 Python，请安装最新版本。

其他一切都是“某些”技能所需要的，而其他技能则不需要。而不是包裹的购物清单
您从未听说过，请询问工具包**这**计算机可以做什么：

```bash
python3 installers/doctor.py          # what works, what does not, and the exact fix for each
python3 installers/doctor.py --fix    # offers to install what is missing — asking before each one
```
（或双击 `installers/check-setup-macos.command` / `installers/check-setup-windows.cmd`。）

它以您试图*做*的方式进行报告——“将您的手稿变成期刊格式的期刊”
Word文件”需要**pandoc**； “阅读并质量控制提交 PDF”需要 **poppler**； “完全打开 .docx”
需要 **python-docx** — 并根据要求安装小东西。大型事物（TeX 发行版，
R、PyTorch）永远不会为您安装：它会打印大小和命令并留下选择
独自一人。

**R 不是必需的。** `/analyze-stats` 默认编写 Python，并且仅在您要求时才发出 R；
工具包本身从不执行 R。安装 R（使用 `meta`、`metafor`、`mada` 进行荟萃分析）
仅当您想运行它为您编写的 R 代码时。 PyTorch 也是如此
`/model-scaffold`：不需要编写训练代码；运行它需要火炬。

## 用例

**“我有数据，想要一份零手动步骤的完整手稿。”**
```
/orchestrate --e2e      # Autonomous: analyze → figures → write → QC → DOCX
```
或者等效地：`/write-paper --autonomous`（如果分析和数据已存在）。

**“我有一份诊断准确性研究草案，需要检查合规性。”**
```
/design-study          # Review study design for leakage and bias
/analyze-stats         # Generate DTA statistics (sensitivity, specificity, AUC with CIs)
/make-figures          # Create ROC curve + STARD flow diagram
/check-reporting       # Audit against STARD checklist
```

**“我正在开始一项荟萃分析，需要找到相关研究。”**
```
/search-lit            # Systematic search across PubMed + Semantic Scholar
/fulltext-retrieval    # Batch download open-access PDFs for included studies
/meta-analysis         # Full DTA or intervention MA pipeline
/make-figures          # Forest plot + PRISMA flow diagram
/check-reporting       # Audit against PRISMA-DTA checklist
```

**“我需要在期刊俱乐部发表一篇论文。”**
```
/present-paper         # Analyze paper, find supporting refs, draft speaker script
```

**“我需要提交一项新研究的 IRB 方案。”**
```
/search-lit            # Background literature for rationale
/design-study          # Validate study design, identify bias risks
/calc-sample-size      # Power analysis with IRB justification text
/write-protocol        # Generate 4 core sections + 6 skeleton sections
```

**“我有一个有趣的案例要发表。”**
```
/write-paper           # Case report mode (CARE 2016, 1000-word short-form)
/self-review           # Pre-submission self-check
/find-journal          # Which journal accepts case reports in this field?
```

**“我的论文被拒绝了。我还应该向哪里提交？”**
```
/find-journal          # Exclude rejected journal, recommend alternatives
/write-paper           # Generate new cover letter (Phase 8+)
```

**“我有凌乱的临床数据，需要在分析之前进行清理。”**
```
/deidentify            # Remove PHI from clinical data (standalone Python, no LLM)
/clean-data            # Profile dataset, flag issues, generate cleaning code
/analyze-stats         # Run statistics on cleaned data
/make-figures          # Publication-ready figures
```

**“我想为放射学人工智能项目写一份资助提案。”**
```
/design-study          # Validate study design before writing
/grant-builder         # Structure significance, innovation, approach
/search-lit            # Find supporting literature with verified citations
```

## 贡献

**如果您已经在自己的机器上更改了某些内容，`/contribute` 将为您发送。**
大多数使用它的人是临床医生，而不是 git 用户：他们添加他们发表的期刊，修复
检查清单中的项目不适合他们的专业，调整一项技能以适应他们的部门——以及
更改死在一台笔记本电脑上。

```
/contribute
```

它将您安装的技能与交付的技能进行比较，准确地告诉您您更改了什么，
**扫描患者数据、医院名称、IRB 编号和稿件 ID**（扫描块，并
这就是为什么这是一项技能而不是按钮），向您显示将离开您的每一行
机器，然后才打开拉取请求 - 你永远不会输入 git 命令。没有 GitHub CLI？它
相反，作为一个问题到达项目。

相同的技能会导致**误报**（“这标记了我的论文，它是错误的”）或失败
步骤。这并不是一个较小的贡献：这是任何人拥有的关于探测器如何工作的唯一证据
表现在真实的手稿上，而不是合成的固定装置上。

**您不会被打扰。** 提醒默认关闭；安装程序提到该选项一次
然后再也不会了。 `/contribute` 仅在您运行时才会运行。

---

也欢迎以普通方式做出贡献 - 大多数都是**一个独立的小文件**
模板将引导您完成。您无需了解整个管道即可增加价值。
Pick a [**good first issue**](https://github.com/Aperivue/medsci-skills/contribute), or start
来自其中之一：

|想要添加... |如何|问题 |
|---|---|---|
| 为尚未收录的期刊添加 **CSL 引文样式** | 将一个 `.csl` 放入 `manage-refs/citation_styles/` | [#117](https://github.com/Aperivue/medsci-skills/issues/117) |
| 为另一个国家添加 **去标识化语言包** | 在 `deidentify/` 下新增一个模式文件 | [#116](https://github.com/Aperivue/medsci-skills/issues/116) |
| 添加 **README 翻译**（如 zh-CN） | 一个翻译后的 `README` 文件 | [#119](https://github.com/Aperivue/medsci-skills/issues/119) |
| **A figure exemplar** (ROC, KM, forest, Bland–Altman, confusion matrix…) | one `make-figures/references/exemplar_plots/*.md` anatomy model | [#118](https://github.com/Aperivue/medsci-skills/issues/118) |
| **A journal profile** (submission rules for a journal we don't cover) | `/add-journal`, or copy an existing `journal_profiles/*.md` | [#115](https://github.com/Aperivue/medsci-skills/issues/115) |
| 添加 **报告清单或同行评议范例** | 在对应技能中新增一个参考文件 | [#120](https://github.com/Aperivue/medsci-skills/issues/120) |

其中每一个都添加**恰好一个新文件** - 不需要编辑计数、生成的文件
页面，或构建配置，以及目录一致性检查自动派生配置文件计数
磁盘，这样它就不会标记你。 **无需作业：只需打开一个 PR - 第一个通过的 PR
CI 获胜，维护者负责审核中的所有簿记工作。** 请参阅
[5-minute first-PR quickstart](CONTRIBUTING.md#quickstart-your-first-pr-5-minutes) to get going.

每个贡献都以与维护者相同的方式进行控制：它必须是一个独立的
文件，通过 CI（`validate.yml` — PII 扫描、结构、目录一致性），并且不携带
patient or author identifiers. See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the PR checklist
以及 PII/出版物卫生规则。不适合模板的新想法？打开一个
[skill request](https://github.com/Aperivue/medsci-skills/issues/new?template=skill_request.yml)
or a [detector request](https://github.com/Aperivue/medsci-skills/issues/new?template=detector_request.yml).

**Governance:** [`ROADMAP.md`](ROADMAP.md) (priorities + scope boundary),
[`MAINTAINERS.md`](MAINTAINERS.md) (roles — clinical authority stays with the founder),
[`docs/maintainer_workflow.md`](docs/maintainer_workflow.md) (review + release process),
and [`SECURITY.md`](SECURITY.md) (vulnerability reporting + the medical-scope boundary).
涉及医疗/研究声明的变更需要临床主管审查。
报告、验证或塑造该项目的社区成员将被记入
[`CONTRIBUTORS.md`](CONTRIBUTORS.md).

## 在野外

### 文献中引用

**Chen, Wang & Qu (2026), *Recursive Self-Improvement in AI*** — [arXiv:2607.07663](https://arxiv.org/abs/2607.07663), a
对 **1,250 篇论文的调查** — 引用了该项目的方法论文
([arXiv:2606.09500](https://arxiv.org/abs/2606.09500)) twice, as the reference for what fails when an AI
审核其自己的科学成果，并将此处采取的方法命名为响应：

> “在受监管的领域，**插入了确定性完整性门**，因为‘自我批评’
> 继承了产生自信制造的盲点。”
> - §6.3（引用方法论文；也在§5.3中引用，关于自我确认循环）

这就是该存储库构建的论点：要求检查其自身工作的模型继承了
产生错误的盲点，而**重新计算**数字的脚本则不会。

Every citation we know of is logged in [`docs/citations.md`](docs/citations.md).

### 收养

Adoption is tracked openly in [`IMPACT.md`](IMPACT.md) (stars, forks, traffic,
release downloads — snapshotted weekly into [`metrics/traffic_log.csv`](metrics/traffic_log.csv))
and academic use is logged in [`docs/citations.md`](docs/citations.md).

**在您的研究中使用了医学科学技能？** 请
[let us know](https://github.com/Aperivue/medsci-skills/issues/new?template=used-in-research.yml).
它可以帮助其他研究人员找到该工具包 - 我们将其列出（经过您的许可）。

## 引文

如果 MedSci Skills 帮助您制作了手稿、方案或分析，请引用它 —
软件引用是这样的工具获得学术认可的方式，而且只需要一行字。

**在您的手稿中**（方法或致谢 - 引用您实际使用的版本）：

> 报告准则合规性、参考资料验证和提交前完整性检查
> were assisted by MedSci Skills (version X.Y.Z; https://github.com/Aperivue/medsci-skills;
> archived at Zenodo, https://doi.org/10.5281/zenodo.20155321).

**BibTeX**（软件以及描述其设计的预印本）：

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

The Zenodo **concept DOI** [10.5281/zenodo.20155321](https://doi.org/10.5281/zenodo.20155321)
always resolves to the latest release; [`CITATION.cff`](CITATION.cff) carries the machine-readable
元数据（GitHub 的“引用此存储库”按钮可读取它）。

**在已发表或正在审稿的作品中使用过它吗？** 通过
["Used in research" issue template](https://github.com/Aperivue/medsci-skills/issues/new?template=used-in-research.yml)
— with your permission it is added to [`docs/citations.md`](docs/citations.md).

## 免责声明

这些技能是研究生产力工具。他们**不**提供临床决策支持、医疗建议或诊断建议。所有输出在用于任何出版物或临床环境之前均应由合格的研究人员进行审查。

## 致谢

- `make-figures` Critic Loop is inspired by [PaperBanana](https://github.com/dwzhu-pku/PaperBanana) (Zhu et al., *Automating Academic Illustration for AI Scientists*, arXiv:2601.23265, 2025) and by prior self-refinement research — Self-Refine (Madaan et al., 2023), Reflexion (Shinn et al., 2023), and Constitutional AI (Anthropic, 2022). The implementation in this repository is a clean-room reconstruction specialized for medical publication figures; no code, prompts, or configurations are derived from PaperBanana's repository.
- 与 `check-reporting` 捆绑在一起的报告指南清单根据其原始知识共享许可证重新分发（请参阅每个清单以了解归属）。
- Wong 色盲安全调色板：Wong B. *Points of view: Color blindness.* Nature Methods 8:441 (2011).

## 执照

MIT License. See [LICENSE](LICENSE) for details.

Some bundled material is **not** ours and is not MIT: the official guideline templates, the CSL citation styles, and a few checklist summaries carry their own terms — including CC BY-NC, which restricts commercial use. Those are indexed in [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md), which ships with every copy and is checked against the tree on every build.

捆绑的报告指南清单保留其原始的知识共享许可。请参阅每个清单文件的归属。

Optional dependency: `pdf_to_md.py` uses [pymupdf4llm](https://pymupdf.readthedocs.io) (AGPL-3.0). Not bundled -- installed separately by the user via `pip install pymupdf4llm`.

## 明星历史

<a href="https://star-history.com/#Aperivue/medsci-skills&Date">
  <img src="https://api.star-history.com/svg?repos=Aperivue/medsci-skills&type=Date" alt="MedSci Skills star history" width="640">
</a>

## 关于

Built by [Aperivue](https://aperivue.com) -- tools for medical AI research and education.

**Runs anywhere the [Agent Skills standard](https://agentskills.io) is supported** -- not Claude Code alone. Claude Code, OpenAI Codex, Cursor, and GitHub Copilot are all verified against each host's own docs: one install, four hosts, no per-host fork ([host compatibility](docs/host_compatibility.md)).

如果您觉得这很有用，请考虑给它一颗星。它可以帮助其他研究人员发现这些工具。
