# revision_values.json — declared numbers for the response-claim gate (revise)

`check_response_claims.py --values revision_values.json` checks that each number the revision
changed is actually in the revised manuscript, next to the sentence it belongs to. It is the
revision-time numerical audit table (SKILL.md, Step 4) written as data. The letter's own quotes
are still graded as before; this adds a check the quote matcher cannot make, because a quote
that differs from the body by one number reads like extraction debris.

Start from `templates/revision_values.json`.

| Field | Type | Meaning |
|---|---|---|
| `entries` | list (non-empty) | one object per changed number or group of numbers |
| `entries[].id` | string | the response item, e.g. `R1-3` |
| `entries[].anchor` | string, at least 4 words | words of the revised sentence that hold the values, as they appear in the body |
| `entries[].values` | list (non-empty) | each a JSON number (`0.92`, `1234`), or a string: an inequality (`"<0.001"`, `"≤ .05"`), a range (`"0.88-0.95"`, `"0.88 to 0.95"`) or a percentage (`"12.5%"`) |
| `entries[].location` | string, optional | where it is (recorded, not checked) |
| `notes` | any | free text, not read |

Any other key, a wrong type, an empty list, a non-finite number, or a value string in another
form (for example `"1,234"`: write `1234`) exits 2 and names the field.

How a value is checked. The anchor is located paragraph by paragraph with the same
extraction-tolerant matcher the quote check uses. The numbers of the matching paragraph(s) are
read with the body's formats folded: mid-dot decimals (`0·92`), thin or non-breaking-space
thousands (`12 345`), comma thousands (`1,234`), decimal commas (`0,92`), a Unicode minus, and a
leading-dot value (`P = .03`). Each reading is tried and a value counts as present under any of
them. A number equals the declared one numerically (`0.920` matches `0.92`); a positive declared
value also matches a number written after a range dash; an inequality needs the same comparator.

| Verdict | Severity | When |
|---|---|---|
| `RESPONSE_VALUE_MISMATCH` | major | the anchor is found but a declared value is not among that paragraph's numbers |
| `RESPONSE_VALUE_NOT_ASSESSED` | minor | the anchor is not found; or the value is missing from a paragraph that has superscript digits or `x10^n` notation, which this gate cannot read |

The gate checks numbers only. A flipped finding ("was significant" → "was not significant") is
not compared; read each changed sentence for that by eye.
