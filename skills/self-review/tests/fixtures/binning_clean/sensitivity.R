sub$age_band <- cut(sub$bl_age, breaks = c(-Inf, 45, 50, 60, Inf),
                    labels = c("<45","45-49","50-59",">=60"), right = FALSE)
