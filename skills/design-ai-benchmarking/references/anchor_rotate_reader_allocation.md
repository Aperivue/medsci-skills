# Reader allocation under burden constraints — anchor-and-rotate (incomplete-block)

A reviewer panel that must rate many items often cannot have **every reader rate every
item**: a per-reader session cap (time/fatigue) bounds how many items one reader can score.
Forcing full overlap caps the *total* item pool at the per-reader cap, which throws away
coverage. This note gives a deterministic allocation that keeps per-reader burden bounded
while expanding total coverage, and still yields inter-rater reliability.

This complements the reliability plan (set ICC / weighted-kappa targets; report reliability
on planted control items separately). It does **not** compute agreement statistics — carry
the resulting rating records into `/analyze-stats` for ICC / kappa / agreement sample size.

## The design

A **balanced-incomplete-block** layout with two strata:

- **Anchor set** (size `A`): rated by **all** readers → carries the inter-rater ICC/kappa
  (and, if you plant calibration probes, the control-item reliability).
- **Rotating unique blocks**: the remaining `pool - A` items are split into per-reader
  blocks of size `cap - A`, distributed across readers so each unique item is seen by
  `m` raters on average. This grows the total pool **independently of the per-reader cap**.

### Parameters
- `cap` — max items one reader rates per session (the hard ceiling).
- `pool` — total **unique** items you want evaluated.
- `A` — anchor-set size (rated by all readers).
- `m` — target average raters per unique (non-anchor) item.

### Formulas
```
rot_budget        = cap - A                      # each reader's rotating (unique) slots; must be > 0
unique            = pool - A
R (readers)       = ceil(m * unique / rot_budget) # readers needed for ~m raters per unique item
reads_per_reader  = A + rot_budget  (= cap)
raters_per_unique = R * rot_budget / unique
anchor_reads      = R * A                          # reliability strength on the anchor set
```

### Reverse (the usually-binding question)
Given **R available readers** (expert raters are typically the scarce resource), the largest
unique pool you can evaluate at `m` raters/item is:
```
max_pool = A + (R * (cap - A)) // m
```
This is the real ceiling: with a small expert panel, total feature-scored coverage is small.
Curate the must-rate item set to fit `max_pool` rather than assuming the cap is per-study.

## Trade-off (report honestly)
- Anchor items get all `R` raters → strong, reportable ICC/kappa.
- Unique (non-anchor) items get only ~`m` raters → usable for **point estimates**, weaker
  per-item reliability. Report anchor-set reliability and unique-item coverage **separately**.
- The per-reader cap is **per session, not per study**: rotation decouples total coverage from
  the cap. The binding constraint is usually the **number of available expert readers**, not
  the item count.

## Reference implementation (stdlib only, deterministic)
```python
import math

def plan(cap, pool, anchor, m):
    """Anchor-and-rotate allocation. Returns readers needed + per-reader load, or None if infeasible."""
    rot = cap - anchor
    if rot <= 0:
        return None  # anchor >= cap: no room to rotate
    unique = pool - anchor
    R = max(m, math.ceil(m * unique / rot))
    return {
        "readers": R,
        "reads_per_reader": anchor + rot,           # == cap
        "raters_per_unique": (R * rot) / unique if unique else float("inf"),
        "anchor_reads": R * anchor,
        "within_cap": (anchor + rot) <= cap,
    }

def max_pool_for_readers(cap, anchor, m, R):
    """Reverse: largest unique pool for R available readers at m raters/item."""
    rot = cap - anchor
    return None if rot <= 0 else anchor + (R * rot) // m

# Example: cap=30 items/expert/session, anchor=20, target 2 raters/unique item.
# With only 4-8 expert readers, max feature-scored pool is ~40-70 items — curate to fit.
```

## When to use / cautions
- Use when a multi-reader study has a **large item pool** and a **bounded per-reader session**.
- Pre-specify `A`, `m`, the rotation seed, and which items are anchor vs rotating **before**
  rating (and pre-register if applicable) — post-hoc reassignment biases reliability.
- A two-pass study (fast screening pass for many readers + deep rubric pass for few experts)
  can use different `cap` / `A` / `m` per pass; the deep-rubric expert pass is usually the
  binding one.
- This allocates raters; it does not replace a power/sample-size calculation for the primary
  estimand — pair with `/calc-sample-size` and `/analyze-stats`.
