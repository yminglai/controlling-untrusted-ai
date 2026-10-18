# Concept B: Atlas

Design concept for the companion site of *Controlling Untrusted AI: A Survey*. Written 2026-10-17 against `BRIEF.md` and `SCHEMA.md`. Numbers below come from the real data: `corpus_full.json` (1,788 papers in 56 subsections, sizes 1 to 103, median 26; 191 cited arXiv papers; 149 empty one-liners; author lists up to 265 names), `grey_v2.json` (155 entries, 153 verified), `summaries_zh.json` (239 entries, almost all with four 发现 and six or more 术语), `outline.json` (11 sections, 56 subsections, 3 to 9 plan bullets each).

## 1 Idea and Signature Moments

Atlas treats the survey as a map and the stream as the weather over it. One diagram, the mechanism map (two levers, Verify, Deploy and Assure, and the three failure sources above them), is the site's only navigation metaphor: every page filters through the same seven operations and three failure sources, so a reader always knows where they stand in the taxonomy. The surface is dense with counts and compact cards, but the hierarchy is strict: one serif voice for the paper's words, one sans voice for the data, one mono voice for numbers and ids, and colour only where it means something.

Three signature moments:

1. **One map, two collections.** On the landing page a reader clicks *Observe* on the mechanism map. The two readouts beneath it change together: the corpus side lists the six subsections of Section 5 with their counts (70 papers in Guardrails and Action Monitors, 57 in Chain-of-Thought Monitoring, ...), the field side shows the stream items whose operation is `observe`, with their ticks lit on the timeline. The same click works on the Papers and Stream pages.
2. **The failure-source strip.** A thin horizontal timeline of every stream item, one small square per item, coloured coral, amber or purple by failure source (forest or gold when the item is a success or mixed). It runs under the stream entry card on the landing page and becomes the brushable axis at the top of the Stream page, so the field record is visible as a shape before any card is read.
3. **The bilingual reading card.** Opening a paper that has a structured Chinese summary shows the nine fields in fixed order, 定位 to 存疑, with the 部署启示 (deployer takeaway) set apart in a panel of the section colour, followed by the stream items that cite the paper or share its subsection. Paper, placement and field evidence on one screen.

## 2 Information Architecture and Navigation

Five static pages share one header: `index.html`, `papers.html`, `stream.html`, `about.html`, `404.html`. The header is 56 px, sticky, and carries the wordmark (the title in the serif), the nav links Papers, Stream, About, a disabled PDF link with the tooltip "arXiv link to come", and the theme toggle. On Papers and Stream the key `/` focuses the page search; `?` shows a keyboard sheet.

Deep links use the hash with `URLSearchParams` semantics, because GitHub Pages has no rewrites and the site must work from `file://`. The body of the hash is parsed as a query string; a bare token matching `^s\d+(_\d+)?$` is a shorthand for a section or subsection.

| Target | URL |
|---|---|
| Section or subsection | `papers.html#s5` or `papers.html#s5_2` (long form `#sub=s5_2`) |
| A paper (opens the drawer, scopes to its subsection) | `papers.html#paper=sharkey2025open` |
| Filtered paper list | `papers.html#sub=s5_2&year=2025,2026&cited=1&score=3&zh=1&q=monitor&sort=year` |
| Stream filter | `stream.html#polarity=bad&source=manipulation&op=observe&kind=incident&req=in-scope&domain=coding&from=2025-01&to=2025-12&q=injection` |
| Stream items for a subsection | `stream.html#sub=s6_5` |
| One stream item (scrolls to it, expands it) | `stream.html#item=2025-07-18-replit-agent-deleted-production-database` |
| Landing with a preselected operation | `index.html#op=observe` |
| About anchors | `about.html#corpus`, `#stream`, `#data`, `#cite` |

