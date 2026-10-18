# Concept A: Journal companion

Design concept for the companion website of *Controlling Untrusted AI: A Survey*, written 2026-10-17 against `BRIEF.md`, `SCHEMA.md`, and the real data: 1,788 arXiv papers (908 from 2026, 417 from 2025, a tail back to 2011), 160 reports and posts, 239 Chinese reading notes, 56 subsections sized from 1 paper (11.5) to 103 (8.2). Labels are at most 27 characters; titles run to 176; one-line summaries have a median of 149 characters and are empty for 149 papers; author lists reach 265 names; one paper is cross-referenced into 21 subsections. Everything below is sized for those numbers.

## 1. Idea

The site is set like a journal, not a dashboard: the survey's table of contents is the primary navigation, and every line of it opens into the papers placed under it, so the structure of the paper and the structure of the corpus are one object. Beside the contents, in the same spread, runs a dated ledger of what has happened to deployed agents in the world, each entry filed under the same subsection ids, so the reader sees the argument on the left and the field evidence on the right. Type carries the hierarchy (a serif display face, small-caps running heads, hairline rules); colour is kept for the survey's own signals: section identity, failure source, polarity.

Three signature moments:

1. **The front-page spread.** Below the title, two columns under two running heads of equal weight: THE PAPER COLLECTION on the left as an eleven-line table of contents with a 3 px colour rule per section and the paper count in the margin; THE LIVE STREAM on the right as a dated ledger of the twelve most recent items, each with a polarity dash. A vertical hairline separates them. Nothing else competes.
2. **Opening a contents line.** On the papers page a subsection title ("5.3 Chain-of-Thought Monitoring") becomes the running head, its plan bullets fold out as "What this subsection covers", and the catalogue entries fall in below in the survey's order: cited first, then score, then reading rank. The section colour appears only as a thin margin rule and as the square mark before each label.
3. **The ledger entry that points back into the contents.** Expanding a stream row reveals its classification line: failure source, control operation, requirement, and the subsection links in section colour. Clicking "4.1 Least Privilege" lands on that subsection in the papers page; the subsection head there shows "3 items in the stream" pointing back. The taxonomy is the binding between the two halves.

## 2. Information architecture and navigation

Five HTML files, as fixed in the brief: `index.html`, `papers.html`, `stream.html`, `about.html`, `404.html`. Every page shares the masthead: running head left (*Controlling Untrusted AI: A Survey*, small caps), navigation right (Papers, Stream, About), theme toggle, GitHub link. All links are relative.

Routing is client-side on `location.hash`. The part of the hash before `?` is the route; the part after is parsed with `URLSearchParams`. `hashchange` drives rendering; nothing reloads. Closing a drawer calls `history.back()` when the previous entry is on the same page, otherwise it replaces the hash. `document.title` is updated per route ("5.3 Chain-of-Thought Monitoring · Papers · Controlling Untrusted AI").

`papers.html`

- `#s5`: section 5 open in the rail, scrolled to the section head.
- `#s5_3`: subsection 5.3 scrolled into view, its section expanded.
- `#paper/terekhov2025adaptive`: detail drawer for that bib key, opened over its home subsection.
- `#grey/institute2025introducing`: detail drawer for a report or post.
- `#s5_3?cited=1&zh=1&years=2024-2026&score=3&q=monitor&sort=year`: filters scoped to 5.3.
- `#all?q=monitor&sec=s5,s9`: search across the whole corpus, optionally restricted to sections.
- Filter keys: `q`, `years` (`YYYY-YYYY`), `cited` (`1`), `score` (`3`), `zh` (`1`), `sort` (`survey | year | title`), `sec` (comma list, only with `#all`), `density` (`full | compact`).

`stream.html`

- `#` (empty): the whole ledger, date descending.
- `#item/2025-07-18-replit-agent-deleted-production-database`: that entry expanded and scrolled to.
- `#?polarity=bad&source=manipulation&op=observe&kind=incident&req=in-scope&domain=coding&evidence=first-party&from=2025-01&to=2026-10&q=replit`: filters; every key accepts a comma list; `from`/`to` are `YYYY-MM`.
- `#s4_1`: shorthand for "items whose `subsections` include s4_1" (what the papers page links to).
- `#paper/khan2026token`: shorthand for "items whose `related_papers` include that key".

