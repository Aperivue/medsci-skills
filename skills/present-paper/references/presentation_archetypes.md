# Presentation archetypes — the skeleton, chosen by where you are standing

A deck has two independent choices, and conflating them is why so many talks fail:

| | | |
|---|---|---|
| **Archetype** | *this file* | What the talk has to **do**, and therefore how it is built: what a slide is for, how many there are, how much can be on one, how the argument moves. |
| **Visual style** | `slide_visual_styles/` | What it **looks like**. Palette, type, grid. A skin. |
| **Content plan** | `medical_presentation_templates.md` | For the five *medical* venues only: the section-by-section plan, slide counts, design seed, pre-presentation checklist. |

**Do not read the content plan until the venue is known** — you need one of its five, not all five.
Archetypes A–D below are the same four medical venues; this file gives the **stance** (what the talk
must do, what fails), the template gives the **sections**. Where they overlap, this file wins: a
section list cannot tell you that a journal club which merely summarises the paper has failed.

A conference oral in a keynote's skeleton dies (no data on the slides; the reviewer in row three
came for the numbers). A keynote in a conference oral's skeleton dies harder (a 40-word slide read
aloud to 400 people who came to be moved). **The skin is a preference. The skeleton is not.**

Every archetype below is still subject to `ai_slide_tells.md` and `check_slide_tells.py`. There is
no venue where an unlabelled arrow is fine.

---

## Pick the skeleton

| Where you are standing | Archetype | Minutes | Slides | Words / slide | Skin |
|---|---|---|---|---|---|
| Society meeting, oral abstract (RSNA/ECR/KCR) | **A. Conference oral** | 8–12 | ≈ minutes | ≤ 40 | Nature/Lancet |
| Journal club | **B. Critique** | 20–40 | ≈ minutes | ≤ 50 | Nature/Lancet |
| Grand rounds, tumour board | **C. Case-anchored** | 30–50 | ≈ minutes | ≤ 45 | Clinical Blue |
| Residents, course, workshop | **D. Didactic** | 50–90 | ≈ minutes ÷ 1.5 | ≤ 40 | Clinical Blue / Nature |
| Thesis defence, job talk | **E. Defence** | 20–45 | ≈ minutes | ≤ 45 | Nature/Lancet |
| Invited keynote, plenary, big-idea talk | **F. Keynote** | 15–45 | free (often many) | **≤ 12** | Editorial Mono / Dark |
| Public / lay audience, TEDx, patient group | **G. Lay talk** | 10–20 | free | **≤ 12** | Editorial Mono |
| Investors, IR, grant panel, steering committee | **H. Decision brief** | 10–20 | **≤ 15** | ≤ 25 | Institutional / Editorial |

Ask two questions and the row falls out: **who is in the room, and what must be true when they
leave?** If you cannot answer the second one, no archetype will save the deck.

---

## The one pattern that holds everywhere

**Assertion-Evidence.** The headline is a **full-sentence claim**; the body is the **evidence for
it**, preferably a visual. Not "Results" — *"Adjunctive ablation halved local recurrence (12% vs
26%)."*

This is the only slide-design pattern in this file with **experimental support**: Alley & Neeley
(2005), and Garner & Alley's later comparisons, found sentence-headline + visual-evidence slides
beat topic-headline + bullet slides on comprehension and retention. Everything else here is craft —
good craft, from people who are very good at this, but craft. The distinction matters when you are
deciding what to argue with.

`check_slide_tells.py` enforces the negative half of it (`TOPIC_TITLE`).

---

## A. Conference oral (8–12 minutes)

**The room:** specialists, half of them planning their own talk, one of them your future reviewer.
They will remember **one** thing.

**The job:** land one finding, defensibly, and survive Q&A.

**Structure:** question → what you did (fast) → **the finding** → why it might be wrong → what it
changes. Methods are a service, not a performance: they exist so the finding is believable.

**Slides:** roughly one per minute. Every content slide is Assertion-Evidence. **One figure per
slide, and say what the figure shows in the headline.**

**Steal:** the Radiology/RSNA convention of a single "Advances in Knowledge" line — decide what it
is *before* you build the deck.

**Fails when:** you present the methods you are proud of instead of the ones needed to believe the
result; when the last slide is "Thank you" instead of the finding; when the figure has no headline
and you narrate it verbally (the recording, and the person looking at their phone, get nothing).

---

## B. Critique (journal club, 20–40 minutes)

**The room:** peers who have (mostly not) read the paper. They are here to learn how to *read*.

**The job:** not "summarise the paper" — **teach the appraisal**. The paper is the specimen.

**Structure:** the claim the paper makes → the design that would justify it → the design they used →
the gap → what would change your mind.

**Slides:** the paper's own figures, cropped (`scripts/trim_caption.py`), with **your** headline over
them, not the journal's caption. Your headline is the appraisal.

**Fails when:** it becomes a table of contents of the paper. If your deck could be produced by
someone who did not have an opinion, you did not do the job.

---

## C. Case-anchored (grand rounds, tumour board, 30–50 minutes)

**The room:** mixed specialty, mixed seniority. Someone has seen more of this than you.

**The job:** a real patient carries the argument; the evidence explains the patient.

**Structure:** present the case *cold* (no diagnosis) → the decision point → what the evidence says →
back to the patient → what you would do differently.

**Slides:** the imaging is the argument. Full-bleed, unannotated first (let them look), then
annotated. **The annotation is the second slide, not the first** — do not tell them what to see
before they have seen it.

**Fails when:** the case is a pretext for a review talk. The audience can feel the moment the patient
stops mattering.

---

## D. Didactic (50–90 minutes)

**The room:** trainees who will be tested, and who stop absorbing at ~15 minutes without a change of
mode.