Multi-values are comma separated. Filter changes call `history.replaceState`; opening or closing a drawer calls `pushState`, so Back closes the drawer rather than leaving the page. Three cross-linking rules hold everywhere: a subsection id shown anywhere links to `papers.html#<sid>`; an operation chip on a stream card links to `stream.html#op=<id>`; the "In the field" count in a paper drawer links to `stream.html#sub=<sid>`. `404.html` reads the requested path and offers the four pages plus a search box that forwards to `papers.html#q=`.

## 3 Landing Page

Content width 1,200 px at 1440; blocks top to bottom with heights at that width.

1. **Header** (56 px). Described above. Background `--surface`, 1 px hairline below.
2. **Title band** (about 280 px). Left seven twelfths: `h1` "Controlling Untrusted AI" in Newsreader 56/60, with "A Survey" on the second line in `--text-muted`; beneath it a mono status line, 13 px: "Draft v0.2 · October 2026 · [Authors] · arXiv link to come". Right five twelfths: the first three sentences of `taxonomy.thesis` in Newsreader 18/28.
3. **Two entries** (two equal cards, about 280 px tall, `--surface`, 1 px border, radius 8). Two cards of equal weight, each with an eyebrow, a big numeral, a verb button and a distinct accent, make both parts unmistakable in five seconds.
   - Left, eyebrow "PART ONE", `h2` "The Paper Collection". Stat tiles inline: **1,788** papers, **56** subsections, **239** cited in the PDF, **160** grey items (from `stats.json`). A sparkline of 16 bars, 2011 to 2026, in `--text` (908 of the papers are from 2026, so the shape is a sharp rise). One line: "Every paper placed in one subsection of the survey, with a method-style label and a one-line summary." Primary button "Browse the papers"; secondary link "Jump to a subsection" that opens a `datalist` of the 56 titles. Accent: a 4 px rule in `--text` along the left edge.
   - Right, eyebrow "PART TWO", `h2` "The Live Stream". Stat tiles: **N** items, **N** incidents and near misses, **N** controls that worked, and "updated 3 h ago" in mono with a 6 px dot (static under reduced motion). The compact failure-source strip (last 12 months, 48 px). A polarity bar showing good, bad and mixed proportions in forest, coral and gold. One line: "Field evidence on deploying agents, classified into the same subsections." Primary button "Open the stream"; secondary link "Submit an item". Accent: a 4 px left rule split vertically coral over forest.
4. **The Mechanism Map** (about 540 px including readout). `h2` plus kicker "Two levers, verification, deployment. Select an operation to filter both collections." The map is a CSS grid of real `<button>` nodes, not an SVG, so it is keyboard native; a decorative SVG layer draws the bracket from Observe, Intervene and Steer into Verify and the base line to Deploy and Assure, as in Figure 2.
   - Row 0: label "How Agents Fail §2" and three failure-source chips (Mistakes, Manipulation, Misalignment) with counts of papers in 2.1, 2.2 and 2.3 plus 2.4, and counts of stream items.
   - Row 1: lever label "Lever 1 · change the deployment", then nodes Constrain §4, Observe §5, Intervene §6. Verify §9 occupies the last two columns and spans rows 1 and 2.
   - Row 2: "Lever 2 · change the model", then Train §8 and Steer §7 (order as in Figure 2).
   - Row 3: a 40 px bar "Deploy and Assure §10" spanning the node columns; to its right the two-level test in 13 px italic: "L1 does it work if the agent is indifferent; L2 does it work if the agent tries to defeat it and knows how it works."
   - Node anatomy (min height 96 px): a 20 px line icon top right, "§5" in mono, the label in Newsreader 20, the figure's keywords in 13 px muted ("classifiers, monitors, probes, logs, review"), and two mono counts bottom right, "226 papers · 41 items". Fill `color-mix(token 18%, --bg)`, border 1 px `color-mix(token 60%, --bg)`. Selected: border 2 px token, fill 28 %, other nodes at 55 % opacity. Roving `tabindex`, arrow keys move, Enter toggles, Esc clears, `aria-pressed` reflects state.
   - Readout, two columns of about 240 px: "In the corpus" lists the selected section's subsections as rows with title, a primary-count bar scaled to 103 (the largest subsection), the cited count, and a link; with nothing selected it shows the eight operation sections as bars. "In the field" shows the strip filtered to the operation, the three latest item titles with date and polarity mark, and "All 41 items in the stream". Numerals tween over 240 ms, disabled under reduced motion.
