# Concept C: Narrative Map

Concept (c) of three for the companion site of "Controlling Untrusted AI: A Survey", written against BRIEF.md, SCHEMA.md and the real data: 1,788 arXiv papers (908 from 2026), 56 subsections holding from 1 paper (11.5) to 103 (8.2), 239 cited, 160 grey items, 239 Chinese summaries (171 read in part, 55 in full), labels of at most 27 characters, titles up to 176, one-liners up to 242 and empty for 149 papers, `also` lists up to 21 entries.

## 1 Idea and signature moments

The landing page retells Figure 1 in one short scroll: what agents can do rose in four steps while what a human can check stayed flat, the gap is filled by three failure sources, and the operations close it. Every block is drawn live from `taxonomy.json`, `stats.json` and `stream.json`, so the story is also the index: each failure source, operation and section shows its real count and is a link. At the end of the scroll the story hands over to the two tools, the paper collection and the live stream, and the same colour tokens and chip shapes continue into both, so the Papers rail and the Stream cards need no new learning.

Three signature moments:

1. **The gap opens.** In the hero, four capability steps (Chat 2022, Tool use 2024, Autonomous agents 2025 to 26, Recursive self-improvement 2026 and later) rise from the baseline while a dashed coral line, human review capacity, stays flat; the vertical distance is labelled "the control gap". The steps grow once, on first view, in 450 ms with an 80 ms stagger; under `prefers-reduced-motion` they are simply there.
2. **The operations become the rail.** Eight operation tiles on the landing page (How Agents Fail, Constrain, Observe, Intervene, Steer, Train, Verify, Deploy and Assure) each show their section's paper count and link to `papers.html#s4` and so on. The Papers rail reuses the same tiles at smaller size in the same colours.
3. **The wall is alive.** The Stream page is a wall of dated cards, newest first, with month separators, a quiet live indicator ("Live, updated 3 h ago") and a chronology rail: one tick per month, bar length proportional to item count, a cursor that follows the scroll. The rail is the only place time is drawn; the cards carry the dates.

## 2 Information architecture and navigation

Pages: `index.html` (Home: the story and the handover), `papers.html` (the corpus by section and subsection, search, filters, detail drawer), `stream.html` (wall, chronology rail, filters, item drawer, pipeline note, submit path), `about.html`, `404.html` (header, "Nothing at this address", links to the four pages).

Header, 56 px, sticky, identical on every page: text wordmark "Controlling Untrusted AI" in the display serif; links Papers, Stream, About; "PDF" as a disabled link with `aria-disabled="true"` and title "arXiv link to come"; theme toggle. The Stream link carries a 6 px forest dot when `stats.stream_updated` is within seven days. The current page has a 2 px ink underline. A skip link is the first focusable element.

URL scheme: filters live in the query string (survive reload, pasteable); position and entity live in the hash (no reload, Back closes a drawer).

- Subsection: `papers.html#s5`, `papers.html#s5_2`. Scrolls the heading under the sticky toolbar and expands the subsection fully.
- Paper: `papers.html#paper/han2024wildguard`. Opens the drawer; the list behind scrolls to the primary subsection.
- Paper filters: `papers.html?q=guardrail&year=2025,2026&cited=1&score=3&zh=1&grey=0&sort=year` (`year` accepts a comma list and `le2022`; `sort` is `survey`, `year` or `title`).
- Stream filters: `stream.html?polarity=bad&source=manipulation&op=observe,intervene&kind=incident&req=safe&domain=coding&sub=s4_1&from=2025-01&to=2025-12&q=database`.
- Stream item: `stream.html#item/2025-07-18-replit-agent-deleted-production-database`. Stream month: `stream.html#2025-07`.
- Landing anchors: `#gap`, `#failures`, `#operations`, `#papers`, `#stream`, `#figures`, `#cite`.

`common.js` exports `readState()` (query plus hash as one object) and `writeState(patch, {push})`: filter changes use `replaceState` debounced at 250 ms; opening a drawer uses `pushState`. `hashchange` and `popstate` re-run `readState()`. One helper, `linkTo(page, state)`, produces every cross-page link so no page hand-builds URLs.

## 3 Landing page

Container 1280 px, side padding 24 px. Blocks top to bottom:

