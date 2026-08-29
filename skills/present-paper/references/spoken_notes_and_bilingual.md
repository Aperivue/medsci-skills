# Notes that survive being read aloud — and decks in two languages

Two problems that only appear once a deck stops being a document. Speaker notes are **spoken**, not
read, and most prose that looks fine on the page jams the mouth. A deck for a domestic audience is
**bilingual**, and the choice of which language carries which part is not cosmetic.

Read this in Phase 2, before drafting notes, and again at Step 3.8 when the deck is rendered.

---

## Part D — Speaker notes are a script, not a summary

The Phase 2 rules already govern *what goes in* the notes: narrative not numbers, pronunciation for
drug names, timing markers. This section governs *how the sentences are built*, which is a different
failure. The notes can be entirely correct and still be unusable — because the presenter is reading
them under a clock, in a dark room, in front of two hundred people, and any sentence that needs a
second pass is a sentence that produces a stumble.

### 1. No markdown in the notes pane

`**강조**` renders **literally**. The presenter sees asterisks, reads around them, and the emphasis
is lost exactly where it was wanted. The notes pane has no formatting; treat it as plain text.

For emphasis, use a parenthetical stage direction, which the presenter reads as an instruction
rather than as content:

```
안 좋게 말하면, 사람이 조용히 실패합니다. (여기서 한 박자)
```

Same for `*italics*`, `` `code` ``, `#` headings, and `-` bullets — a bullet is fine as a visual
break inside long notes, but it is not markup and will not render as one.

### 2. Dashes are read by the eye and not by the mouth

An em dash and a colon-appositive both mean *"and here is the thing I actually meant"*. Written,
they are efficient. Spoken, they have no sound, so the presenter has to invent one mid-sentence.

| Written | Read aloud |
|---|---|
| 막힌 곳은 인프라와, 오류 메시지를 내지 않는 실패였습니다 — 그래서 게이트를 만들었습니다. | stumble at the dash |
| 막힌 곳은 두 가지였습니다. 인프라, 그리고 오류 메시지를 내지 않는 실패. 그래서 게이트를 만들었습니다. | reads clean |

The rewrite is always the same move: **break the sentence where the dash was.** If the two halves
cannot survive as separate sentences, the dash was hiding a claim that had not been thought through.

### 3. A list of fragments does not speak

Nominalised parallel lists read well and speak badly, because the listener has no verb to attach
them to and no cue for where the list ends.

> **Before** — 맞춰 달라, 만들어 달라, 도와 달라.
> **After** — 맞춰 줄 수 있느냐, 만들어 줄 수 있느냐, 하고 물어보시면 됩니다.

The general rule: **in notes, every item in a parallel series carries its own predicate**, even at
the cost of repetition. Repetition is invisible when spoken; ellipsis is not.

### 4. Check the first six words of every slide's notes

Notes get drafted one slide at a time, so each one independently reaches for the same opener. Four
consecutive slides that begin *"…하고 가겠습니다"* sound like a template even when the content is
entirely different, and the audience starts hearing the pattern instead of the argument.

Extract the openers and look at them as a column:

```python
for i, s in enumerate(prs.slides, 1):
    t = s.notes_slide.notes_text_frame.text.strip()
    print(i, " ".join(t.split()[:6]))
```

Any opener that appears three or more times, or twice in adjacent slides, gets rewritten.

### 5. Say each thing once

The same accretion produces the same duplication in the body: a definition given on slide 9 is given
again on slide 14 because slide 14 was drafted without slide 9 in view. Spoken, the second telling
reads as the presenter having lost their place.

Read the notes end to end as one document before the deck is final. Delete the second explanation of
anything, not the first.

### 6. The only test that works is reading it out loud

Not scanning it. Out loud, at speaking pace, once per slide. Every sentence that produces a stumble
is wrong regardless of how it looks in the pane — the stumble *is* the finding. This catches things
no rule above anticipates: an unpronounceable acronym string, a subordinate clause three levels
deep, a number that needs a unit spoken that is not written.

### 7. Practical: the notes only exist if the presenter can see them

Presenter view requires the speaker's own machine, or a venue that provides a confidence monitor.
Many society sessions collect slides in advance and run them from a house PC, where the notes are
invisible. Confirm this before investing in notes at all — and if the house PC is unavoidable, the
notes belong in a printed script or the lecture handout instead.

---

## Part E — English skeleton, local-language body

For a domestic academic audience, neither monolingual deck works. An all-English deck makes the
audience *read*; an all-Korean deck loses the terms the field actually uses and looks like a
translation of the field rather than the field itself.

The split that works:

| Element | Language | Why |
|---|---|---|
| Slide titles, section dividers | **English** | Titles are scanned, not read. English keeps them short and gives the deck a spine. |
| Table headers, axis labels, figure labels, numeric captions | **English** | These are read as symbols. They also match the figures, which are already English. |
| Technical and medical terms, anywhere | **English** | The word the audience uses in the reading room. Never translate `segmentation`, `harness`, `Dice`. |
| Subtitles, body text, callouts | **Local** | This is where the argument lives. |
| Speaker notes | **Local** | Spoken language. See Part D. |
| Lecture handout / 강의록 | **Local**, fuller prose | The handout is read; it can carry the sentences the slide could not. |

### The reason the body must be local

The force of a domestic talk lives in sentences the audience recognises as their own complaint —
*"매일 이것 때문에 짜증이 납니다"*, *"이건 아직 안 됩니다"*. Rendered in English, the same sentence
becomes something the audience decodes, and while they are decoding they are not listening. The
English skeleton costs nothing because nobody reads a title; the English body costs the talk.

Invert the whole table for an international meeting: full English deck, local language only in the
notes.

### Never put both languages on the same content

A bilingual label — `Reading room / 판독실` — doubles the reading load to convey one thing, and it is
one of the clearer signs that the deck was assembled rather than written. Choose per the table and
commit.

### Layout consequences

Mixed-script text does not behave like Latin text, and the differences are large enough to break a
layout that was tuned on English:

- **Korean is wider per character.** At the same point size a Korean line occupies substantially
  more width than an English line of the same character count, so a text box sized against English
  copy will wrap unexpectedly when the Korean goes in.
- **Korean wraps anywhere.** There are no word boundaries to protect, so a line breaks mid-phrase
  and leaves a one- or two-character orphan on its own line. This is the single most common way a
  bilingual slide looks careless.
- **Hard line breaks are how you control it**, and a hard-broken line that then soft-wraps produces
  exactly the orphan you were trying to prevent.

Do not try to predict any of this arithmetically — Step 3.8 records why estimators were removed from
this skill. **Render and look.** Export to PDF, rasterise to a contact sheet, and read the pages at
thumbnail size; orphan lines and overflow are visible there in one pass across the whole deck:

```bash
soffice --headless --convert-to pdf output/presentation.pptx --outdir output/
pdftoppm -png -r 60 output/presentation.pdf output/page
```

Fix by shortening the line or widening the box, then re-render. Two or three passes is normal and is
cheaper than any predictor.
