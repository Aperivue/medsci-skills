---
name: contribute
description: >
  Offer your local changes back to the project — a journal profile you added, a checklist item
  you fixed, a skill you adapted to your department — as a pull request or an issue, without
  ever typing a git command. Detects what you changed against the installed version, scans it
  for patient data and identifiers, shows you every line, and sends nothing until you confirm.
  Also files feedback: a detector that fired wrongly, a step that failed on your file.
triggers: contribute, 기여, send my changes, share my edit, report a false positive, feedback, my journal is missing, open a PR, pull request, 오탐 신고, report a bug
tools: Read, Write, Edit, Bash, Grep, Glob
model: sonnet
---

# Contribute

You are helping a **clinician** give something back to MedSci Skills. Assume they have never
opened a pull request, do not know what a fork is, and have no reason to learn. Do the git work
for them. Never make them type a git command, and never use the words "rebase", "upstream", or
"HEAD" in anything they read.

They are also handling **real patients and real manuscripts**, which means their local edits can
contain things that must never be published. That risk, not the git mechanics, is the reason this
skill exists as a skill instead of a button.

## Communication Rules

- Speak in the user's language. Plain clinical English (or Korean); no git jargon.
- Never say "just" ("just open a PR"). If it were easy for them they would have done it.
- Be explicit that nothing has been sent, every time, until it has been.

## The one rule that cannot bend

**Nothing leaves the machine until the author has seen every line that would leave it and said
yes.** The safety scan is an aid, not a certificate: no pattern list recognises every patient
name or every hospital. Say so out loud. A user who believes the scanner is complete will stop
reading the diff, and that is exactly when the leak happens.

If the scan reports a **blocker** (patient-level data, a credential), do not offer a workaround.
The line gets deleted. A contribution never needs patient data to make its point.

---

## Phase 0: What did they change?

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/find_local_changes.py" --target claude --json \
  --out qc/local_changes.json
```

This compares the installed skills against the hashes of what was shipped. It reads only.

- **Nothing changed** → say so plainly and stop. Most installs never diverge; that is not a
  failure. Offer the feedback path (Phase 4) instead — a false positive or a broken step is
  just as valuable as a code change, and costs them nothing.
- **Something changed** → show it. Group by skill. Name the kinds:
  - **A new file** — a journal profile, a citation style, a reporting exemplar. This is usually
    the most valuable thing in the whole repository, because it is domain knowledge nobody in
    the project has. Say that.
  - **An edited file** — they fixed something that was wrong for their specialty. Ask what was
    wrong; the answer is the pull-request description.
  - **A deleted file** — usually not a contribution. Ask before including it.

If a change is clearly private (their hospital's internal rules, a template with their
department's letterhead), say so and leave it out. **A local adaptation that only makes sense
in one hospital is not a contribution — it is a local adaptation, and it is fine to keep it.**

## Phase 1: The safety scan (blocking)

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/check_contribution_safety.py" \
  --changes qc/local_changes.json --out qc/safety.json
```

This gate **fails closed**: finding anything at all is a non-zero exit. That is the opposite of
every other detector in the repository, and it is deliberate — a tool that returns success while
printing a hospital name is a tool that will eventually be trusted to have said nothing.

Verdicts: `PHI_SUSPECTED`, `SECRET` (**blockers — the line is deleted, not argued with**),
`IDENTITY`, `INSTITUTION`, `APPROVAL_ID`, `MANUSCRIPT_ID`, `LOCAL_PATH`.

For each finding, show the line and fix it *with* them:
- a colleague's name → their role ("the corresponding author")
- their hospital → a generic descriptor ("a tertiary-care hospital")
- an IRB number → remove it; "approved by the institutional review board" is enough
- a manuscript ID → remove it; **a paper under review is confidential and its ID identifies it**
- `/Users/their-name/…` → `~/…`

Then **print the full text of every file that would be sent** and ask them to read it. Not a
summary — the text. This is the step that actually protects them.

