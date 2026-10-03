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
| `entries[].anchor` | string, at least 4 Latin-letter or digit words | words of the revised sentence or table row label that hold the values, as they appear in the body |
| `entries[].values` | list (non-empty) | each a JSON number (`0.92`, `1234`), or a string: an inequality (`"<0.001"`, `"≤ .05"`), a range (`"0.88-0.95"`, `"0.88 to 0.95"`, `"-4.1 to -0.5"`, `"80.1%-89.2%"`) or a percentage (`"12.5%"`); write a negative with `-` or `−`, not `+` for a positive; no `P` prefix or e-notation in a string |
| `entries[].location` | string, optional | where it is (recorded, not checked) |
| `notes` | any | free text, not read |

Any other key, a wrong type, an empty list, a non-finite number, or a value string in another
form (for example `"1,234"`: write `1234`) exits 2 and names the field.

How a value is checked. The manuscript is cut into blocks: for a .docx, each paragraph (its soft
line breaks included, tracked changes read as accepted: inserted text in, deleted text out) and each table row (its cells joined, a multi-paragraph cell kept whole); for
.md/.txt, each blank-line-separated block, with every `|` table row a block of its own. The anchor
is found word by word (case, punctuation and markdown emphasis ignored) inside a block, and the
declared values must be among that block's numbers — before or after the anchor, on any wrapped
line of it. A number in another paragraph or another table row is not used, so anchor a table
value on its row label, not on the caption. The numbers are read with the body's formats folded:
mid-dot decimals (`0·92`), thousands grouped by a comma or by a plain, thin or non-breaking space
(`1,234`, `12 345`), decimal commas (`0,92`), and a leading-dot value (`P = .03`). Each reading is
tried and a value counts as present under any of them. A hyphen, Unicode minus or en dash directly
before a number is its sign unless a digit precedes it, so `–2.3` and `−4.1–−0.5` read as negatives
and the dash of `0.88-0.95` does not. A number equals the declared one numerically (`0.920` matches
`0.92`); a positive declared value also matches by magnitude; an inequality needs the same
comparator (`P less than 0.001` is not read as `<0.001`). If an anchor occurs in several blocks
(the Abstract and the Results), a value found in any of them passes — check repeated numbers by eye.

If the anchor is matched only approximately (a word damaged in extraction or reworded), a missing
value is reported as minor, never major.

| Verdict | Severity | When |
|---|---|---|
| `RESPONSE_VALUE_MISMATCH` | major | the anchor is found word for word but a declared value is not among the numbers of its paragraph or table row |
| `RESPONSE_VALUE_NOT_ASSESSED` | minor | the anchor is not found, or found only approximately; or the value is missing from text that has superscript digits, `x10^n` or e-notation, which this gate cannot read |

The gate checks numbers only. A flipped finding ("was significant" → "was not significant") is
not compared; read each changed sentence for that by eye.

Not read: text in .docx headers, footers, text boxes and content controls (an anchor there is
`RESPONSE_VALUE_NOT_ASSESSED`); European `1.234,5` and Swiss `1'234` thousands; a full-width `＜`.
A value written that way is reported missing — write the anchor on a plain body sentence.
