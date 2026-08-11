# The Three-Layer Vault

Read this when the user asks how the pieces fit together, or why the skill refuses to write
certain notes.

## The layers

```
┌──────────────────────────────────────────────────────┐
│  Layer 3 — Thought      Thoughts/                    │
│  The reader's own questions and hypotheses            │
│  USER-AUTHORED. This skill never writes here.         │
├──────────────────────────────────────────────────────┤
│  Layer 2 — Atomic       Concepts/                    │
│  Concepts synthesized across papers                   │
│  SKILL DRAFTS, USER REWRITES.                         │
├──────────────────────────────────────────────────────┤
│  Layer 1 — Capture      Literature/  +  PDFs/        │
│  One templated note per paper, plus the sources       │
│  SKILL GENERATES from extracted text.                 │
└──────────────────────────────────────────────────────┘
```

Links alone do not make a second brain — they give topology without meaning. What makes the
vault usable is that captured knowledge, the reader's understanding of recurring ideas, and
the reader's own open questions live in separate places and are maintained differently.

Only layer 1 scales through automation. Layer 2 is a collaboration. Layer 3 is not the
skill's to write.

## What this skill does at each layer

**Layer 1 — automated.** Extract PDF text, write one templated note per paper, keep
frontmatter consistent so Dataview resolves, embed the PDF for split-view reading, track
progress in the queue file.

**Layer 2 — drafted, then handed over.** Identify ideas recurring across 3+ notes, draft
concept notes with the definition section explicitly marked as a placeholder, propose which
literature notes should link to each, and say when enough papers have accumulated to extract
more.

**Layer 3 — untouched.** The skill may point out tensions between papers that look worth
thinking about. It does not write thought notes. What is worth thinking about is the reader's
call.

## Folder layout

```
vault/
├── MOC.md                    # dashboard, usually Dataview-driven
├── Literature/               # layer 1 — one note per paper
├── Concepts/                 # layer 2 — atomic concepts
├── Thoughts/                 # layer 3 — user only
└── PDFs/                     # the source files the notes embed
```

Text extraction caches outside the vault (`~/.local/cache/paper-vault-texts/` by default) so
intermediate files never sync to other devices.

**Honor the layout that exists.** Vaults in the wild use `02_research/논문/`, `papers/`,
`Reading/`, and many others. Match what is there and never rename a folder the user already
organizes around. Korean-structured vaults: `locale/ko/note_templates.md`.

## End to end

**First run** — confirm PyMuPDF; agree the vault paths; create the literature folder and the
text cache; extract; build `PAPER_QUEUE.md` from the PDF list; run the first batch of five
subagents.

**Each subsequent batch** — extract any new PDFs, group the batch thematically, run five
subagents, mark the queue, and report which concepts are approaching the 3-paper threshold.

**Concept pass, every 10+ papers** — scan for recurring terms, filter against the criteria in
`concept-extraction.md`, draft three to five notes, hand them to the user to rewrite the
definitions.

## When the vault is working

The user opens a note and reads the PDF beside it. Dataview tables populate. Concept notes
carry three or more backlinks. The user has started writing in layer 3 unprompted.

And the one that decides whether any of the rest matters: **the user trusts the notes enough
to cite them.** That trust is broken by a single fabricated number, and it does not come
back — which is why extraction to text, and never writing from model knowledge, is the rule
the others are built around.
