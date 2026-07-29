# Cross-reference QC — symptom triage

`check_xref.py --strict` writes a 3-way matrix to `qc/xref_audit.json` that
classifies every Table/Figure label across (a) in-text citations, (b) body
captions in `## Tables` / `## Figures` / `## Figure Legends` /
`## Supplementary {Tables,Figures}`, and (c) caption paragraphs in the
rendered DOCX (via `python-docx`).

| Status | Meaning | Severity | Fix |
|---|---|---|---|
| `OK` | cited + body caption + DOCX caption all present, caption text agrees (Jaccard ≥ 0.40) | — | none |
| `MISSING_DOCX` | cited but no caption with that label in the rendered DOCX | **P0 blocker** | drop the citation if the figure/table was retired, or re-add it to the build pipeline and rebuild DOCX |
| `MISSING_BODY` | cited but no caption definition in the markdown body sections | **P0 blocker** | add the caption under `## Tables` / `## Figures` in `manuscript.md`, then re-render — **but if you ran without `--docx`, read the note below first** |
| `MISMATCH` | label exists in both body and DOCX but caption text disagrees (Jaccard < 0.40) | **P0 blocker** | reconcile body vs build script — body caption is the SSOT, update the build pipeline to match, never the reverse |
| `UNCITED` | caption defined or rendered but never cited in main text | warn | either delete the caption or add a citation; never ship UNCITED on a clean run |
| `NOT_CITED_NO_BODY` | label appears only in DOCX (rare; legacy artifact) | warn | clean up the build pipeline; the DOCX is leaking captions from a previous draft |

### `MISSING_BODY` names two different situations

The row above describes the one people mean by it — **build SSOT drift**: the float is rendered in
the DOCX, but nothing in `manuscript.md` defines its caption, so the build pipeline is the only
place that knows the text. That is a P0 and stays one.

The same verdict is also returned when **no `--docx` was supplied at all**. Then there is no
rendered artifact to have drifted *from*, and the run genuinely cannot distinguish

- a caption you forgot to write, from
- a float that lives in a **separate supplement file** this invocation never saw — the normal
  packaging for radiology and most medical journals.

`--allow-separate-attachments` does not help here, and that surprises people: the flag downgrades
`MISSING_DOCX`, and a float only *becomes* `MISSING_DOCX` once a `--docx` has shown it to be absent
from the rendered output. Without `--docx`, `_classify` never reaches that branch.

**So: pass `--docx <rendered.docx>` to decide it.** The run now says so itself, and names the labels
it could not decide, rather than printing `SUBMISSION BLOCKED` on a correctly packaged submission
with no way forward. (A gate that is red on correct work is a gate the operator learns to skip,
which costs more than the check is worth.)

## Why this exists

Internal consistency in `/self-review` Phase 2.5 does NOT catch
cross-reference defects because both the body prose and the build script
can echo their own divergent SSOTs cleanly — each looks self-consistent in
isolation. Precedent: an STROBE cohort manuscript revision — body cited
"Supplementary Table S4 (a sensitivity-analysis)" but the rendered DOCX S4 was
a diagnostics table; S1, S6, S7 mismatched and S8, S9 were cited but absent
from the DOCX entirely. The 3-way matrix between citations, body captions,
and DOCX captions is the only place those drifts surface.

## Pipeline placement

Always run **after** the DOCX build (Workflow A step 2 or after
`render_pandoc.sh`) and **before** the final submission gate. If
`python-docx` is unavailable, the script falls back to a body-only audit
(citations vs body captions) with a stderr warning; install with
`pip install python-docx` for full coverage.
