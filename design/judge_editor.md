# Judge: design editor

Panel judgement on `concept_a.md` (Journal companion), `concept_b.md` (Atlas) and `concept_c.md` (Narrative Map), 2026-10-17. Lens: a design editor at a serious publication, judging typography, hierarchy, restraint, delight, and whether the design still looks right when the data changes and grows.

Before scoring I checked the concepts' load-bearing claims against the real files rather than taking them on trust.

## What the data says

- `taxonomy.json`: section titles run to 31 characters ("Training for Control Properties"), subsection titles to 38 ("Representation Training and Unlearning"). A 264 to 280 px rail at 14 to 17 px cannot hold these on one line; it must wrap, not truncate.
- `papers.json`: 1,788 items, subsections from 1 (11.5) to 103 (8.2), median 25.5. Labels at most 27 characters (median 21), titles to 176 (median 75), one-liners empty for 149 papers but `reason` present for every paper. Cross-reference load peaks at 40 (3.2), 37 (2.2), 36 (2.4), 35 (10.1). Years: 908 of 1,788 are from 2026; 95 are 2022 or earlier.
- `summaries_zh.json`: 239 entries; 227 have exactly four 发现; 术语 lists run 5 to 10; depth is 部分 171, 全文 55, 仅摘要 9, 仅题录 4.
- `grey.json`: 174 items, 153 verified, 19 "existing bib entry", 2 "likely"; venue strings up to 111 characters.
- The stream is empty today (`stats.json` has `stream_items: 0`, no `stream.json`). The seed sweeps hold 279 candidates dated 2024-02 to 2026-10 across 32 months, at most 28 in one month (2025-08). Seed titles are median 95 characters (max 136); seed summaries are median 503 characters (max 857), far longer than the schema's "two factual sentences". Whatever wins, stream rows must be sized for 500 characters or the pipeline must trim.
- Contrast on white (computed, WCAG): gray `#7D7D7D` 4.12:1 (fails AA for small text). Raw tokens: coral 3.94, terracotta 3.04, blue 3.41, purple 3.47, periwinkle 3.13, forest 3.07 pass 3:1 as marks; amber 2.37, teal 2.11, gold 1.99, sand 2.29, sky 1.83 do not. Token mixed 70 % with ink: amber 3.77, teal 3.42, gold 3.26, sand 3.67, sky 3.06, all below 4.5. Token mixed 60 % with ink: 5.4 to 6.6 except amber 4.49, teal 4.11, gold 3.93; at 50 % all pass. On ink, every token passes 3:1 as a mark and token mixed 65 % with white gives 5.6 to 9.2 as text.

Concept C's contrast table is accurate to a tenth. Concept A's "gray is about 4.1:1" is accurate. Concept B's rule that "token 70 % with ink" fixes coloured text is false for five tokens, and B assigns `--text-muted: gray` to 13 px authors and keywords while also promising a test script that fails anything under 4.5:1. The script would fail B's own cards.

## Scores

Scale 1 to 10 per criterion; total is the sum of seven.

| Criterion | A Journal | B Atlas | C Narrative Map |
|---|---|---|---|
| Clarity (five seconds, two parts) | 8 | 9 | 8 |
| Credibility (deployers, security researchers) | 9 | 7 | 8 |
| Delight (fancy without gimmicks) | 7 | 8 | 8 |
| Vocabulary fit (terms and colour tokens, functionally) | 9 | 7 | 8 |
| Feasibility (vanilla, performance, researcher-maintainable) | 9 | 7 | 7 |
| Papers usability (1,788 papers by 56 subsections) | 9 | 9 | 8 |
| Stream usability (daily reading and filtering) | 7 | 8 | 6 |
| **Total** | **58** | **55** | **53** |

## Concept A: Journal companion