5. **Three Failure Sources** (three tiles, about 170 px). Each: colour dot, name, the one-sentence blurb from `taxonomy.failure_sources`, "N papers · N stream items", and the defining subsections (Mistakes: 2.1 Compounding Mistakes; Manipulation: 2.2 Prompt Injection and Memory Poisoning; Misalignment: 2.3 Reward Hacking and Harness Tampering, 2.4 Deception and Loss of Control). Click goes to `stream.html#source=<id>`.
6. **Fifty-Six Rows** (about 500 px collapsed). A dense table of the survey: 11 group rows (number, title, one-line purpose clamped, total count with bar, 3 px left rule in section colour), each expanding to its subsection rows with four mono columns headed Primary, Cited, Cross, Grey, and a fifth 中文 column. Row click goes to `papers.html#<sid>`. "Expand all" opens every group (about 1,900 px).
7. **Latest from the Stream** (about 320 px). Six compact stream cards (no summary) in a 3 by 2 grid and a link to the Stream page.
8. **Footer** (about 220 px). Four columns: Data (the six JSON files with sizes and `generated` dates), Pipeline (one paragraph on the collector, links to the workflow and the issue template), Cite (BibTeX disclosure, placeholder authors), Site (no analytics, no cookies, licence, theme). Last line: "Generated 2026-10-17 · stream updated <datetime>".

The landing page fetches `stats.json` and `taxonomy.json` before the map renders (both small) and `stream.json` after first paint for the strip and the latest items. It never loads `papers.json`.

## 4 Papers Page

**Layout at 1440.** Three panes: section rail 280 px, main column fluid with cards at most 760 px wide, detail drawer 560 px that pushes the main column when open. The page header reads "Papers · 1,788" with a breadcrumb of the active scope, "§5 Observing Agent Behaviour › 5.2 Guardrails and Action Monitors".

**Rail.** "All sections" at the top, then the 11 sections as disclosure groups with a 3 px colour rule, title and mono count. Expanded groups list subsections with number, title and primary count. The active section is expanded by default; others open on click. Counts are live: with filters active a row reads "12 / 70". The rail is sticky and scrolls independently; it is a nested list of links with `aria-current` on the active row.

**Filter bar** (sticky under the header, 48 px): search input with placeholder "Search 1,788 papers: title, label, author, summary"; Year as multi-select chips 2026, 2025, 2024, 2023, 2022 and earlier; "Cited in the PDF" toggle; Score as a three-way segment All / 3 must-cite / 2 relevant; "Chinese summary" toggle; "Include grey items" toggle, on by default; Sort as Reading order (file order), Year newest, Title. Active filters become removable chips with "Clear all". The results header states the scope: "70 papers in 5.2 Guardrails and Action Monitors · 10 cited · 12 with Chinese summary · 0 grey".

**Search behaviour.** No library. At load, each paper gets a lowercase search string of `label + title + authors + one_line + key + arxiv_id`; filtering 1,788 strings takes a few milliseconds. Minimum two characters, debounce 120 ms. Ranking: label or title prefix match, then title contains, then author, then one-line; ties keep file order. Matches are wrapped in `<mark>`. A query widens the scope to all sections and groups results under sticky section headers, with a chip "within 5.2 only" to narrow back; rail counts update to the query. Empty result: "No papers match 'xyz' in 5.2. Search all sections (3 matches) or clear filters."

**Paper card**, fields in order:

