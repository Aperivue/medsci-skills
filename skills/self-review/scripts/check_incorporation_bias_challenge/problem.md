# Challenge: the reference standard and the predictor are the same construct

A nodule study classifies nodules benign by **resolution / decrease / stability**
(all forms of *not growing*) and then reports **growth** as associated with
malignancy (OR 50.9). A resolved nodule cannot be malignant under that standard —
the growth–malignancy association is partly definitional (incorporation bias). Two
reviewers called it fatal; no gate fired.

`check_incorporation_bias.py` reads trajectory tokens from the reference-standard
DEFINING sentences and, if a trajectory-named predictor is reported as associated
with the outcome, emits `INCORPORATION_BIAS` (Major) — unless the overlap is
disclosed. `verify.sh` runs it on `fixture/incorp_bad.md` (fires) and
`fixture/incorp_ok.md` (a pathology + follow-up standard → silent), diffing stdout
against `expected/` and asserting exit codes. Synthetic fixtures only; network-free.
