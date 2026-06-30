<!-- Domain probe module — shared, vendored BYTE-IDENTICAL by /peer-review and /self-review.
     Severity words below (MAJOR / MINOR / major / minor) denote finding severity, NOT a journal
     recommendation. Each consuming skill maps findings to its own output:
       - peer-review: Major / Minor comments + Confidential Comments to the Editor; a
         scoping-fit / mapping-not-pooling / over-claim flaw is placed as Major #1.
       - self-review: Anticipated Major / Minor Comments (Fatal / Fixable) mapped to category letters.
     Do NOT edit one copy only — run `python3 scripts/check_domain_probe_sync.py --sync`. -->

# Scoping review probes (SC1–SC8)

An 8-probe checklist for **scoping reviews** — reviews that *map* the breadth of evidence on a topic, clarify concepts/definitions, and identify gaps. These probes complement (do not replace) the generic Phase 2 checklist and the **PRISMA-ScR** reporting items (Tricco et al. *Ann Intern Med* 2018), and assume the JBI / Arksey & O'Malley / Levac conduct frameworks. They target what is specific to a scoping design: whether the question genuinely suits a *mapping* (not an effectiveness/accuracy) review, whether the conduct uses scoping methods (PCC framing, charting, optional appraisal), and — the single most common over-reach — whether the synthesis stays a **map** rather than drifting into pooled effect estimates and definitive effectiveness claims. SC1 (scoping fit), SC6 (critical-appraisal calibration — the asymmetric trap), and SC7 (mapping not pooling) are the highest-yield; run them first.

**SC1 — Scoping fit and objectives (mapping intent, PCC framing)**:
- Is the review genuinely a **scoping** question — mapping the extent/range/nature of evidence, clarifying concepts, or identifying gaps — rather than a focused **effectiveness/accuracy** question that should be a systematic review (PRISMA 2020 / PRISMA-DTA)?
- Are objectives framed with **Population, Concept, Context (PCC)** or an equivalent mapping structure, not a PICO effectiveness/comparison frame with a defined outcome estimate?
- A focused "is X effective / is test Y accurate?" question run as a scoping review (to sidestep risk-of-bias and synthesis), or a scoping review whose objectives are really an SR's → MAJOR (reframe as a systematic review, or restate the objective as mapping).

**SC2 — Protocol and registration (a-priori; OSF, not PROSPERO)**:
- Is an **a-priori protocol** available (OSF / Figshare / a published protocol), with the question, eligibility, and charting plan pre-specified?
- Note that **PROSPERO does not register scoping reviews** — a manuscript claiming PROSPERO registration for a scoping review is in error and should cite the correct registry/repository.
- No protocol for a scoping review of any size, or a wrong-registry claim → MINOR (protocol absent → MAJOR if the charting plan appears post-hoc / outcome-driven).

**SC3 — Eligibility by concept; sources of evidence (not only studies)**:
- Are eligibility criteria specified by **PCC plus source characteristics** (years, language, publication status, source/evidence types) **with a rationale**?
- Does the review admit the **heterogeneous "sources of evidence"** a scoping review is meant to map (quantitative and qualitative research, grey literature, policy/guidance, expert opinion) where relevant, rather than silently restricting to a narrow study type and presenting it as a comprehensive map?
- Over-restrictive, study-only eligibility presented as a comprehensive map of the field, or eligibility with no rationale → MINOR.

**SC4 — Search comprehensiveness and reproducibility**:
- Is the **full search strategy for at least one database reproducible** (terms, limits), the date of the most recent search stated, and the information sources appropriate to a *mapping* aim — typically **multiple databases plus grey literature** rather than a single narrow source?
- Given that scoping reviews aim for breadth, is the search broad enough to support a "map the field" claim?
- A comprehensiveness/mapping claim resting on one narrow database with no grey-literature or no reproducible strategy → MAJOR / MINOR per the strength of the claim.

**SC5 — Selection and data charting**:
- Is the **two-stage selection** process (title/abstract then full-text) described, and the **data-charting** process specified — a calibrated/team-tested charting form, whether charting was **independent / in duplicate**, and any **iterative refinement** of the form (charting is iterative in scoping reviews)?
- Is the correct terminology used (**charting**, not extraction; **sources of evidence**, not only studies)?
- No charting process described, or single-reviewer charting with no calibration behind a large map → MINOR (or MAJOR if selection itself is undocumented).

**SC6 — Critical appraisal is OPTIONAL (the asymmetric trap)**:
- Critical appraisal / risk-of-bias is **not required** in a scoping review (PRISMA-ScR items 12/16 are optional). A reviewer must **not** flag "no risk-of-bias assessment" as a deficiency for a scoping review, and authors need not appraise.
- Conversely, if appraisal **was** done, is the rationale, method, and use reported (items 12/16)? And does the review avoid claiming **certainty grading (GRADE) or quality-weighted conclusions** it never derived?
- The trap is bidirectional: (a) demanding RoB of a scoping review is a mis-calibrated review comment; (b) a scoping review asserting GRADE-style certainty or "high-quality evidence shows…" without having appraised is over-claiming → MINOR/MAJOR per how load-bearing the certainty claim is.

**SC7 — Synthesis is mapping, NOT pooling (no effect estimates)**:
- Are results presented as a **map/characterisation** — counts, categories, concept/theme groupings, evidence-gap maps, charting tables — rather than a **meta-analytic pooled estimate** (pooled OR/RR/HR/AUC, summary sensitivity/specificity)?
- A scoping review should **not** compute or headline a pooled effect/accuracy estimate; doing so is an estimand/scope mismatch (the design carries no risk-of-bias or synthesis machinery to support an effect claim).
- A pooled effect/accuracy estimate, forest plot of effects, or quantitative effectiveness synthesis presented from a scoping review → MAJOR (move to a systematic review/meta-analysis, or relabel the figure as a descriptive frequency map).

**SC8 — Interpretation, gaps, terminology, and reporting**:
- Are conclusions matched to a **descriptive map** — what evidence exists, where the gaps are, whether a future systematic review/primary study is warranted — and free of **clinical-practice recommendations** or definitive effectiveness/accuracy claims a map cannot support (cf. the scope-coherence discipline)?
- Is a **PRISMA-ScR flow diagram** present, the study correctly labelled a scoping review (not conflated with a systematic review), and the report mapped to **PRISMA-ScR**?
- A practice recommendation or definitive effectiveness/accuracy conclusion drawn from a scoping map, mislabelling the study as a "systematic review," or missing PRISMA-ScR reporting → MAJOR (over-claim) / MINOR (reporting), per centrality.