**The job:** transfer a mental model, not a set of facts.

**Structure:** in blocks of 10–15 minutes, each ending in a question they answer (aloud, or by
hand). Glossary slide early if the audience is multidisciplinary
(`multidisciplinary-presentation.md`).

**Slides:** fewer than one per minute — a slide should *survive* several minutes of talking. This is
the one archetype where a dense slide is legitimate: they will photograph it, and they will study
from it.

**Fails when:** it is a conference talk stretched to fill the hour.

---

## E. Defence / job talk (20–45 minutes)

**The room:** deciding about **you**, not only about the work.

**The job:** show the arc of a research programme, and that you know where its edges are.

**Structure:** the question you chose and *why it was worth choosing* → what you did → what you
found → **what you got wrong and how you knew** → what you do next.

**Slides:** the limitations slide is not an obligation, it is your best slide. Pre-empt the
committee's objection and answer it before they raise it. Nothing convinces a panel faster than
watching someone attack their own result competently.

**Fails when:** limitations are a list of hedges nobody believes ("single-centre, larger studies
needed"). Name the *specific* thing that would falsify you.

---

## F. Keynote / big idea (15–45 minutes)

**The room:** came to be persuaded and moved. They will not take notes.

**The job:** one idea, felt.

**Structure — Duarte's sparkline:** what **is** → what **could be** → back and forth, widening the
gap → a **new bliss** at the end. Jobs did this on stage for a decade: the tension is the engine,
and the product is the resolution.

**Slides:** ≤ 12 words. Often one word, or one image, or nothing. Two disciplined extremes:

- **Takahashi method** — a few enormous words per slide, changing fast. The slide is punctuation.
- **Lessig method** — rapid-fire, tightly synchronised to speech, one beat per slide.

**Steal from Jobs:** the STAR moment (Duarte: *Something They'll Always Remember*) — one engineered
instant the room will repeat afterwards. Also: he rehearsed for **days**. The apparent effortlessness
is the most expensive thing on that stage, and a generated deck cannot fake it.

**Fails when:** a scientific audience wanted the numbers and you gave them a mood. **Do not use this
skeleton for an oral abstract.** If you need both, put the data in a handout or a backup section, and
say so.

**Honesty:** the evidence base here is "these talks worked". That is not nothing, but it is not
Alley's experiment either.

---

## G. Lay talk (10–20 minutes)

**The room:** patients, journalists, students, the public. They do not have your vocabulary and they
do not owe you their attention.

**The job:** one true idea they can repeat to someone else tonight.

**Structure:** a concrete person or object first, abstraction second — never the reverse. Heath's
*Made to Stick*: concrete beats abstract; unexpected beats comprehensive.

**Slides:** images, ≤ 12 words, no axis labels smaller than the punchline. If a chart needs a legend,
it needs a different chart.

**Fails when:** you "simplify" by deleting the caveats instead of by choosing a smaller claim. That
is not simplification, it is a false statement with a friendly tone.

---

## H. Decision brief (investors, grant panel, steering committee, 10–20 minutes)

**The room:** deciding whether to give you something. They are busy, sceptical, and reading ahead.

**The job:** make the decision easy to make. **Answer first.**

**Structure — Minto's pyramid / SCQA:** Situation → Complication → Question → **Answer**, then the
support beneath it. The answer goes at the top, not at the end. A scientific talk earns its
conclusion; a decision brief *opens* with it and spends the rest defending it.

**Slides:** ≤ 15. **Action titles**: every headline is the sentence you want them to carry out of the
room, and the deck read as titles alone must be the complete argument. (Consulting calls this the
"ghost deck" test — write the titles first, in order, before any content exists. If the titles do not
argue, the deck will not either.)

**Kawasaki's 10/20/30** — 10 slides, 20 minutes, 30-point minimum type — is folklore, and it is
folklore that has survived contact with a great many pitches.

**Fails when:** you build suspense. Suspense is a gift you give an audience that wants to be
entertained; an investor experiences it as evasion.

**Special warning for this archetype.** Investors now report telling their portfolio founders **never
to use AI for an IR deck** — and it is not about looks:

> "만드는 사람은 효율적이라고 느낄지 모르겠으나, 슬라이드를 만드는 목적을 달성하기 위해 결코
> 효과적이지는 않음."

The deck *is* the evidence that you have thought about the problem. A generated one is evidence of
the opposite, and the person reading it does this all day.

---

## The trade you are making, per archetype

| Archetype | Slide carries | Speaker carries |
|---|---|---|
| A, B, C, D, E (academic) | the evidence — it must stand alone in the recording | the interpretation |
| F, G (keynote, lay) | almost nothing — a beat | everything |
| H (decision brief) | the whole argument — they will read it without you | emphasis |

**Ask which column your slide is in.** Most bad decks are a slide from one column being spoken as if
it were in another.

---

## Composing with the rest of the skill

1. **Archetype** (this file) → the skeleton, the slide budget, what a headline is for.
2. **Visual style** (`slide_visual_styles/CATALOG.md`) → the skin. Any skin fits any skeleton;
   the table above is a default, not a rule.
3. **Medical context template** (`medical_presentation_templates.md`) → the section-by-section
   content plan for the five medical venues.
4. **`ai_slide_tells.md`** → applies to all of them, without exception.
5. **`check_deck_budget.py --archetype <X> --minutes <N>`** → the mechanical half of this file:
   slide count against the clock, words per slide, type-size floor. It knows the table at the top.

The archetype changes what "too much text" *means*. Forty words is a normal academic slide and a
catastrophic keynote slide. That is why the check takes an archetype and not a universal threshold —
a single global rule for "words per slide" would be wrong for most of this table.
