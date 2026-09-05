# Challenge: an effect estimate whose CI spans an order of magnitude

A manuscript's Conclusions report **OR 24.0 (95% CI 3.0–240.0)** as a magnitude.
The interval spans **80-fold** — the data support a direction, not the point
estimate — and the model was fit on **18 events for 3 covariates** (EPV 6.0 < 10).
This is a synthetic counterexample: the expected findings are a wide-interval
warning and a low events-per-variable warning.

`check_effect_stability.py` recomputes both from the printed cells:
`UNSTABLE_EFFECT_ESTIMATE` when a headline OR/HR/RR has a CI upper/lower ratio > 10
with no co-located imprecision caveat, and `EPV_LOW` when events/covariates < 10.

`verify.sh` runs the detector on `fixture/effect_bad.md` (fires both) and
`fixture/effect_ok.md` (a tight CI plus the same wide CI labelled exploratory —
must stay silent), diffing stdout against `expected/` and asserting exit codes.
Synthetic fixtures only; network-free.