The strongest typographic idea of the three and the only one that treats the paper's table of contents as the object of the site. The front-page spread (contents left, ledger right, equal running heads, one hairline) is a genuine editorial device, not a layout; the two halves speak two colour languages (section rules left, polarity dashes right), which is the clearest possible answer to "what are the two parts". The mark-shape system (square for operation and section, circle for failure source, dash for polarity) is the single best piece of visual thinking across all three concepts, because coral is shared by polarity bad, failure source mistakes and Section 2 and only shape can keep them apart. Muted text set in ink rather than gray is correct and shows the author measured. Cross-referenced papers collapsed under "Also placed here (40)" is sized for 3.2's actual load. Reports and posts show `confidence` only when it is not "verified", which handles the 21 non-verified grey items without shouting. The growth story is the best: the contents column is eleven rows forever, the ledger shows the twelve most recent at any N, the chronology strip is a column histogram that degrades gracefully when a month holds 200 items, and the author truncation, two-line title clamp and "+3" chips absorb every outlier in the corpus. The cut order is honest and none of the cuts touch the signature moments.

Weakest point. The landing is quiet to the edge of plain. Above the fold there is a serif title, a dek, three text buttons and a two-column list; colour appears only as 3 px rules and 3 px dashes, and the only pictures are the two rasters below the fold. The user has already pushed back on a monochrome-leaning design once (the InkPaper review), and asked for "fancy"; A's fanciness lives entirely in Newsreader rendering well and in the spread, and if the web font fails the page is a Georgia document. Second: on the stream page a collapsed ledger row carries the full summary in Newsreader 16/24; with seed summaries at 500 characters that is seven to nine lines of serif per row, which turns a daily scan into a read. Third: in the light theme A's amber, teal and gold marks sit at 2.4, 2.1 and 2.0 to 1 with no outline; a "mixed" polarity dash in gold will be nearly invisible on white. A acknowledges the dark-theme case and misses the light one. Fourth: the catalogue card leads with the label at Newsreader 20 and demotes the title to Inter 14; labels such as "Governable Agentic SE" are opaque without the title, and the 20 to 14 step is too steep. Fifth: the card simply shortens when `one_line` is empty, throwing away `reason`, which every paper has.

## Concept B: Atlas

The clearest five-second read: two entry cards with eyebrows PART ONE and PART TWO, big numerals, distinct accents, verb buttons. The mechanism map as a real `<button>` grid that filters both collections is the most memorable interaction proposed by anyone and is content-true, since it is the paper's own Figure 2. B is also the best on the papers page in several particulars: the search widens to the whole corpus and offers a "within 5.2 only" chip to narrow back; rail counts go live ("12 / 70") while filters are active; a card with no one-liner shows `reason` as "Why here:"; author lists from 50 names show one name and "and N more"; the drawer has previous and next with j and k and "12 of 70". On the stream it has "Recently verified" as a sort, a stale-collector note, and "Report a problem" per item with the id prefilled. The JSON cache-busting with `?v=<generated>` is a small thing that will save a real bug.

Weakest point. Restraint. The landing stacks a title band with thesis, two entry cards each holding four stat tiles plus a sparkline or a strip plus a polarity bar plus a one-liner plus two buttons inside 280 px, then a 540 px mechanism map with a two-column readout, then three failure-source tiles (which repeat the map's top row), then a 56-row table (which repeats the readout), then a six-card "latest" grid (which repeats the entry card's strip), then a four-column footer. That is four indexes to the same 56 subsections on one page, and the hierarchy has to be strict because nothing else is. It reads as a product dashboard with stat tiles and sparklines, and for a security audience that register is weaker than a journal's. Second: the colour rules are contradicted by the numbers, as set out above; `--text-muted` gray at 13 px fails AA, and the 70 % variants fail for Intervene amber, Steer teal, mixed gold, grey-item sand and 中文 sky. Third: on the stream page coral means "mistakes" on the timeline squares and "bad" on the card rules, the exact collision A's mark shapes exist to prevent. Fourth: the timeline draws one 8 px square per item; it is the least growth-stable device on the panel (B caps stacks at 12 and admits a split at 1,500 items), and the 48 px landing strip cannot hold six rows of 8 px squares plus gaps for a busy month. Fifth: a 560 px drawer that pushes the main column at 1440 leaves roughly 550 px for cards that were 760 px wide; the list reflows every time a paper is opened.

