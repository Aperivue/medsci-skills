---
name: ma-scout
description: Use when looking for a meta-analysis topic before any protocol exists. Starts from a professor's publication profile or from a clinical question, finds gaps, assesses feasibility and returns a ranked topic list. Running the review itself is /meta-analysis.
model: opus
metadata:
  triggers: "ma-scout, MA 주제 찾기, professor MA, 메타분석 주제, MA gap, topic-first MA, 트렌드 MA, meta-analysis topic, 교수님 분석, 연구 분석"
---

# MA Scout Skill

This skill handles the **pre-protocol phase** of a meta-analysis — from idea to ranked topic list.
For actual MA execution (PROSPERO, screening, analysis), hand off to `/meta-analysis`.

## Mode Selection

| Signal | Mode |
|--------|------|
| Professor name or profile URL provided | **A: Professor-first** |
| Clinical question, keyword, trend, or "find me a topic" | **B: Topic-first** |
| Both supplied (e.g., "this topic with this professor") | **A** (topic as filter) |

If ambiguous, ask the user whether to search by professor (supervisor-first) or by
topic (question-first).

## Inputs

### Mode A: Professor-first
- Professor name (native-language + English); profile URL (ScholarWorks, SKKU Faculty, Google
  Scholar, ORCID); PubMed author link (preferably with cauthor_id for disambiguation); known
  specialty; affiliation history (e.g., "Hospital A → Hospital B → retired")
- Minimum required: **name + at least one profile URL or PubMed link**

### Mode B: Topic-first
- Clinical question or keyword; radiology subspecialty scope; MA type preference (DTA,
  prognostic, intervention — optional); desired role (solo first author / co-first /
  supervisor-matched)
- Minimum required: **clinical question or keyword**

## Workflow

> **Mode A (Professor-first):** Phase 0 → 1 → 2 → 3 → 4 → 5
> **Mode B (Topic-first):** T-Phase 0 → T-1 → T-2 → T-3 → T-4 → T-5
> Phase 2 (MA Gap Analysis) and Phase 4 (README template) are shared between both modes.

Query PubMed with `/search-lit`'s E-utilities scripts, not WebFetch — they are faster and return
structured JSON/XML: `${CLAUDE_SKILL_DIR}/../search-lit/references/pubmed_eutils.sh` and
`parse_pubmed.py` beside it. Rate limit: 350 ms between calls (100 ms with `NCBI_API_KEY`).

# MODE A: PROFESSOR-FIRST WORKFLOW

### Phase 0: Disambiguation & Context Confirmation

Resolve the author's identity BEFORE any PubMed search:

1. **Resolve the full English name first.** If a cauthor_id is provided, fetch that PMID page to
   get the full name + affiliation. NEVER start with an initials-only search, because common
   Korean/Asian initials (e.g., "Lee KS") return 300+ papers with massive contamination. The first
   search must be `"[Full Name]"[Author]`.
2. **Confirm the affiliation chain with the user.** Ask whether `{detected affiliation}` matches
   the professor's history (professors move institutions — do not assume), and ask the user's
   relationship to the professor so topic proposals can be tuned. Skip only if the user already
   gave an explicit affiliation history.
3. **Profile URL fallback chain:**
   - 1st: PubMed full-name search (always works)
   - 2nd: Google Scholar profile (WebSearch `"[Full Name]" radiology scholar`)
   - 3rd: ResearchGate profile (WebSearch `"[Full Name]" researchgate radiology`)
   - 4th: ScholarWorks / SKKU / university faculty page (if URL provided)
   - Last: Scopus/ScienceDirect — returns 403 or a login redirect; never rely on it

### Phase 1: Profile Exploration (E-utilities API)

**Goal:** Identify the professor's 5-6 distinct research pillars.

**Step 1 — Total publication count + PMID list:**
```bash
bash ${CLAUDE_SKILL_DIR}/../search-lit/references/pubmed_eutils.sh search \
  '"[Full Name]"[Author]' 200 \
  | python3 ${CLAUDE_SKILL_DIR}/../search-lit/references/parse_pubmed.py esearch
```
If the parser exits non-zero (an error body, or no `count`), the count is unknown — re-run the
search; never record it as 0 papers or 0 MAs.

**Step 2 — Fetch metadata for MeSH-based clustering (parallel):**
```bash
# Get PMIDs from Step 1, then fetch summaries
bash ${CLAUDE_SKILL_DIR}/../search-lit/references/pubmed_eutils.sh fetch_json \
  "PMID1,PMID2,..." \
  | python3 ${CLAUDE_SKILL_DIR}/../search-lit/references/parse_pubmed.py esummary
```

