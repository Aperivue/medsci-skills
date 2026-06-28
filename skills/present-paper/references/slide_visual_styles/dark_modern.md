# Slide Visual Style — Dark Modern

Sharp, contemporary dark-mode style for **AI / method / technical** talks and low-light
auditoria. On a deep slate background, colors pop and figures with dark backgrounds
(heatmaps, attention maps, 3-D renders) sit naturally without a white box around them.
Keep it disciplined — dark mode amplifies clutter as much as it amplifies signal.

> **Triggered from**: SKILL.md Phase 3, Step 0b style menu. Implement via the generic
> builder tokens (`references/generate_pptx_templates.py`). Obeys
> `references/presentation_design_guidelines.md`.

## 1. Color palette

| Token | Hex | Usage |
|---|---|---|
| `BG` | `#0E1116` | Slide background (deep slate) |
| `BG_PANEL` | `#171B22` | Card/table panel on background |
| `TEXT` | `#E8EAED` | Primary text (off-white, not pure white — less glare) |
| `MUTED` | `#9AA4B2` | Captions, footer, secondary |
| `ACCENT` | `#4DA3FF` (electric blue) *or* `#5EE0B0` (mint) | Key emphasis, underline, 1 use/slide |
| `HAIRLINE` | `#2A313B` | Dividers, table grid |
| `WARN` | `#E0A33E` | Use with a label only (not red/green encoding) |

**Contrast**: off-white on slate exceeds 4.5:1 (`presentation_design_guidelines.md` §7).
Avoid pure-white text (glare) and avoid dark-gray-on-black body (fails contrast).

## 2. Typography

| Role | Latin | Korean | Size | Weight |
|---|---|---|---|---|
| Title | Inter / Space Grotesk | Pretendard | 30–36 pt | SemiBold/Bold |
| Subtitle | Inter | Pretendard | 16–18 pt | Regular |
| Body main | Inter | Pretendard | 24–26 pt | Regular |
| Body sub | Inter | Pretendard | 18–20 pt | Regular |
| Eyebrow | Inter | Pretendard | 11–13 pt | Bold, ALL-CAPS, letter-spaced 300, accent color |
| Footer | Inter | Pretendard | 9 pt | Muted |

## 3. Layout
Shared 16:9 grid. Differences:
- Title underline = **accent hairline** (glows against slate).
- Bullet markers: main `▸` accent + 24 pt text; sub `·` muted.
- Tables: `BG_PANEL` fill, `HAIRLINE` grid, accent header text; alternating rows are a
  hair lighter than `BG_PANEL`, not white.

## 4. Slide types
Title = accent eyebrow + off-white hero title on slate + presenter line. Section divider =
even darker band (`#0A0D12`) + large accent number. Content / table / closing as in
`nature_lancet.md` §4 with the dark tokens.

## 5. Figure handling
Dark-background figures (heatmaps, traffic-lights, embeddings) sit directly on the slate.
**White-background figures (PRISMA flow, line charts) need a white card** (`#FFFFFF`
rounded rectangle) behind them — never place black-on-white line art directly on slate.
Keep RoB traffic-light `L/U/H` letters for CVD/grayscale safety.

## 6. Speaker notes
Presenter-language narrative, 150–300 chars/slide, 13 pt, run-level markdown parser.

## 7. Mac compatibility
Run the `nature_lancet.md` §7 checklist. Additionally confirm the **slide background**
fill is set per slide (a missing background renders white on some viewers); verify on Mac
PowerPoint + PDF export.

## Cross-references
- `references/presentation_design_guidelines.md`; `references/generate_pptx_templates.py`
- `~/.claude/rules/pptx-mac-compatibility.md`, `~/.claude/rules/academic-lecture-style.md`
