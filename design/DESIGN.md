# DESIGN.md: the companion site of *Controlling Untrusted AI: A Survey*

Specification for the front-end, written 2026-10-17 from `BRIEF.md`, `SCHEMA.md`, the three concepts and the two judge reports. The judges split (deployer: B 59, A 58, C 53; editor: A 58, B 55, C 53); on the aggregate A leads 116 to 114 to 106 and both graft lists converge, so this spec is built on Concept A's skeleton and surface, takes B's structure where it serves a deployer (the mechanism map as the one interactive plate, live rail counts, widening search, recently-verified sort, stale note, report-a-problem) and takes C's measured colour rule, URL scheme and staleness ladder. Every number below was checked against `site/data/` on 2026-10-17 (1,788 papers, 174 reports and posts, 240 cited, 239 Chinese notes of which 50 belong to reports, 149 empty one-liners; stream empty, seed of 285 candidates with summaries median 503 characters). Where this document is silent, Concept A governs.

## 1. Design Intent

The site is set like a journal, not a dashboard. The survey's table of contents is the primary navigation and every line of it opens into the papers placed under it, so the structure of the paper and the structure of the corpus are one object; beside the contents runs a dated ledger of what has happened to deployed agents in the world, filed under the same subsection ids. Type carries the hierarchy (Newsreader for the paper's words, Inter for the interface, IBM Plex Mono for dates, ids and counts; hairline rules; small-caps running heads; radius 0). Colour is reserved for section identity, failure source and polarity, and because coral is shared by Section 2, "benign" and "bad", shape disambiguates: square for section or operation, circle for failure source, dash for polarity. The one picture above the fold is the paper's own Figure 2 redrawn live from the data, which gives the page its colour and gives a deployer the operation-level entry A lacked.

The three signature moments:

1. **The Spread.** Below the title, two columns under running heads of equal weight. Left, THE PAPER COLLECTION: an eleven-line table of contents with a 3 px rule per section and the count in the margin, an 11-segment section-colour bar under the head. Right, THE LIVE STREAM: the twelve most recent ledger entries, a polarity dash each, a 3-segment polarity bar under the head. A vertical hairline divides them. A visitor sees both parts, their size and their colour language in five seconds.
2. **The Mechanism Map.** Figure 2 as a CSS grid of plain links: a thin coral row for How Agents Fail, two lever rows (Constrain, Observe, Intervene; Train, Steer), Verify tall at the right, Deploy and Assure as the base bar, each node tinted in its section colour with its paper count and stream count. One click lands on that section of the papers page; the item count lands on the stream filtered to that operation.
3. **The Ledger Row That Points Back.** A collapsed stream row already shows date, polarity, kind, title, two lines of summary and its classification line. Clicking "4.1 Confinement" lands on that subsection of the papers page, whose head reads "3 items in the stream" pointing back. The taxonomy binds the two halves.

## 2. Information Architecture

### 2.1 Pages

| File | Purpose | `<title>` pattern |
|---|---|---|
| `index.html` | Title, the Spread, the Mechanism Map, Figure 1, readers, numbers, colophon | `Controlling Untrusted AI: A Survey` |
| `papers.html` | The paper collection by section and subsection, search, filters, detail drawer | `5.3 Human Oversight · Papers · Controlling Untrusted AI` |
| `stream.html` | The live stream: chronology strip, facets, ledger, pipeline panel | `Stream · Controlling Untrusted AI` (plus ` · 42 of 285` while filtered) |
| `about.html` | The survey, taxonomy, corpus, notes, stream method, submit, cite, data, limitations, colophon | `About · Controlling Untrusted AI` |
| `404.html` | Masthead, "Not in the Contents", four links, a search box forwarding to `papers.html?q=` | `Not found · Controlling Untrusted AI` |

### 2.2 Global navigation

The masthead is 56 px, sticky, `<header>` with `<nav aria-label="Site">`. Left: the running head "Controlling Untrusted AI: A Survey" in Inter small caps 11/16, tracking 0.08em, linking to `index.html`; at 390 it shortens to "Controlling Untrusted AI". Right, in order: "Papers", "Stream", "About" (Inter 14/20; the current page carries a 2 px `--fg` underline at 6 px offset and `aria-current="page"`), a 16 px vertical hairline, the theme toggle (sun or moon icon, `aria-label` "Switch to dark theme" or "Switch to light theme"), and "GitHub" as text linking to `REPO_URL`. The "Stream" link carries a 6 px forest circle (`.nav__dot`) when `stats.stream_updated` is within seven days, with visually hidden text "updated this week". A skip link "Skip to content" is the first focusable element on every page. Below the masthead a 1 px `--rule`; on `index.html` only, a double hairline (1 px, 3 px gap, 1 px). At 390 and 768 the three links sit behind a "Menu" button opening a full-width sheet; the theme toggle stays visible.

### 2.3 Footer

Identical `<footer class="colophon">` on all five pages, a 1 px `--rule` above, Inter 13/18, two rows. Row 1 in mono: "Data generated {stats.generated} · Stream updated {stats.stream_updated or 'not yet'}". Row 2: "Submit an item" (`ISSUE_URL`), "Cite" (`about.html#cite`), "Data" (`about.html#data`), "GitHub" (`REPO_URL`), the text "No analytics, no cookies, no trackers. Typefaces served by Google Fonts." and "CC BY 4.0 for text and data" linking to `LICENSE`.

### 2.4 URL scheme

Filters live in the query string, so they survive reload and paste; position and entity live in the hash, so changing them does not reload and Back closes a drawer. `common.js` exports `readState()` (query and hash merged), `writeState(patch, {push})` and `linkTo(page, state)`; no page builds a URL by hand. Query keys are alphabetical, defaults omitted, multi-values comma lists. Filter changes call `replaceState` (immediately for chips and selects, debounced 250 ms for text); opening a drawer or expanding a row calls `pushState` with `history.state = {drawer: true}`. Closing calls `history.back()` when that flag is set, otherwise `replaceState` to the entity's home hash. `document.title` follows every state change.

| Target | URL |
|---|---|
| Section, subsection | `papers.html#s5`, `papers.html#s5_3` |
| Paper, report | `papers.html#paper/terekhov2025adaptive`, `papers.html#grey/greenblatt2025controlmeasures` |
| Papers filters | `papers.html?cited=1&density=compact&grey=0&q=monitor&scope=all&score=3&sort=year&years=2025,2026,le2022&zh=1#s5_3` |
| Stream filters | `stream.html?domain=coding&evidence=first-party&from=2025-01&kind=incident&op=observe&paper=khan2026token&polarity=bad&q=replit&req=in-scope&sort=verified&source=external&sub=s4_1&to=2026-10` |
| Stream item, month | `stream.html#item/2025-07-18-replit-agent-deleted-production-database`, `stream.html#2025-07` |
| Landing anchors | `index.html#collection`, `#stream`, `#map`, `#gap`, `#readers`, `#numbers` |
| About anchors | `about.html#survey`, `#taxonomy`, `#corpus`, `#notes`, `#stream`, `#submit`, `#cite`, `#data`, `#limitations`, `#colophon` |

Cross-links are symmetric and produced by `linkTo`: a subsection id anywhere links to `papers.html#sX_Y`; a subsection head links to `stream.html?sub=sX_Y`; a related paper to `papers.html#paper/<key>`; a drawer's "In the stream" to `stream.html?paper=<key>`; an operation node or chip to `stream.html?op=<id>`; a failure-source mark to `stream.html?source=<id>`. `?theme=light|dark` overrides the stored theme for screenshots and is ignored by `readState()`.

## 3. Design Tokens

`tokens.css` holds every custom property. Component CSS reads semantic roles and `--c`; it never names a hue. `--c` is set by attribute selectors (`[data-section="s5"] { --c: var(--c-s5) }`, `[data-source="benign"]`, `[data-polarity="bad"]`, `[data-op="observe"]`) so a chip, mark, rule or tint is one rule each.

