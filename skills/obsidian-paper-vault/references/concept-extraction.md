# Extracting Atomic Concept Notes

Literature notes capture what each paper said. Concept notes hold what the reader now
understands across papers. The second layer is where a vault stops being an archive.

## When

Once **10+ literature notes** exist. Below that there is nothing to cross-reference, and the
notes produced are definitions rather than syntheses.

Natural triggers: the user asks what concepts to pull out; a batch just finished; three or
more notes circle the same unlinked idea; the user is preparing to write.

## What qualifies

A phrase earns a concept note when all five hold:

1. It appears in **3+ literature notes**
2. Someone could **learn something** from the note
3. Different papers **treat it differently** — there is something to compare
4. It is **stable**, not a passing label
5. It needs **synthesis**, not a definition lookup

Entities fail criterion 5 and should not become concept notes: model names (GPT-4, Claude),
datasets (MedQA), journals, organizations, evaluation formats. They are references, and a
note about one is a stub that never grows.

Borderline: technique names. `chain of thought` works as a concept if the vault holds papers
that disagree about it; it is a stub if they merely use it.

## Process

**1. Scan for recurring links and terms**

```bash
grep -ho "\[\[[^]]*\]\]" <vault>/Literature/*.md | sort | uniq -c | sort -rn | head -30
```

Or have a subagent read the literature notes and report term frequency with the notes each
term came from.

**2. Filter** — drop entities, keep what passes all five criteria.

**3. Draft** — one note per candidate, following `templates.md`: the papers it draws on, a
synthesized definition, a comparison of how each paper treats it, and two or three open
questions.

**4. Hand back for the user's own edit.** Present drafts and say plainly that the definition
section is a placeholder until the user rewrites it. A concept note the user has not touched
is still a summary wearing a concept note's frontmatter.

## Growth stages

```
🌱 Seedling   →   🌿 Growing    →   🌳 Mature
  ~3 papers       5–10 papers       10+ papers
  AI-drafted      user-edited       user's own position
```

Every note this skill creates starts at 🌱Seedling. Only the user's edits move it along.

## Guarding against sprawl

Roughly **one concept note per 5–7 literature notes** is healthy. Warning signs:

- Dozens of concept notes and none the user has edited — slow down
- Many concepts linked from a single paper — wait for corroboration
- Near-duplicates (`CoT`, `CoT reasoning`, `Chain-of-Thought`) — merge them

## Worked example

Ten medical-AI papers, with the concepts each literature note mentions:

| Literature note | Concepts mentioned |
|---|---|
| AgentClinic | sequential decision-making, multi-agent, bias simulation |
| GPT-4 RCT | management reasoning, LLM co-pilot, clinical trial |
| Med-Gemini | uncertainty-guided search, multimodal, RAG |
| AMIE DDx | differential diagnosis, OSCE, self-play |
| MAI-DxO | sequential diagnosis, cost-aware, multi-agent |
| R-IDEA | clinical reasoning, physician comparison |
| Medprompt | prompt engineering, few-shot, ensemble |
| MAIRA-2 | radiology report, grounded generation |
| HealthBench | physician rubric, LLM-as-judge |
| Reasoning-model CPC | reasoning models, case conference |

**Extracted** (3+ appearances, all five criteria): sequential decision-making; management
reasoning; LLM co-pilot in medicine; uncertainty and hallucination; healthcare benchmarking;
multi-agent systems.

**Not extracted** (entities): GPT-4, o1, Med-PaLM 2; MedQA, NEJM CPC; OSCE; Google, Microsoft.