**Block 1, Hero.** `min-height: calc(100svh - 56px)`, capped at 880 px, two rows. Top row, a 7/5 grid. Left: mono eyebrow "Survey, draft v0.2, October 2026"; the title in Newsreader at the hero size on two lines, "Controlling Untrusted AI" then "A Survey" in weight 400 and muted colour; "[Authors]"; the first two sentences of `taxonomy.thesis` as a 20 px lede; actions "Browse 1,788 papers" (primary; number from `stats.papers`), "Open the stream" (ghost, with live dot), and a disabled "PDF soon". Right: the gap chart, an inline SVG (`viewBox 0 0 560 360`) with a visually hidden caption "What AI can do has grown; what a human can check has not."

Bottom row: the two doors, 50/50, 168 px tall, radius 14 px, 1 px border, panel background, whole-card links.

- `.door--papers`: small-caps label "The paper collection"; `stats.papers` in mono at 40 px; "arXiv papers in 11 sections and 56 subsections; 239 cited in the paper; 160 grey items" (numbers from `stats.json`); an 11-segment bar 6 px tall, each segment the section colour, width proportional to `stats.per_section`; arrow icon.
- `.door--stream`: "The live stream" with the live indicator; `stats.stream_items` at 40 px; "field evidence on agent deployment, good and bad, classified into the survey taxonomy"; a three-segment polarity bar (forest, coral, gold) once `stream.json` loads, grey until then; "updated 3 h ago" in mono; arrow.

Five-second test: the title names the survey; the doors are the only two large numbers on screen, each with a verb and a coloured bar; the header's first two links repeat the two names. Nothing requires scrolling at 1440 by 900 or 390 by 844 (on the phone the doors stack under the title and the chart moves below).

**Block 2, the story.** Three beats. On desktop each beat is a 5/7 grid, text left (max 44 ch), one shared stage right, `position: sticky; top: 96px; height: 560px`. The stage is one inline SVG (`viewBox 0 0 960 600`) with three groups; a `data-state` attribute, set by an IntersectionObserver on the beats at threshold 0.5, chooses the visible group. Each beat has `min-height: 85vh`. Under reduced motion the group change is a 150 ms opacity cross-fade. Below 1024 px there is no sticky stage; each beat shows its own static group above its text.

- Beat 1, `#gap`, "The Control Gap". Three short paragraphs from 1.2: capabilities rose in steps, review capacity stayed fixed, each step added irreversibility (one turn and reversible; minutes and mostly reversible; thousands of actions and often irreversible; a cascade too fast to monitor). Stage: the gap chart at full size with Figure 1(a)'s labels. Link: "Read 1.2 in the papers" to `papers.html#s1_2`.
- Beat 2, `#failures`, "Three Failure Sources". Mistakes, manipulation, misalignment, one sentence each from `taxonomy.failure_sources[].blurb`, then the line that a guardrail stops mistakes while control must also hold for manipulation and misalignment. Stage: three blocks, coral, amber, purple, each with label, blurb at 15 px and two live links: "Open problems 11.1" (to `papers.html#s11_1`, 11.2, 11.3) and "N items in the stream" (count by `failure_sources`, link `stream.html?source=mistakes`; reads "..." until the stream loads).
- Beat 3, `#operations`, "The Operations". Two levers and verify, with the two-level test in one italic line (L1 indifferent agent; L2 agent trying to defeat it and knowing how it works). Stage: the mechanism map simplified. Row "Lever 1: change the deployment": Constrain (4), Observe (5), Intervene (6). Row "Lever 2: change the model": Train (8), Steer (7). A tall tile at right, Verify (9). A base bar, Deploy and Assure (10). A thin coral tile above, How Agents Fail (2). Each tile shows the section number, label and the sum of `counts.primary` over its subsections (Train, 356) and links to its section; fills follow the tint rule in section 7.

**Block 3, the handover.** Two panels, 50/50, `min-height 520px`, panel background, 14 px radius, 32 px gap.

