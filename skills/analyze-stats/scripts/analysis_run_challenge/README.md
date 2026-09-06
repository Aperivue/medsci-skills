# Analysis execution record challenge

Run `bash verify.sh` from this directory. Requires Python 3.10+, numpy, pandas,
SciPy, scikit-learn and matplotlib; no network or private data is used.

The bundled demo creates original synthetic observations in a temporary project.
The normal control checks exact confusion counts, two matching calculations and
a current byte audit. The defect control adds one synthetic input row: two audits
must report drift without rewriting the old record. The temporary project is removed.
The complete regression suite under `../../tests/test_analysis_run.py` additionally
covers units, denominators, undefined metrics, rounded-input refusal and output/code
changes. These controls test software behavior, not clinical validity.