```css
:root {
  /* palette, from BRIEF.md, used only through roles and --c */
  --ink:#2E2E2E; --gray:#7D7D7D; --gray-mid:#C7C7C7; --gray-light:#EAEAEA; --panel:#F7F7F7; --white:#FFFFFF; --link:#598DD2;
  --coral:#D95358; --terracotta:#E27553; --blue:#598DD2; --amber:#E09A3B; --teal:#65C2B9; --periwinkle:#8D86E8;
  --forest:#62A16E; --purple:#A37CAD; --gold:#D1B745; --sky:#6FCBEF; --pink:#E072AF; --sand:#C7A678; --slate:#75A4B5;
  /* sections */
  --c-s1:var(--gray); --c-s2:var(--coral); --c-s3:var(--gray); --c-s4:var(--terracotta); --c-s5:var(--blue); --c-s6:var(--amber);
  --c-s7:var(--teal); --c-s8:var(--periwinkle); --c-s9:var(--forest); --c-s10:var(--purple); --c-s11:var(--gray);
  /* operations */
  --c-failures:var(--coral); --c-constrain:var(--terracotta); --c-observe:var(--blue); --c-intervene:var(--amber);
  --c-steer:var(--teal); --c-train:var(--periwinkle); --c-verify:var(--forest); --c-deploy:var(--purple);
  /* failure sources, polarity, item classes */
  --c-benign:var(--coral); --c-external:var(--amber); --c-insider:var(--purple);
  --c-good:var(--forest); --c-bad:var(--coral); --c-mixed:var(--gold);
  --c-report:var(--sand); --c-verified:var(--slate);
  /* roles, light */
  --bg:var(--white); --bg-panel:var(--panel); --fg:var(--ink);
  --fg-muted:color-mix(in srgb, var(--gray) 75%, var(--ink));          /* #696969, 5.49:1 on white, 5.12:1 on panel */
  --rule:var(--gray-light); --rule-strong:var(--gray-mid);
  --link-underline:var(--link); --focus:var(--link); --mark-bg:var(--panel);
  --tint:14%; --c-text-mix:60%;                                           /* derived colour: see rules below */
  --mark-outline:color-mix(in srgb, var(--c) 70%, var(--ink));          /* 1 px on small marks, light only */
  --c-tint:color-mix(in srgb, var(--c) var(--tint), var(--bg));
  --c-border:color-mix(in srgb, var(--c) 70%, var(--ink));
  --c-text:color-mix(in srgb, var(--c) var(--c-text-mix), var(--ink));
  --scrim:rgb(46 46 46 / 0.4); --shadow-float:0 0 0 1px var(--rule-strong), 0 24px 48px -12px rgb(46 46 46 / 0.24);
  /* type */
  --serif:"Newsreader","Iowan Old Style","Palatino Linotype",Charter,Georgia,serif;
  --sans:"Inter",system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  --mono:"IBM Plex Mono",ui-monospace,"SF Mono",Menlo,Consolas,monospace;
  --cjk:"Newsreader","Songti SC","Noto Serif CJK SC","PingFang SC","Hiragino Sans GB","Microsoft YaHei",serif;
  --fs-display:clamp(40px,6vw,72px); --lh-display:1.05;   /* landing title */
  --fs-page:44px; --lh-page:48px;                           /* page titles, section heads */
  --fs-drawer:32px; --lh-drawer:38px;                       /* drawer label */
  --fs-h2:28px; --lh-h2:34px;                               /* subsection and about heads */
  --fs-h3:24px; --lh-h3:30px;                               /* contents rows, month heads */
  --fs-dek:22px; --lh-dek:32px;
  --fs-row-title:20px; --lh-row-title:26px;                 /* ledger titles, map nodes */
  --fs-label:18px; --lh-label:24px;                         /* card labels; purpose text 18/28 */
  --fs-body:16px; --lh-body:24px;                           /* summaries; About essay 18/30 */
  --fs-ui:15px; --lh-ui:21px;                               /* card titles */
  --fs-ui-s:14px; --lh-ui-s:20px;                           /* nav, inputs, rail */
  --fs-meta:13px; --lh-meta:18px;                           /* meta, chips, counts */
  --fs-caps:11px; --lh-caps:16px; --ls-caps:0.08em;         /* small caps */
  --fs-mono-s:12px; --fs-mono-xs:11px;
  /* spacing, 4 px base */
  --s1:4px; --s2:8px; --s3:12px; --s4:16px; --s5:24px; --s6:32px; --s7:48px; --s8:64px; --s9:96px; --s10:128px;
  --gutter:24px; --margin:48px; --content-max:1280px; --measure:68ch; --measure-dek:60ch;
  /* shape */
  --r0:0; --r-chip:2px; --r-input:3px; --hairline:1px solid var(--rule); --hairline-strong:1px solid var(--rule-strong); --colour-rule:3px;
  /* layers */
  --z-rail:10; --z-sticky:20; --z-masthead:30; --z-sheet:40; --z-drawer:50; --z-toast:60;
  /* motion */
  --t-hover:120ms; --t-toggle:200ms; --t-drawer:260ms; --ease:cubic-bezier(.2,.7,.2,1);
  /* breakpoints: 390, 768, 1024, 1440 */
}
[data-theme="dark"] {
  --bg:var(--ink); --bg-panel:color-mix(in srgb, var(--ink) 90%, white);   /* #434343 */
  --fg:var(--gray-light); --fg-muted:var(--gray-mid);                         /* 11.29:1 and 8.03:1 on ink */
  --rule:color-mix(in srgb, var(--gray) 50%, var(--ink)); --rule-strong:var(--gray);
  --link-underline:color-mix(in srgb, var(--link) 75%, white); --focus:color-mix(in srgb, var(--link) 75%, white);  /* #82AADD, 5.65:1 */
  --mark-bg:color-mix(in srgb, var(--ink) 90%, white);
  --tint:18%; --mark-outline:transparent;
  --c-border:var(--c);
  --c-text:color-mix(in srgb, var(--c) 65%, white);
  --scrim:rgb(0 0 0 / 0.5); --shadow-float:0 0 0 1px var(--rule-strong), 0 24px 48px -12px rgb(0 0 0 / 0.6);
}
[data-section="s6"],[data-op="intervene"],[data-source="external"],[data-section="s7"],[data-op="steer"],[data-polarity="mixed"],[data-c="report"] { --c-text-mix:50%; }
@media (prefers-reduced-motion: reduce) { :root { --t-hover:0ms; --t-toggle:0ms; --t-drawer:0ms; } }
```

Rules that follow from the measured ratios (section 9 lists them):

- **Text is `--fg` or `--fg-muted`, never a hue**, at every size, with one exception: the live indicator label uses `--c-text` and sits on `--bg` only (on `--bg-panel` gold and sky at 50 % fall to 4.47 and 4.26). Links are `--fg` with a 1 px underline in `--link-underline` at 3 px offset, 2 px on hover; external links carry the arrow-up-right icon.
- **Hues appear as marks, rules, bars, tints and chip borders.** Small marks (8 px squares and circles, 3 × 14 px dashes, 6 px dots) carry a 1 px `--mark-outline` in the light theme, which lifts amber, teal, gold, sand and slate to 3.05 or better on white; in the dark theme every raw token is 3.45 or better on ink and the outline is transparent.
- **Tints are `--c-tint`** (14 % light, 18 % dark) with `--fg` on top. If the landing reads plain in review, raise `--tint` to 18 % in light before adding any element.
- **Gray `#7D7D7D` is for rules and for text at 24 px and above** (4.12:1 on white); `--fg-muted` is the 75 % mix.
- The theme is `data-theme` on `<html>`, set by an inline script before the stylesheets from `?theme`, then `localStorage` key `cuai-theme`, then `prefers-color-scheme`. The toggle never animates colours.