**Step 3 — Topic-specific counts (launch 4-5 searches in parallel Bash calls):**
```bash
bash ${CLAUDE_SKILL_DIR}/../search-lit/references/pubmed_eutils.sh search \
  '"[Full Name]"[Author] AND "keyword1"' 5
bash ${CLAUDE_SKILL_DIR}/../search-lit/references/pubmed_eutils.sh search \
  '"[Full Name]"[Author] AND "keyword2"' 5
# ... repeat for each suspected pillar keyword
```

**Step 4 — MeSH term extraction for automatic pillar clustering:**
```bash
# Fetch full XML for top-cited papers to extract MeSH headings
bash ${CLAUDE_SKILL_DIR}/../search-lit/references/pubmed_eutils.sh fetch \
  "PMID1,PMID2,...,PMID20" \
  | python3 -c "
import sys, xml.etree.ElementTree as ET
from collections import Counter
root = ET.fromstring(sys.stdin.read())
mesh_counts = Counter()
for article in root.findall('.//PubmedArticle'):
    for mh in article.findall('.//MeshHeading/DescriptorName'):
        mesh_counts[mh.text] += 1
for term, count in mesh_counts.most_common(30):
    print(f'{count:3d}  {term}')
"
```
→ Top MeSH terms reveal natural research pillars (e.g., "Colonography, Computed Tomographic" = CTC pillar).

**Step 5 — Google Scholar profile (parallel with PubMed calls):** WebSearch
`"[Full Name]" radiology scholar google` for h-index and citation data; WebFetch any other profile
URL the user provided (skip Scopus).

**Output: Pillar Summary Table.** Publication counts and pillar assignments come from E-utilities
output and the h-index from the Scholar profile — never estimate them.

| Pillar | Domain | Representative keywords | MeSH terms | Est. # papers |
|--------|--------|-------------------------|-----------|---------------|
| 1 | ... | ... | ... | ~N+ |

### Phase 2: MA Gap Analysis (Multi-Source)

**Goal:** For each pillar, determine if a viable MA topic exists using PubMed + Consensus + Scholar
Gateway + bioRxiv + PROSPERO.

Run pillars in parallel: up to 4 subagents, each covering 1-2 pillars and running 2a–2g, each
reporting raw k, realistic k and every source checked. If PubMed returns 0 or Consensus/Scholar
Gateway is unavailable, state that limitation rather than guessing.

#### 2a. PubMed E-utilities — Existing MAs + Primary studies

```bash
# Existing MAs (structured count)
bash ${CLAUDE_SKILL_DIR}/../search-lit/references/pubmed_eutils.sh search \
  '[pillar keywords] AND ("meta-analysis"[pt] OR "systematic review"[pt])' 50

# Primary studies with extractable outcomes
bash ${CLAUDE_SKILL_DIR}/../search-lit/references/pubmed_eutils.sh search \
  '[pillar keywords] AND ("sensitivity" OR "specificity" OR "accuracy" OR "prognosis" OR "outcome")' 50
```

#### 2b. Consensus MCP — Semantic MA gap detection

Use `mcp__claude_ai_Consensus__search` to find existing SRs/MAs that PubMed keyword search might miss:
```
query: "systematic review OR meta-analysis [pillar topic] [imaging modality]"
```
Consensus returns citation-ranked results — check if any highly-cited MA already covers the proposed scope.
**Limit:** max 3 Consensus calls per Phase 2 batch, in total across all agents (rate limit). If
rate-limited, wait 30 s and retry once.

#### 2c. Scholar Gateway — Semantic similarity search

Use `mcp__claude_ai_Scholar_Gateway__semanticSearch` to find MAs under different terminology
(e.g., "pooled analysis" instead of "meta-analysis"), scope-overlapping MAs that use different
keywords, and methodological reviews that partially cover the topic.

#### 2d. bioRxiv/medRxiv — In-press competition detection

Use `mcp__claude_ai_bioRxiv__search_preprints` to catch MAs posted as preprints but not yet in
PubMed, SR/MA protocols shared as preprints, and very recent primary studies that could change
feasibility.
```
query: "[pillar keywords] meta-analysis OR systematic review"
server: "medrxiv"  (clinical topics; "biorxiv" for preclinical)
```

#### 2e. Assessment matrix

| Factor | Criteria |
|--------|----------|
| MA gap | 0 existing = best, 1-3 = check scope overlap, >5 = saturated |
| Primary k | ≥8 for DTA, ≥6 for prognostic (minimum), ≥15 ideal |
| Recency | Last MA >5 years old = update opportunity |
| Competition | Check 2024-2026 for very recent MAs that block entry |

