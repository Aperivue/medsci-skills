# Critic Rubric — Data Plots

Apply this rubric when the generated figure is a data visualization (not a
flow diagram): ROC, forest, KM, calibration, Bland-Altman, confusion matrix,
box/violin, bar, heatmap. The Claude session should Read the rendered PNG
plus any available exemplars from `references/exemplar_diagrams/{type}/`,
then mark each item below as **PASS / PARTIAL / FAIL** with a one-line
justification.

After scoring, produce a list of concrete matplotlib/seaborn edits that
would resolve every FAIL or PARTIAL item. Return the scored rubric + edit
list to the user.

---

## A. Axes, labels, units

1. **X-axis label** present with units where applicable.
2. **Y-axis label** present with units where applicable.
3. **Axis tick labels** readable (no overlap, sensible density, no scientific
   notation where plain numbers fit).
4. **Axis limits** sensible — no wasted whitespace (e.g., ROC axes should
   be 0–1 exactly, forest plot x-axis should frame all CIs without
   clipping).
5. **Tick direction inward**, tick marks minor/major where needed. No
   chart-spine clutter.

## B. Legend / caption

6. **Legend present** when ≥2 series are shown; placed where it does not
   obscure data.
7. **Legend labels** are descriptive (not "Series 1"); include N or group
   size where relevant.
8. **Legend ordering** matches visual order of series (top to bottom).
9. **Caption-ready** — plot does not rely on external notes the caption
   cannot repeat concisely.

## C. Figure-type–specific requirements

### ROC curve
- AUC and 95% CI displayed on plot or in legend
- Diagonal reference line (chance) shown
- Sensitivity on Y-axis (0–1), 1−Specificity on X-axis (0–1)
- Multiple models distinguished by color AND line style (grayscale-safe)

### Forest plot
- Effect estimates aligned to a vertical reference line (null effect)
- CIs drawn as horizontal bars with appropriate caps
- Box size proportional to study weight
- Diamond summary at the bottom; pooled estimate and CI printed
- Left column: study labels; right column: effect (95% CI) numeric
- Heterogeneity statistics (I², τ², Q p-value) reported in caption or plot

### KM curve
- Number at risk table below the plot
- Median survival and its CI shown or reported in caption
- Log-rank p-value or Cox HR reported
- Curves distinguishable in grayscale (line style + color)
- Censoring marks visible

### Calibration plot
- Ideal diagonal line (y=x) shown
- Binned observed vs. predicted points
- Hosmer-Lemeshow p-value or Brier score reported
- Histogram of predicted probabilities overlaid or beside the plot

### Bland-Altman
- Mean difference line
- ±1.96 SD limits of agreement
- LoA values printed
- Scatter points not clipped at plot edges

### Confusion matrix
- Cells annotated with counts AND percentages
- Axis labels "Predicted" / "Actual" (or "Reference")
- Diagonal emphasized (darker color or heavier stroke) if useful

## D. Typography and accessibility

10. **Font size ≥ 8pt at final dimensions** (most journals require 6–7pt min
    for axis numerics, 8pt for labels). At 300 DPI in a 3.5×3.5 inch
    figure, this corresponds to roughly ≥25 px — use `critic_figure.py`
    OCR min-height flag as a proxy.
11. **Single font family** throughout (typically sans-serif). No mixed
    Arial/Helvetica/Times.
12. **Colors from Wong palette** or equivalent colorblind-safe scheme.
    `critic_figure.py` flags out-of-palette fractions >15%.
13. **Grayscale-safe** — every series is distinguishable in grayscale
    conversion, either through line style, marker shape, or luminosity
    differences.

## E. Publication readiness

14. **Vector PDF produced** in addition to PNG.
15. **Dimensions match journal spec** — width per figure_specs.md for the
    target journal (single column ≈3.5 in, double ≈7.0 in).
16. **DPI ≥ 300 (halftone) or ≥ 600 (line art)**.
17. **No duplicate data encoding** (e.g., color + shape + size all mapped
    to the same variable adds clutter without information).
18. **Statistical annotations** — where significance markers are used
    (`*`, `**`, `***`), the caption defines thresholds. Prefer actual
    p-values for publication.

## F. Exemplar comparison (if exemplars exist for this type)

19. **Visual density** comparable to exemplars — not significantly sparser
    or more cluttered.
20. **Annotation style** — placement of summary statistics, N labels,
    p-values consistent with exemplars.

---

## Scoring output format

```
## Critic report (data plot, round T)

| Item | Score | Note |
|------|-------|------|
| A.1 X-axis label | PASS | — |
| A.2 Y-axis label | FAIL | Missing units ("Sensitivity" should be unitless OK; but "Time" needs "(months)") |
| ...

### Required edits before next render
1. Add unit "(months)" to Y-axis label.
2. Increase legend font from 6pt to 8pt.
3. ...

### Overall verdict
[ ] PASS — ready for manuscript
[ ] REFINE — items above must be fixed before next round
```

Record `critic_pass: yes | partial | no` and `refine_rounds: N` in the
`_figure_manifest.md` for this figure after the final round.
