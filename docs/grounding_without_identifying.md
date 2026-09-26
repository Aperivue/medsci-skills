# Grounding a rule without identifying the case

Rules in this repository are written from things that actually went wrong. That is deliberate and it
is why they are worth following — `"Precedent failure pattern — treat this as a lived near-miss, not
hypothetical"` appears in the skills themselves. Nothing here asks anyone to stop doing that.

What it asks is narrower: **keep the grounding, drop the identification.**

## Why this page exists

A repo-wide PII audit on 2026-08-15 found that the literal blocklist was doing its job and the
leaks were elsewhere. `check_precedent.py` matches literals — names, emails, submission IDs — and
what survives a literal sweep is never a literal. It is the sentence that grounds the rule.

The worst instance carried no name, no email and no ID, and described one peer review in three
directions at once: what the manuscript claimed versus measured, what a co-reviewer's report said
and how long it was, and what the editor decided. Every gate read it as clean. All of them were
correct; none of them was looking at the right thing.

## The three directions of a peer review

A review is confidential in three directions, and all three are easy to write down by accident:

| direction | what leaks | safe version |
|---|---|---|
| **the manuscript** | claimed-vs-measured task, design, the specific reframe proposed | "a task-formulation mismatch" |
| **a co-reviewer's report** | its length, its argument, its conclusion | omit entirely — it was never yours |
| **the editor's decision** | the verdict, or the distance from your recommendation | "the outcome landed below its tier" |

The second one is the trap: describing a co-reviewer's report feels like describing the *case*, but
it is describing *another person's confidential document*.

## Your own submissions are not exempt

An author's submission history is not public either. Specifically:

- the target journal **with** a day-precision date, an article type and a subspecialty,
- and above all **a cascade** — that a submission followed a decline elsewhere.

Journal-profile provenance should say what it was read off and roughly when: *"verified in-portal
YYYY-MM"* carries the staleness signal that a date exists for. *"live submission, YYYY-MM-DD, after
a rejection"* carries a person's year. The second form is written here with the digits removed on
purpose: an illustration of a leak does not need to be one.

## A shared date is a batch, and a batch can be a shortlist

Five journal profiles once carried the same harvest **day** in their text. Individually each was a
public document; together they were one manuscript's target list, and their order carried which
were the fallbacks. Month precision keeps the staleness signal and drops the batch.

## The four questions

Before committing a block that begins *Precedent*, *Why this is here*, *Source*, *Motivation*, or
*verified &lt;date&gt;*:

1. **Could the person, manuscript, review or submission be worked out from this** — including by
   combining it with the public author byline, or with a commit message in this same repository?
2. **Does it describe anyone else's confidential document?** A co-reviewer's report and an editor's
   decision are the two that keep appearing.
3. **Does the number need that many digits?** A result to four decimals fingerprints one dataset. A
   word count fingerprints one document. "They disagreed in the fourth decimal" teaches the same
   lesson.
4. **Does the date need the day?** Almost never. Month precision is enough for staleness.

If the lesson survives without the specifics, they were never the lesson.

## What checks this — two tiers, because one cannot work

The first version of this gate had a single tier tuned to give zero standing hits. Run against the
six findings the audit had actually produced, it caught **zero of them**. A threshold tuned for
silence is silent, and it would have shipped a gate whose real function was to make the repository
feel covered. The split below is measured, not guessed.

**Tier 1 — CI refuses outright** (`check_provenance_blocks.py --mode block`). Three signals, each
with a standing count of **0** across the 53 provenance blocks here, because nothing legitimate
does them: describing a co-reviewer's report or an editor's decision · a submission ID · quoted
assessment language. Run by `validate_skills.sh`.

**Tier 2 — routed to a reader** (`--mode route`, 39 blocks repo-wide, 0–2 per diff). A fetch date,
a rounded statistic, a block with no public citation. These fire on perfectly good provenance, so
they are **not** enforced deterministically — no threshold over them separates "identifies someone"
from "does not", because that distinction is semantic.

**The judgement** — a person, reading the candidates the router hands over. Tooling to put a model
in front of that reader is drafted but not shipped here, deliberately: it would have to fail open
when the CLI is absent (most contributors do not have it, and a checklist typo must never be blocked
by a tool nobody has), and a check that fails open is worth having only once someone is watching
whether it ever fires. Note for whoever builds it: read the **added lines**, not only paragraphs —
a table row and a bullet list are neither, and two of the six audit findings were exactly those
shapes.

**The regression** — `tests/test_provenance_blocks.sh`. Its positive fixtures are the shapes the
audit actually found; its negatives are this repository's own working provenance, because the first
version of the router fired on a public DOI, and a checker that rejects the world's notation gets
switched off. One case exists purely to stop tier 2 going quiet again.

A model's verdict is an opinion, not a finding. Read the block yourself before acting on it — and
before dismissing it.

## Prior art in this repository

`skills/peer-review/references/reviewer_profiles/README.md` reached the same rule independently and
earlier, for one directory: *"Date and round only — never the manuscript ID."* The audit found
those profiles clean. A written convention held where an unwritten one did not, which is the
argument for this page existing.