Type loading: one `<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>` and one stylesheet `https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400..700;1,6..72,400..500&family=Inter:wght@400;500;600&family=IBM+Plex+Mono&display=swap`; `font-optical-sizing: auto` on the serif. Local `@font-face` fallbacks `"Newsreader Fallback"` (`local("Georgia"); size-adjust: 97%`) and `"Inter Fallback"` (`local("Arial"); size-adjust: 93%`) precede the system stacks so layout does not shift when web fonts arrive or fail. `[lang="zh-Hans"]` uses `--cjk` at 16/29. Numerals use `font-variant-numeric: tabular-nums lining-nums`. Grid: 12 columns, `--content-max`, gutters 24, outer margins 48 at 1440, 32 at 1024, 24 at 768, 16 at 390. Icons are one inline `<svg hidden>` sprite per page, 20 × 20, `stroke: currentColor` 1.5 px, round caps: arrow-right, arrow-up-right, search, sliders, chevron-down, x, sun, moon, copy, check, link, file, list, clock, download, flag, menu. No icon fonts, raster icons or logos.

## 4. Landing Page

Twelve columns at `--content-max`; blocks separated by `--s9` (`--s7` below 768). Fetch order: `stats.json` (`cache: "no-cache"`) and `taxonomy.json` (`?v=<stats.generated>`) in parallel before the Spread's counts and the map render; `stream.json` only when `stats.stream_items > 0`, after first paint in `requestIdleCallback`, with the ledger column reserved at 12 × 72 px so nothing shifts. `papers.json` is never loaded here. Every numeral in static HTML is written from today's `stats.json` and carries `data-bind="stats.papers"` and the like; `common.js` re-binds on load. Numbers use `Intl.NumberFormat("en-GB")`.

**Block 1, Masthead** as in 2.2 with the double hairline.

**Block 2, Title Block** (about 320 px at 1440). `<h1>` in Newsreader 400 at `--fs-display`, line-height 1.05, tracking -0.01em, 8 columns, forced break after the colon: "Controlling Untrusted AI:" / "A Survey". Dek in Newsreader 22/32 at `--measure-dek`: the first two sentences of `taxonomy.thesis`, bound. Then "[Authors]" in Inter small caps 11 and the status line in Inter 13 `--fg-muted`: "Draft v0.2 · October 2026 · arXiv link to come" (`PAPER_STATUS` in `common.js`). Three text buttons with arrow icons, Inter 14 medium, 2 px radius, 1 px `--rule-strong` border, padding 8 px 14 px: "Read the Paper" (`aria-disabled="true"`, `title="arXiv link to come"`), "Browse the Papers", "Open the Stream". No hero image.

**Block 3, The Spread** (`id="collection"` left, `id="stream"` right). Seven columns, a 1 px vertical `--rule` in the gutter, five columns. Each column opens with a running head in small caps 11, a 6 px signature bar beneath it, and a mono 13 count line.

Left: running head "The Paper Collection"; the bar is 11 segments in `--c-s1` to `--c-s11`, widths proportional to `stats.per_section`, 1 px `--bg` gaps, `role="img"` `aria-label="Papers per section"`; the count line "1,788 papers · 174 reports and posts · 35 subsections" from `stats.papers`, `stats.grey`, `stats.subsections`. Then the contents: eleven `.toc__row`s, each a 3 px vertical rule in the section colour, the number in mono 13 ("§4"), the title in Newsreader 24/30 linking to `papers.html#s4`, the primary count right-aligned in mono 13 (sum of `counts.primary`), and under the title the subsection titles in Inter 13 `--fg-muted` separated by " · ", each a link ("4.1 Confinement · 4.2 Formal Enforcement · …"). Rows have 12 px vertical padding and a hairline between; hover sets `--bg-panel`. The column renders from `taxonomy.json` alone.

Right: running head "The Live Stream"; the bar is 3 segments good, bad, mixed in `--c-good`, `--c-bad`, `--c-mixed` proportional to the counts in `stream.json`, one `--rule` segment until the stream loads or when it is empty; the count line "285 items · updated 17 Oct 2026" from `stream.generated` (UTC timestamp in `title`), or "No items yet". Then the short ledger: the twelve most recent items under month heads (Newsreader 17 italic, "October 2026"), each a `.ledger__row--short`: date "17 Oct" in mono 12 (72 px column, right-aligned), a 3 × 14 px polarity dash, the kind in small caps 11, the title in Newsreader 17/22 clamped to two lines linking to `stream.html#item/<id>`, the publisher in Inter 13 `--fg-muted`, a 6 px forest "New" dot before the title when `verified_on` is within seven days. Footer link in Inter 13: "All 285 items". When `stats.stream_items` is 0 the column shows, in Newsreader 17 italic, "The ledger opens with the first verified sweep." and the text button "Submit an item" (`ISSUE_URL`, new tab, `rel="noopener"`); no placeholder rows.

At 1440 × 900 the Spread begins near y = 380 px. Below 1024 the columns stack, contents first (subsection lists behind a chevron at 390), then eight ledger rows at 390 and twelve at 768.

**Block 4, The Mechanism Map** (`id="map"`, full width, about 420 px). `<h2>` "The Mechanism Map" in Newsreader 28/34. Kicker in Newsreader 18/28 at `--measure`: "Two levers act on an untrusted agent. The first changes the deployment around it, the second changes the model. Verify tests either lever, and deployment and assurance compose the mechanisms into a stack." Then the plate, a CSS grid of 6 columns and 4 rows with 8 px gaps, rendered by `taxonomy.renderMechanismMap(el, stats, streamCounts)`:

- Row 0, columns 1 to 5: a 40 px bar `data-section="s2"`, tinted, 1 px `--c-border`, with "How Agents Fail" in Newsreader 20 and "§2" in mono, then three circle marks labelled "Benign", "External", "Insider" in Inter 13 with stream counts in mono ("· 41 items") once loaded; the bar links to `papers.html#s2`, each label to `stream.html?source=<id>`.
- Row 1, column 0: lever label in Inter small caps 11 `--fg-muted`, two lines: "Lever 1" / "Change the Deployment". Columns 1 to 3: nodes Constrain (`s4`), Observe (`s5`), Intervene (`s6`). Columns 4 to 5, rows 1 to 2: Verify (`s9`), tall.
- Row 2, column 0: "Lever 2" / "Change the Model". Train (`s8`) spans columns 1 to 2 and Steer (`s7`) takes column 3, the figure's own proportion.
- Row 3, columns 1 to 5: a 40 px base bar Deploy and Assure (`s10`), the row 0 anatomy without marks. Beneath the grid, one line in Newsreader 15 italic `--fg-muted`: "Two-level test. L1, does it still work if the agent is indifferent to the requirement. L2, does it still work if the agent tries to defeat it and knows how it works."

Node anatomy (`.mech__node`, min height 112 px, padding 12, radius 0, `--c-tint` fill, 1 px `--c-border`): "§5" in mono 12 top left and a 20 px glyph top right (lock, eye, hand, dial, compass, shield-check, layers for Constrain, Observe, Intervene, Train, Steer, Verify, Deploy and Assure); the label in Newsreader 20/26 as the primary link `papers.html#s5` with a `::after` covering the node; the figure's keywords in Inter 13 `--fg-muted`, two-line clamp, from this fixed table: Constrain "permissions, sandboxes, action interfaces, information-flow limits"; Observe "classifiers, action and reasoning monitors, probes, logs, human review"; Intervene "approve, clarify, block, edit, defer, resample, stop, recover"; Train "safety fine-tuning, preference learning, adversarial curricula, circuit breakers, unlearning, retention"; Steer "instruction hierarchies, context and memory selection, self-critique, activation steering"; Verify "control evaluations, red teams, white-box audits, statistics, safety cases"; Deploy and Assure "reference architectures, release gates, safety cases, policy, independent assurance". Bottom line in mono 12: "226 papers" (from `stats.per_section`) and, when loaded, "· 41 items" as a second link to `stream.html?op=observe` raised above the covering pseudo-element with `z-index: 1`. Hover and focus-visible: 2 px inset border in `--c`. No roving tabindex, no `aria-pressed`, no readout: the map is a `<nav aria-label="Mechanism map">`. At 768 the grid becomes 3 columns with Verify a full-width row under the levers; at 390 a single column of 64 px nodes, keywords hidden, lever labels as small-caps headers.

