# `figures/_figure_manifest.md` — format and field definitions

Load-on-demand companion to `/make-figures`. SKILL.md states that the manifest is
mandatory and who consumes it; this file is the literal format.

Read it when you are writing the manifest.

After generating all figures, create a structured manifest file at `figures/_figure_manifest.md`:

```markdown
# Figure Manifest
Generated: {YYYY-MM-DD}
Study type: {study type or "custom"}

| Figure | Path | Type | Tool | Critic | Rounds | Description |
|--------|------|------|------|--------|--------|-------------|
| Figure 1 | figures/fig1_stard_flow.svg | flow-diagram | D2 | yes | 2 | STARD participant flow diagram |
| Figure 2 | figures/fig2_roc.pdf | roc-curve | matplotlib | yes | 1 | ROC curves for Model A vs B |
| Figure 3 | figures/fig3_calibration.pdf | calibration | matplotlib | partial | 3 | Calibration plot; legend still crowded (see notes) |

## Critic notes
- Figure 3: after 3 rounds, legend placement remains crowded at the
  double-column width. Candidate remediations documented but not applied
  to avoid reducing data-point visibility.
```

**Manifest field definitions:**
- **Path**: Relative path from project root
- **Type**: One of: `flow-diagram`, `roc-curve`, `forest-plot`, `funnel-plot`, `calibration`, `km-curve`, `bland-altman`, `confusion-matrix`, `box-violin`, `bar-chart`, `heatmap`, `pipeline`, `visual-abstract`, `sroc-curve`, `other`
- **Tool**: Tool used to generate (`matplotlib`, `D2`, `python-pptx`, `seaborn`, etc.)
- **Critic**: `yes` (all rubric items PASS) / `partial` (some PARTIAL after max rounds) / `no` (never critiqued — avoid for submission figures) / `skip` (deliberately bypassed, e.g., panel figure assembled externally)
- **Rounds**: Number of Critic Loop rounds executed (0 if skipped)
- **Description**: One-line description suitable for figure legend context

A `## Critic notes` section at the bottom of the manifest records any
residual PARTIAL items and the rationale for accepting them.

This manifest is consumed by `/write-paper` Phase 2 (figure embedding) and Phase 7 (DOCX build). It **MUST** exist after figure generation completes. Verify the file is non-empty before finishing.
