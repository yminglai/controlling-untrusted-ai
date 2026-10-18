# Review: design fidelity and copy

Lens: design-copy. Reviewed 2026-10-17 against `design/DESIGN.md` (block by block), `BRIEF.md` (vocabulary, heading style, banned words, branding) and `SCHEMA.md` (visible data fields). No site file was edited.

## Method

- Static server at `http://localhost:8765/` (already running). Headless Chrome `--headless=new`, `--virtual-time-budget` 5 to 8 s.
- Screenshots: all five pages at 1440 × 900 in light and dark; full-length 1440 × 4200 (index, about), 1440 × 3600 (stream), 1440 × 2400 and 3200 (papers with drawer); 1024 × 900 (papers, stream, drawer); 768 × 1024 (index, papers, stream); 390 × 844 and tall through a 390 px iframe wrapper (Chrome enforces a 500 px minimum window, see IMPLEMENTATION_NOTES §1.8). States: subsection scope, section scope, compact density, search with widening, empty search, paper drawer, report drawer, expanded stream row by deep link, filtered stream, empty stream filter, "Recently verified" sort, month anchor, web fonts blocked (`--host-resolver-rules` to a dead port) for the Georgia/Arial fallback check.
- Console: `--enable-logging=stderr --v=0 --dump-dom` on all five pages: no `CONSOLE` lines at any level (only the two harmless `task_policy_set` lines).
- Copy: grep of `site/**/*.html|css|js|svg`, `README.md`, `.github/`, and a scan of every visible data field (`taxonomy.json` thesis, readers, blurbs, purposes, bullets; `papers.json` labels, one-liners, reasons; `grey.json`; `stream.json` titles, summaries, tags, verification notes) for em-dashes, en-dashes, the banned word list and employer or company names. Headings extracted from the rendered DOM of every page.

Screenshots used as evidence are in the session scratchpad (`shots/rv_*.png`, `shots/rv2_*.png`); file names are quoted per finding. Two deep-link captures (`#item/…`, `#2025-07`) came out blank or offset in headless Chrome after the page's programmatic scroll; the DOM dump confirms the row is `is-expanded` with field 6 filled, and the builder's own `design/shots/stream_1440x900_item_expanded_light.png` shows the state correctly, so this is a capture artefact, not a site defect.

## What passes

