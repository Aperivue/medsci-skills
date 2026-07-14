# Changelog

## [Unreleased]

### Fixed

- **`/self-review` `check_analysis_definitions` was reading layout, not defect** (detector #66,
  shipped hours earlier in #340). Two bugs, both caught on the *second* real manuscript:

  1. **It could not see a CHEST manuscript at all.** `METHODS_RE` matched `Methods` /
     `Materials and Methods` / `Patients and Methods`. CHEST *requires* `Study Design and Methods`, so the
     gate emitted `SECTIONS_NOT_FOUND` and silently skipped the whole cross-check. Broadened to accept
     `Study Design and Methods`, `Subjects and Methods`, `Design and Methods`, `Methods and Materials`.

  2. **`MODEL_OUTCOME_UNDEFINED` was a formatting artifact.** It searched for the outcome declaration in a
     400-character window around each model mention. A manuscript that declares its outcome once under
     *Outcomes* and then specifies models under *Statistical Analysis* is following the **recommended**
     structure — and the windowed search fired on it. It flagged a clean manuscript for exactly the reason
     it flagged a rejected one. The declaration is now sought across the **whole Methods section**.

  **This makes the check sound but deliberately narrower**, and the honest consequence must be stated: it
  no longer fires on the rejected manuscript that motivated it. That paper declares three outcomes and
  never says which one a given Cox model used — a real defect, and one a reader can see and a regex cannot.
  The original detector appeared to catch it, but only because the outcome paragraph happened to sit more
  than 400 characters from the model sentence, which is true of every well-structured paper. **One
  manuscript, three findings matching three reviewer comments, and I called it validated. That was luck,
  and the second manuscript exposed it.**

  `REFERENCE_STANDARD_UNDEFINED` likewise now honours a declared outcome: *reference standard* is
  diagnostic-accuracy vocabulary, and a prognostic model scores its predictions against the outcome it has
  already declared. `MODEL_NOT_IN_METHODS`, `TIER_LABEL_UNDEFINED` and the informational `ANALYSIS_LOAD`
  are unchanged.

### Added

- **`/self-review` — every analysis you report must have been defined**
  (`skills/self-review/scripts/check_analysis_definitions.py`, detector #66, with a challenge card).

  Twenty-four detectors in this skill ask whether a number is *correct*. **None asked whether the
  analysis that produced it was ever *defined*** — and a reviewer walks straight into that gap:

  > "The outcome (dependent variable) for the multivariable Cox model is not specified." … "The ground
  > truth (reference standard) against which discrimination and calibration were assessed is not
  > defined." … "This section is largely incomprehensible in its current form."

  A Cox model whose dependent variable is never stated is not a *hard* paper. It is an **incomplete**
  one. The gate emits `MODEL_OUTCOME_UNDEFINED`, `MODEL_NOT_IN_METHODS`, `REFERENCE_STANDARD_UNDEFINED`
  (Major) and `TIER_LABEL_UNDEFINED` (Minor).

  **`ANALYSIS_LOAD` is informational and never a verdict.** The same reviewer wrote *"too many analyses
  have been performed and reported"* — and named the mechanism in the next sentence: *"this appears to
  have contributed to omissions of critical information in the Materials and Methods section."* A second
  reviewer of the same manuscript listed its sensitivity analyses as a **strength**. So **load is the
  cause, not the crime**, and a detector that capped the count would have punished the strength and
  missed the defect. The two challenge fixtures carry the **identical** analysis count (two model
  families, two auxiliary analyses) and get opposite verdicts: definition is what the gate reads.

  The remedy is not to cut analyses. It is to restore the definitions they crowded out — and, where load
  is genuinely high, to move the defensive analyses to the supplement: same defence, far less reader
  burden and far less attack surface.

- **`/peer-review` — the request-type rule now has a script behind it**
  (`skills/peer-review/scripts/check_review_request_types.py`, detector #65, with a challenge card).
  **Every other detector in this repo audits the manuscript. This one audits the review.**

  Phase 3 already told reviewers to sort each ask into two kinds — **disclosure** ("show what the
  study already knows and has not printed": costs the authors nothing, and *surfaces* errors) and
  **computation** ("produce a number that does not yet exist": creates a new, unreviewed error
  surface, written under revision deadline by authors who will not re-check it, and accepted next
  round by a reviewer who reads its *existence* as compliance). In the incident that produced the
  rule, three of the four defects found in a revision had been **manufactured by the reviewer's own
  two computation requests**.

  **The rule shipped as prose, and prose did not bind.** In the first live review after it landed, a
  draft went out with fifteen asks — six computation, one demanding a second reader — and it passed
  *every* neighbouring gate: word count, em-dash density, forbidden recommendation words, attitude
  markers, hedging ratio. Those held because they are scripts. This one failed because it was a
  sentence. The difference was not importance; it was executability.

  The gate emits `COMPUTATION_UNJUSTIFIED` (a computation request stating no reason the existing
  tables cannot answer it — *feasibility is not justification*: "a text filter on data you already
  hold" says the work is cheap, not that the tables cannot answer it), `COMPUTATION_HEAVY`,
  `NEW_DATA_REQUESTED` (a second reader, re-segmentation, a new cohort — strictly worse, because it
  cannot be satisfied in a revision at all), `NESTED_P_REQUESTED` (never *request* the subset-vs-parent
  table that `check_nested_group_comparison.py` exists to flag), and `ESTIMATOR_UNNAMED`.

  Deliberately high-precision: it honours negation ("I am not asking you to repeat the validation";
  "a single reader **without** adjudication"; "**without** a significance test — the groups are
  nested") and ignores plain description ("bootstrap intervals are reported for the median only"
  states a fact, it does not ask for work). A detector that never falsely accuses a disclosure
  request is worth more than one that catches every computation.

  Wired into Phase 3 (beside the rule it enforces), Phase 4 self-QC item 7, and the Phase 6
  pre-submission checklist.

- **`/present-paper` — presentation archetypes: the skeleton, chosen by where you are standing**
  (`references/presentation_archetypes.md`, and its mechanical half `check_deck_budget.py`,
  detector #64). A deck has **two independent choices**, and conflating them is why talks fail: the
  **archetype** is what the talk has to *do*; the **visual style** is what it *looks like*. The skill
  had five skins and no skeletons. Now it has eight — conference oral, journal-club critique,
  case-anchored grand rounds, didactic lecture, defence/job talk, keynote (Duarte's sparkline, the
  Jobs STAR moment, Takahashi and Lessig), lay talk, and the decision brief (Minto's pyramid, action
  titles, Kawasaki's 10/20/30) — each with what the room is, what a slide is *for* there, what to
  steal, and what fails.

  A conference oral in a keynote's skeleton dies (no data on the slides; the reviewer in row three
  came for the numbers). A keynote in a conference oral's skeleton dies harder. **The skin is a
  preference; the skeleton is not.**

  `check_deck_budget.py --archetype X --minutes N` enforces the mechanical part — slides against the
  clock, words per slide, the type floor for the back row. It takes an archetype instead of a
  universal threshold **because a single global number would have to be wrong for most venues**:
  40 words is an ordinary academic slide and a catastrophic keynote slide. The challenge card proves
  exactly that, by judging *the same deck* twice and requiring opposite verdicts.

  Honest about evidence: **assertion-evidence is the only pattern here with experimental support**
  (Alley & Neeley 2005). The rest is craft — good craft, from people who are very good at this, but
  craft, and the file says so.

- **`/present-paper` — the marks an AI leaves on a deck, caught in the built `.pptx`**
  (`check_slide_tells.py`, detector #63). Reviewers now say roughly a third of the decks they
  receive were made by an AI, that they can spot it instantly, and — the part that matters — that
  the tell is **not that the deck is ugly**. Templates solved ugly. The tell is that the deck stops
  communicating: *"무슨 말을 하고 싶은 것인지 전달이 잘 안 된다. 만드는 사람의 생각을 잘 읽을 수가
  없음."* Investors are telling founders never to use AI for an IR deck. Six verdicts, each one a
  mark people name unprompted:

  | | |
  |---|---|
  | `CHROME_ON_EVERY_SLIDE` | the little words along the top and bottom of every slide |
  | `SCAFFOLD_PHRASE` | a slide narrating its own construction — "요약하자면", "The key takeaway is…" |
  | `TOPIC_TITLE` | a content slide titled "Results" instead of saying what the result was |
  | `SHAPE_MONOTONY` | the same rounded box, eight times, at the same size |
  | `DEAD_SPACE_BAND` | a mostly-empty slide with a hole through the middle |
  | `ARROW_NO_SEMANTICS` | two or more arrows and not one of them labelled |

  Stdlib-only (it reads the `.pptx` as the ZIP of XML it is), so it also audits a deck a colleague
  sends you. It does **not** detect "was AI used" — AI used as a booster leaves none of these marks.

- **`references/ai_slide_tells.md`** — the teaching half, read before drafting. Scaffolding is the
  centre of it: a person thinking A→B→C→D does it in silence and writes down **D**; a model says
  *"having completed B, I will now proceed to C"* and leaves the sentence in. Scaffolding is what a
  writer takes down in revision. AI hands over the building with the scaffolding still bolted on.

- **Diagrams and plots are now drawn as CODE and inserted** — matplotlib, or Graphviz DOT where the
  graph is the point, because a DOT edge *must* be written `A -> B [label="seeds along"]`: the
  language will not let you draw an unlabelled arrow. Assembling a diagram from `python-pptx`
  autoshapes produces both remaining tells at once and is now forbidden. This is the one approach
  practitioners report actually working when they hand slide-making to an agent.

### Fixed

- **Three detectors were counted, tested, released — and never ran.** `check_table_percentages`,
  `check_reported_p_from_counts` and `check_dta_denominators` shipped in v5.20.0 with challenge cards,
  CI steps, JSON envelopes and a release note, and **`self-review/SKILL.md` never mentioned them**.
  They passed every gate we had and had never once run on a manuscript, while being counted in the
  number we publish. A challenge card proves a detector **works**; nothing proved the skill **calls**
  it. They are now wired into Phase 2.5 — the arithmetic a reviewer redoes with a calculator: a
  percentage that does not follow from its own denominator, and a P value that does not follow from
  its own counts. `scripts/check_detector_reachability.py` (CI) now fails if any detector is not
  invoked by a SKILL.md, directly or through a named bundle runner.

- **`/present-paper` Phase 0 demanded ~14,000 tokens of references before a single slide.** Three of
  the six mattered up front; `medical_presentation_templates.md` alone cost ~3,700 tokens to use a
  fifth of, and the visual-style file was read before the style was chosen. Split into *read now*
  (the AI-tells file, the archetypes, the enforceable rules) and *read when Q0/Q2 tells you which
  one*. **~7,400 tokens saved per invocation, with nothing decision-shaping removed.**

- **The archetypes file duplicated the medical templates.** Archetypes A–D (conference oral, critique,
  case-anchored, didactic) are the same four venues the content templates already covered — two files
  answering "how do I structure a journal club talk". The boundary is now explicit: the archetype
  gives the **stance** (what the talk must do, what fails), the template gives the **sections**, and
  the archetype wins where they conflict. A section list cannot tell you that a journal club which
  merely summarises the paper has failed.
- **An MIT-licensed package was redistributing ten figures cropped from published papers.** Under
  `make-figures/references/exemplar_diagrams/`, ten PNGs were — in the directory README's own words —
  *"rendered figure cropped from a published paper"*. The README promised each carried a sidecar
  recording *"source PDF, page, DOI, crop coords"*, and that it *"records DOI and source for every
  exemplar."* **It recorded `label`, `figure_type`, `dpi`.** No source, no DOI, no licence; eight of
  the eighteen images had no sidecar at all. The safeguard the README described had never been
  implemented, and nothing checked. Its fair-use argument — that exemplars are *"not redistributed as
  part of generated figures"* — was true and beside the point: they were redistributed **as part of
  the package**, on npm and in the classroom ZIP every user downloads, under a licence that grants
  the world the right to copy, modify and sell them. Some were probably open-access and reusable with
  credit; we cannot say which, because the provenance was never recorded, and **a permission you
  cannot demonstrate is not a permission.**

  The ten are removed. The `_why.md` design notes stay — they are ours, and they are where the value
  was: a paragraph on why a two-tone palette survives greyscale teaches more than the picture it was
  written about. Three things now prevent a recurrence:

  - **`scripts/check_bundled_media_license.py` (CI)** — every raster image under `skills/` must be
    either generated by a named script of ours or carry a sidecar declaring `source`/`doi` **and** a
    redistributable `license`. No "probably fine" tier: the whole failure was a probably-fine nobody
    checked.
  - **`extract_exemplar_from_pdf.py` now requires `--doi` and a new `--license`.** `--doi` used to be
    optional, which is exactly how ten unattributable figures got in. A tool that *can* produce an
    unattributable exemplar eventually will.
  - The directory README says plainly what happened, and how to keep your own exemplars **locally**
    (a file you never commit is never redistributed).

  Payload: **13 MB → 1.1 MB.** Our own rendered exemplars were also downsampled to 1568 px — the
  ceiling the vision pipeline applies before a model ever sees them — so the removed pixels cost
  bandwidth and reached nobody. Verified by reading a compressed diagram back: every count and label
  in the PRISMA flow is still crisp.

- **A broken workflow file does not turn a pull request red — it makes the checks *disappear*.**
  A step named ``- name: Run deck-budget challenge (same deck: fits an oral, ...)`` put a `: ` inside
  an unquoted YAML scalar. `validate.yml` stopped being valid YAML, GitHub ran **zero jobs**, and
  `gh pr checks` said **"no checks reported on the branch"** — not a failure, just silence. Every
  gate in the repository (the PII scanner, the detector-envelope contract, the manifest, all 153
  steps) was quietly not running, and the branch looked *quiet* rather than *broken*. Anyone merging
  on green would have merged on nothing. `scripts/check_workflow_yaml.py` now parses every workflow
  file — and names that specific trap — as the first step of CI. It was verified by restoring the
  defect and watching the gate go red.

- **Our own house style was manufacturing the most-cited tell.** `academic-lecture-style.md` required
  an all-caps eyebrow on **every** slide and a `2026 · NEUROGENETICS` brand footer on **every**
  slide; `nature_lancet.md` gave them fixed coordinates; and `build_pptx_nature_lancet.py` took
  `eyebrow` as a **required** argument, so every content slide got one whether or not it meant
  anything. *"슬라이드 상단과 하단에 자잘한 글자들"* is the first thing reviewers name. Chrome is now
  off by default — the page number stays (someone in Q&A says "go back to twelve"), the eyebrow
  survives on the title slide and section dividers, and the rest is gone. **The builder was changed,
  not just the style guide**: editing the guide would have been a fix that changed nothing, because
  the builder is what makes the deck. `tests/test_builder_no_chrome.py` builds with the shipped
  builder (must be clean) *and* restores the old eyebrow-everywhere default (must be caught) — the
  second half is what makes the first half mean anything.

- **`check_detector_envelopes.py` failed a detector for doing the right thing.** It grepped source
  for the literal `"detector": "check_x"`, so a detector that names itself once
  (`DETECTOR = "check_x"`) and uses the constant in both the envelope and every finding was reported
  as not self-identifying. That would have pushed authors toward copy-pasted string literals to
  appease a checker, which is how a gate starts making the code worse. It now accepts both, and
  still catches a wrong name.

### Added

- **A setup check that answers "what else does this computer need?" before you need it**
  (`installers/doctor.py`; double-click `check-setup-macos.command` / `check-setup-windows.cmd`).
  Every skill that needs an outside program already fails politely — the problem is *when*: you find
  out in the middle of the work, and a clinician who hits that message does not stop and install a
  package manager. They close the window. The check runs at the end of every install and reports in
  terms of what you were trying to **do** — "turn your manuscript into a journal-formatted Word file"
  needs pandoc, "read and QC submission PDFs" needs poppler, "open a .docx at all" needs python-docx
  — and with `--fix` installs the small things after asking. Large things (a TeX distribution, R,
  PyTorch) are **never** installed for you: it prints the size and the command and leaves the choice
  alone. It installs nothing on its own, and cannot fail an install that worked.

- **The installers now offer to install Python itself.** Telling someone with no Python to "go to
  python.org" is a step they have to perform; on Windows the installer now offers
  `winget install --exact --id Python.Python.3.13 --scope user` — no administrator password, which
  matters on a locked-down hospital PC — and otherwise opens the download page for them, on both
  platforms. The one checkbox that breaks everything if missed ("Add python.exe to PATH") is called
  out.

### Fixed

- **We invited contributors through the browser, then failed them with a Python script.** A
  stranger's first pull request — five nephrology journal profiles, exactly what our "good first
  issue" asked for — went red with `DISTRIBUTION_MANIFEST_DRIFT: … out of date — run python3
  scripts/gen_distribution_manifest.py`. He had added ten shipped files, so the hashed inventory the
  self-updater verifies against no longer matched. Nothing was wrong with his work. But CONTRIBUTING
  promises a browser-only path with **no git and no terminal**, and someone who accepts that
  invitation cannot run a Python script: we told them to do the one thing we had just promised they
  would never have to do. The gate stays strict — it protects the updater — but it now **names the
  files that moved**, gives the command, and says plainly that a contributor who cannot run it should
  leave it red, because **a maintainer will refresh the manifest before merging and this is not a
  rejection**. CONTRIBUTING says the same. A regression test adds a shipped file and asserts the
  message, because the message was the defect.

- **The README demanded R and never mentioned pandoc — both wrong.** It listed "R 4.0+ with `meta`,
  `metafor`, `mada`" under Requirements, which reads as *you cannot use this without R*. The toolkit
  **never executes R**: `/analyze-stats` writes Python unless asked for R. Meanwhile **pandoc** — which
  people genuinely hit, because it renders the manuscript to Word — was not listed at all. Requirements
  now says what is true: Python and an agent host, and everything else on demand.

- **The Windows installer could report success while installing nothing.** On a Windows machine with
  no Python, `python` still *exists*: it is an App Execution Alias that opens the Microsoft Store. So
  `where python` succeeded, the installer ran it, a Store page opened — and the script said it was
  done. **Windows is 65% of classroom-ZIP downloads.** An interpreter is now accepted only after it
  proves, **by running**, that it is Python 3.9 or newer; asking `where` only proves a name exists.

- **A too-old Python produced a traceback instead of an explanation.** `install.py` *parses* on 3.8,
  so it did not fail cleanly — it died partway through and left a clinician staring at a Python stack
  trace. All four double-click scripts (install / update × macOS / Windows) and both Python entry
  points now check the floor **before** anything runs, and say which of the two problems it is ("no
  Python" and "too old a Python" need different actions), what to do about it, and that nothing on the
  computer was changed. A failed install now also says so, rather than ending on a cheerful prompt.

- **`check_python_floor.py` (CI)**: every script that reaches a user — the installers and the skill
  scripts the agent runs on their machine — must parse on **Python 3.9**, the floor the README
  promises. CI runs 3.11 and this project is developed on 3.14, so a `match` statement would have
  shipped, broken only on a clinician's computer, and been invisible: when a research tool errors out,
  a physician does not file a bug. They close the window and go back to doing it by hand.

### Added

- **`/contribute` — the way back** (new skill; **56 skills**, **detectors 61 → 62**). The people who use
  this toolkit are clinicians. They install it once, adapt a skill to the way their department actually
  works, add the journal they publish in, fix a checklist item that was wrong for their specialty — and
  then stop. The edit sits on one laptop. They do not open a pull request, because a pull request is not
  a thing they do. Frequently that edit is the most valuable thing in the repository, because it is real
  domain knowledge nobody in the project has, and it dies where it was written.

  The detection already existed and nobody had noticed: the installer hashes every shipped file and takes
  a **permanent backup** of any skill you modified before overwriting it. Nothing ever read the backup
  again. `/contribute` is the other half — it compares the installed skills against the shipped hashes,
  tells the author exactly what they changed and added, and offers it back as a pull request **without
  them ever typing a git command**. No GitHub CLI? It reaches the project as a pre-filled issue instead;
  installing a developer tool is not made a condition of helping.

  **`check_contribution_safety.py` is the load-bearing part.** These users edit skills *while working on
  real manuscripts and real patients*, so a local edit can carry a patient identifier, a national ID, an
  IRB number, a manuscript under review, a colleague's name, or a home directory with their own account
  name in it. A contribution flow that simply uploads "the files you changed" is a PHI leak with a
  friendly button on it. Patient-level data and credentials are **blockers** — the line is deleted, not
  argued with — and identity, institution, approval-ID, manuscript-ID and local-path findings are shown
  with the remedy next to them.

  And the skill says out loud, every time, that **the scan is not a certificate**: no pattern list
  recognises every patient name or every hospital, and a scanner that is *believed* to be complete is
  more dangerous than none, because it replaces the human check. The author reads every line that would
  leave their machine, and confirms, or nothing is sent.

  It also files the feedback that is not a code change — *"this flagged my paper and it was wrong"*, *"this
  failed on my Word document"*. A false positive is the only evidence anyone has of how a detector behaves
  on a **real** manuscript rather than a synthetic fixture; it is not a lesser contribution.

  **And nobody is nagged.** Reminders are **opt-in and off by default** — a clinician installed a
  research tool, they did not sign up to be asked for things, and an installer that greets a physician
  mid-manuscript with *"you changed a file, would you like to share it?"* is an installer they stop
  running, which this audience already under-does. Defaulting to silence costs a few contributions;
  defaulting to noise costs the update path itself.

  The install also, **once**, says how to say thanks — because clinicians who find this useful write
  to the maintainer personally and have often never starred the repository, not having weighed it up
  and declined but never having been told that starring is the thing you do, what it is for, or that
  it takes one click. That is a **missing instruction, not a missing favour**. `star_repo.py` explains
  what a star is (how the next researcher with the same problem finds the tool; the closest thing
  research software has to a citation when it is not in anyone's reference list) and then makes it one
  command with the GitHub CLI, or one click without it. If they have already starred it, it says thank
  you and stops. It never asks twice.

  The contribution option is mentioned **once**, at the end of a first install, and then never again whatever the
  user does — *ignoring the question is an answer*. Opted in, the reminder appears only when something
  actually changed, and **at most once a month**. The setting governs reminders **only** (`/contribute`
  runs whenever it is run; turning reminders off is not opting out of contributing, it is opting out of
  being asked), and it **cannot weaken the safety scan**, which reads no configuration at all — the
  tests assert that.


## [5.21.0] - 2026-07-13

Verification-layer batch: the marked-manuscript round trip, a self-improvement probe, an artifact
contract that lets a qc file name the detector that wrote it, two `/verify-refs` precision defects,
and `/find-cohort-gap` opened to researchers who do not have a named public cohort.
**55 skills / 61 integrity detectors / 46 guidelines / 23 domain-probe modules.**

### Added

- **A domain probe + gate for manuscripts that claim a system improved *itself*** (`/peer-review` +
  `/self-review`, `self_improving_system.md` SI1–SI7 and `check_self_improvement_claims.py`;
  **detectors 60 → 61**, domain probes 22 → 23). An agent that critiques and rewrites its own reports, a
  pipeline fine-tuned on data it generated, an LLM used as the judge that scores the training signal — a
  fast-growing class in medical AI, and one that is reviewed badly, because the loop *looks* like a
  method while the thing that decides whether it worked is often the system itself.

  The probe's organizing question is not *did it improve?* but **what said so?** Every improvement loop
  is a claim that some signal can substitute for human judgment, and signals are not interchangeable: a
  formal verifier is sound by construction; execution feedback is reliable but incomplete; an
  LLM-as-judge is bounded by its own competence and is itself an optimization target; a model's own
  confidence is the most gameable of all. Demonstrated self-improvement tracks that order, so a rung-1
  conclusion drawn from a rung-3 signal is a design-level Major.

  Two of the seven probes are decidable by reading, and the detector takes them:
  `SELF_CONFIRMING_EVALUATOR` (the judge is the same model family as the system it judges, and is never
  validated against anything outside the loop — when generator and evaluator share weights their biases
  correlate, and the loop reinforces the errors the model is *most confident about*) and
  `UNGROUNDED_SELF_LOOP` (an explicit self-refinement claim with no external signal named anywhere;
  ungrounded self-critique converges to rewording, not correction). Plus `SELF_TRAINING_NO_REAL_DATA`
  (minor) for training on generated data with no real-data mixing, where the distribution's tails — the
  rare presentations — are what erodes first.

  It is deliberately conservative: a paper that self-refines **and** validates its judge against human
  experts or a held-out labelled set has named its signal and does not fire. From there the probes are
  judgment, and stay judgment.

  Framework and evidence: Chen, Wang & Qu, *Recursive Self-Improvement in AI* (arXiv:2607.07663, a
  survey of 1,250 papers) for the verification hierarchy and the self-confirming loop; DeVilling, *The
  Mirror Loop* (arXiv:2510.21861) for the measured 55% decline in informational change across ten rounds
  of ungrounded self-critique; Shumailov et al., *Nature* 2024, for collapse under self-generated
  training data.

- **Complete / quasi-complete separation is caught before the model is fitted** (`/analyze-stats`
  Phase 2, `check_separation.py`; **detectors 59 → 60**). A predictor that perfectly predicts the
  outcome breaks maximum likelihood — no finite MLE exists — and the failure is **silent**. `glm`
  does not error: it returns an odds ratio of 0.00 (or an enormous one), *p* ≈ 0.99, and an AUC.
  That AUC gets written into a table as a result.

  This is routine in diagnostic imaging, because the good signs are the pathognomonic ones. A sign
  with 100% specificity and 100% PPV — T2-FLAIR mismatch for IDH status, the string sign, a halo
  sign — has an empty cell against the outcome *by construction*. Enter it as a covariate in an
  incremental-value model and the model is numerically undefined while looking entirely healthy.

  The gate is a cross-tabulation, not an inference: an empty cell is arithmetic, and arithmetic can
  be checked in advance. It runs on the **data**, in the analysis-plan phase, and reports
  `COMPLETE_SEPARATION` (an empty cell, or a continuous predictor whose ranges do not overlap) and
  `QUASI_SEPARATION` (a cell below the sparsity floor, where the estimate converges but its CI is
  not trustworthy).

  Both verdicts name **both** remedies, because the choice is a study-design decision and not a
  numerical one: Firth's penalised likelihood keeps a single model, while a **two-stage rule** —
  classify the sign-positive cases directly, model only the sign-negative remainder — is usually the
  clinically meaningful design for a pathognomonic sign, since a sign-positive patient is already
  diagnosed and the real question is what to do with everyone else.

- **Publisher markup in a `.bib` title is now caught before it renders** (`/manage-refs`,
  `check_bib_title_markup.py`; **detectors 58 → 59**). CrossRef ships titles containing markup —
  `<scp>WHO</scp>`, `<i>IDH</i>`, `<sub>1</sub>` — and a DOI-add stores them verbatim. Better BibTeX
  then either escapes the tags (`{$<$}scp{$>$}`) or strips them without restoring the space they
  occupied, and the reference list prints as garbage: *"The 2021 {$<$}scp{$>$}WHO{$<$}/scp{$>$}
  Classification…"*, *"Glioma Groups Based on 1p/19q,IDH, andTERTPromoter Mutations"*.

  Nothing caught this. `/verify-refs` checks whether a reference is **true**; `check_citation_keys`
  checks whether its key **resolves**; neither looks at the title as it will be **printed** — so the
  corruption survived every green gate and was found by eyeballing the rendered document, which is
  exactly the reading nobody gives a reference list. The new gate joins the `pre_submission_gate.sh`
  chain, so it runs where the others already run.

  `TITLE_FUSION` is deliberately narrow — it fires on an English function word or a comma welded to
  an acronym, not on any lowercase-then-uppercase transition — so `mRNA`, `hTERT`, `nnU-Net`, `pH`
  and `1,2-dichloroethane` do not fire. A gate is only worth having if a clean run means something.

- **`/find-cohort-gap` accepts your own cohort** (issue #69, requested by an external user).
  The skill used to start from a *named* database — NHIS, UK Biobank, and the handful of registries it
  knows about. Most researchers do not have one of those: they have an institutional registry, a
  single-centre EMR export, or a specialty cohort, described by a data dictionary nobody else has ever
  seen. Those users could not use the skill at all.

  **`scripts/build_cohort_profile.py`** is the input layer that lets them in. It reads a local codebook
  (`.csv` / `.tsv` / `.json` / `.md` / `.txt`, plus `.xlsx` via openpyxl and `.pdf` via `pdftotext`) and
  emits the same cohort profile the skill already consumes, so the intersection matrix, saturation scan
  and 6-pattern scoring are unchanged. A review, guideline, or preprint can be attached as domain
  context (`--context`), as a file or a URL. A `.csv` is auto-detected as a codebook (rows are
  variables) or a data export (the header row is the variable list).

  It is a script and not "the model reads the file" for a reason: asked to *summarise* a codebook, a
  language model will paraphrase a variable name, merge two that look alike, or invent one the cohort
  does not have — and the intersection matrix, the feasibility gate, and eventually the manuscript's
  Methods all inherit it. So variables are **enumerated, never generated**: copied verbatim, each
  carrying its provenance (`file:row`). What the codebook cannot state — sample size, follow-up
  duration, IRB status, prior publications — is emitted as `[UNKNOWN - ask the user]` rather than
  guessed, because a fabricated N does not merely sit there; it flows into the Phase 5 feasibility gate,
  which then passes for a reason unrelated to the cohort.

  Two structural facts *are* derivable from variable names, and both feed patterns the skill already
  scores: **serial / repeated-measure groups** (P1 Longitudinal Advantage) and **endpoint candidates**
  (P2 Endpoint Upgrade). Endpoints also get a cluster of their own (`outcome_endpoint`), assigned only
  when no other cluster claims the variable — otherwise the profile contradicted itself, listing
  `death_date` as "matched nothing, review it" in the cluster map while citing it as the P2 evidence
  two sections below. Each is reported with the variables that justify it, and a measurement is only
  called serial when it genuinely repeats. Cluster assignment records the keyword that triggered it, and
  a variable matching nothing is left `unclassified` rather than forced into a bucket.

- **Marked (tracked-changes) manuscript: a build step and a round-trip gate** (`/sync-submission` Phase 10,
  used by `/revise`). Every revision round must ship the revised paper with tracked changes against the
  version the reviewers saw. This was the last hand-done, unverified step of a submission: produced by
  clicking through Word's Compare, then "checked" by grepping the file for a sentence or two that ought to
  appear as an insertion — a check that passes even when Compare has dropped a paragraph, duplicated one, or
  split the revisions between two authors.

  - **`check_marked_manuscript.py`** (new detector; **57 → 58**) verifies the marked file the only way that
    is correct by construction: **accepting every revision must reproduce the revised manuscript exactly, and
    rejecting every revision must reproduce the original**. Verdicts: `MARKED_ACCEPT_MISMATCH`,
    `MARKED_REJECT_MISMATCH`, `MARKED_NO_REVISIONS`, `MARKED_AUTHOR_MIXED`, `MARKED_TABLE_LOSS`,
    `MARKED_BASE_TRACKED`. Stdlib only, so it audits a marked file produced by any means, on any platform.
  - **The gate is move-aware.** Word encodes relocated content as `w:moveFrom` / `w:moveTo`, *not* as
    `w:ins` / `w:del`. A verifier that knows only insert-and-delete reconstructs the original with the moved
    paragraph in it twice, and reports a perfectly good file as corrupt — a false alarm confirmed against a
    real, already-submitted marked manuscript. Resolution: `revised = unchanged + w:ins + w:moveTo`;
    `original = unchanged + w:delText + w:moveFrom`.
  - **`build_marked_manuscript.py`** drives Word's Compare from the command line through AppleScript
    (`author name` is passed to Compare, so revisions are attributed at source instead of by rewriting
    `w:author` afterwards), optionally injects continuous line numbers, and runs the gate on its own output.
    macOS + Word only, and therefore deliberately *not* a detector. `pandiff` and LibreOffice `--compare`
    remain forbidden: they corrupt OOXML tables and superscript runs.
  - Detector hygiene, encoded once: docx text must be read by walking exact `w:t` / `w:delText` elements. The
    regex `<w:t[^>]*>` also matches `<w:tbl>`, `<w:tc>` and `<w:tr>`, silently swallowing table markup as prose.

- **Every detector's JSON artifact now names the detector that wrote it.** A verification layer
  whose artifacts cannot be traced back to the check that produced them is only half a verification
  layer. The `qc/*.json` envelopes carried the findings but not the finding's author, so a consumer
  aggregating a project's `qc/` directory — an audit trail, a dashboard, a precision ledger — had to
  infer the detector from the **filename**, which is chosen freely at the call site (`--out qc/cs3.json`,
  `--out qc/v13_scope.json`). Two runs of one detector under different filenames read as two detectors;
  one run under an unexpected filename read as none.

  All 56 JSON-emitting detectors now emit `"detector": "<id>"` in the envelope (a purely additive key —
  every existing consumer keeps working), and **`scripts/check_detector_envelopes.py`** enforces it in
  CI, so a new detector cannot ship without it and a cloned one cannot keep its parent's name. It is a
  source check, not an execution check: detectors need fixtures and sometimes a network to run, but the
  key is a literal and can be verified without either.

### Fixed

- **Two precision defects in `/verify-refs`'s author cross-check**, found on the same clean
  bibliography and failing in opposite directions.

  *A false alarm.* The surname normalizer folds accents but not Unicode **dashes**, and its final
  filter keeps `[a-z\s-]` and deletes everything else — so a publisher-supplied U+2010 in a
  hyphenated surname was *deleted* rather than matched. CrossRef's `Foltyn‐Dumitru` normalized to
  `foltyndumitru` while the identical ASCII bib entry gave `foltyn-dumitru`, and the audit fired
  `MISMATCH` — its loudest verdict, the one that means *fabricated author* — on a correct reference.
  Unicode dash variants now fold to ASCII first.

  *A false pass, which is worse.* Better BibTeX brace-protects a hyphenated or particle surname so
  BibTeX will not re-split it (`author = {{Eckel-Passow}, Jeanette E. and {von Deimling}, Andreas}`).
  The corporate-author heuristic treated **any** brace as an organization and **skipped the author
  cross-check entirely** — the one thing the tool exists to do — reporting `UNVERIFIED — corporate
  author` and moving on. A brace now signals an organization only when the field carries an
  organizational keyword or has no personal-name structure at all; genuine collective authors
  (`{{KDIGO Working Group}}`) are still skipped.

- **The locale-inventory gate no longer trips over build artifacts.** It scanned `__pycache__`, so a
  compiled `.pyc` of a Korean-bearing module — produced simply by running a test that imports it — was
  reported as an un-inventoried Korean file: a CI failure on a git-ignored file that does not ship and
  has nothing to fix.

- **The JOSS paper's detector total is now gated.** `paper.md` states the size of the detector suite in its
  Summary but was absent from `DETECTOR_CLAIM_FILES`, so it would have silently disagreed with the software
  it describes the moment the suite grew. Added to `scripts/validate_catalog_consistency.py`.

## [5.20.1] - 2026-07-11

Audit-driven fixes (no behaviour change to skills): a real `/orchestrate --e2e` state-transition bug
(the pipeline halted at step 3 requiring a DOCX only rendered at step 7), 20 skills made routable from the
single entry point with a CI reachability gate, and a README plugin-count that had drifted from the
marketplace SSOT (now gated). No new skill or detector; **55 skills / 46 guidelines / 57 integrity detectors**.

### Fixed

- **Public-claim plugin-count gate** (audit F/§6.1, PR-3) — the README plugin-marketplace claim was not
  cross-checked against the SSOT, so it drifted: README said "eight `medsci-*` category plugins" while
  `.claude-plugin/marketplace.json` has nine (all `medsci-*`). Fixed to "nine", and extended
  `scripts/validate_catalog_consistency.py` to recompute the plugin count from the marketplace SSOT and
  assert the README claim (word or digit) matches — the same drift-guard the skills / guideline / detector
  counts already have. CI-enforced.

- **`/orchestrate` coherence** (audit F1 + F2) — two P0 findings from a repo-improvement audit.
  **F1 (E2E state transition):** the `--e2e` post-skill validation required `manuscript_final.docx` for
  `/write-paper`, but the DOCX is only rendered by `/manage-refs` at step 7, so an `--e2e` run halted at
  step 3 ("STOP, do not proceed"). `/write-paper` now validates only `manuscript.md`; the DOCX requirement
  stays on the `/manage-refs` row where it is produced. **F2 (reachability):** the hand-maintained
  "Available Skills" routing table listed 34 of 55 skills, so the single entry point could not route to the
  other 20 (most of the model-engineering lane: `architecture-zoo`, `preprocess-imaging`, `model-scaffold`,
  `radiomics-ml`, `model-validation`, `model-evaluation`, `mllm-eval`, `explainability`,
  `uncertainty-imaging`, `model-card`, plus `author-strategy`, `batch-cohort`, `cross-national`,
  `replicate-study`, `ma-scout`, `find-cohort-gap`, `design-ai-benchmarking`, `review-paper`,
  `polish-language`, `setup-medsci`). All 20 are added to the table, and a new
  `scripts/check_orchestrate_reachability.py` CI gate (with self-test) asserts every skill directory is
  routable from `/orchestrate` (or explicitly direct-only), so the drift cannot recur. No new skill or
  detector; catalog counts unchanged.

## [5.20.0] - 2026-07-11

Reviewer-arithmetic gates — five deterministic `self-review` detectors that recompute what a manuscript
already prints (an `n (%)` cell vs its column denominator; a subset-vs-parent-cohort P value; a row P from
2×2 counts via pure-stdlib Fisher / Pearson χ²; sensitivity/specificity denominators vs the reference-standard
category counts; median-difference parity), plus `/peer-review` request-type discipline (disclosure vs
computation) and impossibility-claim verification. Additive and backward-compatible;
**55 skills / 46 guidelines / 57 integrity detectors**.

### Changed

- **Reviewer request-type discipline + impossibility-claim verification** (`peer-review`, R2/R3/R4) — Phase 3
  now classifies every Major's ask as *disclosure* (the study already holds the answer — surfaces errors,
  costs nothing) vs *computation* (a number that does not yet exist — a new, unreviewed error surface); a
  computation request must justify that the existing tables cannot answer it and name its estimator, and a
  subset-vs-parent-cohort P value must never be requested (nested groups → invalid). Phase 4 item 14
  (verify-your-own-criticism) is widened to cover assertions of arithmetic/statistical *impossibility* from
  the manuscript's own summary statistics (restate as premise→conclusion + counterexample; a quantile/IQR
  does not constrain the tail, an agreement coefficient does not constrain the marginal), plus re-deriving a
  reviewer-requested new statistic before accepting it Resolved. The observational (`O10`) and
  diagnostic-accuracy (`D2`) domain probes gain the nested subset-vs-parent P-value invalidity rule (vendored
  byte-identical into `self-review`). Pairs with the D1/D4 deterministic gates and the `~/.claude/rules`
  R1/R5 updates. No new detector; catalog counts unchanged.

### Added

- **Reviewer-arithmetic detectors D1–D4** (`self-review`) — four deterministic gates promoted from a
  reviewer-side review cycle, each recomputing what a manuscript already prints:
  `check_nested_group_comparison.py` (`NESTED_GROUP_TEST` — a P-value table comparing an analysed subset
  against the parent cohort that contains it is an *invalid* test, not merely uninformative; the valid
  contrast is subset vs remainder), `check_reported_p_from_counts.py` (`P_NOT_REPRODUCIBLE` — rebuilds each
  2×2 row and recomputes Fisher / Pearson χ² ± Yates in pure stdlib, calibrates the family on rows that
  reproduce, and flags a reported P off by >1 order of magnitude under every family), `check_dta_denominators.py`
  (`DTA_DENOMINATOR_MISMATCH` / `STAGE_ROWSUM` — sensitivity/specificity denominators must equal the
  reference-standard category counts in the characteristics table; grand-total agreement is not accepted as
  passing), and `check_paired_difference_estimator.py` (`MEDIAN_PARITY` / `DEGENERATE_CI` / `ESTIMATOR_UNNAMED`
  — an odd-n integer-scale median cannot be non-integer, a zero-width CI, and an effect size with no named
  estimator). All run on first submissions, not only revisions; each ships a synthetic challenge card that runs
  in CI. Paired with rule updates R1 (requested-analysis correctness audit) and R5 (portal box-provenance) in
  `~/.claude/rules`. **Integrity detectors 53 → 57.**

- **Table-percentage gate** (`self-review`) — `check_table_percentages.py` recomputes every `n (p%)` table
  cell against its own column denominator (a `n = N` header, a Total row, or the column's counts summing)
  and flags a printed percentage off by more than 0.5 pp — the cheapest, zero-judgement arithmetic check,
  which routinely survives multiple review rounds because the error is present from the first submission
  (e.g. `79 (63%)` / `53 (37%)` under 132, true 59.8% / 40.2%). A column is treated as percentages only when
  a cell carries an explicit `%` or its parentheticals sum to ~100, so `mean (SD)` cells never false-fire.
  Sibling to `check_cohort_arithmetic`; challenge card runs in CI. **Integrity detectors 52 → 53.**

## [5.19.0] - 2026-07-11

Reviewer-safety + reporting-checklist batch — a PDF hidden-text / prompt-injection guard for
`/peer-review`, plus the TARGET (target-trial emulation) and REMARK (prognostic tumour-marker)
reporting checklists. Additive and backward-compatible; **55 skills / 46 guidelines / 52 integrity detectors**.

### Added

- **PDF hidden-text / prompt-injection guard** (`peer-review`) — a two-stage reviewer-safety tool for
  manuscripts that smuggle a review-steering instruction into the PDF where a human cannot see it but an
  LLM ingesting the text layer reads it (white-on-white text, sub-visible fonts, off-page glyphs, invisible
  render mode, or a document-metadata field; the injection attack first reported at scale in 2025).
  `scan_pdf_layers.py` (PyMuPDF) transcribes the PDF into a span manifest; the new stdlib-only detector
  `check_pdf_injection.py` audits the manifest, flags hidden runs and instruction-style phrases (HIGH inside
  a hidden run, LOW in visible prose), and emits the visible-only text (`--sanitize`) to feed an LLM instead
  of the raw PDF. A synthetic-manifest challenge card runs in CI without PyMuPDF. Guards the reviewer against
  an author's injection; it is unrelated to a venue's own canary text, and does not change the rule that the
  journal's LLM-use policy governs whether a confidential manuscript may be uploaded at all.
  **Integrity detectors 51 → 52.**

- **TARGET reporting checklist** (`check-reporting`) — Transparent Reporting of Observational Studies
  Emulating a Target Trial (Cashin, Hansford, Hernán et al. JAMA 2025;334(12):1084-1093). 21 items across
  6 sections, pairing the target-trial specification (item 6) with its emulation in the data (item 7) for
  each protocol element (eligibility, treatment strategies, assignment, time zero, outcome, causal
  contrast, assumptions, analysis). Routed via the study-type table + `target` / `targettrial` / `tte`
  aliases, with a TARGET critical-item floor (protocol-and-emulation specification, time-zero alignment /
  immortal-time control, causal estimand + identifying assumptions). Closes the design→reporting loop with
  the existing `/design-study` target-trial-emulation module. **Reporting guidelines 45 → 46.**

- **REMARK reporting checklist** (`check-reporting`) — REporting recommendations for tumour MARKer
  prognostic studies (McShane et al. Br J Cancer 2005; Altman et al. Explanation & Elaboration, PLoS
  Med 2012). 20 items across Introduction / Materials and Methods / Results / Discussion, vendored as a
  faithful own-words summary of item intent. Routed via the study-type table + `remark` / `tumormarker`
  aliases, with a REMARK critical-item floor (marker definition, cutpoint justification, multivariable
  adjustment for established prognostic variables, all-endpoint reporting). Fills the reporting-audit gap
  for prognostic tumor-marker / ctDNA-MRD studies (pair with STROBE for the observational-design items).
  **Reporting guidelines 44 → 45.**

## [5.18.0] - 2026-07-07

Reliability & workflow-integrity batch — a new deterministic gate for revision response letters, a
reframe/headline-change survivor scan, a pre-drafting backbone full-text gate, a skill-registry
consistency validator, plus AI-tool citation-framing guidance and the PneumoniaMNIST model-engineering
demo. Additive and backward-compatible; **55 skills / 44 guidelines / 51 integrity detectors**.

### Documentation

- **verify-refs guard hook — extended warn-only coverage (issue #14)**. The optional local PostToolUse
  hook (`~/.claude/hooks/verify-refs-guard.sh`, document-only in this repo) previously gated only
  `submission/` and `revision/R*/…circulation…` saves, so senior-mentor reply drafts and pre-submission
  `outgoing/` packages skipped the citation audit entirely. Documented (README + verify-refs manual-checkpoint
  guide) the added **warn-only** patterns — `*/outgoing/*.{docx,md}`, `*/8_Review_Comments/*/outgoing/*.{docx,md}`,
  and any `*/circulation/*.{docx,md}` — which surface a missing audit without blocking and never enforce,
  regardless of SSOT/migration state. Extends the local-only regression suite (`tests/test_phase1c_hooks.sh`)
  with a case asserting an `outgoing/` FABRICATED draft warns rather than blocks even under `MODE=enforce`.

- **AI-tool citation framing (`/academic-aio`)** — a use-class guide for citing an AI-assisted research
  tool safely (`references/ai_tool_citation_framing.md` + a Section 2.4a pointer). Verification/QA and
  analysis uses belong in a Software / Code-availability statement (citable, rigor-signalling); generative
  drafting belongs in the journal's AI-disclosure field, not a proud citation. Self-citation by a tool's
  author additionally requires a COI disclosure. States why a deterministic gate is deferred (use-class
  classification is high-FP without context). Motivated by the recurring "how do I cite an AI-QA tool
  under journal AI-hostility" question.

### Added

- **`make-figures` PPTX Mac-compatibility validator test** (`skills/make-figures/tests/test_pptx_mac_compat.py`).
  `validate_pptx_mac_compat.py` (TIFF media / `<a:sp3d>` bevel / `docProps/app.xml` slide-count mismatch /
  `srcRect` over-crop) previously shipped without a regression test. The test builds a clean deck
  (python-pptx, with a corrected app.xml slide count so the known `<Slides>0` bug does not false-fail),
  asserts it passes, then injects each of the four defect classes and asserts a `--strict` failure, plus a
  missing-input exit code and the WARN-tolerated (no app.xml) path. CI-wired. No skill-logic change.

- **Backbone full-text readiness gate for `/write-paper`** (`skills/write-paper/scripts/gate_backbone_fulltext.py`,
  issues #4 + #8). Phase 0 records a backbone article (`project.yaml::backbone_article`), but nothing forced
  its **full text** to be extracted before drafting — so the draft could follow an abstract. The gate resolves
  the backbone (via `project.yaml`, or `--backbone`, mapping citekey→DOI from `refs.bib`) and confirms an
  extracted Markdown full text exists and is substantial: `BACKBONE_FULLTEXT_MISSING` (nothing extracted),
  `BACKBONE_FULLTEXT_THIN` (below the full-text size floor — an abstract/landing page), or `BACKBONE_UNDECLARED`
  (warn). Wired into Phase 0 as a mandatory pre-drafting gate that routes to `/lit-sync` Phase 2.7 +
  `/fulltext-retrieval` `pdf_to_md.py`. A pre-draft **workflow prerequisite**, not a manuscript-integrity
  detector (named `gate_*`, not `check_*`) — **detector count unchanged (51)**. Ships
  `skills/write-paper/tests/test_backbone_fulltext.sh`.

- **Reframe / headline-change survivor scan** — `check_cross_artifact_stale.py` (sync-submission) gains
  opt-in `--retired-term` / `--old-value`. After a revision reframes a claim class or changes a headline
  number, stale copies survive in un-touched body paragraphs, figure/table legends, the supplement, and
  the response letter (which often claims the change was applied "throughout"). Given the retired
  vocabulary / superseded value(s), the gate scans the **body and every aux artifact** and flags each
  survivor (`retired_framing_survivor` / `stale_old_value`), automating the claim-site grep of
  `manuscript-versioning.md` §6.1 across all artifacts rather than a sample. Numeric survivors are
  digit-bounded (`1.72` never matches `11.723`). Additive — **no new detector, detector count unchanged**;
  extends the existing `test_cross_artifact_stale.sh` (11 cases). Demand-gated by recurrence across
  multiple projects (reframe drift + claim-site propagation).

- **Response-claim verification gate** (`skills/revise/scripts/check_response_claims.py`, integrity
  detectors **50 → 51**). A response-to-reviewers letter's *"we added the sentence '…'"* / *"we now
  cite Tariq et al. [15]"* is verified against the **revised manuscript body** — the source of truth,
  not the response prose. Fires `RESPONSE_QUOTE_UNVERIFIED` (a quoted added sentence absent from the
  body) and `RESPONSE_CITATION_UNVERIFIED` (an added citation whose token is nowhere in the body).
  Conservative by design: paraphrased edits and reviewer-comment blockquotes are not flagged, so a
  firing verdict is a real discrepancy. Wired into `/revise` (author, pre-send gate) and `/peer-review`
  (reviewer, verifying the author's claims), implementing the rule that a claimed-but-absent edit is a
  reputation-fatal class both a reviewer round and the authors can miss. Ships
  `skills/revise/tests/test_response_claims.sh`; `/revise` gains its first deterministic gate.

### Developer tooling

- **Skill-registry consistency validator** (`scripts/validate_capabilities.py`, CI-enforced, issue #15).
  Asserts that `capabilities.yml` (which adjudicates the overlapping domains) and every
  `skills/*/skill.yml` (`owner_domain`) agree: valid-YAML contracts, owner⇄skill agreement, no silent
  claimant of a declared domain, and resolvable `overlaps`/umbrella members. It found and fixed two
  latent drifts it now guards against — a malformed `render-pdf-doc/skill.yml` (an unquoted embedded
  colon that no prior check caught, because `validate_skill_contracts.py` parses skill.yml by regex and
  was never wired into CI) and `fulltext-retrieval` claiming the `literature_discovery` domain without
  appearing in its `overlaps`. Ships `tests/test_capabilities_validator.sh` (each drift class fails
  under `--strict`; the live repo is clean). Not an integrity detector — a repo validator, so the
  detector count is unchanged.
- **manage-refs designated canonical** (issue #16) — `skills/manage-refs/SKILL.md` now carries a
  canonical-source banner for the reference *workflow* (`verify-refs` remains canonical for bib
  *audit*), so external/user-scope notes point here rather than restating the "how" and drifting.

### Documentation

- **Demo 4 — PneumoniaMNIST CNN** (`demo/04_pneumoniamnist_cnn/`). A fourth live demo that runs the
  medical-AI **model-engineering lane** end to end on a public benchmark (PneumoniaMNIST, MedMNIST v2,
  CC BY 4.0) — the deep-learning counterpart to Demos 1–3 (classical stats / manuscript pipeline).
  Architecture choice → scaffold → data-stage/split/hygiene gates → 3-seed training → held-out evaluation
  (AUROC 0.964 ± 0.004; ensemble 0.969, 95% CI 0.956–0.980) → calibration (ECE 0.127) → Grad-CAM with
  Adebayo sanity checks → write-up. Every number is produced by an executed run (results manifest is the
  single source of truth); gate outputs (split-leakage, training-hygiene, explainability-report) are all
  clean; references were verified with `/verify-refs`. Tooling demonstration, not a clinical claim. README
  "Live Demos" now lists four pipelines.

## [5.17.0] - 2026-07-04

Model-engineering produce-side depth — completion. Deployment safety plus the final wiring and candidate
items of the [produce-side depth roadmap](docs/roadmap_model_engineering_depth.md): a new
`uncertainty-imaging` skill + `check_uncertainty_reporting` gate (uncertainty quantification / OOD /
selective prediction for a deployment-framed model), an MLOps wiring reference for `model-scaffold`, and
an `architecture-zoo` graph-neural-net family card (brain connectomes) that closes the last candidate
gap. The six-item roadmap **and** its candidate list are now complete. Additive and backward-compatible;
skills **54 → 55**, integrity detectors **49 → 50**. PRs #279–#281.

### Documentation

- **`architecture-zoo` graph-neural-net family card** (`references/graph.md`) — closes the last candidate
  gap in the [model-engineering coverage map](docs/method_coverage_map.md). Covers GNNs for brain
  **connectomes** and **population graphs** — GCN, GraphSAGE, GAT, GIN, and the brain-specific
  **BrainGNN** — each with its source paper, when-to-use, medical use, PyTorch Geometric / DGL reference
  implementation, and validation setup, plus the connectome-specific traps (subject-level split, ComBat
  site-harmonisation leakage, p ≫ n, interpretability-is-not-proof). States the boundary honestly:
  `model-scaffold` has no graph template, so integrate PyTorch Geometric / DGL directly while the lane's
  subject-level gates (`model-validation`, `radiomics-ml`, `explainability`, `uncertainty-imaging`,
  `check-reporting`) still apply. Reference-only — no skill, no detector, no count change. PR #281.
- **MLOps wiring reference** (`model-scaffold/references/mlops_guide.md`, Item 6 — the final item of the
  [model-engineering produce-side depth roadmap](docs/roadmap_model_engineering_depth.md)). A
  reproducibility-safe **wiring + reporting** reference — experiment tracking (W&B / MLflow /
  TensorBoard), config / data / environment versioning, pipeline orchestration via the framework's own
  (nnU-Net / MONAI bundles), CI-for-ML (gate the network-free properties, never a real training run),
  and an MLOps reporting checklist for TRIPOD+AI / CLAIM. Deliberately **not** a training-loop,
  hyperparameter-search, or experiment-tracking reimplementation — it points to the frameworks and never
  replaces them (the ROADMAP out-of-scope clause). Cross-linked from `model-scaffold` Phase 5 and
  `training_guide.md`. No skill, no detector, no count change. PR #280.

### Added

- **`uncertainty-imaging` skill + `check_uncertainty_reporting` detector** (Item 5 of the
  [model-engineering produce-side depth roadmap](docs/roadmap_model_engineering_depth.md), deployment
  safety). Designs and audits the uncertainty-quantification / out-of-distribution / selective-prediction
  layer of a deployment-framed medical-imaging model, so a clinical-use claim carries calibrated per-case
  uncertainty (MC-dropout / deep ensemble / conformal / Bayesian), an OOD guard validated on a held-out
  OOD set, an abstention rule at a pre-specified operating point, and calibration checked under
  distribution shift. Emits an uncertainty manifest and a stdlib-only deterministic gate with seven
  verdicts: `POINT_PREDICTION_NO_UNCERTAINTY`, `CONFORMAL_NO_COVERAGE_VALIDATION`, `OOD_NO_HELDOUT_SET`
  (Major); `ENSEMBLE_NOT_INDEPENDENT`, `MCDROPOUT_DISABLED_AT_INFERENCE`, `SELECTIVE_NO_TARGET`,
  `NO_CALIBRATION_UNDER_SHIFT` (Minor). Complements `model-evaluation`'s executed calibration/subgroup
  metrics at the reporting-spec level. Ships a `references/uncertainty_guide.md` (conformal coverage
  validation, ensemble independence, MC-dropout-active-at-inference, OOD held-out evaluation, selective
  prediction, calibration-under-shift, TRIPOD+AI / DECIDE-AI reporting), a network-free challenge card,
  and a CI-wired regression test. Integrates MAPIE / captum / OOD scorers by reference; never reimplements
  them or touches real patient data. Skills **54 → 55**, integrity detectors **49 → 50**
  (`reporting_compliance` family). PR #279.

## [5.16.0] - 2026-07-04

Model-engineering produce-side depth, clinical fine-tuning focus — Items 3–4 of the
[produce-side depth roadmap](docs/roadmap_model_engineering_depth.md). A new `radiomics-ml` skill +
`check_radiomics_ml` detector for the most common solo-doable clinical-ML workflow (radiomics /
tabular features → any classical learner → a clinical outcome, no GPU), broadened to the full
classical/statistical-ML family with a learner-agnostic gate; and a `model-scaffold` fine-tuning
mode (`--task finetune` + `--from-pretrained`) that adapts a pretrained backbone on collected clinical
data with a frozen→unfrozen schedule, discriminative learning rates, and a pretrained-weight provenance
record (a `PRETRAINED_PROVENANCE_MISSING` verdict added to the existing `check_training_hygiene` — no
new detector). Plus a ML/DL method coverage map. Additive and backward-compatible; skills **53 → 54**,
integrity detectors **48 → 49**. PRs #276–#278.

### Changed

- **`radiomics-ml` broadened to the full classical / statistical-ML family** (not just RF / XGBoost).
  The skill description, triggers, workflow, and `references/radiomics_ml_guide.md` now enumerate
  penalised regression (LASSO / ridge / elastic-net), SVM, k-NN, naive Bayes, LDA/QDA, trees, bagging,
  boosting (XGBoost / LightGBM / CatBoost / HistGBM / AdaBoost), shallow MLP, stacked ensembles, plus
  unsupervised reduction/clustering — and make explicit that the `check_radiomics_ml` gate is
  **learner-agnostic** (it audits the pipeline, not the algorithm). No code or count change.

### Documentation

- **ML / DL method coverage map** (`docs/method_coverage_map.md`, linked from README and `ROADMAP.md`).
  A single matrix showing every common ML/DL method family — imaging deep learning (CNN / transformer /
  segmentation / detection / foundation-SAM / diffusion / SSL / multimodal), the full classical/tabular
  family, and LLM/MLLM — mapped to the skills that select, produce, validate, interpret, and report it,
  with the integrate-not-reimplement boundary and open candidate gaps (graph neural nets, Item 4
  fine-tuning) stated explicitly.

### Added

- **`model-scaffold` fine-tuning mode** (Item 4 of the
  [model-engineering produce-side depth roadmap](docs/roadmap_model_engineering_depth.md), clinical
  fine-tuning focus). Extends the scaffold from train-from-scratch to the target user's real workflow —
  **fine-tune a pretrained backbone on collected clinical data**. New `--task finetune` +
  `--from-pretrained <source>` emits a leakage-safe transfer-learning repo with a frozen→unfrozen
  schedule, discriminative learning rates, and a pretrained-weight **provenance record**
  (`PRETRAINED.md` + a `config.yaml` `pretrained:` block). The existing `check_training_hygiene` gate
  gains one additive verdict — `PRETRAINED_PROVENANCE_MISSING` (Minor) — that fires when a repo loads
  pretrained weights (`pretrained=True` / `from_pretrained`) but records no provenance; the scaffold
  passes by construction, a hand-rolled fine-tune with no recorded checkpoint fails. Ships a new
  `references/finetuning_guide.md` (freeze schedule, MedSAM/SAM adapter fine-tuning, train-only
  diffusion augmentation with the pretraining-set-contamination leakage warning), plus challenge +
  regression-test coverage for the finetune task and the provenance verdict. Reuses
  `check_training_hygiene` + `check_preprocessing_leakage` — **no new skill, no new detector**
  (skills stay **54**, integrity detectors stay **49**). PR #278.
- **`radiomics-ml` skill + `check_radiomics_ml` detector** (Item 3 of the
  [model-engineering produce-side depth roadmap](docs/roadmap_model_engineering_depth.md), clinical
  fine-tuning focus). Produces and audits a radiomics / tabular clinical-ML study — features → random
  forest / XGBoost / regularised logistic → a clinical outcome, the most common solo-doable clinical-ML
  workflow (no GPU, no engineer). Emits a pipeline manifest and a stdlib-only deterministic gate with
  six verdicts: `NO_NESTED_CV`, `HIGH_DIM_LOW_EVENTS`, `SELECTION_OUTSIDE_CV` (Major);
  `NO_FEATURE_STABILITY`, `NO_CALIBRATION`, `NO_EXTERNAL_VALIDATION` (Minor). Complements the prose
  `check_cv_leakage` audit at the pipeline-spec level. Ships a `references/radiomics_ml_guide.md`
  (pyradiomics/IBSI settings, nested-CV skeleton, ICC stability, calibration + decision curve,
  CLEAR/TRIPOD+AI/PROBAST-AI reporting), a network-free challenge card, and a CI-wired regression test.
  Integrates scikit-learn / xgboost / pyradiomics by reference; never reimplements them or touches real
  patient data. Skills **53 → 54**, integrity detectors **48 → 49** (`data_preparation` family). PR #276.

## [5.15.0] - 2026-07-03

Model-engineering produce-side depth. Two new skills that *produce* the leakage-safe, rigorously
reported artifacts the review lane previously only audited — `preprocess-imaging` (data-stage
leakage) and `explainability` (interpretability rigor) — Items 1–2 of the
[produce-side depth roadmap](docs/roadmap_model_engineering_depth.md), plus a multi-host README/About
refresh, copy-paste citation ergonomics, a release-cadence policy, and a real-project precision fix.
Skills **51 → 53**, integrity detectors **46 → 48**. PRs #271–#275.

### Added

- **`explainability` skill + `check_explainability_report` detector** (Item 2 of the
  [model-engineering produce-side depth roadmap](docs/roadmap_model_engineering_depth.md)). Produces and
  audits the interpretability analysis of a medical-imaging model (Grad-CAM / attention-rollout /
  saliency / integrated-gradients) so it clears the rigor bar reviewers expect: it *produces* what
  `self-review` previously only audited. Emits an explainability-report manifest and a stdlib-only
  deterministic gate with six verdicts: `SALIENCY_AS_VALIDATION`, `NO_SANITY_CHECK`,
  `NO_LOCALIZATION_METRIC` (Major); `INSUFFICIENT_SANITY`, `CHERRY_PICKED_EXAMPLES`, `MISSING_METHOD`
  (Minor). Enforces Adebayo (2018) model- and data-randomisation sanity checks, a quantitative
  localisation metric (IoU / pointing game / Dice vs ground truth) over a cohort, and attribution-not-
  validation framing. Ships a modality-aware `references/explainability_guide.md`, a network-free
  challenge card, and a CI-wired regression test. Integrates captum / pytorch-grad-cam by reference;
  never reimplements them or touches real patient data. Skills **52 → 53**, integrity detectors
  **47 → 48** (`reporting_compliance` family; the family's `MEDSCI_AUDIT.md` row also regained the
  previously-dropped `check_figure_citation`). PR #275.

- **`preprocess-imaging` skill + `check_preprocessing_leakage` detector** (Item 1 of the
  [model-engineering produce-side depth roadmap](docs/roadmap_model_engineering_depth.md)). Designs and
  audits the data-preparation stage of a medical-imaging model *before* `model-scaffold` builds the
  training repo, extending the split-leakage moat upstream to preprocessing. Emits a declarative
  preprocessing manifest (transforms with `type`/`fit_scope`/`stage` + patient-level split) and a
  stdlib-only deterministic gate with six verdicts: `NORMALIZATION_LEAKAGE`, `PREPROCESS_BEFORE_SPLIT`,
  `PATIENT_CROSS_SPLIT` (Major); `AUGMENTATION_ON_EVAL`, `UNSPECIFIED_FIT_SCOPE`, `MISSING_SEED`
  (Minor). A per-sample transform is correctly treated as leakage-free even before the split. Ships a
  modality-aware `references/preprocessing_guide.md`, a network-free challenge card, and a CI-wired
  regression test. Integrates MONAI / TorchIO by reference; never reimplements them or touches real
  patient data. Skills **51 → 52**, integrity detectors **46 → 47** (`data_preparation` family). PR #274.

### Fixed

- **`self-review` scope-coherence: enumerated-defect-label false positive.** `check_scope_coherence`
  no longer fires `CROSS_SECTIONAL_PROGNOSTIC` on a sentence that *names* the anti-pattern as a defect
  in a list (e.g. "… flags … an unsupported prognostic claim in a cross-sectional study, a fabricated
  citation, …"), which the existing meta-document guard missed. A new `ANTIPATTERN_LABEL` guard treats
  a prognostic/surveillance token preceded by a defect adjective (unsupported/unwarranted/…) or
  followed by overclaim/overreach/fallacy/error as a label, not a claim — high-precision, no genuine
  overclaim suppressed. Field-harvested from real-project precision tracking; regression test added.
  No detector count change (46).

### Documentation

- **Model-engineering produce-side depth roadmap** (`docs/roadmap_model_engineering_depth.md`,
  linked from `ROADMAP.md` § Research throughput). Sequences the three thin produce stages of the
  in-scope model-engineering lane — imaging data pipeline + data-stage leakage, interpretability/
  explainability production, uncertainty/OOD reporting — each as a rigor gate with a challenge card,
  never a training-framework reimplementation, released as one batch. Working checklist for the
  next expansion cycle.

- **README: by-stage skill index, multi-host framing, and star history.** A scannable "by research
  stage" grouping of all 51 skills sits above the full table; a Star History chart is added; and the
  About section now states the toolkit runs on all four verified Agent Skills hosts (Claude Code,
  Codex, Cursor, GitHub Copilot) rather than Claude Code alone. The GitHub repo description and topics
  were broadened to match (leads with "Agent Skills"; adds `codex`/`cursor` topics).

- **Copy-paste citation ergonomics** (README § Citation). Adds a ready-to-adapt Methods/Acknowledgement
  sentence (with a version placeholder), BibTeX for the software (Zenodo) and the design preprint,
  a note that the concept DOI resolves to the latest release, and a pointer to the "Used in research"
  issue → `docs/citations.md`. Lowers the friction to legitimately cite the toolkit.

- **Release-cadence policy** (`docs/maintainer_workflow.md` § Release cadence). Codifies that
  `[Unreleased]` is a staging area a release drains, that a minor release must be a coherent
  user-noticeable batch (not internal symmetry-completion), and a guardrail of at most ~one minor
  release per week under additive work — bundle otherwise; only a broken-install/CI/correctness/security
  patch ships immediately. Content creation (merge when ready, demand-driven) and releasing
  (batch-driven) are decoupled. ROADMAP "honest versioning" now links it; the release checklist
  clarifies draining `[Unreleased]` in place.

## [5.14.0] - 2026-07-02

Research enablement: a fourth executable-depth produce-guide and completion of the worked-exemplar
set. The `analyze-stats` **calibration** guide (probe S7 — the apparent-slope-of-1.00 tell →
bootstrap optimism correction) extends the produce-guide line to agreement / diagnostic-accuracy /
survival / calibration; the `write-paper` **RCT/CONSORT** exemplar completes the five-pillar
reporting-guideline worked-exemplar set (STROBE / STARD / TRIPOD+AI·CLAIM / PRISMA / CONSORT),
raising worked exemplars to 5/10 paper types. No detectors added; **46 integrity detectors
unchanged**. PRs #267–#268.

### Added

- **`write-paper` RCT worked IMRAD structure exemplars (CONSORT 2010).** A fifth study-type structure model (`exemplar_{methods,results,discussion}/rct_consort.md`) completes the five-pillar reporting-guideline set of worked exemplars — STROBE (observational), STARD (diagnostic), TRIPOD+AI/CLAIM (AI validation), PRISMA (systematic review), and now **CONSORT (randomized trial)**. Paragraph-order skeletons anchored to CONSORT 2010 critical items (registration, sequence generation + allocation concealment + blinding as three distinct items, the single pre-specified primary, ITT, a reconciling flow diagram), naming the RCT-specific traps (allocation-concealment-vs-blinding conflation, ITT-vs-per-protocol primary, baseline p-values, clinical-vs-statistical significance vs the MCID); cross-linked to the `rct_trial` domain-probes. Raises worked exemplars 4/10 → 5/10 paper types. SKILL.md Phase 3/Results/Discussion pointers + three exemplar READMEs updated. No detectors, no count change.

- **`analyze-stats` prediction-model calibration methodology guide (`analysis_guides/calibration.md`).** Executable-depth enablement paired with probe **S7** (calibration beyond discrimination): the **apparent calibration slope of a maximum-likelihood fit is exactly 1.00 by construction** (the in-sample tell), so the guide produces the **bootstrap optimism-corrected** slope/intercept (Harrell/Steyerberg) instead; Van Calster's calibration hierarchy (report weak calibration — intercept + slope — plus a flexible curve, not decile bins); scaled Brier; and why **Hosmer–Lemeshow is deprecated** (dropped from the logistic required-outputs in favour of slope/intercept + flexible plot). Survival-at-a-horizon calibration noted. Core claims verified (apparent slope 1.00 → optimism-corrected 0.75 on an overfit model; scaled Brier; calibration-in-the-large). `survival_prognostic` probe S7 gains a "Produce the fix" back-link; SKILL.md loads the guide before generating prediction-model code. No detectors, no count change.

## [5.13.0] - 2026-07-02

Executable-depth research enablement. Two `analyze-stats` produce-guides complete the
core-analysis arc — **agreement → diagnostic-accuracy → survival** — so each of the three
most common analysis families now *produces* the estimand its review domain-probe flags the
absence of (not only checks for it). No detectors added; **46 integrity detectors unchanged**.
PRs #265–#266.

### Added

- **`analyze-stats` survival / time-to-event methodology guide (`analysis_guides/survival.md`).** Executable-depth enablement paired with the `survival_prognostic` domain-probes: **competing risks first** — a naive 1−KM overestimates cumulative incidence, so the guide produces the Aalen–Johansen / Fine–Gray CIF and names cause-specific (etiologic) vs subdistribution (absolute-risk) for the right question (produce-side of probes **S3/S8**); the PH check → **RMST** fallback under non-proportional hazards; reverse-KM median follow-up + C-index-variant selection (**S6**). Core numerical claims (1−KM overestimation vs CIF, reverse-KM, RMST-as-area) verified. `survival_prognostic` probe S3 gains a "Produce the fix" back-link; SKILL.md loads the guide before generating survival code. Completes the executable-depth arc (agreement → diagnostic-accuracy → survival). No detectors, no count change.

- **`analyze-stats` diagnostic-accuracy / reader-study methodology guide (`analysis_guides/diagnostic_accuracy.md`).** Executable-depth enablement paired with the `diagnostic_accuracy` domain-probes: every metric with a CI on a stated per-patient/per-lesion unit (Wilson for proportions, DeLong/bootstrap for AUC); the **confidence-weighted trap** — a strictly-monotone (call × confidence) encoding check that catches the folded-score bug plus the **unweighted-baseline AUC** beside the weighted primary (produce-side of probe **D9**); paired DeLong vs MRMC for reader-generalising claims; a **per-stratum admissibility table** that tests each stratum against a stated AUC rule (produce-side of **D10**); and one-scale-per-comparison (**D11**). All code snippets verified runnable. `diagnostic_accuracy` probe D9 gains a "Produce the fix" back-link; analyze-stats SKILL.md loads the guide before generating diagnostic-accuracy code. No detectors, no count change.

## [5.12.0] - 2026-07-02

Research-enablement continuation plus a feature-selection leakage detector. **Integrity
detectors 45 → 46** (`check_cv_leakage`). Two produce-side artifacts on the research-throughput
frontier — `write-paper` meta-analysis worked IMRAD exemplars (worked structures 3/10 → 4/10
paper types) and an `analyze-stats` agreement/reliability guide paired with self-review probe
O18 — plus a code-label estimand reconcile and a peer-review salvage-reframe sub-rule.
PRs #261–#264.

### Added

- **`write-paper` meta-analysis worked IMRAD structure exemplars (PRISMA 2020).** A fourth
  study-type structure model completes the trio in `exemplar_methods/`, `exemplar_results/`,
  and `exemplar_discussion/` (`meta_analysis_prisma.md`) — paragraph-order skeletons stating
  what each Methods/Results/Discussion paragraph must establish for a systematic review with
  quantitative synthesis, anchored to PRISMA 2020 critical items (verbatim search strategy,
  reconciling flow diagram, per-study risk of bias, protocol/registration) and cross-linked to
  the `sr_ma` domain-probes. Enablement (produce, not check): raises worked exemplars from 3/10
  to 4/10 paper types. SKILL.md Phase 3/Results/Discussion pointers and the three exemplar
  READMEs updated; `paper_types/meta_analysis.md` now points to the skeletons. No detectors,
  no count change.

- **`analyze-stats` inter-rater agreement/reliability methodology guide (`analysis_guides/agreement_reliability.md`).** Executable-depth enablement paired with self-review probe O18: the pseudoreplication trap for clustered/repeated measurements + the pseudoreplication-safe per-subject-aggregation and subject-random-effect ICC code (produce, not only flag), ICC model/type selection, and the agreement-vs-reliability distinction. Wired into the skill's agreement section and cross-linked from O18.

- **`check_claim_artifact` gains `--scripts` + `PRIMARY_LABEL_CODE_DRIFT` (advisory; no count change).** When the manuscript asserts a SINGLE primary model/analysis but an analysis script annotates a model as `co-primary`, the code label (a third SSOT) has drifted — reconcile it with the declared estimand. Advisory, since code comments can lag.

- **`check_cv_leakage` (self-review, `data_preparation`; integrity detectors 45 → 46).** `CV_SELECTION_LEAKAGE` (Major): for a classifier / NLP / tabular manuscript, a data-driven selection step (feature selection, log-odds / univariate filtering, vocabulary construction, a threshold) that co-occurs with cross-validation without any fold-nesting disclosure ('within each fold', 'nested CV') — if the selection was fit on the full dataset the CV metric is optimistically inflated. Distinct from patient-vs-image split leakage.
- **peer-review §1C contribution-gate: salvage-reframe sub-rule.** A fix that *narrows* a claim to survive a construct/validity flaw is Reject-leaning, not an encourage-major-revision, when novelty/importance is already weak — a shrunk contribution is the product, not addressable-in-revision.

## [5.11.0] - 2026-07-02

Review-harvest inbox goal-mode processing: field-observed self-review / peer-review
gaps promoted into detectors, domain-probes, and precision fixes. **Integrity
detectors 42 → 45** (`check_rounded_delta`, `check_figure_citation`,
`check_emphasis_density`); seven review domain-probes added (sr_ma P18/P19,
observational O18, diagnostic_accuracy D9/D10/D11, ai_overclaiming AO7); one new
supplement-hygiene verdict; five precision fixes on already-shipped detectors.

### Added

- **`check_supplement_hygiene` gains `SUPP_PARTICIPANT_PII_TIE` (Major; no count change).** Flags a reader/participant identity — a pseudonym (`R`+hex) or a named participant — tied to an INDIVIDUAL response on one line of a reader-facing / public supplement (a re-identifiable datum). A byline / roster line with only aggregate responses does not fire. Motivated by a preprint supplement that linked a reader pseudonym to a real name + individual response.

- **Four review domain-probes (no detector-count change).** Canonical in `peer-review`, vendored into `self-review`: **diagnostic_accuracy D9** (confidence-weighted reader study needs an unweighted-baseline AUC + monotonic-encoding check), **D10** (a "no stratum met threshold X" claim vs a per-stratum AUC+CI table that does meet X), **D11** (mixed-normalisation values in one comparison column), and **ai_overclaiming AO7** (a "within/comparable-to X variability" claim whose benchmark X was never quantified). SKILL.md probe ranges updated (D1–D11, AO0–AO7).

- **Three review domain-probes (no detector-count change).** Canonical in `peer-review`, vendored byte-identical into `self-review`: **sr_ma P18** (train-vs-validation pool integrity — an apparent/in-sample estimate smuggled into the "validation" pool), **sr_ma P19** (reviewer-side included-study cell audit — metric-type identity, self-eligibility contradiction, CI provenance), and **observational_confounding O18** (pseudoreplication in multi-rater agreement / reader studies — pooled pairwise vs per-subject). SKILL.md probe ranges/counts updated.

- **`check_emphasis_density`** (self-review `style_review`, humanize Pattern 25; integrity detectors 44 → 45) — `EMPHASIS_OVERUSE` (Minor): inline italic-emphasis density over a per-1000-word threshold (after an allowlist of statistical symbols, Latin phrases, and gene/species terms) is an LLM typographic tell. Bold is NOT counted so a Nature/npj bold run-in subheading is never flagged; whole-clause italics escalate. humanize gains Pattern 25 pointing at it.
- **Two self-review deterministic detectors (integrity detectors 42 → 44).** Each
  ships positive+negative fixtures, a regression test wired into `validate.yml` +
  `skill.yml`, and a family mapping.
  - **`check_rounded_delta`** (`numerical_cohort`, Phase 2.5a) — `ROUNDED_DELTA_MISMATCH`
    (Minor): a stated difference must equal the subtraction of its two displayed
    component values at the same precision. Catches "AUC 0.70 vs 0.73 … difference 0.02"
    (a shown gap of 0.03). A higher-precision component pair with a lower-precision delta
    is the legitimate unrounded case and is not flagged.
  - **`check_figure_citation`** (`reporting_compliance`, Phase 2.5d) — `FIGURE_ORPHAN` /
    `TABLE_ORPHAN` (Minor): every captioned `Figure N.` / `Table N.` must be cited at
    least once in the body. The markdown-stage, no-build counterpart to `check_xref`'s
    DOCX-stage `UNCITED`.

### Fixed

- **Four self-review detector precision fixes (no count change, no schema change).**
  Field-observed false positives / masking on already-shipped gates, each with a
  positive+negative regression fixture:
  - `check_binning_consistency` (`DERIVED_DEF_DRIFT`) no longer fires on a legitimately
    **parallel sensitivity cohort** — the SAME derivation rule expressed against a
    different dataframe-receiver object (`v0['col']` vs `lenient_cohort['col']`). The
    clause-set now compares on column+operator+rhs; the Python `df['col']` subscript is
    dropped from each atom, matching the existing base-R `df$col` normalisation.
  - `check_null_calibration` (`CONFIRM_NULL_NO_MDE`) is now **per-claim-site**: a
    power/CI caveat co-located with one null no longer masks a bare "equivalence within
    the bound" claim in a different region. Each unqualified claim site is evaluated on
    its own neighbourhood.
  - `check_scope_coherence` (`CROSS_SECTIONAL_PROGNOSTIC`) no longer fires on a
    **meta-document** — a QC/methods/detector paper (or review) whose SUBJECT is the
    anti-pattern and that NAMES it rather than committing it.
  - `check_classical_style` (`INBODY_AI_DISCLOSURE`) no longer fires on a paper whose
    SUBJECT is AI-use disclosure and that carries disclosure phrasing as an object of
    study. All meta-document guards are kept tight (they require the meta-framing
    structure) so a genuine overclaim / in-body disclosure is never suppressed.
  - `check_claim_artifact` (`ESTIMAND_DRIFT`) now anchors on explicit structured
    prereg fields (`primary_exposure` / `primary_outcome` / `primary_estimand` / …)
    when the pre-registration is a `project.yaml` / form, rather than on a free-text
    paragraph or a `# PRIMARY — locked` YAML comment. Structured extraction reads the
    raw (line-based) prereg; a moderate overlap against a structured field is a soft
    `ESTIMAND_CONFIRM` (advisory) instead of a false `ESTIMAND_DRIFT`. Removes the
    false drift flag on an estimand already reconciled to the registration.

## [5.10.0] - 2026-07-01

Figures enablement — the make-figures **render-test layer** grows from 4 to **10** tested,
deterministic generators, substantively closing the suite's self-identified weakest area.
No count change (the render layer is a generator, not a detector).

### Added

- **make-figures render layer extended to MRMC ROC, Manhattan, and clinical timeline.**
  Three more deterministic generators in `scripts/render_core_figures.py`, each with
  `assert_structure` invariants: **MRMC ROC** (a curve per reader + the reader-averaged
  curve + chance diagonal + averaged-AUC annotation — reader studies), **Manhattan**
  (point scatter + named significance-threshold line + −log10(p) axis — agnostic
  many-exposure scans), and **clinical timeline** (time baseline + an event marker/label at
  each event + time axis — case reports). The render-regression challenge now renders all
  **ten** figures. `imaging_panel` is documented as staying prose-only by design (it
  composes real images, not computed numbers). Detector count unchanged. Only `imaging_panel`
  now remains a prose-only exemplar.

- **make-figures render layer extended to forest, Bland–Altman, and confusion matrix.**
  Building on the v5.9.0 tested-generator layer (KM / ROC / calibration / decision-curve),
  `scripts/render_core_figures.py` gains three more deterministic generators from
  already-computed inputs, each with `assert_structure` load-bearing-element invariants:
  **forest** (per-study CI whisker for every study + null reference line + pooled diamond +
  study/pooled row labels), **Bland–Altman** (difference scatter + bias line + 95% limits of
  agreement at bias ± 1.96·SD + difference-vs-mean axes), and **confusion matrix** (matrix
  image + every cell annotated + Predicted/Actual axes). The render-regression challenge now
  renders all **seven** figures from the synthetic fixture and confirms the gate fails on a
  non-monotonic KM curve *and* a non-square confusion matrix. Detector count unchanged
  (render layer is a generator, not a `check_*` detector). Continues closing the suite's
  self-identified weakest area; forest / Bland–Altman / confusion move from prose-only
  exemplars to tested generators.

## [5.9.2] - 2026-07-01

Maintenance patch (no count change).

### Fixed

- **`gen_distribution_manifest.py` no longer scans `installers/.logs/`.** The gitignored,
  per-machine install logs `install.py` writes there were picked up by the manifest scan,
  so running `install.py` locally and regenerating would add a machine-specific log path
  to the inventory (local `--check` drift, or an accidental committed log path). `.logs` is
  added to the generator's excluded directory names; a regression assertion in
  `installers/tests/test_distribution_manifest.py` (CI-wired) locks it — a stray
  `installers/.logs/*.txt` is excluded and a normal installer file is still included.

## [5.9.1] - 2026-07-01

Documentation + connector-transparency patch (no count change; behaviour unchanged by
default). Adds a research-connector registry and clarifies that the toolkit's external
APIs are keyless public services, plus an adjacent-not-competing note vs hosted
AI-for-science workbenches.

### Added

- **Research-connector registry (`docs/connectors.md`).** A declarative registry of the
  external research APIs the skills call — PubMed / NCBI E-utilities, CrossRef, OpenAlex
  (verification) and Unpaywall / Europe PMC / PMC (open-access full text) — with what uses
  each, its keyless/legitimate boundary, and a plain "how you authorize" guide. The
  clinical-manuscript analogue of a curated connector panel: **keyless public APIs (nothing
  to paste in the common case)**, a `.claude/settings.json` permission-allowlist snippet as
  the "call these domains without asking each time" mechanism, and an explicit boundary
  (metadata + open access only; no paywalled-publisher scraping, no institution-auth
  connectors, no omics/cheminformatics databases). Linked from the README intro.

### Changed

- **Optional contact-email / NCBI key via environment (never required).**
  `fetch_oa.py --email` now falls back to `MEDSCI_CONTACT_EMAIL` (and errors clearly if a
  contact email is set nowhere — Unpaywall requires one). `verify_refs.py` E-utilities
  calls now send NCBI-recommended `tool`/`email` courtesy params and honour an optional
  `NCBI_API_KEY` (raising the PubMed rate limit from 3 → 10 req/s); absent the key the calls
  stay keyless, so behaviour is unchanged by default. All verify-refs + fulltext-retrieval
  tests pass.

- **Competitive positioning — adjacent-not-competing note for hosted AI-for-science
  workbenches (Claude Science).** `docs/competitive_positioning.md` gains an "Adjacent
  platforms" section clarifying that a hosted bench/omics workbench (Anthropic's Claude
  Science: genomics / single-cell / proteomics / structural biology / cheminformatics,
  biological-database connectors, compute/HPC, BioNeMo) is **complementary**, not
  competing: different scientific domain (clinical manuscript / observational epidemiology
  vs bench/omics), different core value (EQUATOR reporting-guideline compliance +
  submission / peer-review + drift control, which such a workbench does not cover), and the
  same Agent Skills primitive — so a clinical-manuscript skill-set sits alongside it, and
  stays open-source (MIT), host-portable, and citable where a hosted product is
  subscription-gated.

## [5.9.0] - 2026-07-01

A **research-enablement pivot**. After six reporting-guideline lanes and exhaustion of the
scored reverse-engineering backlog (G50–G68), this release rebalances the suite toward
*producing* research rather than only checking it: a tested figure-render layer, design-time
artifacts (target-trial emulation + DAG adjustment sets), prediction-model sample sizing, a
prospective/deployment-monitoring model-validation seam, default-on clinical-utility output,
a less-defensive review layer, and a roadmap / gap-scoring correction. Skill, detector, and
reporting-guideline counts are unchanged (51 / 42 / 44).

### Changed

- **Hygiene + self-review SKILL.md slimming.**
  - `installers/install.py` now writes timestamped install logs to a gitignored
    `installers/.logs/` directory and prunes to the most recent 10, instead of accumulating
    them in the repo root (21 had piled up). `.gitignore` updated.
  - `self-review` SKILL.md (1399 lines) starts honouring the maintainer's own
    reference-split rule: the observational-only **Phase 2.5e (Confounding Completeness,
    ~84 lines)** is extracted to `references/phases/confounding_completeness.md` and loaded
    on demand. A non-observational review (RCT, diagnostic-accuracy, SR/MA, descriptive) no
    longer carries the procedure inline. The stub preserves the trigger, the deterministic
    `check_confounding_completeness.py --strict` gate, and the research-type gating; full
    content is byte-preserved in the reference. SKILL.md 1399 → 1344 lines; the same
    pattern can be extended to the other research-type-gated phases.
### Added

- **model-validation — prospective evaluation & deployment-monitoring seam (DECIDE-AI).**
  The validation tier ladder stopped at "multi-site / prospective external" and the lane
  never routed to DECIDE-AI, leaving no design step for the clinical-use horizon a model is
  headed toward. `references/validation_design.md` §2b now extends the ladder past
  retrospective external to **silent / shadow deployment → prospective comparative (impact)
  RCT → live deployment + post-deployment monitoring** (performance / dataset-shift /
  calibration drift with recalibration-or-withdrawal triggers + ongoing subgroup audit). A
  new SKILL **Phase 6.5** covers this horizon and scopes claims to the tier reached, and
  Phase 7 reporting now routes prospective/live evaluation to **DECIDE-AI** (early clinical
  evaluation) or **CONSORT-AI / SPIRIT-AI** in addition to CLAIM 2024 / TRIPOD+AI / STARD-AI.
- **calc-sample-size — Riley prediction-model sample size (Tests 12–13).** For a clinical
  prediction / medical-AI model, EPV-10 (Tests 9/11) is outdated and reviewer-vulnerable.
  New `references/prediction_model_sample_size.md` + decision-tree branch + Tests 12
  (development via `pmsampsize` — the four Riley criteria) and 13 (external validation via
  `pmvalsampsize` — target CI widths for the C-statistic, calibration slope, O:E, and net
  benefit). Test 9's EPV note now scopes EPV-10 to single-predictor hypothesis tests and
  routes prediction models to Riley. (TRIPOD+AI-aligned; directly in the radiology-AI lane.)

### Changed

- **analyze-stats — clinical utility is a default output, not an optional add-on.** The
  primary-effect output contract now *requires*, by default: absolute risk + risk
  difference + NNT/NNH (baseline stated) for OR/HR/RR outcomes; the IQR-anchored
  real-world-translation line for continuous outcomes; and a **decision-curve / net-benefit
  pass** (plus incremental net benefit / NRI / IDI over the established clinical model) for
  prediction / classification models — not AUC alone. Moves the headline from
  "significant / X-fold" toward "changes this decision by this much."
- **design-study — target-trial-emulation module + DAG adjustment-set scaffold
  (design-time enablement frontier).** `design-study` told authors to "emulate a target
  trial" and "pre-specify the adjustment set from a DAG" but shipped **no scaffold** (it
  had no `references/` or `scripts/`). Two design artifacts now make that buildable:
  - `references/target_trial_emulation.md` — the seven-component target-trial protocol
    table (eligibility, treatment strategies, assignment, **time zero**, outcome, causal
    contrast, analysis plan) with its data emulation, plus the immortal-time / prevalent-
    user / confounding-by-indication guards, new-user + active-comparator design, the
    grace-period clone-censor-weight pattern, ITT-vs-per-protocol estimand choice, and
    negative-control falsification. Turns an association into a defensible causal contrast
    — the highest-leverage point for the suite's NHIS/registry/RWE work.
  - `references/dag_adjustment.md` + `scripts/adjustment_set_helper.py` — DAG-based
    confounder selection. The helper deterministically classifies each proposed covariate
    by DAG role (reachability only) and flags `MEDIATOR_ADJUSTMENT`,
    `DESCENDANT_ADJUSTMENT`, `COLLIDER_ADJUSTMENT`, and `CONFOUNDER_OMITTED`, proposing a
    candidate backdoor set; it defers the **minimal** sufficient set to dagitty (a
    validated tool) and never ships a homegrown d-separation solver. A confounder is
    defined soundly as a common cause with an **X-free** path to the outcome, so an
    instrument-like `A→X→Y` ancestor is not mis-flagged. A network-free challenge
    (`scripts/adjustment_set_challenge/`, wired into `skill.yml` validation) locks the
    classification on canonical confounder / mediator / M-bias / instrument DAGs.
  - Detector catalogue count unchanged (the helper is a design-time generator, validated
    by its challenge, not a manuscript-integrity `check_*` detector).
- **make-figures — runnable, tested render layer for the four core clinical figures
  (research-enablement frontier).** The suite's self-identified weakest area had prose
  figure anatomy but **no deterministic render test for any data plot**. New
  `scripts/render_core_figures.py` turns the Kaplan–Meier, ROC, calibration, and
  decision-curve exemplar anatomies into deterministic matplotlib generators that take
  already-computed inputs (the statistical estimation stays in `/analyze-stats`; the
  render layer never recomputes a number) and `assert_structure` introspects the actual
  matplotlib artists to verify each figure's load-bearing elements — KM number-at-risk
  table + monotonic survival + no extrapolation past follow-up; ROC chance diagonal +
  AUC annotation + operating point; calibration identity line + slope/intercept;
  decision-curve treat-all/treat-none references + net-benefit axis. A network-free
  render-regression challenge (`scripts/render_core_figures_challenge/`, wired into
  `skill.yml` validation) renders all four from a synthetic fixture and confirms the
  structural gate fails on a malformed figure (non-monotonic KM). Closes the
  defense/enablement asymmetry (integrity detectors had challenge fixtures; the figure
  generators had none).
### Changed

- **Less-defensive QC trims (precision over volume).** The over-defensiveness in the
  review layer is structural/volume-driven, not per-detector; three trims reduce
  manufactured findings without weakening genuine gates:
  - `self-review` panel template no longer imposes a per-reviewer comment **quota**
    ("Produce 4–8 major / 4–10 minor"). Reviewers now report **only genuine threats** —
    zero majors is a valid outcome for a clean manuscript — while the Step 3.5
    lens-diversity gate still enforces axis *coverage* (so under-reporting is caught).
  - `check_claim_artifact.py`: `ESTIMAND_DRIFT` (fuzzy prereg↔manuscript token overlap)
    is **downgraded from Major to advisory** — the docs already require manual
    confirmation against the registration, and a P0 that needs hand-confirmation is not
    a P0. A bare honest **manuscript-stage analytical-decision disclosure** (which
    estimand-provenance guidance *recommends writing*) is now a separate advisory
    `PRIMARY_DISCLOSURE_NOTE`, not `PRIMARY_REASSIGNED`; only **explicit** post-hoc
    re-designation remains Major. New regression case locks the advisory behaviour.
  - `check_framework_naming.py`: `VAGUE_GUIDANCE` is now **context-gated** to sentences
    with a reporting cue (report/reporting/checklist/EQUATOR), so method-level wording
    like "external validation following recent best-practice recommendations" no longer
    false-fires. New FP-guard regression case added.
- **Direction pivot — research throughput over compliance breadth.** After six
  consecutive reporting-guideline lanes (v5.3.0–v5.8.0) and exhaustion of the
  scored reverse-engineering backlog (G50–G68), the roadmap and gap-scoring model
  are rebalanced toward research-enablement:
  - `ROADMAP.md` near-term priorities are restructured into a **Research
    throughput (frontier)** tier — figure & artifact generation, executable
    analysis depth, design-time enablement — above a demoted **Sustaining
    (reliability floor)** tier. New reporting-guideline lanes are now explicitly
    *maintenance mode*.
  - `reverse_engineer/gap_register.md` scoring gains a **leverage** multiplier
    (`score = impact × frequency × deficit × leverage`; check-only 1.0 / ships an
    artifact 1.5 / unblocks a pre-data-collection decision 2.0) plus a
    **saturation tax** (deficit − 2 for an Nth genre lane that only adds a
    presence-check). Corrects the structural bias toward checkable-over-generative
    gaps. The G50–G68 batch is marked `closed`.
  - `README.md` model-lane wording corrected: `model-scaffold` ships a minimal
    runnable default model for a forward-pass smoke test and *integrates* MONAI /
    nnU-Net / timm / torchvision for production models, rather than the prior
    "never reimplements" claim (the scaffold emits a smoke-test U-Net/CNN).

## [5.8.0] - 2026-06-30

### Added

- **Qualitative-research reporting lane (SRQR + COREQ + QL1–QL8 domain probes).** A new
  study-genre lane for **qualitative studies** — interviews, focus groups, ethnography,
  grounded theory, phenomenology, document analysis:
  - `check-reporting` gains two checklists — **SRQR** (`references/checklists/SRQR.md`, alias
    `srqr` / `qualitative`; 21 items, all qualitative approaches; O'Brien et al. *Acad Med*
    2014, DOI 10.1097/ACM.0000000000000388) and **COREQ** (`COREQ.md`, alias `coreq`; 32 items
    in 3 domains, interviews/focus groups specifically; Tong et al. *Int J Qual Health Care*
    2007, DOI 10.1093/intqhc/mzm042). Both are **in-house faithful summaries** of the item
    intents (paraphrased — both standards are ©, no Creative Commons licence). Brings the
    reporting-guideline catalogue to **44**.
  - `peer-review` / `self-review` gain a vendored, byte-identical **`qualitative_research.md`**
    domain probe (**QL1–QL8**): approach/paradigm fit, researcher **reflexivity**, purposive
    sampling & saturation (a small sample is not a flaw), data-collection rigour, **analysis
    transparency / audit trail** (not "themes emerged"), **trustworthiness** (credibility/
    dependability/confirmability/transferability — *not* statistical validity), findings
    grounded in quoted data, and ethics/interpretive scope. Includes the **bidirectional
    calibration trap** — neither demand quantitative yardsticks (power, "representative" sample,
    statistical generalizability, κ-as-truth) of qualitative work, nor let it claim causal/
    prevalence/population over-reach. Review domain-probe modules: 21 → **22**.
  - Wired into check-reporting study-type routing and the peer-review / self-review trigger tables.
- Counts: 51 skills / 42 detectors / **44 reporting guidelines** / **22 review domain-probe modules**.

## [5.7.0] - 2026-06-30

### Added

- **Scoping-review reporting lane (PRISMA-ScR + SC1–SC8 domain probes).** A new study-genre
  lane for **scoping reviews** — reviews that *map* the breadth/nature of evidence, clarify
  concepts, and identify gaps (distinct from a systematic review, which answers a focused
  effectiveness/accuracy question):
  - `check-reporting` gains a **PRISMA-ScR** checklist (`references/checklists/PRISMA_ScR.md`,
    aliases `prisma-scr` / `scoping review` / `scoping`) — an **in-house faithful summary** of
    the 20 essential + 2 optional reporting items (paraphrased intents, not verbatim; the
    PRISMA-ScR statement is ©ACP with no Creative Commons licence), citing Tricco et al.
    *Ann Intern Med* 2018 (DOI 10.7326/M18-0850). Brings the reporting-guideline catalogue to **42**.
  - `peer-review` / `self-review` gain a vendored, byte-identical **`scoping_review.md`** domain
    probe (**SC1–SC8**): scoping fit & PCC framing, a-priori protocol (OSF, not PROSPERO),
    eligibility by concept, search comprehensiveness, selection & data **charting**, the
    **asymmetric critical-appraisal calibration** (a scoping review need not assess risk of bias —
    do not flag its absence, but do flag GRADE-style certainty claimed without appraisal),
    **synthesis-is-mapping-not-pooling** (no pooled effect/accuracy estimate from a scoping
    review), and interpretation/gaps/terminology. Review domain-probe modules: 20 → **21**.
  - Wired into the `make-figures` figure map (PRISMA-ScR flow diagram), check-reporting study-type
    routing, and the peer-review / self-review trigger tables.
- Counts: 51 skills / 42 detectors / **42 reporting guidelines** / **21 review domain-probe modules**.

## [5.6.0] - 2026-06-30

### Added

- **`/self-review` editorial-impression counterweight (the "ceiling" pass).** The gate stack
  minimizes *rejection-for-cause* (the floor) and several gates do so by *adding* hedges,
  caveats, disclosures, and audit trails — with no opposing force, iterated self-review
  monotonically over-defends until an editor reads the manuscript as a rebuttal letter. New
  deterministic detector `check_editorial_impression.py` (self-review category **L** /
  Phase 2.5g) reads the manuscript as a whole and recommends **SUBTRACTION** — REMOVE / MOVE /
  TIGHTEN:
  - `HEDGE_DENSITY` (defensive-caveat tokens per 1,000 narrative words), `HEDGE_REPEAT` (one
    caveat motif repeated across body + Abstract), `AUDIT_IN_BODY` (SHA / commit / unit-test /
    post-lock / manifest / seed in the Intro/Results/Discussion narrative → Methods/supplement),
    `LIMITATIONS_VOLUME` (a long enumerated Limitations list), `ABSTRACT_CAVEAT_LOAD` (caveat
    clauses crowding the Abstract), and `BURIED_DEFENSE` (a strong numeric robustness/sensitivity
    result hidden in Limitations/supplement → promote to Results — the inverse of the
    scope-coherence gate).
  - **Advisory and non-blocking** — every finding is Minor with a REMOVE/MOVE/TIGHTEN `action`;
    the gate emits no Major and exits 0 even under `--strict`. Thresholds are tunable. Conservative
    by construction (fires only on an explicit, locatable signal); ships positive + negative
    challenge-card fixtures and a CI-wired regression test.
  - SKILL.md gains a **two-objective frame** (quality = min rejection-for-cause AND max
    editorial-championing), a first-class **Editorial-Impression Risks (REMOVE/MOVE/TIGHTEN)**
    report block kept separate from the additive Anticipated-Comments axis, and a `--panel`
    **handling-editor desk-impression** persona plus an editor-synthesis defensiveness lens
    symmetric to the contribution lens.
- Counts: 51 skills / **42 detectors** / 41 reporting guidelines / 20 review domain-probe modules.

## [5.5.0] - 2026-06-29

### Added

- **Survey-research lane (CROSS / CHERRIES).** The third study-genre lane of the autonomous
  reverse-engineer cycle (after CHEERS and RECORD), filling the most common uncovered manuscript type:
  - `check-reporting/references/checklists/CROSS.md` — an in-house faithful summary of the CROSS 2021
    reportable elements (paraphrased item intents; CROSS is ©SGIM, so not reproduced verbatim — DOI
    cited) integrating the CC-BY CHERRIES internet-survey items. Routed via the study-type table +
    `cross` alias. **Reporting guidelines 40 → 41.**
  - `peer-review` + `self-review` `domain-probes/survey_research.md` (SV1–SV8; vendored byte-identical,
    review domain-probe modules 19 → 20): sampling-frame representativeness, sampling method +
    sample-size justification, response rate (defined denominator) + non-response bias, instrument
    development/validation/reliability, CHERRIES e-survey specifics, question design,
    weighting/denominators/missingness, generalisability/ethics.
- Counts: 51 skills / 41 detectors / **41 reporting guidelines** / 20 review domain-probe modules.

## [5.4.0] - 2026-06-29

### Added

- **RECORD lane — routinely-collected / registry / claims / EHR observational reporting.** The second
  lane of the autonomous reverse-engineer cycle (after CHEERS), chosen by the same CC-BY-cleanliness
  logic and directly relevant to the suite's heavy NHIS/KNHANES/health-checkup-DB cohort emphasis:
  - `check-reporting/references/checklists/RECORD.md` — faithful 13-item RECORD summary (base STROBE +
    RECORD extension; RECORD-PE noted for drug studies; CC BY 4.0, Benchimol et al. *PLoS Med* 2015).
    Routed via the study-type table + `record` alias. **Reporting guidelines 39 → 40.**
  - `peer-review` + `self-review` `domain-probes/record_routinely_collected_data.md` (RD1–RD8; vendored
    byte-identical, review domain-probe modules 18 → 19): database fitness-for-purpose, phenotype
    code-lists & validation, data linkage & linkage-quality, participant-selection flow incl.
    data-quality filtering, misclassification, informative missingness, unmeasured confounding +
    immortal-time/prevalent-user (RECORD-PE), eligibility drift + code/protocol availability.
- Counts: 51 skills / 41 detectors / **40 reporting guidelines** / 19 review domain-probe modules.

## [5.3.0] - 2026-06-29

### Added

- **Health economic evaluation lane (CHEERS 2022).** A new study-genre lane filling the suite's
  largest open reporting gap (absent from medsci-skills and from competing toolkits), surfaced by an
  EQUATOR-grounded competitor + reporting-standard research scan:
  - `check-reporting/references/checklists/CHEERS_2022.md` — faithful 28-item CHEERS 2022 summary
    (CC BY 4.0, Husereau et al. *BMJ* 2022); routed via the study-type table + `cheers`/`cheers2022`
    aliases. **Reporting guidelines 38 → 39.**
  - `peer-review` + `self-review` `domain-probes/health_economic_evaluation.md` (HE1–HE8; vendored
    byte-identical, review domain-probe modules 17 → 18): comparator/perspective, time-horizon &
    discounting, effectiveness source + QALY valuation, costing/currency/price-year, model structure
    + validation, deterministic and **probabilistic** uncertainty (PSA/CEAC, not a point ICER), ICER
    vs a stated willingness-to-pay threshold + dominance, equity/generalisability/funding-COI.
  - `analyze-stats` `analysis_guides/health_economic_evaluation.md` + SKILL entry — ICER/net-benefit,
    decision-analytic models (Markov/DES), PSA → plane + CEAC, `heemod`/`dampack`/`BCEA`.
- Counts: 51 skills / 41 detectors / **39 reporting guidelines** / 18 review domain-probe modules.

## [5.2.0] - 2026-06-29

### Added

- **Model-engineering lane — reference grounding for three thin lane skills.** New load-on-demand
  reference docs, grounded in named public standards (cross-checked against the repo's own
  check-reporting SSOT, e.g. STARD-AI *Nat Med* 2025, PROBAST+AI *BMJ* 2025), wired into each
  SKILL.md:
  - `model-validation/references/validation_design.md` — data-leakage taxonomy, internal vs
    genuine-external validation, comparator/variance/test-set sizing, CLAIM 2024 / TRIPOD+AI /
    STARD-AI reporting map.
  - `mllm-eval/references/evaluation_axes.md` — clinical-efficacy metrics beyond n-gram overlap,
    faithfulness/hallucination, benchmark contamination, prompt-sensitivity, answer-matching,
    reader study.
  - `model-evaluation/references/metric_selection_grounding.md` — Metrics Reloaded task-fingerprint
    principle, calibration vs discrimination, disaggregated reporting, CLAIM 2024 reporting fit.

### Fixed

- **`model-evaluation` metric-reporting gate false positive.** `check_metric_reporting.py`'s
  `iou_crit` proximity window used `[^.\n]`, so a hard-wrapped IoU match criterion (the IoU and its
  threshold on different physical lines) was undetectable and the gate fired a spurious
  `DETECTION_METRIC_MISSING` on a legitimately formatted detection report. Changed to `[^.]`
  (newline-tolerant, still period-bounded); locked by a load-bearing `det_good_wrapped` regression
  case plus `det_no_iou` detection-branch coverage in the CI-wired `metric_reporting_challenge`.

- Counts unchanged (**51 skills / 41 detectors / 38 reporting guidelines / 14 probes**); reference
  docs are uncounted.

## [5.1.0] - 2026-06-29

### Added

- **`/lit-sync` fulltext-retrieval phase (opt-in, owner-only).** A new Phase 2.7 orchestrates two
  complementary full-text routes and reconciles them into `references/fulltext_retrieval.json`:
  disk open-access PDFs by delegating to the `/fulltext-retrieval` engine, and in-library
  Zotero-native PDFs via a user-run `find_available_pdf.js` snippet that triggers Zotero's own
  `addAvailablePDF` / `addAvailablePDFs` — reusing the user's own proxy / OpenURL configuration, so
  no credentials or institutional identifiers ever enter the skill. Adds a DOI/PMID/Title worklist
  entry mode.
- **`fetch_oa.py` (the single authored open-access cascade) enhancements:** TSV/CSV/Markdown-table +
  `Title` worklist parsing; direct **arXiv** resolution for `10.48550/arXiv.*` DOIs (new/old-style,
  version suffixes); a `--report retrieval_report.json` (schema_version + per-DOI
  `status`/`source`/`title_match` tri-state); and pure, offline-testable report/title-match helpers
  with a best-effort `pdftotext` title cross-check that **flags** mislabeled PDFs without
  auto-rejecting them. New network-free `fetch_oa_report_challenge` wired into CI.

### Changed

- **DRY consolidation.** `/search-lit` Phase 5 now delegates full-text retrieval to
  `/fulltext-retrieval` and drops the duplicated inline open-access code (and the unsafe Sci-Hub
  env-var wording) — the OA cascade now lives in exactly one authored place.
- Counts unchanged (**51 skills / 41 detectors / 38 reporting guidelines / 14 probes**).

## [5.0.0] - 2026-06-28

### Changed

- **v5.0.0 — storefront repositioning for the medical-AI model-engineering lane.** A material
  distribution change, not a label bump: the model-engineering lane (built additively across
  v4.x Phases 1–4 plus the Phase 5 breadth below) now has its own storefront home and the repo's
  identity is widened to cover it.
  - **New `model_engineering` storefront category** ("Model Engineering & Validation") and
    **`medsci-modeling` marketplace plugin**, carved out of "Data & Study Design" (`medsci-data`).
    The 6 lane skills — `architecture-zoo`, `model-scaffold`, `model-validation`, `model-card`,
    `model-evaluation`, `mllm-eval` — now group under their own catalog filter and installable
    plugin (`/plugin` now lists nine category plugins). Both catalog generators
    (`gen_skills_catalog_json.py` category mapping/order, `gen_marketplace_json.py` plugin
    name/description) and their self-tests cover the new category.
  - **README + ROADMAP repositioned to the end-to-end identity**: MedSci Skills is an end-to-end
    research tool for physician and medical-engineering researchers to design → scaffold →
    validate → publish — for the clinical manuscript and the medical-AI model alike. "Clinical AI
    model research engineering is in scope" is now explicit, while "not a general AI-scientist
    platform" (and not a diagnostic tool or autonomous author) is kept; the lane **integrates**
    MONAI / nnU-Net and never reimplements them or runs anything autonomously.
  - Counts unchanged (**51 skills / 41 detectors / 38 reporting guidelines**); CI stays torch-free.

### Added

- **Medical-AI model-engineering lane — Phase 5 (build-lane breadth).** Expands the existing
  `/model-scaffold` and `/architecture-zoo` skills; no new skills/detectors/probes (counts
  unchanged: 51 skills / 41 detectors / 38 guidelines), torch-free CI.
  - **`/model-scaffold` now generates 5 task types** (was segmentation-only): `--task`
    **segmentation** (U-Net), **classification** (small multi-label CNN; swap in a `timm`
    backbone), **detection** (torchvision Faster R-CNN + FPN), **synthesis** (Pix2Pix U-Net
    generator + PatchGAN), **ssl** (SimCLR encoder + projection head, NT-Xent). Every task keeps
    the reproducibility guarantees by construction — the patient-level seed-locked split is
    task-independent, and each emitted `train.py` / `evaluate.py` passes `check_training_hygiene`
    (all RNGs seeded, cuDNN deterministic, train-only loader, `eval()` + `no_grad()`). The
    challenge + regression test now verify all 5 tasks (split + hygiene + valid Python, network-free).
  - **`/architecture-zoo` adds the `detection.md` and `synthesis.md` family cards** (R-CNN family /
    Faster R-CNN+FPN / Mask R-CNN / RetinaNet / YOLO / DETR; Pix2Pix / CycleGAN / SPADE / diffusion
    / VAE / fastMRI), each with the source paper, when-to-use, medical use, reference implementation,
    validation setup, and matching scaffold template; the decision-tree index now routes to them.

## [4.11.0] - 2026-06-28

### Added

- **find-journal:** acceptance-feasibility axis. A Phase 2.5 pre-flight
  (`assess_acceptance_readiness.py`, deterministic + reproducible challenge card)
  scans a manuscript for design-ceiling / unfixable-defect / importance-risk /
  claim-mismatch signals and a ceiling verdict (advisory risk band, never a
  probability). Adds two-axis ranking (scope fit × acceptance feasibility) with
  explicit mismatch surfacing, an `Acceptance Signals` profile schema
  (`references/acceptance_signals_schema.md`, populated for European Radiology, AJR,
  KJR, RYAI, Investigative Radiology), a reject-fallback cascade plan, and a
  desk-reject vs post-review distinction in Post-Rejection Mode. Helper named
  `assess_*` (not a detector-catalog member); counts unchanged (additive). (#215)
- **Medical-AI model-engineering lane — Phase 1 (validation MVP).** First slice of the v5.0
  "design → scaffold → validate → publish medical-AI model research" lane, led by the
  validation/reporting half (the build/scaffold half lands in a later phase). Clinician-anchored,
  torch-free, additive.
  - **New skill `/model-validation`** (Layer D, advisory + deterministic audit) — design or audit
    the clinical-validation study for an engineer-built medical-imaging model (segmentation /
    classification / detection): patient-level split disjointness + the data-leakage taxonomy,
    tuning-on-test, internal vs genuine external validation, comparator design, single-run vs
    multi-seed variance, task-correct metric selection (Metrics Reloaded), test-set sizing handoff
    to `/calc-sample-size`, and CLAIM 2024 / TRIPOD+AI / STARD-AI reporting fit. Integrates with
    MONAI / nnU-Net — does not replace them. Skills 45 → 46.
  - **New reviewer domain-probe `model_development.md` (MD0–MD8)** (`/peer-review` + `/self-review`,
    vendored byte-identical) — partition/leakage mechanics, tuning/threshold/model-selection on the
    test set, the internal-vs-external-validation conflation, seed/run variance, test-set event
    count, metric selection, reproducibility/provenance, and reference-standard/label quality.
    Domain-probe modules 15 → 16. Grounded in the leakage taxonomy (Kapoor & Narayanan, *Patterns*
    2023), Varoquaux & Cheplygina (*npj Digit Med* 2022), CLAIM 2024, and Metrics Reloaded
    (Maier-Hein & Reinke et al., *Nat Methods* 2024).
  - **New deterministic detector `check_split_leakage.py`** (`/model-validation`) — *proves* (by set
    arithmetic on the emitted `split_assignment.csv`, not heuristics) that no patient crosses
    train/val/test, and that the split records a reproducible seed. Verdicts `PATIENT_OVERLAP`
    (Major), `MISSING_SEED` (Major), `SINGLE_PARTITION` (Minor); train/validation/holdout synonyms
    collapse so a labelling variant never trips it. Stdlib-only, network-free, with a reproducible
    challenge card + CI-wired regression test. Integrity detectors 36 → 37.
- **Medical-AI model-engineering lane — Phase 2 (build/scaffold).** Completes the
  build → validate chain in-repo, staged after Phase 1's verification contract. Clinician-anchored
  (a *reproducible research scaffold generator that integrates MONAI / nnU-Net*, not a replacement);
  default CI stays torch-free.
  - **New skill `/model-scaffold`** (Layer B) — `scaffold.py` stamps out a runnable PyTorch
    segmentation training repo (configurable U-Net, `dataset.py`, `losses.py`, `train.py`,
    `evaluate.py`, `config.yaml`, `requirements.txt`, `REPRODUCIBILITY.md`, `methods_stub.md`) with
    the reproducibility guarantees baked in **by construction**: a patient-level seed-locked split
    written as an auditable artifact (`splits/split_assignment.csv` + `split_seed.txt`, disjoint by
    construction so it clears `/model-validation`'s `check_split_leakage`), all-RNG seeding + cuDNN
    determinism, a train-only loader, and `eval()` + `no_grad()` inference. No fabricated numbers
    (`[VERIFY]` placeholders). Skills 46 → 47.
  - **New deterministic detector `check_training_hygiene.py`** (`/model-scaffold`) — conservative
    AST linter (flag-not-prove, the training-code analogue of `check_generated_code`): all RNGs
    seeded, cuDNN deterministic, `eval()` + `no_grad()` inference, no training on a non-train split.
    Verdicts `SEED_INCOMPLETE` / `MISSING_EVAL_MODE` / `TRAIN_ON_NONTRAIN_SPLIT` (Major),
    `CUDNN_NONDETERMINISTIC` / `EVAL_SHUFFLE` (Minor). Integrity detectors 37 → 38.
  - **`scaffold_challenge`** executes the build → validate chain network-free: scaffold a repo →
    deterministic split matches the frozen expected + is patient-disjoint (proven inline) → passes
    `check_training_hygiene` → a **self-skipping** torch tier (forward shape + gradients + reproducible
    loss when torch is installed; `SKIP`, never CI coverage of runnability, when absent).
  - **New skill `/architecture-zoo`** (Layer D, advisory) — the *choose* front end of the lane: maps a
    research question (task + modality / dimensionality + labelled-data scale + class imbalance) to a
    **paper-grounded** architecture shortlist via a decision tree, then per-architecture cards with core
    idea, when-to-use, medical-imaging use, reference implementation, the typical validation/experiment
    setup, and the matching `/model-scaffold` template. Seeds the classification (ResNet / DenseNet /
    EfficientNet / Inception / ViT / Swin / DeiT), segmentation (U-Net / 3-D U-Net / V-Net / Attention
    & Residual U-Net / nnU-Net / SegResNet / Swin-UNETR / Mask R-CNN), and foundation/SSL (SAM / MedSAM /
    MedSAM2 / TotalSegmentator / SegVol / BiomedCLIP / DINO / MAE / SimCLR / MoCo) families. Every
    recommendation names its source paper; it teaches archetypes, not a live SOTA leaderboard. Skills
    47 → 48.
- **Medical-AI model-engineering lane — Phase 3 (reporting).** The documentation seam of the lane,
  after validation (Phase 1) and build (Phase 2). Clinician-anchored, additive.
  - **New skill `/model-card`** (Layer C) — generate the documentation an engineer-built model must
    carry: a **Model Card** (Mitchell et al., *FAccT* 2019), a dataset **Datasheet** (Gebru et al.,
    *CACM* 2021), and a **METRIC-informed data-quality pass** (Schwabe et al., *npj Digit Med* 2024),
    filled from user-supplied facts — never fabricated (intended use, out-of-scope use, training data,
    per-subgroup performance, caveats, provenance, consent, licence). Templates live in `references/`
    and are **uncounted** (documentation standards, not clinical reporting checklists — same treatment
    as `appraisal_tools/METRICS.md`), so `reporting_guidelines` is unchanged. Skills 48 → 49.
  - **New deterministic detector `check_model_card_complete.py`** (`/model-card`) — verifies every
    required Model Card / Datasheet section is **present and non-empty** (not missing, not an unfilled
    `[NEEDS INPUT]` placeholder). Verdicts `MISSING_SECTION` / `EMPTY_REQUIRED_SECTION` (Major); a
    presence check, not a truth check. `reporting_compliance` family. Integrity detectors 38 → 39.
  - Reproducible challenge (`check_model_card_complete_challenge`, synthetic complete + incomplete
    fixtures) + CI-wired regression test (8 cases).
- **Medical-AI model-engineering lane — Phase 4 (evaluation + MLLM).** The evaluation half, completing
  the choose → build → validate → evaluate → report chain. Clinician-anchored, additive.
  - **New skill `/model-evaluation`** (Layer B) — compute task-correct held-out metrics for a trained
    imaging model (segmentation: Dice + a boundary metric HD95/NSD per structure; classification: AUROC
    + AUPRC + sensitivity/specificity with bootstrap CIs at the deployment prevalence; detection: FROC/
    mAP with a stated IoU criterion) + calibration + subgroup slices, emitting a per-case table for
    `/analyze-stats`. `check_metric_reporting.py` gates the metric choice against Metrics Reloaded
    (Maier-Hein & Reinke et al., *Nat Methods* 2024) / CLAIM 2024 (`PIXEL_ACCURACY_SEG` /
    `NO_BOUNDARY_METRIC` / `ACCURACY_ONLY` / `DETECTION_METRIC_MISSING` / `CI_MISSING`). data_preparation
    family. Skills 49 → 50.
  - **New skill `/mllm-eval`** (Layer B) — a model-agnostic (closed API or open weights) evaluation
    harness for an LLM/MLLM on a clinical task (report generation, VQA, extraction): adjudicated
    reference standard, clinical-efficacy metrics (RadGraph-F1 / CheXbert-F1 beyond BLEU/ROUGE),
    faithfulness/hallucination, pretraining-contamination, prompt sensitivity, reader study.
    `check_mllm_eval_completeness.py` gates the plan (`NGRAM_ONLY` / `FAITHFULNESS_MISSING` /
    `REFERENCE_STANDARD_MISSING` / `CONTAMINATION_UNADDRESSED` / `READER_STUDY_MISSING` / …).
    reporting_compliance family. Skills 50 → 51.
  - **New reviewer domain-probe `mllm_evaluation.md` (ME0–ME8)** (`/peer-review` + `/self-review`,
    vendored byte-identical) — the reviewer-side audit of an LLM/MLLM clinical evaluation. Grounded in
    RadCliQ (Yu et al., *Patterns* 2023), RadGraph (Jain et al., NeurIPS 2021), CheXbert (Smit et al.
    2020), MedVH / Med-HALT, MI-CLEAR-LLM. Domain-probe modules 16 → 17. Integrity detectors 39 → 41.
  - **Uncounted appraisal ref** `appraisal_tools/METRICS_RELOADED.md` (metric-selection guidance; not a
    counted reporting checklist). Reproducible challenges + CI-wired regression tests for both detectors.

## [4.10.0] - 2026-06-28

### Added

- **Three new reviewer domain-probe modules** (`/peer-review` + `/self-review`, vendored
  byte-identical), reverse-engineered from high-IF CC-BY papers under the `reverse_engineer/`
  license firewall: **`mendelian_randomization.md`** (MR1–MR8: the three IV assumptions, a
  pleiotropy-robust sensitivity suite rather than IVW alone, Steiger/direction, sample overlap,
  non-linear-MR caution, drug-target colocalization); **`polygenic_risk_score.md`** (PG1–PG8:
  ancestry transferability/portability, base/target leakage, incremental value over the clinical
  model, screening detection-rate-vs-discrimination, target-population calibration);
  **`network_meta_analysis.md`** (NM1–NM8: transitivity, global+local incoherence, SUCRA/P-score
  over-interpretation, CINeMA/GRADE-NMA certainty, component-NMA additivity). Domain-probe modules
  12 → 15.
- **Observational probe O17** (`observational_confounding.md`) — agnostic many-exposure-scan
  multiplicity (ExWAS / EWAS / MWAS): correction matched to claim against the honest test-count
  denominator, independent replication as the real safeguard, correlated-exposure conservatism,
  selective top-hit reporting.
- **Two reporting-guideline checklists** (`/check-reporting`): **STROBE-MR** (Mendelian
  randomization) and **PGS-RS / PRS-RS** (polygenic-score risk prediction), with study-type
  routing + aliases. Reporting guidelines 36 → 38.
- **Four `/analyze-stats` analysis guides**: multiple-testing/high-dimensional screening,
  Mendelian randomization, polygenic risk score, and network meta-analysis.
- **`/clean-data` implausible-value & cross-field validity rules** reference — organ-system
  compatible-with-life bounds + cross-field logical-consistency rules (temporal ordering,
  derived-vs-source, sex-/state-specific), flag-not-auto-fix.

### Changed

- **Clinician-friendly update reminders.** The classroom installers
  (`install-macos.command` / `install-windows.cmd` / `install-windows.ps1`) now enable the in-app
  "update available" notice and the one-click Desktop updater by default (turnkey path; disable
  with `--disable-update-notify` or `MEDSCI_NO_UPDATE_CHECK=1`). For the `npx`/manual paths the
  installer prints a one-time nudge showing how to turn reminders on (`--enable-update-notify`),
  and the README Quick Start recommends it. New read-only `update.session_hook_enabled()` gates the
  nudge; the `npx`/manual paths stay opt-in (no silent SessionStart hook).

## [4.9.0] - 2026-06-26

### Added

- **Duplicate-bibliography gate** — new `check_reference_duplication.py`
  (`/manage-refs`, also usable from `/sync-submission`) reads the BUILT artifact
  (`.docx` via stdlib zipfile, or a rendered `.md`/`.txt`) and fires
  `DUP_REF_HEADING` / `REF_NUMBER_RESTART` / `REF_SIGNATURE_DUP` (Major) when the
  reference list is duplicated. Catches the hybrid failure where a manuscript
  carries both inline `[@key]` citations and a hand-typed `## References` list and
  is built with pandoc `--citeproc`: the build renders the hand list **and** a
  citeproc bibliography (often after the legends), so the same reference appears
  twice; `check_xref` does not see it. Author-anchored `(first-author, year)`
  signature detection works on Word auto-numbered lists. Validated against a real
  built docx with the duplicate (caught) and its single-list fix (clean).
  Stdlib-only; PII-free fixtures + `test_reference_duplication.sh`.

- **Cross-script binning-consistency gate** — new `check_binning_consistency.py`
  (`/self-review`, Phase 2.5b) parses analysis source (R/Python) and emits
  `BINNING_DRIFT` (Major) when one derived categorical (age band, BMI category,
  eGFR stage, risk tier) is binned with ≥2 different `(breaks, right-closure)`
  signatures across files. The same cohort then splits differently per script:
  per-stratum Ns drift between a primary table and a sensitivity table while the
  grand total still reconciles, so a row-sum check passes but a stratum can
  spuriously cross a threshold. Motivated by a screening cohort that binned age
  `right=FALSE` in the primary script vs `right=TRUE` in a threshold sensitivity
  script — fractional ages shifted hundreds of participants and produced a
  spurious "reached" stratum. Stdlib-only; PII-free fixtures +
  `test_binning_consistency.sh`.

  Together these two gates take the analysis-integrity detector suite **34 → 36**
  (citation family 6 → 7, data-preparation 5 → 6); skills and reporting guidelines
  unchanged. Additive and backward-compatible.

- **Float citation-order gate** — new `check_citation_order.py` (`/self-review`)
  flags numbered floats not cited in ascending order of first appearance, per series
  independently (main Tables, main Figures, Supplementary Tables, Supplementary
  Figures). It scans only the narrative body (auto-excluding the Figure Legends /
  back-matter so an in-order legends block cannot mask an out-of-order body) and
  tolerates plural lists ("Tables S4, S5"), ranges, and non-float sensitivity-spec
  labels ("S1–S6"). `CITATION_ORDER` (Major) is a pre-peer-review desk/technical-check
  item editorial offices "unsubmit" for; `CITATION_GAP` (Minor) flags non-contiguous
  numbering. Motivated by a journal technical-check unsubmit where main Table 3 was
  cited before Tables 1–2 and the supplementary tables were cited wildly out of order
  (S4, S9, S16, S12, …). Wired into `/self-review`'s technical-check pass; synthetic
  positive/negative fixtures + regression test. Analysis-integrity detectors
  **33 → 34** (Reporting compliance family 8 → 9); skills 45 and reporting guidelines
  36 unchanged. Additive and backward-compatible.
- **Percentage-decimal style check + KJR technical-check conventions** — `/self-review`'s
  `check_classical_style.py` gains a `PERCENT_DECIMALS` verdict (Minor, report-only)
  flagging percentages reported to >1 decimal place ("35.14%"), which several journals
  (e.g. KJR) require at one decimal at technical check; regression fixture + test added.
  The KJR journal profile (`write-paper` detail + `find-journal` compact) gains a
  **Technical-Check Conventions** section enumerating the deterministic pre-review desk
  items that "unsubmit" a manuscript: ascending float citation order, demographics in
  Materials and Methods, one-decimal percentages, double spacing, Acknowledgments/Funding/
  Author-Contributions on the Title Page only, reporting checklist cited as "Supplementary
  Material 1", IRB number in Methods even when blinded, and ICMJE forms only after
  acceptance. No detector-count change (existing detector extended; profiles updated, not
  added). Motivated by a 2026-06 KJR technical-check unsubmit.

- **Audit-dump leak gate** — new `check_checklist_dump_leak.py` (`/sync-submission`)
  scans every `.md`/`.docx`/`.pdf` in a submission directory for the residue of a
  `/check-reporting` or `/self-review` *internal* audit report (`compliance_pct`,
  `fixable_by_ai`, `check_reporting_version`, `Auto-fix:`, `[PARTIAL→auto-fixed]`,
  `suggested_fix`, `Action Items`, `_pipeline_log`, `NON-AUTHORITATIVE`). Any hit is
  a **P0 leak**: these tooling tokens must never reach a reviewer. Motivated by a
  near-miss where a prior project's `STROBE_checklist_v4.pdf` was actually the
  check-reporting dump, reused by filename and compiled into the reviewer-visible
  proof (exposing auto-fix notes, raw JSON, and a stale old title). Wired into
  `preflight_gate.py` as a P0 check over the journal asset directory; writes
  `qc/checklist_dump_leak.json`. `/check-reporting` reports now also open with a
  `NOT-FOR-SUBMISSION` banner so the working audit is self-identifying.
  Analysis-integrity detectors **32 → 33**; skills 45 and reporting guidelines 36
  unchanged. Additive and backward-compatible.

- **Frontmatter schema gate (Agent Skills cross-platform portability)** — new
  `scripts/check_frontmatter_schema.py` + CI step strictly `yaml.safe_load`s every
  `skills/*/SKILL.md` frontmatter and enforces the published Agent Skills spec: valid
  YAML, `name` ≤64 chars / lowercase-hyphen / no reserved `claude`/`anthropic` token,
  `description` present / ≤1024 chars / no XML angle brackets. The repo's own generators
  use a tolerant line-based reader, so a frontmatter block that is not valid YAML could
  pass every prior gate yet be rejected by a strict-YAML consumer (the agentskills.io
  directory validator or another agent platform). Self-test (`tests/test_frontmatter_schema.sh`)
  covers each violation class. This is a repo-CI validator, not a counted detector.

### Changed

- **Skill-boundary documentation** — a diagnostic pass confirmed the 45 skills are
  deliberately specialized (no consolidation warranted), but several boundaries were
  easy to confuse. README's "Skills Work Together" now carries a **Skill boundaries**
  block spelling out the reference pipeline (`search-lit` → `lit-sync` → `manage-refs` →
  `verify-refs`), the language pass order (`humanize` → `polish-language` → `academic-aio`),
  manuscript-type selection (`write-paper` / `review-paper` / `revise`), author-vs-reviewer
  (`self-review` / `peer-review`), project entry (`intake-project` / `orchestrate`), study
  design (`design-study` perceptual ceiling gate / `design-ai-benchmarking`), and content
  vs template (`write-protocol` / `fill-protocol`). `/revise` now documents the manual
  fallback when `/analyze-stats` or `/make-figures` is unavailable (emit a checklist, hold
  responses as `BLOCKED — pending analysis/figure`, never invent numbers). Docs only.

- **`/analyze-stats` observational-design precondition** — Phase 2 (Analysis Plan) now opens
  with a WARN-level precondition: before planning an observational analysis (cohort,
  case-control, cross-sectional, registry, survey), confirm a literature-grounded
  `variable_operationalization.md` (from `/define-variables`) or equivalent codebook-backed
  definition table exists; if not, warn and recommend `/define-variables` first so
  exposure/outcome/covariate definitions and cutoffs are citation-backed rather than invented
  ad hoc from the data dictionary. WARN, not a hard block (proceed on explicit confirmation;
  stricter projects can treat it as a hard stop). Mirrors the precondition `/write-protocol`
  already enforces before drafting Methods, closing the one observational-pipeline skill that
  lacked it. Guidance only — non-breaking, no new code gate.

- **`/meta-analysis` progressive disclosure (token hygiene)** — the two inline "Empirical
  Lessons" sections (16 dated SR-MA peer-review lessons, ~45 lines) moved verbatim to
  load-on-demand `references/empirical_lessons.md`, with an explicit "load before Phase 4
  extraction-form design and before Phase 8 submission" pointer and a `Reference Files`
  entry — matching the skill's own established pattern (15 existing reference files). The
  largest SKILL.md in the bundle drops 804 → 775 lines (less context loaded on every
  activation); the lessons stay discoverable via the reference list. Content byte-preserved
  (no rewrite, no renumber — a pre-existing duplicate "9." label is carried over and noted in
  the reference file). No skill/detector count change.

- **De-drift the `sync-submission` YAML front-matter splitter** — `check_wordcount_cap.py`
  and `cover_letter_drift_check.py` each carried their own `_strip_yaml_front_matter`, marked
  "keep in sync" but already drifted (list vs tuple return; subtly different unclosed-fence
  handling). Extracted one canonical `split_yaml_front_matter()` into a private
  `scripts/_yaml_frontmatter.py` (leading underscore → not counted as a detector) imported by
  both — the helper ships in the same skill's `scripts/` dir, so it stays self-contained when
  vendored/installed. Behavior-preserving (verified normal / no-front-matter / unclosed cases
  + the wired `test_wordcount_cap` and `test_preflight_gate` subprocess-import path). No
  skill/detector count change.

### Fixed

- **Public-doc count reconciliation** — `README.md` (MedSci-Audit suite line) and
  `CITATION.cff` (abstract) cited stale catalog totals from before the detectors above
  merged (28 detectors / 32 EQUATOR guidelines). Reconciled to the disk SSOT
  (`metadata/catalog_counts.json`): **36 analysis-integrity detectors / 36 reporting
  guidelines**. Added a `What's New` "Unreleased" block to `README.md` so the public
  progression no longer implies v4.8 is current. No code or count change — the SSOT was
  already correct; only the prose was stale. Verified by `validate_catalog_consistency.py`.

- **`check_csl_render.py` hardening** (`/manage-refs`) — the CSL acceptance detector
  had five latent bugs that could surface a raw traceback or a silently-wrong verdict:
  it carried the two citekeys as module globals (`render()` was not standalone-callable),
  did not check pandoc's return code (a failed render was analyzed as if it succeeded),
  leaked `NamedTemporaryFile(delete=False)` temp files, imported `python-docx` deep inside
  a function, and read the `.bib` with an unguarded `open().read()`. Now: citekeys are
  passed as parameters, pandoc's return code (and a missing pandoc binary) raise a clear
  error and exit 2, all temp files live in a `TemporaryDirectory`, the `python-docx` import
  is guarded with an install hint, and a missing `.bib` reports `bib file not found`. No
  detector-count or behavior change on the happy path. New CI-wired regression test
  (`tests/test_csl_render.sh`, PII-free fixture) covers the error paths without requiring
  pandoc (the no-pandoc branch runs in CI; the render branch runs wherever pandoc exists).

- **CI test-coverage gap closure (15 dormant tests wired)** — fifteen skill regression
  tests shipped with their detectors but were never added to `.github/workflows/validate.yml`,
  so CI gave false coverage (`check-reporting` fail-fast / framework-naming / PRISMA-cascade,
  `manage-refs` duplicate-bibliography, `self-review` binning-consistency / citation-order /
  claim-artifact / panel-diversity / reviewer-team-consistency, `sync-submission` audit-dump-leak
  / copy-divergence / cross-document-N / scope-drift / vN-docx-assertion, `verify-refs`
  pagination-placeholder). All pass on the toolchain CI installs (stdlib + python-docx; no
  pandoc/R) and are now `run:` steps in `validate.yml`.

- **Dormant PRISMA Figure 1 detector activated** — `check_prisma_figure.py` (a counted
  MedSci-Audit detector implementing `/check-reporting` Step 4d's arithmetic + body↔figure
  cross-reference audit) existed and worked but was never invoked: Step 4d described the
  algorithm in prose and asked the model to extract numbers by hand. Step 4d now runs the
  deterministic script first (manual algorithm kept as the PNG/SVG-transcription fallback),
  with a new CI-wired test (`tests/test_prisma_figure.sh`, PII-free fixtures). The two
  `manage-refs` CSL tools surfaced by the same audit (`check_csl_render.py`,
  `fill_journal_abbrev.py`) are now documented in that skill's tool table.

- **`skills/MAINTENANCE.md`** — documents the four skill-script categories (counted detector /
  helper / run-once authoring tool / test fixture) and the wiring rules that prevent a detector
  or test from going dormant again (a detector must be invoked from SKILL.md and CI-tested; a
  test only counts as coverage if it is a `run:` step in `validate.yml`). No skill or detector
  count change.

- **`manage-project` frontmatter was not valid YAML** — its inline `description` ended with
  `Commands: init, status, …`, and the `: ` makes a plain inline scalar invalid YAML (a strict
  parser raises "mapping values are not allowed here"). The repo's tolerant reader accepted it,
  so it passed every prior gate, but a strict-YAML consumer would reject the skill. Quoted the
  description value (text unchanged; the storefront catalog first-sentence and per-skill docs are
  byte-identical). Found by the new frontmatter schema gate above.

## [4.8.0] - 2026-06-24

The **review-harvest batch**: deterministic detector hardening promoted from real-manuscript review
cycles — four false-positive fixes, two new gates, nine reviewer-side domain probes, and a
design-stage gate. **Additive and backward-compatible** — no skill, CLI, or output-path change;
skills 45 and reporting guidelines 36 unchanged; analysis-integrity detectors **30 → 32**.

### Added

- **Reader-facing supplement / multi-file hygiene gate** — new `check_supplement_hygiene.py`
  (`/self-review`) lints the rendered supplement, a separately-built tables file, and caption files
  (not just `manuscript.md`) for the technical-check-fatal residue that hides there: `§`/`§L` internal
  labels, unfilled placeholders (`Table SX`, `[Authors]`, figure-path globs, build-dir paths), build
  markers (`[VERIFY]`/`TODO`), response-to-reviewers framing, planning residue, and body↔supplement
  cross-reference numbers that don't resolve. `check_artifact_coverage.py` gains
  `PROMISED_STAT_NO_VALUE` + a `--supplement` corpus (a bound/ceiling/de-confounded statistic promised
  but never given a number anywhere). (#187)
- **Power-aware null-interpretation gate** — new `check_null_calibration.py` (`/self-review`)
  flags a headline negative/equivalence claim ("no synergy", "not associated") that carries no
  minimum-detectable-effect, power, equivalence-margin/TOST, or CI-compatibility statement. Plus a
  reusable `rating_monotonicity.py` template (`/analyze-stats`) that catches a folded
  confidence-weighted (call × confidence) → AUC encoding, and a `/design-study` design-stage ceiling
  gate for perceptual/reader-AI studies (6 ceiling-breakers set before data lock). (#188)
- **Nine reviewer-side domain probes** across the shared peer-review/self-review modules: SR/MA
  small-k enrollment-overlap, mixed-denominator pooling, prospective-registration chronology, and
  boundary-degenerate proportions (P14–P17); observational selection-on-availability and
  serial-imaging lesion-tracking (O15/O16); diagnostic exclusion-flow ↔ prose + modality-safety (D8);
  AI arm-task-vs-deployment-workflow (AO6); and a survival apparent-vs-optimism deterministic tell
  (S7). (#186)
- **Integrity detector count: 30 → 32.**

### Fixed

- **Four detector false positives** that fired Major on legitimate (often recommended) patterns:
  `check_generated_code` no longer flags a hex-color palette (the colorblind-safe WONG palette
  `make-figures` recommends) as hand-typed tabular data; `check_classical_style` fires the `§` AI-tell
  only on a section cross-reference, not on author-footnote daggers; `check_scope_coherence` clears
  `CROSS_SECTIONAL_PROGNOSTIC` when the prognostic token sits inside a negation/deferral frame; and
  `check_cohort_arithmetic` no longer mis-binds the `RATE_BACKCALC` numerator to a tier label's digit
  or a decimal's fraction. Each ships a regression fixture; three previously-unwired test suites are
  now CI-wired. (#185)

### Changed

- **Release pipeline now also publishes to npm** (idempotent, with npm provenance via OIDC), so the
  `npx medsci-skills@latest install` channel no longer drifts behind the GitHub release. The step runs
  only when the `NPM_TOKEN` repo secret is set, skips if that version is already on npm (re-running a
  tag is safe), and runs after the GitHub Release so an npm hiccup never blocks it. No product change.

## [4.7.0] - 2026-06-22

The **self-update foundation**: physician-researchers stay current without GitHub, git, or a
terminal — via a transactional crash-safe installer, a verified one-click updater, a hardened
release pipeline, and an opt-in update notice. **Additive and backward-compatible** — no skill, CLI,
or output-path change; skills 45 and reporting guidelines 36 unchanged. All four pieces are
network-mocked-tested and run on Ubuntu + macOS + Windows CI.

### Added

- **Transactional, crash-recoverable installer + per-target state.** `install.py` now installs each
  target through a durable **journal state machine** (`installers/medsci_txn.py`,
  `prepared → old_moved → new_installed → committed`, atomic-write + `fsync`): an interrupted install
  is recovered on the next run (roll back an incomplete transaction, forward-clean a committed one,
  **fail closed** on a corrupt journal). It keeps a per-target installed manifest at
  `~/.medsci-skills/targets/<target>/` with a **per-skill SHA-256 inventory** — a skill you modified
  is snapshotted to `~/.medsci-skills/backups/<ts>/` before an update, legacy collisions are backed up
  there (never inside the skills dirs, never auto-deleted), and only MedSci-owned skills are pruned
  (your/third-party skills are untouched). Adds **canonical-home containment** path-safety, a
  disk-space preflight, two deterministic tracked manifests
  (`metadata/distribution_manifest.json` ownership/version + `metadata/distribution_files.json`
  payload inventory) with a CI `--check` gate, and a Windows/macOS CI matrix. (#177)
- **One-click self-updater (`installers/update.py`).** Fetches the latest classroom release and
  re-installs through the transactional installer — no GitHub UI, git, or terminal. Resolves the
  release via **`api.github.com` only** and **fails closed** if the API has no sha256 digest; verifies
  the download's sha256 == the API digest, the asset name, and the tag; and **never `extractall()`s** —
  it extracts per entry, rejecting path traversal (POSIX + Windows), symlink/hardlink/junction,
  case-insensitive duplicates, and zip-bombs, and enforcing the `distribution_files.json` allowlist +
  per-file hash. Installs the updater to `~/.medsci-skills/updater/` (survives deleting the download
  folder); `install.py --check-update` reports availability via semver with a clock-sane 24h cache;
  optional consented `--desktop-launcher`. Thin `.command`/`.cmd` launchers wrap it; a privacy notice
  (`docs/update_privacy.md`) states the honest scope. (#178)
- **Release-pipeline supply-chain hardening.** `release.yml` now gates on a version-consistency check
  (the pushed tag must equal `CITATION.cff` == `package.json` == `metadata/distribution_manifest.json`
  and the tracked inventory must match the tree); injects a verified `provenance.json`
  `{schema_version, tag, version, git_sha, built_at}` into each classroom ZIP via
  `build_classroom_release.py --tag/--git-sha/--built-at`; attests the ZIPs' build provenance
  (`actions/attest-build-provenance`); runs on a protected `release` environment (required-reviewer
  approval); and — via the new `scripts/check_release_zip.py` — verifies each ZIP round-trips through
  the **updater's own** safe-extract + provenance validation before publishing, so a release can never
  ship a ZIP the self-updater would reject (locked by `installers/tests/test_release_zip.sh`).
  `provenance.json` stays a control file (excluded from the safe-extract inventory). `SECURITY.md`
  gains a "Release integrity & revocation" section; `docs/maintainer_workflow.md` documents the
  protected-environment setup. (#179)
- **Opt-in update notice for Claude Code (off by default).** `install.py --enable-update-notify`
  merges a SessionStart hook (`installers/session_update_check.py`) into `~/.claude/settings.json`
  that prints a one-line "update available" `systemMessage` at session start; `--disable-update-notify`
  removes only that hook (keying on the home-anchored script path, so it never touches a foreign hook).
  The hook **does not read the SessionStart stdin** (no cwd/transcript/session id), has no
  telemetry/analytics/unique-id, uses the shared clock-sane 24h cache + a 4 s timeout, stays silent on
  any error (never blocks a session), honors `MEDSCI_NO_UPDATE_CHECK=1`, and installs nothing — it
  only notifies. A version *check* resolves the latest tag without the OS-specific download asset
  (`resolve_latest_tag`), so the notice works on Linux too; the settings merge is idempotent, preserves
  foreign hooks/settings, and refuses to clobber an unparseable `settings.json`. Tested offline
  (`installers/tests/test_session_hook.py`, 38 cases). (#180)

### Trust boundary (honest scope)

- Running a release's bundled installer **is remote code execution within the GitHub trust boundary**.
  The digest and the build-provenance attestation detect **transport / asset tampering** — they do
  **not** defend against a compromised publisher account or a malicious official release. See
  `SECURITY.md` and `docs/update_privacy.md`.

## [4.6.0] - 2026-06-21

A maintainability, governance, and review-depth release. **Integrity detectors 28 → 30; domain probes 11 → 12; skills 45 and reporting guidelines 36 unchanged.** No skill rename, CLI, or output-path change — additive and backward-compatible.

### Added

- **Fairness / equity / subgroup-performance domain probe (`equity_fairness.md`, EQ0–EQ6).** Vendored byte-identical into `/peer-review` and `/self-review` (`MODULES` 11 → 12). Fires only when a manuscript claims cross-population performance or presents subgroup analyses as a fairness argument: disaggregated subgroup metrics (not aggregate-only), error-rate-vs-discrimination parity and base-rate dependence, a named fairness estimand + between-group gap test, development-cohort representativeness, subgroup EPV/power, and equity-aware framing aligned to TRIPOD+AI / DECIDE-AI / CONSORT-AI. (#170)
- **AI-disclosure + data/code-availability detector (`sync-submission/check_disclosure_availability.py`).** An AI-use disclosure must carry four tokens — version + access channel + date/date-range + responsible party (the tool name only triggers the check) — plus Data/Code Availability presence with a repository/DOI where the journal expects one, keyed by `journal_availability_policy.json`. (#171)
- **Structured-summary-box conformance detector (`academic-aio/check_summary_box.py`).** Key Points bullet count + one-claim-per-bullet, Research-in-context's three sub-blocks, and plain-language word band, journal-keyed via `summary_box_specs.json` — catches the wrong-format box a production technical check rejects. (#171)
- **Skill `maturity` taxonomy (`official` / `experimental` / `community`).** A required, additive `skill.yml` v2.2 field (`schema_version` stays 2), enforced by `validate_skill_contracts.py` and surfaced in `skills_catalog.json`; all 45 current skills are `official`. (#174)
- **Governance & answer-engine docs:** `ROADMAP.md` (priorities + explicit out-of-scope), `MAINTAINERS.md` (clinical authority stays with the founder), `SECURITY.md` (vulnerability reporting + medical-scope boundary), `docs/maintainer_workflow.md` (review + release checklist), `docs/faq.md` (AEO/GEO), and two new issue templates (installation problem, detector request). (#173)

### Changed

- **Positioning leads with the compliance moat.** README hero subline and the marketplace source description (`MARKETPLACE_DESCRIPTION`) now lead with reporting-guideline + risk-of-bias compliance, reference verification, and deterministic integrity gates rather than skill count. README gains a "What is MedSci Skills?" answer block, a "Start here: 3 workflows" section, and a "Validation status" section (available vs CI-gated vs E1-evaluated). A stale "32 EQUATOR" hero count was corrected to "36 reporting guidelines and risk-of-bias tools". (#173, #174)
- **`write-paper` Phase 7 token diet (pilot).** The three integrity-audit sub-steps (7.3a/7.3b/7.3c) moved to `references/phase7_integrity_audits.md` behind a control-flow-preserving pointer; measured −10,238 chars (~2,559 tokens) per invocation, loaded on demand only when Phase 7 runs. (#172)

### Documentation

- `CONTRIBUTING.md` and the PR template add a medical-claim → founder-review gate and an official/experimental/community classification line; `IMPACT.md` adds an "Interpretation of metrics" caveat block ("early community interest, not widespread adoption"). (#173)

### Validation / Evidence

- New deterministic scripts each ship a network-free challenge/regression test wired into CI. `MEDSCI_AUDIT.md` detector-count claims corrected (it had drifted to 27/28) and a `DETECTOR_CLAIM_FILES` gate added to `validate_catalog_consistency.py` (anchored current-total patterns, never historical evaluation numbers) so the total cannot silently drift again. A regression test for the routing-asset gate (`tests/test_routing_assets.sh`) covers the references/ pointer that guards the Phase-7 extraction. (#169, #171)

## [4.5.0] - 2026-06-20

### Added

- **Self-review domain-probe batch (SR/MA + DTA + prediction-model) + submission asset-anon abs-path gate.** Five new review probes promoted from field cycles, plus one deterministic submission check. `sr_ma.md`: **P12** risk-of-bias table row-sum ↔ figure-matrix reconciliation (each NOS ★/JBI Y row must equal its printed total; the traffic-light figure's data matrix must match the supplementary table; SSOT = the primary appraisal form, not a plotting-script constant) and **P13** included-study ↔ reference-list completeness (every characteristics-table study must be a numbered reference; source citations from PubMed `efetch`, not hand-kept notes; disambiguate same author/year by technique + sample size). `diagnostic_accuracy.md`: **D7** index-test-as-enrollment-criterion circularity (escalate past Major when an inclusion threshold is the index test under study). `clinical_prediction_model.md`: **CP5** intended-use horizon leakage (claim-timepoint adjectives vs each predictor's availability timepoint) and **CP6** validation-nomenclature conflation (development/CV vs held-out/external test). Probes are vendored byte-identical to `peer-review`. `sync-submission/scripts/check_asset_anonymization.py`: new scan class 4 — a `word/*.xml` attribute (e.g. a pandoc-embedded image's `<pic:cNvPr descr="…">`) carrying an absolute home-dir path (`/Users/…`, `/home/…`) is a username leak invisible to a rendered-text scan; flagged as `docx_embedded_abs_path` (leak severity), with a regression test fixture. No version bump — probe/reference + detector additions.
- **`/clean-data` + `/analyze-stats` — reverse-coded-item / negative-alpha detector (integrity detectors 27 → 28).** A multi-item Likert scale with a negatively-worded item must recode it `(min+max) - x` before the scale total or Cronbach's alpha is computed; left un-recoded, the item correlates negatively with the rest of the scale and alpha collapses (often *negative*). A negative alpha is a coding bug, not a "multidimensional construct" — defending it as such loses a review round. New stdlib-only `skills/clean-data/scripts/check_reverse_coding.py` computes per-item corrected item-total (item-rest) correlations + the raw Cronbach's alpha and returns `REVERSE_CODING_LIKELY` (alpha < 0) / `REVERSE_CODING_SUSPECT` (negative item-rest, alpha ≥ 0) / `OK`, exit 1 under `--strict`. `skills/analyze-stats/references/templates/likert_summary.py` is hardened to print item-rest correlations, flag negative ones as reverse-code suspects, warn loudly on a negative alpha, and apply the recode via a new `--reverse-items` flag before scoring/alpha. Ships a synthetic fixture (a 3-item scale with one reverse item → raw α = −1.71, plus a clean aligned scale) + CI-wired regression test (`skills/clean-data/tests/test_reverse_coding.sh`). Detector mapped to the `data_preparation` family; `metadata/detectors_catalog.json` regenerated; `catalog_counts.json::integrity_detectors` 27 → 28. Motivation: a medical-education pilot whose Trust scale shipped at α = −0.57 (one reverse item un-recoded) and consumed a major-revision round before `6 - x` restored α = 0.58.

- **Test backfill (cont.) — `fill-protocol` + `fulltext-retrieval` regression tests (Tier 1 complete).** `skills/fill-protocol/tests/test_fill_form.sh` builds a synthetic Word template at runtime (python-docx: 2-column key/value table + numbered section headers + title paragraph), runs `fill_form.py` with a content YAML exercising `table_kv`/`section_replace`/`paragraph_replace`, and asserts the values landed in the reopened docx, the title placeholder was replaced, and an absent label is reported `[MISS]` — no committed binary fixture. `skills/fulltext-retrieval/tests/test_pdf_to_md.py` stubs `pymupdf4llm` before import (the module exits on a missing dep) and pins the dependency-free helpers `parse_page_range` (ranges/lists/whitespace) and `clean_markdown` (collapse 4+ newlines, rstrip lines, single trailing newline, idempotent) — no heavy PyMuPDF dependency added to CI. Both use deps already present (python-docx/pyyaml; stdlib). No skill/version change — test infrastructure only.
- **Test backfill (cont.) — `fill-icmje-coi` + `academic-aio` regression tests.** Three more deterministic, network-free tests wired into CI. `skills/fill-icmje-coi/tests/test_fill_icmje_coi.sh` clones the shipped synthetic seed for two authors and asserts the documented contract per output docx (14 checked boxes, 13 "None" disclosures, new title/date substituted, author name present, zero placeholder leakage; stdlib zipfile path). `skills/academic-aio/tests/test_validate_schema.sh` checks the JSON-LD validator (valid ScholarlyArticle passes; wrong `@context`, unknown `@type`, missing required field, malformed DOI each fail). `skills/academic-aio/tests/test_batch_metadata_audit.sh` checks the repo/HF-card auditor (clean repo passes `--fail-on-issue`; missing README/CITATION/LICENSE fails; report-only mode stays exit 0; a PHI-shaped string in an HF card is flagged). All fixtures synthetic. No skill/version change — test infrastructure only.
- **Test backfill — Tier 0 CI-wiring + `deidentify` PHI-scan regression test.** Ten skill regression tests that existed on disk but were never gated are now wired into `.github/workflows/validate.yml`, so a silent break fails CI: `make-figures` (legend reconcile), `clean-data` (structural-zero), `lit-sync` (poll logic), `meta-analysis` (pool consistency), `generate-codebook`, `present-paper` (speaker-notes markdown), `version-dataset` (manifest/verify), `manage-refs` (vN-docx cross-ref), and `polish-language` (consistency-linter challenge). New `skills/deidentify/tests/test_deidentify_scan.sh` asserts the exact PHI-classification contract (PHI/REVIEW_NEEDED/SAFE counts + `rrn` phi_type) on the three committed fixtures — the CSV scan path is stdlib-only and network-free, and the test file is Hangul-free (column-specific asserts read the fixture header at runtime). CI now installs pandas/numpy/python-pptx/python-docx up front (was: pandas installed after the gates, which would silently skip the dep-guarded tests); `version-dataset` gains a pandas skip-guard for local robustness. No skill/version change — test infrastructure only.

## [4.4.0] - 2026-06-20

### Added

- **`/peer-review` + `/self-review` — Image-Synthesis / Cross-Modality Generation probe module (IS1–IS4) + reviewer-side reference-integrity spot-check.** New domain-probe module `image_synthesis.md` (vendored byte-identical into `/self-review`; `MODULES` 10 → 11, sync gate updated) for studies that synthesize one imaging modality from another (MRI→PET / MRI→CT / non-contrast→contrast / low-dose→full-dose) and claim the output carries functional/molecular information or substitutes for the unavailable target. **IS1** determinism/information-ceiling (the synthetic image is a deterministic function of the source, so a same-reader "source + synthetic > source alone" gain is a presentation/interpretability effect absent a direct source→label baseline); **IS2** target-derived-preprocessing / undescribed slice-selection leakage (a lesion mask drawn on the target modality guiding slice selection or training makes "function inferred from structure" circular — undescribed provenance is itself a Major #1 candidate); **IS3** global-vs-lesion-level quantitative agreement (whole-organ SUVR agreement does not establish lesion-level fidelity); **IS4** mechanistic/proxy-signal plausibility (name what the source physically measures vs the target's biology — high image similarity is not evidence an unmeasured signal was recovered). Routed from a new peer-review **Phase 2K** + Phase 3 QC item 15 + Phase 5 routing line, and a `/self-review` routing-table row. Per Phase 2F, IS2/IS4 are typically unfixable-in-current-form and govern the recommendation toward Reject-leaning. Companion **reviewer-side reference-integrity spot-check** added to the Phase 2 issue checklist + Phase 3 QC item 16 (all original-research reviews): spot-check the load-bearing Introduction/Discussion citations used *as evidence the method/premise works* — a paper cited for a different task, a duplicate reference, a wrong year/author — phrasing unconfirmed suspicions "please verify" (the reviewer-side mirror of the authoring citation-safety discipline). Motivation: a decision-audit of a cross-modality MRI→synthetic-PET reader-study review where the three structurally distinct synthesis failure modes were split across reviewers and the reference-list errors went uncaught on the reviewer side.
- **`/author-strategy` — trajectory-archetype classification (optional, explainable multi-label heuristic).** Adds an opt-in capability that classifies a queried author's PubMed trajectory into abstract career archetypes (A1 infrastructure builder, A2 methodology rule-maker, A3 clinical→AI hybrid, A4 SR/MA volume engine, A5 large-consortium participation pattern, A6 clinical-subspecialty device/technique depth, plus a computed A3+A6 composite). The rubric is a single canonical data file (`references/trajectory_archetypes.yaml`); the narrative `references/trajectory_archetypes.md` is generated from it by `render_archetype_doc.py` (`--check` gate). Each label carries a 0–1 score (computable-signal-weight denominator; `unavailable` signals — h-index/citation/venue-tier — are excluded and surfaced as `[VERIFY]`, never fabricated), a confidence band capped per archetype, and evidence drawn from the author's own PMIDs (`evidence_pmids` for per-paper signals, `evidence_summary` for corpus-level); a negative rule suppresses a label to `insufficient evidence`. A **disambiguation gate** precedes classification: `fetch_pubmed.py` writes a `corpus_manifest.json` cryptographically bound to the CSV (`csv_sha256` + `pmid_set_hash`) and `classify_archetypes.py` refuses to run unless `review_status: approved` and the hashes match — a surname alone never resolves an author, and `--approve` is a human gate. Target-author attribution (ORCID/affiliation/initials/position) is split into a stdlib-only `pubmed_parse.py` and never borrows a co-author's metadata on a same-surname collision; author position is reported as a `first/middle/last/unknown` positional heuristic (not leadership metadata), and `analyze_patterns.py`'s "Leadership rate" is renamed "First/last positional rate". The output header states the labels are explainable heuristics, not objective classifications. Ships name-free synthetic fixtures + a CI-gated regression test (A14). Skill count unchanged — an enhancement, not a new skill.
- **`/verify-refs` — OpenAlex tertiary index (conference-proceedings / non-DOI recovery).** PubMed covers only biomedical literature and CrossRef's proceedings coverage is uneven, so NeurIPS / ICLR / ACL-style citations — common in medical-AI manuscripts — fall through both and were marked `UNVERIFIED`. After the PubMed and CrossRef tiers, `verify_refs.py` now consults OpenAlex (`https://api.openalex.org`, free, no API key) **only when no authoritative author list was obtained yet** (a reference already resolved by PubMed/CrossRef incurs no extra call). It resolves by DOI when present, otherwise by a token-similarity-guarded title search so a fabricated title cannot earn a spurious `OK`. This is the free analogue of the second index (e.g. Scopus) that journal portals run alongside CrossRef. Because OpenAlex display names carry no structured family/given field and mix `First Last` with `Last, First` forms, OpenAlex-sourced authors support an existence check plus a tolerant first-author *membership* check but **never** drive the strict positional or author-count MISMATCH (reserved for PubMed efetch / CrossRef); an OpenAlex miss is `UNVERIFIED`, never `FABRICATED`. New `--no-openalex` flag restricts verification to PubMed + CrossRef. Ships a network-free regression test (`tests/test_openalex_tier.sh`, monkeypatched `http_json`, CI gate A8b). Motivation: a medical-AI reference list where two NeurIPS citations validated on Scopus but not CrossRef in a journal portal's reference check.

## [4.3.0] - 2026-06-16

### Added

- **Observational / cohort probe + gate hardening** (sourced from two cross-sectional health-screening cohort self-review→revise loops). Expands `observational_confounding.md` **O1–O6 → O1–O9** (vendored byte-identical into `/self-review`): **O7 — over-adjustment** (conditioning on a mediator or consequence of the outcome — the opposite-direction failure to O1, e.g. a renally-excreted lab in an eGFR model; "adjust for everything that differs in Table 1" is not a confounder-selection rule), **O8 — analysis unit & clustering** (records vs unique subjects → anti-conservative CIs), **O9 — outcome construct validity** for report-/registry-derived outcomes (composite homogeneity, ascertainment/κ, dictionary-first label provenance, misclassification direction). O1 also gains an **exposure-defining-covariate exemption** for guideline-defined exposures and a reference-arm-contamination-vs-selection-bias note (O3); `check_confounding_completeness.py` now **computes SMD from per-stratum mean ± SD** when the wide Table 1 carries no p / SMD column (interop with `/analyze-stats`).
- **New domain-probe module `clinical_prediction_model.md` (CP1–CP4)** for cross-sectional / observational prediction models (TRIPOD / TRIPOD+AI nested predictor-set comparisons): apparent-vs-optimism-corrected calibration/DCA, the incremental-value-vs-marginal-effect **two-null distinction**, EPV per nested model, and net benefit as a model comparison (not a policy endorsement). Vendored byte-identical into `/self-review`; `MODULES` 9 → 10; routed from peer-review (new Phase 2E-2) and self-review. Plus two `/self-review` `exemplar_findings/` (`over_adjustment_collider.md`, `prediction_two_null_conflation.md`).
- **Cohort-analysis probes (G39–G41).** `survival_prognostic.md` gains **S9 — panel-data / multistate variance** (occupancy/intensity CIs must be person-clustered or person-bootstrapped, not naive model-based on within-person-correlated visit transitions; S1–S8 → S1–S9). `observational_confounding.md` gains **O10 — overlapping-subset gradient** (an effect-size gradient across nested/overlapping cohorts is attributable by construction; inferential "attenuated/accounted-for" language needs a difference/interaction test; O1–O9 → O1–O10). Both vendored byte-identical into `/self-review`. Plus an **extended-adjustment missingness-frame** discipline (compare adjusted vs unadjusted on the *same* reduced complete-case frame, not the full-frame anchor) in `/self-review` Phase 2.5e + `/analyze-stats` over-adjustment guidance.
- **Cross-sectional survey-epidemiology probes (G45–G46, paper-driven from CC-BY NHANES cohorts).** `observational_confounding.md` gains **O11 — complex-survey design & weighting** (NHANES/KNHANES/CHNS: design-based estimation with the correct/scaled weight + stratification + PSU, subpopulation-domain-not-row-deletion, weighted total is a population estimate not a sample n, design-effect/effective-n) and **O12 — data-driven threshold / non-linearity mining** (a recursive-search 'inflection point' / 'saturation effect' needs a breakpoint CI + pre-specified non-linearity test + stability check, not a quoted cutoff). O1–O10 → O1–O12, vendored byte-identical into `/self-review`. `/analyze-stats` `survey_weighted.md` gains a subpopulation-domain (never row-delete) + survey-reporting-errors block.
- **Cross-sectional mediation probe (G47, paper-driven from CC-BY mediation papers).** `observational_confounding.md` gains **O13 — cross-sectional mediation (temporal order & sequential ignorability)**: a Baron–Kenny / Sobel / PROCESS / bootstrapped indirect-effect chain estimated on single-timepoint data cannot establish the X→M→Y sequence (the bootstrap CI addresses sampling variability, not identification); needs an unmeasured-mediator–outcome-confounding sensitivity analysis (e.g. an E-value for the indirect effect) + a temporal-order caveat, and proportion-mediated is unstable when the total effect is small. O1–O12 → O1–O13, vendored byte-identical into `/self-review`; adds `exemplar_findings/cross_sectional_mediation.md`.
- **Cleanup batch (G48/G42/G43).** `/analyze-stats` gains a **mediation analysis guide** (`analysis_guides/mediation.md` + SKILL entry): bootstrapped a×b indirect effect, proportion-mediated only with uncertainty, AGReMA reporting, and the discipline that identification (no unmeasured mediator–outcome confounding → E-value for the indirect effect) — not the bootstrap — is the issue (pairs O13). `/sync-submission` gains **`scripts/assemble_supplement.py`** (NOT an integrity detector): validates an `S{N}_*.md` + index supplement (index↔file 1:1, duplicate/skipped sub-section numbers), rebuilds `_combined.md` in index order, and reports main-text callout coverage. `/render-pdf-doc` gains **`scripts/scan_glyph_coverage.py`** + a Step 3.5 pre-render scan for the xelatex silent-glyph-drop failure (arrows / − ≤ ≥ ± √ / Greek / ★ ✓ / CJK; optional `fonttools` cmap check). Both ship fixtures + CI-wired tests (A12/A13). Integrity-detector count unchanged (27).
- **Interaction-scale probe (G49, paper-driven from CC-BY joint-effect papers).** `observational_confounding.md` gains **O14 — interaction scale (additive vs multiplicative)**: a synergy / joint-effect / effect-modification claim is an additive-scale statement and needs **RERI / AP / synergy index with CIs**, not a multiplicative-only OR product term, joint-category ORs, or stratified-only estimates (the difference-in-significance fallacy). O1–O13 → O1–O14, vendored byte-identical into `/self-review`; `/analyze-stats` gains an Interaction & Effect-Modification entry (RERI/AP/S, Knol & VanderWeele). The cross-sectional-cohort review lane (O1–O14 + CP1–CP4 + S9 + gates) is now comprehensive.
- **`check_cohort_arithmetic.py` — new `ANALYSIS_UNIT_UNDISCLOSED` check** (`--id-col`, auto-detect with a cardinality guard): when records > unique subjects and the manuscript discloses neither the analysis unit nor a one-record-per-subject sensitivity, emits a Major with a `records / unique_subjects / repeat_subjects / max_visits` reconciliation (probe O8).
- **`check_scope_coherence.py` — new `CROSS_SECTIONAL_YIELD_LANGUAGE` lexicon** (Minor): a cross-sectional / prevalence design using incidence-flavored vocabulary ("yield", "detection rate", "number-needed-to-screen/image", "rescreen interval") without defining "yield" once as cross-sectional report-positive prevalence.
- **New detector `check_paren_spans.py`** (`/self-review`, integrity detectors **26 → 27**, family *Style & review-process*) — a post em-dash→paren-conversion safety scan (cohort-cycle follow-up): a bulk `— X —` → `(X)` edit can pair two *unrelated* dashes across a sentence boundary and wrap a whole sentence — or an ordinal limitation ("Sixth, …") — inside one parenthesis, paren-balanced so a balance check misses it. Flags `PAREN_SPAN_ORDINAL` and `PAREN_SPAN_SENTENCE` (long spans only, so short legitimate parentheticals like "(Dr. Smith)", "(Fig. 2)", "(95% CI …)" are clean). Wired into `/self-review` `--fix` post-edit and `/humanize` pattern 13. Fixtures + regression test (CI-gated).
- **New detector `check_wordcount_cap.py`** (`/sync-submission`, integrity detectors **25 → 26**, family *Reporting compliance*) — the **revision-inflation trap**: a revise loop monotonically adds words and silently breaches the target journal's body cap. Counts the body (Introduction → Discussion, skipping abstract/refs/tables/declarations), compares to a cap from `--limit` or a parsed `--journal-profile` article-type line, and emits `WORDCOUNT_OVER_CAP` (Major) / `WORDCOUNT_NEAR_CAP` (Minor, >0.95×). The binding number is the rendered count (citeproc expands `[@key]`), so it prefers `--rendered-words N` and otherwise estimates from the markdown body + inline-citation expansion. Wired as `/sync-submission` Gate 13, a `/revise` exit gate (re-run after every pass), and a `/self-review` §F check. Ships fixtures + regression test.

### Fixed

- **`verify_refs.py` — corporate/collective-author render-abort fix (cohort-cycle follow-up).** A guideline body double-braced in BibTeX (`{{EASL} and {EASD}}`, `{{KDIGO CKD Work Group}}`) or returned by PubMed as `<CollectiveName>` tripped the first-author cross-check as MISMATCH, which **aborted `render_pandoc.sh` on every guideline-citing cohort manuscript**. Corporate authors are now detected (surviving brace / `<CollectiveName>` / organization keyword) and exempted from the personal-name family cross-check (annotated `corporate/collective author`, never MISMATCH). Personal-author entries are unaffected.
- **`check_classical_style.py` — em-dash counter counts prose only (cohort-cycle follow-up).** It excludes structural dashes — markdown table cells (incl. "—" N/A placeholders and `(A) —` panel-label captions), ORCID separators, and author/affiliation lines — and reports prose-vs-structural separately, so a cohort manuscript with large baseline tables is not pushed into destructive edits on correct table dashes.
- **`check_confounding_completeness.py` — DB-column-code ↔ prose alias map.** A DB-exported Table 1 carrying column codes (`he_sbp`, `b_uric`, `b_chol_hdl`) was false-flagged as imbalanced-and-unadjusted when the adjustment set was written in prose ("systolic blood pressure"). An alias map now resolves both to a shared concept; it only ever *adds* matches (no new false ✓). Genuinely unadjusted covariates still flag.
- **`check_confounding_completeness.py` — exposure-defining-covariate exemption (O1 false-positive on guideline-defined exposures).** For a guideline-defined exposure (MASLD / metabolic syndrome / CKM / sarcopenia / frailty), the components of its own diagnostic criteria (BMI, glycaemia, lipids, BP) are imbalanced *by construction* and correctly unadjusted — the gate flagged each as a Major. New `--exposure-defining-list/-file` marks these `EXPOSURE_DEFINING_EXEMPT` (adjusting for them is over-adjustment, probe O7), so the Major remains only for genuine non-defining prognostic covariates. O1 wording updated; also a fixed `_pick_col` substring bug (a 1–2-char hint like "p" matched an unrelated column such as "exposed").

### Changed

- **`/self-review`** — adds a **difference-in-significance discipline** check (§C; "stronger in A (p<0.05) than B (p=NS)" without a formal interaction test), **statistic-type fidelity** and **stale-derived-CSV (n-mismatch)** checks (Phase 2.5a), **`POWER_MODEL_MISSPEC` / `POWER_VALUE_INTERPOLATED`** (Phase 2.5a-2; the power/MDE simulation must use the primary-model adjustment set and not be interpolated), an additive **`requires_reanalysis`** issue-schema field that routes data-level fixes to `/analyze-stats` instead of a prose `--fix` (Phase 4), and **re-run-the-panel-after-a-large-revision** guidance (Phase 2.6).
- **`/analyze-stats`** — over-adjustment covariate-selection guidance for cross-sectional outcome models, and a **Table 1 mean(SD)-vs-median(IQR) rule by `|skewness|>1`** (not a mean−median/SD heuristic) coupled to Wilcoxon / t-test.
- **`/check-reporting`** — STROBE common-gap items: power-aware framing of a null result, and confounder-selection rationale (no kitchen-sink / no outcome-consequence adjustment).
- **`/write-paper`** — observational-cohort Discussion exemplar gains power-aware null framing and an over-adjustment limitation.
- **`/revise`** — `requires_reanalysis` self-review findings auto-route to `/analyze-stats`; adds a Body-word-count-vs-cap exit gate (re-run `check_wordcount_cap.py` after every pass).
- **`/self-review`** — `--panel` now treats the SSOT-singularity gate (Phase 1 step 4) as a **blocking precondition**: if >1 manuscript-like `.md` exists and none is pinned (`SSOT.yaml` / `--ssot`), it halts before spawning reviewers rather than risk a whole panel on a stale copy.

No skill / reporting-guideline count change (45 / 36); integrity detectors 25 → 27 (`check_wordcount_cap`, `check_paren_spans`).

## [4.2.0] - 2026-06-15

### Added

- **Radiology / imaging-led case-report track (G33–G35)** — a dedicated layer for radiology, nuclear-medicine, and interventional-radiology case reports, grounded in six CC-BY radiology case reports (Europe PMC, learn-only under `distill.py`; `_corpus/` gitignored, no source prose reproduced). Adds a `write-paper` **`exemplar_case_report_radiology.md`** (per-modality technique→findings→impression discipline; structured-reporting lexicons BI-RADS/LI-RADS/PI-RADS/TI-RADS/Lung-RADS/O-RADS with category meaning; quantitative anchors with ROI method and threshold honesty; multimodality discordance + modality-completeness; an interventional-radiology procedure/complication subtype; incidental-finding reporting; DICOM de-identification, real alt text, and device-vendor COI) wired into Phase 0 for imaging-led cases; extends the `/peer-review` + `/self-review` case-report probe to **CR1–CR9** (CR9 imaging-led discipline); and adds a compact `/find-journal` **BJR Case Reports** profile (`journal_profiles_find` 72→73). No new skill or reporting-guideline count.
- **Case-report depth batch (G27–G30)** — extends the case-report feature, grounded in six CC-BY case reports (fetched via Europe PMC, learn-only under the `distill.py` license firewall; `_corpus/` gitignored). Adds a `write-paper` **case-series** paper type (`references/paper_types/case_series.md`) + Phase 0 case-series mode — a methods-light mini-cohort (design/identification/eligibility/protocol + all-cases summary table + cross-case synthesis), not N stacked single reports, enforcing counts-not-rates and selection disclosure; enriches `exemplar_case_report.md` with **adverse-event/pharmacovigilance** (Naranjo/WHO-UMC causality, dechallenge, severity/preventability, denominator framing) and **diagnostic-pitfall/mimic** (differential adjudication, diagnostic-delay framing, self-critical mechanism reasoning) subtypes; extends the `/peer-review` + `/self-review` case-report probe to **CR1–CR8** (CR7 adverse-event causality discipline, CR8 case-series design); and adds a `/make-figures` **annotated multimodality imaging-panel** exemplar (`exemplar_plots/imaging_panel.md`) for discordance/response figures, distinct from the clinical-timeline chronology figure. Also adds four compact `/find-journal` **case-report venue profiles** (Journal of Medical Case Reports, Cureus, Radiology Case Reports, BMJ Case Reports; `journal_profiles_find` 68→72, identity/scope verified from primary CC-BY articles, submission limits flagged for pre-submission verification) and enriches `/check-reporting` `CARE.md` with adverse-event (causality instrument) and case-series (cohort-methods) application notes. No new skill or reporting-guideline count (36).
- **Reverse-engineering batch — adjacent clinical-research scaffolds (reporting guidelines 32 → 36).** A scored, gap-register-driven loop (`reverse_engineer/`) added guideline-grounded scaffolds for clinical-AI areas the project did not yet cover, each authored under the license firewall (`distill.py`): own-words **educational summaries** of the guideline item *intent* (no verbatim wording from copyrighted/NC sources), with `_corpus/` raw sources gitignored. Four new vendored reporting checklists in `skills/check-reporting/references/checklists/` — **TRIPOD-LLM** (studies using large language models; numbered to the official 19-item scheme), **CONSORT-AI** + **SPIRIT-AI** (AI clinical-trial reports + protocols; close a pre-existing `MISSING_CHECKLIST_CONTRACT_VIOLATION` where both were routed/aliased but unvendored), and **DECIDE-AI** (early-stage live clinical evaluation of AI decision-support). Each wired end-to-end (alias map, fail-fast test, `LICENSES.md` row, Step 1 auto-detect row, `skill.yml` card) and CI-gated by `validate_catalog_consistency.py` (32 → 36).
- **METRICS radiomics appraisal reference (`skills/check-reporting/references/appraisal_tools/METRICS.md`)** — a methodological-quality / risk-of-bias tool (EuSoMII; Kocak et al. *Insights Imaging* 2024, CC BY 4.0), 9 categories / 30 weighted condition-dependent items. Deliberately placed under `appraisal_tools/` (NOT counted `references/checklists/`) so it does **not** inflate the reporting-guideline count — the repo keeps appraisal tools distinct from reporting checklists (`critical_item_floor.md`). Wired as the load-on-demand reference behind the Step 4f appraisal cross-check; reporting-guideline count stays 36.
- **New domain-probe module + AI-extension subsections** (`skills/peer-review/references/domain-probes/`, vendored byte-identical into `/self-review`). New module **`diagnostic_accuracy.md` (D1–D6)** for DTA primary studies + multi-reader multi-case (MRMC) reader studies (verification/spectrum/blinding bias, indeterminate handling, fully-crossed/washout design, reader+case variance). Plus AI reporting-flow subsections on three existing modules: **TRIPOD+AI (T1–T4)** on `survival_prognostic.md`, **CONSORT-AI/SPIRIT-AI (A1–A5)** on `rct_trial.md`, and **decision-impact (DI1–DI5, DECIDE-AI axis)** on `ai_overclaiming.md`. `MODULES` tuple 7 → 8; routed from both peer-review (new Phase 2I) and self-review.
- **Figure-anatomy exemplars (`skills/make-figures/references/exemplar_plots/`)** — four new synthetic, citation-free anatomy models: **`decision_curve.md`** (net-benefit / DCA), **`mrmc_roc.md`** (MRMC reader-study ROC with per-reader + reader-averaged curves and reader+case CIs), **`bland_altman.md`** (agreement: bias + ±1.96·SD limits with CIs, proportional-bias check, not-a-correlation discipline), and **`confusion_matrix.md`** (raw + row/column-normalized, class-imbalance caveat).
- **Table-type standards (`skills/analyze-stats/references/table-standards/table-types/`)** — **`incremental_value.md`** (added value beyond a baseline: paired ΔAUC + DeLong CI, NRI event/non-event split, IDI, net benefit) and **`reader_study.md`** (MRMC per-reader + reader-averaged performance with Obuchowski–Rockette/DBM reader+case CIs, per-patient vs per-lesion unit).
- **Structured-abstract exemplar (`skills/write-paper/references/exemplar_abstract.md`)** — completes the write-paper exemplar set (intro/methods/results/discussion already shipped); mandates a primary estimate with 95% CI + denominator and a failure-modes section (no estimate-free "significant", no body↔abstract number mismatch). Wired into Phase 6.
- **Case-report writing feature (G24–G26)** — adds a clean-room `write-paper` case-report exemplar (`references/exemplar_case_report.md`) for CARE narrative flow and 150-word Introduction / Case Presentation / Conclusion abstracts; a new byte-vendored `/peer-review` + `/self-review` case-report domain probe (`domain-probes/case_report.md`, CR1–CR6) covering novelty/teaching value, consent and image de-identification, n=1 causal overclaiming, literature-boundary claims, CARE timeline/follow-up completeness, and teaching-point scope; and a `/make-figures` clinical-timeline anatomy model (`exemplar_plots/clinical_timeline.md`) for CARE timeline figures and annotated imaging-panel pairing. No new skill or reporting-guideline count.

### Changed

- **CARE version label aligned to the vendored checklist** — `/write-paper` case-report mode and paper-type template now refer to CARE 2013, matching `/check-reporting`'s bundled `CARE.md` (Gagnier et al. 2014 / care-statement.org), instead of the previous CARE 2016 label.
- **Recommendation-calibration gate (Phase 2F) extended to review articles + fixable/unfixable tier-domination** (`skills/peer-review/SKILL.md`). Phase 2F (previously "AI/Method Papers" only) now also fires for **Review / narrative / primer** articles and adds three rules: (1) **fixable vs unfixable tier-domination** — when repairable defects (extraction errors, missing supplementary, mislabeled table) coexist with unrepairable ones (poolability of incommensurable studies, broken construct, invalid evaluation instrument), the unfixable class governs the recommendation; (2) **review/narrative escalation** — for a review article the distinct contribution (novelty/synthesis/domain-specificity) *is* the product, so weak-novelty/no-distinct-contribution is **unfixable-in-current-form** ("add a contribution" = a different paper) and escalates one tier toward Reject rather than defaulting to the revision/Reconsider tier; (3) **confidential-note Reject-grade self-grep** — deferring the value/priority judgment to the editorial board is itself a Reject-grade tell, not a neutral hand-off. QC items 11/12 and the final checklist updated. Sourced from a review-article (LLM-hallucination primer) decision self-audit in which the reviewer recommended a Reconsider tier and the editor rejected — the 6th lenient-calibration recurrence; diagnosis remains calibration discipline, not a new type-probe.
- **Narrative-review RV4/RV5 sub-probes** (`skills/peer-review/references/domain-probes/narrative_review.md`, vendored byte-identical into `/self-review`). **RV4** gains a **model-class conflation** check for LLM/VLM-in-radiology reviews (text-only LLM language-support vs multimodal VLM image-interpretation vs conventional CAD treated as one risk profile; the actionable radiology contribution is usually a task-risk stratification, not a generic "LLMs hallucinate" statement). **RV5** gains a **source/cause vs masking/amplifying-factor** check (e.g., black-box opacity and automation bias listed as "sources" of hallucination when they hide or amplify rather than generate it — a sharper defect than "scattered taxonomy"). Both are in-niche conceptual catches missed in the source review but caught by other reviewers; bundled into existing RV4/RV5 (no new RV, no probe-count change).
- **Narrative-review probe expanded RV1–RV8 → RV1–RV9** (`skills/peer-review/references/domain-probes/narrative_review.md`, vendored byte-identical into `/self-review`). Adds **RV9 — Bibliometric circularity of a curated base**: a non-systematic review asserting a field-level/bibliometric asymmetry ("the field invested in X, neglected Y") is making a *measured* claim from an *unmeasured*, author-curated base; a hostile reviewer manufactures the reverse thesis by re-curating. RV9 names the two acceptable resolutions as a strategy fork — down-scope every claim site to "within the surveyed literature" (zero field-level residue) **or** add a documented search + per-axis counts — plus the engineering-density-vs-clinical-validation reframe. **RV6** gains the single-anchor-overload check (Abstract "landmark" ↔ body "base is thin" register mismatch); **RV8** gains the self-citation-architecture disclosure check (weakest axes coinciding with the authors' own forthcoming work). The `/self-review` narrative panel reviewer-set gains an **R4 Adversarial reject-hunter** seat (structural: RV9/RV6/RV8), with a matching focus checklist in `panel_review_template.md`. No skills/detector count change. Probe-count pointers across peer-review / self-review / review-paper SKILLs and the AJR reviewer profile updated to RV1–RV9.

## [4.1.0] - 2026-06-11

Theme: **distribution + a submission pre-flight gate.** Ships the borrow-distribution levers (Claude Code plugin marketplace, the named MedSci-Audit detector registry, and standalone hero-skill mirror tooling with two live mirror repos) and a single submission pre-flight halt-on-failure gate that bundles the existing detectors + `/verify-refs`. Analysis-integrity detectors **24 → 25** (still 43 skills). Frozen `demo/` and `evaluation/runs/canonical` artifacts (pinned to the published methods paper) are unchanged.

### Added

- **Claude Code plugin marketplace (`.claude-plugin/marketplace.json`)** — one-line install via `/plugin marketplace add Aperivue/medsci-skills`, then `/plugin` discovery of eight `medsci-*` category plugins (`medsci-literature`, `-data`, `-analysis`, `-writing`, `-review`, `-submission`, `-project`, `-presentation`) mirroring the storefront categories. Generated from `metadata/skills_catalog.json` by `scripts/gen_marketplace_json.py` (a pure downstream transform — the SSOT chain stays single-source) and CI-gated with `--check` plus `tests/test_marketplace_json.sh` (validated by `claude plugin validate`). The marketplace tracks `main`: no `version` is emitted, so each plugin's version is its git commit SHA. No skills change (still 43).
- **MedSci-Audit detector registry (`metadata/detectors_catalog.json` + `MEDSCI_AUDIT.md`)** — names and enumerates the 24 deterministic analysis-integrity detectors (previously only *counted* in `catalog_counts.json`) as a citable suite grouped into six audit families. Generated by `scripts/gen_detectors_catalog_json.py` using the same `skills/*/scripts/` glob as `validate_catalog_consistency.py`, so `detector_count` always equals `catalog_counts.json::integrity_detectors` (24); CI-gated with `--check` + `tests/test_detectors_catalog_json.sh`. `MEDSCI_AUDIT.md` documents the suite, the anti-hallucination vs mechanical-fix split, and keeps the current catalog (24) distinct from the v3.8-era canonical evaluation evidence (E1: 19 specs / 17 injectors; E7: n=21). No skills change (still 43).
- **Hero-skill standalone mirrors (`metadata/hero_skills.json` + `scripts/sync_hero_skill.py`)** — distribution lever: mirror a focused single skill out to its own repo as a star funnel that backlinks to the full suite. `sync_hero_skill.py` builds a complete standalone tree (skill copied verbatim + generated README/LICENSE/CITATION.cff/`.claude-plugin/marketplace.json`/installer/minimal CI; author metadata read at runtime from the canonical `CITATION.cff`) and force-pushes it; `.github/workflows/mirror-hero-skills.yml` auto-syncs on `main` changes (no-ops without the `HERO_SKILL_TOKEN` secret). First hero: **`verify-refs`** → [`Aperivue/verify-refs`](https://github.com/Aperivue/verify-refs). The canonical `verify-refs` SKILL.md companion note was made tool-agnostic so it mirrors verbatim. CI-gated with `tests/test_sync_hero_skill.sh`. No skills change (still 43).
- **Second hero skill: `check-reporting`** → [`Aperivue/check-reporting`](https://github.com/Aperivue/check-reporting) — audit a manuscript against 32 EQUATOR reporting guidelines. Added as one `hero_skills.json` entry (no new tooling). The skill's `references/LICENSES.md` third-party carve-out (CC BY-NC for CARE / MI-CLEAR-LLM, RSNA for CLAIM) is carried into the standalone `LICENSE` by the sync script. `tests/test_sync_hero_skill.sh` now builds and verifies every hero skill (28 checks). No skills change (still 43).
- **Placeholder/marker detector (`skills/write-paper/scripts/check_placeholders.py`)** — promotes the previously grep-in-prose pre-submission marker check (write-paper Phase 0/7, self-review Phase 2.5c) to a deterministic, CI-tested gate. Flags unresolved `[@NEW:topic]` citation placeholders, AI-disclosure `[version]/[date]/[tool]/[model]/[channel]` tokens, `TODO`/`FIXME`/`TBD`/`XXX` markers, and template/empty URLs (`example.com`, `doi.org/XXXX`, empty `]( )`, `[URL]`) as **blockers**; bare `[N]`/`[N–N]` numeric citations as **warn** (legitimate in Vancouver style — escalated with `--strict`). Guards skip fenced code blocks and the References section. Stdlib-only; exit 1 on any blocker. Registered in the MedSci-Audit catalog under *citation & reference integrity*, bringing the analysis-integrity detector count **24 → 25**; CI-gated by `gen_detectors_catalog_json.py --check` + `skills/write-paper/tests/test_placeholders.sh` (A5). No skills change (still 43).
- **Submission pre-flight gate (`skills/sync-submission/scripts/preflight_gate.py`)** — the single last-step-before-freeze halt check. Orchestrates the existing detectors + `/verify-refs` into one command that writes an aggregated manifest (`qc/preflight_gate_report.json`) and **exits non-zero on any blocker** so a build/CI wrapper halts the freeze. Composes the per-check scripts via subprocess (reimplements none); the halt decision is driven by each sub-check's normalized exit code, not by parsing its JSON. By default it halts only on the unambiguous deterministic errors (**P0**: leftover placeholders, undefined `[@key]` citations, duplicate references, canonical-vs-submission hash drift); the heuristic/conditional checks (`check_xref`, `detect_copy_divergence`, `scope_drift_check`, `cover_letter_drift_check`, `cross_document_n_check`, `check_cross_artifact_stale`) run and report as **P1 warn** unless promoted with `--strict`/`--require`, and `check_asset_anonymization` under `--double-blind`. Absent inputs are `skipped`, never blockers (tolerant of projects with no docx/cover letter/copies). Normalizes the inverted `cover_letter_drift_check.py` exit code. The offline references pass is the deterministic subset (duplicates + pagination placeholders); an online `/verify-refs --strict` remains the authoritative fabrication/author check. CI-gated by `skills/sync-submission/tests/test_preflight_gate.sh` (A6). Not a detector (no catalog change); no skills change (still 43).

## [4.0.0] - 2026-06-10

Theme: extend the project's own deterministic, no-drift SSOT discipline to the public storefront, finish the detector backlog, and roll up the English-canonical i18n migration. Analysis-integrity detectors **21 → 24** (still 43 skills). Frozen `demo/` and `evaluation/runs/canonical` artifacts (pinned to the published methods paper) are unchanged.

### Added

- **Storefront catalog SSOT (`metadata/skills_catalog.json`)** — a generated, machine-readable catalog (slug + research-lifecycle category + one-line description for all 43 skills, derived from each `SKILL.md` + `skill.yml` `owner_domain`) via `scripts/gen_skills_catalog_json.py`, CI-gated with `--check`. The aperivue.com storefront vendors this file behind an offline sync gate so the public site can never silently drift behind the repo (it had shown 40 skills while the repo shipped 43).
- **Asset/figure anonymization gate** — `skills/sync-submission/scripts/check_asset_anonymization.py` scans figure-generating scripts, figure-PDF rendered text, and docx/PDF metadata authors (`dc:creator`, `/Author`) for the institution/author leaks a body-text scan misses. Generic English+Korean institution patterns + a local-only `--names-file`; degrades gracefully when poppler is absent.
- **Cross-artifact staleness gate** — `check_cross_artifact_stale.py` flags supplement values that disagree with the corrected body (reconciliation-prone labels) and reporting checklists built against an older manuscript version. `/check-reporting` now emits a `target_manuscript` / `target_version` / `source_sha256` contract (report `check_reporting_version` 1.1) verified by `check_checklist_version.py`.
- **Survival reporting hardening** — `/analyze-stats`'s survival template now reports median survival with its 95% CI, a Cox events-per-variable gate, and cluster-robust (cluster-sandwich) SE for nested observation units (`--cluster`); the cluster-robust rule extends to logistic/linear regression.
- **Language Policy + locale-inventory gate** — MedSci Skills is now explicitly English-canonical: skill mechanics and prose are English, and non-English (currently Korean) text is allowed only as a labeled locale feature, a locale-jurisdiction mode (e.g. `grant-builder`'s Korean Government Grant Mode), a bilingual `triggers:` alias, or an opt-in `*_ko` variant. A new [`docs/locale_inventory.md`](docs/locale_inventory.md) lists every Korean-bearing file under `skills/` with a one-line justification, and a new stdlib detector `scripts/check_locale_inventory.py` (wired into CI + `tests/test_locale_inventory.sh`) fails if any Korean-bearing file is missing from that inventory — the authoritative allowlist, complementing the WARN-only Korean-prose check in `validate_skills.sh`. CONTRIBUTING gains a Language Policy section + PR-checklist item. This is the policy/scaffold step (PR1); incidental-prose translation (PR2) and English-default-with-Korean-opt-in redesign (PR3) follow. Catalog unchanged at 43 skills.

### Changed

- **English-canonical translation of incidental skill prose (PR2)** — translated leftover Korean *prose* to English across 12 files with zero functional loss: `humanize/references/ai_patterns.md` (Patterns 19–21), the four `meta-analysis/references/*.md` (data-integrity / release-ops / review-orchestration / package-drift), `meta-analysis/SKILL.md`, `ma-scout/SKILL.md` (internal tables), `author-strategy/SKILL.md` (example query), `define-variables/{references/common_definitions.md, templates/variable_operationalization.md}`, `check-reporting/references/step4d_prisma_figure_audit.md`, `write-paper/references/section_guides/step7_1_classical_qc.md`, `orchestrate/references/dialogue_nodes.md`, and `peer-review/references/reviewer_profiles/RYAI.md`. Functional/locale Korean is preserved and inventory-tracked (KNHANES labels, Korean PHI pack, Korean-form-matching demo in `fill-protocol/references/best_practices.md`, bilingual triggers). The `validate_skills.sh` Korean-prose check now passes for every skill except one inventory-justified locale example. No behavior change; catalog unchanged at 43 skills. (PR3 = English-default + Korean-opt-in redesign follows.)
- **English-default skills with opt-in Korean (PR3)** — the skills that previously *defaulted* to Korean output/interaction now default to English, with Korean preserved as an opt-in `*_ko` variant or via a "communicate in the user's preferred language" instruction. User-facing prompts are English by default (`write-paper` Discussion-planning Q1–Q5 + review prompt, `analyze-stats` / `make-figures` / `orchestrate` PHI prompts, `fill-icmje-coi` co-author email). `present-paper` speaker-notes default to the user's language (Korean register still supported; pronunciation dict + legacy Korean slide-marker parser kept). `lit-sync` defaults to English vault folders (`Literature/`, `Concepts/`) and English note headings but **honors an existing Korean vault layout** (never renames a user's folders); the Korean layout + templates move to `references/locale/ko/note_templates.md`. `render-pdf-doc` body/skill.yml are English and each `templates/*.md` starter gains a `*_ko.md` Korean sibling; `orchestrate/references/report_template.md` and `ma-scout/references/project_readme_template.md` become English defaults with `*_ko.md` variants. The locale inventory is reconciled (50 Korean-bearing files, all justified; `check_locale_inventory.py --strict` clean). No catalog change (43 skills); the 7 new `*_ko`/locale files are opt-in variants, not new skills.
- **Locale labels + finalize (PR4)** — added explicit "Locale: Korean" header notes to the whole-file Korean locale references (`render-pdf-doc/references/{pandoc_korean_cheatsheet,known_pitfalls}.md`, `deidentify/references/korean_phi_patterns.md`) so an internal reader sees the intent immediately, and marked `docs/locale_inventory.md` as migration-complete (steady state). The English-canonical migration is now complete: every remaining Korean string is a justified locale feature, a Korean-jurisdiction mode (`grant-builder`'s Korean Government Grant Mode), a bilingual trigger, or an opt-in `*_ko` variant. Validator #9 stays WARN-only by design; `check_locale_inventory.py` is the authoritative allowlist gate.

## [3.8.0] - 2026-06-07

An `evaluation/` harness suite that validates the instrument itself, plus a reconcile of the README Live-Demos numbers with the v3.7.0 clean-room demo artifacts. Catalog unchanged at 43 skills, 21 detectors — this release adds tooling and tracked evidence, not skills.

### Added

- **Evaluation harness suite (`evaluation/`)** — stdlib-only harnesses that validate the tool (not manuscript quality): **E1** seeded-defect detector benchmark (one defect injected per temp copy, recall + clean false-positive rate; offline-deterministic with a `--check` reproducibility-hash gate; network-required citation defects marked NOT_RUN unless `--online`), **E4** fresh-clone manifest reproducibility (`--ref` RC-SHA pre-tag / `v3.8.0` tag post-tag), **E5** claim audit-trail completeness (deterministic provenance pre-fill: manuscript → analysis table → manifest → QC), **E6** host-portability smoke (installer `--self-test` + path-contract scan + host-target mapping), **E7** detector coverage inventory, **E8** catalog claim-drift resistance (temp-copy only), and **E3** cost/time. Each run writes a self-describing log package (`run_manifest.json` with per-component determinism class + input/output hashes, `commands.sh`, `environment.txt`, `git_commit.txt`, `metrics.csv`, `limitations.md`). A committed canonical run lives under `evaluation/runs/canonical/`. The LLM comparator (**E2**) and a self-review convergence harness (**E9**) ship runnable with MI-CLEAR-LLM-inspired logging but are NOT executed in this release (graceful NOT_RUN without an API key / runner). All harnesses operate on temp copies and never mutate the real `demo/` tree or repo.

### Changed

- **README Live-Demos reconcile** — demo numbers re-derived from the v3.7.0 QC artifacts (STARD 60.9% (14/23), PRISMA 57.1% (24/42), STROBE 83.3% (25/30); Demo 3 analytic N 5,010; Demo 3 adjusted OR 3.03 (2.29–4.02); self-review verdicts from `qc/self_review.md`); figure links relinked to actual paths (`forest.png`, `forest_or.png`, `figures/stard_flow.svg`); unproduced slide/cover-letter/bubble-plot entries removed. Provenance for every number is logged in `evaluation/_readme_reconcile_sources.md`.

## [3.7.0] - 2026-06-07

Three new deterministic, stdlib-only detectors extend the v3.6.0 panel-derived gates — reference *adequacy*, panel lens-diversity, and generated-code quality — bringing the analysis-integrity detector count in `skills/` to 21. A publish-time skill-worthiness gate and public adoption/impact tracking round out the release. Catalog unchanged at 43 skills; every addition is a check, probe, or convention inside an existing skill.

### Added

- **Reference adequacy gates (`/self-review` Phase 2.5c-2, `/write-paper` Step 7.3c, `/search-lit`)** — a new stdlib detector `scripts/check_reference_adequacy.py` adds a reference *adequacy* layer (enough refs, the right sections, every named method cited), complementing the existing reference *integrity* gate (`/verify-refs`). The dominant failure mode in an autonomous draft is a Statistical Analysis subsection that names a competing-risk model, multiple imputation, the E-value, and an eGFR equation with zero citations — internally consistent prose no integrity check flags. The checker carries an article-type alias map + count targets, a two-tier named-method registry (STATISTICAL → Major / GUIDELINE → Minor), and paragraph-level citation clustering; `/self-review` Phase 2.5c-2 folds findings into `issues[]` (category F). `/write-paper` Step 7.3c invokes the same checker via the `${MEDSCI_SKILLS_ROOT}` cross-skill pattern and loops `/search-lit → /lit-sync → /verify-refs`; `/search-lit` gains a "Manuscript Paper Reference Pool" mode (25–40 candidates across six categories, appended to `references/library.bib` only). Every finding is `fixable_by_ai:false` (diagnose only). PII-free fixtures + regression test (#88).
- **Adoption & impact tracking** — a public [`IMPACT.md`](IMPACT.md) dashboard, an automated weekly metrics snapshot (`.github/workflows/metrics.yml` → `metrics/traffic_log.csv`, capturing stars/forks/release-downloads/14-day traffic/Zenodo stats that GitHub otherwise discards after 14 days), a [`docs/citations.md`](docs/citations.md) ledger for academic citations and named downstream use, and a "Used in research" issue template (`.github/ISSUE_TEMPLATE/used-in-research.yml`) for collecting user reports. No skill behavior changes; catalog unchanged at 43 skills.
- **Skill-worthiness gate (`/publish-skill` Phase 0.5)** — before the PII scrub, a three-way gate (Uniqueness: not reconstructable by a 5-minute web search; Specificity: encodes a domain/workflow heuristic, not a generic snippet; Effort: took real debugging, design, or reviewer-anticipation effort) decides whether a workflow merits distribution as a skill at all. A failing workflow is routed to documentation or a memory note rather than diluting the catalog — the publish-time analogue of the "reusable pattern vs one-off hack" distinction. Prose-only.
- **Panel lens-diversity gate (`/self-review` Phase 2.6, `--panel`)** — a new stdlib detector `scripts/check_panel_diversity.py` post-processes the panel's reviewer outputs so its cost buys breadth, not a louder echo of one theme: `UNCOVERED_AXIS` (an axis the research type is expected to probe drew zero major findings — re-probe before finalizing), `FAMILY_MONOCULTURE` (the majors concentrate in one concern family), and `LENS_COLLAPSE` (a fully-redundant reviewer adding no independent axis). Healthy CONSENSUS is preserved — the checks fire on panel-level coverage and full redundancy, never on agreement. A new Step 3.5 wires it into the editor synthesis, and `panel_review_template.md` documents the expected-axis manifest. PII-free fixtures + regression test.
- **Generated-code quality gate (`/analyze-stats` Phase 3.5; pointers in `/batch-cohort` rule 10 and `/make-figures`)** — a new stdlib detector `scripts/check_generated_code.py` lints emitted `.py`/`.R` analysis scripts for the reproducibility/integrity slop AI-generated code recurrently carries: `MISSING_SEED`, `HARDCODED_DATA_LITERAL` (hand-typed tabular data instead of read_csv + subset — the data-integrity rule), `HARDCODED_ABS_PATH`, and `INPLACE_SOURCE_OVERWRITE` (writing to the source path) as Major, plus `DEBUG_LEFTOVER` and `UNUSED_IMPORT` flags. Conservative on the Major checks (Python uses AST for unused-import detection). Dogfooding it over the shipped analysis templates surfaced and removed ten genuinely dead imports. PII-free fixtures + regression test. Catalog unchanged at 43 skills.

## [3.6.0] - 2026-06-06

A 13-project panel self-review distilled 158 cross-project traces into 12 recurring defect patterns; this release lands the 18 resulting gates (P1/P2/P3) as deterministic, stdlib-only checks wherever a grep is clean, and as prose/probe guidance where the call needs a human. Six new detectors join the existing trio, each with PII-free synthetic fixtures and a regression test. Catalog unchanged at 43 skills — every addition is a check, probe, or convention inside an existing skill.

### Added

- **Cohort arithmetic gate (`/self-review` Phase 2.5 / 2.5b)** — a new stdlib detector `scripts/check_cohort_arithmetic.py` recomputes the numbers a reviewer checks by hand: `RATE_BACKCALC` (an incidence rate must invert to its own events ÷ person-years), `CASCADE_SUM` (a STROBE exclusion cascade must balance — start − Σexclusions == final; total − missing == complete), and `PARTITION_OVERLAP` (an ordinal tier/stratum split claimed disjoint must satisfy Σn == unique total and Σevents == total events; all-equal-n is a stratum-total mis-entry). Parses prose equations + GFM tables, recomputes from a committed CSV when given one. Phase 2.5b's screening-count reconciliation is extended from SR/MA to observational tier/stratum partitions.
- **Methods ↔ Results ↔ disk artifact coverage (`/self-review` Phase 2.5f, `/write-paper` Step 7.3b)** — a new detector `scripts/check_artifact_coverage.py` reconciles both directions: `PROMISED_ABSENT` (an analysis named in Methods that never reaches Results) and `DISK_UNREPORTED` (an analysis output on disk — an added-value DeLong CSV, a calibration table — never mentioned in the body, the run-but-unreported result that may undercut the headline). The reverse direction is calibrated against false positives via an `_analysis_outputs.md` manifest (source of truth when present) and analysis-bearing file-stem escalation otherwise.
- **Endpoint ↔ conclusion scope gate (`/self-review` §D, `/design-study`, `/write-paper`)** — a new detector `scripts/check_scope_coherence.py` flags `CROSS_SECTIONAL_PROGNOSTIC` (a cross-sectional/single-visit design with a prognostic or surveillance conclusion) and `SURROGATE_CARE_DIRECTIVE` (a binary surrogate endpoint driving a defer/withhold/initiate-therapy directive). Fires only when a design/endpoint signal and a conclusion-region action verb co-occur.
- **Reporting-framework naming audit (`/check-reporting` Step 4e)** — a new detector `scripts/check_framework_naming.py` flags `BASE_MISSING` (an AI extension — PROBAST+AI, STARD-AI, TRIPOD+AI, PRISMA-DTA — invoked without naming/citing its base instrument), plus `HYPHEN_MIX`, `CITE_MISSING`, `SELF_COINED_LABEL`, and `VAGUE_GUIDANCE` ("adapted per recent guidance"). `/write-paper` Step 7.1 adds an AI-disclosure meta-applicability gate (a disclosure paragraph must itself carry version + access channel + date range + responsible party, with zero placeholders).
- **Classical-style body lint (`/self-review` §J, `/write-paper` Step 7.1)** — a new detector `scripts/check_classical_style.py` flags `SECTION_SYMBOL` (any § in the body) and `INBODY_AI_DISCLOSURE` (an AI-disclosure paragraph that belongs on the title page) as Major, and `ELIGIBILITY_PROSE`, `DECIMAL_INCONSISTENCY` (mixed OR/HR decimal places), `EM_DASH_OVERUSE` as Minor — the machine-checkable subset of the classical-QC checklist.
- **Reviewer-team 3-way (`/self-review` §K)** — `scripts/check_reviewer_team_consistency.py` extends beyond the dual-claim/single-confession conjunction to the prose ↔ JSON ↔ confession 3-way: an LLM named in an extraction JSON's reviewer field (`--extraction-json`) is fatal (a tool is not a reviewer), and a future-tense deferred mitigation ("will be completed before submission") is a Major. The existing contract is preserved.
- **Estimand & CI output contract (`/analyze-stats`)** — quantile estimands (T25, median time-to-event), pooled proportions, and subdistribution HRs must emit a 95% CI, not a bare point estimate; a Cox events-per-variable ≥ 10 gate (Firth/penalized fallback); single-arm proportion meta-analysis bans Egger's (Peters'/arcsine, k ≥ 10) and standardizes τ² + a 95% prediction interval; naive Wilson CIs on study-nested proportions are flagged; Fine-Gray requires a subdistribution-PH check. Interaction/synergy questions must anchor the estimand to the interaction parameter, and equivalence claims must declare a margin (TOST/MCID).
- **Stratified & survival reporting (`/analyze-stats`)** — a strata-disjointness gate before any Cochran-Armitage trend test; a secondary stratum-HR checklist (referent + per-stratum events + sparse caveat); a proportion-CI lower-bound clamp to max(0, ·); an interval-censoring auto-trigger for visit-dated events; a PH-violation rule (piecewise/time-stratified HR, never a single time-averaged HR); and a number-at-risk requirement when a KM/CIF is quoted past median follow-up.
- **Meta-analysis pool & method guards (`/meta-analysis`)** — the FINAL_POOL_LOCK now also locks patient/lesion aggregate totals (arm-separable vs both-arm), a "fixed"/"resolved" audit note requires re-run evidence, the k=1-subgroup lesson extends to k < 4, a PROSPERO ID format gate (`^CRD42\d{9}$`, 14 chars) lands in both `/meta-analysis` Phase 1 and `/check-reporting` Step 4c, plus new lessons on outcome harmonization (do not pool different outcome definitions into one range) and heterogeneous-RoB κ (per-instrument agreement, never one pooled κ), and a flag → form-edit forced transition in Phase 4c.
- **Leakage, time-origin & construct concordance (`/design-study`, survival probe)** — Phase 2 gains a time-origin & survivorship subsection (immortal time, left-truncation, mediator-ascertainment-window survivorship, complete-case primary-set selection) and the survival domain-probe S1 escalates a "not formally assessed" self-confession to Major; Phase 2C adds construct ↔ nominal-definition match, per-flag reference-standard concordance, and a manuscript-definition ↔ `variable_operationalization.md` cross-check.
- **Reference placeholder gate (`/verify-refs` Gate 6, `/self-review` Phase 2.5c, `/write-paper` Phase 0)** — `verify_refs.py` flags pagination/publication-stage placeholders (`e000–e000`, `in press`, `TBD`, `forthcoming`) as `UNVERIFIED + note="pagination_placeholder"` while staying manuscript-agnostic; the centrality call (a method/headline-load-bearing cite → P0) is made by `/self-review` Phase 2.5c, and `/write-paper` Phase 0 blocks bare `[N]`/`[N–N]` citation placeholders alongside `[@NEW:]`.

## [3.5.0] - 2026-06-06

Analysis-integrity guards across the manuscript pipeline — backporting the findings a multi-agent panel review caught into deterministic, stdlib-only single-pass checks, and pushing them upstream into the source, writing, figure, and submission stages. Catalog unchanged at 43 skills; the new probes are checks and reference files inside existing skills.

### Added

- **`/self-review` category C — power-aware null interpretation**: a new check that scores non-significant primary results (p > 0.05, 95% CI crossing the null) for whether the analysis is powered to *exclude* a clinically meaningful effect. An underpowered null is flagged as "not yet established" rather than "no effect," and the check watches for bilateral over-correction (a prior overclaim swinging to an equally unsupported negative claim during revision). Undocumented null = Minor; a null driving a clinical recommendation without power/CI-compatibility justification = Major. Backports a panel-only finding into the single-pass review (prose check, no new dependency).
- **`/self-review` Phase 2.5e — confounding completeness (observational)** + a new **`observational_confounding.md` domain-probe module (O1–O6)**: a deterministic gate (`scripts/check_confounding_completeness.py`, stdlib-only) joins the exposure-stratified Table 1 against the Methods adjustment set and flags every covariate that is measured, imbalanced by exposure (p < 0.05 or SMD > 0.1), yet absent from the adjustment set as an `UNADJUSTED_IMBALANCED` Major candidate, with an extended-adjustment sensitivity fix. The O1–O6 probe module (confounding completeness, adjustment-set provenance, selection/collider bias, exposure measurement validity, missing-data / complete-case collapse, residual-confounding E-value) closes the gap where observational studies had no domain-probe set; it is vendored byte-identical into `/peer-review` (canonical, new Phase 2E) and `/self-review`, and added to the `check_domain_probe_sync.py` drift gate (now 5 modules). `/design-study` gains a matching DAG-first adjustment-set planning note. Backports the panel's highest-yield observational finding into the single-pass review.
- **Structural-zero / dose-duration covariate guards (`/analyze-stats`, `/clean-data`, `/define-variables`)**: a coupled source-side defense against the most common observational miscoding — a dose/duration variable anchored to a categorical exposure (pack-years under smoking status, grams/week under alcohol use). `/clean-data` gains a Stage-2 flag for *categorical-implied zeros* (a `never` record with a NULL dose is a contradiction, not missing data) plus a stdlib detector `scripts/check_structural_zero.py`; `/analyze-stats` gains a "Covariate Pitfalls" section warning against imputing structural zeros (MICE fabricates a non-zero dose for the unexposed) and against complete-case collapse (the unexposed stratum is silently dropped, shrinking n 40–60%), recommending adjustment on the categorical status with the continuous dose reserved for an exposed-only secondary analysis; `/define-variables` gains a matching failure mode requiring `IF status == 'never' THEN dose = 0` to be operationalized explicitly. Synthetic PII-free fixtures + regression test included.
- **`/self-review` Phase 2.5f — claim-vs-artifact cross-check** + survival probe **S8 (estimand provenance)**: a deterministic gate (`scripts/check_claim_artifact.py`, stdlib-only) checks claims against the artifacts they should trace to — it flags `PRIMARY_REASSIGNED` / `ESTIMAND_DRIFT` when the manuscript's primary contrast was re-designated after results were known or does not match the pre-registration, and `EVALUE_ARITHMETIC` / `EVALUE_NON_PRIMARY` when a reported E-value does not recompute from its primary estimate or is borrowed from a secondary one. A primary-change guard accompanies it. The survival/prognostic domain-probe module gains **S8 (estimand provenance)** and an **S2** note on structural-zero covariates collapsing the complete-case Cox sample (both vendored byte-identical into `/peer-review` canonical Phase 2B and `/self-review`; module now S1–S8). Figure/flow-count, Methods-promised-analysis, and imputation-input subchecks are reserved in the JSON schema for follow-up. Backports the panel's estimand-provenance findings into the single-pass review.
- **`/write-paper` Step 7.3b — estimand provenance & promised-analysis audit** + Abstract estimand-shopping guardrail: a new Phase-7 step delegates the claim-vs-artifact cross-check to `/self-review` Phase 2.5f (P0 blocker → Audit Recovery on `PRIMARY_REASSIGNED` / `ESTIMAND_DRIFT` / `EVALUE_ARITHMETIC`) and adds an inline Methods→Results promised-analysis grep (a promised-but-absent analysis HALTs the pipeline). Phase 6 (Abstract) gains a guardrail to lead with the *pre-specified primary estimand* rather than the largest effect — tightening effect-size language is fine, but promoting a secondary/exploratory/post-hoc estimate to the headline is estimand shopping. Prevents the estimand-provenance failure at write time.
- **`/make-figures` — Figure 1 caption ↔ flow-SSOT reconciliation**: a new stdlib detector `scripts/derive_figure_legend_counts.py` re-derives participant counts from the flow-diagram config (the SSOT consumed by `generate_flow_diagram.R`) and flags any `n = N` in the Figure 1 caption that is not a box count in the diagram (the classic "caption says n = 1,284 analytic, box says n = 998" defect that surfaces only at submission). Parses the config as text, so it is flow-tool-agnostic; pairs with numerical-safety's re-derive-every-revision rule. Synthetic fixtures + regression test included.
- **`/sync-submission` Phase 8 + Gate 11 — multi-copy manuscript divergence**: a new stdlib detector `scripts/detect_copy_divergence.py` compares a designated SSOT manuscript against each hand-maintained copy (circulation, portal) and reports the SSOT numeric claims (`n = N`, percentages, `p`, OR/HR/RR, 95% CI) and headings that did not propagate — the "14 edits applied to the SSOT, only 8 reached the portal copy" failure. A `STALE_COPY` is a P0 blocker; the recommended fix is to generate the variants from the single SSOT via a build step rather than hand-maintain parallel copies. Claims match as normalized strings (wording differences do not register). Synthetic fixtures + regression test included.
- **Incremental-value probe (`/design-study`, `/write-paper`)**: when a study frames a model/marker as adding value *beyond* an existing tool, `/design-study` Phase 3 now requires pre-specifying the in-routine-use baseline comparator plus an incremental metric (ΔC-index/ΔAUC with a paired CI, NRI, IDI, or decision-curve net benefit), and `/write-paper` Results requires the nested-model comparison to be reported — a standalone discrimination number does not support a "beyond X" claim, and the gap cannot be filled post hoc without the baseline model. Prose-only.

## [3.4.0] - 2026-06-06

Dual-review consolidation and a multi-agent panel mode for self-review — depth without broadening the catalog (still 43 skills).

### Added

- **`/self-review --panel`**: an opt-in multi-agent panel mode — several domain-expert reviewers run independently (blinded), then an editor consolidates their findings with CONSENSUS (≥2-reviewer) flags and R1/R2/R3 attribution, for a high-stakes pre-submission final pass. The default single-pass review stays the fast path. Portable across hosts: parallel subagents where the host provides them, with an explicit sequential blinded fallback and no `Workflow`-tool dependency. Output maps onto the existing Fatal/Fixable framing and R0 numbering, so `/revise` still consumes it; ships a PII-scrubbed `panel_review_template.md` and a structural + leak test (PR #73).
- **Shared domain-probe modules**: the SR-MA (P0–P10), survival/prognostic (S1–S7), radiomics (R1–R4), and narrative-review (RV1–RV8) critique probes are now reusable modules under `references/domain-probes/`, vendored byte-identical into both `/peer-review` (canonical) and `/self-review`. This closes the gap where `/self-review` had no survival / time-to-event probe set. A new `scripts/check_domain_probe_sync.py` drift gate (sha256 byte-identity) is wired into CI and `validate_skills.sh` (PR #72).
- **`/orchestrate`**: routes harsh / top-tier / multi-reviewer requests to `/self-review --panel`; the panel is opt-in and never auto-applied in chains or `--e2e` (PR #73).

### Changed

- **`/peer-review` Phase 2A–2D** now point to the shared domain-probe modules instead of carrying the probe bodies inline; the Major / Minor + Confidential-to-editor routing is applied at the pointer, so review behavior is unchanged. `references/reviewer_profiles/`, the Aczel tone audit, and `narrative_review_audit.md` remain peer-review-only (PR #72).

Catalog unchanged at 43 skills — the panel is a mode of an existing skill, and the probes are reference files inside existing skills.

## [3.3.0] - 2026-06-03

Packaging, portability, and trust signals — sharpening the "submission-grade clinical manuscript workflow" wedge without broadening scope.

### Added

- **Per-skill Quality Cards**: every skill now ships a `skill.yml` (42/42) with an optional, additive **v2.1 quality-card** extension — `purpose`, `safety_boundaries`, `known_limitations`, `validation_commands`, and a strict `evidence_surface` label (`ci_validator` / `demo` / `bundled_script` / `manual_workflow` / `not_yet_demonstrated`). `scripts/gen_skill_docs.py` renders the card into each `docs/skills/` page and tags the index with each skill's evidence level. Labels are grounded in repo reality, not asserted (PR #57, #58, #59).
- **`docs/skills/AUDIT.md`**: the validation story grounded in the actual CI gates and the three manifest-locked demos, with explicit trust boundaries — what is automated, what is reviewed by hand, and what is deliberately not claimed (PR #59).
- **`docs/host_compatibility.md`**: a verified host-compatibility matrix (Claude Code, Codex, Cursor, GitHub Copilot). Each VERIFIED cell carries a source URL and retrieval date; OpenClaw/Hermes are marked UNVERIFIED-roadmap. Confirms Codex reads `~/.agents/skills` and that Cursor + GitHub Copilot read the same directories as Claude Code, so the existing two install targets already cover four hosts (PR #60).
- **`docs/competitive_positioning.md`**: a neutral comparison to broad skill catalogs, with caveated, dated skill counts (PR #54).
- **`installers/install.py --self-test`**: simulates Claude/Codex/Cursor installs into temporary directories, asserts every skill is discoverable, and proves no real host directory is touched; real installs now run a post-copy discoverability check (PR #56).

### Changed

- **README positioning sharpened**: adds the canonical lines (a submission-grade clinical manuscript workflow; competes on clinical submission reliability, not skill count), removes volatile competitor skill counts from the body, and softens the citation claim to validator-backed language (reference-verification gates + citation-audit workflows) (PR #54).
- **`skill.yml` contract now required**: with all 42 skills shipping a contract, a missing `skill.yml` is a CI failure rather than a migration warning — closing the v1→v2 migration (PR #57, #58).

### Fixed

- CITATION.cff EQUATOR-guideline count corrected from 33 to 32 (matches the catalog count SSOT).

## [3.2.0] - 2026-06-01

### Added

- **`/version-dataset`** (new skill, brings the catalog to 42): dataset version control — a deterministic content-hash manifest (file SHA-256 + tabular schema + per-column value hashes), `verify` to detect drift (schema / row-count / value changes), and `diff` between versions. Each bundled `demo/*/` now carries a `manifest.lock.json` (input data + deterministic result tables) verified in CI — closing codex Improvement E (demo reproducibility).
- **`/generate-codebook`** (new skill, brings the catalog to 41): generates a citable data dictionary / codebook (`codebook.md` + `codebook.json`) from a tabular dataset, profiling variable role / type / level frequencies / range / missingness. Coded variables whose level meanings are unknown are flagged `[NEEDS DICTIONARY]` rather than guessed — the generator side of the dictionary-first workflow; feeds `/define-variables`.
- `/calc-sample-size`: observational-cohort precision-branch reference for retrospective / fixed-extract studies (PR #40).
- `/verify-refs`: **v1.3.0** full-author cross-check via PubMed `efetch` — co-author hallucinations at positions #2..#N are now caught, not just the first author; `schema_version` → 4 (PR #41).
- `/check-reporting`: fail-fast guard (`scripts/check_checklist_exists.py`) — a routed guideline with no vendored checklist now halts with `MISSING_CHECKLIST_CONTRACT_VIOLATION` instead of silently constructing items from model memory; from-memory requires explicit `--allow-from-memory` (PR #42).
- `/check-reporting`: vendored four previously-gitignored checklists — **CONSORT 2025, SPIRIT 2025, CARE 2013, CLAIM 2024** — with per-file license attribution and a "Third-party licenses" note (PR #43, #45).
- `scripts/validate_routing_assets.py`: CI gate that every `${CLAUDE_SKILL_DIR}` asset reference and check-reporting checklist bullet resolves to a real file (PR #43).
- `metadata/catalog_counts.json` + `scripts/validate_catalog_consistency.py`: single source of truth for skill / guideline / journal-profile counts, wired into CI — public-doc counts that drift from disk now fail the build. The check now also gates the README shields **badge** (`Skills-N`) and matches guideline-count claims case-insensitively, so a drifted badge or section heading fails CI (PR #50).
- **`/revise`**: R1 vs R2+ cover-letter protocol — on a second-or-later revision the editor cover letter folds into the response-letter "head" rather than a separate document; adds a "Succinctness & non-defensiveness (R2+)" voice section, a synthetic before/after gallery, and matching verification gates. `/humanize` cross-references it as a triage cue (PR #51).
- **Contributor funnel**: GitHub issue forms (skill request / bug report / docs improvement), a pull-request template, `CODE_OF_CONDUCT.md` (Contributor Covenant 2.1 by reference), and `docs/seed_issues.md` (PR #50).

### Changed

- **Reporting-guideline count corrected from 33 to 32** across README, `/orchestrate`, `/check-reporting`, and the make-figures guideline map — the enumeration and vendored checklist files were both 32; "33" was an off-by-one now backed by the count SSOT.
- **README restructured for faster onboarding** — a Quick Start (install + first command) above the demos, the three heavy demo output tables collapsed behind `<details>`, and "What's New" refreshed and moved below the demos (PR #50).
- Skill badge corrected from 40 to 42 (PR #50).

### Fixed

- **DOI badge now renders on GitHub** — the Zenodo-hosted badge SVG was served with `Cache-Control: no-cache`, which GitHub's Camo image proxy cannot cache, so it displayed as a broken image; replaced with a shields.io static DOI badge (Camo-cacheable). The DOI value and link are unchanged (PR #50).

### Hygiene

- Validator precedent blocklist no longer stores the maintainer's name, mentor names, institutions, or project codes in cleartext: `scripts/validate_skills.sh` delegates to `scripts/check_precedent.py`, which keeps generic structural shapes as regex but matches sensitive identifiers against SHA-256 digests (`scripts/precedent_hashes.txt`), with an `--allow-author` exemption for citation files (PR #44).
- Fixed `/present-paper` note-injection script path (`references/` → `scripts/`) (PR #43).

### Stats

- 42 skills (was 40); Zenodo concept DOI `10.5281/zenodo.20155321` preserved.

## [3.1.0] - 2026-05-23

### Added — v2.10 cycle integration

- `/peer-review`: Phase 2A SR-MA 8-probe extension (P1-P8) for systematic review meta-analyses (PR #22).
- `/verify-refs`: Gate 5 PMID/DOI duplicate detection; `submission_safe` / `fully_verified` synchronous propagation (PR #23).
- `/meta-analysis`: SR-MA dual-extractor workflow, cohort overlap detection, and supplementary 8-file pack (PR #24).

### Changed

- Validator scope extended to `templates/` and `scripts/` for permanent PII blocklist enforcement.
- `setup-medsci` skill now reflected in the public skill roster so filesystem, README, and external mirrors can align at 40 skills.
- `README.md` refreshed with v2.10 public-surface highlights and 40-skill badge/text sync.

### Hygiene

- Generalized legacy non-hyphenated MA project codes in `skills/meta-analysis/SKILL.md`.
- Added the non-hyphenated MA project-code family to the validator blocklist.

### Stats

- 40 skills (was 39); Zenodo concept DOI `10.5281/zenodo.20155321` preserved.

## [3.0.1] - 2026-05-13

### Added — first Zenodo-archived release with DOI

- First release archived on Zenodo. **Concept DOI**: [`10.5281/zenodo.20155321`](https://doi.org/10.5281/zenodo.20155321) (always-latest); **versioned DOI for this release**: [`10.5281/zenodo.20155322`](https://doi.org/10.5281/zenodo.20155322).
- README DOI badge populated; `CITATION.cff` `doi:` field + `identifiers:` block added.
- Bumps `version: 3.0.1` in `CITATION.cff`.

This release archives the v3.0.0 Tier 0 polish bundle (see entry below) so it becomes academically citable. No code changes vs v3.0.0 except the DOI back-fill commit.

## [3.0.0] - 2026-05-13

### Added — Tier 0 polish: CITATION.cff, Zenodo integration, setup onboarding, peer-review tone audit (2026-05-13)

- `CITATION.cff` (cff-version 1.2.0) and `.zenodo.json` for academic citation backlink. DOI populates after first Zenodo archive of a tagged release.
- `.github/workflows/release.yml` — on `v*` tag push, builds classroom ZIPs, creates GitHub Release with notes from CHANGELOG, attaches ZIPs. Zenodo integration (toggle once at `https://zenodo.org/account/settings/github/`) auto-archives the release.
- `docs/setup/` — five-doc onboarding guide for clinicians new to Python/R/Claude Code/MCP: `README.md` (decision tree), `mac.md` (Homebrew → pyenv → R → Node → Claude Code), `windows.md` (winget-based, no WSL), `mcp-setup.md` (Zotero / Google Drive / PubMed servers), `common-issues.md` (top 10 issues with copy-paste fixes).
- `skills/setup-medsci/` — diagnostic-only skill that runs `which python3 / Rscript / claude / node` and `claude mcp list`, prints a checklist with status (✅ / ⚠️ / ❌) and links to the right setup doc for any missing component. Intentionally read-only — does not install anything.
- README: added `## What This Is NOT` scope-out section (positions vs K-Dense scientific-agent-skills and OpenClaw Medical Skills) and `## Setup` section linking the new docs and `/setup-medsci`. Citation badge added.
- GitHub topics: swapped 4 generic (`ai-tools`, `academic-writing`, `open-source`, `research-tools`) for 4 specific (`agent-skills`, `tripod-ai`, `irb-protocol`, `physician-researcher`) — capped at GitHub's 20-topic limit.
- `skills/peer-review/` — Aczel 2021 anti-reviewer-2 tone patterns integrated into Phase 4 Self-QC and Tone Calibration sections (PR #11 merged 2026-05-13).

### Changed — `/publish-skill` Phase 2 `audit_skill.sh` rewritten for parity with monorepo linter (2026-05-03)

`skills/publish-skill/scripts/audit_skill.sh` was overhauled to mirror the per-skill rules in `scripts/validate_skills.sh`. Old behavior had three structural problems: (1) raster bytes inside compiled `.pyc` and PNG images falsely tripped path / email regexes (a known-clean skill reported 3 findings), (2) the institutional-reference category used `(?<!...)` lookbehinds that `grep -E` silently does not support — the entire category was inert, (3) several monorepo rules had no equivalent here, so a personal skill that passed `audit_skill.sh` could still fail when moved into the public repo.

New coverage matches the monorepo categories one-for-one:

- **rule 6 / 7 / 7b** — text-pass with `--binary-files=without-match` so PNG / DOCX / pyc byte collisions stop generating findings.
- **rule 7c** — author-style filename pattern (`<Surname>{Year}_*`) with the same generic-token allow-list as the monorepo (`Issue`, `Sample`, `Example`, etc.).
- **rule 8** — blockquote dated precedent (`> YYYY-MM-DD ...`) with allow-list for routine version stamps (`Last updated:`, `Created:`, `Updated:`, `Date:`, `Version:`, `Released:`).
- **rule 10** — binary EXIF metadata scan via `exiftool` (DOCX / PPTX / XLSX / PDF / PNG / JPG / TIFF). exiftool is a soft dependency; the script prints a one-line install hint and continues if missing, so users without the binary can still get the other nine categories.
- **email whitelist** — `example.com` / `example.org` / `example.net` / `your@email` / `noreply@` / `placeholder` / `<your-email>` / `<email>` placeholders no longer flag.
- **institutional regex** — `(?<!...)` lookbehinds replaced with `\b` word boundaries so the rule actually fires.
- **single-file EXIF mode fix** — exiftool only emits `======== <file>` headers when given two or more files; the parser now pre-primes `current_file` from `binary_files[0]` so a one-file EXIF audit attributes hits correctly.

`skills/publish-skill/SKILL.md` Phase 2 was rewritten to enumerate the ten audit categories, document the second positional argument (user-specific name / institution / collaborator alternation pattern), and explain the false-positive guard. The "Cross-validation" section was scoped down to the things the script does not yet automate (uncommon institutional acronyms, project-specific identifiers like `CK-NN` / `MA-NN`).

Regression sweep across all 39 monorepo skills: **30 clean, 9 with legitimate generalization flags** (language hardcoding to a specific natural language, location-specific examples, institution names in documentation prose). The flagged set is the cross-publication scope by design — the medsci-skills internal `validate_skills.sh` deliberately allows these because the monorepo is medical-domain-specific, while `audit_skill.sh` enforces the broader publish-time scope.

### Changed — 14 skill contracts migrated from schema_version 1 → 2 (2026-05-03)

All remaining v1 skill.yml contracts (`calc-sample-size`, `check-reporting`, `lit-sync`, `manage-refs`, `meta-analysis`, `orchestrate`, `peer-review`, `render-pdf-doc`, `revise`, `search-lit`, `self-review`, `sync-submission`, `verify-refs`, `write-paper`) gained `layer:` (A/B/C/D per `docs/skill_yml_schema_v2.md`), `when_to_use:` (3–5 trigger entries each), and `when_NOT_to_use:` (3–5 routing-guard entries each). Existing v1 fields preserved verbatim; the only schema-level change is the bump to `schema_version: 2`. Closes the 2026-07-24 v1 sunset deadline; `validate_skill_contracts.py` now reports `v1 contracts: 0  |  v2 contracts: 15`.

Layer assignments follow the schema doc (`/verify-refs` → A, `/write-paper` → C, `/orchestrate` → D, `/self-review` → D, `/revise` → B) and infer the rest from skill role: deterministic-script skills (calc-sample-size, check-reporting, lit-sync, manage-refs, render-pdf-doc, search-lit, sync-submission) on Layer A; structured-data skills (meta-analysis) on Layer B; free-form prose skills (peer-review) on Layer C.

## [2.4.0] - 2026-05-03

### Added — Binary EXIF metadata scan (validate_skills.sh rule 10)

`scripts/validate_skills.sh` now scans every shipped DOCX / PPTX / XLSX / PDF / PNG / JPG / TIFF for personal-name PII in document and image metadata. The text linter (rules 6 / 7 / 7b) cannot see fields like PDF `Author`, OOXML `dc:creator` / `cp:lastModifiedBy`, or EXIF `Artist`, so a personally-authored slide deck or annotated screenshot could ship with the author's real name in metadata while the file content read clean. Rule 10 closes that gap by piping the same `precedent_patterns` regex used for text scanning over an `exiftool -S` dump of `Author / Creator / LastModifiedBy / LastSavedBy / Copyright / Artist / Owner / OwnerName / CompanyName / Manager / HostComputer / UserComment / Subject / Title / Description / Keywords / Comment / Producer / CreatorTool / Software`. Upstream / 3rd-party document authors not in the precedent list (e.g., STARD's Patrick Bossuyt, the python-pptx maintainer) pass without an explicit allow-list. exiftool is now a hard dependency; the script exits early with an install hint if missing, and `.github/workflows/validate.yml` installs it via `apt-get` so server-side enforcement matches the local pre-commit hook.

Sanity-tested by injecting representative English- and Korean-script precedent identifiers from the blocklist into a tracked PNG's `Author` and `Artist` fields — both name forms are caught and FAIL on the next `validate_skills.sh` run, with cleanup automatically restoring the clean baseline.

### `/make-figures` v1.1.0 — design principles + flow diagram lessons (2026-05-03)

Adds a communication-first design layer to the figure pipeline and codifies five production lessons distilled from a multi-revision PRISMA Figure 1 cycle. The skill previously documented *which* figure type to use; v1.1.0 documents *what message to convey first* and *which template-fidelity / PDF-export pitfalls reliably waste a circulation round*. Skill contract bumped from schema_version 1 → 2 (sunset deadline 2026-07-24).

- **Added** — `skills/make-figures/references/design_principles.md` (~150 lines). Communication-first guide based on Brunner et al., *Nat Hum Behav* (2026) "Designing effective figures for scientific communication" (DOI: 10.1038/s41562-026-02466-9). Five strategies in reading order: (1) identify the one-sentence key message, (2) match the reading-time budget to the deployment context, (3) match graph type to data structure with intentional color use, (4) keep ≤7 visual elements / ≤3 colors per panel, (5) ask whether a figure is genuinely needed. Includes a figure-vs-table decision table, an audience-context matrix (specialist / generalist / mixed), a cognitive-load Step-4 checklist, and an anti-pattern list (default-palette syndrome, legend-dependence, decorative 3-D, chart-of-three-values, caption-as-Methods, mismatched detail).

- **Added** — `skills/make-figures/references/flow_diagram_lessons.md` (~150 lines). Five generalized lessons from a meta-analysis Figure 1 cycle (PII-scrubbed): (1) custom Graphviz prototypes are fine but switch to the official template before circulation, (2) headless LibreOffice corrupts PRISMA 2020 docx → PDF because of VML fallback drift; use macOS AppleScript / Windows COM driving native Word, (3) raw `str.replace` on `word/document.xml` breaks on `&`, `<`, `>` — always entity-escape via `xml.sax.saxutils.escape()` before substitution, (4) the PRISMA 2020 docx duplicates each numeric box as `<w:t>` pairs in non-rendering order; build a sequential placeholder map and validate with a `999`-sentinel render, (5) freeze figures alongside the manuscript v_N — never edit `figures/v3/*.pdf` after circulation, branch to `v4/` instead. Closes with a 4-row stage-vs-tool table that maps draft / QC / circulation / submission to the right approach.

- **Added** — `skills/make-figures/references/reporting_guideline_figure_map.md` (~140 lines). Bridges this skill to `/check-reporting` (33 reporting guidelines) by mapping 17 study designs and AI-extension guidelines to their mandatory figures and current support status: ✅ official template + R generator (PRISMA 2020, CONSORT 2025, STARD 2015, SPIRIT 2025, TRIPOD calibration), ⚠️ generic flow generator only (PRISMA-DTA, STROBE, CARE), ❌ no template — manual production via D2/Graphviz (CONSORT-AI 2020 PMID 32908283, STARD-AI 2025 PMID 40954311, TRIPOD+AI 2024 PMID 38636956, CLAIM 2024 PMID 38809149, DECIDE-AI 2022 PMID 35585198, PRISMA-NMA, PRISMA-P, CHEERS 2022, SQUIRE 2.0). Includes a "AI-specific figures most often missing" priority list (dataset-flow, calibration, fairness/subgroup panel, decision-curve analysis, architecture, saliency overlay) ranked by reviewer-checklist frequency.

- **Added** — `skills/make-figures/references/pipeline_concepts_medical_ai.md` (~200 lines). Four canonical diagram types not covered by reporting-guideline flows: (1) DICOM workflow (scanner → PACS → de-id → research store → splits), (2) annotation pipeline (annotator pool, consensus rule, inter-rater agreement), (3) federated learning topology (per-site cohorts, what flows between sites, aggregation algorithm), (4) model architecture (input shape, backbone, head, parameter count, trainable layers). Each section gives canonical layout, required annotations, common pitfalls, and preferred tool (D2 / drawio / NN-SVG / PlotNeuralNet). Closes with a 6-row "use this section if your figure shows…" selector.

- **Added** — `skills/make-figures/references/design_principles.md` companion citations: Rougier et al., *PLoS Comput Biol* 2014 (PMID 25210732) "Ten simple rules for better figures" — foundational general-purpose checklist; Crameri F., *Curr Protoc* 2024 (DOI 10.1002/cpz1.1126) "Choosing the right colors" — definitive 2024 reference for perceptually-uniform colorblind-safe palettes (`viridis` / `cividis` / `batlow`) and redundant encoding. Updated the Color section to recommend `vik` for diverging diagnostic data and to make redundant encoding explicit when color carries diagnostic meaning.

- **Changed** — `skills/make-figures/references/critic_rubrics/flow_diagram.md`. Appended Section G "Communication-first checks" with five new rubric items (22–26): cognitive load (≤7 boxes per column, ≤3 shapes, ≤3 colors), key-message visibility (analytic cohort visually emphasized within 2 seconds), official-template fidelity (PRISMA 2020 / CONSORT 2010 / STARD 2015 / STROBE), exclusion-box geometry (rectangles with `\l` left-aligned bullets, not `shape: note`), and frozen-version sync with the manuscript v_N path.

- **Changed** — `skills/make-figures/references/critic_rubrics/data_plot.md`. Appended Section G "Medical AI / prediction-model checks" with five new rubric items (21–25): calibration plot accompanies discrimination (TRIPOD+AI), subgroup/fairness panel for deployment claims (CLAIM 2024 §C, TRIPOD+AI), colorblind-safe + redundant encoding stronger than the existing D.13 (Crameri 2024), dataset-flow visible (STARD-AI / CLAIM 2024 / TRIPOD+AI), decision-curve analysis when the paper claims clinical utility (Vickers & Elkin, *Med Decis Making* 2006).

- **Changed** — `skills/make-figures/SKILL.md` Step 1 "Specify" now opens with a three-tier reading directive: (1) `design_principles.md` for every figure (key message + reading-time budget), (2) `reporting_guideline_figure_map.md` for any figure mandated by a reporting guideline, (3) `pipeline_concepts_medical_ai.md` for DICOM / annotation / federated / architecture diagrams. Step 4b "Critic Loop" Stage 2 now loads (a) `flow_diagram_lessons.md` for PRISMA / CONSORT / STARD / STROBE flows, (b) `reporting_guideline_figure_map.md` for AI-extension guidelines (CONSORT-AI / STARD-AI / TRIPOD+AI / CLAIM 2024 / DECIDE-AI) so the worker knows which figures the target guideline mandates, and (c) `pipeline_concepts_medical_ai.md` for AI/engineering pipeline figures.

- **Changed** — `skills/make-figures/SKILL.md` Journal AI-Image Policies section now declares an explicit sync pointer to `~/.claude/rules/journal-ai-image-policies.md` (the user's authoritative global rule), preventing the local copy from drifting silently when the policy table is updated upstream.

- **Changed** — `skills/make-figures/SKILL.md` triggers expanded with `key message`, `figure design`, `figure planning`, `effective figure`, and `cognitive load` so design-first prompts route here.

- **Changed** — `skills/make-figures/skill.yml` migrated to schema_version 2: added `layer: B`, `when_to_use` (5 entries covering /write-paper Phase 5 trigger, post-/analyze-stats visualization, PRISMA/CONSORT/STARD/STROBE flows, journal-specific abstracts), `when_NOT_to_use` (4 entries — tabular results → /analyze-stats, decorative slides → /present-paper, logos out of scope, AI images for prohibited targets), and `version: 1.1.0`. Existing `inputs / outputs / deterministic_scripts / side_effects / downstream_consumers / forbidden_actions` retained; `forbidden_actions` gained `generate_AI_images_for_prohibited_targets` to make the JACC / NEJM policy machine-checkable.

- **Added** — `skills/make-figures/scripts/validate_pptx_mac_compat.py` (~210 lines, deterministic). Codifies the four PowerPoint-Mac-only defect classes from `~/.claude/rules/pptx-mac-compatibility.md`: (1) TIFF images embedded in `ppt/media/` (Mac silently drops), (2) `<a:sp3d>` 3-D bevels (renders as red outlines invisible in PDF export), (3) `docProps/app.xml` slide-count mismatch with actual slide XML files (triggers PowerPoint recovery dialog), (4) `<a:srcRect>` values >100000 (1/1000-percent overflow → 99 % over-crop on Mac only). Pure-stdlib (zipfile + regex), no python-pptx dependency. Returns JSON report + human-readable summary; `--strict` exits 1 on any FAIL. Wired into SKILL.md Step 5 Export for any visual-abstract / central-illustration PPTX.

#### Cross-skill harmonization (2026-05-03)

- **Changed** — `skills/check-reporting/SKILL.md` Step 4d (PRISMA Figure 1 audit) now performs a `_figure_manifest.md` cross-check as step 3 of its procedure: verifies the manifest row whose Type matches the audit target points at the same source path and that the row's `Critic` field is not `no`. A missing row, mismatched path, or `Critic = no` logs `[MANIFEST-XREF]` (advisory). Skips silently if `_figure_manifest.md` does not exist (older projects). Closes the prior gap where a figure could pass the arithmetic audit while a parallel `_figure_manifest.md` recorded `critic_pass: no`.

- **Changed** — `skills/write-paper/SKILL.md` Phase 2 step 9 ("Manifest verification") promoted from advisory to **HALT gate** in autonomous mode. Previous behavior was log-and-continue, which silently dropped all figures from the Phase 7 DOCX build (manifest is the figure-embedding source at line 567). New behavior in `--autonomous`: HALT with `MANIFEST_MISSING` error code, log to `qc/_pipeline_log.md`, and write recovery instructions to `manuscript/<id>/REPORT.md` Tier-3 section. Interactive mode unchanged.

- **Changed** — `skills/present-paper/SKILL.md` slide-type templates section now declares the figure source-format contract for `T_image_right`: PNG ≥300 dpi preferred for slides, PDF only when projection >1080p (convert via `pdftoppm -r 300` first because python-pptx PDF embedding is unreliable across PowerPoint versions); TIFF / JPEG-for-line-art / raw-SVG forbidden. Caption contract: re-draft for spoken-narration context (5–10 s of attention) rather than copying journal legends verbatim.

#### Follow-up (deferred, not in this PR)

- 14 remaining skill.yml files still on schema_version 1 (deadline 2026-07-24).
- `scripts/generate_flow_diagram.R` itself unchanged — the new lessons live in references/ text only; codifying the lessons into the R generator (e.g., `--official-template` flag, `--sentinel` mode) is a separate PR.

### `/orchestrate --e2e` v4 integration — pre-flight + REPORT + Tier-3 guard (2026-05-01)

Folds the delegated-mode plan v4 into `skills/orchestrate/` so `/orchestrate --e2e` becomes a "single-researcher" mode: one delegation, no per-phase confirmations except the PHI gate, and a single REPORT.md the user reviews at the end. Replaces the earlier scheme that put the report template and the usage rule under `~/.claude/templates/` + `~/.claude/rules/` (both deleted) — the repo is now the only source of truth.

- **Added** — `skills/orchestrate/references/report_template.md`. Canonical 11-section REPORT layout written to `manuscript/<id>/REPORT.md` at every `--e2e` termination (success or halt). Sections: 한 줄 요약, Frozen / Version status, Source artifacts checked, 변경 파일, Changed claims, 검토 포인트, 환각 게이트 결과, QC artifact links, Human-only missing fields, Tier-3 차단 항목, 다음 액션 + Next safe command + Pipeline log. The Tier-3 section is split into hook-confirmed (`tier3-confirm.sh`) vs prompt/skill-guard-only blocks so a future hook regression cannot silently re-open a prompt-only block.

- **Changed** — `skills/orchestrate/SKILL.md` `### --e2e Flag` now opens with a Pre-flight Validation block (4 checks): STATUS / project_state, frozen artifact (v_N `_FROZEN` marker → v_(N+1) branch only), required inputs, dependency miss. Default on dependency miss is halt; `--auto-extend` is the only opt-in that prepends missing phases. PHI Safety Gate remains the only legitimate interrupt after pre-flight passes.

- **Added** — `skills/orchestrate/SKILL.md` `### REPORT.md Generation` section after Post-Skill Validation. Worker MUST write `manuscript/<id>/REPORT.md` from the new template at every `--e2e` termination. Empty fields render as `(none)` / `(unknown)` — never omitted. The §"Pipeline log" entry is a 5-line summary, not the full log.

- **Added** — `skills/orchestrate/SKILL.md` `### Tier-3 Worker Guard` section. Permanently forbids `--e2e` auto-entry into `git push`, `gh pr create`, MCP Gmail/Calendar send, MCP GitHub create-pr, `/sync-submission build` external publication paths, Phase 8 submission DOCX auto-build, and senior-mentor automatic email reply. `git commit` is allowed; subsequent `git push` halts. Reinforces the existing `### Post-E2E` boundary (Phase 8 already required explicit user invocation).

- **Changed** — `skills/orchestrate/SKILL.md` `check-reporting` row in the Available Skills table now reads "33 reporting guidelines and risk-of-bias tools" to match README and the skill's own SKILL.md (was stale at 22).

#### Follow-up (deferred, not in this PR)

- Release ZIP refresh — `dist/medsci-skills-classroom-*.zip` is stale at v2.1.1 / 37 skills (current 39, including `/manage-refs`, `/render-pdf-doc`, and the e2e+REPORT contract).
- skill.yml v1 → v2 contract migration — 15 skill.yml files still v1; v2 schema not yet adopted across the bundle.
- Mock test for frozen-artifact halt under `--e2e` (Plan v4 Verification §3) — current PR ships docs/contract only.

### Integration cleanup — orchestrator hardening + `/render-pdf-doc` adoption (2026-05-01)

End-to-end integration sweep after the parallel-session conflict around the manage-refs split. Three sessions had been editing the repo simultaneously (`/render-pdf-doc` spinoff, `/write-paper` backbone Phase 0, manage-refs split + circulation memo). This cleanup folds the surviving artifacts together, fixes the runtime breakage left in `/write-paper` Phase 7.6, registers the four previously-unrouted skills with `/orchestrate`, and standardizes per-skill `## Gates` sections.

- **Fixed (P0 blocker)** — `skills/write-paper/SKILL.md` Phase 7.6 hardcoded `${CLAUDE_SKILL_DIR}/scripts/check_citation_keys.py` / `render_manuscript.sh` / `check_xref.py`, all of which moved to `/manage-refs` in the previous release. The hardcoded paths produced a runtime "file not found" the moment the autonomous pipeline tried to render a DOCX. Replaced all three with `${MEDSCI_SKILLS_ROOT:-$HOME/workspace/medsci-skills}/skills/manage-refs/scripts/...` and added a one-line delegation note pointing users at `/manage-refs` directly. The Phase summary table at line 861 was updated to label step 7.6 / 7.6a as `/manage-refs` calls.

- **Added** — `skills/render-pdf-doc/` (147-line SKILL.md + scripts/{render_pdf.sh, infer_colwidths.py, check_deps.sh} + 4 templates + 2 references). Skill renders non-bibliography academic markdown (proposal, briefing, anchor doc, IRB cover, reference table) to PDF via pandoc + xelatex with CJK font fallback (Apple SD Gothic Neo / Noto Sans CJK KR) and content-proportional pipe-table column widths. Boundary opposite of `/manage-refs scripts/render_pandoc.sh` (bibliography-driven). Origin: a calibration-anchor PDF that needed manual column-width fixes twice in succession.

- **Added** — `skills/render-pdf-doc/skill.yml` v1 contract (inputs / outputs / forbidden_actions / quality_gates). `bibliography_rendering`, `institutional_word_form_filling`, `figure_or_pptx_generation` are explicitly forbidden so the skill cannot drift into adjacent domains.

- **Changed** — `skills/orchestrate/SKILL.md` Available Skills table now includes `verify-refs`, `manage-refs`, `lit-sync`, `humanize`, `academic-aio`, `render-pdf-doc`, `fill-protocol`, `fill-icmje-coi`, `sync-submission`, `peer-review` (all previously referenced in workflows but not registered). Classification Logic gained 9 new routing rows (manage-refs, lit-sync, render-pdf-doc, fill-protocol, fill-icmje-coi, academic-aio, humanize, peer-review). Multi-skill Workflows table gained 6 new chains (Submission rendering & cascade reformat, Cascade rejection re-target, Non-bibliography academic deliverable, Reference housekeeping cycle, ICMJE COI batch, plus `/manage-refs` insertion into the existing "Draft exists, prepare for submission" chain). Standard Pipeline now lists `/manage-refs` as step 7 (DOCX build + xref QC `--strict` submission gate). Data Flow Contract table gained rows for lit-sync, manage-refs, render-pdf-doc, fill-protocol, fill-icmje-coi, sync-submission, peer-review.

- **Added** — `skills/orchestrate/references/dialogue_nodes.md` two new fork nodes: **N10** Reference Workflow (manage-refs Workflow A pandoc vs B Zotero CWYW vs hybrid 3-phase) and **N11** Protocol Delivery Format (`/fill-protocol` vs `/render-pdf-doc`). Defaults align with `~/.claude/rules/manuscript-references.md` (hybrid) and `~/.claude/rules/institutional-form-fill.md` (institutional template first).

- **Changed** — SSOT writer boundaries declared in `skill.yml`:
  - `skills/search-lit/skill.yml` — `references/library.bib` is search-candidate pool only; sole writer of `manuscript/_src/refs.bib` is `/lit-sync`. New forbidden_action: `write_to_manuscript_refs_bib`.
  - `skills/lit-sync/skill.yml` — declared sole writer of `manuscript/_src/refs.bib` (via Better BibTeX auto-export). New downstream consumer: `manage-refs`. New quality_gates: `refs_bib_refreshed`, `bbt_auto_export_active`. New forbidden_action: `hand_edit_manuscript_refs_bib`.
  - `skills/calc-sample-size/skill.yml` (new) — declares `protocol/sample_size_justification.md` + `sample_size_calc.{R,py}` as canonical outputs; `/write-protocol` and `/write-paper` embed verbatim, never rephrase numbers.

- **Changed** — `skills/write-protocol/SKILL.md` input contract for calc-sample-size now references `protocol/sample_size_justification.md` (canonical artifact path) and mandates verbatim embedding per `~/.claude/rules/numerical-safety.md`.

- **Changed** — `skills/manage-refs/SKILL.md` Anti-Hallucination Guarantees expanded with `[@NEW:topic]` placeholder convention. `check_citation_keys.py` classifies these as `NEW_PLACEHOLDER` (not UNDEFINED) so drafting can proceed; Phase 7.6 (DOCX render) is a hard gate where zero NEW_PLACEHOLDER entries must remain.

- **Added** — Per-skill `## Gates` sections classifying every gate as ENFORCED / ADVISORY / OPT-IN. Updated: `/write-paper` (13-row Phase 0–8+ table + cross-cutting rule list), `/self-review` (5 gates), `/check-reporting` (4 gates), `/humanize` (6 gates including Pattern 19–21 ENFORCED), `/revise` (6 gates including [VERIFY-CSV] tagging + post-revision `/verify-refs --strict`).

- **Added** — `docs/rule-application-map.md` — single-page matrix mapping every global rule (`~/.claude/rules/`) to the skill / phase that triggers it, with severity. Index only; rule bodies remain in the user's `.claude/rules/` directory.

- **Moved** — internal planning note for the `render-pdf-doc` skill from project-root scratchpad into the per-session planning area (now gitignored).

### Added — `/manage-refs` skill split (2026-05-01)

The reference-handling lifecycle (citekey validation, journal-CSL pandoc rendering, manuscript ↔ DOCX cross-reference QC, marker conversion, native Zotero CWYW field-code injection) was extracted from `/write-paper` Phase 7.6 into a new cross-cutting `/manage-refs` skill so it can be invoked uniformly from `/revise`, `/peer-review`, `/sync-submission`, and `/find-journal` (cascade rejection re-render). Validated against a 21-reference systematic-review manuscript, both pandoc-citeproc and Zotero-CWYW paths.

- **New skill** `skills/manage-refs/`:
  - `SKILL.md` (216 lines, MID tier) — decision tree, Workflows A–D (pandoc citeproc / Zotero CWYW / cascade rejection / cross-reference QC), Anti-Hallucination Guarantees (6 items), Quality Gates (3 submission gates + 1 user approval gate).
  - `skill.yml` — v1 contract with full `inputs / outputs / deterministic_scripts / side_effects / downstream_consumers / forbidden_actions` declaration plus provenance entry for the vendored Zotero CWYW writer.
  - `citation_styles/` — 9 journal CSL files relocated from `write-paper/references/citation_styles/` (european-radiology, radiology, AJR, CVIR, KJR, vancouver, vancouver-superscript, springer-basic-brackets, springer-vancouver-brackets).
  - `scripts/check_citation_keys.py`, `scripts/check_xref.py`, `scripts/render_pandoc.sh` — relocated from `write-paper/scripts/` (`render_manuscript.sh` renamed to `render_pandoc.sh`).
  - `scripts/md_marker_convert.py` (new) — generalized `[N]` ↔ `[@key]` converter, mapping-driven, supports `.md` and `.docx`, partial-conversion safe with `--active-ns`. Extracted and generalized from a per-project temporary `build_zotero_docx.py` replacer.
  - `scripts/inject_zotero_cwyw.py` (new) — wraps the vendored `citation_writer.insert_citations` and patches `zotero_to_csl_json` to fetch native CSL-JSON via Zotero's connector API (handles webpage / report / non-journal item types correctly, where the upstream `_ITEM_TYPE_MAP` falls back to `"article"` and silently drops fields).
  - `scripts/_vendor_citation_writer.py` (vendored) — from `alisoroushmd/zotero-mcp` @ `ed5dfb71`, MIT license. See `NOTICE.md` and `LICENSE.zotero-mcp`.
  - `references/check_xref_symptoms.md` — `MISSING_DOCX` / `MISSING_BODY` / `MISMATCH` / `UNCITED` triage table.

- **Dependents updated** to point at the new location:
  - `skills/write-paper/SKILL.md` Phase 7.6 — old in-skill scripts replaced with `/manage-refs` invocations + visible deprecation note. Old paths `${CLAUDE_SKILL_DIR}/scripts/{check_citation_keys.py, check_xref.py, render_manuscript.sh}` and `${CLAUDE_SKILL_DIR}/references/citation_styles/` are retired in this release.
  - `skills/verify-refs/SKILL.md` — companion citation-key check now references `/manage-refs/scripts/check_citation_keys.py`.
  - `skills/self-review/SKILL.md` Phase 2.5b — cross-reference QC invocation now references `/manage-refs/scripts/check_xref.py`.

- **Global rules** updated to single-source the new entry point:
  - `~/.claude/rules/agent-skill-routing.md` — added `/manage-refs` rows for lifecycle, CSL render, citekey check, cross-reference QC, and CWYW injection; `/verify-refs` clarified as audit-only.
  - `~/.claude/rules/manuscript-references.md` — pandoc pipeline section repointed at `manage-refs/scripts/render_pandoc.sh`, with `check_xref.py` step added inline.

### Added — Senior MA reviewer harvest

Lessons from senior meta-analysis mentor circulation feedback promoted into global rules and skill checklists, so subsequent manuscript circulations in the same pipeline do not repeat the same comments.

- **Global rules (5 files)** under `~/.claude/rules/`:
  - `manuscript-style-classical.md` (new) — 11-item style policy: `## **METHODS**` heading, abstract sub-headers `**Objectives:**`, eligibility numbered list, no `§` symbol, no AI Disclosure paragraph in body, em-dash <25, Vancouver 6+ et al., ORCID one-per-line, table header punctuation, British/American per journal.
  - `senior-mentor-circulation.md` (new) — mandatory `8_Review_Comments/` folder layout, 1차 source preservation, 1:1 verification, mentor README (per-mentor preference accumulation).
  - `ai-drafted-document-policy.md` (new) — verbatim absorption forbidden when senior mentors attach AI-drafted documents; `_DO_NOT_USE_VERBATIM` filename suffix mandatory; trust hierarchy SSOT > mentor direct text > AI-draft. Motivation: 2026-04-12 Ishikawa 2017 denominator hallucination (5/70 vs 12/33 → real 35/68).
  - `data-integrity.md` — one-line augmentation cross-linking the AI-drafted policy.
  - `agent-skill-routing.md` — new "Cross-cutting 룰 (Manuscript / 회람)" table referencing the six rule files.

- **`/write-paper` Step 7.1 — Classical-style QC sub-step**:
  - `skills/write-paper/references/section_guides/step7_1_classical_qc.md` (new) — load-on-demand 7-grep checklist (`§` symbol, AI Disclosure paragraph, heading style, eligibility numbered list, Funding placeholder, PROSPERO chronology, em-dash overuse).
  - `skills/write-paper/SKILL.md` Step 7.1 — trigger table + load-on-demand pointer added.

- **`/humanize` Pattern 19–21**:
  - `skills/humanize/references/ai_patterns.md` — Pattern 19 (`§` section sign), Pattern 20 (Methods/Results self-reference parenthetical), Pattern 21 (AI Disclosure boilerplate in body) added with detection regex + rewrite guidance.
  - `skills/humanize/SKILL.md` — 18 → 21 patterns; section-specific focus extended to MA / SR Methods and Discussion.

- **`/meta-analysis` Phase 4.0 — AI-drafted starting document gate**:
  - `skills/meta-analysis/SKILL.md` — new sub-step at the top of Phase 4 (Data Extraction) requiring `_DO_NOT_USE_VERBATIM` filename suffix and source-PDF re-verification of every per-study N, denominator, event count, and effect estimate carried over from a senior mentor's AI-drafted directive. Trust hierarchy: SSOT > mentor direct text > AI-draft (never promote tier 3 to tier 2).
  - Cross-links `~/.claude/rules/ai-drafted-document-policy.md` (motivation: 2026-04-12 Ishikawa 2017 denominator hallucination caught at SSOT re-verification).

- **`/check-reporting prisma` Step 4d — PRISMA Figure 1 arithmetic & cross-reference audit**:
  - `skills/check-reporting/scripts/check_prisma_figure.py` (new) — extracts PRISMA numbers from manuscript body and Figure 1 source, runs 4 arithmetic equations (`screened = identified - duplicates`, etc.) and a body↔figure 1:1 cross-reference, emits `qc/prisma_figure_audit.json` + table. Exits 1 on any MISMATCH.
  - `skills/check-reporting/SKILL.md` Step 4d — invocation block + flagging policy (`[PRISMA-FIGURE]`, `fixable_by_ai: false`).
  - `skills/check-reporting/references/step4d_prisma_figure_audit.md` (new) — regex set, JSON schema, edge cases (multi-database, citation-searching strand, dual-reviewer screening, reports-vs-records terminology).

Resolves the meta-analysis project → medsci-skills handoff P1+P2.

### Added — Manuscript ↔ rendered DOCX cross-reference QC (`/write-paper` Step 7.6a + `/self-review` Phase 2.5d)

New 3-way audit catches the failure mode where in-text Table/Figure citations resolve to a different rendered caption because the build script carries its own legacy SSOT. Internal consistency (Phase 2.5) cannot detect it — both the prose and the build artifact echo their own divergent truths cleanly.

**Precedent:** in a STROBE cohort manuscript, the body cited "Supp Table S4 (sensitivity analysis)" but the rendered DOCX S4 was a different table; S1, S6, S7 mismatched and S8, S9 were cited but absent from the DOCX entirely. Caught only on co-author circulation review.

- `skills/write-paper/scripts/check_xref.py` — extracts (a) `(Supplementary )?(Table|Figure)\s+(S?\d+[A-Z]?)` in-text citations, (b) caption definitions from `## Tables` / `## Figures` / `## Supplementary {Tables,Figures}` body sections, (c) rendered DOCX caption paragraphs via python-docx. Emits `qc/xref_audit.json` with status codes `OK | MISSING_DOCX | MISSING_BODY | MISMATCH | UNCITED | NOT_CITED_NO_BODY`. Caption agreement via Jaccard ≥0.40. Panel-letter fallback (`Figure 2A` cite resolves to `Figure 2` caption). `--strict` exits 1 on any P0 finding.
- `/write-paper` Step 7.6a (new) — runs after Step 7.6 DOCX build, before Step 7.7 final gate. Submission gate; HALT pipeline on non-OK. Routing table for fixes by symptom (body update vs build-script update) — body caption is the SSOT, never the reverse.
- `/self-review` Phase 2.5d (new) — reuses the same script when a rendered DOCX exists. Translates findings to P0 Major Comments (category F, `fixable_by_ai: false`). Auto-fix forbidden in `--fix` mode (caption rewrites without rebuilding DOCX would only move the mismatch).

Resolves an internal improvement queue item (cross-reference QC, HIGH priority).

### Added — `/make-figures` flow diagram pipeline (R + DiagrammeR + rsvg)

New standardized flow-diagram generation for STROBE / CONSORT / PRISMA / STARD in a single R script, replacing the former D2 + matplotlib mix that caused repeated overlap, font, and DOCX-embed issues.

- `skills/make-figures/scripts/generate_flow_diagram.R` — CLI dispatcher: `--type {strobe|consort|prisma|stard} --config <yaml> --out <prefix>`. Reads a YAML node/edge spec, emits true vector PDF + 300 dpi PNG + 600 dpi PNG. Monochrome black outline on white fill, Arial, auto-overlap via Graphviz `dot` engine.
- `skills/make-figures/references/exemplar_diagrams/{strobe,consort,prisma,stard}/` — each directory now contains `template_input.yaml` + rendered `template_output.{pdf,png,_600.png}` so users can fork a concrete example.
- `skills/make-figures/references/exemplar_diagrams/strobe/` — new directory (previously missing alongside consort/prisma/stard).
- `skills/make-figures/references/exemplar_diagrams/README.md` — layout description extended to cover both "review anchors" (existing curator-curated PDFs) and "generation templates" (new).
- `skills/make-figures/SKILL.md` — "Flow diagram generation rule" rewritten to mandate the R pipeline as the single canonical tool. D2 recipe demoted to a legacy-fallback block. Tool Selection Guide table updated to route all four reporting-guideline flow diagrams through `generate_flow_diagram.R`.
- `skills/make-figures/references/figure_specs.md` — new "Flow Diagram Tool Selection" section documenting the stack choice, PRISMA 2020 compliance note, and rejection rationale for matplotlib / D2 / `consort` / `PRISMA2020` / Mermaid.

**System dependency:** `brew install librsvg` (macOS) or `apt-get install librsvg2-bin` (Linux). R packages: `DiagrammeR`, `DiagrammeRsvg`, `rsvg`, `yaml`.

**Validated end-to-end:** a STROBE cohort Figure 1 rebuilt with the new pipeline — single-color outline, no overlap, Arial rendered correctly for en-dash / bullet / `≤` / minus sign. Counts derived from a tracked cohort CSV. Legacy `create_figure1.py` and `figure1_flow.d2` preserved with `_legacy` suffix.

**Rollout:** retrofitted across multiple manuscripts spanning STROBE, STARD, PRISMA, PRISMA-DTA, and CONSORT-edu reporting guidelines.

- SKILL.md Flow-diagram section now documents the **per-project `create_figure1.R` pattern** (sprintf'd `dot` string + `stopifnot()` count reconciliation + multi-rank `{rank=same}` blocks) as the preferred route when the generic YAML dispatcher cannot express complex layouts.
- SKILL.md style rules hardened: **no HTML-like labels** (`label=<...>` with `<B>`/`<I>`/`&#8226;`) — plain quoted labels with `\l` bullets produce tighter, more readable structure than HTML ragged wrapping.

### Added — New skill `/academic-aio` + pipeline integration across README, write-paper, orchestrate

Medical AI paper optimization for AI search engines (Perplexity, ChatGPT web, Elicit,
Consensus, SciSpace) and RAG-based literature tools. Integrates TRIPOD+AI, CLAIM,
STARD-AI, TRIPOD-LLM, and DECIDE-AI reporting anchors with generative-engine-optimization
(GEO) principles from Aggarwal 2024 (arXiv:2311.09735). Scope covers title, abstract,
structured summary boxes (Key Points / Research in Context / Plain-Language Summary),
preprints, GitHub README, `CITATION.cff`, Zenodo, and Hugging Face model / dataset
cards. Explicit defense against LLM citation fabrication (Agarwal 2025, Nat Commun
doi:10.1038/s41467-025-58551-6, which reports up to 78–90% fabricated citations in
medical LLM answers). Produces a visible PASS/PARTIAL/FAIL checklist; never applies
edits silently (Communication Rules).

**Pipeline integration** (added in this release, not in the new skill itself):
- `README.md`: skill-table row added + main pipeline diagram branches
  `humanize → academic-aio` off the self-review / find-journal spine.
- `write-paper/SKILL.md` Skill Interactions table: new rows 7.5 (`/humanize`) and
  7.5a (`/academic-aio` opt-in `--aio`), running after `/self-review` Phase 7.4
  and before DOCX build (Phase 7.6).
- `orchestrate/SKILL.md`: (a) new multi-skill-workflow row "Medical-AI paper,
  AI-search visibility pass" with N4 + N9 nodes; (b) existing "Draft exists,
  prepare for submission" chain extended to `humanize → academic-aio (--aio)`;
  (c) new `--e2e` clause #8 specifying AIO is OFF by default in autonomous
  mode (AI-search visibility is a pre-submission, not a pre-draft, concern and
  autonomous silent rewrites would violate AIO's "never edit silently"
  contract) — opt-in via `--aio`, report always surfaced to user.
- Internal pipeline planning notes record the AIO-position rationale for 7.5a
  placement (after `check-reporting` so the Section 1.6 guideline anchor reflects
  real compliance; after `humanize` so the human-readability pass does not erase
  AIO edits; before DOCX build so the optimizations reach the final artifact)
  and the Anti-Hallucination division of labour with `search-lit` /
  `check-reporting` / `write-paper` / `humanize`.

**Anti-Hallucination block added to `/academic-aio` SKILL.md**: bars fabricated
citations / DOIs / arXiv IDs / reporting-guideline item numbers; bars invented
journal-specific summary-box rules (Lancet Digital Health "Research in context",
Radiology "Key Points", npj Digital Medicine); bars fabricated AI-search
discoverability metrics (Perplexity / Elicit / Consensus retrieval scores may
only be reported from recorded probes); bars auto-completion of CITATION.cff
and Zenodo author lists, ORCIDs, and affiliations. This closes the last
validator FAIL from the v2 content-integrity lint rollout.

**Skill count**: 32 → 33. Validator reports 265 PASS / 32 WARN / 0 FAIL after
these changes.

### Changed — Reference split for `/meta-analysis` Phase 4 & Phase 6 (R templates + KM/composite)

`/meta-analysis` SKILL.md had two oversized phases after the earlier Phase 9/10 split:
Phase 6 (Statistical Synthesis) ran 119 lines with full R code for DTA bivariate models,
intervention `metagen`/`metabin`, the dual-approach comparative + single-arm pooled
proportion decision table, practical R notes (method.tau, HK CI, zero-cell correction),
publication-bias test power, and sensitivity-analysis menu; Phase 4 (Data Extraction)
contained two specialised sub-procedures — KM curve reconstruction via WebPlotDigitizer
+ `IPDfromKM` (Guyot 2012) and composite-exposure disaggregation — that together ran
~40 lines. Both were moved to `references/phase6_statistical_synthesis.md` (148 lines)
and `references/phase4_km_composite.md` (58 lines), with SKILL.md bodies retaining a
one-table summary + load-on-demand pointer. Net impact: `/meta-analysis` 594 → 459
lines (−135, cumulative −281 from 740 pre-recovery-loop inlined state).

### Changed — Korean→English prose translation for `/ma-scout`, `/lit-sync`, `/grant-builder`, `/deidentify`

Four skills carried substantial Korean prose body text that tripped rule 9 of the v2
content-integrity lint (Korean outside code/tables/Communication Rules/frontmatter).
Translations preserve Korean domain terms in parenthetical references where they are
literal references to the Korean research system (Korean government agency names in
`/grant-builder`: 복지부=MOHW, 산자부=MOTIE, 중기부=MSS; Korean attachment names:
첨부1-3; Korean vault folder paths in `/lit-sync`: `02 연구/문헌/`, `02 연구/개념노트/`;
Obsidian note template headings in `/lit-sync` that must match the user's existing vault
convention: `## 서지 정보`, `## 핵심 내용`, `## 내 생각`, `## 관련 노트`). `/ma-scout`
also extracted the 72-line bilingual PROSPERO-ready README template block to
`references/project_readme_template.md` (includes Solo-Mode Adaptations for topic-first
mode without supervisor) and replaced the inlined block with a load-on-demand pointer.
Net impact: all four skills now pass lint rule 9 for SKILL.md body text; remaining
Korean is confined to frontmatter triggers (permitted), literal template content, and
Obsidian vault paths (the 32 outstanding WARNs are legitimate Korean-in-parenthesis
references that are not targeted by the rule).

### Changed — Reference split for `/meta-analysis` Phase 9/10, `/check-reporting` Step 4c, `/write-paper` Step 7.4a

The recently added recovery-loop phases were fully inlined in `SKILL.md` bodies,
inflating three skill files beyond what load-on-demand expects. Procedural detail was
extracted to new reference files (`meta-analysis/references/phase9_circulation.md`,
`phase10_recovery.md`, `check-reporting/references/step4c_registration_timing.md`,
`write-paper/references/section_guides/step7_4a_audit_recovery.md`) with SKILL.md bodies
retaining only the trigger table, routing table, and summary paragraph plus a
`Load-on-demand procedural detail` pointer. Net impact: `/meta-analysis` 740 → 594
lines (−146), `/check-reporting` 425 → 376 (−49), `/write-paper` 853 → 829 (−24). Pattern
follows the existing `checklists/QUADAS2.md` load-on-demand convention. All nine
content-integrity lints continue to pass.

### Added — `scripts/validate_skills.sh` v2 content-integrity lints + pre-commit hook

The validator previously checked frontmatter, size tiers, and reference integrity but
could not catch content regressions that had accumulated over prior sessions. v2 adds
four content-integrity rules scoped to shipped skill prose (`SKILL.md` plus
`references/**/*.md`, excluding `HANDOFF.md` and `TODO_*.md` meta-docs):
**Rule 6** blocks project-specific precedent identifiers (per-project IDs,
prior-citation slugs, ordinal-numbered paper labels) from leaking into shipped
skills; **Rule 7** blocks absolute personal home-directory paths in shipped
prose (scripts and exemplar `.meta.yaml` fixtures are out of scope); **Rule 8** flags dated precedent
blockquotes (`^> ... YYYY-MM-DD`) while allow-listing `Last updated:` / `Created:` /
`Updated:` / `Date:` meta-header prefixes; **Rule 9** warns on Korean prose in
`SKILL.md` body outside fenced code blocks, tables, blockquote examples, the
Communication Rules section, and frontmatter (Korean triggers remain permitted).
Rules 6–8 are FAIL-level; rule 9 is WARN-only pending per-skill translation
decisions. A `.git/hooks/pre-commit` hook runs the validator automatically when any
`skills/**/*.md` or the validator itself is staged, early-exiting otherwise to keep
non-skill commits fast.

### Changed — `/orchestrate` Dialogue Protocol is now the default interactive execution path

The prior interactive flow was a plain bulleted plan followed by "Shall I proceed with
step 1?" — a confirmation that surfaced no lock-in cost. The revised **Workflow Execution
— Dialogue Protocol** section makes per-fork decision-node rendering the primary control
flow: identify the node, render the template (context + numbered options + per-option
`unlocks` / `locks` / `recovery_cost`), wait for a numeric choice or a control word
(`back` / `pause` / `skip`), echo the lock in one line, invoke the matched skill, and
return for the next fork. The Multi-Skill Workflows table gained a **Nodes** column that
maps each scenario to the N1 – N9 node IDs. The `--e2e` Flag section now prescribes
node-by-node default application with per-node logging to `qc/_pipeline_log.md`, and
specifies that the PHI gate (N6) is the sole node that can HALT autonomous mode, while
Audit Recovery (N8) HALTs only when the routed recovery fails validation twice. The
Output Format multi-skill example was replaced with a worked N2 Paper Type rendering to
anchor downstream rendering style.

### Added — `/orchestrate` Dialogue Mode prototype (RPG-style decision nodes)

`/orchestrate` previously executed multi-skill pipelines with plan-then-confirm but
did not surface the downstream cost of each commitment (paper type, study design,
target journal timing, MA synthesis scope, audit recovery branch). The new
**Dialogue Mode** is the interactive default: at each major fork, the orchestrator
renders a decision node (context, numbered options, per-option `unlocks` / `locks` /
`recovery_cost`) and the user picks a number. `--autonomous` / `--e2e` bypasses the
rendering and uses each node's `default`, logging the choice to
`qc/_pipeline_log.md`. The prototype lists 9 primary nodes — entry classification,
paper type, study design (STARD/CONSORT/STROBE/TRIPOD+AI), target-journal timing
(commit-now vs. late-bind), MA synthesis depth (primary / +subgroups / +sensitivity /
+meta-regression), PHI Safety Gate, autonomy flag, Step 7.4a audit recovery branch,
and `/write-paper` section entry on re-entry — with rendering templates and
autonomous-default rationales. Load-on-demand reference at
`skills/orchestrate/references/dialogue_nodes.md`; `SKILL.md` body gains only a
one-paragraph pointer to preserve token economy.

### Added — `/meta-analysis` Phase 9 (Co-author Circulation) + Phase 10 (Self-Audit Recovery)

The pipeline previously stopped at Phase 8 (Reporting & Manuscript), leaving two operational
loops undocumented. **Phase 9** standardizes pre-submission circulation: thread-reply
continuity, attachment scope (body + change summary only; exclude GA / cover letter / COI
until journal is confirmed), recipient structure (corresponding + one senior methodologist
TO, co-authors CC), the 7-day deadline rule, and journal-undetermined framing. **Phase 10**
formalizes the v{N} → v{N+1} rebuild sprint when an audit uncovers structural data or
protocol-application errors — audit log, CSV re-verification, analysis re-run, manuscript
auto-sync, figure regeneration, change summary, protocol-registry amendment in parallel,
and the transparent re-circulation framing. Triggers include extraction ↔ source
mismatch, protocol-analysis disagreement, hand-typed script literal errors, and
consensus-record ↔ locked-dataset disagreement. Anti-patterns (hide & submit, reframe as
"minor revision", cover-letter-only disclosure) are documented as do-not.

### Added — `/write-paper` Step 7.4a Audit Recovery Branch

Phase 7 polish was a linear flow (draft → review → revise → submit) that silently proceeded
past structural self-review findings. Step 7.4a makes the recovery loop explicit: when
Step 7.4 returns a fatal `accuracy`, `data_fidelity`, `protocol_mismatch`, or
`numerical_claim` issue, an unresolved Step 7.3a primary-source disagreement, a persistent
`[VERIFY-CSV]` tag, or a registry ↔ analysis inconsistency, the pipeline halts Steps 7.5 –
7.6 and routes to the appropriate upstream recovery. For MA manuscripts this is
`/meta-analysis` Phase 10; for non-MA manuscripts with extraction errors, back to
`/write-paper` Phase 2; protocol amendments halt for human decision. On re-entry the
pipeline resumes at Step 7.3, not Step 7.1, because recovery may have introduced new
citations. Loop budget: one recovery cycle expected; a second cycle on the same manuscript
prompts a root-cause review of Phase 2 / 6 / 6b.

### Added — `/check-reporting` Step 4c Registration / Protocol Timing Consistency Check

The registration identifier alone is a single checklist item and passes even when the
manuscript is internally inconsistent about registration / amendment timing. Step 4c
audits five consistency items: registration identifier present in Methods/Abstract/
cover letter, registration date ↔ screening/extraction milestone order, amendment date ↔
Methods-described change agreement, cross-artifact agreement between Methods and the
registry record (e.g., PROSPERO PDF), and retrospective-registration disclosure when
the registration date post-dates extraction start. Findings carry the
`[REGISTRATION-TIMING]` label in Part C Action Items, with `fixable_by_ai: false` when
reconciliation requires an external amendment filing. A new `registration_timing` JSON
field is emitted in Part D. Applies to PRISMA 2020, PRISMA-DTA, PRISMA-P, MOOSE, CONSORT,
and SPIRIT. Common Gaps list updated to include amendment-date consistency as item #2.

### Added — Verified neurointervention/cerebrovascular journal profiles

- **JNIS (Journal of NeuroInterventional Surgery)** — compact + detail profiles built from user-supplied author-guidelines PDF (BMJ, SNIS). Covers double-anonymised review, ORCID mandate, BMJ Tier 3 data-sharing policy, Key Messages box requirement, AI policy aligned with BMJ/ICMJE.
- **Journal of Stroke** (Korean Stroke Society) — compact + detail profiles from user-supplied author-guidelines PDF. Full OA CC BY-NC 4.0 with no APC; Vancouver numbered references; structured 250-word abstract for Original Articles; mRS/mTICI/sICH definition requirements; AI policy defaults to ICMJE/WAME (no explicit journal-specific text).
- **Stroke (AHA/ASA)** — compact + detail profiles from user-supplied author-instructions PDFs. ISSN verified against ISSN Portal (print 0039-2499 / online 1524-4628, ISSN-L 0039-2499). Three-category science triage (Basic/Translational, Clinical, Population); structured 300-word abstract; Vancouver references listing first 10 authors + "et al."; 90-day revision window with mandatory Graphic Abstract at revision; explicit AI policy per AHA/ICMJE.

All three profiles follow the two-tier public-library format established by `INSI.md` and include a verification note citing the source author-guidelines PDF.

### Added — `/find-journal` Phase 3.6 Profile Coverage Advisory

Previously, when the public profile library had a known gap for the manuscript's field,
the ranking silently substituted adjacent journals and the user never learned that a
better-fitting target existed. The new Phase 3.6 scans `skills/find-journal/TODO_*_profiles.md`
files, matches their `## Field Keywords` block against the manuscript's themes, and appends
a Coverage Advisory block between the comparison note and the Mandatory Disclaimer when
a relevant TODO has still-missing journals. The advisory names the missing journals,
cites their publisher and 1-line rationale verbatim from the TODO file, and directs the
user to `/add-journal` with a PDF to close the gap per `POLICY.md`. No false alarms when
no TODO is relevant.

`TODO_neurointervention_profiles.md` updated with a `## Field Keywords` section so it
feeds the advisory. Future field TODO files should follow the same convention.

### Added — `/write-paper` Step 7.3a trigger 5 (reporting-quality checklist SRs)

Step 7.3a Numerical Claim Audit previously fired only on pooled estimates, comparative-arm
values, `[VERIFY-CSV]` tags, or post-v1 revisions. It missed the reporting-quality
systematic review pattern, where all headline numbers are derived by counting cells in an
items × studies checklist matrix (TRIPOD+AI, PROBAST+AI, CLAIM, PRISMA, STARD, CHARMS,
ARRIVE). The same failure class applies — hand-tallied totals drift from cell-level truth
while every downstream artifact echoes the wrong number.

Trigger 5 is now mandatory whenever the manuscript reports corpus-level, study-level, or
item-level PRESENT / PARTIAL / ABSENT / compliance counts or percentages from a checklist
synthesis. The procedure adds five steps specific to this pattern: per-study totals
recomputation, corpus-level Σ non-NA denominator, item-level roll-up, 3-way consistency
(manuscript ↔ per-study JSON ↔ summary document), and a reproducible audit script that
emits `numerical_claims_log.csv` and exits non-zero on any mismatch.

A companion rule is recorded in `~/.claude/rules/numerical-safety.md` so the gate
triggers even in non-skill workflows.

## [2.3.0] - 2026-04-19

### Added — Numerical Hallucination Prevention Layer

A real incident during a revision run exposed that the citation-safety pipeline did not have
a symmetric counterpart for numerical claims. Citations were verified end-to-end against
PubMed (0 fabricated refs), while a hand-typed `matrix()` in a revision-era R script silently
reversed a Fisher exact 2x2 ("3/45 vs 0/56, p=0.085" where the source said "0/45 vs 1/56,
p=0.37"). Every internal consistency check passed because every artifact echoed the same
wrong number. Detection required an explicitly requested second-pass audit with random
sampling against the primary paper.

To close that gap, four skills now enforce a common 3-layer (CSV ↔ analysis script ↔
manuscript) audit, with additional back-checking against the primary paper for revisions and
pooled estimates:

- **`/meta-analysis` Phase 6b — Post-Analysis Source Fidelity Audit (new).** After Phase 6
  statistical synthesis, mandates no hand-typed numerical matrices when a CSV exists,
  separate consensus-log rows for comparative-arm subsets, and a random 3-claim back-check
  (manuscript → R output → primary-source Table/Figure) before advancing to GRADE. A single
  mismatch is a P0 blocker.
- **`/self-review` Phase 2.5a — Numerical Source-Fidelity Audit (new).** Complements the
  existing Phase 2.5 internal consistency check with external validation: stratified random
  sampling of 5 claims, 3-layer traversal (manuscript ↔ CSV ↔ primary paper), and escalation
  of any mismatch to Major Comment. Revision-introduced numbers and comparative-arm specific
  values are the two highest-yield strata and are always sampled.
- **`/revise` Step 2.5 — Revision Numerical Lineage Check (new).** Any `/analyze-stats`
  re-run during revision must tag new numerical claims with `[VERIFY-CSV]`, read inputs from
  the locked extraction CSV, and maintain a response-document audit table that maps each new
  number to its source script:line + CSV coordinate + primary-source location. Prose
  generation is gated on the audit clearing.
- **`/write-paper` Step 7.3a — Numerical Claim Audit (new).** Sits alongside the existing
  citation verification step. Triggered whenever the manuscript contains pooled estimates,
  comparative-arm values, `[VERIFY-CSV]` tags, or is a post-v1 revision. Greps all analysis
  scripts for hand-typed numerical literals without CSV-coordinate comments and flags them
  as structural risks regardless of current correctness.

All four skills reference the revision-era Fisher-exact reversal pattern described above as
a concrete failure mode rather than an abstract risk. Complementary companion rules were
added to `~/.claude/rules/data-integrity.md` and a new `~/.claude/rules/numerical-safety.md`
so the gates trigger even in non-skill workflows.

## [2.2.1] - 2026-04-18

### Added

- **`/meta-analysis` Phase 3 multi-round screening structure**: Phase 3a now distinguishes Round 1 (single-reviewer initial screen), Round 2 (dual independent screen with Cohen's kappa), Round 3 (first-reviewer adjudication of disagreements), Round 4 (full-text), and PRISMA flow.
- **AI-assisted pre-screening template** (`meta-analysis/references/ai_pre_screening_template.py`): reusable script for compressing R3 adjudication. Generates AI suggestions only; first reviewer must independently confirm or overturn each. Includes Methods boilerplate citing model name and version. Companion priority-sort logic built in.

### Changed

- **`/meta-analysis` SKILL.md**: Phase 3 expanded from 17 to 39 lines (3a–3e). Maintains kappa requirement and adds explicit guidance for handling MAYBE-tagged records.

## [2.2.0] - 2026-04-18

### Added

- **5 new skills** (32 total): `humanize`, `author-strategy`, `peer-review`, `ma-scout`, `lit-sync`
  - **humanize**: 18-pattern AI writing detection and removal for academic manuscripts
  - **author-strategy**: PubMed author profile analysis with study type classification and strategy report
  - **peer-review**: Structured peer review drafting with journal-specific formatting (RYAI, INSI, EURE, AJR, KJR)
  - **ma-scout**: Meta-analysis topic discovery — professor-first or topic-first modes with PubMed E-utilities, PROSPERO check, and PICO scaffolding (732 lines, largest new skill)
  - **lit-sync**: Zotero + Obsidian reference sync pipeline with cross-cutting concept note extraction
- **Anti-hallucination clauses** added to all 32 skills. Domain-specific rules prevent fabricated variables, effect sizes, citations, and clinical definitions.
- **SKILL_TEMPLATE.md** (`docs/`) — canonical template for new skill creation with quality tier requirements
- **validate_skills.sh** (`scripts/`) — automated skill linter checking frontmatter, anti-hallucination, gates, line count tier, and reference integrity
- **3-country harmonization CSV** (`replicate-study/references/harmonization_3country.csv`) — KNHANES+NHANES+CHNS variable mapping (45 rows)

### Changed

- **cross-national**: Expanded from 2-country to 3-country support (KNHANES+NHANES+CHNS). Added ~100 lines of validated variable codings for KNHANES, NHANES, and CHNS with specific warnings (BMI cutoffs, hemoglobin units, survey weight handling). Added composite score replication warnings from LE8 validation.
- **batch-cohort**: Added physician-diagnosis requirement for outcome definitions (rule 8) and full 8-covariate default (rule 9). Expanded self-adjustment removal for education/income/MetS.
- **replicate-study**: Added 3-country harmonization reference.
- **fulltext-retrieval**: Fixed frontmatter (added missing `tools` and `model` fields).

### Infrastructure

- All 32 skills now pass `validate_skills.sh` with 0 FAIL.
- Quality tier distribution: 15 HIGH (300+ lines), 14 MID (150-300), 3 THIN (<150).

## [2.1.0] - 2026-04-15

### Added

- **find-cohort-gap**: New skill for systematic research gap discovery from cohort databases. 6-phase pipeline (cohort intake → PI profiling → intersection matrix → literature saturation scan → 6-Pattern scoring with comparison tables → feasibility gate → ranked one-pager proposals). Works with any cohort: NHIS, UK Biobank, institutional EMR, health checkup registries. Includes 4 reference files (pattern scoring rubric, cohort profile template, one-pager template, saturation query templates). Integrates with `/search-lit` for PubMed searches and feeds into `/design-study` → `/write-paper` pipeline.

## [2.0.0] - 2026-04-14

### Changed

- **Demos regenerated with `orchestrate --e2e` pipeline.** All 3 demos now produce a consistent artifact set: `analyze.{py,R}`, `_analysis_outputs.md`, `_pipeline_log.md`, `manuscript.md`, `manuscript_final.docx`, `reporting_checklist.md`, `review_comments.md`, `figures/_figure_manifest.md`, and study-type-specific tables and figures.
- Demo output structure flattened: `tables/` replaces `output/` for CSV files; manuscript and QC artifacts live at demo root.
- Previous demo scripts and outputs archived to `demo/_archive/` for reference.

### Added

- **Demo 1 (Wisconsin BC, STARD):** 19 artifacts. STARD flow diagram (D2), reporting checklist (82.1% compliance), self-review (74/100), submission-ready DOCX.
- **Demo 2 (BCG Vaccine, PRISMA):** 24 artifacts. R metafor analysis with forest plot, funnel plot, bubble plot, PRISMA flow diagram (D2), reporting checklist (77.8% compliance), self-review (72/100), submission-ready DOCX.
- **Demo 3 (NHANES Obesity, STROBE):** 23 artifacts. Python analysis with prevalence chart, OR forest plot, HbA1c distribution, age x BMI subgroup plot, STROBE flow diagram (D2), reporting checklist (81.8% compliance), self-review (75/100), submission-ready DOCX.
- `CHANGELOG.md` (this file).

### Pipeline artifacts (new in each demo)

| Artifact | Description |
|----------|-------------|
| `_pipeline_log.md` | 7-step execution trace with pass/fail status |
| `_figure_manifest.md` | Structured figure inventory for downstream consumption |
| `reporting_checklist.md` | Item-by-item guideline compliance assessment |
| `review_comments.md` | Self-review with Major/Minor classification and scores |
| `manuscript_final.docx` | Pandoc-built submission-ready Word document |

## [1.0.0] - 2026-04-08

Initial release with 22 skills and 3 demo pipelines.