- Left, `#papers`, "Browse the collection". Eleven section rows (number, title, bar in the section colour proportional to `stats.per_section`, mono count), each linking to its section. A search field, placeholder "Search 1,788 papers", navigating on Enter to `papers.html?q=`. Three fact links: "239 cited in the paper" (`?cited=1`), "160 grey items" (`?grey=1`), "239 Chinese reading summaries" (`?zh=1`).
- Right, `#stream`, "Follow the field", with the live indicator and update time. The three newest items as compact rows (mono date, polarity dot, two-line title, kind badge) linking to `stream.html#item/<id>`. A polarity total bar with legend "good 61, bad 54, mixed 22". Button "Open the stream"; text link "Submit an item". If `stream.json` fails or is empty, the panel shows the pipeline note and the submit link; no console error.

**Block 4, `#figures`, "From the Paper".** The two figures as `<figure>` elements side by side, `loading="lazy"`, re-encoded to 1600 px JPEG under 300 KB each (`fig2_mechanism_map.jpeg` is 2.2 MB today). Captions name what each shows. Clicking opens a native `<dialog>` lightbox; Esc closes.

**Block 5, `#cite`, "Cite and Follow".** Three columns: a BibTeX placeholder with a copy button; "Status" (draft version, `stats.generated`, stream update time); "Contribute" (the submit link and the sentence that items are verified before publication).

**Footer.** Page links, "No analytics, no cookies", licence, theme toggle, "Data built 2026-10-17".

## 4 Papers page

Layout at 1440: a 264 px rail on the left (`position: sticky; top: 56px; height: calc(100vh - 56px); overflow: auto`), a results column of at most 880 px, and the drawer as a 560 px overlay from the right. The toolbar is sticky under the header.

**Rail (`.toc-rail`).** Eleven section rows: 3 px bar in the section colour, mono number, title truncated to one line, primary count. A chevron expands the subsections (number, title, count). Scroll-spy sets `aria-current="location"` and a 2 px underline on the section and subsection in view. Arrow keys move, Enter navigates. Sections 1, 3 and 11 use grey.

**Toolbar.** Row 1: search input with icon, placeholder "Search titles, labels, authors, summaries", shortcut hint "/" in a `<kbd>`; a live count "1,788 papers and 160 grey items; showing 1,948"; sort select (Survey order, Newest, Title). Row 2 (open at 1440, behind a "Filters" button below 1024): toggle chips "Cited in the paper", "Must-cite (score 3)", "Relevant (score 2)", "Chinese summary", "Grey items" (on by default); year chips 2026, 2025, 2024, 2023, "2022 and earlier", multi-select. Active chips are ink-filled with white text. A "Clear" link appears when any filter is active. Filters are AND-combined; the rail scopes only through deep links and never hides other sections, so cross-references always resolve.

**Results.** Grouped by section then subsection in survey order.

- `.section-head`: 3 px top bar in the section colour; "4 Constraining Agent Actions" in Newsreader 28 px; the section purpose from `taxonomy.json` at 16 px muted; a counts line. Sticky below the toolbar while its cards scroll.
- `.sub-head`: "4.1 Least Privilege" in Newsreader 22 px; "35 papers, 3 cited, 13 cross-references, 1 grey item"; a "Plan" disclosure listing the subsection bullets; a "Field evidence: N stream items" link to `stream.html?sub=s4_1` (N filled after `stream.json` loads).
- Cards: the first 12 in file order, then "Show all 35". Grey items are interleaved with a sand badge. Papers listing this subsection in `also` sit at the end under a collapsed "Also relevant here (13)".

**Paper card, fields in order.**

1. Top row: `.paper-label` (method-style label, Plex Sans 600, 15 px, section colour mixed 60/40 with ink); badges right-aligned: `.badge--cited` "Cited" (ink fill, white text) when `selected`; `.badge--score`, a two-dot meter, two filled dots for score 3 (`aria-label="must-cite"`), one for score 2 ("relevant"); `.badge--zh` with the glyph 中 when `has_zh`; `.badge--grey` with the venue truncated at 24 characters.
2. `.paper-title`: Newsreader 400, 18 px, two lines max, a button opening the drawer.
3. `.paper-meta`: first three authors then "and 5 more" (450 papers have eight or more); year; arXiv id in mono as an external link (grey items show "source").
4. `.paper-line`: `one_line` at 14.5 px muted, two-line clamp, omitted when empty.
5. `.xref-row`: up to four `.xref-chip` ("5.2", "10.1") in their section colours, subsection title as tooltip, linking to `#s5_2`; "+17" when more.

Cards use `content-visibility: auto; contain-intrinsic-size: 0 124px`.

