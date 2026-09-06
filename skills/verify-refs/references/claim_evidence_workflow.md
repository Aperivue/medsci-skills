# Reviewing a sentence against its cited source

Use the existing claim-fidelity report to connect a manuscript sentence to the
source actually inspected. This workflow does not fetch papers, invent source
excerpts, or turn word/number matches into semantic support. It adds no detector
or submission-blocking verdict; `--strict` retains the existing probe behavior.

## Create the review surface

Run the command in the skill's “Sentence-level source evidence table” section.
`--retrieval-report` consumes the existing `fetch_oa.py` report, including each
DOI's PDF filename, hash and advisory identity assessment. PDFs are looked up next
to that report unless `--pdf-dir` selects another directory. The converted texts
can be in a different `--fulltext-dir`.

`--reference-audit` reads existing `records[]` from the metadata audit. Its recorded
OK status has no input hash binding in that artifact and is shown as context only.
It cannot establish PDF identity, a current bibliography audit, or source support.
Missing/ambiguous links remain visible. No network or bibliography writes occur.

`qc/claim_fidelity.json` schema 2 retains the existing `findings`, probe counts,
and source-resolution fields, and adds:

| Field | Meaning |
|---|---|
| `evidence_rows[]` | One row per recognized prose sentence/citation pair, including citations outside the three probes. Duplicate occurrences have distinct IDs. |
| `manuscript` | Exact text, character offsets and line coordinates in the `read_text` representation. DOCX coordinates refer to extracted paragraph/table text, not rendered pages. |
| `source` | Selected converted text and hash, actual PDF hash, report hash, advisory identity and hash status. Filename/DOI resolution is not identity verification. |
| `reference_audit` | Linked metadata status with its binding limitation. |
| `automatic_finding_indices` | Same-sentence or quoted-span links to existing `findings`; these do not assign the manual assessment. |
| `assessment` | Editable, attributed review record described below. Initially `not_assessed`. |
| `binding` / `binding_sha256` | Current manuscript, bibliography, mapping, report and source hashes. |
| `verdict` / `review_state` | Effective recorded outcome and whether the assessment is current, incomplete or stale. Never a machine-certified fact. |
| `orphaned_evidence_reviews` | Preserved prior rows that no longer match a current sentence/citation pair. Excluded from current assessment counts. |

The old `sources_resolved` and `claims_checked` fields still describe probe
execution; use `evidence_counts` for the broader sentence/citation inventory.
Neither count covers uncited statements, Markdown tables, blockquotes, code or
the bibliography. Citation recognition is syntactic and can miss unsupported
formats. A complete inventory is not a complete scientific review.

## Enter an assessment after reading the source

Edit only the row's `assessment` in the JSON. Supply:

- `verdict`: `supported`, `contradicted`, `unresolved` or `not_assessed`.
- `assessor`, `assessed_at`, `method`, `rationale`: who made the judgment, when,
  how it was made (including AI assistance), and why. These are attributed
  declarations, not authenticated human signatures or approval.
- `source_scope`: `full_text`, `abstract_only`, `partial` or `unknown`;
  `identity_checked`: whether the assessor actually checked the paper identity.
- `source_pages`: a nonempty list of one-based PDF page indices, not printed
  journal page numbers; `source_excerpt`: the relevant text actually inspected.
- `claim` and `source`: compare `metric`, `unit`, `denominator`, `population`,
  and `direction` separately. Use an explicit `not applicable` explanation for a
  qualitative field; an empty field is not a completed comparison.

For example, a synthetic software experiment can report the same latency
percentage for a subgroup that the manuscript attributes to the whole sample.
The equal number does not support the manuscript's population claim. A direction
reversal also needs a source-level judgment despite matching terms and numbers.

Do not fill pages or excerpts from memory. The tool does not check that an
excerpt appears on the declared PDF page, authenticate an assessor, or adjudicate
the meaning of a comparison. Complete fields allow a **recorded judgment**, not
an independent source verification. Check the PDF itself, including tables,
subgroups and qualification of the claim, before using a recorded conclusion.

The extraction tool does not currently bind the converted text to the PDF with a
conversion manifest. The report explicitly marks that derivation as unrecorded;
matching filenames are insufficient. Source-text and PDF hashes identify the
files reviewed, not proof that one was faithfully extracted from the other.

## Carry reviews forward without losing their history

Rerun the original command with `--reviewed-report qc/claim_fidelity.json` and the
same `--out`. The old JSON is read first; findings and the Markdown view are
regenerated. `--evidence-table` requires `--out`, and output aliases of selected
source inputs are rejected. Input files are not edited.

The assessment's `binding_sha256` stays pinned to its original inputs. Changes to
the manuscript, bibliography, source text, PDF, input reports or reference map
make the old conclusion `unresolved` with `stale_inputs`. Repeating the command
does not make it current again. Inspect the changed source/context, update the
assessment, and only then copy the row's current `binding_sha256` into
`assessment.binding_sha256`. Changed sentence IDs retain the old row under
`orphaned_evidence_reviews` for explicit reconciliation; they are not silently
discarded or transferred to a different sentence.

A supported/contradicted outcome additionally requires a source text, a PDF
matching the retrieval hash, no reported identity conflict, full-text inspection,
pages, an excerpt and a populated comparison. Missing PDFs, legacy reports
without hashes, DOI-unresolved sources, abstract-only evidence, and incomplete
reviews remain unresolved. A consistent retrieval identity is advisory, not
enough by itself. Resolve conflicting source identity before recording support;
this workflow does not override the retrieval assessment automatically.

The Markdown file is a derived view. Its source excerpts and project context may
be private; do not publish generated reports without reviewing their contents.
