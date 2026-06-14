# Reverse-engineering PLAYBOOK — one loop iteration

This is the single source of truth the self-improvement loop follows. Each iteration
turns a small batch of open-access papers / published reviews into **one** concrete,
committed improvement to a skill, with a Codex review checkpoint and hard outward gates.

Read `LICENSING.md` first — it is binding on every artifact this loop commits.

## Invariants (every iteration)

- **One improvement per iteration.** A single new probe section, one rubric extension,
  one exemplar set, one calibration table, or one detector — never a grab-bag.
- **Learn-then-synthesize.** Sources stay in `_corpus/` (gitignored). Commits carry only
  distilled patterns + freshly authored synthetic content (+ CC-BY/CC0 anchors). The
  `distill.py` manifest gate enforces this.
- **Feature branch only.** Commit and push to a `feat/*` branch. **Never** merge to main,
  publish, tag, release, or change the marketplace without explicit human approval.
- **Green before commit.** The full local mirror of `.github/workflows/validate.yml`
  must pass (see Step E).
- **Codex is a lead, not a verdict.** Fold in only the feedback you can verify; record
  rejections with a one-line reason.

## Step A — Acquire

1. Pull the next batch (N ≈ 5) of `record_id`s / DOIs from `doi_lists/queue.txt`.
2. Fetch full text into `_corpus/papers/<record_id>.md` (use the `fulltext-retrieval`
   skill for OA articles; open-review APIs for review reports). `scripts/acquire.py`
   prepares the batch directory and a manifest stub per record.
3. Fill each manifest record in `_corpus/manifest.json` (schema:
   `source_manifest.schema.json`): real `license` / `license_url`, `retrieved_at`,
   and keep the defaults (`verbatim_allowed: false`, `public_reuse_policy: synthetic_only`)
   unless a permissive license is **verified** for that record.
4. **Harvest the article's linked artifacts.** Most strong papers ship a *Data/Code
   availability* statement: supplementary files, a **GitHub/GitLab** repo, a **Zenodo / OSF /
   Figshare** deposit, a **HuggingFace** model/dataset card. Record each under the record's
   `linked_artifacts[]` with its **own** verified license — a code repo carries a *software*
   license (MIT / Apache / GPL / none) and a Zenodo deposit a *per-deposit* license, both
   distinct from the article; supplementary usually inherits the article license but verify.
   These artifacts are where the highest-value findings live: released code reveals the real
   decision threshold, the actual train/test split, and whether the claimed tuning ran;
   supplementary holds the calibration plot, per-subgroup tables, and the flow counts; a data
   deposit shows provenance and overlap. Fetch what you can into
   `_corpus/artifacts/<record_id>/` (gitignored) and note what each adds.
5. Unknown/unverifiable license (article **or** any linked artifact) → leave it learn-only
   (defaults). It can inform reading but cannot appear in a committed artifact. `distill.py`
   validates and authorizes each linked artifact independently (`--authorize id#N`).

## Step B — Analyze

For each paper, write a structured analysis to `_corpus/analysis/<record_id>.json`
(`scripts/analyze_paper.py` scaffolds and validates the shape). Capture *patterns*, not
copied prose: study type, applicable reporting guideline, what makes the
Methods/Results/Discussion strong, figure/table strengths, and the concerns a sharp
reviewer would raise (in your own words).

Then **review the linked artifacts** (Step A.4) and fold what they add into the analysis
(`linked_artifacts_reviewed[]`): what the released **code** revealed about the real method
(threshold, split, leakage, whether the claimed tuning ran), what the **supplementary** held
(calibration, per-subgroup results, flow counts), and what a **data/model deposit** showed
(provenance, overlap, dataset card limitations). These often surface the sharpest, most
reusable findings — and they ground figure exemplars, because the repo's plotting code or the
supplementary figure shows the *actual* anatomy of the chart. Still capture *patterns*, never
copied code or figures.

## Step C — Distill

Aggregate the batch into **one** candidate improvement. Pick the highest-priority open
item from the priority order below. Author it as synthesis:

