---
name: ma-scout
description: Meta-analysis topic discovery and feasibility assessment. Professor-first (profile → gap) or Topic-first (question → gap → co-author). Pre-protocol phase from idea to ranked topic list.
triggers: ma-scout, MA 주제 찾기, professor MA, 메타분석 주제, MA gap, topic-first MA, 트렌드 MA, meta-analysis topic, 교수님 분석, 연구 분석
tools: Read, Write, Edit, Bash, Grep, Glob
model: opus
---

# MA Scout Skill

You are helping a medical researcher discover meta-analysis topics.
Two modes are available depending on the starting point.

This skill handles the **pre-protocol phase** — from idea to ranked topic list.
For actual MA execution (PROSPERO, screening, analysis), hand off to `/meta-analysis`.

## Mode Selection

Determine the mode from user input:

| Signal | Mode |
|--------|------|
| Professor name or profile URL provided | **A: Professor-first** |
| Clinical question, keyword, trend, or "find me a topic" | **B: Topic-first** |
| Both supplied (e.g., "this topic with this professor") | **A** (topic as filter) |

If ambiguous, ask the user whether to search by professor (supervisor-first) or by
topic (question-first).

## Communication Rules

- Communicate with the user in their preferred language (typically Korean).
- Research questions, PICO/PIRD, and README content in English.
- Medical terminology always in English.

---

## Inputs

### Mode A: Professor-first
- Professor name (native-language + English)
- Profile URL (ScholarWorks, SKKU Faculty, Google Scholar, ORCID)
- PubMed author link (preferably with cauthor_id for disambiguation)
- Known specialty (e.g., "thoracic imaging", "abdominal imaging")
- Affiliation history (e.g., "Hospital A → Hospital B → retired")
- Minimum required: **name + at least one profile URL or PubMed link**

### Mode B: Topic-first
- Clinical question or keyword (e.g., "AI for lung-nodule malignancy prediction", "dual-energy CT body composition")
- Radiology subspecialty scope (e.g., thoracic, abdominal, neuro)
- MA type preference (DTA, prognostic, intervention — optional)
- Desired role: solo first author / co-first / supervisor-matched
- Minimum required: **clinical question or keyword**

---

## Workflow

> **Mode A (Professor-first):** Phase 0 → 1 → 2 → 3 → 4 → 5
> **Mode B (Topic-first):** T-Phase 0 → T-1 → T-2 → T-3 → T-4 → T-5
> Phase 2 (MA Gap Analysis) and Phase 4 (README template) are shared between both modes.

---

# ═══════════════════════════════════════════
# MODE A: PROFESSOR-FIRST WORKFLOW
# ═══════════════════════════════════════════

### Phase 0: Disambiguation & Context Confirmation

**Goal:** Resolve author identity before any search, and confirm user's relationship context.

**CRITICAL — Do this BEFORE any PubMed search:**

1. **Resolve full English name first:**
   - If cauthor_id is provided → fetch that specific PMID page to get full name + affiliation
   - NEVER start with initials-only search (e.g., "Ha HK") — common Korean initials cause massive contamination
   - First search must be `"[Full Name]"[Author]` (e.g., `"Ha Hyun Kwon"[Author]`)

2. **Confirm affiliation chain with user:**
   - Ask the user whether `{detected affiliation}` matches the professor's history,
     and request the user's relationship to the professor so topic proposals can be
     tuned accordingly.
   - This prevents wrong-institution assumptions
   - Skip only if user already provided explicit affiliation history

3. **Profile URL fallback chain** (Scopus requires auth, so plan alternatives):
   - 1st: PubMed full name search (always works)
   - 2nd: Google Scholar profile (WebSearch `"[Full Name]" radiology scholar`)
   - 3rd: ResearchGate profile (WebSearch `"[Full Name]" researchgate radiology`)
   - 4th: ScholarWorks / SKKU / university faculty page (if URL provided)
   - Last: Scopus/ScienceDirect (often fails due to auth — do NOT rely on it)

---

### Phase 1: Profile Exploration (E-utilities API)

**Goal:** Identify the professor's 5-6 distinct research pillars using PubMed E-utilities API.

**CRITICAL — Use E-utilities API, NOT WebFetch for PubMed:**
- Scripts: `~/.claude/skills/search-lit/references/pubmed_eutils.sh` + `parse_pubmed.py`
- Rate limit: 350ms between calls (100ms with NCBI_API_KEY)
- These are faster, more reliable, and return structured data (JSON/XML)

