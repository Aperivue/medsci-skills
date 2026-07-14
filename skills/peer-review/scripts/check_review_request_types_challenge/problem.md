# Challenge card — review-request-type gate (peer-review)

## Problem

Every detector in this repository audits the **manuscript**. None audits the
**review**. That is the gap this card closes.

Sort every reviewer request into two kinds:

- **Disclosure** — *"show what the study already knows and has not printed."*
  The analysis unit; the subset's characteristics; a CI already computed; the n
  per stratum; the reading order. It costs the authors nothing and **surfaces**
  errors.

- **Computation** — *"produce a number that does not yet exist."*
  Test this difference; bootstrap a CI; propagate these rates. It creates a
  **new, unreviewed error surface**, produced under revision deadline by authors
  who will not re-check it, and accepted next round by a reviewer who reads its
  *existence* as compliance.

In the incident that motivated the rule, three of the four defects found in a
revision had been **manufactured by the reviewer's own two computation requests**.
The fourth had been on the page since the first submission and survived two
rounds of review.

## Why a script and not a sentence

The rule already exists. `/peer-review` Phase 3 states it in prose; Phase 6 lists
it as a checkbox. **Prose did not bind.** In the first live review after the rule
shipped, a draft went out with fifteen asks, six of them computation and one
requiring a second reader — and it **passed every neighbouring gate**: word count,
em-dash density, forbidden recommendation words, attitude markers, hedging ratio.

Those gates held because they are scripts. This one failed because it was a
sentence. The difference was not importance — request-type is the most important
of them — it was **executability**.

## What the gate does

`check_review_request_types.py` reads the reviewer's draft, treats every bullet
and numbered item as an ask, and classifies it:

| verdict | fires when |
|---|---|
| `COMPUTATION_UNJUSTIFIED` | a computation request states no reason the manuscript's existing tables cannot answer it (Phase 3 requires that justification) |
| `COMPUTATION_HEAVY` | more than `--max-computation` (default 2) computation/new-data requests |
| `NEW_DATA_REQUESTED` | the ask needs data that does not exist — a second reader, re-segmentation, a new cohort. Strictly worse: it cannot be satisfied in a revision at all |
| `NESTED_P_REQUESTED` | the ask requests a P value between an analysed subset and the parent cohort containing it. Never *request* the table `check_nested_group_comparison.py` exists to flag |
| `ESTIMATOR_UNNAMED` | an effect size or interval is requested without naming the estimator; the authors adopt the loose phrase verbatim |

## Precision over recall, deliberately

The gate cannot know whether a number already exists in the manuscript, so it
gates on the **request's own verbs** and errs toward silence:

- **Negation is honoured.** *"I am not asking you to repeat the validation"* and
  *"a single reader **without** adjudication"* are not requests for new data.
  *"…**without** a significance test — the groups are nested"* is a reviewer doing
  the right thing, and is not flagged.
- **Description is not request.** *"bootstrap intervals are reported for the median
  only"* states a fact. Only an ask carrying a request cue (a leading imperative,
  or *please / should / consider / I would suggest*) is classified at all.
- **Feasibility is not justification.** *"this is a text filter on data you already
  hold"* says the work is cheap, not that the existing tables cannot answer the
  question. Phase 3 asks for the second, and so does the gate.

A detector that never falsely accuses a disclosure request is worth more than one
that catches every computation.

## Fixtures

Synthetic. No real review, no manuscript, no PII — only the *shape*.

- `fixture/undisciplined.md` — propagate, bootstrap, a second reader, a
  subset-vs-parent P value, and modelling, none of them justified.
- `fixture/disciplined.md` — the same review rewritten: disclosure asks, one
  computation carrying an explicit *"the present tables cannot answer this"*, and
  a subset table requested **without** a significance test.

## Verify

```bash
./verify.sh
```

Exit 0 and `PASS` when the undisciplined draft is flagged (exit 1 under `--strict`)
and the disciplined draft is clean (exit 0).
