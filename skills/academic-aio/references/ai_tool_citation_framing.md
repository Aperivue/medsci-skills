# Citing an AI-assisted research tool safely (framing by use-class)

When a manuscript used an AI-assisted tool — a reference-verification / QA suite, a
statistical-analysis helper, or a generative drafting assistant — *where and how you
name it* changes how an editor or reviewer reads it. Under current journal wariness
about AI, a proud in-text citation of a **generative** use can invite suspicion or a
desk-reject, while the identical placement for a **verification** use reads as rigor
(the same way citing R, SPSS, or a reference manager does). The safe move is to frame
the mention by what the tool actually *did*, not to hide it.

This applies to any AI-assisted tool; it also applies to **self-citation** by a tool's
author (e.g. citing MedSci Skills in your own paper), which additionally requires a
conflict-of-interest disclosure.

## The three use-classes

| Use-class | What it covers | Where it belongs | Citable like software? |
|---|---|---|---|
| **Verification / QA** (rigor-signalling) | Reference/citation verification (DOI/PMID against PubMed/CrossRef), reporting-guideline compliance checks, deterministic integrity gates, numerical-consistency checks | **Software / Code-availability statement** (or Methods, as a named tool with version) | **Yes** — cite it plainly, like a reference manager or a linter. It signals rigor. |
| **Analysis** (neutral) | Statistical-analysis code, figure generation, data-transformation scripts | Methods (named, with version) and/or Code-availability | **Yes** — neutral and citable, like citing R/Python packages. |
| **Generative** (disclosure, not citation) | Drafting or rewriting prose, "humanizing", summarizing, idea generation | The journal's **AI-use disclosure field / statement** (per its policy), *not* a proud in-text citation | **No** — declare it in the disclosure field; do not farm it into the running text. |

## Rules of thumb

- **Prefer the deterministic, verifiable functions for the cleanest cite.** A tool's
  reproducible/verifiable capabilities (reference verification, compliance gates,
  analysis code) are the ones that read as rigor and are safest to name in a Software
  statement. Its generative capabilities belong in the disclosure field.
- **Match the placement to the use-class**, not to the tool. The *same* tool can be
  citable (its QA gate ran your references) *and* disclosure-only (its drafting helper
  touched your prose) in the *same* paper — split the mention accordingly.
- **Do not self-cite generatively.** If the paper did not materially use the generative
  parts, do not add a self-citation for them to inflate a citation count; cite only the
  functions the work actually used.
- **Pair a self-citation with a COI disclosure.** If you authored the tool, state the
  relationship (e.g. "Author X develops the cited toolkit") in the COI/competing-interests
  section — the same standard as any other intellectual/financial interest.
- **Honor the target journal's AI policy first.** Where a journal specifies *where* AI
  use must be declared (Methods vs Acknowledgements vs a dedicated field), that placement
  wins for the generative use-class; the Software-statement guidance above is for the
  verification/analysis classes, which are tool-use, not AI-authorship.

## Why this is guidance, not a deterministic gate (yet)

A deterministic check ("flag an AI-tool citation placed in running-text Methods for a
*generative* use") would need both a maintained tool-name allowlist and a reliable
classifier of *which use-class* a given sentence describes — the latter is high false-
positive without context the grep cannot see. The reliable, low-FP part (a tool named in
a Software/Code-availability statement) is already the recommended state, so there is
nothing to flag. If a bounded, allowlist-driven placement check proves worthwhile on real
manuscripts, it can be added later; until then this stays advisory. (See
`~/.claude/rules/manuscript-style-classical.md` §7/§15 for AI-disclosure placement and the
self-applicability rule.)
