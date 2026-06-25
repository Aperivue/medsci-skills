# same definitions: clauses reordered, tighter whitespace, extra outer parens,
# and the &-group operands swapped — all semantically identical.
df2 <- df2 %>% mutate(
  mets_bp = as.integer((bl_hypertension==1 | bl_tx_hypertension_med==1 | bl_he_dbp>=85 | bl_he_sbp>=130)),
  mets_wc = as.integer((bl_he_wc >= 80 & bl_sex == 0) | (bl_he_wc >= 90 & bl_sex == 1))
)