**Block 5, The Control Gap** (`id="gap"`, 8 columns centred). `<h2>` "The Control Gap" in Newsreader 28/34. `<figure class="plate">` with the re-encoded `fig1_why_control.jpg`, explicit `width` and `height`, `loading="lazy"`, a 1 px `--rule` border in dark theme only; clicking opens it in a native `<dialog class="dialog">` at up to 90 vw with a close button. Caption in Newsreader italic 15/22: "Figure 1. What an AI system can do has grown while what a human can check has not. Four operations close the gap against three failure sources."

**Block 6, Who This Is For** (`id="readers"`). `<h2>` "Who This Is For". Three columns (stack at 768) with small-caps heads "Researchers", "Deploying Teams", "Evaluators and Policy Staff" and paragraphs bound to `taxonomy.readers[0]`, `[1]`, `[2]` in Newsreader 16/24.

**Block 7, By the Numbers** (`id="numbers"`). Hairlines above and below. Left, mono 13 in one wrapping line: "1,788 papers · 240 cited in the PDF · 174 reports and posts · 35 subsections · 2011 to 2026" from `stats.papers`, `stats.cited`, `stats.grey`, `stats.subsections` and the first and last keys of `stats.years`. Right, an inline SVG year histogram 320 × 56 px, bars in `--fg` per year from 2016 (earlier years folded into "≤2016"), mono 11 ticks at 2016, 2020, 2024, 2026, `role="img" aria-label="Papers per year"`. Beneath, the key in Inter 13 under a small-caps head "Reading the Marks": "● failure source (benign, external, insider)   ■ section or operation   ▍ polarity (good, bad, mixed)", each glyph the real CSS mark in its colour; this is the colour legend for the site.

**Block 8, Colophon** as in 2.3.

Motion on the landing: hover transitions at `--t-hover`; nothing animates on load or scroll; the plate dialog fades 260 ms (0 under reduced motion).

## 5. Papers Page

### 5.1 Layout

At 1440: a sticky left rail of 264 px (`top: 56px; height: calc(100vh - 56px); overflow: auto`), a 24 px gutter, a main column of at most 760 px, and the drawer as a 520 px overlay from the right edge (it covers the right 200 px of the card column at 1440, sits wholly in the margin from 1680, and the column never reflows). The page header is 72 px: `<h1>` "Papers" in Newsreader 44/48 with "· 1,788" in mono 20 `--fg-muted` (bound), and the crumb of the active scope in Inter 13 ("§5 Observe › 5.2 Untrusted Monitors", links). At 1024: rail 240, drawer 440. At 768: the rail becomes a horizontal strip of eleven section chips (square mark, number) under the filter bar plus a "Contents" button opening a bottom sheet; the drawer is a full-screen sheet with a sticky close bar. At 390: same, the filter bar collapses to search and a "Filters (2)" button.

### 5.2 Rail ("Contents")

`<nav class="rail" aria-label="Contents">`, a nested list. Eleven `.rail__section` disclosure rows: 3 px rule in `--c`, number in mono 13, title in Newsreader 17/22 wrapping to two lines (never truncated; "Deployment and Assurance" is 24 characters), count in mono 13 right-aligned. The current section is open; others open on the chevron (24 px target) without navigating; the title navigates to `#sN`. Open sections list `.rail__sub` rows in Inter 14/20 (number, wrapping title, count); the current one carries a filled 8 px square in `--c` and `aria-current="location"`. **Live counts**: while any filter or query is active, every count reads "12 / 70" (matches / primary); sections with zero matches stay listed at 55 % opacity, never hidden, so every cross-reference chip resolves. Keyboard: Up and Down move, Right opens, Left closes, Enter follows, Home and End jump. The rail scrolls independently and brings its current row into view on hash change.

### 5.3 Filter bar

Sticky under the masthead (`--z-sticky`, 48 px, hairline below, `--bg`). Row 1: the search input (icon left, placeholder "Search titles, labels, authors, summaries", a `<kbd>/</kbd>` hint right, 320 px), the scope control as a segmented `<fieldset>` of radios "This subsection", "This section", "Whole corpus" (the first disabled when the hash is a section), the sort `<select>` ("Survey order", "Year", "Title"), the density toggle (icon buttons "Full", "Compact", `aria-pressed`). Row 2 (open at 1024 and above, behind "Filters (N)" below): toggle chips "Cited in the PDF" (`cited=1`), "Score 3" (`score=3`), "Chinese notes" (`zh=1`), "Reports and posts" (on by default; off writes `grey=0`); year chips "2026", "2025", "2024", "2023", "2022 and earlier" (`years=…,le2022`), multi-select. Active chips are `--fg` filled with `--bg` text and repeat in an active row with × buttons and "Clear". The results header beneath, `aria-live="polite"`, Inter 14: "70 papers in 5.2 Untrusted Monitors · 10 cited in the PDF · 1 report"; with filters "12 of 70 papers match in 5.2 Untrusted Monitors", and when the scope is narrower than the corpus and the corpus count is larger, "Also 41 matches in the whole corpus" as a link that sets `scope=all`.

Scope defaults: `#sN` opens `sec`, `#sN_M` opens `sub`; `scope=` is written only when it differs. `sub` renders the section head as a crumb and one subsection in full; `sec` the section head and all its subsections; `all` every section. Filters are AND-combined; year chips are OR within.

### 5.4 Search

Indexed per paper: `label`, `title`, `authors` (full names), `one_line`, `reason`, `key`, `arxiv_id`, `year`; per report: `label`, `title`, `authors`, `venue`, `one_line`, `key`. The index is built after first paint in `requestIdleCallback` chunks of 200 (fallback `setTimeout` 0): each field lower-cased, NFD-normalised with diacritics stripped, non-alphanumerics replaced by spaces, stored with a leading space. A query is split on whitespace; minimum two characters; debounce 150 ms. An item matches when every token is a word prefix in some field (`field.includes(" " + token)`). Rank: sum over tokens of the best field weight (label 8, title 4, authors 2, line or reason 1, ids 1), ties by file order; grouping by subsection stays. Matches are wrapped in `<mark>` styled `background: var(--mark-bg); text-decoration: underline 1px; color: inherit`. **Widening**: when a query is active and the scoped result has fewer than 3 matches, the page shows whole-corpus results grouped under section heads and a chip "within 5.3 only" that restores the previous scope. Rail counts reflect the query. Empty: "No papers match 'xyz' in 5.3" with "Clear filters" and "Search the whole corpus". Esc clears the search and blurs; `/` outside inputs focuses it.

### 5.5 Section and subsection heads

`.section-head`: "§5" in mono 20 `--fg-muted`, the title in Newsreader 44/48, an operation chip (square mark, "Observe", to `stream.html?op=observe`; absent for sections 1, 3, 11), the `purpose` paragraph in Newsreader 18/28 at `--measure`. `.sub-head` is `<h3>` inside `<section id="s5_3" data-section="s5">`: "5.3" in mono and the title in Newsreader 28/34; a count line in Inter 13 `--fg-muted`: "57 papers · 6 cited in the PDF · 4 cross-referenced here · 0 reports" from `counts`; a `<details class="sub-head__covers">` "What this subsection covers" listing `bullets` in Newsreader 16/24; the link "N items in the stream" to `stream.html?sub=s5_3` (filled once `stream.json` has loaded; hidden when zero). The last subsection in scope ends with "Next · 5.4 Activation Probes" in Inter 14.

### 5.6 Card

`<article class="card" data-section="s5">`, single column, padding 16 px 12 px, hairline below, `content-visibility: auto; contain-intrinsic-size: 0 150px` (`0 56px` in compact). Fields in order:

