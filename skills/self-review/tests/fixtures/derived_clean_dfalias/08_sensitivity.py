import numpy as np

# parallel sensitivity cohort `lenient_cohort`: IDENTICAL derivation rule, only the
# dataframe-receiver object differs (by design — a second cohort, not a drift).
lenient_cohort['mets_bp'] = np.where(
    (lenient_cohort['bl_he_sbp'] >= 130) | (lenient_cohort['bl_he_dbp'] >= 85) | (lenient_cohort['bl_tx_htn_med'] == 1),
    1, 0,
)