**Drawer.** 560 px, slides over a scrim, traps focus, closes on Esc, scrim, close button and Back. Header: breadcrumb "Section 5 > 5.2 Guardrails and Action Monitors" (links), label, title at 24 px, full authors, year, "arXiv 2406.18495" button, "Copy key". Body in order: "Summary" (`one_line`); "Why it is here" (`reason`); "Also relevant to" (subsections from `also` with full titles and score meters); "Field evidence" ("N stream items in 5.2", hidden when 0); "Reading summary (中文)" only when `has_zh`, loaded on demand from `summaries_zh.json` (fetched once, held in a module variable, about 400 KB) behind a five-line skeleton. Its structure: a depth badge first (全文, 部分, 仅摘要, 仅题录 with the grey English hint "read in full", "read in part", "abstract only", "metadata only"), then the fields in this order: 定位 Positioning, 问题 Problem, 方法 Method, 发现 Findings (ordered list, four on average), 部署启示 Deployer takeaway (a highlighted panel with a 3 px bar in the section colour), 局限 Limitations, 与小节关系 Relation to subsection, 存疑 Doubts (muted italic), 术语 Terms (two-column `<dl>`, English left, Chinese right, split at the equals sign). Field headings are the Chinese word in Plex Sans 600 with the English word in grey small caps beside it. Chinese text uses the system CJK stack at 15 px, line height 1.8; no CJK web font. Footer: Previous and Next within the current result list; j and k do the same.

**Search.** Tokens split on whitespace, lower-cased; a paper matches when every token is a substring of an index string built once from `label`, `title`, `authors`, `one_line`, `key`, `arxiv_id`. Rank within a subsection: label or title hit, then `selected`, then `score`, then file order. Grouping stays while searching; subsections with no match collapse to one line. Matches are wrapped in `<mark>`. Debounce 120 ms; "/" focuses; Esc clears; `q` updates in the URL. No library at this size; pinned MiniSearch is the only candidate if fuzzy matching is ever wanted.

**Loading and empty states.** The toolbar and rail are static HTML; counts fill from `taxonomy.json` (about 60 KB). The results column shows the eleven section heads at once and six skeleton cards under the first. `papers.json` (about 1 MB, roughly 250 KB compressed) is fetched after first paint; sections render cards only within one screen of the viewport (IntersectionObserver, `rootMargin: 100% 0px`). Empty results: "No papers match", removable filter chips, "Clear all", and the hint "Search matches titles, labels, authors and one-line summaries; try a shorter word." On fetch failure: "The paper list could not be loaded" with a retry button; the rail and section purposes still work.

## 5 Stream page

Layout at 1440: an 88 px chronology rail on the left (sticky, full height), the wall at up to 1180 px, the toolbar sticky under the header, the item drawer as a 560 px overlay.

**Toolbar.** Row 1: the live indicator; search ("Search titles, summaries, publishers, tags"); the polarity segmented control All, Good, Bad, Mixed with dots; a kind select over the eight kinds; two `<input type="month">` fields for the date range; "Submit an item" at the right. Row 2 ("More filters", open at 1440): failure source chips Mistakes, Manipulation, Misalignment in their colours; operation chips Constrain, Observe, Intervene, Steer, Train, Verify, Deploy and Assure in their colours; requirement chips Correct, Compliant, In scope, Within budget, Safe; a domain select with the 14 values; a subsection picker (a `<select>` grouped by section), shown as a removable chip "4.1 Least Privilege" when the page opens with `?sub=s4_1`. Count line: "Showing 42 of 137 items".

**Live indicator.** An 8 px forest dot and "Live, updated 3 h ago" (relative to `stream.generated`; absolute UTC as tooltip). The dot breathes in opacity between 1 and 0.5 over 2.4 s; static under reduced motion. Staleness is honest: beyond 48 hours the dot is gold and reads "Collector last ran 3 days ago"; beyond 7 days it is coral and reads "Collector stalled since 2026-10-10". Clicking opens a popover "How this feed is built": the `sources` list, counts by `added_by` and `kind`, the verification rule in one sentence, links to `pipeline/feeds.yml` and the workflow file.