1. An 8 px square in `--c` at the left of the label line: filled when `primary` is this subsection; hollow (1 px `--c-border`) with the mono prefix "from 2.4" when listed here through `also`.
2. **Label**: `label` in Newsreader 600 at 18/24, the drawer trigger (`<button class="card__open">` whose `::after` covers the article; `aria-label` "Open {label}: {title}").
3. **Title**: `title` in Inter 15/21, clamped to two lines.
4. **Byline** in Inter 13 `--fg-muted`: surnames of the first three authors, "+N" when longer ("Terekhov, Panfilov, Dzenhaliou +1"), " · " and the year in mono. For 50 or more authors, the first surname and "and N more". Reports show the venue after the year, clamped to one line.
5. **Line**: `one_line` in Newsreader 16/24 clamped to three lines; when empty, `reason` in Inter 14/20 italic `--fg-muted` prefixed "Why here: ".
6. **Marks row**, small caps 11 and mono 13, 8 px gaps: badge "Cited" (`--fg` fill, `--bg` text) when `selected`; mono "3" (`title="score 3, must cite"`) or `--fg-muted` "2" ("score 2, relevant"); badge "中文" (1 px `--rule-strong` border) when `has_zh`, or for reports when the key exists in the loaded `summaries_zh.json`; badge "Report" (sand tint, `data-c="report"`) with `confidence` appended when not "verified" ("Report · likely"); "also in 2.4, 5.5 +3" as chips linking to those subsections; "arXiv 2510.09462" or the report's domain as an external link, raised with `z-index: 1` so it is not covered.

Full density is about 150 px per card; compact keeps fields 1, 2, 4 and 6 in one 56 px row. Order within a subsection: primary papers in file order; then `<details class="runin">` "Reports and posts (3)", open; then `<details class="runin">` "Also placed here (40)", collapsed, holding cross-referenced papers with hollow marks. Rendering is chunked: 24 cards then a sentinel; an `IntersectionObserver` with `rootMargin: 800px` renders the next 24; switching scope removes the previous DOM.

### 5.7 Detail drawer

A native `<dialog class="drawer">` opened with `showModal()`; `::backdrop` transparent at 1024 and above, `--scrim` below; backdrop click, Esc, the × button and Back close it; focus returns to the card. Width 520 at 1440, 440 at 1024, full screen below; slides in over `--t-drawer`; `--shadow-float`. Content, top to bottom: a 6 px band in `--c`; the crumb ("§5 Observe › 5.3 Human Oversight", links); label in Newsreader 32/38; title in Newsreader 20/26; the full author list in Inter 14 collapsed after twelve with "Show all 265 authors"; the meta line in mono 13: year, arXiv id or venue, "score 3", "cited in the PDF" when `selected`, "reading list #5" when `reading_rank` is set; buttons "arXiv abstract", "PDF", "Copy key", "Copy link" (a "Copied" toast for 1.5 s); the one-line summary in Newsreader 18/28; "Why it is here" with `reason` in Inter 14; "Placed in" listing the home subsection and every `also` entry as "2.1 Benign Failures · score 3" with a square mark, each a link that re-scopes the list and closes the drawer; "In the stream" with the count of items whose `related_papers` contain the key or whose `subsections` contain the primary, up to five titles with dates and polarity dashes, a link to `stream.html?paper=<key>`, hidden when the stream is empty.

Then "Reading notes (中文)" when notes exist. `summaries_zh.json` (549 KB) is fetched on the first open that needs it, cached in module scope, a five-line skeleton meanwhile. The head carries the depth badge from `reading_depth` with its English hint in `--fg-muted` (全文 "read in full", 部分 "read in part", 仅摘要 "abstract only", 仅题录 "metadata only") and one line in Inter 13: "Structured reading notes; the depth marks how much of the paper was read." The container is `<section lang="zh-Hans" class="notes">` in `--cjk` 16/29. Fields as a `<dl>` in this order, each `<dt>` the Chinese name in Inter 600 14 with the English gloss in small caps 11 `--fg-muted`: 定位 Positioning; 问题 Problem; 方法 Method; 发现 Findings as `<ol>` (references such as "第 8.1 节" verbatim); 部署启示 Deployer takeaway in `.notes__takeaway`, a `--c-tint` panel with a 3 px left rule in `--c`; 局限 Limitations; 与小节关系 Relation to this subsection; 存疑 Doubts in italic; 术语 Terms as a two-column `<dl class="notes__terms">` split on " = " (English left in Newsreader, Chinese right; one column at 390). Closing meta line in mono 12: "阅读深度 部分 · text depth partial · s5_3".

Footer: "Previous" and "Next" within the current result list with "12 of 70" in mono; keys `j` and `k`; a neighbour replaces the hash. Deep-linking `#paper/<key>` without list context renders the home section at scope `sub` behind the drawer. `#grey/<key>` renders the same drawer for a report with the venue line and the external link to `url`.

### 5.8 States

While `papers.json` (1.3 MB, about 250 KB compressed) and `grey.json` load after first paint, the rail, heads and counts render from `taxonomy.json` and each subsection shows three skeleton rows in `--bg-panel`. A failed fetch renders "The paper list could not be loaded." with "Retry" and logs nothing. The "Chinese notes" filter triggers the `summaries_zh.json` load and computes membership over papers and reports by key, so the count reads 239, not 195. Every subsection has at least one primary paper (11.5 has one), so emptiness arises only from filters.

## 6. Stream Page

### 6.1 Layout and header

At 1440: a sticky filter rail of 260 px, a 24 px gutter, the ledger at most 800 px. `<h1>` "The Live Stream" in Newsreader 44/48; dek in Newsreader 20/30: "News about deploying AI agents, good and bad. Every item is filed under the survey's failure sources, requirements, control operations and subsections." The status line in mono 13 is the **live indicator** (`.live`): an 8 px circle and a label in `--c-text`, graded from `stream.generated` (or `stats.stream_updated` before the stream loads): under 48 hours, forest, "Live · updated 3 h ago"; to 7 days, gold, "Collector last ran 3 days ago"; beyond, coral, "Collector stalled since 10 Oct 2026"; null, `--rule-strong`, "The ledger opens with the first verified sweep". Absolute UTC in `title`; the dot never animates. Beside it: "285 items · sources: seed sweep 2026-10-17, collector". Text buttons: "Submit an item" (`ISSUE_URL`, new tab), "How items are collected" (`about.html#stream`), "Download stream.json" (`<a download>` with the icon; hidden when the stream is absent). At 768 the rail becomes a "Filters (3)" button opening a bottom sheet; at 390 the date moves above the title.

### 6.2 Chronology strip

An inline SVG, 100 % wide, 72 px tall (56 at 768; a "Jump to month" `<select>` at 390), under the header. Months run from the earliest item in the file to the current UTC month; each is a column of width `(W - 2(n-1)) / n` (minimum 6 px), a stacked bar of bad (bottom, `--c-bad`), mixed (`--c-mixed`), good (top, `--c-good`), one unit per item in the **filtered** set, scaled so the tallest month is 56 px; months with zero are a 2 px `--rule-strong` tick. Month labels in mono 11 every third month, year labels in small caps at each January. Each column is an SVG `<a href="#2025-07">` with a `<title>` "July 2025 · 3 bad · 1 mixed · 2 good"; clicking scrolls its month head under the sticky bar and sets the hash. An `IntersectionObserver` on month heads sets `.is-current` on the column (a 2 px `--fg` line under it). The SVG has `role="img"` and an `aria-label` summary ("285 items from February 2024 to October 2026"); the month inputs remain the accessible range control. Drawn from the filtered set, the strip is a histogram of the current query.

### 6.3 Filter rail