#### 2f. PROSPERO competition check (MANDATORY)

- Search PROSPERO via WebSearch `site:crd.york.ac.uk/prospero [topic keywords]`; also try WebFetch `https://www.crd.york.ac.uk/prospero/#searchadvanced`
- Look for registered-but-unpublished protocols that could block entry; if a PROSPERO match is found → flag as 🚫 competition risk in ranking
- Record the exact query, the search date and one status: `searched (match found)`, `searched (no match)`, or `not checked (unavailable/failed)`; a fetch that returns the site shell or an error page instead of a result list is `not checked`. Only `searched (no match)` clears the PROSPERO gate.

#### 2g. Realistic k estimation

- Raw PubMed hit count is NOT the real k — most studies lack 2x2 data or HR, so raw counts
  overestimate by 3-7x
- Apply conservative discount: **k_realistic ≈ raw_count × 0.15–0.30** for DTA topics
- Flag if k_realistic < 8 (DTA) or < 6 (prognostic) as ⚠️ feasibility risk
- Report both raw and realistic estimates, e.g., `estimated k: ~130 (raw) → ~20–40 (extractable DTA data)`

#### 2h. Niche subtopic discovery (if pillar appears saturated, >5 prior MAs)

Try these angles, and use Consensus to check whether the niche angle has already been covered:
1. **"First MA" rule:** the professor's most unique/niche subtopic where MA = 0
2. **AI/radiomics overlay:** classical imaging topic + AI approach
3. **Treatment response:** diagnosis MAs are often saturated; treatment monitoring is often open
4. **Modality comparison:** head-to-head (e.g., CEUS vs MRI) is often underserved
5. **Guideline gap:** professor-authored guidelines → MA supporting/updating them
6. **Population niche:** specific subpopulation, disease subtype, or regional population (e.g., parasitic diseases, TB)
7. **Temporal update:** last MA >5 years old + significant new primary studies since

### Phase 3: Topic Ranking

**Goal:** Rank all viable topics by composite score. Score each candidate on 5 criteria (★1-5):

| Criteria | Weight | Description |
|----------|--------|-------------|
| **Professor fit** | Highest | Core area of the professor's career, publication count, distinctive contribution |
| **MA gap** | High | No prior MA > ≥5 yr since last MA > recent MA exists |
| **Feasibility (k)** | High | Number of includable studies and extractability of 2×2 or HR data |
| **Clinical impact** | Medium | Whether the topic directly informs clinical decision-making |
| **Execution ease** | Medium | Completable from literature alone; difficulty of managing heterogeneity |

**Output: Ranked Topic Table**

| Rank | Topic | Professor's Pillar | Prior MA | Estimated k (raw→realistic) | PROSPERO competition | Verdict |
|------|-------|--------------------|----------|-----------------------------|----------------------|---------|
| 1 | ... | ... | 0 | ~98 → 15–30 | None | ✅ Best fit |

### Phase 4: Folder & README Scaffolding

**Goal:** Create project folders and README for each viable topic.

1. **Folder location:** `{working_dir}/ma-scout/{initials}_{professor_name}/{NN}_{topic_slug}/`
   - Professor folder: `{initials}_{name}` (e.g., `KDK_Kim`, `LKS_Lee`)
   - NN: sequential number within professor (01, 02, ...); topic_slug: English, underscore-separated
   - Check existing folders with `ls` before creating
2. **README.md (PROSPERO-ready):** copy the template block from
   `${CLAUDE_SKILL_DIR}/references/project_readme_template.md` into `{topic_folder}/README.md` and fill it (PICO/PIRD
   frame, preliminary search, target journal table, backward-planned timeline). Write the research
   question, PICO/PIRD and README content in English, medical terms always in English, unless the
   user asks for the Korean PI-facing variant that reference names.

### Phase 5: Output Summary

1. Save the ranked topic table and README files to the working directory.
2. Summarize: total topics scanned, viable topics found, recommended next steps (see Handoff).

# MODE B: TOPIC-FIRST WORKFLOW

### T-Phase 0: Topic Clarification & Scope

**Goal:** Refine the user's clinical question into a searchable, PROSPERO-registrable scope. When
the user asks for topic suggestions without a specific idea, read
`${CLAUDE_SKILL_DIR}/references/topic_discovery_heuristics.md` first to generate candidate questions.