- a new domain-probe **section** (extend an existing module — see the probe note below),
- a `critic_rubrics/` or `reviewer_calibration/` extension,
- a synthetic `exemplar_*` set (with a `_why.md` curator note),
- a journal compliance-floor table, or
- a deterministic detector candidate.

Run `scripts/distill.py --check` so the manifest gate confirms every source feeding the
artifact permits the reuse you applied.

## Step D — Integrate

Wire the artifact into the target skill the lean way: keep `SKILL.md` short, put the
knowledge in `references/` loaded on demand.

- **Domain probes are vendored byte-identical** across `peer-review` and `self-review`.
  Prefer adding a **section to an existing module**, then run
  `python3 scripts/check_domain_probe_sync.py --sync`. A genuinely new probe **file**
  requires updating `check_domain_probe_sync.py` `MODULES`, both skills' copies, and any
  generated docs in the **same** commit, or CI fails.
- **A new detector** follows the 8-step contract (FAMILY_BY_ID in
  `gen_detectors_catalog_json.py`, regenerate + `--check`, PII-free fixture, test,
  `validate.yml` wiring, `catalog_counts.json` bump). A detector ships as P0 only after
  measuring precision on the corpus; otherwise it lands as a P1 warning.

## Step E — Verify, review, commit

1. **Codex checkpoint.** Manuscript/design artifacts → `/codex:adversarial-review
   --background`; detector/CLI code (< 3 files) → `/codex:review --wait`. Read the
   output critically; apply only verified findings; record rejections with a reason.
2. **Local CI mirror.** Run every step in `.github/workflows/validate.yml`
   (validate_skills, routing assets, domain-probe sync, locale inventory, the catalog/
   marketplace/detector/skill-doc generators + self-tests, A1–A6, demo manifest). All
   green.
3. **Anti-leak grep.** Confirm the diff carries no verbatim source prose, no figure from a
   non-CC source, no code copied from a linked repo whose license was not verified-permissive
   (`distill.py --authorize id#N verbatim`), and nothing under `_corpus/`.
4. **Commit + push** to the feature branch. Append a row to `PROGRESS.md`.
5. **ScheduleWakeup** (1200–1800s) for the next iteration, or stop at a merge/release
   gate for human approval.

## Priority order (work top-down)

1. Review skills: `peer-review` / `self-review` probes + `exemplar_reviews/` (from
   published open reviews).
2. `reviewer_calibration/` — journal compliance floors + critical items (a new
   reference dir, **not** `reviewer_profiles/`, which is form-fields-only).
3. `write-paper` `exemplar_methods` / `exemplar_results` / `exemplar_discussion`
   (synthetic).
4. `analyze-stats` `exemplar_tables/`.
5. **`make-figures` is a standing multi-iteration lane — figures are the suite's weakest
   area, so keep returning to it (one figure type per iteration).** `exemplar_plots/` anatomy
   models + `critic_rubrics/` extensions, working through, at least: forest (done) → KM curve
   (pairs the survival table-type) → ROC / precision-recall → calibration plot → Bland–Altman
   → confusion matrix → visual / graphical abstract → JACC-style central illustration →
   model-architecture / pipeline diagram → STARD-AI dataset-flow → CLAIM per-subgroup +
   calibration panel. Each iteration: one figure type, grounded in the linked code/supplementary
   (Step A.4) that shows the chart's real anatomy, complementing (not duplicating) the
   `critic_rubrics/data_plot.md` §C checklist. The non-flow gaps the figure_map marks ❌
   (STARD-AI, CLAIM) are high-value targets.
6. `check-reporting` compliance-floor integration.
7. New deterministic detectors (corpus-precision-validated) — often seeded by a linked code
   repo or supplementary that exposes a checkable failure (an unstated threshold, a
   train/test overlap, a metric the code does not actually compute).
8. Token-efficiency pass (probe-sync CI, SKILL.md duplication → references, catalog SSOT).

## Outward-action gates (require explicit human approval)

Merge to main · `npm publish` · GitHub release · tag · marketplace change · opening a PR
for merge. Feature-branch commit and push are the only outward actions the loop performs
on its own (reversible).