- **Blocks.** Every block in DESIGN.md §4 to §7 is present and in order: masthead with double hairline on index only, title block ([Authors], status line, three buttons with the first `aria-disabled`), the Spread (7/5, vertical rule, two running heads, 11-segment and 3-segment bars, count lines, eleven contents rows with subsection lists, twelve ledger rows under italic month heads, "All 231 items"), the Mechanism Map (coral bar with three circle marks and item counts, Lever 1 and Lever 2 labels, Constrain/Observe/Intervene, Verify tall, Train wide + Steer, Deploy and Assure base bar, glyphs, keyword lines, "N papers · N items" links, two-level-test line), the Control Gap plate with native dialog, Who This Is For, By the Numbers with the year histogram and the "Reading the Marks" key, colophon. Papers: 264 px rail with live "m / n" counts and 55 % zero rows, sticky filter bar with the segmented scope, sort, density, toggle and year chips with counts, active row with × and Clear, results head with "Also N matches in the whole corpus", section head with operation chip and purpose, subsection head with counts, covers disclosure and "N items in the stream", cards with all six fields, run-in groups (Reports and posts open, Also placed here collapsed), the drawer (band, crumb, label 32/38, title, authors collapsed after twelve, meta, four buttons, summary, Why it is here, Placed in, In the stream, Reading notes with depth badge, dl fields, tinted takeaway panel, two-column terms, meta line, Previous/Next with "i of n"). Stream: h1, dek, live indicator (forest, "Live · updated 23 h ago"), sources line, three buttons, chronology strip with stacked polarity bars, ticks for empty months, mono month labels every third month and small-caps year labels, facet rail in the specified order with counts against the other groups, pipeline panel with counts and links, sticky month heads "October 2026 · 6 items", rows with date, New dot, dash, kind, title with external icon, two-line summary, classification chips, More button, expansion with source line, Also reported by, Related papers, verified line with slate check, note, tags, Copy link and Report a problem. About: all ten sections with the spec copy verbatim, the colour key table, the eleven `<details>` groups with the 中文 column, enumeration tables, BibTeX with Copy, data list with sizes and dates, Provenance and Limitations, Colophon. 404: "Not in the Contents", four buttons, search forwarding to `papers.html?q=`.
- **Colour.** Hues appear only as marks, rules, bars, tints and chip borders; text is `--fg` or `--fg-muted` with the single allowed exception (`.live__label` in `--c-text`). Shape disambiguates as specified: squares for sections and operations, circles for failure sources, dashes for polarity; the Report badge is sand (`data-c="report"`), the verified check is slate. Section colours on contents rules, rail rules, sigbar, map nodes, section heads, drawer band, card marks and `chip--sub` left rules all resolve through `data-section`; failure-source and polarity chips through `data-source` / `data-polarity`. Dark theme uses the 18 % tint, raw-hue borders and transparent mark outlines as specified.
- **Type.** Newsreader, Inter and IBM Plex Mono at the specified sizes (checked in the stylesheets and in the renders); with web fonts blocked the Georgia/Arial fallbacks hold the layout (`rv_index_nofonts_light.png`).
- **Motion and states.** Hover 120 ms, toggle 200 ms, drawer 260 ms slide with `@starting-style`, dialog fade; all zeroed under reduced motion, skeleton shimmer disabled, the deep-link flash suppressed. Empty, error, skeleton, no-stream (rail at 55 % with `aria-disabled`), widening, zero-count chips, disabled scope radios, pressed density buttons all render as specified.
- **Responsive.** 1024 (rail 240, drawer 440 with scrim), 768 (Menu sheet, section strip + Contents sheet, Filters button, 56 px strip) and 390 (short masthead title, stacked Spread, eight ledger rows, chevron contents, single-column map with 64 px nodes, Jump-to-month select, date above title, full-screen drawer with sticky close bar) match §4 to §6.
- **Copy and branding.** No company or employer name anywhere under `site/` (the only hits are the font name "Microsoft YaHei" in the CJK stack and news subjects inside `stream.json`, which are the events themselves). "[Authors]" appears on the landing, on About and in the BibTeX. About covers provenance and limitations with the spec paragraph verbatim. No em-dashes in any site file or in any visible data field; survey vocabulary (failure sources, requirements, two levers, Constrain/Observe/Intervene/Train/Steer/Verify, Deployment and Assurance, two-level test, L1/L2) is used exactly as in BRIEF.md.
- **Console.** Zero console messages on all five pages.

## Findings

Severity: blocker | major | minor. Lines refer to the current files.

### F1 · major · `site/assets/js/papers.js:264` (and :214, :240)
**The results head says "191 cited in the PDF" while the chip directly above it says "Cited in the PDF 240" and About says "240 items are cited".**
Evidence: `rv_papers_1440_light.png` (whole corpus): results head "1,788 papers in the whole corpus · 191 cited in the PDF · 174 reports"; chip row "Cited in the PDF 240". DOM dump confirms both strings. Cause: `computeCounts` sets `cited` from primary papers only (`S.primaryOf…filter(selected)`, line 214), so `scoped.cited` excludes the 49 selected reports, while `countChip("cited")` and `stats.cited` include them.
Fix: add `(S.greyOf.get(ss.id)||[]).filter(g=>g.selected).length` to `cited` at line 214 (and to `counts.selected` in `build_data.py` if the subsection heads should agree too), or reword the head to "191 papers and 49 reports cited in the PDF" so the two numbers on screen reconcile.

### F2 · minor · `site/assets/css/site.css:79` (`.title-block`), `:81` (`.dek`); `site/index.html:79`
**The Spread begins at about y = 520 at 1440 × 900, not "near y = 380"; the title block is about 460 px, not "about 320 px" (DESIGN §4 Block 2 and 3).**
Evidence: `index_1440_light.png`: running heads at y ≈ 527, count lines at y ≈ 570; only the first contents row and the first ledger row sit above the fold. The h1 takes two 72 px lines (151 px) and the two-sentence dek wraps to four lines at 60ch (128 px); with paddings the block is ~460 px. The five-second test is still met (both heads, bars and counts are visible) but the first signature moment is mostly below the fold.
Fix: tighten `.title-block` to `padding: var(--s4) 0 var(--s5)` and `.dek` to `--measure-dek: 68ch` so the dek fits three lines, or drop `--fs-display` to `clamp(40px,5vw,64px)`; target the running heads at y ≤ 440.