**Step 1 — Total publication count + PMID list:**
```bash
bash ~/.claude/skills/search-lit/references/pubmed_eutils.sh search \
  '"[Full Name]"[Author]' 200 \
  | python3 ~/.claude/skills/search-lit/references/parse_pubmed.py esearch
```

**Step 2 — Fetch metadata for MeSH-based clustering (parallel):**
```bash
# Get PMIDs from Step 1, then fetch summaries
bash ~/.claude/skills/search-lit/references/pubmed_eutils.sh fetch_json \
  "PMID1,PMID2,..." \
  | python3 ~/.claude/skills/search-lit/references/parse_pubmed.py esummary
```

**Step 3 — Topic-specific counts (launch 4-5 searches in parallel via Bash):**
```bash
# Run these in parallel Bash calls
bash ~/.claude/skills/search-lit/references/pubmed_eutils.sh search \
  '"[Full Name]"[Author] AND "keyword1"' 5
bash ~/.claude/skills/search-lit/references/pubmed_eutils.sh search \
  '"[Full Name]"[Author] AND "keyword2"' 5
# ... repeat for each suspected pillar keyword
```

**Step 4 — MeSH term extraction for automatic pillar clustering:**
```bash
# Fetch full XML for top-cited papers to extract MeSH headings
bash ~/.claude/skills/search-lit/references/pubmed_eutils.sh fetch \
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

**Step 5 — Google Scholar profile (parallel with PubMed calls):**
- WebSearch: `"[Full Name]" radiology scholar google` for h-index, citation data

**Output: Pillar Summary Table**

| Pillar | Domain | Representative keywords | MeSH terms | Est. # papers |
|--------|--------|-------------------------|-----------|---------------|
| 1 | ... | ... | ... | ~N+ |

---

### Phase 2: MA Gap Analysis (Multi-Source)

**Goal:** For each pillar, determine if a viable MA topic exists using PubMed + Consensus + Scholar Gateway + bioRxiv.

For each pillar (run in parallel using meta-analyst agents):

#### 2a. PubMed E-utilities — Existing MAs + Primary studies

```bash
# Existing MAs (structured count)
bash ~/.claude/skills/search-lit/references/pubmed_eutils.sh search \
  '[pillar keywords] AND ("meta-analysis"[pt] OR "systematic review"[pt])' 50

# Primary studies with extractable outcomes
bash ~/.claude/skills/search-lit/references/pubmed_eutils.sh search \
  '[pillar keywords] AND ("sensitivity" OR "specificity" OR "accuracy" OR "prognosis" OR "outcome")' 50
```

#### 2b. Consensus MCP — Semantic MA gap detection

Use `mcp__claude_ai_Consensus__search` to find existing SRs/MAs that PubMed keyword search might miss:
```
query: "systematic review OR meta-analysis [pillar topic] [imaging modality]"
```
Consensus returns citation-ranked results — check if any highly-cited MA already covers the proposed scope.
**Limit:** max 3 Consensus calls per Phase 2 batch (rate limit).

#### 2c. Scholar Gateway — Semantic similarity search

Use `mcp__claude_ai_Scholar_Gateway__semanticSearch` for:
- Finding MAs with different terminology (e.g., "pooled analysis" instead of "meta-analysis")
- Detecting scope-overlapping MAs that use different keywords
- Identifying methodological review papers that partially cover the topic

#### 2d. bioRxiv/medRxiv — In-press competition detection

Use `mcp__claude_ai_bioRxiv__search_preprints` to catch:
- MAs posted as preprints but not yet indexed in PubMed
- Ongoing SR/MA protocols shared as preprints
- Very recent primary studies that could change feasibility

```
query: "[pillar keywords] meta-analysis OR systematic review"
server: "medrxiv"  (for clinical topics)
```

#### 2e. Assessment matrix

| Factor | Criteria |
|--------|----------|
| MA gap | 0 existing = best, 1-3 = check scope overlap, >5 = saturated |
| Primary k | ≥8 for DTA, ≥6 for prognostic (minimum), ≥15 ideal |
| Recency | Last MA >5 years old = update opportunity |
| Competition | Check 2024-2026 for very recent MAs that block entry |

#### 2f. PROSPERO competition check (MANDATORY)

- Search PROSPERO via WebSearch: `site:crd.york.ac.uk/prospero [topic keywords]`
- Also try WebFetch: `https://www.crd.york.ac.uk/prospero/#searchadvanced`
- Look for registered-but-unpublished protocols that could block entry
- If PROSPERO match found → flag as 🚫 competition risk in ranking