1. Left rule, 3 px, section colour, full card height.
2. Meta line, mono 12: subsection number and title as a link ("5.2 Guardrails and Action Monitors"); year right-aligned.
3. Label line: a filled dot for score 3 or a hollow dot for score 2 (tooltip "score 3, must-cite"), then the method-style label in Inter 13 semibold, then badges: "Cited" (ink pill) when `selected`, "中文" (sky-bordered pill) when `has_zh`, "Grey" (sand-bordered pill) for grey items.
4. Title, Newsreader 18/24, opens the drawer.
5. Authors, Inter 13 muted: up to three names in full; otherwise the first two and "and N more"; from 50 names, the first one and "and N more" (the o1 system card has 265).
6. One line, Inter 14/20, clamped to two lines. When `one_line` is empty (149 papers) the card shows `reason` prefixed "Why here:" in muted italic.
7. Footer, 12 px: cross-reference chips "also 2.1 · 11.2" (three shown, then "+n"); arXiv id as an external link, or venue for grey items; "Summary" link when `has_zh`; reading rank "#5" when present.

Card height is about 150 px; a "Compact" density toggle drops lines 5 and 6 to give 72 px rows.

**Detail drawer**, top to bottom: a 6 px band in the section colour; breadcrumb; label; title in Newsreader 24; full author list, collapsed after eight with "show all 265"; year; action row with arXiv abstract, arXiv PDF, copy bib key, copy link, close. Then "In the survey": the primary subsection with its title, a disclosure "What this subsection covers" holding the plan bullets from `taxonomy.json`, and the placement in words, "Cited in the PDF · score 3, must-cite · reading rank 5". Then "One line" and "Why it is here" (`reason`). Then "Cross-references": each `also` entry as "§2.1 Compounding Mistakes · score 3", a link that re-scopes the list (one paper, `greenblatt2023ai`, has 21; the list scrolls inside a 240 px box). Then, when `has_zh`, "Reading summary · 中文": `summaries_zh.json` is fetched on the first open and cached in module scope; a skeleton shows meanwhile; the panel has `lang="zh-Hans"`, line height 1.75, and renders a definition list in fixed order with bilingual labels: 定位 Positioning, 问题 Problem, 方法 Method, 发现 Findings (ordered list), 部署启示 Deployer takeaway (set in a panel with a left rule in the section colour), 局限 Limitations, 与小节关系 Relation to the subsection, 存疑 Doubts (muted italic), 术语 Terms (chips "term = 术语"), and a meta line "阅读深度 部分 · text depth partial". Then "In the field": the count of stream items whose `subsections` include the primary or whose `related_papers` include the key, up to five titles with dates and polarity marks, and a link to the filtered stream; the block is hidden if `stream.json` is unavailable. Finally previous and next within the current result list, keys `j` and `k`, with "12 of 70". The drawer traps focus, closes on Esc, returns focus to the card, and writes `paper=` to the hash.

**Empty and loading states.** Six skeleton cards with a shimmer that is static under reduced motion. Fetch failure: "The paper list could not be loaded." with a Retry button and no console error. Zero results as above. Every subsection has at least one primary paper (11.5 has exactly one), so emptiness arises only through filters.

**Handling 1,788 items.** One `fetch` of `papers.json` after first paint (about 250 KB compressed); parse into a `Map` by key and an index by subsection. Only the active scope is rendered: a single subsection is at most 103 cards; a whole section is at most 356 (Section 8), rendered in chunks of 48 through a sentinel and `IntersectionObserver`; "All sections" uses the same chunking so the DOM never holds more than about 400 cards. If parse time on a mid-range laptop exceeds 200 ms, `build_data.py` can additionally emit `papers.<section>.json`; this would be an extension to `SCHEMA.md` and is not assumed.

## 5 Stream Page

**Layout at 1440.** Page header "Stream · N items", "updated 2026-10-17 12:00 UTC (3 h ago)", and the "Submit an item" button. Beneath it the full timeline (140 px). Then two columns: filter rail 260 px and the feed at most 800 px wide. Items expand in place; there is no drawer.

