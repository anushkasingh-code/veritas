# DESIGN.md

Working title: **Veritas** (rename freely). Product: paste a claim, watch 5 agents split it, search, verify, and cross-check it. The UI is the evidence, not a chat box.

## Concept: the cyanotype wall

A blueprint-blue drafting surface. Claims are drawn on it in white line. Sources are translucent tracing-paper slips pinned beside each claim. Verdicts are rubber stamps. Contradictions are red thread pulled tight between two slips.

The one memorable thing: **claims "develop" like a cyanotype print while agents work, then a stamp lands.** Everything else stays quiet.

## Tokens

Color (CSS variables on `:root`; no other colors):
- `--ground` #0E3A78 (cyanotype blue, page background)
- `--ground-deep` #08234D (panels, report drawer)
- `--line` #EAF2FF (primary linework and text)
- `--line-dim` #7FA3D6 (secondary text, guides, grid)
- `--stamp-red` #E5482F (REFUTED, contradiction thread, errors)
- `--hold` #F2B84B (INCONCLUSIVE only)
- `--slip` rgba(246,248,251,0.92) with `--slip-ink` #0B1B3A (source slips)

Background: `--ground` plus a faint drafting grid (1px `--line-dim` at 10% opacity, 32px cells). No gradients, no glass, no shadows except a 1px offset hard shadow under slips.

Type (Google Fonts, with fallbacks):
- Display: **Big Shoulders Display** 700/800, for claims and headings. Tight tracking, sentence case.
- Text: **Newsreader** 400/500, for evidence snippets, reasoning, report. Line-height 1.55, max 68ch.
- UI controls: Newsreader 500. No monospace anywhere.
- Scale: 14 / 17 / 22 / 32 / 56 px. Claim text 32px display.

Shape: slips are square-cornered (0 radius). Stamps rotate -4 to +3 degrees, never the same angle twice. Only the input frame has corner registration marks (small L-shaped ticks), nothing else is decorated.

## Verdict encoding (never color alone)

- SUPPORTED: solid `--line` filled stamp, `--ground` text.
- REFUTED: `--stamp-red` double-border stamp with a diagonal strike bar.
- INCONCLUSIVE: dashed `--hold` outline stamp, no fill.
Stamp text is the verdict word in caps (the only all-caps text in the UI). Confidence shows as a row of 10 small ticks, filled = round(confidence*10), plus the number ("0.82").

## Layout

Three states in one page, no routing.

1. **Intake**: a single wide input frame (registration marks at the corners) vertically centered-left. Big placeholder in display type. One button: "Check this". Under it, three example claims as plain text links. No hero, no feature list, no logo cloud.
2. **Wall** (while running and after): left rail is the pipeline, a vertical drafting-style line with 5 nodes (Claim extractor, Search retriever, Fact verifier, Contradiction detector, Report generator). Active node pulses once per second; done nodes are solid. Main area is a horizontally scrolling wall of claim columns: each column = claim text (display), stamp, confidence ticks, reasoning, then its source slips stacked below. A full-width SVG layer behind draws red thread between conflicting slips.
3. **Report**: "Read the report" opens a right drawer (`--ground-deep`, 560px) rendering `report_markdown`. Esc closes. Headings in display type.

```
+--rail--+-----------------------------------------------+
| o      |  claim 1          claim 2          claim 3    |
| |      |  [STAMP]          [STAMP]          [developing]|
| o      |  ||||||||..       |||||.....                   |
| |      |  reasoning...     reasoning...                |
| *      |  [slip]--red------[slip]                      |
| |      |  [slip]           [slip]                      |
| o      |                                  [Read report]|
+--------+-----------------------------------------------+
```

Alignment: everything left-aligned. No centered paragraphs.

## Motion (spend it here only)

1. **Develop**: when `claim_extractor done` arrives, each claim fades from 0 to full opacity with a blur(6px)->0 and a brightness ramp over 900ms, staggered 150ms. Claims with no verdict yet stay slightly "underexposed" (opacity 0.65).
2. **Stamp**: when a claim gets a verdict, the stamp scales 1.6->1 with a 140ms ease-in and a 2px shake. One time per claim.
3. **Thread**: contradictions draw their red path with stroke-dashoffset over 700ms.
All other state changes are instant. Respect `prefers-reduced-motion` (no blur/scale/shake, just appear).

## Copy rules

Sentence case. Plain verbs. Button: "Check this". Running: "Reading sources for claim 2 of 5" style status in the rail. Empty: "Paste a claim or a question. Veritas splits it into statements and finds sources for each." Errors say what failed and what to do, no apologies: "The search step timed out. Try again, or shorten the claim."

## Banned

Purple/blue-violet gradients, glassmorphism, rounded-xl cards, identical card grids, emoji icons, Inter/Roboto/system-ui as the visible face, centered hero with subtitle, all-caps eyebrow labels, "01 / 02 / 03" markers, spinner-only loading states, chat bubbles, fade-up-on-scroll on sections, hover lift on cards, a footer.

## Quality floor

Responsive: on <800px the claim columns stack vertically and the rail becomes a top bar. Visible keyboard focus (2px `--line` outline, 3px offset). Contrast AA on all text. Stamps have `aria-label` with verdict and confidence.
