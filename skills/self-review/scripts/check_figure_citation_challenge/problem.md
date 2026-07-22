# Challenge — figure-citation gate must read panel-suffixed citations

## The defect this fixes

Multi-panel figures are cited in the body only by panel — `(Figure 3a)`, `(Figure 3b)`
— never as a bare "Figure 3". The orphan gate's mention regex ended in
`(?P<num>\d+)\b`, and there is **no word boundary between "3" and "a"**, so "Figure 3a"
matched nothing. Figure 3 therefore looked uncited and `FIGURE_ORPHAN` fired — a false
positive on every manuscript that uses multi-panel figures.

The fix allows an optional single-letter panel suffix in the *citation* regex only; the
caption anchor (`Figure 3.` names the whole float) is unchanged, so the caption↔citation
correspondence the gate depends on is preserved.

## Fixtures

- **`panel_regression.md`** (regression / negative): Figure 1 is cited only as
  `(Figure 1a)` / `(Figure 1b)`, Figure 2 only as `Figure 2c`, the table is cited, and
  both images are embedded. Post-fix this is **clean (zero claims)**; pre-fix Figures 1
  and 2 both fired `FIGURE_ORPHAN`.
- **`real_orphan.md`** (positive): Figure 1 is cited (`Figure 1a`) but Figure 2 has a
  caption and is **never cited in any form** → `FIGURE_ORPHAN` for Figure 2 only. Proves
  the fix did not blind the gate to genuine orphans.

## Verify

`bash verify.sh` — deterministic, network-free. Asserts the panel-cited manuscript is
clean and the truly-uncited figure still fires.
