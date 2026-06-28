# Slide Visual Style — Clinical Blue

Calm, trustworthy, **colorblind-safe** style for hospital-facing talks: grand rounds,
tumor board, CME, guideline reviews. The clinical navy-teal-on-white palette is the
medical-presentation industry standard (signals sterility/trust) and avoids any
meaning-by-red/green. White slide body keeps it readable under bright OR-style lighting.

> **Triggered from**: SKILL.md Phase 3, Step 0b style menu. Implement by swapping the
> generic builder tokens (`references/generate_pptx_templates.py`). Obeys
> `references/presentation_design_guidelines.md` and the Mac-compat checklist.

## 1. Color palette (CVD-safe)

| Token | Hex | Usage |
|---|---|---|
| `INK` | `#0B3D62` | Primary text, titles, table header bg |
| `TEAL` | `#0E7C9B` | Accent — underline, key number, 1 use/slide |
| `TEAL_SOFT` | `#D8EBF0` | Alt table row, subtle panel |
| `BODY` | `#1F2933` | Body text |
| `MUTED` | `#5B6B7A` | Captions, footer, low-emphasis |
| `HAIRLINE` | `#C4D3DD` | Dividers, image border |
| `BG` | `#FFFFFF` | Background |
| `BG_TINT` | `#F4F8FB` | Optional very-light-blue background |
| `POS` / `NEG` | `#0072B2` / `#D55E00` | Good/bad when needed (Okabe–Ito blue/vermillion, **not** green/red) |

**Restraint**: white + ink + teal. Use `POS/NEG` only for a genuine good-vs-bad encoding,
and always with a label (never color alone).

## 2. Typography

| Role | Latin | Korean | Size | Weight |
|---|---|---|---|---|
| Title | Inter / Source Sans 3 | Pretendard | 30–34 pt | Bold |
| Subtitle | Inter | Pretendard | 16–18 pt | Regular |
| Body main | Inter | Pretendard | 24–26 pt | Regular |
| Body sub | Inter | Pretendard | 18–20 pt | Regular |
| Eyebrow | Inter | Pretendard | 11–13 pt | Bold, letter-spaced 300 |
| Footer | Inter | Pretendard | 9 pt | Regular |

Set the EastAsia attribute on every run (Mac falls back to Times otherwise —
`~/.claude/rules/pptx-mac-compatibility.md` §6).

## 3. Layout

Shared 16:9 grid (see `nature_lancet.md` §3). Differences:
- Title underline is a **teal hairline** (0.7" wide, 2.5 pt).
- Eyebrow in teal, all-caps, letter-spaced.
- Bullet markers: main `●` small teal disc + 24 pt body; sub `–` muted + 18–20 pt.
- Table: `INK` header row (white text), alternating `TEAL_SOFT` rows, ≤5×5.

## 4. Slide types
Same recipes as `nature_lancet.md` §4 (title, divider, content, table, closing). Section
divider uses a full-bleed `INK` background with a teal accent strip. Title slide: left
teal bar, ink title, muted subtitle.

## 5. Figure handling
Aspect-preserving fit; hairline border. For risk-of-bias / traffic-light figures keep the
`L/U/H` (or `+/−`) cell letters so the judgement survives grayscale and CVD
(`presentation_design_guidelines.md` §4).

## 6. Speaker notes
Presenter-language narrative, 150–300 chars/slide, 13 pt, run-level markdown parser.

## 7. Mac compatibility
Run the checklist in `nature_lancet.md` §7 (TIFF / sp3d / app.xml / markdown-in-notes).

## Cross-references
- `references/presentation_design_guidelines.md` — §4 color/accessibility
- `references/generate_pptx_templates.py` — generic builder (swap tokens)
- `~/.claude/rules/pptx-mac-compatibility.md`, `~/.claude/rules/academic-lecture-style.md`
