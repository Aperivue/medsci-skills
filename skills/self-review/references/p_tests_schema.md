# p_tests.json — declared P-value tests for the reported-P gate (self-review Phase 2.5)

`check_reported_p_from_counts.py --tests p_tests.json` recomputes a table row's P with the
test the authors declare, and checks it against the declared alpha. A table cannot show which
test produced its P. Without a declaration, the gate can flag only a P that is off by more than
an order of magnitude under every test. It cannot see a P on the wrong side of alpha (open
finding SR-01). The order-of-magnitude rule still runs, and its output is unchanged.

Start from `templates/p_tests.json`.

| Field | Type | Meaning | How it is used |
|---|---|---|---|
| `alpha` | number, 0 < alpha < 1, optional (default 0.05) | the significance level from the Methods | the side each P falls on |
| `rows` | list (non-empty) | one object per row to check | each row is checked |
| `rows[].row` | non-empty string | the row's first cell as printed | finds the row (see below) |
| `rows[].test` | string | `fisher`, `chi2`, `chi2_yates`, `adjusted`, `paired`, or `other:<description>` | the test the P is recomputed with |
| `notes` | any | free text | not read |

`test` ignores case and reads a space or hyphen as `_`.

- `fisher` is Fisher's exact test, two-sided.
- `chi2` is Pearson's chi-square without continuity correction.
- `chi2_yates` is Pearson's chi-square with Yates' continuity correction.

These are the three families the script already computes. `adjusted` and `paired` are the
cases SKILL.md names as ones the counts cannot show.

These all exit 2 and name the field:

- any other key;
- a wrong type, such as a string or boolean `alpha`, or a number as a label;
- an empty `rows` list or an empty label;
- two entries with the same label, compared word for word;
- a test that is not on the list, or `other:` with no description;
- an `alpha` that is not strictly between 0 and 1;
- `NaN`, `Infinity` or `1e999`;
- an unreadable or deeply nested file.

## How each row is checked

1. **Finding the row.** The label must equal a table row's first cell word for word. Case,
   punctuation and markdown emphasis are ignored, so `diabetes` matches `**Diabetes**` but
   `Statin` does not match `Statin use`. Tables are read the same way the order-of-magnitude
   rule reads them. A header cell with `n =` is a group column, and a header cell `P` or
   `P value` is the P column.
2. **Groups.** Two group columns make a 2x2 table. With three or more, a Total column is
   dropped first: its header must say Total, Overall or All, and its n must equal the sum of
   the other columns' n (so the larger arm of a 2:1:1 trial is not taken for a total). Only a table with exactly two
   groups left is recomputed.
3. **Counts.** Each group cell must be an integer count, optionally followed by
   `(percent)`.
   - *Percentage printed.* The percentage must equal count / column n, allowing half a unit
     of its last printed place. If it does not, the row uses another denominator (missing
     data) and is not assessed.
   - *No percentage printed.* The count is read against the column's header n. A
     missing-data denominator cannot be seen on such a row, so check its n by hand.
4. **Recompute.** The P is recomputed from the row's own counts, using the declared test
   only.
5. **Reported P.** The reported P is read as the interval of its printed precision. `0.04`
   is [0.035, 0.045). `<0.001` is (0, 0.001). `0.05` is [0.045, 0.055), which straddles an
   alpha of 0.05, so it never fires.
6. **Crossing.** `P_ALPHA_CROSSING` fires only when the whole reported interval lies on one
   side of alpha and the recomputed P lies strictly on the other side. Below alpha means
   P < alpha.

## Verdicts

| Verdict | Severity | When |
|---|---|---|
| `P_ALPHA_CROSSING` | Major | the reported P's whole interval and the recomputed P lie on opposite sides of alpha |
| `P_NOT_ASSESSED` | Minor | see the list below |
| `UNLISTED_METHOD` | Minor | the test is `other:<description>` |
| `P_NOT_REPRODUCIBLE` | Major | unchanged: the order-of-magnitude rule, which runs whether or not `--tests` is given |

`P_NOT_ASSESSED` is given when any of these holds:

- the test is `adjusted`, `paired` or `other:`;
- no row has the label, or two or more rows do;
- the row has no readable P, or its counts are not integers (a continuous row, or `n/N`);
- a count exceeds its column n;
- a printed percentage is not count / n;
- the table compares three or more groups.

With `--tests`, `--strict` exits 1 on either Major. The text report adds a
`declared tests:` line, and the JSON adds a `declared_tests` key. A row that passes adds
nothing.

## Not read

- A P cell with a footnote mark (`0.04*`), with `≤` or `>`, or a P in prose.
- Counts written as `n/N`.
- Tables that are not pipe tables.
- A one-sided test, an exact mid-P, or a chi-square with more than one degree of freedom.
  Declare these as `other:`. This includes a multi-level categorical variable whose single P
  is printed on its first level's row: declaring that row `chi2` recomputes a 2x2 for one
  level and can give a Major.
- Whether the declared test was the right test for the data.
