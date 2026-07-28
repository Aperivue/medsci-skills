# The marks an AI leaves on a deck — and how not to leave them

Read this **before drafting a single slide.** `check_slide_tells.py` catches these after the deck
exists. This file is so that the deck does not need catching.

---

## The thing being complained about is not ugliness

Reviewers now say roughly a third of the decks they receive were made by an AI, that they can spot
it instantly, and — this is the part that matters — that the tell is **not that the deck is ugly.**
Templates have solved ugly. The tell is that *the deck stops communicating*:

> "AI로 만든 슬라이드는 특유의 '쪼' 때문에 무슨 말을 하고 싶은 것인지 전달이 일단 잘 안 된다.
> 만드는 사람의 생각을 잘 읽을 수가 없음."

And the diagnosis behind it:

> "이건 읽는 사람에게 메시지가 잘 전달되기를 바라는 게 아니라, 그냥 '딸깍'으로 만드는 사람 자기가
> 편하기 위함인 것 같다."

That is the whole problem in one sentence. **A generated deck optimises the maker's comfort. A
presentation exists to serve the audience.** Every rule below follows from that, and any rule that
stops following from it should be deleted.

Investors are now telling their portfolio founders never to use AI for an IR deck. Not because it
looks bad — because it reads as *someone who has not thought about this yet*.

---

## 1. Scaffolding shipped with the building

A person thinking A → B → C → D does it in silence and writes down **D**. They do not narrate
themselves. A model thinking A → B → C → D says *"having completed B, I will now proceed to C"* —
and then leaves the sentence in the delivered work.

These are not thoughts. They are **the record of a thought being assembled**:

| The scaffolding | What it is |
|---|---|
| "핵심은 ~라는 점이다" | announcing that a point is coming, instead of making it |
| "요약하자면 / In summary" | narrating a stage of the process |
| "단순히 A가 아니라 B이다" | the shape of a reasoning move, performed as content |
| "이는 세 가지 층위에서 살펴볼 수 있다" | promising structure instead of delivering it |
| "이 글에서는 ~를 다룬다" / "This slide shows…" | the text describing itself (meta-sentence) |
| "요청하신 내용을 정리하면" | echoing the prompt back as the first line |
| "위에서 살펴본 바와 같이" | referring to the process, not the substance |

A human writer builds scaffolding too — and then **takes it down in revision**. It is the thing you
delete on the second pass. The AI hands over the building with the scaffolding still bolted to it.

**The rule: write D.** If a sentence's only job is to tell the reader what the next sentence is
going to do, delete it and let the next sentence do it.

**Test:** delete the sentence. If nothing is lost, it was scaffolding. (Every pattern in the
detector's bank passes this test — that is the admission criterion for the bank.)

---

## 2. The furniture along the edges

The little words at the top and bottom of every slide: the all-caps eyebrow label, the
`2026 · NEUROGENETICS` brand footer, the section tag, the running theme.

**This project used to mandate them.** `academic-lecture-style.md` required an eyebrow on *every*
slide and a brand footer on *every* slide, and `nature_lancet.md` gave them fixed coordinates. We
were manufacturing the single most-cited visual tell and calling it house style.

They are gone as a default. What survives:

- **the page number** — someone in Q&A says "go back to twelve", and they are right to;
- **chrome on the title slide and the section dividers**, where an orienting label is doing work.

Everything else was there because a template said so, and the audience has never once needed it.

---

## 3. The same box, eight times

A person draws the shape the idea needs. A generator reaches for the shape it has — usually the
rounded rectangle — and repeats it until the slide is full.

If five things are genuinely parallel, say so **once**, in a table or a list. If they are not
parallel, the shapes should differ, because the ideas differ. A row of identical boxes with
different words in them is a list wearing a costume.

---

## 4. Arrows are claims, and unlabelled arrows are arguments waiting to happen

> "다이어그램 요소별 상관관계는 매우 중요하고, 화살표 하나 잘못 그렸을 때 사람들마다 해석이 달라져서
> 대환장 혼란으로 이어지는 경우를 많이 봤음."

An arrow asserts something: **causes**, **becomes**, **flows into**, **is compared with**,
**predicts**, **is a subset of**. Six different claims, one glyph. Draw it without a label and every
person in the room supplies their own verb — and they will not supply the same one.

**Label every arrow, or put a legend on the diagram saying what an arrow means here.** No exceptions
in a scientific talk.

---

## 5. Diagrams and plots are drawn as CODE, then inserted

This is the single highest-yield rule in this file, and it comes from someone who kept trying:

> "에이전틱하게 PPT 도구를 사용하거나 / 웹페이지 형식으로 구성하는 경우는 거의 100% 실패함. 그나마
> 성공률을 높일 방법은 다이어그램 / 플롯을 모두 잘 알려진 도구(matplotlib 등)를 활용해 '코드'로
> 그리도록 시킨 다음, 그 결과를 그대로 삽입하도록 지시하는 방법인 듯."

So:

- **Plots** → matplotlib / R. Never hand-placed shapes pretending to be a chart.
- **Diagrams, flows, mechanisms** → matplotlib, or Graphviz DOT where the graph is the point
  (a DOT edge *has* to be written `A -> B [label="seeds along"]`, which forces the arrow to declare
  its meaning — the language will not let you draw rule 4's mistake).
- **Then insert the rendered PNG** (≥300 dpi) with `add_picture()`.

Drawing a diagram out of `python-pptx` autoshapes is how you get §3 and §4 at the same time. Do not
do it.

---

## 6. A vague brief produces a deck nobody can use — including you

> "적당히 '큰 주제'를 던져주고 만들라고 하면, 적당한 나도 모르고 / 청중도 모를 자료가 만들어지곤
> 하지만, 각 장표마다 내러티브 / 대본 수준으로 글을 정교하게 쓰면, 70~80% 수준의 원하는대로
> 발표자료가 완성되는 것 같다."

70–80% is the ceiling **when the brief is a per-slide script**, and it is far below that when the
brief is a topic. This is why Phase 2 (Script) comes before Phase 3 (Slides) and is not optional:
**if there is no per-slide narrative, there is nothing to build from, and the deck will be generic
in exactly the way everyone can see.**

And be honest about what 70–80% means to the person giving the talk:

> "기술자에게 20%가 어긋나는 것은 폭망이므로 … 그 20%를 조정하고, 뜯어 고치는 데 들어가는 시간은
> 직접 100% 만드는 시간보다 오래 걸리기도 한다."

So the skill's job is **not** to hand over a finished deck. It is to do the mechanical work
faithfully — the layout, the Mac-compat XML, the fonts, the notes, the figure cropping — and to be
loud about the parts it is not confident in, rather than smoothing them over. A confidently wrong
diagram costs more than no diagram.

---

## 7. What the audience actually wants

> "생각보다 청중들은 발표자료의 시각적 아름다움보다, 그냥 백지에 글자만 적어넣더라도 메시지가 잘
> 전달되는걸 더 선호한다."

If a choice ever comes down to *prettier* versus *clearer*, it is not a choice.

---

## The line this skill is trying to stay on

> "AI딸깍이냐, AI부스팅이냐 따라 차이는 엄청나지요."

**Button (딸깍):** topic in, deck out, nobody thought about anything, and everyone in the room can
tell.

**Booster (부스팅):** you decide what each slide must prove; the tool builds it faithfully, draws
the figures as code, keeps the arrows honest, handles the XML that PowerPoint for Mac will otherwise
corrupt, and tells you where it is unsure.

This skill is built for the second one and will keep asking you for the thing only you have.