`about.html`: `#taxonomy`, `#corpus`, `#notes`, `#stream`, `#submit`, `#cite`, `#data`, `#colophon`.

`404.html`: masthead, the line "This page is not in the contents", links to the four pages.

Cross-links are symmetric: subsection heads on the papers page link to `stream.html#sX_Y`; ledger rows link to `papers.html#sX_Y` and `papers.html#paper/<key>`; landing contents lines link to `papers.html#sX` and `#sX_Y`; landing ledger rows link to `stream.html#item/<id>`.

## 3. Landing page

Grid: 12 columns, max width 1,280 px, 24 px gutters, 48 px outer margin at 1440. Vertical spacing between blocks 96 px. Top to bottom:

**Block 1, Masthead (56 px).** Running head in Inter small caps 11/16, letter-spacing 0.08em. Navigation items in Inter 14. Theme toggle (sun/moon inline SVG). GitHub icon link. Below it, on this page only, a double hairline (1 px rule, 3 px gap, 1 px rule) in `--rule`; on other pages a single hairline.

**Block 2, Title block (about 320 px at 1440).** Title in Newsreader 400, `clamp(40px, 6vw, 72px)`, line-height 1.05, letter-spacing -0.01em, spanning 8 columns so the title breaks after "AI:". Beneath it the dek: the first two sentences of the thesis from `outline.json`, verbatim, in Newsreader 22/32 at 60ch. Then "[Authors]" in Inter small caps and "Draft v0.2 · October 2026 · arXiv link to come" in Inter 13. Three text buttons with arrow icons: "Read the paper (PDF placeholder)", "Browse the papers", "Open the stream". No hero image; the title is the hero.

**Block 3, The spread (the five-second block).** Two columns with a vertical hairline between them. Left, 7 columns, running head THE PAPER COLLECTION and under it, in IBM Plex Mono 13, "1,788 papers · 160 reports and posts · 56 subsections" from `stats.json`. Right, 5 columns, running head THE LIVE STREAM and "N items · updated 17 Oct 2026" from `stream.json.generated`.

The left column is the table of contents: eleven rows, each with a 3 px vertical rule in the section colour (gray for sections 1, 3, 11), the section number in mono 13, the title in Newsreader 24/30, the primary count right-aligned in mono 13, and under the title the subsection titles in Inter 13 separated by middle dots ("4.1 Least Privilege · 4.2 Sandboxing and Isolation · ..."). Hover turns the row `--bg-panel`; the title links to the section, each subsection title to itself. Counts come from `taxonomy.json`, so the column renders without `papers.json`.

The right column is the ledger: the twelve most recent items from `stream.json` under month heads ("October 2026", Newsreader 17 italic). Each row: date in mono 12 ("17 Oct"), a 3 × 14 px dash in the polarity colour, the kind in Inter small caps 11, the title in Newsreader 17/22 clamped to two lines, the publisher in Inter 13. Footer "All N items". With zero items before seeding the column reads "The ledger opens with the first verified sweep" plus the submit link; no placeholder rows.

Why both parts are unmistakable in five seconds: identical running heads of equal weight; the two figures ("1,788 papers", "N items · updated 17 Oct") directly beneath; two different colour languages (section rules left, polarity dashes right); the vertical hairline; and the buttons in Block 2 that name both. At 1440 × 900 the spread begins near y = 380 px, above the fold.

**Block 4, Plates.** Figure 1 and Figure 2 two-up (6 columns each) at 1024 and above, stacked below. Captions in Newsreader italic 15/22: "Figure 1. The control gap, four operations, three failure sources." and "Figure 2. Two levers, Verify, and the five questions asked of every mechanism." Images carry width and height attributes and `loading="lazy"`; clicking opens the full raster in a native `<dialog>`. Figure 2 (2.2 MB) is re-encoded to under 300 KB at 2,000 px for the page.

**Block 5, Who this is for.** Three columns from `taxonomy.json.readers`, each with a small-caps head ("Researchers", "Deploying teams", "Evaluators and policy staff") and the reader paragraph in Newsreader 16/24.

**Block 6, By the numbers.** A rule row: "1,788 papers · 239 cited in the PDF · 160 reports and posts · 56 subsections · 2011 to 2026" in mono 13, with an inline SVG year histogram to the right (bars 2016 to 2026 in `--fg`, mono 11 ticks, 320 × 56 px) from `stats.json.years`. Below it the key: failure sources as circle marks, operations as square marks, requirements as plain words. This is the colour legend for the whole site.