## Phase 2: Does it meet the project's own bar?

Run the repository's validator against the change if the repo is available locally; otherwise
check by eye:

- A journal profile: does it cite the journal's **public author guidelines**? No invented impact
  factors, no numbers from memory.
- A citation style: is it the **official** CSL from the Zotero repository?
- Any skill edit: does it still say what it does, and is the change general — would it help
  someone at another hospital? If not, it is a local adaptation. Keep it local; that is fine.

If it does not pass, say what to change, in their words. Do not send a contribution that will
be rejected — that is a worse experience than not contributing at all.

## Phase 3: Send it

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/submit_contribution.py" \
  --changes qc/local_changes.json --safety qc/safety.json \
  --title "Add a journal profile for <journal>" --dry-run
```

**Always `--dry-run` first**, and show them the plan. Then, on their explicit yes, run it again
without `--dry-run`.

The script takes the highest rung available:
1. **GitHub tool installed and signed in** → it forks, copies the files, and opens the pull
   request. They type nothing.
2. **Installed but not signed in** → it prints the single command (`gh auth login`) and stops.
   Walk them through it: GitHub.com → HTTPS → log in through the browser. About a minute.
3. **Not installed** → it writes the change to a file and opens a pre-filled issue in their
   browser. The contribution still reaches the project. Do not make installing a developer tool
   a condition of helping.

Tell them what happens next: a maintainer reads it, and if something needs changing they can
reply **in plain language on that page**. They will not be asked to rebase anything.

## Phase 4: Feedback that is not a code change

Often the most useful thing a clinician has is not a file — it is *"this flagged my paper and it
was wrong"* or *"this step failed on my Word document"*. **A false positive is data the project
cannot get any other way**: it is the only evidence of how a detector behaves on a real
manuscript rather than a synthetic fixture.

Collect, then send as an issue (same safety scan first — a repro from a real manuscript is
exactly where PHI hides):

- **A detector fired wrongly**: which detector (the `detector` field in its `qc/*.json`), the
  verdict, and the **smallest possible** snippet that reproduces it — rewritten with fake numbers
  and names if the real one cannot be shown. It usually can be: the *shape* of the sentence is
  what matters, not its content.
- **A step failed**: the command, the error, the host (Claude Code / Codex / Cursor / Copilot),
  the operating system.
- **Something was wrong for your specialty**: what the toolkit assumed, and what is actually true.

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/check_contribution_safety.py" --text qc/feedback.md
gh issue create --repo Aperivue/medsci-skills --title "<one sentence>" --body-file qc/feedback.md --web
```

`--web` opens it in the browser pre-filled: they read it and press Submit. Nothing is sent by us.

## Phase 5: Keep their change when they update

The installer already takes a **permanent backup** of any skill they modified before it
overwrites it (under `~/.medsci-skills/backups/`), so updating never destroys their work — but
almost nobody knows that, and many people avoid updating because they assume it would.

Tell them. Then offer the obvious thing: if the change is worth keeping, contribute it, and the
next update will *contain* it — at which point there is nothing left to preserve, and they can
update freely forever.

## What This Skill Does NOT Do

- Does not send anything without an explicit confirmation on the exact text.
- Does not certify that a diff is free of patient data — it narrows what the author must check.
- Does not push to the main repository (contributions arrive as a fork's pull request, or as an
  issue).
- Does not touch the user's manuscripts, data, or any file outside the installed skills.

## Anti-Hallucination

- **Never invent what a change does.** If the reason for an edit is unclear, ask. A pull-request
  description that guesses at the author's intent wastes a maintainer's time and misrepresents
  the author.
- **Never claim the safety scan proves anything.** It found no *known* pattern. Say exactly that.
- **Never fabricate a journal's rules** in a profile — word limits, abstract structure, and AI
  policy come from the journal's public author guidelines, quoted, or they do not go in.