**Wall.** CSS grid, three columns at 1440, 16 px gap, file order (newest first). A `.month-sep` spans all columns before each month's first card: "July 2025", the count, a small three-segment polarity bar. The first 60 cards render at once; a sentinel loads 60 more. Summaries clamp to three lines so rows stay level without masonry.

**Item card, fields in order.**

1. A 3 px left bar in the polarity colour (coral bad, forest good, gold mixed), `aria-label` "bad".
2. `.card-date` in mono 13 px, formatted by `date_precision` ("2025-07-18", "2025-07", "2025"); a forest "New" dot when `verified_on` is within seven days; `.kind-badge` at the right, outlined.
3. `.card-title`, Newsreader 18 px, three lines max, a button opening the drawer; beside it an external-link icon to `url` with `rel="noopener"`.
4. `.card-source`: "Fortune, press" (publisher, evidence), 13 px muted.
5. `.card-summary`: `summary`, 14.5 px, three-line clamp.
6. `.taxo-row`: failure source dots with labels (only those present); operation chips outlined in their colour with ink text; requirement chips with a plain border; the domain tag in sand outline.
7. `.card-foot`: subsection chips "4.1", "6.5" in section colours linking to `papers.html#s4_1`; "2 papers" when `related_papers` is non-empty; a check icon titled "Verified 2026-10-17".

**Chronology rail.** A `<nav aria-label="Months">` of buttons, newest at top, filling the rail height. Each month is a tick: a 1 px line and a bar whose length is proportional to the month's count (max 56 px), coloured by the dominant polarity; year labels at boundaries in mono 11 px. The `.chrono-cursor`, a 2 px ink marker, sits at the month whose separator is in view. Clicking a tick scrolls to the separator (smooth unless reduced motion) and sets `#2025-07`. Months emptied by filters fade to 30 percent.

**Item drawer (`#item/<id>`).** Header: date (precision spelled out when not a day), kind, polarity, title linking to the source, publisher and evidence beneath. Body: summary; "Actors" (vendor, deployer, model; non-null only); "Why it is here": failure sources with blurbs, requirements, operations grouped by lever, subsections with full titles linking to the Papers page; "Related papers": mini cards (label, title, year) from `papers.json`, fetched on first need, each opening `papers.html#paper/<key>`; "Verification": `verified_on`, `verification_note`, `added_by`, `lens`; tags; "Report a problem with this item" linking to the issue form with title "[stream] <id>". Footer: previous and next within the filtered list.

**Links back.** Subsection chips go to the Papers page; the paper count opens the related papers; clicking a failure source dot or operation chip on a card applies that filter (a filter icon appears on hover and focus; the chip has `aria-label="Filter by Observe"`).

**Transparency.** Besides the indicator, a `.pipeline-note` at the end of the wall: "Seeded by a verified sweep on 2026-10-17. Refreshed by a scheduled collector (RSS and search, then classification into the taxonomy by a language model); only items whose URL, date and claims were checked are published. Last run 2026-10-17 12:00 UTC. 137 items: 120 seed sweep, 15 collector, 2 reader submissions." Numbers computed from `stream.json`.

**Submit path.** "Submit an item" opens `https://github.com/yminglai/<repo>/issues/new?template=submit_item.yml&title=%5Bstream%5D%20` in a new tab; the repository name is one constant in `common.js`. The tooltip says what the form asks: URL, date, what happened, and whether it went well or badly. The page writes nothing itself.

**Empty states.** With filters: "No items match", removable filter chips, "Clear all". With no data (before the seed lands or on fetch failure): the pipeline note, the submit button, the taxonomy chips greyed out, no console error.

## 6 About page

One reading column (68 ch) with a right-hand mini table of contents at 1440. Headings as Title Case noun phrases: "The Survey" (full thesis, title, "[Authors]", draft v0.2, October 2026, PDF to come); "Who It Is For" (the three reader groups from `taxonomy.readers`); "Two Levers and a Test" (Figure 2 with caption, one paragraph on the two-level test); "How Agents Fail" (Figure 1 with caption); "The Collection" (5,421 retrieved, 1,788 placed with one primary subsection each, 239 cited, 160 grey items, 239 Chinese reading summaries, the build date, what `label`, `one_line` and `reason` mean); "The Stream" (the pipeline in plain words, the enumerations for kind, polarity and evidence, the verification rule, the submit path); "Colour" (a legend generated from `taxonomy.json`); "Cite" (BibTeX placeholder with copy button); "Data and Code" (each file under `site/data/` with a one-line description and link); "Licence and Privacy" ("no analytics, no cookies, no trackers").

