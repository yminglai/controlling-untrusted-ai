# Review summary: companion site of Controlling Untrusted AI: A Survey

Four review passes ran on 2026-10-17 (design/review_visual.md, review_data.md, review_a11y-perf.md, review_design-copy.md). The sections below record what was done with their findings.

## Fix log 2026-10-17

One fixing pass over all four reviews. Verified afterwards in headless Chrome (zero console messages on every page and
route tested, light and dark, 1440 × 900 and a true 390 × 844 render through a same-origin iframe harness that was
deleted afterwards), with `pipeline/tests/test_build_data.py`, the new `pipeline/tests/test_contrast.py` (102 role
pairs) and `pipeline/tests/test_collector.py` (26 tests) all passing. Screenshots: `design/shots/fixed_<page>_<size>_<theme>.png`
for index, papers, stream, about and 404 at 1440 × 900 and 390 × 844, both themes (20 files). Measured after the
fixes: fixed chrome on papers.html 56 + 49 px (was 222); a hash target lands with its head at y = 125 under a 113 px
stack; the drawer close button is at y = 14 after the dialog has scrolled 1,400 px; the Spread begins at y = 436
(was 520); the landing fetches stats.json, taxonomy.json and stream_recent.json only.

Data: `pipeline/build_data.py` was rebuilt against the 15:20 clone (taxonomy generated 2026-10-17, corpus generated
2026-10-16 recorded as `stats.source_generated`): 1,788 papers, 164 reports and posts (was 174: six grey records were
the same work as a paper and four more were arXiv papers reached by a report URL, all folded into the paper; the two
bib keys of Anthropic's sabotage risk report became one record with a cross-reference), 239 cited documents, 238 cards
with Chinese notes (the note of the merged duplicate key was dropped). The nine reward-hacking stream items moved
from `s2_3` to `s2_4` and `stream.json` carries `taxonomy_generated`. `SCHEMA.md` records every new field.

### Blocker

1. **Stale taxonomy.json and papers.json (outline replaced at 15:20).** Fixed. Rebuilt; the test suite now compares
   every subsection title with `outline.json` and fails when the clone is newer than `site/data`, and
   `stats.source_generated` records the corpus date. Titles, thesis, placements and `also` lists match the TeX.

### Major

2. **Sticky filter bar 165 px.** Fixed. Only `.filterbar__row1` is sticky (`.filterbar` is `display: contents` so the
   row sticks within the results column); the search field flexes so the row is one 48 px line at 1440. At 390 the row
   is static while Filters is open and sticky again when closed.
3. **Hash targets land under the sticky stack.** Fixed. `papers.js` publishes the live stack height as `--sticky-h`
   (ResizeObserver); `scroll-margin-top`, `scroll-padding-top` and `scrollToResults()` read it.
4. **Drawer close button scrolls away.** Fixed. The button rides a zero-height sticky strip at every width (44 px at 390).
5. **Tap targets 18 to 36 px.** Fixed below 1024 px: chips 32 px with a 44 px hit area, icon buttons, More and the theme
   toggle 44 px, small buttons 36 px with a 44 px hit area, card links, stream links and covers summaries ±13 px, TOC
   chevron ±7 px, mobile Filters buttons 44 px, ledger chip gaps 10 × 8.
6. **Chip and results-head counts disagree (240 vs 191; Chinese notes 195 → 245).** Fixed. The head counts papers
   and reports like the chip (239 = 239); `grey.json` carries `has_zh` and the key collisions are merged (238 = 238).
7. **Stream items filed under the renamed s2_3.** Fixed. Nine items moved to s2_4 with "most specific first";
   `taxonomy_generated` added; the collector warns and the tests fail on a mismatch.
8. **classify.py hard-codes the old section 2.** Fixed. FALLBACK titles retitled, s2_3 rules carry insider vocabulary,
   reward hacking and harness patterns moved to s2_4; tests assert rule ids and titles against taxonomy.json.
9. **Fourteen cited reports with an empty URL.** Fixed. DOI or publisher pages (`GREY_URL_FALLBACK`, each checked to
   resolve); the test requires a URL on every grey record; the UI shows the venue if a URL were ever missing.
10. **Six keys in both grey.json and papers.json; reports that are arXiv papers.** Fixed. Merged into the paper record
    (selected, subsection added to `also`); a leftover collision is a hard build failure.
11. **stats.cited double-counts the sabotage risk report.** Fixed. 239; one record with `also: [{sid: s10_3}]`, rendered
    as a hollow-marked report card under 10.3 and listed in the drawer as "cross-reference".
12. **Filter chips lose focus.** Fixed. Chips are built once and updated in place; removing an active chip moves focus
    to the next chip, Clear, or the matching filter chip.
13. **Drawer Previous and Next recreated.** Fixed. Persistent nodes in `papers.html`; focus verified to stay on Next.
14. **Zero-count chips and rail rows at 55 % opacity.** Fixed. Colour (`--fg-muted`, 5.49:1) and a dashed border; still clickable.
15. **Chronology svg role=img with 33 focusable links.** Fixed. `role="group"`, links `tabindex="-1"`, the "Jump to
    month" select is the single keyboard stop at every width (visually hidden until focused above 767 px).
16. **Results head "191 cited" vs chip "240".** Fixed (see 6).

### Minor

17. Mechanism-map bar counts misaligned. Fixed.
18. Search placeholders clipped. Fixed: "Search papers", "Search the papers", "Search the stream", with `title`
    listing the fields; placeholders take `text-overflow: ellipsis`.
19. "Requested by name by the pass-2 agent" (104 cards). Fixed: "Named in the section plan".
20. Section strip clipped at 390. Fixed: fade mask, scroll snap, current chip scrolled into view.
21. Dark marks on the panel under 3:1. Fixed: lightened outline on panel surfaces (coral 4.95:1 measured).
22. Light control borders 1.69:1. Fixed: `--control-border` (4.12:1 light, 5.45:1 dark).
23. Year histogram collapses to 1 px. Fixed: square-root scale, 3 px floor (3, 4, 4, 4, 5, 5, 8, 15, 21, 27, 40).
24. Chronology starts "Feb" without a year. Fixed: "Feb 2024".
25. Score digit unexplained. Fixed: visually hidden "score 3, must cite" text plus `title`.
26. Rail in the Tab order (44 stops to the first card). Fixed: roving tabindex, chevrons `tabindex="-1"`, a second
    skip link "Skip to results".
27. Drawer 520 px at 1024. Fixed: 440 px from 1439 px down; scrim unchanged at 1023.
28. Spread at y = 520. Fixed: title block padding and `--measure-dek: 68ch`; measured 436.
29. Mechanism-map keywords clamp mid-word. Fixed: three lines, `title`, node min-height 128.
30. Three vendor prompt-injection posts under s2_3. Fixed: override to s2_2, logged as an anomaly.
31. Confidence "existing bib entry" shown as a badge. Fixed: closed set verified | likely | unverified.
32. Raw TeX math in ten titles. Fixed: `clean_math()` (τ-bench, τ²-Bench, E²AT, AI-45° Law); test asserts none left.
33. 中文 badge and chip for reports. Fixed (`has_zh`).
34. guo2026personalization note sid mismatch. Fixed by the merge; the notes footer prints the card's own subsection.
35. Two summaries "exceed two sentences". Skipped: both are two sentences; "Inc.", "N.D. Cal.", "No." and "U.S." fooled
    the counter. An abbreviation-aware check is in `test_collector.py` (reports at three, fails above) with a length cap.
36. Dark focus ring on a checked segment 2.0:1. Fixed: `--bg` ring on the `--fg` fill.
37. Mechanism-map hover ring in the raw hue. Fixed: `--c-border`.
38. Row chips with a never-updated `aria-pressed`. Fixed: action buttons ("Filter by X") without a pressed state.
39. Three more focus drops. Fixed: stream active-chip removal and row chips move focus deliberately; papers in-results
    links focus the results head.
40. No forced-colors handling. Fixed.
41. Colour-only objects. Fixed: counts in both signature-bar `aria-label`s, a 1 px `--bg` seam between stacked
    chronology segments, the dark panel outline on dashes.
42. Rail and facets sheets not modal. Fixed: `inert` on the rest of the page while open (both pages, verified).
43. Failed stream fetch shown as an empty ledger. Fixed on both pages (landing error card with "All items"; the stream
    page resets the live indicator and the count line).
44. Empty state disables the pipeline panel. Fixed: only the facet controls fade.
45. Landing downloads stream.json. Fixed: `stream_recent.json` and `stats.stream_*` counts, written by `build_data.py`
    and the collector; the landing never requests stream.json unless the small file is missing.
46. Fonts render-blocking without preconnect. Fixed on all five pages (preconnect, preload, print-media swap, noscript).
47. Three avoidable data costs. Partly fixed: About reads `counts.zh` and `stats.zh` (no 549 KB fetch); Figure 1 has a
    1000 px rendition with `srcset`. Not done: splitting papers.json per section (the file loads after first paint and
    the split touches every route; deferred).
48. `#live` rewritten every minute. Fixed: written only when the text changes.
49. Filter chips' `aria-label` hides the count. Fixed: toggle chips are named by their visible text.
50. test_contrast.py missing. Fixed: written and run in `pages.yml` with the other tests.
51. About colour key "(How Agents Fail)". Fixed.
52. "Recently verified" sort: heads and strip disagree, column click dead. Fixed: head reads "· verified", a column
    resolves to the first row of that event month, the strip follows the first row under the sticky head.
53. External links without the arrow icon; footer Submit without target. Fixed on all pages.
54. Banned word "robustness" in the readers paragraph. Skipped: it is the paper's own text (the EU AI Act term) bound
    from `outline.json`; recorded in IMPLEMENTATION_NOTES.md section 9. Corpus labels left alone as the finding suggests.
55. README em-dash. Fixed: "Companion site for Controlling Untrusted AI: A Survey".
56. Headings not Title Case noun phrases ("Who This Is For", "Submit an Item", "By the Numbers", "Reading the Marks").
    Skipped: DESIGN.md verbatim; a change belongs in the spec.
57. "What this subsection covers" opens to the writer plan. Addressed without changing the spec label: a lead line
    "From the authors' section plan: the points this subsection is written to make."
58. "New" dot on every row. Fixed: suppressed when more than half the items (stream) or all twelve rows (landing) are new.
59. Drawer "Placed in" rows wrap badly at 390. Fixed: inline rows (24 px each measured).
60. Badge "Report · existing bib entry"; arXiv items as reports. Fixed (see 10, 31).
61. Source line prints raw slugs. Fixed: evidence and domain labels.
62. Long verification notes. Fixed in the UI: first sentence with "Show full note"; the collector keeps writing the
    full note to the data.
63. Summaries long for two sentences. Partly fixed: the classifier prompt now asks for about 350 characters (never more
    than 450) for new items; the seed summaries meet the two-sentence contract and are unchanged.

Also done while fixing: an empty state for 2.3 Insider Threats (no primary paper in the October outline, "No papers are
placed in 2.3 ... in this draft of the survey"); `IMPLEMENTATION_NOTES.md` section 9 documents the shared-file changes.