`<aside class="facets">`, fieldsets with small-caps legends, in order: Search (placeholder "Search titles, summaries, publishers, tags", `/` focuses, 150 ms debounce, matches `title`, `summary`, `publisher`, `actors`, `tags`, highlighted with `<mark>`); Polarity (good, bad, mixed; dash marks); Failure source (benign, external, insider; circle marks); Operation (the seven operations; square marks in section colours); Requirement (five values; no mark); Kind (eight values); Domain (`<select>` of the fourteen values); Evidence (six values, inside a `<details>` "More"); Subsection (a `<select>` with an `<optgroup>` per section, options "5.2 Untrusted Monitors (12)"); Date range (two `<input type="month">` "From", "To", `pattern="\d{4}-\d{2}"` fallback for Safari); Sort (radios "Date", "Recently verified"); Density ("Full", "Compact"). Every option is a checkbox styled as a chip with a facet count in mono computed against the other active groups; zero-count options stay at 55 % opacity and clickable. OR within a group, AND across groups. Active filters repeat as removable chips above the ledger (a `sub=` chip reads "4.1 Confinement"; a `paper=` chip reads the paper's label once `papers.json` is loaded, the key before) with "Clear all". The rail ends with the panel "How this is collected" (6.6).

### 6.4 Ledger row

`<article class="ledger__row" data-polarity="bad" id="item-<id>">`, grouped under sticky month heads (`.ledger__month`, Newsreader 24/30, "July 2025 · 4 items", hairline below, `id="2025-07"`); in "Recently verified" sort the heads group by `verified_on` month and the date column shows `verified_on` with a small-caps "verified" above it. `content-visibility: auto; contain-intrinsic-size: 0 124px`. Fields in order:

1. Date column, 88 px, mono 13, right-aligned: "17 Oct"; precision `month` shows "Jul" with `title="date known to the month"`; `year` shows "2025" with "date known to the year". A 6 px forest "New" dot (`.new`) under the date when `verified_on` is within seven days, visually hidden text "new this week".
2. A 3 × 18 px polarity dash in `--c` and the kind in small caps 11 ("Near miss", "Safety feature").
3. Title in Newsreader 20/26 clamped to two lines (the 136-character maximum fits), linking to `url` with `rel="noopener"` and the external icon.
4. Summary in Newsreader 16/24 clamped to **two lines** collapsed, full when expanded.
5. Classification line: failure-source chips (circles, "Benign"), operation chips (squares, "Constrain"), requirement chips (plain, "In scope"), then subsection chips with a 3 px left rule in `--c` ("2.1 Benign Failures") linking to `papers.html#s2_1`. Failure-source and operation chips are buttons that apply that filter here (a sliders icon on hover and focus; `aria-label="Filter by Observe"`); subsection chips navigate.
6. On expand only: source line in Inter 13 `--fg-muted`: "Fortune · press · coding · Replit (vendor), SaaStr (deployer)" (nulls omitted); related papers as labels from `papers.json` (fetched on first need; the bib key in mono until loaded) linking to `papers.html#paper/<key>`; verification: a slate check icon, "verified 17 Oct 2026 · seed sweep" (`added_by` with hyphens as spaces) and `verification_note` in a line beneath; "Review pending" in small caps when the optional `needs_review` is true; tags in mono 12; buttons "Copy link" and "Report a problem" (`ISSUE_URL + "&title=" + encodeURIComponent("[Submission]: Correction to " + id)`, new tab).

A "More" button (chevron, `aria-expanded`) at the row's right toggles expansion; Esc on an expanded row collapses it; `#item/<id>` expands and scrolls to the row and flashes its dash once (not under reduced motion). Compact density shows fields 1, 2 and a one-line title, about 40 px per row. The ledger renders 60 rows, then 60 more per sentinel. Collapsed full rows are about 124 px, so a week of items reads in one scroll.

### 6.5 URL state and keyboard

All filters as in 2.4; `sort=verified`, `density=compact`, `from`/`to` as `YYYY-MM`. `#item/<id>` and `#YYYY-MM` are the hash entities. `/` focuses search; Tab order is rail, active chips, strip, rows (title link, chips, More button are separate stops).

### 6.6 Pipeline note and submit path

The panel "How this is collected" (Inter 14/20, `--bg-panel`, hairline border) reads: "The stream was seeded by a verified sweep and is refreshed by a scheduled collector that reads RSS feeds and search results every six hours. A language model classifies each candidate into the survey taxonomy. Every item is fetched and checked before publication; items that cannot be verified are not published. Reader submissions arrive through a GitHub issue and go through the same check." Then counts in mono by `added_by`: "285 items · 279 seed sweep · 6 collector · 0 reader submissions", links "feeds.yml", "collect_news.py", "classify.py", "the workflow" to the repository paths, and "About the stream" (`about.html#stream`). `ISSUE_URL` is `https://github.com/yminglai/controlling-untrusted-ai/issues/new?template=submit_item.yml`; `REPO_URL` is one constant in `common.js`.

### 6.7 States

No matches: "Nothing in the ledger matches these filters" with "Clear all". `stats.stream_items` 0: the page does not request `stream.json` (a 404 would log a console error) and renders the header, the null indicator, a bare baseline strip, the rail at 55 % with `aria-disabled`, and the empty card "The ledger opens with the first verified sweep." with the submit button and the pipeline note. Fetch failure when the file should exist: "The stream could not be loaded." and "Retry". Loading: three skeleton rows.

## 7. About Page

A single column at `--measure`, body in Newsreader 18/30, `<h2>` in Newsreader 28/34 with ids as in 2.4, hairline above each head. Numbers are written from today's `stats.json` with `data-bind` and re-bound at runtime. Copy follows, verbatim.

**The Survey** (`#survey`). The full `taxonomy.thesis` paragraph, bound. Then: "Title: Controlling Untrusted AI: A Survey. Authors: [Authors]. Status: draft v0.2, October 2026; the arXiv link will appear here. This site holds the complete reading list behind the paper, organised by the paper's own sections, and a live record of what has happened when agents were deployed, filed under the same headings." Then a small-caps head "Who It Is For" and the three `taxonomy.readers` paragraphs.

**The Taxonomy** (`#taxonomy`). "Agents must meet five requirements: correct, compliant, in scope, within budget and safe. They fail to meet them for three reasons. Mistakes: {blurb}. Manipulation: {blurb}. Misalignment: {blurb}." (blurbs bound from `taxonomy.failure_sources`). "Control works through two levers. The first changes the deployment around the agent: Constrain what it can do, Observe what it does, Intervene when something is off. The second changes the model: Train before deployment, Steer at inference time. Verify tests either lever with control evaluations, red teams, audits and statistics. Deployment and Assurance composes mechanisms into stacks, safety cases, policy and independent assurance. Every mechanism is graded by a two-level test. L1 asks whether it still works if the agent is indifferent to the requirement. L2 asks whether it still works if the agent tries to defeat it and knows how it works." Then Figure 2 as a `<figure>` (re-encoded, lazy) captioned "Figure 2. Two levers, Verify, and the five questions asked of every mechanism." and the colour key table: one row per section, failure source and polarity with the real mark, the token name and its meaning.

**The Paper Collection** (`#corpus`). "The collection holds {stats.papers} arXiv papers and {stats.grey} reports and posts from outside arXiv, placed in {stats.subsections} subsections of {stats.sections} sections. Each paper has one primary subsection, a score (3, must cite; 2, relevant), a method-style label, a one-line summary where one was written, and a sentence on why it was placed there. Papers that matter to more than one subsection carry cross-references. {stats.cited} items are cited in the PDF; the rest are the reading list behind it. Reports and posts were verified against their source pages; the few not fully verified are marked." Then "The Sections", the 35-row table: eleven `<details>` groups (number, title, 3 px rule, totals) opening to subsection rows with mono columns Primary, Cited, Cross, Reports, 中文 from `taxonomy.counts`; the 中文 column fills from `summaries_zh.json` when the table enters the viewport. Each row links to `papers.html#sX_Y`.

**Reading Notes in Chinese** (`#notes`). "239 items carry structured reading notes in Chinese: positioning, problem, method, findings, deployer takeaway, limitations, relation to the subsection, doubts and a glossary of terms. Each note states how much of the paper was read: in full, in part, abstract only or metadata only. The notes were written against the papers; they are not translations of them. They open from the paper's card." (count bound to `Object.keys(summaries).length` when loaded)

**The Live Stream** (`#stream`). "The stream records real events in the deployment of AI agents: incidents, near misses, deployments, shipped safety features, evaluations, research with direct deployment relevance, policy, and vendor disclosures. Each item is marked good, bad or mixed and classified into the taxonomy: which failure source, which requirement, which control operation, which subsections. The stream was seeded by a verified sweep and is refreshed every six hours by a collector that reads RSS feeds and search results and classifies candidates with a language model. Every item is fetched and its date and claims checked against the source before publication; unverifiable items are not published." A table of the enumerations from `SCHEMA.md`: kind (eight values with their definitions), polarity, evidence, date precision.

**Submit an Item** (`#submit`). "Readers can submit items through a GitHub issue. The form asks for a public URL, a date, two to four factual sentences, whether the item went well or badly, the failure source and the operation involved. The collector reads open submissions every six hours, classifies them, verifies the URL and adds them to the stream marked for review until an editor confirms the classification." Button "Submit an item".

**Cite** (`#cite`). "Until the arXiv version appears, cite the draft as below." A `<pre class="bibtex">` with a "Copy" button:

```
@article{authors2026controlling,
  title  = {Controlling Untrusted AI: A Survey},
  author = {[Authors]},
  year   = {2026},
  note   = {Draft v0.2, October 2026. arXiv link to come.},
  url    = {https://yminglai.github.io/controlling-untrusted-ai/}
}
```

**Data** (`#data`). "The site reads only the files below; they are regenerated from the paper's repository and by the collector. All are UTF-8 JSON under `site/data/`." A list with, per file, a link, its size and generated date (written into the static HTML at build time; the stream row reads "not yet published" while `stats.stream_items` is 0) and a two-line description from `SCHEMA.md`.

**Provenance and Limitations** (`#limitations`). "Three limits apply. The paper cards rest on abstract-level evidence: labels, summaries and placements were written from abstracts and, for cited papers, from the paper text; a card is a pointer, not a review. Stream items are classified by a language model and then verified for URL, date and claims; human review of the classification is pending for items so marked, and until then a classification may be wrong. The collection is a snapshot of the draft: subsections, counts and placements will change as the paper does, and the generated dates above say when."

**Colophon** (`#colophon`). "Set in Newsreader, Inter and IBM Plex Mono, served by Google Fonts with system fallbacks; Chinese text uses the system's own faces. Static HTML, CSS and JavaScript, no build step, no analytics, no cookies, no trackers; the only third-party request is for the typefaces. Light and dark themes follow the system and switch in the masthead. Text and data are released under CC BY 4.0." Links: "Source on GitHub", "Licence".

## 8. Components Inventory

Every interactive component: hover transitions background or border over `--t-hover`; `:focus-visible` is a 2 px solid `--focus` outline, 2 px offset, never removed; `:active` sets `--bg-panel`; disabled is 55 % opacity with `aria-disabled="true"`.

| Component | Classes | States and notes | Pages |
|---|---|---|---|
| Masthead | `.masthead`, `.masthead__title`, `.masthead__nav`, `.masthead--double`, `.nav__link`, `.nav__dot`, `.menu-btn`, `.menu-sheet` | current page underline, `aria-current`; sheet below 1024 | all |
| Theme toggle | `.theme-toggle` | icon swaps; label flips | all |
| Skip link | `.skip-link` | visible on focus, `--fg` on `--bg`, 2 px border | all |
| Running head | `.running-head` | small caps 11 | index, papers, stream |
| Signature bar | `.sigbar`, `.sigbar--sections`, `.sigbar--polarity`, `.sigbar__seg` | widths from data; `--rule` when empty | index, about |
| Title block | `.title-block`, `.title-block__title`, `.dek`, `.byline`, `.status` | | index |
| Button | `.btn`, `.btn--arrow`, `.btn--icon`, `.btn--ghost`, `.btn[aria-disabled]` | 2 px radius, 1 px border; hover `--bg-panel` | all |
| Spread | `.spread`, `.spread__left`, `.spread__right`, `.spread__rule` | 7/5; stacks below 1024 | index |
| Contents | `.toc`, `.toc__row`, `.toc__rule`, `.toc__num`, `.toc__title`, `.toc__count`, `.toc__subs` | hover `--bg-panel` | index |
| Mechanism map | `.mech`, `.mech__bar`, `.mech__lever`, `.mech__node`, `.mech__node--tall`, `.mech__label`, `.mech__keys`, `.mech__counts`, `.mech__test` | `--c` from `data-section`; hover and focus 2 px inset border | index |
| Plate | `.plate`, `.plate__img`, `.plate__caption`, `.dialog`, `.dialog__close` | native dialog, Esc | index, about |
| Readers | `.readers`, `.readers__col` | | index |
| Stat line | `.statline`, `.statline__items`, `.statline__chart` | SVG histogram | index |
| Key | `.key`, `.key__item` | real marks | index, about |
| Mark | `.mark`, `.mark--square`, `.mark--square-hollow`, `.mark--circle`, `.mark--dash`, `.mark--dot` | `--c`; outline in light | all |
| Chip | `.chip`, `.chip--section`, `.chip--source`, `.chip--op`, `.chip--req`, `.chip--sub`, `.chip--plain`, `.chip--removable`, `.chip--filter`, `.is-on` | tint and `--c-border`; `is-on` is `--fg` fill | papers, stream |
| Badge | `.badge`, `.badge--cited`, `.badge--zh`, `.badge--report`, `.badge--depth`, `.badge--new`, `.score` | small caps 11 | papers, stream |
| Rail | `.rail`, `.rail__section`, `.rail__chevron`, `.rail__sub`, `.rail__count`, `.is-open`, `.is-current` | `aria-current="location"`; 55 % when zero | papers |
| Filter bar | `.filterbar`, `.filterbar__search`, `.filterbar__scope`, `.filterbar__sort`, `.filterbar__density`, `.filterbar__chips`, `.filterbar__active`, `.results-head` | sticky; `aria-live` results head | papers |
| Section head | `.section-head`, `.section-head__num`, `.section-head__op`, `.section-head__purpose` | | papers |
| Subsection head | `.sub-head`, `.sub-head__counts`, `.sub-head__covers`, `.sub-head__stream`, `.sub-head__next` | `<details>` for covers | papers |
| Card | `.card`, `.card--report`, `.card--cross`, `.card--compact`, `.card__mark`, `.card__label`, `.card__open`, `.card__title`, `.card__byline`, `.card__line`, `.card__marks`, `.card__ext` | hover `--bg-panel` | papers |
| Run-in group | `.runin`, `.runin__summary` | `<details>` | papers |
| Drawer | `.drawer`, `.drawer__band`, `.drawer__crumb`, `.drawer__label`, `.drawer__meta`, `.drawer__actions`, `.drawer__section`, `.drawer__placed`, `.drawer__stream`, `.drawer__nav`, `.drawer__close` | native dialog; slide 260 ms | papers |
| Reading notes | `.notes`, `.notes__head`, `.notes__depth`, `.notes__field`, `.notes__takeaway`, `.notes__terms`, `.notes__meta` | `lang="zh-Hans"` | papers |
| Live indicator | `.live`, `.live--fresh`, `.live--stale`, `.live--stalled`, `.live--none`, `.live__dot`, `.live__label` | `--c-text` on `--bg` only | stream |
| Chronology | `.chronology`, `.chronology__col`, `.chronology__bar`, `.chronology__tick`, `.chronology__label`, `.is-current`, `.chronology__jump` (select) | SVG `<a>` columns | stream |
| Facets | `.facets`, `.facet`, `.facet__legend`, `.facet__option`, `.facet__count`, `.facets__active`, `.facets__clear`, `.facets__sheet` | counts against other groups | stream |
| Ledger | `.ledger`, `.ledger__month`, `.ledger__row`, `.ledger__row--short`, `.ledger__row--compact`, `.ledger__date`, `.ledger__dash`, `.ledger__kind`, `.ledger__title`, `.ledger__summary`, `.ledger__class`, `.ledger__source`, `.ledger__related`, `.ledger__verified`, `.ledger__more`, `.is-expanded`, `.new` | `aria-expanded` on More | index (short), stream |
| Pipeline panel | `.pipeline`, `.pipeline__counts`, `.pipeline__links` | | stream |
| Skeleton | `.skeleton`, `.skeleton__row` | no animation under reduced motion | papers, stream |
| Empty and error | `.empty`, `.empty__actions`, `.error`, `.error__retry` | | papers, stream |
| Toast | `.toast` | "Copied", 1.5 s, `aria-live` | papers, stream |
| About | `.essay`, `.sections-table`, `.enum-table`, `.bibtex`, `.datalist`, `.colour-key` | | about |
| Footer | `.colophon`, `.colophon__row` | | all |
| Utilities | `.caps`, `.mono`, `.serif`, `.measure`, `.visually-hidden`, `.clamp-1`, `.clamp-2`, `.clamp-3` | | all |

## 9. Accessibility and Performance

**Structure.** Landmarks on every page: `header`, `nav`, `main`, `aside` (rails), `footer`; one `h1` per page; heading levels unbroken. The skip link is first in the tab order. Drawers are native `<dialog>` elements (focus trap, Esc, `aria-modal`) and focus returns to the trigger. Result counts, the live indicator and the toast carry `aria-live="polite"`. Every mark has an adjacent label or `aria-label`; colour is never the only carrier. The chronology strip has a text summary and the month inputs are the accessible range control. Toggle chips use `aria-pressed`, rails `aria-current`, the More button `aria-expanded`. Chinese blocks carry `lang="zh-Hans"`. Tap targets are at least 44 px at 390 and 768. Under `prefers-reduced-motion: reduce` all durations are 0 ms, skeletons do not shimmer, `scrollIntoView` uses `behavior: "auto"`, nothing flashes. Check the landing in Georgia (web fonts blocked) and all pages with VoiceOver before sign-off.

**Contrast pairs to verify** (sRGB; `pipeline/tests/test_contrast.py` recomputes these from `tokens.css` and fails under 4.5:1 for text and 3:1 for marks and focus rings).

| Role | Light (on white / on panel) | Dark (on ink / on dark panel) | Requirement |
|---|---|---|---|
| `--fg` text | 13.58 / 12.68 | 11.29 / 8.22 | 4.5 |
| `--fg-muted` text (13 px) | 5.49 / 5.12 | 8.03 / 5.85 | 4.5 |
| `--fg` on `--c-tint` (chips, nodes, takeaway panel) | worst 11.42 (coral) | worst 7.66 (sky), 7.77 (gold) | 4.5 |
| `--bg` text on `--fg` fill (Cited badge, active chip) | 13.58 | 11.29 | 4.5 |
| `--c-text` live indicator, forest 60 % / gold 50 % / coral 60 % | 5.39 / 4.79 / 6.57 on white only | 6.85 / 8.77 / 5.63 on ink only | 4.5 |
| Raw token marks | coral 3.94, terracotta 3.04, blue 3.41, purple 3.47, periwinkle 3.13, forest 3.07 pass; amber 2.37, teal 2.11, gold 1.99, sand 2.29, slate 2.72 fail, hence the outline | all 3.45 or better | 3.0 |
| Mark outline `--c` 70 % ink on white | amber 3.77, teal 3.42, gold 3.26, sand 3.67, slate 4.19, sky 3.05 | not used | 3.0 |
| Focus ring `--focus` | 3.41 | 5.65 | 3.0 |
| Link underline (decorative) | 3.41 | 5.65 | none |
| Gray `#7D7D7D` as 24 px+ text or rule | 4.12 | 3.30 (rule only) | 3.0 at 24 px |

**Performance.** First paint under 1 s on a laptop: `tokens.css` (about 4 KB), `site.css` (under 20 KB), one page module (under 12 KB) and system fallback fonts; web fonts swap in. Budgets before data: index 60 KB compressed, papers and stream 70 KB. `stats.json` and `taxonomy.json` are preloaded (`<link rel="preload" as="fetch" crossorigin>`); every other JSON fetch appends `?v=<stats.generated>`; `stats.json` uses `cache: "no-cache"`. `papers.json` and `grey.json` load only on the papers page after first paint; `summaries_zh.json` only on first need; `stream.json` only when `stats.stream_items > 0`. The DOM holds at most about 400 cards or rows. Images: `fig1_why_control.jpg` re-encoded to 1600 px under 200 KB; `fig2_mechanism_map.jpeg` re-encoded to 1600 px under 300 KB and used only on About; both with `width`, `height`, `loading="lazy"`; `favicon.svg` (32 × 32, ink square, a 3 px white circle of radius 9 centred); `og.png` 1200 × 630 generated once with headless Chrome from `assets/img/og.html` (title in Newsreader on white, the 11-segment bar beneath). No analytics, no third-party scripts, no console output at warning level or above. The headless check runs all five pages at 1440 × 900 and 390 × 844 in both themes (`?theme=`), against today's data with no `stream.json` and against the fixture copied to `site/data/stream.json`, asserting zero console errors and a visible `h1`, with a screenshot of each.

## 10. File Plan and Split of Work

Matches `BRIEF.md`; nothing else is added. Order of work: tokens and the shell; the papers page (largest content, settled contract); the stream page against `pipeline/tests/fixtures/stream.sample.json` (40 items over six months exercising every enumeration, month and year precision, a 136-character title, an 857-character summary, a `needs_review` item and one with four subsections); the landing last. The three parts proceed in parallel once `tokens.css` and the exports below exist.

**Shell** (one implementer): `site/assets/css/tokens.css`; `site/assets/css/site.css` (every component in section 8 used on more than one page or on index and about, including the ledger base and the drawer base); `site/assets/js/common.js` exporting `REPO_URL`, `ISSUE_URL`, `PAPER_STATUS`, `fetchJSON(path, {version})`, `loadStats()`, `readState()`, `writeState(patch, {push})`, `linkTo(page, state)`, `fmtInt`, `fmtDate(iso, precision)`, `fmtRelative(iso)`, `fmtMonth(yyyymm)`, `authorsLine(list)`, `withinDays(iso, n)`, `initTheme()`, `initMasthead(stats)`, `bindStats(stats)`, `openDrawer(dialog)`, `closeDrawer(dialog)`, `renderLedgerRows(items, {mode})`, `polarityBar(el, counts)`, `debounce`, `idleChunks(array, size, fn)`, `toast(text)`; `site/assets/js/taxonomy.js` exporting `loadTaxonomy()`, `sections`, `subsectionById`, `sectionOf`, `titleOf`, `numberOf`, `operations`, `failureSources`, `requirements`, `colourFor`, `chip({kind, id, href, removable, asFilter})`, `mark({shape, c, hollow})`, `renderToc`, `renderSectionBar`, `renderMechanismMap(el, stats, streamCounts)`, `renderYearHistogram`, `renderKey`; `site/index.html`, `site/about.html`, `site/404.html`; `site/assets/img/favicon.svg`, `og.html`, `og.png`, the two re-encoded figures; the inline theme script and icon sprite as a shared snippet pasted into each page; `pipeline/tests/test_contrast.py`.

**Papers page** (one implementer): `site/papers.html`, `site/assets/css/papers.css` (rail, filter bar, heads, card, run-in groups, drawer content, reading notes, responsive rules), `site/assets/js/papers.js` (indexing `papers.json` and `grey.json` into Maps by key, primary and `also`; scope and filters; chunked rendering; live rail counts; the drawer with notes loader and j/k; stream counts in heads and drawer), `site/assets/js/search.js` (exporting `buildIndex(items, fields)`, `search(index, query)`, `highlight(text, tokens)`; shared with the stream).

**Stream page** (one implementer): `site/stream.html`, `site/assets/css/stream.css` (live indicator, chronology strip, facets and sheet, ledger expansion, pipeline panel, responsive rules), `site/assets/js/stream.js` (conditional load of `stream.json`, facet counts, filtering and sorting, the strip from the filtered set with scroll-spy, row expansion and deep links, chip filters, related-paper labels via a lazy `papers.json` load, download and report links, empty and stale states).

Schema extensions requested of the pipeline, tolerated as absent by the front-end: `grey.json[].has_zh` (the 中文 badge on report cards before the notes file loads), `stats.zh` and `stats.zh_per_subsection` (note counts for the landing and the About table), the optional `stream.json[].needs_review` the collector already emits, and `stream_recent.json` (the twelve newest items) once the stream passes a few hundred items. Each is recorded in `SCHEMA.md` by the pipeline owner before use.