## 7 Visual system

**Type.** Three Google Fonts, `display=swap`, preconnected, limited weights (about 120 KB total):

- Display: Newsreader (variable, optical size axis), 400 and 500, italic 400. Fallback `"Iowan Old Style", "Palatino Linotype", Georgia, serif`.
- UI and body: IBM Plex Sans, 400, 500, 600. Fallback `system-ui, -apple-system, "Segoe UI", Roboto, sans-serif`.
- Mono for dates, ids, counts: IBM Plex Mono 400. Fallback `ui-monospace, "SF Mono", Menlo, Consolas, monospace`.
- CJK: no web font; `"PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "Noto Sans CJK SC"` appended for `lang="zh-Hans"`.

Scale (16 px base) with line heights: `--fs-0` 13 px / 1.45 (mono, badges); `--fs-1` 14 / 1.5 (meta); `--fs-2` 14.5 / 1.5 (card summaries); `--fs-3` 16 / 1.55 (body); `--fs-4` 18 / 1.35 (card titles); `--fs-5` 22 / 1.25 (subsection heads); `--fs-6` 28 / 1.2 (section heads); `--fs-7` `clamp(2.25rem, 1.5rem + 3vw, 3.5rem)` / 1.1 (page titles); `--fs-8` `clamp(2.75rem, 2rem + 4.5vw, 4.75rem)` / 1.02, letter-spacing -0.01em (hero). Prose measure 68 ch, card text 60 ch. Numbers use `tabular-nums`.

**Colour tokens.** Declared once in `tokens.css` with the BRIEF values, one custom property per token (`--coral`, `--terracotta`, `--blue`, `--amber`, `--teal`, `--periwinkle`, `--forest`, `--purple`, `--gold`, `--sky`, `--pink`, `--sand`, `--slate`, `--ink`, `--gray`, `--gray-mid`, `--gray-light`, `--panel`, `--white`, `--link`). Semantic aliases: `--sec-s2` through `--sec-s10` to the operation colours, `--sec-s1`, `--sec-s3`, `--sec-s11` to gray; `--fs-mistakes`, `--fs-manipulation`, `--fs-misalignment`; `--pol-good`, `--pol-bad`, `--pol-mixed`. Elements set `--c` from `data-section`, `data-source` or `data-polarity`, and component CSS reads only `--c`.

Measured contrast sets the rules. On white the raw tokens fail AA for small text (coral 3.9:1, blue 3.4, purple 3.5, periwinkle 3.1, forest 3.1, terracotta 3.0, amber 2.4, teal 2.1, gold 2.0), and ink on solid token fills fails for coral (3.5), blue (4.0), purple (3.9) and gray (3.3). Therefore:

- Full-strength tokens are used only for bars, dots, borders, rails and display text of 28 px and up (where 3:1 applies, and only coral, blue, purple, periwinkle, forest and terracotta qualify).
- Coloured small text is `color-mix(in srgb, var(--c) 60%, var(--ink))`, giving 5.4 to 6.6:1 on white for the section colours except amber (4.5), so amber, teal, gold, sky and sand use 50 percent.
- Tinted fills are `color-mix(in srgb, var(--c) 14%, var(--bg))` with ink text; text never sits on a solid token.
- Muted small text is not `--gray` (4.1:1) but `color-mix(in srgb, var(--gray) 85%, var(--ink))`, about 5.5:1; `--gray` is reserved for 18 px and larger and for rules.

Light theme: `--bg` white, `--surface` panel, `--border` light gray, `--text` ink, body links blue mixed 60/40 with ink. Dark theme (`[data-theme="dark"]`, defaulting from `prefers-color-scheme`): `--bg` ink, `--surface rgba(255,255,255,.05)`, `--border rgba(255,255,255,.14)`, `--text` light gray (11.3:1), `--muted` medium gray (8.0:1); coloured small text becomes `color-mix(in srgb, var(--c) 65%, white)`, 5.6 to 9.2:1 on ink for every token; tinted fills use 18 percent. Bars, dots and borders keep raw tokens in both themes. Figures get a 1 px border in dark mode. The toggle stores one `localStorage` key and applies before first paint through a three-line inline script.