**Timeline.** An inline SVG, full width, months on the x axis from the earliest item to the current month. Each item is an 8 px square, 2 px gap, stacked per month and coloured by `failure_sources[0]`: Mistakes coral, Manipulation amber, Misalignment purple; items with no failure source take polarity colour, good forest, mixed gold, otherwise medium gray. Stacks cap at 12 squares with a "+n" numeral above. A brush on the axis selects a month range with draggable handles and sets `from` and `to`; double click clears. Hovering a square shows title, date and kind; clicking scrolls the card into view and flashes its left rule. In light theme every square has a 1 px outline of `color-mix(token 70%, --ink)` so teal, amber and gold squares pass 3:1 non-text contrast. The SVG is `aria-hidden`; two visually hidden month selects provide the same range control, and "Show as table" lists counts per month and source. The same module draws the 48 px strip on the landing page without the brush.

**Filters** (rail, each a `fieldset` with facet counts that reflect the other active filters): Polarity (good, bad, mixed); Failure source (three); Operation (constrain, observe, intervene, steer, train, verify, deploy in section colours); Kind (incident, near-miss, deployment, safety-feature, evaluation, research, policy, disclosure); Requirement (correct, compliant, in scope, within budget, safe); Domain (a select with the 14 values and counts); Evidence (six values, inside a "More" disclosure); Date range (from and to month inputs mirrored by the brush); Search (title, summary, publisher, actors, tags, with the same debounce and highlighting as Papers). Active chips row with "Clear all".

**Stream card**, fields in order:

1. Left rule, 3 px, polarity colour.
2. Row 1, mono 12: date rendered by precision ("18 Jul 2025", "Jul 2025", "2025"); kind badge with a 16 px icon; domain chip; publisher right-aligned.
3. Title, Newsreader 18, linking to `url` with `rel="noopener"` and an external icon.
4. Summary, Inter 14/20, in full.
5. Taxonomy row: failure-source chips (dot and label), operation chips (section-colour dot and label, linking to the stream filter), requirements as small caps text "in scope · correct".
6. Subsection links, up to four: "§6.5 Reversibility and Rollback", each to `papers.html#s6_5`.
7. "Details" disclosure: actors as "vendor · deployer · model" (nulls omitted), evidence type, tags, related papers as label and title linking to `papers.html#paper=<key>`, verification line "Verified 2026-10-17 · URL fetched; date and claims confirmed from the article body", `added_by` and `lens`, and "Report a problem" linking to the issue template with the item id prefilled.

A collapsed card is about 200 px tall. The feed is sorted by date descending with sticky month dividers ("July 2025 · 4 items"); an alternative sort "Recently verified" uses `verified_on`.

**Pipeline transparency.** A panel "How this feed is made" at the bottom of the rail: seeded once by a verified sweep (`sources[0]`); refreshed by a scheduled collector that reads RSS feeds and search results and classifies with a language model; every published item has a working URL that was fetched and a verification note; unverifiable items are not published; counts by `added_by` and by kind; links to `pipeline/feeds.yml`, `collect_news.py`, `classify.py` and the workflow file. "Last run" is `stream.generated`; if it is older than 14 days an amber note reads "The collector has not run since <date>".

**Submit path.** The button opens `<repo>/issues/new?template=submit_item.yml` with the title prefilled "[stream] "; the template asks for URL, date, what happened, kind and polarity, and optional subsection guesses. The About page states that submissions are verified before publication.

## 6 About Page

Single column, 720 px, Newsreader prose at 17/28 with anchored `h2`s. *The Survey*: the thesis paragraph, the two figures as `<figure>` elements with captions in the paper's wording (Figure 1 the control gap, four operations, three failure sources; Figure 2 two levers, Verify, five questions), and the three reader groups. *The Two-Level Test*: L1 and L2 in two sentences. *How the Corpus Was Built*: 5,421 retrieved, 1,788 placed with one primary subsection each, 828 at score 3 and 960 at score 2, 239 cited in the PDF; method-style labels; 160 grey items verified against their source pages, mostly Redwood Research, Anthropic Alignment Science, METR, Google DeepMind, Apollo Research and OpenAI posts. *How the Stream Is Collected*: the enumerations from `SCHEMA.md` in a table, the verification policy, the cadence. *Data and Downloads*: the six JSON files with field lists and sizes. *Cite*: BibTeX with placeholder authors. *Changelog*. *Authors*: "[Authors]". *Licence*.

