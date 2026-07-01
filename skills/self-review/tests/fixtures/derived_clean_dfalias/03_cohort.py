import numpy as np

# primary cohort `v0`: metabolic-syndrome blood-pressure component
v0['mets_bp'] = np.where(
    (v0['bl_he_sbp'] >= 130) | (v0['bl_he_dbp'] >= 85) | (v0['bl_tx_htn_med'] == 1),
    1, 0,
)
