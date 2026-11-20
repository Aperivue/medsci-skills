# Exemplar — immortal-time bias from misaligned time zero

**Finding class:** exposure is assigned using future treatment information, but follow-up
starts earlier; survival time before treatment is incorrectly credited to the exposed group.
**Typical severity:** **Major #1** when the headline protective effect depends on this
misclassified person-time; **Minor** when exposure is already modelled time-varying and
only reporting of time zero or the grace window is unclear.

## What the reviewer noticed

In this synthetic retrospective registry cohort, Methods (Exposure definition) defines
users as patients filling at least one prescription at any time during follow-up, and
non-users as those with no fill. Methods (Follow-up) starts everyone's mortality follow-up
at diagnosis. Table [X] treats ever-use as a fixed exposure; Figure [Y] shows survival by
that same label. The Abstract interprets the lower mortality among users as protection.
To become a user, a patient must survive from diagnosis to the first fill, yet that
pre-fill time is counted as exposed. Deaths before a possible first fill fall among
non-users. All study details and table/figure labels here are invented placeholders.

## Weak phrasing (avoid)

> There is immortal-time bias. Please adjust for it and discuss the limitation.

(No anchor or explanation of the misclassified interval; adjustment is not a specific fix.)

## Strong phrasing (model this)

> Methods (Exposure definition and Follow-up) assigns ever-use using future fills while
> starting follow-up at diagnosis. In Table [X] and Figure [Y], this appears to credit
> users with survival time before their first prescription. Because patients must survive
> that interval to enter the user group, the Abstract's protective interpretation could
> reflect the exposure definition rather than a treatment effect.
>
> I'd suggest stating time zero for each group, when eligibility is assessed, how exposure
> is assigned, and where person-time and deaths before the first fill enter the analysis.
> It would help to reanalyse with a design appropriate to the intended question. One option
> is time-varying exposure, counting time before the first fill as unexposed and updating
> exposure thereafter under stated rules. This corrects the time allocation but does not
> by itself resolve confounding by indication or time-varying confounding.
>
> Alternatively, a landmark analysis at a stated, clinically justified [x]-month landmark
> could classify exposure using only information available by that point and start both
> groups' follow-up there. It would help to report who is excluded and acknowledge that
> this conditions on survival to the landmark, omits early deaths, and changes the question
> to one about landmark survivors. For a target-trial emulation of initiation within a
> grace period, I'd suggest aligning eligibility, strategy assignment, and follow-up at
> time zero and using clone-censor-weight, with the grace window, artificial-censoring
> rules, weighting models, and assumptions stated, as in `target_trial_emulation.md`.
>
> I'd also suggest sensitivity analyses with justified alternative landmarks or grace
> windows, reporting estimates with uncertainty and any population or estimand changes.
> If prescription timing cannot be recovered sufficiently to repair the allocation, I'd
> suggest withdrawing the protective-effect claim in the Abstract and Discussion and
> presenting the comparison as descriptive, explicitly subject to survivor selection.
> A limitation paragraph alone would not make the current estimate a treatment effect.

## Severity calibration

This is **Major #1** when misclassified person-time underpins the headline protection:
the analysis needs repair, not just clearer wording. An admission that immortal time was
not assessed does not downgrade it; apply S1's self-confession escalation in
`survival_prognostic.md`. It is **Minor** when exposure is already correctly time-varying
and only the account of time zero or the grace window needs clarification.

## What this is not

Prevalent-user bias concerns selecting existing treatment survivors at entry; confounding
by indication concerns prognostic reasons for treatment choice; reverse causation /
protopathic bias concerns early disease prompting treatment. These can coexist, but none
is the specific misallocation of pre-fill survival time here. `comparator_adequacy.md`
concerns whether the comparison establishes added value; `selective_outcome_reporting.md`
concerns undisclosed outcome changes. Neither substitutes for checking the exposure clock.

## Related checks

RD7 in `record_routinely_collected_data.md`; S1 time origin & survivorship and self-confession
escalation in `survival_prognostic.md`; O3's immortal-time item in
`observational_confounding.md`; `/design-study` `target_trial_emulation.md` (time zero and
grace period + clone-censor-weight); `/check-reporting` `TARGET.md` items 6d/7d for an
emulation, and `RECORD.md` with its RECORD-PE guidance for drug studies.
