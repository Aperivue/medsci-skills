df <- df %>% mutate(
  mets_bp = as.integer(bl_he_sbp >= 130 | bl_he_dbp >= 85 |
                       bl_tx_hypertension_med == 1 | bl_hypertension == 1),
  mets_wc = as.integer((bl_sex == 1 & bl_he_wc >= 90) |
                       (bl_sex == 0 & bl_he_wc >= 80))
)
