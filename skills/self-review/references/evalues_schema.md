# evalues.json — declared E-values for the claim-vs-artifact gate (self-review Phase 2.5f)

`check_claim_artifact.py --evalues evalues.json` recomputes every E-value the manuscript reports
from the risk ratio and CI it belongs to. The prose scan reads only some ways of writing an
E-value and never a CI-limit E-value (open finding SR-02). A declared table names the estimate
directly, so the check is exact. The prose scan still runs, and the declared findings are added
to its output.

Start from `templates/evalues.json`.

| Field | Type | Meaning | How it is used |
|---|---|---|---|
| `entries` | list (non-empty) | one object per reported E-value pair | each entry is checked |
| `entries[].id` | non-empty string | a label, e.g. `primary` | names the claim (`EVDECL-<id>-point`, `-ci`) |
| `entries[].measure` | string | `rr` (also `RR`, `risk_ratio`, `risk ratio`), or `other:<description>` | `rr` is recomputed; `other:` is not (see below) |
| `entries[].estimate` | number > 0 | the risk ratio as printed | recomputed into the point E-value |
| `entries[].ci_low`, `ci_high` | number > 0 | the 95% CI as printed | must satisfy `ci_low <= estimate <= ci_high`; the limit nearest 1 gives the CI E-value |
| `entries[].evalue_point` | number > 0 | the reported E-value for the estimate | compared with the recomputed value; must appear in the text |
| `entries[].evalue_ci` | number > 0, optional | the reported E-value for the CI | compared with the recomputed value when present |
| `entries[].location` | string, optional | where it is reported | recorded, not gated (shown in messages) |
| `notes` | any | free text | not read |

A number is a JSON number (`1.52`) or a string of digits with an optional decimal point
(`"1.20"`). Write it exactly as printed: a string keeps trailing zeros, and the trailing
zeros set the precision. A JSON number keeps its printed form too (`1.20` is read as two
decimals), so either works. These all exit 2 and name the field:

- any other key, or a missing required field;
- a wrong type (a boolean, a list, a number as `id`);
- an empty `entries` list, an empty `id`, or `other:` with no description;
- a measure that is not on the list;
- a string with a sign, an exponent or letters;
- zero or a negative value;
- `NaN`, `Infinity`, `1e999`, or a value outside 1e-300 to 1e300;
- `ci_low > estimate` or `estimate > ci_high`;
- an unreadable or deeply nested file.

## How each value is checked

**Formula.** The VanderWeele–Ding E-value on the risk-ratio scale is
E = RR + sqrt(RR × (RR − 1)), with RR replaced by 1/RR when RR < 1. It is the formula
`evalue_point()` in this script already uses for the prose check. The CI E-value uses the
confidence limit nearest 1 (`domain-probes/observational_confounding.md` O6, "the point
estimate and the bound nearest the null"; `phases/phase2_5f_claim_artifact.md` §3, "near-null
confidence limit"). When the CI includes 1 there is no limit to explain away and the CI
E-value is 1 — the same formula applied to RR = 1.

**Rounding.** Every printed number is rounded. Each value is therefore read as the interval
of its printed precision: `1.52` means 1.515 to 1.525, and `2.4` means 2.35 to 2.45.

- *Point E-value.* E is recomputed at every RR in the estimate's interval, which gives
  [Emin, Emax]. The interval is 1 to the larger end when the RR interval holds 1.
- *CI E-value.* The same is done at every value the near-null limit can take. If the
  printed estimate cannot tell which side of 1 it is on, both limits are used, plus 1.
- *Verdict.* `EVALUE_DECLARED_MISMATCH` fires only when the declared E-value's interval and
  the recomputed interval do not overlap.

So RR 1.52 with a declared E-value of 2.42 passes. The printed RR gives 2.41, but an RR of
1.5249 gives 2.42.

**Presence.** `evalue_point` must equal some number in the manuscript text, compared as a
value: `"2.420"` matches a printed `2.42`, and a mid-dot decimal is read as a point. The
front matter is not read. `evalue_ci` is not looked for in the text.

**`other:` measures.** No reference in this repository states a conversion from an odds
ratio or a hazard ratio to a risk ratio, so an OR or HR is not accepted as a measure. Convert
it to an RR yourself and declare `rr`, or declare `other:<description>`. An `other:` entry is
still validated, and its presence check still runs, but its arithmetic is not recomputed.

## Verdicts

| Verdict | Severity | When |
|---|---|---|
| `EVALUE_DECLARED_MISMATCH` | Major | the declared point or CI E-value cannot come from the declared RR at any value its rounding allows |
| `EVALUE_DECLARED_NOT_IN_TEXT` | Minor | the declared `evalue_point` is not a number anywhere in the manuscript |
| `UNLISTED_METHOD` | Minor | `measure` is `other:<description>` |
| `EVALUE_DECLARED_NOT_ASSESSED` | Minor | the arithmetic was not checked because the measure is not a risk ratio |
| `OK` | — | the declared value is consistent with its RR |

`EVALUE_DECLARED_MISMATCH` counts toward `--strict`, like the other Majors.

## Not read

- Whether the E-value is attached to the primary estimate. The prose scan's
  `EVALUE_NON_PRIMARY` still covers that.
- E-values for continuous outcomes (standardized mean differences) and for risk differences.
  Declare these as `other:`.
- Any E-value convention that does not use the limit nearest 1 for the CI.
