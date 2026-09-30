---
name: contribute
description: Use when sending local changes back to the project (an added journal profile, a fixed checklist item, an adapted skill) or reporting a false positive or bug. Finds what changed, scans it for patient data, shows every line and sends nothing until you confirm.
model: sonnet
metadata:
  triggers: "contribute, 기여, send my changes, share my edit, report a false positive, feedback, my journal is missing, open a PR, pull request, 오탐 신고, report a bug"
---

# Contribute

The user is a **clinician** who has probably never opened a pull request. Do the git work for
them: never make them type a git command, and never use the words "rebase", "upstream", or
"HEAD" in anything they read. Their local edits sit next to real patients and real manuscripts,
so the safety steps below, not the git mechanics, are why this is a skill.

## The one rule that cannot bend

**Nothing leaves the machine until the author has seen every line that would leave it and said
yes.** Until something has been sent, say explicitly, every time, that nothing has been sent.

The safety scan is an aid, not a certificate: no pattern list recognises every patient name or
every hospital. Say so out loud, because a user who believes the scanner is complete stops
reading the diff, and that is exactly when the leak happens.

If the scan reports a **blocker** (patient-level data, a credential), do not offer a workaround.
The line gets deleted. A contribution never needs patient data to make its point.

## Phase 0: What did they change?

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/find_local_changes.py" --target claude --json \
  --out qc/local_changes.json
```

This compares the installed skills against the hashes of what was shipped. It reads only.

- **Nothing changed** → say so plainly and stop; that is normal, not a failure. Offer the
  feedback path (Phase 4) instead.
- **Something changed** → show it, grouped by skill:
  - **A new file** (a journal profile, a citation style, a reporting exemplar) — usually the most
    valuable kind of contribution, because it is domain knowledge nobody in the project has. Say that.
  - **An edited file** — ask what was wrong for their specialty; the answer is the pull-request
    description. Never guess at the reason for an edit.
  - **A deleted file** — usually not a contribution. Ask before including it.

A change that only makes sense in one hospital (internal rules, a template with the department's
letterhead) is a local adaptation, not a contribution: say so, leave it out, and tell them keeping
it is fine.

## Phase 1: The safety scan (blocking)

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/check_contribution_safety.py" \
  --changes qc/local_changes.json --out qc/safety.json
```

This gate **fails closed**: finding anything at all is a non-zero exit, unlike every other
detector in the repository — deliberately, because a tool that returns success while printing a
hospital name will eventually be trusted to have said nothing.

Verdicts: `PHI_SUSPECTED`, `SECRET` (**blockers — the line is deleted, not argued with**),
`IDENTITY`, `INSTITUTION`, `APPROVAL_ID`, `MANUSCRIPT_ID`, `LOCAL_PATH`. Fix each finding *with*
them, following the `do` line the scan prints for it (a name → a role, a hospital → a generic
descriptor, an IRB or manuscript ID → removed, a home path → `~`). A manuscript ID matters because
a paper under review is confidential and its ID identifies it.

Then **print the full text of every file that would be sent** and ask them to read it. Not a
summary — the text. This is the step that actually protects them.

## Phase 2: Does it meet the project's own bar?

Run the repository's validator against the change if the repo is available locally; otherwise
check by eye:

- A journal profile cites the journal's **public author guidelines**: word limits, abstract
  structure and AI policy are quoted from them or left out. No impact factors or numbers from memory.
- A citation style is the **official** CSL from the Zotero repository.
- A skill edit still says what it does, and the change is general — it would help someone at
  another hospital. If not, it is a local adaptation; keep it local.

If it does not pass, say what to change, in their words. Do not send a contribution that will be
rejected — that is a worse experience than not contributing at all.

## Phase 3: Send it

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/submit_contribution.py" \
  --changes qc/local_changes.json --safety qc/safety.json \
  --title "Add a journal profile for <journal>" --dry-run
```

**Always `--dry-run` first**, and show them the plan. Then, on their explicit yes, run it again
without `--dry-run`. The script takes the highest rung available:

1. **GitHub tool installed and signed in** → it forks, copies the files, and opens the pull
   request. They type nothing.
2. **Installed but not signed in** → it prints the single command (`gh auth login`) and stops.
   Walk them through it: GitHub.com → HTTPS → log in through the browser.
3. **Not installed** → it writes the change to a file and opens a pre-filled issue in their
   browser. Do not make installing a developer tool a condition of helping.

Tell them what happens next: a maintainer reads it, and if something needs changing they can
reply **in plain language on that page**. They will not be asked to do any git work.

## Phase 4: Feedback that is not a code change

A false positive or a failed step is often the most useful thing a clinician has: it is the only
evidence of how a detector behaves on a real manuscript rather than a synthetic fixture. Collect:

- **A detector fired wrongly**: which detector (the `detector` field in its `qc/*.json`), the
  verdict, and the **smallest possible** snippet that reproduces it — rewritten with fake numbers
  and names if the real one cannot be shown; the *shape* of the sentence is what matters.
- **A step failed**: the command, the error, the host (Claude Code / Codex / Cursor / Copilot),
  the operating system.
- **Something was wrong for your specialty**: what the toolkit assumed, and what is actually true.

Send it as an issue, after the same safety scan — a repro from a real manuscript is exactly where
PHI hides:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/check_contribution_safety.py" --text qc/feedback.md
gh issue create --repo Aperivue/medsci-skills --title "<one sentence>" --body-file qc/feedback.md --web
```

`--web` opens it in the browser pre-filled: they read it and press Submit. Nothing is sent by us.

## Phase 5: Keep their change when they update

Tell them the installer already takes a **permanent backup** of any skill they modified before
it overwrites it (under `~/.medsci-skills/backups/`), so updating never destroys their work —
many people avoid updating because they assume it would. If the change is worth keeping,
contributing it means the next update will *contain* it.

## Settings — nobody is nagged

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/contribution_prefs.py" --status
python3 "${CLAUDE_SKILL_DIR}/scripts/contribution_prefs.py" --on    # remind me
python3 "${CLAUDE_SKILL_DIR}/scripts/contribution_prefs.py" --off   # never mention it (default)
```

- Reminders are **opt-in and off by default**. The installer mentions the option once, at the
  end of a first install, and never again. Opted in, a reminder appears only when they actually
  changed something, and at most once a month.
- The setting governs **reminders only**. `/contribute` works whenever it is run.
- The setting **cannot weaken safety**: there is no key for that, and
  `check_contribution_safety.py` reads no configuration. Opting in never means "send without asking".

## Saying thanks

Many clinicians who find this useful have never starred the repository because nobody told them
what a star is for. Once the toolkit has actually done something for them, tell them — the
script explains what a star is and makes it one command:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/star_repo.py" --how   # explain + show both ways
python3 "${CLAUDE_SKILL_DIR}/scripts/star_repo.py" --now   # do it from here (GitHub CLI)
```

- **Never ask twice** — being shown once is recorded, and doing nothing is an answer.
- Never dress this up: do not imply the toolkit is worse off without their star, and do not ask
  before the toolkit has done something for them. Asking for thanks in advance is begging.

## Scope

Touches only the installed skills — never the user's manuscripts, data, or any other file.
Contributions arrive as a fork's pull request or an issue; never push to the main repository.