## 7 Visual System

**Type.** Newsreader (variable, optical size 6 to 72) for headings, paper and item titles, the thesis and About prose; fallback Georgia, "Times New Roman", serif. Inter (variable) for body, cards and controls; fallback -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif. IBM Plex Mono for numerals, ids, dates and counts; fallback "SF Mono", Menlo, Consolas, monospace. Chinese text uses no web font: `:lang(zh-Hans)` sets `"PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "Noto Sans CJK SC", "Source Han Sans SC", sans-serif`. One Google Fonts CSS2 request with `display=swap`, preconnects to `fonts.googleapis.com` and `fonts.gstatic.com`, and `size-adjust` on the fallbacks to limit layout shift. Scale in px/line-height: display 56/60; page title 36/40; `h2` 28/34; `h3` 20/26; card title 18/24; prose 17/28; UI 14/20; small 13/18; micro 12/16; big numeral 40/44 in Newsreader with `font-variant-numeric: lining-nums tabular-nums`; mono 13/16.

**Colour.** Tokens in `tokens.css` exactly as named in the brief: `--coral #D95358`, `--terracotta #E27553`, `--blue #598DD2`, `--amber #E09A3B`, `--teal #65C2B9`, `--periwinkle #8D86E8`, `--forest #62A16E`, `--purple #A37CAD`, `--gold #D1B745`, `--sky #6FCBEF`, `--pink #E072AF`, `--sand #C7A678`, `--slate #75A4B5`, `--ink #2E2E2E`, `--gray #7D7D7D`, `--gray-mid #C7C7C7`, `--gray-light #EAEAEA`, `--panel #F7F7F7`, `--white #FFFFFF`, `--link #598DD2`. Semantic aliases: `--sec-s2` coral, `--sec-s3` gray, `--sec-s4` terracotta, `--sec-s5` blue, `--sec-s6` amber, `--sec-s7` teal, `--sec-s8` periwinkle, `--sec-s9` forest, `--sec-s10` purple, `--sec-s1` and `--sec-s11` gray; `--src-mistakes` coral, `--src-manipulation` amber, `--src-misalignment` purple; `--pol-good` forest, `--pol-bad` coral, `--pol-mixed` gold; grey items sand.

Light theme surfaces: `--bg` white, `--surface` panel, `--border` gray-light, `--border-strong` gray-mid, `--text` ink, `--text-muted` gray, `--focus` link. Dark theme (`[data-theme=dark]`, default from `prefers-color-scheme`, stored in `localStorage`): `--bg color-mix(in srgb, var(--ink) 80%, black)`, `--surface` ink, `--border color-mix(in srgb, var(--ink) 70%, var(--gray-light))`, `--text` gray-light, `--text-muted` gray-mid, `--link color-mix(in srgb, var(--link) 75%, white)`. Every dark value derives from the tokens, so nothing new is introduced.

Three rules keep colour functional and accessible. Fills: `color-mix(token 18%, --bg)` light, `28%` dark, always with `--text` on top. Coloured text only through derived variants, light `color-mix(token 70%, --ink)`, dark `color-mix(token 70%, white)`, because raw teal (2.0:1), amber (2.3:1) and gold (1.9:1) fail on white. Raw tokens only for dots, rules, bars and timeline squares, with a 1 px darker outline in light theme where the mark carries meaning. A script in `pipeline/tests/` computes WCAG ratios for every text variant in both themes and fails under 4.5:1.

**Spacing, shape, depth.** Scale 4, 8, 12, 16, 24, 32, 48, 64, 96. Radii 4 for chips and badges, 8 for cards and map nodes, 12 for the drawer and sheets. Borders 1 px `--border`; inputs `--border-strong`; focus ring 2 px `--focus` with 2 px offset, never removed. Cards carry no shadow; the drawer and sheets use `0 12px 32px rgba(0,0,0,.18)`, doubled in dark theme.

