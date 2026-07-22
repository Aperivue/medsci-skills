# Challenge: an effect estimate whose CI spans an order of magnitude

A manuscript's Conclusions report **OR 50.9 (95% CI 5.8–443.6)** as a magnitude.
The interval spans **76-fold** — the data support a direction, not the point
estimate — and the model was fit on **19 events for 2 covariates** (EPV 9.5 < 10).
Two independent reviewers and the editor flagged exactly these numbers, and the
paper was rejected.

`check_effect_stability.py` recomputes both from the printed cells:
`UNSTABLE_EFFECT_ESTIMATE` when a headline OR/HR/RR has a CI upper/lower ratio > 10
with no co-located imprecision caveat, and `EPV_LOW` when events/covariates < 10.

`verify.sh` runs the detector on `fixture/effect_bad.md` (fires both) and
`fixture/effect_ok.md` (a tight CI plus the same wide CI labelled exploratory —
must stay silent), diffing stdout against `expected/` and asserting exit codes.
Synthetic fixtures only; network-free.
