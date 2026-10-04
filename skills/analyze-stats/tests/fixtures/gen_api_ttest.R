# Synthetic fixture: R's t.test() defaults to Welch (var.equal = FALSE), so neither
# call is an API-default claim.
df <- read.csv("cohort.csv")
t.test(age ~ group, data = df)
t.test(age ~ group, data = df, var.equal = TRUE)