**Spacing.** 4 px base: `--sp-1` 4, `--sp-2` 8, `--sp-3` 12, `--sp-4` 16, `--sp-5` 24, `--sp-6` 32, `--sp-7` 48, `--sp-8` 64, `--sp-9` 96, `--sp-10` 128. Landing blocks are separated by `--sp-9` (`--sp-7` below 768).

**Radii, borders, shadows.** `--r-1` 4 px (chips, badges, kbd), `--r-2` 8 px (cards, inputs), `--r-3` 14 px (doors, panels), pill 999 px (segmented control). Borders 1 px `--border`; emphasis by 3 px bars in `--c`, not heavier borders. Shadows only on floating layers: drawer and popover `0 12px 40px rgba(46,46,46,.18)` (dark `.5`), scrim `rgba(46,46,46,.6)`. Cards have no shadow; on hover and focus-within they take a 1 px border in `--c` and, when motion is allowed, `translateY(-1px)`.

**Iconography.** Inline SVG only, 16 and 20 px, 1.5 px stroke, `currentColor`, `aria-hidden="true"` with a text alternative nearby. Set: arrow-right, arrow-up-right, search, sliders, check-circle, chevron-down, x, sun, moon, copy, and eight operation glyphs for the tiles and rail: alert-triangle (How Agents Fail), lock (Constrain), eye (Observe), hand (Intervene), compass (Steer), dial (Train), shield-check (Verify), layers (Deploy and Assure). No third-party logos; "GitHub" is written as text.

**Motion.** 150 ms (hover, focus), 250 ms (chips, drawer content), 450 ms (drawer slide, stage change); easing `cubic-bezier(.2,.7,.2,1)`; only `transform` and `opacity` animate; scroll-linked behaviour uses IntersectionObserver, never scroll handlers. Under `prefers-reduced-motion: reduce`: durations drop to 1 ms except 150 ms opacity fades, the live dot is static, the gap chart renders complete, `scrollIntoView` uses `behavior: auto`. The theme toggle never animates colours.

## 8 Components inventory

Shared (`site.css`, `common.js`): `.skip-link`, `.site-header`, `.wordmark`, `.site-nav`, `.nav-link`, `.nav-dot`, `.theme-toggle`, `.btn`, `.btn--primary`, `.btn--ghost`, `.chip`, `.chip--on`, `.badge`, `.count`, `.kbd`, `.live-indicator`, `.live-dot`, `.popover`, `.drawer` (with `-scrim`, `-head`, `-body`, `-foot`), `.skeleton`, `.empty-state`, `.visually-hidden`, `.site-footer`, `.lightbox`.

Landing (`landing.js`): `.hero`, `.hero-title`, `.hero-actions`, `.gap-chart`, `.doors`, `.door`, `.door--papers`, `.door--stream`, `.story`, `.story-beat`, `.story-stage`, `.failure-card`, `.ops-map`, `.ops-tile`, `.handover`, `.handover-panel`, `.mini-item`, `.polarity-bar`, `.figure-grid`, `.bibtex`.

Papers (`papers.css`, `papers.js`, `search.js`, `taxonomy.js`): `.papers-layout`, `.toc-rail`, `.toc-section`, `.toc-sub`, `.toolbar`, `.search-field`, `.results`, `.section-head`, `.sub-head`, `.paper-card`, `.paper-label`, `.paper-title`, `.paper-meta`, `.paper-line`, `.xref-row`, `.xref-chip`, `.badge--cited`, `.badge--score`, `.badge--zh`, `.badge--grey`, `.show-more`, `.also-group`, `.zh-summary`, `.zh-field`, `.zh-terms`.

Stream (`stream.css`, `stream.js`): `.stream-layout`, `.chrono-rail`, `.chrono-bar`, `.chrono-cursor`, `.stream-toolbar`, `.polarity-seg`, `.wall`, `.month-sep`, `.stream-card`, `.card-date`, `.kind-badge`, `.card-title`, `.card-source`, `.card-summary`, `.taxo-row`, `.fs-dot`, `.op-chip`, `.req-chip`, `.domain-tag`, `.card-foot`, `.sub-chip`, `.verified`, `.pipeline-note`, `.related-paper`.

