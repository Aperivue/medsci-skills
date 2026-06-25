# CAC>10 sensitivity — DIFFERENT cut definition (bug)
df <- df %>% mutate(
  age_band = cut(bl_age, breaks = c(-Inf, 44, 49, 59, Inf),
                 labels = c("<45", "45-49", "50-59", ">=60"), right = TRUE)
)