#### 2g. Realistic k estimation

- Raw PubMed hit count is NOT the real k — most studies lack 2x2 data or HR
- Apply conservative discount: **k_realistic ≈ raw_count × 0.15–0.30** for DTA topics
- Flag if k_realistic < 8 (DTA) or < 6 (prognostic) as ⚠️ feasibility risk
- Report both raw and realistic estimates, e.g., `estimated k: ~130 (raw) → ~20–40 (extractable DTA data)`

#### 2h. Niche subtopic discovery (if pillar appears saturated)

- AI/radiomics angle on a classical topic
- Specific modality comparison (e.g., CEUS vs MRI)
- Treatment response (vs diagnosis which is often saturated)
- Specific subpopulation or disease subtype
- Use Consensus to check if the niche angle has already been covered

---

### Phase 3: Topic Ranking

**Goal:** Rank all viable topics by composite score.

Score each candidate on 5 criteria (★1-5):

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

---

### Phase 4: Folder & README Scaffolding

**Goal:** Create project folders and README for each viable topic.

1. **Folder location:** `{working_dir}/ma-scout/{initials}_{professor_name}/`
2. **Naming convention:** `{NN}_{topic_slug}/` (within professor folder)
   - Professor folder: `{initials}_{name}` (e.g., `KDK_Kim`, `LKS_Lee`)
   - NN: sequential number within professor (01, 02, ...)
   - topic_slug: English, underscore-separated
   - Check existing folders with `ls` before creating

3. **README.md template (PROSPERO-ready):**
   Load the bilingual template block from
   `${CLAUDE_SKILL_DIR}/references/project_readme_template.md` and copy it into
   `{topic_folder}/README.md`. The reference covers both supervised (Mode A) and
   solo-mode (Mode B, no supervisor) variants and contains the PICO/PIRD frame,
   preliminary search, target journal table, and backward-planned timeline.

---

### Phase 5: Output Summary

**Goal:** Persist findings for the user.

1. Save the ranked topic table and README files to the working directory.
2. Summarize: total topics scanned, viable topics found, recommended next steps.
3. Suggest the user save results to their project management system (e.g., `/manage-project`).

---

## Niche Topic Discovery Heuristics

When all major pillars are saturated (>5 prior MAs), try these angles:

1. **"First MA" rule:** Professor's most unique/niche subtopic where MA = 0
2. **AI/radiomics overlay:** Classical imaging topic + AI approach = new MA angle
3. **Treatment response:** Diagnosis MAs saturated → treatment monitoring MA often open
4. **Modality comparison:** Head-to-head (e.g., CEUS vs MRI) often underserved
5. **Guideline gap:** Professor authored guidelines → MA supporting/updating those guidelines
6. **Geographic/population niche:** Regional population-specific MA (e.g., parasitic diseases, TB)
7. **Temporal update:** Last MA >5 years old + significant new primary studies since

---

## Quality Gates

Before finalizing a topic as viable:

- [ ] **Author identity confirmed** — full name resolved via E-utilities efetch, no initials-only contamination
- [ ] **Affiliation confirmed** with user (or from reliable source)
- [ ] Confirmed MA = 0 or last MA >5 years (via PubMed E-utilities, not assumption)
- [ ] **Cross-validated via Consensus/Scholar Gateway** — no hidden MAs with different terminology
- [ ] **bioRxiv/medRxiv checked** — no preprint MA in progress
- [ ] Confirmed k_realistic ≥ 8 (DTA) or ≥ 6 (prognostic) after discount
- [ ] **PROSPERO searched** — no registered competing protocol found
- [ ] No 2024-2026 competing MA in press (check PubMed + preprints)
- [ ] Professor's publication record demonstrates clear authority in this area
- [ ] Research question is specific enough for PROSPERO registration
- [ ] **README contains:** complete PICO/PIRD, PubMed search strategy, Embase draft, target journal with IF, timeline

---

## Handoff

