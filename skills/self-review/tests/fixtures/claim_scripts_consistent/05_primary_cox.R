# 05_primary_cox.R
model3 <- coxph(Surv(t, e) ~ x + covars)   # the single primary model
model5 <- coxph(Surv(t, e) ~ x + covars2)  # secondary sensitivity analysis
