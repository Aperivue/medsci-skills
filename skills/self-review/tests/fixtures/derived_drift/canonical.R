# canonical MetS component definitions (benchmark script)
df <- df %>% mutate(
  mets_bp = as.integer(bl_he_sbp >= 130 | bl_he_dbp >= 85 |
                       bl_tx_hypertension_med == 1 | bl_hypertension == 1),
  mets_fg = as.integer(bl_b_glu >= 100 | bl_tx_diabetes_med == 1 |
                       bl_diabetes == 1)
)