**Block 7, Footer colophon.** Generated dates, data file links, "Submit an item", "Cite", "GitHub", licence, "No analytics, no cookies, no trackers." Inter 13, rule above.

## 4. Papers page

Layout at 1440: a sticky left rail of 280 px, a main column of 880 px (the prose measure), and the remaining width as margin, into which the detail drawer slides.

**Rail ("Contents").** Eleven sections as disclosure rows: 3 px colour rule, number in mono, title in Newsreader 17, primary count in mono. An open section lists its subsections (number, title, count) in Inter 14; the current one shows a filled 8 px square in the section colour. Arrow keys move, Enter opens, Home/End jump. The rail scrolls independently.

**Filter bar (sticky under the masthead).** Search input ("Search titles, labels, authors, summaries"); toggles "Cited in PDF", "Score 3", "Chinese notes"; two year selects (2011 to 2026); a sort select (survey order, year, title); a density toggle (full, compact); a scope control (This subsection, This section, Whole corpus). Active filters repeat as removable chips with "Clear". With a subsection scope the bar adds "Also 41 matches in the whole corpus". Search is debounced at 150 ms; every token must prefix-match a token in title, label, author surnames, or one-line summary; matches are marked with a `--bg-panel` background and an underline, no colour.

**Section head.** "§5" in mono, the title in Newsreader 44/48, the operation chip, the purpose paragraph from `outline.json` in Newsreader 18/28 at 68ch.

**Subsection head.** "5.3" and the title in Newsreader 28/34; a count line in Inter 13: "57 papers · 6 cited in the PDF · 12 cross-referenced here · 1 report"; a disclosure "What this subsection covers" containing the plan bullets as a list in Newsreader 16/24; the link "N items in the stream". Subsection heads are `<h3>` inside `<section id="s5_3">`, so the hash scrolls natively if JavaScript is slow.

**Card (catalogue entry), fields in order.**