After MA Scout completes:
- To **`/meta-analysis`**: When a topic is approved and ready for PROSPERO protocol (README has PICO + search strategy ready)
- To **`manage-project`**: When project folder needs full scaffolding
- To **`search-lit`**: When deeper preliminary search is needed before committing
- To **`/analyze-stats`**: When feasibility requires power/sample-size calculation for the estimated k

---

## Parallel Execution Strategy

For efficiency, launch multiple agents and API calls in parallel:

**Phase 0 (Identity):**
1. E-utilities esearch: `"[Full Name]"[Author]` → total count + PMIDs (FIRST)
2. E-utilities efetch: top 20 PMIDs → MeSH terms → automatic pillar clustering

**Phase 1 (Profile — all parallel):**
3. Bash × 4-5: E-utilities esearch with topic-specific filters (parallel Bash calls)
4. WebSearch: Google Scholar profile
5. WebFetch: any provided profile URLs (skip Scopus)

**Phase 2 (MA Gap — multi-source parallel):**
6. Up to 4 meta-analyst agents in parallel, each covering 1-2 pillars
7. Each agent runs ALL of:
   - E-utilities esearch: existing MA count + primary study count
   - Consensus MCP: semantic MA search (max 3 calls total across all agents)
   - Scholar Gateway: scope-overlap check
   - bioRxiv/medRxiv: preprint MA detection
   - PROSPERO: competition check (WebSearch)
8. Each agent reports: raw k, realistic k (15-30% discount), all sources checked

**Phase 3 (Ranking):** Sequential, uses Phase 2 outputs.

**Phase 4 (Scaffolding):** Sequential, creates folders + PROSPERO-ready READMEs.

Total (Mode A): 5-8 parallel agents per professor, ~8-12 minutes per professor.

### Mode B Parallel Strategy

**T-Phase 0:** Sequential (user interaction for scope clarification).

**T-Phase 1 (Landscape — all angles in parallel):**
1. Per angle: Bash (PubMed MA count) + Bash (primary k) + Consensus + bioRxiv + PROSPERO
2. 3-5 angles × 5 sources = 15-25 parallel calls

**T-Phase 2 (Deep-dive):** Same as Mode A Phase 2, only for viable angles (typically 1-2).

**T-Phase 4 (Co-author — if needed):**
3. Bash: PubMed author frequency search
4. WebSearch: Google Scholar profiles for top candidates

Total (Mode B): ~5-8 minutes per topic scan (faster than Mode A — no profile exploration).

### Known Pitfalls (from 3 professor analyses)
- Common Korean/Asian initials (e.g., "Lee KS", "Kim DK") return 300+ papers with massive contamination. Always use full name first.
- Scopus/ScienceDirect → 403 or redirect to login. Never rely on Scopus as primary data source.
- Raw PubMed counts overestimate by 3-7x. ~130 hits often means 20-40 with extractable DTA data.
- Professor may have moved institutions. Don't assume affiliation without verification.
- **Consensus rate limit:** Max 3 batch calls. If rate-limited, wait 30s and retry once.
- **E-utilities rate limit:** 350ms between calls (100ms with NCBI_API_KEY). Scripts handle this automatically.
- **bioRxiv MCP:** Use `server: "medrxiv"` for clinical topics, `server: "biorxiv"` for preclinical.

---

# ═══════════════════════════════════════════
# MODE B: TOPIC-FIRST WORKFLOW
# ═══════════════════════════════════════════

### T-Phase 0: Topic Clarification & Scope

**Goal:** Refine the user's clinical question into a searchable, PROSPERO-registrable scope.

1. **Parse the input** — extract:
   - Disease/condition (e.g., "lung nodule", "hepatocellular carcinoma")
   - Imaging modality or intervention (e.g., "dual-energy CT", "AI CAD")
   - Outcome type: DTA (Se/Sp), prognostic (HR/OR), intervention (RR/MD), dosimetry
   - Population specifics (e.g., "screening setting", "cirrhotic patients")

2. **Expand to neighboring angles** — propose 3-5 variations:
   ```
   user input: "AI for lung nodule malignancy prediction"
   → variant 1: AI vs radiologist for lung nodule malignancy prediction (DTA)
   → variant 2: Radiomics for lung nodule malignancy (DTA)
   → variant 3: Deep learning for incidental pulmonary nodule management (prognostic)
   → variant 4: AI-assisted Lung-RADS upgrade accuracy (DTA)
   → variant 5: Low-dose CT AI for lung cancer screening (DTA)
   ```

