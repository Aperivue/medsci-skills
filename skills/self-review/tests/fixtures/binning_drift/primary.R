# primary stratification (Table 2)
df <- df %>% mutate(
  age_band = cut(bl_age, breaks = c(-Inf, 45, 50, 60, Inf),
                 labels = c("<45", "45-49", "50-59", ">=60"), right = FALSE)
)