**Iconography.** One inline SVG sprite per page (`<svg hidden><symbol id="i-…">`), 16 px UI glyphs at stroke 1.5 in `currentColor`: external, search, close, chevron, filter, copy, check, arrow-right, sun, moon, table. Seven 20 px operation glyphs drawn in the same stroke: lock (Constrain), eye (Observe), hand (Intervene), wheel (Steer), weights (Train), shield-check (Verify), stack (Deploy and Assure). No icon fonts, no raster icons, no third-party marks; "GitHub" is written as text.

**Motion.** 160 ms ease-out for hover and focus; 240 ms for the drawer slide, numeral tweens and node selection; nothing moves on its own. `prefers-reduced-motion: reduce` sets every duration to 0 ms and removes the shimmer and the update dot.

## 8 Components Inventory

| Component | Class | Notes |
|---|---|---|
| Header, nav, theme toggle | `.site-header`, `.site-nav`, `.theme-toggle` | sticky, 56 px |
| Title band | `.title-band`, `.title-band__title`, `.title-band__status`, `.title-band__thesis` | landing only |
| Entry card | `.entry`, `.entry--corpus`, `.entry--stream`, `.entry__eyebrow`, `.entry__stats`, `.entry__cta` | the two parts |
| Stat tile | `.stat`, `.stat__value`, `.stat__label` | big numeral 40/44 |
| Sparkline | `.spark`, `.spark__bar` | 16 bars by year |
| Polarity bar | `.pol-bar`, `.pol-bar__seg--good/--bad/--mixed` | proportions |
| Mechanism map | `.mech`, `.mech__lever`, `.mech__node`, `.mech__node--constrain …--deploy`, `.mech__verify`, `.mech__base`, `.mech__sources`, `.mech__links` (SVG layer), `.mech__readout` | buttons with `aria-pressed` |
| Failure-source tile | `.source-tile`, `.source-tile--mistakes/--manipulation/--misalignment` | landing block 5 |
| Sections table | `.rows`, `.rows__group`, `.rows__sub`, `.rows__count` | 56 rows |
| Section rail | `.rail`, `.rail__section`, `.rail__sub`, `.rail__count` | papers page |
| Filter bar and chips | `.filters`, `.filters__search`, `.filters__active`, `.chip`, `.chip--on`, `.chip--sec-s5`, `.chip--src-mistakes`, `.chip--pol-good`, `.segment`, `.toggle` | shared |
| Paper card | `.paper`, `.paper__rule`, `.paper__meta`, `.paper__label`, `.paper__title`, `.paper__authors`, `.paper__line`, `.paper__foot`, `.paper--compact` | fields in section 4 |
| Badge | `.badge`, `.badge--cited`, `.badge--zh`, `.badge--grey`, `.score-dot`, `.score-dot--2` | |
| Drawer | `.drawer`, `.drawer__band`, `.drawer__head`, `.drawer__actions`, `.drawer__section`, `.drawer__nav` | push at 1440, overlay below |
| Chinese summary | `.zh`, `.zh__field`, `.zh__term`, `.zh__takeaway`, `.zh__meta` | `lang="zh-Hans"` |
| Timeline | `.timeline`, `.timeline__axis`, `.timeline__stack`, `.timeline__sq`, `.timeline__brush`, `.timeline__handle`, `.timeline--compact` | SVG |
| Stream card | `.item`, `.item__rule`, `.item__meta`, `.item__title`, `.item__summary`, `.item__taxonomy`, `.item__subs`, `.item__details`, `.kind-badge`, `.kind-badge--incident …` | fields in section 5 |
| Month divider | `.month-divider` | sticky |
| Pipeline panel | `.pipeline`, `.pipeline__stale` | amber note |
| States | `.skeleton`, `.empty`, `.error`, `.toast` | |
| Utilities | `.mono`, `.num`, `.sr-only`, `.icon`, `.prose` | |

