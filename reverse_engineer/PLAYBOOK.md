# Reverse-engineering PLAYBOOK — one loop iteration

This is the single source of truth the self-improvement loop follows. Each iteration
turns a small batch of open-access papers / published reviews into **one** concrete,
committed improvement to a skill, with a Codex review checkpoint and hard outward gates.

Read `LICENSING.md` first — it is binding on every artifact this loop commits.

## Invariants (every iteration)

- **One improvement per commit; batch ~3–4 commits per PR.** Each commit is a single focused
  artifact (a probe section, a table-type, a figure-anatomy exemplar, a checklist), but they
  are bundled into one feature branch + **one PR** to cut CI/merge/review overhead. A commit
  is still independently revertable.
- **Evidence-driven targeting (not a fixed list).** Each iteration works the highest-scoring
  **open** gap in `gap_register.md` (Step 0), not a predetermined order. The goal is to find
  weaknesses across the *whole* suite — including unknown ones — by reading strong papers.
- **Learn-then-synthesize.** Sources stay in `_corpus/` (gitignored). Commits carry only
  distilled patterns + freshly authored synthetic content (+ CC-BY/CC0 anchors). The
  `distill.py` manifest gate enforces this (article **and** linked artifacts — Step A.4).
- **Feature branch only.** Commit and push to a `feat/*` branch. **Never** merge to main,
  publish, tag, release, or change the marketplace without explicit human approval.
- **Green before commit.** The full local mirror of `.github/workflows/validate.yml`
  must pass (see Step E).
- **Codex is a lead, not a verdict — and kept cheap.** Scope each review to the changed
  file(s); **no web-search by default** (turn it on only to verify a factual claim — an
  instrument name, a citation, a statistic). Batch several small artifacts into one review
  when they share a theme. Fold in only verified feedback; record rejections with a reason.
- **Stop at saturation.** When a lane's `gap_register.md` rows are all shipped, mark it
  `saturated` and move on — do not manufacture marginal additions.

## Step 0 — Gap triage (run first)

1. Open `gap_register.md`. Pick the highest-scoring **open** gap (`score = impact × frequency
   × deficit`). Mark it `in-progress`.
2. **Cross-skill audit cadence:** every ~4 iterations, before picking, audit one skill the loop
   has not touched recently — scan its `references/` against the common cases in its domain
   (the table types / figure types / probes / checklists / templates a practitioner expects)
   and add the absent ones as new rows. Rotate the audited skill so coverage spreads beyond
   the obvious (figures, review skills) into the long tail (clean-data, calc-sample-size,
   design-study, deidentify, present-paper, manage-project, …).
3. The gap names the target skill and artifact type, which sets the corpus you acquire next.

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

**Gap discovery.** As you analyze, ask the gap-finding question: *what does a strong paper in
this area need that our skills do not yet cover or check?* Add each new weakness as a row in
`gap_register.md` (skill, gap, impact/freq/deficit). This is how the loop reaches the skills
you did not already know were weak.

## Step C — Distill

Aggregate the batch into the **one** improvement that resolves the Step 0 gap. Author it as
synthesis:

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

1. **Codex checkpoint (kept cheap).** One scoped review per artifact (or one batched review
   across same-theme artifacts) — name the exact files, **no web-search by default** (enable
   it only to verify a factual claim: an instrument name, a citation, a statistic). Read the
   output critically; apply only verified findings; record rejections with a reason. A 40-line
   reference markdown does not need a 150k-token review — keep the prompt tight.
2. **Local CI mirror.** Run every step in `.github/workflows/validate.yml`
   (validate_skills, routing assets, domain-probe sync, locale inventory, the catalog/
   marketplace/detector/skill-doc generators + self-tests, A1–A6, demo manifest). All
   green.
3. **Anti-leak grep.** Confirm the diff carries no verbatim source prose, no figure from a
   non-CC source, no code copied from a linked repo whose license was not verified-permissive
   (`distill.py --authorize id#N verbatim`), and nothing under `_corpus/`.
4. **Commit + push** to the feature branch. Append a row to `PROGRESS.md`, and update the gap's
   `gap_register.md` status to `shipped (#PR)` (or `saturated` if it closes the lane).
5. After ~3–4 commits, **open one PR** for the batch and stop at the merge gate for human
   approval. (Single-iteration `ScheduleWakeup` pacing is fine for an autonomous run, but bundle
   the commits into one PR.)

## Target categories (the gap register draws from these — it, not this list, is the SSOT)

`gap_register.md` is the live priority queue; these are the recurring categories it pulls from,
roughly in descending baseline value. The register's score (impact × frequency × deficit) and
the cross-skill audit (Step 0.2) decide the actual order — including long-tail skills not listed
here.

1. **`make-figures` — the standing lane (the suite's weakest area).** `exemplar_plots/` anatomy
   models + `critic_rubrics/` extensions: forest (done) → KM → ROC/PR → calibration → Bland–Altman
   → confusion matrix → visual/central illustration → architecture → STARD-AI / CLAIM panels.
   Ground each in the linked code/supplementary (Step A.4) that shows the chart's real anatomy.
2. Review skills: `peer-review` / `self-review` `domain-probes/` + `exemplar_reviews/` for
   uncovered study types (RCT/trial, survey, qualitative, economic), and `reviewer_calibration/`.
3. `write-paper` exemplars (methods/results/discussion done; intro/abstract open) and
   `analyze-stats` `table-types/` (the reliability/agreement table is open).
4. `check-reporting` checklists + compliance-floor integration.
5. New deterministic detectors (corpus-precision-validated) — often seeded by a linked code
   repo or supplementary that exposes a checkable failure.
6. **Long-tail audit** (Step 0.2): rotate through the skills the loop rarely touches
   (clean-data, calc-sample-size, design-study, deidentify, present-paper, manage-project,
   write-protocol, …) and register what each lacks.
7. Token-efficiency / structural consistency passes.

## Outward-action gates (require explicit human approval)

Merge to main · `npm publish` · GitHub release · tag · marketplace change · opening a PR
for merge. Feature-branch commit and push are the only outward actions the loop performs
on its own (reversible).
