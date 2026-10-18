# Judge: deployer lens

Written 2026-10-17 against `design/concept_a.md`, `concept_b.md`, `concept_c.md`, `BRIEF.md`, `SCHEMA.md`, the built data under `site/data/`, and the paper's Figure 1 source (`figures/fig_why_control_tikz.tex`).

Lens: a platform/security engineer who deploys agents with real credentials. I would use this site weekly for two jobs: look up a mechanism ("what can I put in front of a browsing agent against prompt injection, and does it survive an adversarial model?") and follow incidents ("what went wrong in the field since last week, and which subsection does it belong to?"). I care about clarity, credibility, speed and information density, in that order. I do not care about being told a story on every visit.

## Checks run before scoring

The concepts all cite the same corpus numbers; I verified them and the colour claims against the data rather than taking them on trust.

- `stats.json` says `grey: 174`, `cited: 240`, `stream_items: 0`, `stream_updated: null`. All three concepts hard-code 160 grey items and 239 cited. The site must read these from `stats.json`; the concepts' prose numbers are already stale.
- `summaries_zh.json` has 239 entries, but only 195 keys are in `papers.json`; the other 50 belong to `grey.json`. Every concept hangs the 中文 badge and the summary loader on `papers.has_zh` only. Grey cards need the badge and the loader too, and any "239 Chinese summaries" filter computed over papers alone will show 195. None of the three noticed.
- Contrast, computed (WCAG, sRGB): raw tokens on white: coral 3.94, blue 3.41, purple 3.47, periwinkle 3.13, forest 3.07, terracotta 3.04, amber 2.37, teal 2.11, gold 1.99; gray `#7D7D7D` on white 4.12. Concept C's table is right to the decimal. Concept A's note that gray fails AA for small text is right. Concept B's rule "coloured text only through `color-mix(token 70%, --ink)`" gives amber 3.77, teal 3.42, gold 3.26, sky 3.06, sand 3.67 on white: five tokens fail AA as specified. B's own test script would catch it, but the rule in the spec is wrong. C's rule (60 percent for most, 50 percent for amber, teal, gold, sky, sand) passes.
- Concept C's hero labels (Chat 2022, Tool use 2024, Autonomous agents, fixed human review capacity, "the control gap") are the paper's own Figure 1 labels, not invented. "Recursive self-improvement 2026 and later" adds a date the figure does not carry.
- `fig2_mechanism_map.jpeg` is 2.2 MB on disk. All three say to re-encode it; this is mandatory, not optional, for the 1 s first paint.
- Cross-references: `s3_2` receives 40, `s2_2` 37, `s2_4` 36, `s10_1` 35. Concept A's collapsed "Also placed here (N)" group is sized for this; B pushes cross-references into the drawer; C collapses them at the end of each subsection as A does.

## Scores

Scale 1 to 10 per criterion; total is the plain sum (max 70).

| Criterion | A Journal | B Atlas | C Narrative Map |
|---|---|---|---|
| Clarity (five-second two parts) | 8 | 9 | 8 |
| Credibility (deployers, security researchers) | 9 | 8 | 7 |
| Delight (fancy without gimmicks) | 7 | 8 | 8 |
| Vocabulary fit (terms and colour tokens used functionally) | 8 | 9 | 9 |
| Feasibility (vanilla, performance, researcher-maintainable) | 9 | 7 | 6 |
| Papers usability (1,788 papers by 56 subsections) | 9 | 9 | 8 |
| Stream usability (daily reading and filtering) | 8 | 9 | 7 |
| **Total** | **58** | **59** | **53** |

B wins by one point. That margin is real but small, and the graft list below is heavy on A for a reason: B has the right structure for a deployer and A has the right surface for a reader who needs to trust what is on the page.

### Concept A: Journal companion (58)

What works for my lens. The front-page spread puts both parts under running heads of equal weight with the two key numbers directly beneath, and the vertical hairline does the rest; the five-second test passes. The papers page is the best lookup tool of the three: the scope control (This subsection, This section, Whole corpus) with "Also 41 matches in the whole corpus" is exactly how I search for a mechanism when I am not sure which subsection the survey filed it under. Cards put the method-style label first at 20 px, which is what a deployer scans; compact density at 56 px per row gives real information density. The collapsed ledger row shows date, polarity, kind, title, summary and the classification line without a click, so a week's items can be read in one scroll. Mark shapes differ by group (circle for failure source, square for operation, dash for polarity), which is the only concept that solves the shared coral problem in a way that survives a dark theme and a colour-blind reader. The contrast analysis is right. The chronology strip is drawn from the filtered set, so it doubles as a histogram of the current query. Feasibility is the best: no CDN, native `<dialog>`, a forty-line router, a typed-array search index, a cut order that never touches the three signature moments.