1. **Parse the input** — disease/condition (e.g., "hepatocellular carcinoma"); imaging modality or
   intervention (e.g., "dual-energy CT", "AI CAD"); outcome type: DTA (Se/Sp), prognostic (HR/OR),
   intervention (RR/MD), dosimetry; population specifics (e.g., "screening setting", "cirrhotic
   patients").
2. **Expand to neighboring angles** — propose 3-5 variations, e.g.:
   ```
   user input: "AI for lung nodule malignancy prediction"
   → variant 1: AI vs radiologist for lung nodule malignancy prediction (DTA)
   → variant 2: Radiomics for lung nodule malignancy (DTA)
   → variant 3: Deep learning for incidental pulmonary nodule management (prognostic)
   ```
3. **User selects 1-3 angles** to investigate further.

### T-Phase 1: Landscape Scan (Multi-Source)

**Goal:** For each selected angle, rapidly assess the MA landscape. **Run all angles in parallel.
For each angle:**

#### 1a. PubMed — Existing MA count
```bash
bash ${CLAUDE_SKILL_DIR}/../search-lit/references/pubmed_eutils.sh search \
  '[topic keywords] AND ("meta-analysis"[pt] OR "systematic review"[pt])' 50
```

#### 1b. PubMed — Primary study pool
```bash
bash ${CLAUDE_SKILL_DIR}/../search-lit/references/pubmed_eutils.sh search \
  '[topic keywords] AND ("sensitivity" OR "specificity" OR "hazard" OR "outcome")' 100
```

#### 1c. Consensus MCP — Semantic MA discovery
```
query: "systematic review [topic] [modality]"
```
Check for MAs using different terminology.

#### 1d. bioRxiv/medRxiv — Preprint competition
```
query: "[topic] meta-analysis"
server: "medrxiv"
```

#### 1e. PROSPERO — Registered protocols
WebSearch: `site:crd.york.ac.uk/prospero [topic keywords]`

**Output: Landscape Summary Table**

| Variant | Existing MAs | Primary k (raw) | k (realistic) | PROSPERO | Preprint MA | Verdict |
|---------|--------------|-----------------|---------------|----------|-------------|---------|
| 1 | 3 | 120 | 18-36 | 1 | 0 | ⚠️ Competitive |
| 2 | 0 | 85 | 13-25 | 0 | 0 | ✅ Optimal |

### T-Phase 2: Feasibility Deep-Dive

**Goal:** For viable angles (MA ≤ 2, no PROSPERO conflict), run the **same Phase 2 (MA Gap
Analysis)** as Mode A — steps 2a through 2h. With no "Professor fit" to evaluate, focus on:
- **Gap certainty** — are existing MAs truly non-overlapping with proposed scope?
- **k quality** — are primary studies heterogeneous enough to warrant MA, or too uniform?
- **User's domain fit** — does this align with user's radiology AI / imaging expertise?

### T-Phase 3: Topic Ranking (Topic-first weights)

| Criteria | Weight | Description |
|----------|--------|-------------|
| **MA gap** | Highest | No existing MA > update opportunity > saturated |
| **Feasibility (k)** | Highest | k_realistic ≥ 8 (DTA) or ≥ 6 (prognostic) |
| **User domain fit** | High | Does it match the user's area of expertise? |
| **Clinical impact** | Medium | Potential to change guidelines; directly tied to clinical decisions |
| **Co-author availability** | Medium | Access to a domain expert (existing relationship or easy to reach) |
| **Execution ease** | Medium | Can be done solo vs requires expert interpretation |

**Output: Ranked Topic Table**

| Rank | Topic | Existing MAs | Est. k | PROSPERO | Co-author needed | Overall |
|------|-------|--------------|--------|----------|------------------|---------|
| 1 | ... | 0 | 25 | None | Optional | ✅ Optimal |

### T-Phase 4: Co-Author Matching (Optional)

**Goal:** If the user wants a senior co-author, find candidates.

**Strategy 1 — Existing network:** check memory files and existing professor folders in the
working directory for professors whose pillar naturally covers this topic (best match).

**Strategy 2 — PubMed reverse search:**
```bash
# Find prolific authors in this specific topic
bash ${CLAUDE_SKILL_DIR}/../search-lit/references/pubmed_eutils.sh search \
  '[topic keywords] AND ("{user_country}"[Affiliation])' 100
```
Then E-utilities efetch → author frequency; the top 5 most-published authors in this niche are
potential co-authors. Cross-check Google Scholar for h-index and recent activity.

**Strategy 3 — Self-led (no senior co-author):** viable when the user has 2+ published MAs and the
topic is methodologically straightforward. A 2nd reviewer (junior colleague or peer) is still
needed — flag this in the README. Corresponding author = user.

**Output:** Co-author recommendation table or a "solo-viable" judgment.

### T-Phase 5: Folder & README Scaffolding (Topic-first)

1. **Folder location:** `{working_dir}/ma-scout/TOPIC/{NN}_{Topic_Abbreviation}/` (e.g.,
   `01_AI_Lung_Nodule_DTA/`). Topic-first projects use the `TOPIC/` prefix, not professor
   initials; if a co-author is matched later, the folder can move under the professor folder.
2. **README.md:** the Phase 4 template with the Solo-Mode Adaptations in
   `${CLAUDE_SKILL_DIR}/references/project_readme_template.md` (Lead/Domain rows, Team Expertise, self-led timeline).
3. **Summary:** same as Mode A Phase 5 — save ranked results and recommend next steps.

## Quality Gates

Before finalizing a topic as viable:

- [ ] (A) **Author identity confirmed** — full name resolved via E-utilities efetch, no initials-only contamination
- [ ] (A) **Affiliation confirmed** with user (or from reliable source)
- [ ] (A) Professor's publication record demonstrates clear authority in this area
- [ ] (B) Clinical question refined to PICO/PIRD (not just a keyword)
- [ ] (A) Confirmed MA = 0 or last MA >5 years (via PubMed E-utilities, not assumption)
- [ ] **Cross-validated** via PubMed + Consensus + Scholar Gateway + bioRxiv/medRxiv — no hidden MAs with different terminology, no preprint MA in progress
- [ ] Confirmed k_realistic ≥ 8 (DTA) or ≥ 6 (prognostic), where k_realistic = raw count × 0.15–0.30
      (§2g: keep 15–30% of raw hits, i.e. a 70–85% discount — not a 15–30% discount)
- [ ] **PROSPERO searched** — the search ran and returned results (query + date recorded, §2f), and no
      registered competing protocol was found. A PROSPERO search that failed or was unavailable is
      "not checked", never "none found": this item stays open
- [ ] No 2024-2026 competing MA in press or preprint
- [ ] Research question is specific enough for PROSPERO registration
- [ ] (B) User's domain expertise sufficient for clinical interpretation (or co-author identified); 2nd reviewer identified or plan to recruit
- [ ] (B) If self-led: user has ≥ 2 published MAs (otherwise, recommend co-author)
- [ ] **README contains:** complete PICO/PIRD, PubMed search strategy, Embase draft, target journal with IF, timeline

## Handoff

- To **`/meta-analysis`**: when a topic is approved and ready for the PROSPERO protocol (README has PICO + search strategy)
- To **`/manage-project`**: when the project folder needs full scaffolding or the user wants results saved to project management
- To **`/search-lit`**: when a deeper preliminary search is needed before committing
- To **`/analyze-stats`**: when feasibility requires power/sample-size calculation for the estimated k

## Phase 6: Pre-Proposal Pipeline (Post-Scout)

After MA Scout identifies viable topics, prepare a "ready-to-propose" package before contacting the
professor. Topics are independent: run up to 4 agents per wave, each doing search → fetch → triage
→ write files.

1. **Search Execution** — E-utilities with broadened synonyms (retmax=200)
   - Primary search: `[topic] AND [outcome keywords]`
   - Existing MA search: `[topic] AND ("meta-analysis"[pt] OR "systematic review"[pt])`
2. **Metadata Collection** — `fetch_json` → `esummary` (batch 40-50 PMIDs)
3. **Title-Based Triage** — classify as INCLUDE / MAYBE / EXCLUDE
   - Check for existing MAs within the results — the initial scout may have missed them
   - Separate sub-approaches that contaminate the pool (e.g., bronchoscopic vs percutaneous)
   - Flag the professor's own papers (authority evidence) and retracted papers
4. **PRISMA Flow Draft** — Identification → Screening → Eligibility → Included (estimated)
5. **Gap Re-assessment** — update the MA count and re-position if needed:
   MA=0 → "first MA" | MA=1 (>5yr) → "update MA" | MA≥3 (recent) → skip/niche
6. **Output Files**:
   - `candidates.md` — full triage table + PRISMA flow + gap finding
   - `README.md` — updated Preliminary Search section with actual numbers

**Professor Contact Package** — the pre-proposal gives the professor: candidate count + gap
evidence (e.g., "MA = 0, 35 studies to include"), a clear role description (e.g., "independent
screening review + discussion only"), and the urgency of PROSPERO pre-registration to secure the topic.