### F3 · minor · `site/assets/js/papers.js:391`, `:55`, `:114`
**The "Chinese notes" chip reads 195 at rest; About says 239; the number jumps to 239 only after the chip is clicked.**
Evidence: `rv_papers_1440_light.png` chip "Chinese notes 195"; About "239 items carry structured reading notes". `hasZh` uses `has_zh` (papers only, 195) until `summaries_zh.json` loads, which only `toggleChip("zh")` triggers. DESIGN §5.8 wants 239.
Fix: call `loadNotesFile().then(() => route({force:true}))` from `loadPapers()` on idle (next to line 114) so the count reads 239 before interaction, or ship `stats.zh` and `grey.has_zh` from the pipeline (the extension IMPLEMENTATION_NOTES already requests) and use them.

### F4 · minor · `site/assets/js/taxonomy.js:193`
**The About colour key reads "§2 How Agents Fail (How Agents Fail)".**
Evidence: `rv_about_full_light.png`, colour-key row 2; DOM dump: `--c-s2 §2 How Agents Fail (How Agents Fail)`. The operation label for `failures` equals the section title, so the parenthetical duplicates it.
Fix: omit the parenthesis when `operationOf(s.id).label === s.title`, or print the operation id ("failures") in mono instead.

### F5 · minor · `site/assets/js/stream.js:449`, `:474`, `:282`; `site/assets/js/common.js:307`
**In "Recently verified" sort the ledger collapses into one head, "October 2026 · 231 items", while the chronology strip still buckets by event date; clicking a strip column then does nothing.**
Evidence: `rv_stream_compact_verified_light.png`: single head "October 2026 · 231 items" above rows dated Feb 2024 to Oct 2026; the strip is unchanged. `applyHash` looks for `sortKeyOf(it) === h` (verified month) while the strip's `href="#2025-07"` is an event month, so no row matches and the page stays put. The head copy does not say it groups by verification month.
Fix: in verified sort either draw the strip from `verified_on` months or resolve `#YYYY-MM` against `monthKey(it.date)`; and suffix the head with "· verified" (e.g. "October 2026 · verified · 231 items") so the grouping is legible.

### F6 · minor · `site/assets/css/site.css:61`; `site/index.html:66, :70, :150` (same markup on all five pages)
**External links in the masthead ("GitHub") and the colophon ("Submit an item", "GitHub", "CC BY 4.0 for text and data") carry no arrow-up-right icon; DESIGN §3 says external links carry it.**
Evidence: `index_1440_light.png` masthead and footer; the `.ext` class and `icon--ext` are used on cards, ledger titles and drawer buttons but not here, so a reader has no cue that these leave the site (the "Submit an item" footer link also has no `target`, unlike the same button elsewhere).
Fix: add `class="ext"` plus `icon("arrow-up-right","icon icon--ext")` to the three colophon links and `.masthead__gh` (`.nav__link.ext .icon--ext { vertical-align: 0 }`), and give the footer "Submit an item" the same `target="_blank" rel="noopener"` as the button.

