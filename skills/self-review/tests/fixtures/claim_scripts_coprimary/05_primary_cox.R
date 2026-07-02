# 05_primary_cox.R
model3 <- coxph(Surv(t, e) ~ x + covars)   # PRIMARY model
model4 <- coxph(Surv(t, e) ~ x2 + covars)  # CO-PRIMARY model (added at revision)
