# Journal Profile Policy

This document defines what a profile must satisfy to live in the public profile library
(`skills/find-journal/references/journal_profiles/` and the matching `write-paper`
directory) versus the user-local private library (`$HOME/.claude/private-journal-profiles/`).

## Why two tiers

The public library ships with the skill and is consumed by every user. A profile that
misrepresents a journal's author guidelines — wrong ISSN, wrong article types, wrong AI
policy wording — propagates that error to every downstream researcher. The private tier
exists so a single user can keep working notes and personal-use profiles without polluting
the shared library.

## The verification bar (public library)

Every public profile must meet **all** of the following. No exceptions, no defaults.

### Source discipline

1. The journal's homepage was opened directly (not inferred from a sibling journal).
2. The journal's Author Guidelines page was opened directly, or equivalent authoritative
   sections were pasted into the session by the maintainer.
3. Every line of the profile cites or is traceable to content on (1) or (2). Plausible
   inference from adjacent journals is not acceptable, even when the journals are in the
   same publisher family.

### Field-level checks

- `Publisher` — transcribed from the journal's own masthead / about page.
- `ISSN (print/online)` — transcribed from the journal's own masthead or ISSN Portal
  (portal.issn.org) entry for that exact journal.
- `Homepage` and `Author guidelines` URLs — both return 200 OK when the profile is
  written. If the guidelines page is 403/login-gated, either paste the accessible
  sections or defer to the private tier.
- `Article Types Accepted` — listed in the journal's own submission/instructions page.
  No "typical for this publisher family" article types.
- `AI policy` sentence — transcribed from the journal's or publisher's AI policy page.
  Family-level defaults (e.g., "follows AHA policy aligned with ICMJE") are only
  acceptable if the journal's own page links to or repeats that family policy; they are
  not a substitute for checking.
- `Special Notes` — any "Choose X over Y" decision rule must be defensible from what the
  two journals' own scope statements say, not from general reputation.

### Proof of verification

Profile authors or maintainers should keep a brief evidence note — either a 1-line
comment at the bottom of the profile, a PR description, or a commit message — stating
which pages were opened and on what date. This lets future audits check whether a profile
has drifted.

## Single entry point for profile creation

Profiles are added and edited through the `/add-journal` skill. Ad-hoc profile creation
(spawning a research agent, writing freehand, copying from another profile) is not
permitted for the public library because it bypasses the skill's built-in 403 handling,
TODO-marking, and anti-hallucination rules.

For one-off personal profiles a user is welcome to write freehand into the private tier,
but the same source-discipline principles apply — infer less, verify more.

## Promotion checklist (private → public)

Before moving a profile from your local private profiles directory (outside this
repo) into `skills/*/references/journal_profiles/`, confirm each item:

- [ ] Journal homepage fetched successfully today and opened manually.
- [ ] Author guidelines page fetched successfully today and opened manually.
- [ ] ISSN cross-checked against portal.issn.org entry for the exact journal name.
- [ ] Publisher name transcribed from the journal's masthead, not inferred.
- [ ] Article types list present on the journal's own page — no family inference.
- [ ] AI policy sentence transcribed from the journal's or publisher's policy page — no
      sibling-journal copy-paste.
- [ ] "Choose X over Y" decision rule defensible from each journal's own scope text.
- [ ] No `[TODO: verify at journal site]` markers remaining.
- [ ] Commit message records which pages were opened and on what date.

Only after all items pass does `git mv` from private to public become appropriate.

## Demotion (public → private)

If an existing public profile is found to fail this bar, either:

1. Fix it in place and commit the correction with evidence, or
2. Demote it back to the private tier with `git mv` and a commit message recording why.

Silently leaving a questionable profile in the public library is not an option.
