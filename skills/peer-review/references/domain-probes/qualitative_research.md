<!-- Domain probe module — shared, vendored BYTE-IDENTICAL by /peer-review and /self-review.
     Severity words below (MAJOR / MINOR / major / minor) denote finding severity, NOT a journal
     recommendation. Each consuming skill maps findings to its own output:
       - peer-review: Major / Minor comments + Confidential Comments to the Editor; a
         reflexivity / analysis-transparency / over-claim flaw is placed as Major #1.
       - self-review: Anticipated Major / Minor Comments (Fatal / Fixable) mapped to category letters.
     Do NOT edit one copy only — run `python3 scripts/check_domain_probe_sync.py --sync`. -->

# Qualitative research probes (QL1–QL8)

An 8-probe checklist for **qualitative studies** — in-depth interviews, focus groups, observation/ethnography, document analysis, grounded theory, phenomenology, narrative research. These probes complement (do not replace) the generic Phase 2 checklist and the qualitative reporting standards — **COREQ** (interviews/focus groups; Tong et al. 2007) and **SRQR** (all qualitative approaches; O'Brien et al. 2014). They target what makes qualitative rigour distinct from quantitative validity: researcher **reflexivity**, a transparent **analysis** process, **trustworthiness** (credibility/dependability/confirmability/transferability) rather than statistical validity, and findings **grounded in quoted data** — and they guard the most common mis-calibration on both sides: applying quantitative yardsticks (sample-size power, statistical generalizability, p-values) to qualitative work. QL2 (reflexivity), QL5 (analysis transparency), and QL6 (trustworthiness, not statistical validity) are the highest-yield; run them first.

**QL1 — Approach/paradigm fit and research question**:
- Is a **qualitative** approach justified for the question — exploring meaning, experience, process, or context, rather than measuring frequency/effect (which would be a quantitative design)?
- Is a **named approach** (grounded theory, phenomenology, ethnography, case study, narrative) and guiding paradigm stated **with a rationale**, rather than an unspecified "qualitative study" / "thematic analysis" with no methodological orientation?
- A question that is really quantitative (prevalence/effect) answered with a few interviews, or no named methodological orientation behind the analysis → MAJOR (method–question mismatch) / MINOR (unnamed approach).

**QL2 — Reflexivity and researcher positioning**:
- Are the **researcher's characteristics** reported — who collected the data, their credentials/role, experience/training, and **prior relationship to participants** — and is there reflexive consideration of how their assumptions/position may have shaped data collection and interpretation?
- Reflexivity is a core qualitative-rigour requirement (COREQ Domain 1; SRQR item 6) and the **single most-omitted** element.
- An interview/focus-group study with no reflexivity / no statement of who interviewed and their relationship to participants → MAJOR (or MINOR if partially addressed).

**QL3 — Sampling logic and adequacy (purposive; information power / saturation)**:
- Is the **sampling strategy** stated and justified — **purposive / theoretical / maximum-variation** logic appropriate to the question, not an unexplained convenience sample — and is there an argument for **when sampling stopped** (data **saturation** or information power)?
- A **small sample is not a flaw** in qualitative work; the flaw is an *unjustified* sample with no purposive rationale and no saturation/information-power discussion.
- Convenience sample presented with no rationale, or no account of sampling adequacy/saturation behind broad thematic claims → MINOR / MAJOR per centrality.

**QL4 — Data-collection rigour**:
- Are the **data-collection methods** described in enough detail to judge them — the **interview/topic guide** (and whether it was piloted/iterated), the **setting**, **recording and transcription**, **field notes**, and interview/focus-group **duration**?
- Thinly reported data collection (no guide, unclear recording/transcription, no setting) that undercuts interpretability → MINOR.

**QL5 — Analysis transparency and audit trail**:
- Is the **analysis process** transparent — how many **coders**, the **coding framework/tree**, whether themes were **derived inductively or applied a priori**, any **software**, and an **audit trail**?
- "Themes **emerged** from the data" with no described coding/analytic process is a black box.
- An analysis with no described coding process / no audit trail behind the reported themes → MAJOR (analysis not reproducible/auditable).

**QL6 — Trustworthiness, NOT statistical validity (the calibration trap)**:
- Are **trustworthiness** techniques reported and matched to the four criteria — **credibility** (member checking, triangulation, prolonged engagement), **dependability** (audit trail), **confirmability** (reflexivity), **transferability** (thick description) — rather than quantitative "reliability/validity"?
- The trap is bidirectional: (a) a **reviewer** must **not** demand a power calculation, a "representative" sample, statistical generalizability, or treat inter-coder κ as the sole truth — these are quantitative yardsticks inappropriate to qualitative work; (b) **authors** must **not** claim statistical generalizability or dress qualitative findings in quantitative certainty.
- Missing trustworthiness strategies entirely, or quantitative-validity language misapplied (by either side) → MAJOR / MINOR per how load-bearing it is.

**QL7 — Findings grounded in data (quotations, thick description, deviant cases)**:
- Are the themes **substantiated by participant quotations / excerpts** (with participant identifiers), with enough **thick description** to let the reader judge the interpretation, and is there **consistency between the data and the findings**?
- Are **negative / deviant cases** and minor themes considered, not just confirmatory exemplars?
- Asserted themes with no quoted evidence, or interpretation not traceable to the data → MAJOR; cherry-picked confirmatory quotes with no deviant-case consideration → MINOR.

**QL8 — Ethics, interpretive scope, and reporting standard**:
- Are **ethics** reported (IRB approval/consent; confidentiality and de-identification of identifiable narrative quotes), and does interpretation **stay within what qualitative data support** — no **causal, effectiveness, prevalence, or population-level** claims, and no over-generalisation beyond the studied context (**transferability**, not generalizability)?
- Is the study mapped to the appropriate reporting standard — **COREQ** (interviews/focus groups) or **SRQR** (broader qualitative)?
- Causal/quantitative/population over-claiming from qualitative data, missing consent/de-identification for identifiable quotes, or no reporting-standard mapping → MAJOR (over-claim / ethics) / MINOR (reporting).
