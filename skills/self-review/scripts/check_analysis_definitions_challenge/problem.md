# Challenge card — analysis-definitions gate (self-review)

## Problem

A manuscript reports a multivariable Cox model. Nowhere does it say what the model
predicts. It reports discrimination and calibration. Nowhere does it say what the
predictions were scored against.

That is not a hard paper. That is an **incomplete** one — and it is invisible to
every other detector in this skill, because all twenty-four of them ask whether a
number is *correct*, and none asks whether the analysis that produced it was ever
*defined*.

## Why the count is not the crime

The rejection that motivated this gate said, verbatim:

> "**too many analyses** have been performed and reported, resulting in a manuscript
> with multiple tables and a lengthy Results section. **This appears to have
> contributed to omissions of critical information in the Materials and Methods
> section** and further undermines readability."

and, of the same manuscript:

> "This section is **largely incomprehensible** in its current form."

It is tempting to read that as *count the analyses and cap them*. **Do not.** A
second reviewer, on the same manuscript, listed the sensitivity analyses as a
**strength**. A detector that capped the count would have punished the strength and
missed the defect.

Load is the **cause**, not the crime: the analyses crowded the Methods until the
definitions fell out. So the gate reports the load as **context** (`ANALYSIS_LOAD`,
informational, never a verdict) and blocks only on what actually went missing.

The two fixtures make this concrete. They contain **the same number of analyses**
(two model families, two auxiliary analyses). One is flagged, one is clean. The only
difference is whether each analysis names its outcome and its reference standard.

## What the gate does

| verdict | fires when |
|---|---|
| `MODEL_NOT_IN_METHODS` | a model carries results but Methods never describes it |
| `MODEL_OUTCOME_UNDEFINED` | a Cox / Fine–Gray / logistic / Poisson / mixed model is specified with no outcome or dependent variable named near it (and, for time-to-event, no time variable or censoring rule) |
| `REFERENCE_STANDARD_UNDEFINED` | discrimination (C-index / AUC) or calibration is reported, but Methods names no reference standard or observed outcome to score against |
| `TIER_LABEL_UNDEFINED` | a tier / group label carries results but Methods never states its defining criterion |
| `ANALYSIS_LOAD` | informational — models, auxiliary analyses, tables. Context for the above; never a verdict on its own |

## Verify

```bash
./verify.sh
```

Exit 0 and `PASS` when the undefined manuscript is flagged (exit 1 under `--strict`)
and the defined one — carrying the identical analyses — is clean.