Weakest point. The site has no operation-level view. The two levers and the mechanism map appear only as a raster plate and on the About page; the landing is the paper's table of contents. A deployer thinks "I need an Intervene mechanism against manipulation", not "section 6", and A makes me translate on every visit. Second, the stream has no staleness signal and no "new since" marker: the "live" is conveyed by dates alone, which is honest but makes the weekly check-in slower. Third, the landing is almost all type; it is credible but it is the least fancy of the three, and the user asked for fancy.

### Concept B: Atlas (59)

What works for my lens. The two entry cards ("Part one, The Paper Collection; Part two, The Live Stream") with big numerals and verb buttons are the clearest five-second signal of the three. The mechanism map as the single navigation metaphor matches the deployer's mental model exactly: operations on one axis, failure sources on the other, and one click filters both collections. The papers rail shows live counts under filters ("12 / 70"), the results header states the scope in words, a search query widens to all sections with grouped sticky headers and a "within 5.2 only" chip to narrow back, and cards show `reason` as "Why here:" when `one_line` is empty (149 papers), which is a good use of data the other two drop. The stream has the features a weekly reader needs: a "Recently verified" sort, a stale-collector note, facet counts that reflect other active filters, click a timeline square to scroll to its card, "Report a problem" with the item id prefilled, and a pipeline panel with counts by `added_by`. j and k through the drawer. Vocabulary fit is the best: the map reproduces Figure 2 including the two-level test text, and failure sources, operations and polarity are each used as a distinct functional signal.

Weakest point. The landing is a dashboard: stat tiles, sparkline, polarity bar, a 540 px interactive map with a readout, a 56-row table, a 3 by 2 card grid, a four-column footer, radius 8 cards and radius 12 drawers. It risks the SaaS-analytics look that the brief's "editorial, paper-like" taste warns against, and for a security audience that look costs trust. Second, the colour rule as written fails AA for five tokens (above). Third, the pushing 560 px drawer at 1440 reflows the card column on every open and close; the overlay-in-margin layout of A is calmer. Fourth, the stream card is about 200 px collapsed with no density toggle, roughly four items per screen. Fifth, the timeline encodes failure source and polarity in one colour channel (coral is both "mistakes" and "bad"), which A's mark shapes avoid.

### Concept C: Narrative Map (53)

What works for my lens. The contrast rules are measured and correct, including the muted-text rule (`gray` 85 percent plus ink) and the dark-theme variants. The live indicator is the most honest of the three: forest under 48 hours, gold "Collector last ran 3 days ago", coral "Collector stalled since <date>". The "New" dot on items verified within seven days, and the dot on the Stream nav link when `stream_updated` is recent, are the two cheapest features that make a weekly check-in fast. The rail never hides other sections, so cross-reference chips always resolve. `content-visibility: auto` on cards is the right performance primitive. The hero retells Figure 1 with the paper's own labels.

Weakest point. The stream wall. A three-column grid of clamped cards breaks chronological reading (row-major order across columns is ambiguous), halves the legibility of each summary, and pushes details into a drawer, so following a week of incidents takes more clicks and more eye travel than either ledger. Second, the three-beat scrollytelling story with a sticky stage is three screens of narrative between the hero and the tools; a weekly user scrolls past it every time, and C itself ranks it first to cut, which says what it is. Third, feasibility: two drawers, a popover, a lightbox, a breathing dot, a scroll-following chronology cursor, a sticky three-state SVG stage and three web fonts is the most code of the three, with a stated Safari problem on `<input type="month">`. Fourth, the papers page renders all 56 subsection heads with a 12-card cap and "Show all 35", so landing on 4.1 to see everything costs a click that A and B do not charge.

## Winner

**Concept B, Atlas**, on the structure: the mechanism map as navigation, live counts in the rail, the search that widens and narrows, the "Recently verified" sort and the stale note. Build it with A's surface and C's colour arithmetic.

## Graft list

Carry these into `DESIGN.md`. Each names its source.

From Concept A:

