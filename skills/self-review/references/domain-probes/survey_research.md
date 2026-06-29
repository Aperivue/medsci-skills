<!-- Domain probe module — shared, vendored BYTE-IDENTICAL by /peer-review and /self-review.
     Severity words below (MAJOR / MINOR / major / minor) denote finding severity, NOT a journal
     recommendation. Each consuming skill maps findings to its own output:
       - peer-review: Major / Minor comments + Confidential Comments to the Editor; a
         representativeness / response-rate / instrument-validity flaw is placed as Major #1.
       - self-review: Anticipated Major / Minor Comments (Fatal / Fixable) mapped to category letters.
     Do NOT edit one copy only — run `python3 scripts/check_domain_probe_sync.py --sync`. -->

# Survey / questionnaire study probes (SV1–SV8)

An 8-probe checklist for **self-report survey / questionnaire studies** — knowledge-attitudes-practices (KAP), physician and patient surveys, cross-sectional questionnaires, and web/e-surveys. These probes complement (do not replace) the generic Phase 2 checklist, the **CROSS** reporting items (and **CHERRIES** for internet surveys), and the scale-reliability guidance (`analyze-stats` Survey/Likert). They target the gap between a clean results table and whether the sample can support a population claim at all: representativeness, the response-rate denominator and non-response bias, and whether the instrument measures what it claims. The most common failure is generalising from a self-selected convenience sample. SV1 (representativeness), SV3 (response rate & non-response), and SV4 (instrument validity) are the highest-yield; run them first.

**SV1 — Target population, sampling frame, and representativeness**:
- Is the **target population** defined and the **sampling frame** (the actual list/channel from which respondents were drawn) stated, with comment on how well the frame **covers** the target population (coverage error)? A survey distributed via a society listserv, social media, or a conference app reaches a self-selected slice, not "clinicians" or "the public."
- Is there any evidence the respondents **resemble the target population** (compare respondent demographics to a known population, or to the frame)?
- A convenience / self-selected / undisclosed-frame sample whose results are generalised to a population, with no representativeness assessment → MAJOR (downgrade claims to "among respondents").

**SV2 — Sampling method and sample-size justification**:
- Is the **sampling method** stated and correctly characterised — **probability** (random/systematic/stratified/cluster) vs **non-probability** (convenience/snowball/quota)? A non-probability sample cannot yield design-unbiased population estimates and should not be presented as if it could.
- Is there an **a-priori sample-size or precision justification** (for a prevalence/estimate: target margin of error; for a comparison: power), rather than a post-hoc rationalisation of however many happened to respond?
- A non-probability sample presented as representative, or no sample-size rationale for a precision / comparison claim → MAJOR / MINOR per the claim.

**SV3 — Response rate (defined denominator) and non-response bias**:
- Is a **response rate reported with an explicit, defensible denominator** (an AAPOR/CASRO-style definition: completed responses ÷ eligible invitees), not just "N people responded"? For an **open** web survey where the denominator is unknowable, is that limitation stated (a view/participation/completion rate per CHERRIES instead of a true response rate)?
- Is **non-response bias** assessed — responders vs non-responders, early vs late responders, or respondents vs the population? A low response rate is not fatal, but an **unassessed** low/undefined response rate carrying a population estimate is.
- No defined denominator, or a low response rate with no non-response analysis behind a population claim → MAJOR.

**SV4 — Instrument development, validity, and reliability**:
- Was the questionnaire **previously validated** (cited) or **newly developed**? For a new/adapted instrument, was it **pre-tested / piloted** (cognitive interviewing, a pilot sample)?
- For **multi-item scales**, are **validity** (content/construct, factor structure) and **reliability** (Cronbach's α / McDonald's ω, test–retest) reported? (A negative or implausibly low α usually signals a reverse-coded item not re-scored — see the scale-reliability guidance, not a multidimensionality story.)
- A novel, unvalidated, un-piloted instrument carrying the headline, or multi-item scales with no reliability evidence → MAJOR (or MINOR if the instrument is established and cited).

**SV5 — Administration mode, coverage, and e-survey (CHERRIES) reporting**:
- Is the **mode** (web, email, postal, telephone, in-person) and its **coverage/selection implications** stated (a web survey excludes the digitally excluded; a clinic survey excludes non-attenders)?
- For an **internet survey**, are the CHERRIES specifics reported: **open vs closed** (invited) survey; how the **denominator and completion** were computed; **voluntariness and any incentive**; **duplicate-submission control** (IP/cookie/log-in); and use of mandatory/adaptive questions and completeness?
- A web survey with no CHERRIES reporting (unknown denominator, no duplicate control, undisclosed incentive) → MAJOR / MINOR per centrality.

**SV6 — Question design and measurement**:
- Is the **instrument available** (appended or referenced) so wording can be judged? Are there **leading, double-barrelled, or ambiguous** questions, and is the handling of **neutral / "don't know" / not-applicable** options appropriate (forced-choice can manufacture opinion)?
- Are **Likert / ordinal** items treated appropriately (ordinal vs assumed-interval), and composite scores justified?
- An unavailable instrument, biased item wording, or inappropriate scale treatment driving a conclusion → MAJOR / MINOR.

**SV7 — Analysis, weighting, denominators, and missing data**:
- For a sample that under-represents parts of the target population, were **design weights / post-stratification** applied (and the weighting described), or are unweighted estimates presented as population figures?
- Are **per-item denominators** explicit and consistent (completers vs all respondents; the denominator should not silently shift across items), and is **item-level missingness / partial completion** handled and reported?
- Unweighted estimates from a skewed sample presented as population values, or shifting/opaque denominators → MAJOR.

**SV8 — Interpretation, generalisability, ethics, and reporting**:
- Are conclusions **matched to the sampled population** (no over-generalisation from a single-setting / low-response / convenience sample to "physicians" or "patients" broadly), and are self-report and **social-desirability** biases acknowledged?
- Are **ethics** (consent, IRB approval/exemption, data protection/anonymity) reported, and is the study mapped to **CROSS** (and **CHERRIES** for e-surveys) with instrument/data availability where possible?
- Over-generalisation beyond the sampled population, or missing ethics/consent reporting for an identifiable-respondent survey → MAJOR (generalisation) / MINOR (reporting), per centrality.
