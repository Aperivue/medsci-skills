# Analysis: synthetic BAD fixture (R) -- set.seed(NULL) re-initialises the RNG
# from entropy, so the bootstrap below is not reproducible.
# Date: 2026-01-01

df <- read.csv("cohort.csv")
set.seed(NULL)
boot <- sample(df$auc, size = 1000, replace = TRUE)
write.csv(data.frame(mean_auc = mean(boot)), "boot_summary.csv")