1. An 8 px square mark in the home-section colour (filled when the paper's primary is this subsection; hollow with a "from 2.4" prefix when the paper is shown here through a cross-reference).
2. Label: `label` in Newsreader 600, 20/26 (fits in one line at 27 characters).
3. Title: Inter 14/20 in `--fg`, clamped to two lines.
4. Byline: surnames of the first three authors, then "+N" when longer, a middle dot, and the year in mono ("Terekhov, Panfilov, Dzenhaliou +1 · 2025"). Inter 13.
5. One-line summary: `one_line` in Newsreader 16/24, clamped to three lines. Omitted when empty; the card simply shortens.
6. Marks row, Inter small caps 11 and mono: "CITED" with a filled mark when `selected`; score as a filled circle for 3 and a hollow circle for 2 with `aria-label="score 3, must cite"`; "中文" when `has_zh`; "also in 2.4, 5.5 +3" when `also` is non-empty; "arXiv 2510.09462" as an external link with the arrow icon.

The whole `<article>` opens the drawer; the arXiv link stops propagation. Full density is about 150 px per card; compact keeps fields 2, 4 and 6 at about 56 px. Cards are single column at 68ch.

**Order and cross-references.** Primary papers follow the file order from `SCHEMA.md` (cited, score, reading rank, year, title). Cross-referenced papers (`also`) follow under a run-in head "Also placed here (12)", collapsed by default; 3.2 Failure Sources and Threat Models has 40 of them and would otherwise double its length. Reports and posts follow under "Reports and posts (3)" with a sand-coloured mark, venue in place of the arXiv id, and `confidence` shown only when it is not "verified".

**Detail drawer.** 520 px wide at 1440, 440 at 1024, a full-screen sheet below; `role="dialog"`, `aria-modal`, focus trapped, Escape closes, focus returns to the card. Content, top to bottom: crumb ("§5 Observing Agent Behaviour › 5.3 Chain-of-Thought Monitoring"); label in Newsreader 32/38; title in Newsreader 20/26; full author list in Inter 14 with "Show all 265 authors" after twelve; meta line in mono: year, arXiv id, score, "cited in the PDF", "reading list #5" when `reading_rank` is set; text buttons "arXiv abstract", "PDF", "Copy key", "Copy link"; the one-line summary in Newsreader 18/28; "Why it is here" (`reason`) as a footnote in Inter 13; "Placed in" listing the home subsection and every `also` entry with its score circle, each a link; "In the stream" with the count of items whose `related_papers` include the key, lazy from `stream.json`, hidden when zero.

Then "Reading notes (中文)", loaded on demand from `summaries_zh.json` and cached. The head carries the depth badge from `reading_depth` (全文 / 部分 / 仅摘要 / 仅题录) and one line: "Structured reading notes; the depth marks how much of the paper was read." The container has `lang="zh-Hans"`. Fields in this order, Chinese field name as the head with the English name beside it in small caps: 定位 Positioning; 问题 Problem; 方法 Method; 发现 Findings as a numbered list (up to four; section references like "第 8.1 节" kept verbatim); 部署启示 Deployer takeaway in a panel tinted with the section colour, since it is the field a deploying team needs; 局限 Limitations; 与小节关系 Relation to this subsection; 存疑 Doubts in italic; 术语 Terms as a two-column glossary split on " = " (English left, Chinese right). Chinese text is set at 16/29 with the CJK fallback stack; Latin terms inside it stay in Newsreader.

**Empty, loading, error states.** A subsection with no matches after filtering shows "No papers match in 5.3" with "Clear filters" and "Search the whole corpus"; subsections with one paper (11.5) render normally. While `papers.json` loads, each subsection shows three skeleton rows in `--bg-panel` with no animation under reduced motion; the rail and all heads render immediately from `taxonomy.json`. A failed fetch renders "papers.json could not be loaded" with a retry button and logs nothing to the console.

**Handling 1,788 items.** `taxonomy.json` loads first and paints the rail, heads and counts. `papers.json` (about 1 MB raw, roughly 250 KB gzipped by GitHub Pages) loads once and is indexed into three Maps: by key, by primary subsection, by `also` subsection. Only the section in the hash is rendered; each subsection renders its first 24 cards and a sentinel; an `IntersectionObserver` with `rootMargin: 800px` renders the next 24. Switching sections removes the previous DOM. The search index is built after first paint in `requestIdleCallback` chunks of 200 papers. `summaries_zh.json` (roughly 350 KB) loads on the first request for notes. If time-to-interactive on a mid-range phone exceeds 2 s, `build_data.py` also emits `data/papers/<section>.json`, an extension recorded in `SCHEMA.md`.

## 5. Stream page

**Header.** "The live stream" in Newsreader 44/48. Dek in Newsreader 20/30: "News about deploying AI agents, good and bad, each item filed under the survey's failure sources, requirements, control operations, and subsections." Status line in mono 13 from `stream.json`: "N items · last updated 17 October 2026, 12:00 UTC · sources: seed sweep 2026-10-17, collector". Text buttons: "Submit an item", "How items are collected" (`about.html#stream`), "Download stream.json".

**Chronology strip.** An inline SVG, full width by 72 px, under the header. Months from the earliest item to the current month; each month a stacked column of bad (coral), mixed (gold), good (forest), one unit per item; month ticks in mono 11 every third month, years in small caps. Hover or focus shows "Jul 2025 · 3 bad · 1 good"; clicking sets `from` and `to` to that month and draws the active range as a `--bg-panel` band. The SVG has `role="img"` with an `aria-label` summary; the from/to inputs remain the accessible path. Drawn from the filtered set, the strip is also a histogram of the current query.

**Filter rail.** 260 px at 1024 and above, sticky; below that a "Filters (3)" button opens a bottom sheet. Fieldsets with small-caps legends, in order: Search; Polarity (good, bad, mixed; dash marks in polarity colours); Failure source (mistakes, manipulation, misalignment; circle marks in coral, amber, purple); Operation (constrain, observe, intervene, steer, train, verify, deploy; square marks in section colours); Requirement (correct, compliant, in scope, within budget, safe; no colour); Kind (the eight values); Domain (the fourteen values as a select); Evidence (the six values); Date range (two month inputs). Mark shapes differ by group because coral is shared by polarity bad, failure source mistakes, and §2. Each option carries a faceted count against the other active groups. OR within a group, AND across groups. "Clear all" at the bottom.

**Ledger (main column).** Items grouped by month under sticky heads (Newsreader 24/30 with a hairline). Row fields in order:

1. Date column, 88 px, mono 13, right-aligned: "17 Oct". For `date_precision: month` the day is omitted; for `year` only the year is shown, with a title attribute "date known to the month" or "to the year".
2. Polarity dash (3 × 18 px, polarity colour) and kind in small caps 11.
3. Title in Newsreader 22/28, linking to `url` with the external-link icon.
4. Summary in Newsreader 16/24 (the two factual sentences).
5. Source line, Inter 13: publisher · evidence · domain; with `actors`, "Replit (vendor), SaaStr (deployer)".
6. Classification line: failure-source chips (circle marks), operation chips (square marks), requirement chips (plain), then subsection chips with a 3 px left rule in section colour ("2.1 Compounding Mistakes", "4.1 Least Privilege", "6.5 Reversibility and Rollback") linking to `papers.html#sX_Y`.
7. Related papers: labels from `papers.json` ("Token Budget Attacks") linking to `papers.html#paper/<key>`; the bib key in mono until `papers.json` is loaded.
8. Verification: check icon and "verified 17 Oct 2026"; hover or focus reveals `verification_note`; `added_by` as "seed sweep", "collector" or "reader submission". Tags in mono last.

Collapsed rows show fields 1 to 4 and 6; "More" (or `#item/<id>`) expands 5, 7, 8 and a "Copy link" button. Enter on a row toggles expansion; the title link and chips are separate tab stops.

**Linking back.** Subsection chips go to the papers page, related-paper labels open the drawer there, and `#s4_1` or `#paper/<key>` here come back from those pages: one loop, entered from the landing spread.

**Last updated and pipeline transparency.** The header status line shows `generated` and `sources`. A panel at the foot of the ledger, "How this is collected", says in four sentences that the collector runs on a schedule (RSS and search), that candidates are classified into the taxonomy by a language model, that every item is fetched and verified before publication, and that unverifiable items are not published. It lists counts by `added_by` and links to the `pipeline/` directory and to `about.html#stream`.

**Submit path.** The button builds `${REPO_URL}/issues/new?template=submit_item.yml` and opens it in a new tab with `rel="noopener"`; `REPO_URL` is one constant in `common.js` since the repository name is not final. The template asks for URL, date, what happened, polarity, and suggested subsections; the collector reads labelled issues.

**Empty and loading states.** No matches: "Nothing in the ledger matches these filters" with "Clear all". Zero items in the file: "The ledger opens with the first verified sweep" and the submit button. Loading: three skeleton rows. Fetch failure: a message and a retry button.

## 6. About page

A single column at 68ch, body in Newsreader 18/30, heads in Newsreader 28/34, Title Case noun phrases. In order: **The Survey** (thesis paragraph, the three readers, status and PDF placeholder); **The Taxonomy** (requirements, failure sources, the two levers and seven operations, Verify, the two-level test, with Figures 1 and 2 at reduced size and the colour key table that serves as the legend for the whole site); **The Paper Collection** (5,421 retrieved candidates, 1,788 placed, scoring 3 must-cite and 2 relevant, `selected` meaning cited in the PDF, labels, cross-references, how reports and posts were verified); **Reading Notes in Chinese** (239 entries, the ten fields, four depth levels, that they are notes read against the paper and not translations); **The Live Stream** (what counts as an item, the eight kinds, polarity, verification policy, cadence, exclusions); **Submit an Item** (the issue template and acceptance rules); **Cite** (a BibTeX block with "[Authors]", 2026, "arXiv link to come", and a copy button); **Data** (each JSON file with size and generated date, a two-line description per file, and the note that the front end reads only these); **Colophon** (typefaces, no analytics or cookies, licence, static HTML). Each head has an id matching the hash list in section 2.

## 7. Visual system

**Type pairing.**

- Serif for display and reading: *Newsreader* (Google Fonts, variable, optical size 6 to 72, weights 200 to 800, italics), `font-optical-sizing: auto`. Fallback: `'Iowan Old Style', 'Palatino Linotype', Charter, Georgia, serif`.
- Sans for interface text: *Inter* at 400, 500, 600. Fallback: `system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif`.
- Mono for dates, ids, counts and keys: *IBM Plex Mono* 400. Fallback: `ui-monospace, 'SF Mono', Menlo, Consolas, monospace`.
- Chinese: no webfont. `[lang="zh-Hans"]` uses `Newsreader, 'Songti SC', 'Noto Serif CJK SC', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', serif` so Latin stays in Newsreader and Han glyphs come from the system.

One `<link>` to Google Fonts with `display=swap` and a `preconnect`. Local `@font-face` fallback declarations with `size-adjust` (Georgia 97%, Arial 93%) keep the layout from shifting when the web fonts arrive or never arrive.

**Sizes (px/line-height).** Display 72/76 (landing title, clamped), 44/48 (page titles, section heads), 32/38 (drawer label), 28/34 (subsection heads, about heads), 24/30 (contents rows, month heads), 22/28 (ledger titles), 20/26 (card labels), 18/30 (essay body), 18/28 (purpose paragraphs), 16/24 (summaries), 15/22 (italic captions). Inter 14/20 (card titles, inputs, rail subsections), 13/18 (meta), 11/16 uppercase small caps with 0.08em tracking (running heads, kinds, legends). Mono 13/18, 12/16, 11/16. Measures: 68ch prose, 60ch dek.

**Colour tokens** (`tokens.css`, custom properties, only the values from the brief): `--ink #2E2E2E`, `--gray #7D7D7D`, `--gray-mid #C7C7C7`, `--gray-light #EAEAEA`, `--panel #F7F7F7`, `--white #FFFFFF`, `--link #598DD2`; sections `--c-s2 #D95358`, `--c-s3 #7D7D7D`, `--c-s4 #E27553`, `--c-s5 #598DD2`, `--c-s6 #E09A3B`, `--c-s7 #65C2B9`, `--c-s8 #8D86E8`, `--c-s9 #62A16E`, `--c-s10 #A37CAD`, `--c-s1`/`--c-s11 #7D7D7D`; failure sources `--c-mistakes #D95358`, `--c-manipulation #E09A3B`, `--c-misalignment #A37CAD`; polarity `--c-good #62A16E`, `--c-bad #D95358`, `--c-mixed #D1B745`; accents `--c-sand #C7A678` (mark for reports and posts), `--c-slate #75A4B5` (verified check), `--c-sky`, `--c-pink` reserved and unused.

Light theme roles: `--bg: --white`, `--bg-panel: --panel`, `--fg: --ink`, `--fg-muted: --ink`, `--rule: --gray-light`, `--rule-strong: --gray-mid`. The muted text role is ink, not gray: `#7D7D7D` on white measures about 4.1:1, below AA for small text. Gray is used for rules, icons, and text at 19 px bold or 24 px regular and above, never for 13 px metadata.

Dark theme (`[data-theme="dark"]`, defaulting from `prefers-color-scheme`, stored in `localStorage`): `--bg: --ink`, `--fg: --gray-light` (11.3:1), `--fg-muted: --gray-mid` (8.0:1), `--rule: --gray` (as a rule only; 3.3:1 is too low for text), `--rule-strong: --gray-mid`. The one derived value is `--bg-panel: color-mix(in srgb, var(--ink) 80%, black)`; a strict token-only reading sets `--bg-panel: --ink` and relies on the gray rule.

Section, failure-source and polarity colours are never small text. They appear as 3 px rules, 8 px squares, 3 px dashes, circle marks, 1 px chip borders, and chip tints `color-mix(in srgb, <colour> 14%, var(--bg))` in light and 28% in dark, with chip text in `--fg`, so contrast does not depend on the hue. Links are `--fg` with a 1 px underline in `--link` at 3 px offset; hover thickens to 2 px; external links carry the arrow icon. Focus is a 2 px solid `--link` outline, 2 px offset, both themes.

**Spacing.** A 4 px base: 4, 8, 12, 16, 24, 32, 48, 64, 96, 128 as `--s1` to `--s10`. Gutters 24. Outer margins 48 (1440), 32 (1024), 24 (768), 16 (390). Landing blocks 96 apart; card inner padding 16/12; chip padding 2/8.

**Radii, borders, shadows.** Radius 0 on cards, panels, drawer, images; 2 px on chips and buttons; 3 px on inputs. Hairlines are 1 px `--rule`; emphasis rules 1 px `--rule-strong`; colour rules 3 px; the landing masthead double rule as described. No shadows on static elements. Drawer and dialog: `0 0 0 1px var(--rule-strong), 0 24px 48px -12px rgb(46 46 46 / 0.24)` (ink as rgb), black in dark.

**Iconography.** One inline `<svg>` sprite per page with `<symbol>` elements, 20 × 20 viewBox, `stroke: currentColor`, 1.5 px, round caps and joins. Set of fifteen: arrow-right, arrow-up-right (external), search, sliders (filters), chevron-down, x (close), sun, moon, copy, check (verified), link (cross-reference), file (PDF), list (contents), clock (chronology), and the GitHub mark as a service link. Marks (square, dash, circle) are CSS, not icons.

**Motion.** Durations 120 ms (hover), 200 ms (chip toggle, disclosure), 260 ms (drawer slide, dialog fade), easing `cubic-bezier(.2,.7,.2,1)`. Only opacity and transform animate; disclosures use `grid-template-rows: 0fr` to `1fr`. Under `prefers-reduced-motion: reduce` all durations are 0 ms and the drawer appears in place. No parallax, no scroll-triggered effects, nothing auto-plays; the "live" in live stream is conveyed by the dates and the updated line, not by movement.

## 8. Components inventory

| Component | Class | Notes |
|---|---|---|
| Masthead | `.masthead`, `.masthead__title`, `.masthead__nav`, `.masthead--double` | sticky; double rule on landing only |
| Theme toggle | `.theme-toggle` | button, `aria-pressed` |
| Running head | `.running-head` | Inter small caps 11 |
| Title block | `.title-block`, `.title-block__title`, `.dek`, `.byline`, `.status` | landing only |
| Text button | `.btn`, `.btn--arrow`, `.btn--primary`, `.btn--ghost` | 2 px radius |
| Spread | `.spread`, `.spread__left`, `.spread__right`, `.spread__rule` | 7/5 columns, vertical hairline |
| Contents | `.toc`, `.toc__row`, `.toc__rule`, `.toc__num`, `.toc__title`, `.toc__count`, `.toc__subs` | landing and papers rail |
| Rail | `.rail`, `.rail__section`, `.rail__sub`, `.is-current` | papers page, disclosure rows |
| Ledger | `.ledger`, `.ledger__month`, `.ledger__row`, `.ledger__date`, `.ledger__dash`, `.ledger__kind`, `.ledger__title`, `.ledger__summary`, `.ledger__source`, `.ledger__class`, `.ledger__related`, `.ledger__verified`, `.is-expanded` | landing (short) and stream (full) |
| Plate | `.plate`, `.plate__img`, `.plate__caption` | figures with `<dialog>` |
| Stat line | `.statline`, `.statline__item`, `.statline__chart` | inline SVG histogram |
| Key | `.key`, `.key__item` | colour legend |
| Chip | `.chip`, `.chip--section`, `.chip--source`, `.chip--op`, `.chip--req`, `.chip--sub`, `.chip--removable` | tint by `--c` custom property set inline |
| Mark | `.mark`, `.mark--square`, `.mark--square-hollow`, `.mark--dash`, `.mark--circle`, `.mark--circle-hollow` | CSS shapes |
| Filter bar | `.filterbar`, `.filterbar__search`, `.filterbar__toggle`, `.filterbar__scope`, `.filterbar__active` | papers page, sticky |
| Facet rail | `.facets`, `.facet`, `.facet__legend`, `.facet__option`, `.facet__count` | stream page |
| Chronology | `.chronology`, `.chronology__col`, `.chronology__band` | SVG |
| Section head | `.section-head`, `.section-head__num`, `.section-head__purpose` | |
| Subsection head | `.sub-head`, `.sub-head__counts`, `.sub-head__covers`, `.sub-head__stream` | |
| Card | `.card`, `.card--paper`, `.card--grey`, `.card--cross`, `.card--compact`, `.card__label`, `.card__title`, `.card__byline`, `.card__line`, `.card__marks` | `<article>` acting as button |
| Run-in head | `.runin` | "Also placed here (12)" |
| Drawer | `.drawer`, `.drawer__crumb`, `.drawer__label`, `.drawer__meta`, `.drawer__actions`, `.drawer__placed`, `.drawer__notes` | dialog, focus trap |
| Reading notes | `.notes`, `.notes__depth`, `.notes__field`, `.notes__takeaway`, `.notes__terms` | `lang="zh-Hans"` |
| Skeleton | `.skeleton`, `.skeleton__row` | no animation under reduced motion |
| Empty state | `.empty`, `.empty__actions` | |
| Dialog | `.dialog`, `.dialog__close` | native `<dialog>` |
| Footer | `.colophon`, `.colophon__row` | |
| Utilities | `.caps`, `.mono`, `.serif`, `.measure`, `.visually-hidden` | |

Scripts: `common.js` (theme, fetch helper with relative base, hash router, formatters for dates, author truncation, number grouping, `REPO_URL`), `taxonomy.js` (load and index `taxonomy.json`, colour lookup, chip and mark factories), `papers.js`, `stream.js`, `search.js` (tokenizer and prefix index, shared by both pages).

## 9. Responsive behaviour

**390 px.** Single column, 16 px margins. The masthead shortens the running head to "Controlling Untrusted AI" and puts the three links behind a menu button. Landing title 40/44, dek 18/26; the spread stacks: contents first (title and count per row, subsection lists behind a chevron), then eight ledger rows. Plates stack. Papers page: the rail becomes a horizontal strip of section chips plus a "Contents" button opening a bottom sheet; the filter bar collapses to search and "Filters (2)"; cards are full width with the summary clamped to two lines; the drawer is a full-screen sheet with a sticky close bar. Stream page: a month jump select replaces the chronology strip; the facet rail is a bottom sheet; the date moves above the title and the chips wrap.

**768 px.** 24 px margins. Landing spread still stacked but with the ledger at twelve rows and the contents showing subsection lists inline. Plates two-up. Papers: rail still a strip; cards keep the 68ch measure; drawer a full-screen sheet. Stream: the chronology strip returns at 56 px height; facets remain a sheet; the date column returns at 72 px.

**1024 px.** 32 px margins. Landing spread side by side at 7/5. Papers: the rail appears at 240 px, drawer at 440 px overlaying the right edge. Stream: facet rail at 240 px, ledger beside it, chronology at 72 px.

**1440 px.** 48 px margins, content capped at 1,280. Rail 280, main 880, drawer 520. The right margin on the papers page holds the drawer without covering the cards being read.

## 10. Feasibility, performance, risks

**Vanilla implementation.** Plain HTML, CSS custom properties, ES modules. The router is forty lines on `hashchange`. The drawer and plate viewer are native `<dialog>` elements, which supply focus trapping and Escape. Disclosures are `<details>`/`<summary>` where no animation is needed and a class toggle where it is. The search index is a Map from token to a Uint16Array of paper indices; no library, so no CDN dependency. `color-mix()` is supported in current Chrome, Safari and Firefox; a flat `--bg-panel` chip background precedes it as fallback.

**Performance plan.** First paint depends only on the HTML, `tokens.css` and `site.css` (under 30 KB combined) and system fallback fonts; web fonts swap in. The landing fetches `stats.json`, `taxonomy.json` and `stream.json`; the ledger needs twelve items, so if the stream passes a few hundred items `build_data.py` can also write `stream_recent.json` (a contract extension). The papers page paints structure from `taxonomy.json` and fills cards when `papers.json` arrives, capped at 24 per subsection until scrolled. `summaries_zh.json` loads on first use. No analytics, no third-party JavaScript. For the headless Chrome check every fetch is wrapped, every image path exists, a `favicon.svg` is linked, and failures render messages instead of throwing.

**Risks and mitigations.** Google Fonts blocked or slow: the `size-adjust` fallbacks keep the layout stable and the design still reads as editorial on Georgia. Coloured marks in the dark theme: marks are decorative and the adjacent text carries the meaning. The 1 MB corpus on slow mobile: the per-section split in section 4. No serif CJK face installed: the stack ends in PingFang or YaHei. `file://` and `http.server`: hash routing and relative fetches need no server features. Repository URL unknown: one constant. Stream empty at launch: honest empty states on both pages.

**What to cut first, in order.** 1. The chronology strip (month heads and date inputs remain). 2. Faceted counts on the stream filters. 3. The landing year histogram. 4. The compact density toggle. 5. Whole-corpus search (keep per-section). 6. The plate `<dialog>` (link to the image file). 7. The derived dark panel colour (flat ink). None of these touches the three signature moments.