1. The typographic surface. Keep B's three voices (Newsreader, Inter, IBM Plex Mono) but apply A's rules: hairline 1 px rules, radius 0 on cards and panels, 2 px on chips, no shadows on static elements, small-caps running heads at 11 px with 0.08em tracking, double hairline under the masthead on the landing only. This removes the dashboard look without removing a single count.
2. Muted text is ink, not gray: `#7D7D7D` on white is 4.12:1. Gray is for rules and for text at 24 px and above.
3. Mark shapes by group: circle for failure source, square for operation and section, dash for polarity. Coral is shared by bad, mistakes and section 2; the shape disambiguates in both themes. Apply to B's timeline squares as well: polarity as a dash row below the failure-source squares rather than one colour channel.
4. The scope control on the papers filter bar (This subsection, This section, Whole corpus) and the line "Also N matches in the whole corpus". Pair it with B's rail counts.
5. Label first on the card: method-style label at 20 px serif, title at 14 px sans beneath it, as A sets it. B's order (title 18, label 13) demotes the field a deployer scans.
6. The collapsed ledger row: date column, polarity dash, kind, title, summary, classification line visible without a click; details (actors, related papers, verification note, tags) on expand. Add a stream density toggle (full, compact) as A has for papers.
7. "Also placed here (N)" as a collapsed group at the end of each subsection, since `s3_2` has 40 and `s2_2` 37 cross-references. Keep B's re-scoping links in the drawer as well.
8. The chronology strip drawn from the filtered set, so it is a histogram of the current query; B's timeline should reflect the active filters, not all items.
9. Honest empty states: with `stream_items` at 0 today, B's 40 px numeral would read "0". Use A's copy ("The ledger opens with the first verified sweep") in the entry card and on the stream page until the seed lands.
10. Drawer as an overlay in the right margin at 1440 (A), not a pushing pane (B), so the card column does not reflow on open and close.
11. "Download stream.json" on the stream header; the per-file size and generated date on the About data list.
12. The 术语 glossary as a two-column list split on " = ", English left, Chinese right; the 部署启示 panel tinted in the section colour (B has this too; keep it).
13. The closing rule for drawers: `history.back()` only when the previous entry is on the same page, otherwise replace the hash.

From Concept C:

14. The colour arithmetic. Coloured small text is `color-mix(in srgb, var(--c) 60%, var(--ink))`, and 50 percent for amber, teal, gold, sky and sand; dark theme `color-mix(var(--c) 65%, white)`; tinted fills 14 percent light, 18 percent dark, always with `--text` on top. Keep B's `pipeline/tests/` contrast script as the guard; it would have caught B's own rule.
15. The staleness ladder on the live indicator: forest under 48 hours, gold "Collector last ran N days ago" to seven days, coral "Collector stalled since <date>" beyond. Replace B's 14-day amber note, which is too lenient for a collector meant to run on a schedule.
16. The "New" dot on items whose `verified_on` is within seven days, and the dot on the Stream nav link when `stats.stream_updated` is within seven days.
17. One custom property `--c` set from `data-section`, `data-source` or `data-polarity`, with component CSS reading only `--c` (A does this inline; C's data-attribute form is cleaner to maintain).
18. The rail never hides other sections, so every cross-reference chip resolves without a scope change.
19. `content-visibility: auto; contain-intrinsic-size: 0 124px` on cards, in addition to B's chunked rendering.
20. Clicking a failure-source dot or an operation chip on a stream card applies that filter, with a filter icon on hover and focus and an `aria-label` ("Filter by Observe"). B only links operation chips; extend to failure sources and subsections.
21. A subsection picker in the stream filters: a `<select>` grouped by section, shown as a removable chip when the page opens with a `sub=` parameter. B supports the deep link but offers no control to set it.
22. The 11-segment section bar (widths from `stats.per_section`, section colours) in the papers entry card; it shows the shape of the corpus in 6 px and costs nothing.
23. C's order of work: tokens and shared header; Papers page (largest content, settled contract); Stream page against the schema with a small fixture; landing last.
24. The static gap chart as an inline SVG, if used at all, belongs on the About page or as a small plate, not as a hero animation. Skip the sticky stage.

From the data checks (not in any concept):

25. Read every headline number from `stats.json` (`grey: 174`, `cited: 240`); never hard-code 160 or 239.
26. Grey cards carry the 中文 badge and open the same reading-notes loader when their key is in `summaries_zh.json` (50 of the 239 entries are grey). Any Chinese-summary count or filter is computed over papers plus grey.
27. Re-encode `fig2_mechanism_map.jpeg` (2.2 MB) to under 300 KB before anything else ships.

## Risks to carry into the spec

- B's landing becomes a dashboard if the type and radius rules from A are not applied from the first commit.
- The 70 percent colour rule in B fails AA for five tokens; use C's rule and keep the test.
- The stream is empty today (`stream_items: 0`); every landing numeral and chart must have the honest empty copy, and the headless Chrome check must run against an empty `stream.json` as well as a fixture.
- The mechanism map is a large keyboard surface (roving tabindex, arrow keys, `aria-pressed`); verify with VoiceOver before it ships, or ship it as plain links first (B's own last cut).
- `summaries_zh.json` keys span papers and grey items; a loader keyed on `papers.has_zh` alone leaves 50 summaries unreachable.
- The timeline grows without bound; cap stacks at 12 per month with "+n" (B) and plan the by-year split of `stream.json` as a schema extension.
- The pushing drawer reflows the list at 1440; prefer the overlay.