3. **User selects 1-3 angles** to investigate further.

---

### T-Phase 1: Landscape Scan (Multi-Source)

**Goal:** For each selected angle, rapidly assess the MA landscape.

**Run all angles in parallel. For each angle:**

#### 1a. PubMed — Existing MA count
```bash
bash ~/.claude/skills/search-lit/references/pubmed_eutils.sh search \
  '[topic keywords] AND ("meta-analysis"[pt] OR "systematic review"[pt])' 50
```

#### 1b. PubMed — Primary study pool
```bash
bash ~/.claude/skills/search-lit/references/pubmed_eutils.sh search \
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

---

### T-Phase 2: Feasibility Deep-Dive

**Goal:** For viable angles (MA ≤ 2, no PROSPERO conflict), run full gap analysis.

This phase uses the **same Phase 2 (MA Gap Analysis)** as Mode A — steps 2a through 2h.
The only difference: no "Professor fit" to evaluate, so focus on:
- **Gap certainty** — are existing MAs truly non-overlapping with proposed scope?
- **k quality** — are primary studies heterogeneous enough to warrant MA, or too uniform?
- **User's domain fit** — does this align with user's radiology AI / imaging expertise?

---

### T-Phase 3: Topic Ranking (Topic-first weights)

**Goal:** Rank viable topics with weights adjusted for topic-first approach.

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

---

### T-Phase 4: Co-Author Matching (Optional)

**Goal:** If the user wants a senior co-author, find candidates.

**Strategy 1 — Existing network (memory-based):**
- Check memory files for professors with overlapping expertise
- Cross-reference existing professor folders in the working directory
- Best match = professor whose pillar naturally covers this topic

**Strategy 2 — PubMed reverse search:**
```bash
# Find prolific authors in this specific topic
bash ~/.claude/skills/search-lit/references/pubmed_eutils.sh search \
  '[topic keywords] AND ("{user_country}"[Affiliation])' 100
```
Then:
- E-utilities efetch → extract author frequency from results
- Top 5 most-published authors in this niche = potential co-authors
- Cross-check Google Scholar for h-index and recent activity

**Strategy 3 — Self-led (no senior co-author):**
- Viable when: user has 2+ published MAs, topic is methodologically straightforward
- Still need 2nd reviewer (junior colleague or peer) — flag this in README
- Corresponding author = user

**Output:** Co-author recommendation table or a "solo-viable" judgment.

---

### T-Phase 5: Folder & README Scaffolding (Topic-first)

**Goal:** Create project folder and PROSPERO-ready README.

1. **Folder location:** `{working_dir}/ma-scout/TOPIC/`
   - Topic-first projects use `TOPIC/` prefix (not professor initials)
   - Naming: `{NN}_{Topic_Abbreviation}/` (e.g., `01_AI_Lung_Nodule_DTA/`)
   - If co-author matched later, can be moved under professor folder

2. **README.md template:** Same PROSPERO-ready template as Mode A Phase 4 (see
   `references/project_readme_template.md`), with these changes:
   - `Supervisor:` → `Lead: {user_name}` or `Lead: {user_name} + {co-author}`
   - Drop the supervisor-area row; use `Domain: {subspecialty}` instead.
   - Rename `Professor's Authority` → `Team Expertise` (user's credentials + co-author if any)
   - Timeline: drop the supervisor-proposal step → start directly at PROSPERO registration.

   **Timeline template (self-led):**
   | Step | Expected timing | Precondition |
   |------|-----------------|--------------|
   | PROSPERO registration | {YYYY-MM} | topic confirmed |
   | Search complete | +1 week | PROSPERO registration |
   | Screening complete | +2 weeks | 2nd reviewer secured |
   | Data extraction | +3 weeks | screening consensus |
   | Analysis + draft | +5 weeks | data lock |
   | Co-author review | +7 weeks | draft complete |
   | Submission | +8 weeks | final approval |

3. **Summary:** Same as Mode A Phase 5 — save ranked results and recommend next steps.

---

### Topic Discovery Heuristics (Mode B specific)

When the user asks for topic suggestions without a specific idea:

1. **Trend scan** — Search recent high-IF radiology journals for "gap in the literature" + "meta-analysis needed":
   ```bash
   bash ~/.claude/skills/search-lit/references/pubmed_eutils.sh search \
     '"no meta-analysis" AND "radiology"[Journal] AND 2024:2026[dp]' 30
   ```