Data attributes: `data-section`, `data-source`, `data-polarity` set `--c`; `data-state="gap|failures|operations"` on the stage; `data-theme` on `<html>`.

## 9 Responsive behaviour

**390 px.** Header 52 px, wordmark at 15 px, a menu button revealing the links as a sheet. Hero: eyebrow, title at the clamp minimum (44 px), lede, two doors stacked (120 px each, number at 32 px, bar kept), full-width buttons, the gap chart below at full width with 11 px labels. No sticky stage. Handover panels and figures stack. Papers: the rail becomes a horizontal chip strip under the toolbar (one chip per section, coloured dot and number); filters sit behind a "Filters (2)" button opening a bottom sheet; cards full width; the drawer is a full-screen panel with a back button. Stream: the rail becomes a 36 px strip with the current month and a "Jump to month" `<select>`; one-column wall; only the polarity control stays visible. Tap targets at least 44 px.

**768 px.** Hero top row stacks (title, then chart at 100 percent up to 520 px), doors side by side. Still no sticky stage. Papers: rail behind a toggle (280 px overlay); one-column cards; drawer full width. Stream: 48 px rail with ticks and year labels but no bars; two-column wall; drawer full width.

**1024 px.** Full header. Hero at 7/5. Sticky stage, 480 px tall. Papers: rail 220 px, one-column cards, drawer 480 px. Stream: 72 px rail with bars, two-column wall, filter row 2 behind the "Filters" button.

**1440 px.** As described in sections 3 to 5: container 1280, rail 264, results 880, drawer 560, three-column wall, filter row 2 open, stage 560 px. Above 1440 the container stays at 1280 and centres.

## 10 Feasibility, performance, risks

**Vanilla implementation.** Six ES modules, no bundler: `common.js` (theme bootstrap, URL state, cached `fetchJSON`, formatters, drawer and popover primitives, icon strings), `taxonomy.js` (section order, titles, colours, `linkTo`), `papers.js`, `search.js`, `stream.js`, `landing.js`. Every page is valid static HTML with its toolbar and empty regions in place before scripts run. No CDN dependency in the baseline. All paths relative, tested from `file://`, `python3 -m http.server 8765` and a GitHub Pages subpath.

**Performance.** First paint under one second: CSS under 24 KB; the hero is plain HTML and inline SVG; the landing page fetches only `stats.json` (under 2 KB) and `taxonomy.json` (about 60 KB) before interaction, and `stream.json` in `requestIdleCallback` with space reserved so nothing shifts. `papers.json` loads after first paint; parse and index take tens of milliseconds; at most a few hundred cards exist in the DOM (per-section lazy rendering, the 12-card cap, `content-visibility`). `summaries_zh.json` loads on the first drawer that needs it. Targets: Lighthouse performance 95 or above, accessibility 100, zero console errors in headless Chrome (guard every fetch, ship a favicon, reference no missing asset).

**Accessibility.** Landmarks (`header`, `nav`, `main`, `aside` for rails, `footer`), one `h1` per page, 2 px focus rings in `--link` on light and light grey on dark, focus trapping in drawers, `aria-current` in rails, `aria-pressed` on toggle chips, `aria-live="polite"` on result counts, `lang="zh-Hans"` on Chinese blocks, and colour never the only carrier: every dot and bar has a label or `aria-label`.

**Risks and what to cut first.**

1. The sticky three-state stage is the most code and layout risk. Cut first: three static SVG panels, already the behaviour below 1024.
2. Hand-drawn SVG labels must fit in fallback fonts; labels stay short, 11 to 14 px, wrapped with `<tspan>`, no `textLength`.
3. `stream.json` growth: past 2 MB the collector splits by year without changing card code; `stats.json` already carries the landing counts; the wall pages by 60.
4. The 2.2 MB Figure 2 must be re-encoded or it alone breaks the first-paint budget.
5. `<input type="month">` has no native picker in Safari; it degrades to text with pattern `YYYY-MM`.
6. Chronology bars need stable heights when filters change. Cut second: keep ticks and cursor, drop bars.
7. Lightbox and figure gallery: cut third, keep plain `<figure>` elements.

Order of work: tokens and shared header; Papers page (most content, settled contract); Stream page against the schema with a small fixture; landing page with static stage panels; then the sticky stage, chronology bars and lightbox if time allows.
