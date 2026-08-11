# Tag Vocabulary

Tags exist so the graph view and Dataview queries stay usable. They are a filtering surface,
not a metadata dump. Three well-chosen tags beat ten exhaustive ones.

Emoji prefixes keep Obsidian's tag panel scannable by group.

## Source type — always exactly one

- `📝Paper` — peer-reviewed or preprint research paper
- `📰Article` — blog post, news piece, whitepaper
- `📘Guide` — tutorial, how-to, reference guide
- `🧪TechReport` — model technical report or system card

## Note type

- `🧠Concept` — atomic concept note
- `💭Thought` — the reader's own argument, drawing on several concepts
- `🗺️MOC` — map of content
- `📚Reference` — glossary or lookup note

## Technology

- `🤖AI/LLM` — general large-language-model work
- `🤖AI/{ModelFamily}` — a specific family when the paper is about it (`🤖AI/Claude`,
  `🤖AI/Gemini`, `🤖AI/Llama`, `🤖AI/DeepSeek`)

## Clinical domain

- `🏥ClinicalReasoning` — diagnostic or management reasoning
- `🏥ClinicalSimulation` — simulated clinical environments
- `🏥ClinicalTrial` — randomized or controlled trials
- `🏥ClinicalApplication` — real-world deployment studies
- `🏥DifferentialDiagnosis` — differential-diagnosis focused

## Technical approach

- `🧬RAG` — retrieval-augmented generation
- `🤝MultiAgent` / `🤝Agent` — multi-agent or single-agent frameworks
- `🔤Prompting` — prompt engineering
- `🎓Training` — pre-training or post-training methods
- `🧠Reasoning` — reasoning models and chain-of-thought work
- `👁️Multimodal` — vision-language or audio

## Evaluation and safety

- `📊Benchmark` — benchmark construction or results
- `📊Evaluation` — evaluation methodology
- `📊HeadToHead` — one system directly against another
- `⚠️Safety` — safety-focused
- `🛡️RedTeam` — adversarial testing
- `⚖️Regulation` — regulatory frameworks

## Adding a tag

Check first whether an existing tag covers it. If it genuinely does not, keep the
emoji + PascalCase form (`📊NewConcept`). Avoid tags implied by the vault itself — `🏥Medicine`
on every note in a medical vault filters nothing. Cap a note at four or five tags.

Korean vaults using Korean tag names: `locale/ko/note_templates.md`.
