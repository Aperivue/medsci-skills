# RECORD Checklist

**REporting of studies Conducted using Observational Routinely-collected health Data**
Version: RECORD 2015 (13 items; a STROBE extension). The pharmacoepidemiology extension is **RECORD-PE** (Langan et al. *BMJ* 2018).
Source: Benchimol EI, Smeeth L, Guttmann A, et al. *PLoS Medicine* 2015;12(10):e1001885 (the RECORD statement). CC BY 4.0. https://www.record-statement.org/ · EQUATOR Network.

Apply when the manuscript is an **observational study conducted using routinely-collected health data** — administrative claims, electronic health records (EHR), disease/population registries, health-administrative or health-checkup databases, or linked versions of these — i.e. data **not collected for the purpose of the specific study**. RECORD extends the base **STROBE** items with reporting specific to secondary-use data: database identity, the codes/algorithms used to define the population and the variables, data linkage and its quality, and the limitations of analysing data collected for another purpose. For a drug safety/effectiveness study in such data, also apply **RECORD-PE**. For the design/validity review of the same study, pair with the RD1–RD8 domain probes in `peer-review` / `self-review` `references/domain-probes/record_routinely_collected_data.md`, and with the observational-confounding probes (`observational_confounding.md`).

## Checklist Items (13 items, extending STROBE)

### Title and Abstract (STROBE item 1)

| # | Item | Description |
|---|------|-------------|
| 1.1 | Data type | The type of data used should be specified in the title or abstract. When possible, the name(s) of the database(s) used should be stated. |
| 1.2 | Geography and timeframe | The geographic region and timeframe within which the study took place should be reported in the title or abstract. |
| 1.3 | Linkage | If linkage between databases was conducted for the study, this should be clearly stated in the title or abstract. |

### Methods — Setting / Participants (STROBE item 6)

| # | Item | Description |
|---|------|-------------|
| 6.1 | Population selection | The methods of study population selection (such as codes or algorithms used to identify subjects) should be listed in detail. If this is not possible, an explanation should be provided. |
| 6.2 | Validation of codes | Any validation studies of the codes or algorithms used to select the population should be referenced. If validation was conducted for this study and not published elsewhere, detailed methods and results should be provided. |
| 6.3 | Linkage diagram | If the study involved linkage of databases, consider use of a flow diagram or other graphical display to demonstrate the data linkage process, including the number of individuals with linked data at each stage. |

### Methods — Variables (STROBE item 7)

| # | Item | Description |
|---|------|-------------|
| 7.1 | Codes for variables | A complete list of codes and algorithms used to classify exposures, outcomes, confounders, and effect modifiers should be provided. If these cannot be reported, an explanation should be provided. |

### Methods — Data access and cleaning (STROBE item 12)

| # | Item | Description |
|---|------|-------------|
| 12.1 | Data access | Authors should describe the extent to which the investigators had access to the database population used to create the study population. |
| 12.2 | Data cleaning | Authors should provide information on the data cleaning methods used in the study. |
| 12.3 | Linkage methods | State whether the study included person-level, institutional-level, or other data linkage across two or more databases. The methods of linkage and methods of linkage quality evaluation should be provided. |

### Results — Participants (STROBE item 13)

| # | Item | Description |
|---|------|-------------|
| 13.1 | Selection of included persons | Describe in detail the selection of the persons included in the study (i.e. study population selection) including filtering based on data quality, data availability and linkage. The selection of included persons can be described in the text and/or by means of the study flow diagram. |

### Discussion — Limitations (STROBE item 19)

| # | Item | Description |
|---|------|-------------|
| 19.1 | Secondary-data limitations | Discuss the implications of using data that were not created or collected to answer the specific research question(s). Include discussion of misclassification bias, unmeasured confounding, missing data, and changing eligibility over time, as they pertain to the study being reported. |

### Other Information — Data access / cleaning (STROBE item 22)

| # | Item | Description |
|---|------|-------------|
| 22.1 | Supplemental access | Authors should provide information on how to access any supplemental information such as the study protocol, raw data, or programming code. |

---

## Notes for Assessors

- RECORD is an **extension of STROBE**; for the non-RECORD-specific items the base `STROBE.md` guidance also applies. Report both the base instrument and the extension when describing methods (do not cite RECORD as if it replaced STROBE).
- The **highest-yield** items are **6.1 / 7.1** (the actual code lists / phenotype algorithms used to define the population, exposures, outcomes, and confounders — the single most common omission; "we identified diabetes from the database" with no codes is non-compliant), **6.2** (whether those algorithms were *validated*, and where), **12.3 / 6.3** (linkage method and linkage-quality evaluation, with a person-flow at each linkage stage), **13.1** (a participant-selection flow that includes data-quality/availability/linkage filtering — not only clinical eligibility), and **19.1** (the limitations specific to secondary-use data: misclassification from codes, unmeasured confounding, informative missingness, and eligibility drift over time).
- For a **drug safety/effectiveness** study in routinely-collected data, also apply **RECORD-PE** (Langan et al. *BMJ* 2018;363:k3532), which adds items on exposure definition (drug codes, dose, duration, exposure windows), the comparator and new-user/active-comparator design, and immortal-time/protopathic bias.
- This checklist was authored as a faithful summary of the RECORD statement (Benchimol EI, et al. *PLoS Med* 2015;12(10):e1001885, **CC BY 4.0**) for item-by-item assessment; verify against the published statement and its explanation-and-elaboration document for full item wording. Verified 2026-06-29.
