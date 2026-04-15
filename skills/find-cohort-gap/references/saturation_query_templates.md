# Literature Saturation Query Templates

## Purpose

These templates help construct PubMed queries for the Phase 3 saturation scan.
Adapt the bracketed terms to the specific topic.

---

## Basic Saturation Query

```
([exposure MeSH] OR [exposure free text]) AND ([outcome MeSH] OR [outcome free text])
AND (cohort OR longitudinal OR prospective OR "follow-up")
```

**Filters:** English, Humans, last 20 years (to capture the full landscape)

## Longitudinal-Specific Query

To check if anyone has used serial/repeated measurements for this topic:

```
([exposure] OR [exposure synonym]) AND ([outcome] OR [outcome synonym])
AND ("repeated measure*" OR "serial" OR "trajectory" OR "longitudinal change"
OR "time-varying" OR "growth curve" OR "latent class trajectory")
```

## Meta-Analysis Check Query

To verify if a meta-analysis already exists:

```
([exposure] OR [exposure synonym]) AND ([outcome] OR [outcome synonym])
AND ("meta-analysis"[Publication Type] OR "systematic review"[Publication Type])
```

If a meta-analysis exists → Red grade (avoid unless doing NMA).

## Population-Specific Queries

### Korean/Asian population filter
```
AND (Korea* OR Korean OR "Republic of Korea" OR Asia* OR Japan* OR China OR Chinese
OR Taiwan*)
```

### Health checkup / screening population filter
```
AND ("health checkup" OR "health screening" OR "health examination" OR "medical checkup"
OR "periodic health exam*" OR "annual exam*")
```

### Large cohort filter (to find comparator studies)
```
AND ("national health insurance" OR "claims data" OR "administrative data"
OR "population-based" OR "nationwide" OR "registry")
```

---

## Saturation Grading Protocol

After running the basic saturation query:

### Step 1: Count total results
- 0-2: Blue Ocean
- 3-10: Possible Green Field (proceed to Step 2)
- 10-30: Possible Yellow (proceed to Step 2)
- 30+: Likely Red (check for MA in Step 3)

### Step 2: Check longitudinal gap
Run the longitudinal-specific query.
- 0 results with serial/trajectory data → upgrade one grade
- 1-2 results → maintain current grade
- 3+ results → no upgrade

### Step 3: Check meta-analysis existence
Run the MA check query.
- MA exists and is comprehensive → Red (firm)
- MA exists but outdated (>5 years) or limited scope → Yellow (update MA possible)
- No MA → maintain current grade

### Step 4: Final grade assignment

| Base Count | Longitudinal Papers | MA Exists? | Final Grade |
|------------|-------------------|------------|-------------|
| 0-2 | 0 | No | Blue Ocean |
| 3-10 | 0 | No | **Green Field** |
| 3-10 | 1-2 | No | Yellow |
| 10-30 | 0 | No | Green Field (upgraded) |
| 10-30 | 1-2 | No | Yellow |
| 10-30 | 3+ | No | Yellow |
| 30+ | Any | No | Yellow (borderline Red) |
| Any | Any | Yes (recent) | Red |
| Any | Any | Yes (outdated) | Yellow |

---

## Example: Fatty Liver and Cardiovascular Mortality

### Basic query
```
("fatty liver" OR "hepatic steatosis" OR NAFLD OR MASLD) AND
("cardiovascular mortality" OR "cardiac death" OR "MACE")
AND (cohort OR longitudinal OR prospective)
```
Result: ~45 papers → base grade Red

### Longitudinal check
```
("fatty liver" OR "hepatic steatosis") AND ("cardiovascular mortality")
AND ("trajectory" OR "serial" OR "repeated measure*" OR "longitudinal change")
```
Result: 2 papers → no upgrade

### MA check
```
("fatty liver" OR NAFLD) AND ("cardiovascular mortality")
AND ("meta-analysis"[PT] OR "systematic review"[PT])
```
Result: 3 MAs → confirmed Red

**Conclusion:** Avoid this topic unless using truly unique data angle.

---

## Tips for Effective Saturation Scanning

1. **Start broad, then narrow.** If the broad query returns >30, add population or
   design filters to find the exact niche.

2. **Check the "last 3 years" subset.** A topic with 20 total papers but 15 in the
   last 3 years is trending (good for timeliness, bad for novelty).

3. **Read the most recent review article.** It maps the field faster than scanning
   individual papers. Look for "future research directions" sections.

4. **Check for registered protocols.** Search PROSPERO or ClinicalTrials.gov for
   ongoing studies that haven't published yet — these are invisible competitors.

5. **Use Semantic Scholar** for citation network analysis. A paper with 200+ citations
   on this exact topic means the field is well-established.