## Concept C: Narrative Map

The most delightful landing and the one most likely to be remembered: the hero retells Figure 1(a) as an inline SVG (capability steps rising, human review flat, the control gap labelled), and the two doors are the only two large numbers on screen, each with a verb and a bar in the right colour language (11 section segments for the papers, 3 polarity segments for the stream). The story beats make the taxonomy navigable as an argument. C has the most correct URL scheme (filters in the query string, entity in the hash, so filters survive reload and Back closes a drawer) and one `linkTo()` helper for every cross-page link. The contrast table is measured and right, including the move of amber, teal and gold to 50 %. The live indicator is the most honest on the panel: gold after 48 hours, coral after 7 days with "Collector stalled since", and a "New" dot on items verified in the last seven days. `content-visibility: auto` on cards, the "2022 and earlier" year bucket, English hints beside the four depth badges, and the risk list that puts its own sticky stage first in the cut order all show judgement.

Weakest point. The stream, which is half the site. A three-column wall of cards with titles clamped at three lines and summaries clamped at three lines is the aggregator pattern: seed titles are median 95 characters and summaries median 500, so most cards will cut a headline or a sentence mid-way, and reading any item costs a drawer open. Chronology zigzags across three columns, so "which is newest in this row" is never obvious; a daily reader wants one column, newest at top, expand in place. Second: the sticky three-state stage is the most code and layout risk of anything proposed, and its SVG groups contain live links that will remain tabbable while faded unless also made inert, which the concept does not say. Third: coral acquires a fourth meaning in the hero as the human-review-capacity line. Fourth: the rail truncates section titles to one line at 264 px, which with 31-character titles means ellipses in a table of contents. Fifth: the register (14 px radii, pill controls, hover lift, breathing dot) is web-app rather than paper, and the lift and the breathing dot are the two touches a strict editor would call gimmicks.

## Verdict

**Winner: Concept A, Journal companion**, by 58 to 55 to 53.

A wins on the four things this lens weighs most: typography carries the hierarchy, colour is kept for meaning and disambiguated by shape, nothing on the page competes with the two parts, and every element has a stated behaviour for the corpus's real outliers and for a stream of any size. It loses on delight, and the user has asked for fancy. The right final spec is therefore A's skeleton and type system with a disciplined set of grafts from B and C that add exactly the colour, the one interactive diagram and the daily-reading affordances A lacks, without importing B's dashboard density or C's wall.

## Graft list (carry into DESIGN.md)

From B:

1. "Why here:" fallback. When `one_line` is empty (149 papers) the card shows `reason` in muted italic instead of shortening.
2. Search that widens. Keep A's "Also 41 matches in the whole corpus" line, and when the scoped result is empty or small, show whole-corpus results grouped under section heads with a "within 5.3 only" chip to narrow back.
3. Live rail counts "12 / 70" while filters or a query are active.
4. A 1 px outline of `color-mix(in srgb, <token> 70%, var(--ink))` on small coloured marks in the light theme so amber, teal and gold marks reach 3:1. Keep raw tokens in the dark theme, where all pass.
5. A contrast test in `pipeline/tests/` that computes ratios for every text and mark role in both themes. Use A's roles (muted is ink) so the test passes.
6. "Recently verified" as a stream sort, and the stale-collector note, merged with C's graded staleness (gold past 48 hours, coral past 7 days, "Collector stalled since <date>").
7. "Report a problem" on each expanded stream row, opening the issue template with the item id prefilled.
8. Drawer previous and next within the current result list, keys j and k, "12 of 70"; `/` focuses search on Papers and Stream.
9. Author truncation for 50 or more names: first name and "and N more" (the 265-author system card).
10. The mechanism map as one interactive plate on A's landing, taking the place of the Figure 2 raster: a CSS grid of plain links (no roving tabindex), two lever rows, Verify tall at right, Deploy and Assure as the base bar, How Agents Fail as a thin coral row above, each node tinted 14 % in its section colour and showing its paper count and stream count, linking to `papers.html#sN`. No readout beneath. This supplies the colour and the one "fancy" moment A lacks, in the paper's own figure.
11. `?v=<generated>` on every JSON fetch so GitHub Pages never serves a stale stream.
12. The 56-row table with Primary, Cited, Cross, Grey and 中文 columns, placed on the About page under The Paper Collection rather than on the landing.

