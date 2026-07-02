# Roadmap

MedSci Skills is a physician-built, submission-grade clinical-manuscript workflow
toolkit with deterministic integrity gates. This roadmap states what the project
prioritizes and — just as important — what it deliberately will **not** become. It
is a direction document, not a delivery commitment; priorities shift with real
manuscript, review, and submission experience.

See also [`docs/competitive_positioning.md`](docs/competitive_positioning.md) for
where the toolkit sits relative to broad agent-skill catalogs, and
[`README.md` § What This Is NOT](README.md) for the scope boundary.

## Near-term priorities

The toolkit's reliability surface — deterministic detectors, reporting
checklists, reference and consistency gates — is now broad and mature. The
near-term frontier is **research throughput**: producing more of the
submission-grade artifacts a physician actually ships. Reliability work is
demoted to a sustaining floor, not the strategic direction.

### Research throughput (the frontier)

- **Figure & artifact generation** — produce submission-ready figures
  (Kaplan–Meier with number-at-risk, ROC with operating point, calibration with
  slope/intercept), visual abstracts, and central illustrations, backed by
  deterministic render tests — not just compliance checks on figures drawn
  elsewhere. This is the suite's self-identified weakest area.
- **Executable analysis depth** — pair each review domain-probe with a runnable
  `analyze-stats` guide so the toolkit *produces* the estimate or table (absolute
  risk, NNT/NNH at a stated baseline, decision-curve net benefit), not only flags
  its absence.
- **Design-time enablement** — turn study design into buildable artifacts:
  target-trial-emulation specifications, DAG-derived adjustment sets, and
  prediction-model-appropriate sample sizes, shaping a study *before* data
  collection — the highest-leverage point in the pipeline.

### Sustaining (the reliability floor)

These stay green but are no longer the strategic direction:

- **Manuscript-audit reliability** — keep the deterministic detectors precise
  (few false positives) and reproducible.
- **Reporting-guideline compliance** — keep the bundled EQUATOR / risk-of-bias
  checklists current and correctly versioned (base + extension naming). New
  reporting-guideline lanes are **maintenance mode** — added only on demonstrated
  demand, and preferentially paired with a production artifact (analysis guide,
  figure exemplar, or worked structure) rather than shipped check-only.
- **Reference and citation integrity** — verification against PubMed / CrossRef /
  OpenAlex before a reference is trusted; no references written from model memory.
- **Numerical, cohort, and cross-artifact consistency** — counts, denominators,
  and submission-package artifacts that agree across the manuscript lifecycle.
- **Release stability and documentation clarity** — honest versioning and a batched
  [release cadence](docs/maintainer_workflow.md#release-cadence) (no per-PR version
  inflation), a clear "start here", and reproducible public demos.
- **Maintainability and governance** — lightweight contributor and maintainer
  process so the project can accept help without diluting clinical scope
  (see [`MAINTAINERS.md`](MAINTAINERS.md)).
- **Citation / adoption evidence** — a durable, cautious record of real use
  (see [`IMPACT.md`](IMPACT.md)); JOSS / software-paper readiness.

## Under consideration (not committed)

Candidate directions that depend on demand and on staying within scope:

- Deeper structured-summary-box and disclosure/availability checks as journals
  formalize their requirements.
- Fairness / equity / subgroup-performance review depth as standards stabilize.
- Broader journal-profile coverage for medical-AI venues.

## Not planned / explicitly out of scope

MedSci Skills is **narrow on purpose**. It will not become:

- a clinical **diagnosis** or decision-support tool, or anything that gives
  patient-specific medical advice;
- an **autonomous manuscript generator** that replaces human authors,
  statisticians, reviewers, IRBs, or journal requirements;
- a broad **general AI-scientist** platform spanning chemistry / drug discovery /
  bench biology, or one that runs experiments autonomously;
- a source of **unsupported guideline interpretation** or **clinical-validation**
  claims about the toolkit itself.

**In scope (as of v5.0):** *clinical AI model research engineering* — choosing a
paper-grounded architecture, scaffolding a reproducible training repo, and
validating, documenting, and evaluating a medical-imaging or LLM/MLLM model so the
work reaches a manuscript. This is the model-engineering lane; it **integrates**
MONAI / nnU-Net and never reimplements them, and it never trains or claims results
autonomously — a human expert runs and verifies everything. That is different from a
general autonomous AI-scientist, which remains out of scope.

These boundaries are a feature: the value comes from doing clinical research
workflow — manuscript and model alike — well, with human experts in the loop, not
from breadth.

## How priorities are set

Priorities come from real manuscript cycles — what actually caused a revision
round, a desk reject, or a reviewer concern — promoted into a reusable detector,
probe, checklist, or doc. Proposals are welcome via the issue templates; the
founder approves anything touching clinical/research scope or medical claims
(see [`MAINTAINERS.md`](MAINTAINERS.md)).
