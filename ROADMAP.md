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

The work that keeps the toolkit trustworthy for real submissions:

- **Manuscript-audit reliability** — keep the deterministic detectors precise
  (few false positives) and reproducible; expand challenge-card coverage.
- **Reporting-guideline compliance** — keep the bundled EQUATOR / risk-of-bias
  checklists current and correctly versioned (base + extension naming).
- **Reference and citation integrity** — verification against PubMed / CrossRef /
  OpenAlex before a reference is trusted; no references written from model memory.
- **Numerical, cohort, and cross-artifact consistency** — counts, denominators,
  and submission-package artifacts that agree across the manuscript lifecycle.
- **Release stability and documentation clarity** — honest versioning, a clear
  "start here", and reproducible public demos.
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