## 9 Responsive Behaviour

**390.** One column. Header shows the wordmark and a menu button; the theme toggle moves into the menu. Title band stacks, display size 36/40. The two entry cards stack with stat tiles in a 2 by 2 grid; the strip stays 48 px. The mechanism map becomes a vertical list: lever labels as small headers, nodes full width at 64 px with keywords hidden, Verify and Deploy and Assure as ordinary rows, failure-source chips scroll horizontally; the readout stacks. Fifty-Six Rows shows only Primary and Cited columns. On Papers the rail becomes two selects (section, subsection) above the list; filters live in a bottom sheet opened by "Filters (3)"; cards drop the footer rank and show two cross-reference chips; the drawer is a full-screen sheet. On Stream the timeline scrolls horizontally with scroll snap to years, the brush is replaced by the month selects, filters move to a sheet, and cards wrap taxonomy chips to two rows.

**768.** Two columns for entry cards and stat tiles (3 by 2). The map keeps the grid with Verify as a full-width row under the levers. Papers: the rail collapses into a disclosure above the list; the drawer overlays at 100 % width with a scrim. Stream: rail becomes a horizontal filter bar with the long fieldsets in a sheet; timeline keeps the brush.

**1024.** Papers: rail 240 px visible, main fluid, drawer overlays 480 px from the right without pushing. Stream: rail 240 px, feed fluid. Landing: content width 960, map keywords shown.

**1440.** The layout described in sections 3 to 5: 1,200 px landing, three-pane Papers with a pushing 560 px drawer, 260 px stream rail, full timeline.

## 10 Feasibility, Performance, Risks

**Modules.** `common.js` (theme, hash parsing and writing, cached `fetch` with a version query from `stats.generated`, date and number formatters, relative time, focus trap, sprite helper); `taxonomy.js` (loads `taxonomy.json`, exposes colour and title lookups, renders the mechanism map and the sections table); `search.js` (search-string builder, ranker, highlighter, debounce); `papers.js` (rail, filters, chunked list, drawer, Chinese summary loader, field-evidence block); `stream.js` (timeline, facets, feed, pipeline panel). CSS: `tokens.css` (about 3 KB), `site.css` (about 18 KB), `papers.css` and `stream.css` (about 8 KB each). No dependencies.

**Performance plan.** First paint under 1 s: HTML plus CSS plus the page module under 60 KB compressed before data; fonts swap in; `stats.json` and `taxonomy.json` are fetched in parallel with `rel=preload`. `papers.json` loads only on the Papers page after first paint behind skeletons; `summaries_zh.json` (about 400 KB) only on the first drawer that needs it; `stream.json` lazily on the landing and immediately on Stream. JSON requests carry `?v=<generated>` so GitHub Pages caching never serves a stale feed. Rendering is scoped and chunked as described. Headless Chrome is run against all five pages at 1440 and 390 in both themes with `--virtual-time-budget=5000`, asserting zero console messages at error level; every `fetch` has a handled failure path.

**Risks.** Headless Linux without CJK fonts renders the Chinese panel as boxes; the check runs on the Mac, and the About page notes the system-font choice. Teal, amber and gold are weak on white; the derived text variants and outlines handle it, and the contrast script guards regressions. The timeline grows unbounded; above about 1,500 items the month stacks cap and `collect_news.py` could split `stream.json` by year (a schema extension). Hash routing with `pushState` must be tested against Back and Forward on Safari. The mechanism map is a large keyboard surface; the roving tabindex must be verified with VoiceOver. `papers.json` parse time on low-end machines is unmeasured; the per-section split is the fallback.

**Cut order.** First the timeline brush (keep the static strip and the month selects); then the "In the field" block inside the paper drawer; then the sparkline and polarity bar in the entry cards; then facet counts that reflect other filters (static counts instead); then the landing readout under the map (keep the map as plain links). The map itself, the two entry cards, the paper drawer with the Chinese summary, and the stream card with its taxonomy row are not cut.