From C:

13. The two signature bars under the spread's running heads: an 11-segment bar in section colours proportional to `stats.per_section` under THE PAPER COLLECTION, and a 3-segment polarity bar under THE LIVE STREAM. One compact colour signature per half; the "two colour languages" made visible at a glance.
14. A "New" dot on stream rows whose `verified_on` is within seven days, and the same dot on the Stream link in the masthead when `stats.stream_updated` is within seven days.
15. Filters in the query string, entity in the hash (`papers.html?q=monitor&cited=1#paper/han2024wildguard`), with one `linkTo(page, state)` helper so no page hand-builds a URL. A's hash grammar with `?` inside the hash is workable but non-standard and does not survive a reload cleanly.
16. `content-visibility: auto; contain-intrinsic-size: 0 150px` on catalogue entries and ledger rows.
17. The year filter as chips 2026, 2025, 2024, 2023, "2022 and earlier" (95 papers) in place of two selects over 2011 to 2026.
18. The gap chart as an optional static SVG plate replacing the Figure 1 raster, drawn in site type and tokens, no stagger animation. Cut it first if time is short; keep the raster.
19. Scroll-spy on A's chronology strip: the month in view is marked, and clicking a month scrolls to its head and sets `#2025-07`.
20. English hints beside the depth badges: 全文 read in full, 部分 read in part, 仅摘要 abstract only, 仅题录 metadata only.
21. `aria-live="polite"` on result counts, skip link first in the tab order, and the `<input type="month">` degradation to text with pattern `YYYY-MM` for Safari.
22. Clamp the summary to two lines in a collapsed ledger row and show it in full when expanded. This is a fix to A's weakest stream point, taken from C's clamp discipline but kept in A's single column.

Not grafted, on purpose: B's stat tiles, sparkline and numeral tweens; B's per-item timeline squares and brush; B's failure-source tiles and latest grid on the landing; C's three-column wall and item drawer; C's sticky scroll stage; C's hover lift and breathing dot; any 8 px or 14 px radius.

## Risks for the final spec

- A reads too quiet for the user's stated taste, who has rejected monochrome-leaning work before. Grafts 10, 13 and 18 are the mitigation; if the landing still looks plain after them, raise the chip tint from 14 % to 18 % before adding any new element.
- Stream summaries from the seed are 500 characters, not two sentences. Either `classify.py` trims to the schema or the ledger row is sized for 500 characters with the two-line clamp (graft 22).
- Light-theme marks in amber, teal and gold are under 3:1 in A and C; graft 4 is required, not optional.
- Rails must wrap 31-character section titles and 38-character subsection titles; no truncation in a table of contents.
- The catalogue card's label-over-title hierarchy (Newsreader 20 over Inter 14) is too steep; set the title at 15 or 16 and the label at 18, or lead with the title when a search query is active.
- Newsreader dependence: keep A's `size-adjust` fallbacks and check the landing in Georgia before sign-off.
- Google Fonts is a third-party request; the brief allows it, but the About colophon should say so, since the site otherwise promises no third parties.
- The stream is empty today and the first `stream.json` will land with roughly 200 to 280 items over 32 months. Both the empty state and the seeded state must be screenshotted in headless Chrome before publishing; a 12-row ledger and a 72 px strip both work at those counts.
- Figure 2 at 2.2 MB breaks the first-paint budget on its own if it is used as a raster anywhere; re-encode under 300 KB, or replace it with graft 10.