### F7 · minor · `site/index.html:133`; `site/about.html:87`; `site/data/taxonomy.json` (readers[2]); data fields in `papers.json` and `grey.json`
**The banned word "robust" appears in visible copy: "robustness" in the third reader paragraph on the landing and About, and in 11 card labels ("System Prompt Robustness", "Reward-Robust RLHF"), 39 one-liners, 15 placement reasons, 4 subsection bullets and 3 report lines; "landscape" in two labels ("Threat-Landscape Survey", "Prompt-Injection Landscape") and "leverage" in one reason.**
Evidence: grep of the rendered HTML and of the data fields (counts above). The readers text is bound from `taxonomy.readers`, which `build_data.py` copies from `outline.json`; the paper fields are corpus data. In the readers sentence "robustness" names a governance requirement (the EU AI Act's accuracy, robustness and cybersecurity), so it is arguably technical vocabulary rather than hype.
Fix: decide once. Either accept "robustness" as a regulatory term in bound and corpus text and keep the ban for the site's own prose (document the exception in BRIEF.md), or rewrite the readers sentence in the pipeline ("human oversight, logging, risk management, resistance to attack") and leave corpus labels alone. No action on the labels is recommended; they are the papers' own terms.

### F8 · minor · `README.md:1`
**The repository README title contains an em-dash: "Controlling Untrusted AI: A Survey — companion site".**
Evidence: `grep -n "—" README.md`. It is the first line a visitor sees on GitHub; the brief bans em-dashes.
Fix: "Controlling Untrusted AI: A Survey. Companion site" or "Companion site for Controlling Untrusted AI: A Survey".

### F9 · minor · `site/index.html:129`, `:138`; `site/about.html:84`, `:114`; `site/assets/js/taxonomy.js:182`
**Several visible headings are not Title Case noun phrases, and the same block is headed differently on two pages.**
Evidence: index h2 "Who This Is For" and About h3 "Who It Is For" (a clause, and two wordings for one block); About h2 "Submit an Item" (imperative); index "By the Numbers" (prepositional; visually hidden) and the key head "Reading the Marks" (gerund). All are DESIGN.md verbatim, so the spec carries the inconsistency.
Fix: use one noun phrase on both pages ("Intended Readers" or "The Readers"), rename the About section "Reader Submissions" (keep the button text "Submit an item"), and "Marks and Colours" for the key; update DESIGN.md §4, §7 to match.

### F10 · minor · `site/assets/js/papers.js:460`; `site/data/taxonomy.json` (`subsections[].bullets`)
**"What this subsection covers" opens to the outline's writer plan in imperative voice, addressed to the authors rather than the reader.**
Evidence: DOM dump of papers.html, subsection 1.1: "Name the five requirements a deployer places on an agent…", "Ground the list rather than assert it: code the incidents…", "Explain why the agent cannot be trusted…", "Cite the parent taxonomies… (DeepMind technical-safety…)". Across the 210 bullets the first words are Survey (20), State (13), Define (12), Report (12), Distinguish (9), Use (8), Discuss (7), Explain (6)… DESIGN §5.5 specifies listing `bullets`, so the page is spec-conformant, but the copy reads as instructions and leaks drafting notes ("(Figure 1)", parent-taxonomy credits).
Fix: relabel the disclosure "Writing plan for this subsection" (honest about what it is) or convert the bullets to declarative noun phrases in `build_data.py` (strip the leading verb, e.g. "The five requirements a deployer places on an agent…").

### F11 · minor · `site/assets/js/common.js:315`
**Every one of the 231 ledger rows and all twelve landing rows carry the forest "New" dot, so the mark carries no information.**
Evidence: `stream_1440_light.png`, `index_1440_light.png`; DOM: 60 `.new` in 60 rendered rows. All items have `verified_on = 2026-10-17`. IMPLEMENTATION_NOTES §8 records this as specified behaviour; it still reads as noise for a week, and will recur after every bulk re-verification.
Fix: suppress the dot when more than, say, half of the items are "new" (`isNew && newCount / items.length < 0.5`), or show it only for items whose `verified_on` is later than `stream.generated` of the previous build; accept the current behaviour if the first collector run lands within days.

### F12 · minor · `site/assets/css/papers.css:174`
**At 390 the drawer's "Placed in" rows break badly when a subsection title wraps: "8.5 Representation Training and Unlearning" wraps to two lines and "· score 3" is pushed to the right edge on its own two lines.**
Evidence: `rv2_m_papers_drawer.png`, Placed in list, third row. `.drawer__placed a` is `inline-flex` with three spans; the long title shrinks and the note cannot wrap after it.
Fix: make the link `display: inline` (mark `vertical-align: middle; margin-right: 8px`) so the note follows the title inline, or `display: grid; grid-template-columns: 8px minmax(0,1fr) auto; align-items: start`.

### F13 · minor · `site/papers.html:98`; `site/assets/js/stream.js:200`; `site/assets/css/papers.css:48`; `site/assets/css/stream.css:44`
**Both search placeholders are clipped, so readers never learn what is searchable.**
Evidence: papers at 1440: "Search titles, labels, authors, summari" with the `/` hint over the end (320 px input, 30 px padding each side); stream at 1440 (260 px rail): "Search titles, summaries…", at 1024: "Search titles, summa…". The spec wording ("…publishers, tags") is never visible.
Fix: shorten the placeholder to "Search papers" / "Search the stream" and move the field list into the visually hidden label (already present) and a `title`, or widen the papers input to 380 px and set the stream placeholder to "Search titles, summaries, tags".

### F14 · minor · `site/assets/js/papers.js:490`, `:703`; `site/data/grey.json` (`confidence`)
**Nineteen report cards and drawers carry the badge "Report · existing bib entry", an internal provenance value, and several of these "reports" are arXiv papers with an arXiv URL.**
Evidence: `rv_drawer_grey_light.png` (mitchell2026ai): badge "REPORT · EXISTING BIB ENTRY", meta "arXiv:2608.23642", button "arxiv.org". `grey.json` confidence values: verified 153, "existing bib entry" 19, likely 2. About promises "the few not fully verified are marked"; "existing bib entry" is not a verification level a reader can interpret.
Fix: in `build_data.py` map `existing bib entry` to `verified` (these come from the paper's own bibliography) and route arXiv-hosted entries into `papers.json`; until then, in `papers.js` append the suffix only when `confidence === "likely"` or `"unverified"`.

### F15 · minor · `site/assets/js/stream.js:369`
**The expanded row's source line prints raw slugs: "Anthropic · first-party · browsing · …", "AI Incident Database · incident-database · coding · …", "email-and-office".**
Evidence: `rv2_m_stream_item_tall.png`, `design/shots/stream_1440x900_item_expanded_light.png`. `renderExtra` joins `it.evidence` and `it.domain` unmapped although `EVIDENCE_LABELS` and `DOMAIN_LABELS` exist in the same file (lines 23, 24) and are used in the facets.
Fix: `[it.publisher, EVIDENCE_LABELS[it.evidence] || human(it.evidence), DOMAIN_LABELS[it.domain] || human(it.domain), actors]`.

### F16 · minor · `site/assets/js/stream.js:373`; `site/data/stream.json` (`verification_note`)
**Verification notes are audit-log prose shown in full on expand: median 567 characters, 183 of 231 longer than 400, and 54 reference pipeline internals ("Same event as seed items 006 (Fortune) and 076 (eWeek)", "the candidate's '18 July 2026' submission", "Merged on 2026-10-17 with 2 further reports…").**
Evidence: `design/shots/stream_1440x900_item_expanded_light.png` (AIID 1152 row, nine-line note); data scan above. DESIGN §6.4 asks for the note "in a line beneath"; the data makes it a paragraph of editor-facing text.
Fix: in `renderExtra` show the first sentence of the note and a "Show full note" `<details>`; in the collector and seed scripts write a reader-facing one-sentence note ("URL fetched 2026-10-17; date and claims confirmed from the article body.") and keep merge and candidate details in a separate, unpublished field.

### F17 · minor · `site/data/stream.json` (`summary`); `pipeline/collect_news.py`, `pipeline/classify.py`
**Summaries meet the two-sentence rule by letter only: median 725 characters for two sentences; the 2026-10-09 Anthropic item is 1,011 characters in two sentences, so an expanded row is an eleven-line paragraph at 1440 and twenty-five lines at 390.**
Evidence: `rv_stream_item_light.png`, `rv2_m_stream_item_tall.png`; scan: 227 of 231 summaries are exactly two sentences, 177 exceed 600 characters. SCHEMA.md: "Two factual sentences taken from the source". The brief asks for plain prose; these are run-on lists joined by commas and semicolons.
Fix: cap summaries at about 350 characters in the classifier prompt and seed sweep (two short sentences), or allow three to four short sentences and update SCHEMA.md; the UI's two-line clamp hides the problem until expand, so no front-end change is needed.

## Notes (no finding)

- The DESIGN heading rule "two to five words, no colons" also catches the spec-mandated one-word h1s "Papers" and "About" and the h2s "Cite", "Data", "Colophon"; these are conventional page labels and are not reported.
- Drawer and pipeline h3/h2s in sentence case ("Why it is here", "In the stream", "Placed in", "How this is collected") render in uppercase small caps, so the case is invisible; not reported.
- Thirteen stream titles begin with a database prefix ("AIID 1152:", "OECD AIM:"); they come from the source and read as catalogue entries. Worth a style decision in the pipeline, not a defect of the page.
- `taxonomy.json` bullet 1.1 names "DeepMind" as the origin of a parent taxonomy. That is a citation inside the paper's plan, not site branding.
- The "Read the Paper" button is an `<a>` without `href` (`role="link" aria-disabled`), so it is not focusable and the "arXiv link to come" tooltip is mouse-only. Acceptable for a placeholder; a `<button disabled>` would read better to assistive tech.
- `site.css` is 29 KB uncompressed against the 20 KB budget (IMPLEMENTATION_NOTES §8 already records this).
