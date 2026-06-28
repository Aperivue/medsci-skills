# Slide Visual Style — Editorial Mono

High-contrast, magazine-style style for **single-message** slides: a keynote, an
opinion/perspective, or a big-result reveal. Oversized type carries the slide; one
accent color does the pointing. Maximum signal-to-noise. Use sparingly — best when the
deck has few slides each making one strong claim.

> **Triggered from**: SKILL.md Phase 3, Step 0b style menu. Implement via the generic
> builder tokens (`references/generate_pptx_templates.py`). Obeys
> `references/presentation_design_guidelines.md`.

## 1. Color palette

| Token | Hex | Usage |
|---|---|---|
| `INK` | `#111111` | Headlines, body, structure |
| `ACCENT` | `#C8102E` (red) *or* `#0050C8` (blue) | One emphasis per slide — pick one per deck |
| `BODY` | `#2B2B2B` | Body text |
| `MUTED` | `#6E6E6E` | Captions, footer |
| `RULE` | `#111111` | Thick rule under eyebrow/title (1.5–3 pt) |
| `BG` | `#FFFFFF` | Background (or `#FAFAF7` warm paper) |

**Restraint**: black + white + one accent. The accent appears on at most one word or
number per slide. No second accent.

## 2. Typography (type *is* the design)

| Role | Latin | Korean | Size | Weight |
|---|---|---|---|---|
| Hero headline | Inter Tight / Archivo | Pretendard | 44–60 pt | Black/ExtraBold |
| Title (content) | Inter Tight | Pretendard | 34–40 pt | Bold |
| Body | Inter | Pretendard | 24–28 pt | Regular |
| Kicker / eyebrow | Inter | Pretendard | 12–14 pt | Bold, ALL-CAPS, letter-spaced 400 |
| Footer | Inter | Pretendard | 9 pt | Regular |

Tight leading on multi-line headlines (line-spacing ~1.05). Big type → fewer words;
≤ 8 words per headline.

## 3. Layout
Shared 16:9 grid. Differences:
- **Generous top margin**; headline often vertically centered or upper-third with deep
  white space below (40–50% empty is on-brand here).
- Eyebrow over a **thick black rule** (not a thin hairline).
- Bullets are rare; prefer 1–3 short lines or a single number. Marker: en-dash `–` only.
- Big-number reveal: one figure at 80–120 pt `INK` with the accent on the unit/label.

## 4. Slide types
Title = hero headline on white, thick rule, small presenter line. Content = kicker → big
title → ≤3 lines or one figure. Closing = single sentence + the accent on the key phrase.
Section dividers optional (large number + word).

## 5. Figure handling
One figure, large, centered, hairline-free (let it sit on white). Caption: small muted
phrase. Redraw any journal table to ≤3 numbers.

## 6. Speaker notes
Because slide text is minimal, the **notes carry the substance** — keep them slightly
fuller (toward 300 chars), presenter-language, 13 pt, run-level markdown parser.

## 7. Mac compatibility
Run the `nature_lancet.md` §7 checklist. Verify the heavy display weights (Black/ExtraBold)
are installed or substitute Inter Bold to avoid Mac font fallback.

## Cross-references
- `references/presentation_design_guidelines.md` (§1 assertion headline, §2 24-pt floor)
- `references/generate_pptx_templates.py`; `~/.claude/rules/pptx-mac-compatibility.md`
