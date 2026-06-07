# Analysis: synthetic BAD fixture (R) for the generated-code quality gate.
# Date: 2020-01-01

# absolute path literal + source read
df <- read.csv("/Users/researcher/data/cohort.csv")

# hand-typed tabular data instead of read.csv + subset
auc <- c(0.81, 0.83, 0.79, 0.88, 0.84, 0.77, 0.82, 0.86, 0.80, 0.85, 0.78, 0.87, 0.83, 0.81)

# randomness with no set.seed() -> non-reproducible
boot <- sample(df$auc, size = 1000, replace = TRUE)

browser()  # debugger left in

# writes back to the source path -> overwrites raw data
write.csv(df, "/Users/researcher/data/cohort.csv")