2. **Guideline update gaps** — New guidelines (ACR, ESR, RSNA) often cite lack of MA evidence:
   - Consensus search: `"practice guideline" AND "insufficient evidence" AND [radiology subspecialty]`

3. **AI + classical imaging** — Overlay AI/DL/radiomics on well-studied classical topics:
   - Many classical DTA topics have 10+ MAs, but AI angle has 0-1

4. **Korean/Asian population** — Population-specific MA for diseases with geographic variation:
   - TB, NTM, parasitic diseases, gastric cancer, liver fluke, HBV-related HCC

5. **Technology adoption** — New modalities with growing evidence but no synthesis:
   - Photon-counting CT, abbreviated MRI, contrast-enhanced mammography, AI CAD

6. **Cross-subspecialty** — Topics spanning two subspecialties often fall through MA cracks:
   - Cardiac + thoracic (coronary CT + lung screening), neuro + MSK (spine imaging)

---

### Quality Gates (Mode B specific)

Before finalizing a topic-first MA as viable:

- [ ] Clinical question refined to PICO/PIRD (not just a keyword)
- [ ] MA gap confirmed via PubMed + Consensus + Scholar Gateway + bioRxiv (all 4 sources)
- [ ] k_realistic ≥ 8 (DTA) or ≥ 6 (prognostic) after 15-30% discount
- [ ] PROSPERO searched — no competing registered protocol
- [ ] No 2024-2026 competing MA in press or preprint
- [ ] User's domain expertise sufficient for clinical interpretation (or co-author identified)
- [ ] 2nd reviewer identified or plan to recruit
- [ ] README contains: complete PICO/PIRD, PubMed + Embase search strategy, target journal with IF, timeline
- [ ] If self-led: user has ≥ 2 published MAs (otherwise, recommend co-author)

---

## Phase 6: Pre-Proposal Pipeline (Post-Scout)

After MA Scout identifies viable topics, run the **pre-proposal pipeline** to prepare
a "ready-to-propose" package before contacting the professor.

### Pipeline Steps

1. **Search Execution** — E-utilities with broadened synonyms (retmax=200)
   - Primary search: `[topic] AND [outcome keywords]`
   - Existing MA search: `[topic] AND ("meta-analysis"[pt] OR "systematic review"[pt])`

2. **Metadata Collection** — `fetch_json` → `esummary` (batch 40-50 PMIDs)

3. **Title-Based Triage** — Classify as INCLUDE / MAYBE / EXCLUDE
   - CRITICAL: Check for existing MAs within results (initial scout may miss them)
   - Separate bronchoscopic vs percutaneous (30% contamination in CBCT topics)
   - Flag professor's own papers (authority evidence)
   - Flag retracted papers

4. **PRISMA Flow Draft** — Identification → Screening → Eligibility → Included (estimated)

5. **Gap Re-assessment** — Update MA count, re-position if needed:
   - MA=0 → "first MA" | MA=1 (>5yr) → "update MA" | MA≥3 (recent) → skip/niche

6. **Output Files**:
   - `candidates.md` — full triage table + PRISMA flow + gap finding
   - `README.md` — updated Preliminary Search section with actual numbers

### Parallel Execution
- Launch up to 4 agents per wave (each topic independent)
- Each agent: search → fetch → triage → write files → ~5-10 min
- 21 topics completed in ~1 hour with 16 parallel agents

### Professor Contact Package
The pre-proposal gives the professor:
- Candidate count + gap evidence (e.g., "MA = 0, 35 studies to include")
- Clear role description (e.g., "independent screening review + discussion only")
- Urgency of PROSPERO pre-registration to secure the topic

## Anti-Hallucination

- **Never fabricate publication counts, h-index, or pillar classifications.** All numbers must come from PubMed E-utilities API output.
- **Never fabricate existing MA counts.** Always verify via PubMed search + PROSPERO check before claiming "MA = 0".
- **Never invent professor expertise or affiliation.** Confirm with user before proceeding.
- **k_realistic must use the 15-30% discount.** Raw PubMed counts overestimate by 3-7x. Always report both raw and realistic estimates.
- If PubMed returns 0 or Consensus/Scholar Gateway is unavailable, state the limitation rather than guessing.
