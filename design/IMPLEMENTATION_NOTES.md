# Implementation notes for the page builders

Written 2026-10-17 by the shell implementer after `tokens.css`, `site.css`, `common.js`, `taxonomy.js`, `index.html`,
`about.html` and `404.html` were finished and verified in headless Chrome (zero console messages, light and dark,
1440 / 768 / 390). This document lists what the papers and stream pages may use and the rules for using it.
`design/DESIGN.md` remains the spec; where this document is silent, the spec governs.

## 1. Rules

1. **Do not edit the shared files**: `site/assets/css/tokens.css`, `site/assets/css/site.css`,
   `site/assets/js/common.js`, `site/assets/js/taxonomy.js`, `site/index.html`, `site/about.html`, `site/404.html`,
   anything under `site/assets/img/`. If a shared change is needed (a new token, a new utility, a bug in a helper),
   write it as a request in `design/requests_papers.md` or `design/requests_stream.md` (what, why, proposed CSS or JS);
   the shell owner applies it. Until then, work around it in your page file.
2. **Page-scoped CSS lives only in `papers.css` or `stream.css`.** Prefix new classes with your page's component
   names from DESIGN.md section 8 (`.rail`, `.filterbar`, `.card`, `.notes` for papers; `.live`, `.chronology`,
   `.facets`, `.pipeline` for stream). Read colour only through roles (`--fg`, `--fg-muted`, `--bg`, `--bg-panel`,
   `--rule`, `--rule-strong`) and `--c` with its derived `--c-tint`, `--c-border`, `--c-text`; never a hue name.
3. **Set `--c` with data attributes, not inline styles**: `data-section="s5"`, `data-op="observe"`,
   `data-source="mistakes"`, `data-polarity="bad"`, `data-c="report|verified|gray|fg"`. Any element carrying one of
   these (and all of its descendants) gets `--c` and the derived colours for free.
4. **Build every URL with `linkTo()` and `readState()` / `writeState()`.** No hand-built query strings.
5. **No console output.** `fetchJSON` throws; catch it and render the error state from the spec. Never log.
6. **Head order is fixed** (see the skeleton): inline theme script, then the fonts link, then `tokens.css`, then
   `site.css`, then your page CSS, then preloads. Icons come from the sprite pasted into the page (section 6).
7. Numbers in static HTML carry `data-bind` so they re-bind at runtime (`bindStats`). Format numbers with `fmtInt`.
8. Headless Chrome enforces a 500 px minimum window, so `--window-size=390,844` renders a 500 px layout cropped.
   For a real 390 viewport, screenshot a temporary wrapper page with a 390 × 844 `<iframe src="papers.html">`
   (its own viewport, media queries apply) at `--window-size=500,844` and crop with `sips -c 844 390`. Delete
   the wrapper afterwards. Theme for screenshots: `?theme=dark` (ignored by `readState()`).

## 2. Tokens (`tokens.css`)

Every custom property in DESIGN.md section 3 exists with that exact name. The ones a page builder touches:

| Group | Tokens |
|---|---|
| Roles | `--bg` `--bg-panel` `--fg` `--fg-muted` `--rule` `--rule-strong` `--link-underline` `--focus` `--mark-bg` `--scrim` `--shadow-float` |
| Current colour | `--c` (set by data attributes), derived per element: `--c-tint` `--c-border` `--c-text` `--mark-outline` |
| Identities | `--c-s1` … `--c-s11`, `--c-failures` `--c-constrain` `--c-observe` `--c-intervene` `--c-steer` `--c-train` `--c-verify` `--c-deploy`, `--c-mistakes` `--c-manipulation` `--c-misalignment`, `--c-good` `--c-bad` `--c-mixed`, `--c-report` `--c-verified` |
| Type families | `--serif` (Newsreader) `--sans` (Inter) `--mono` (IBM Plex Mono) `--cjk` |
| Type sizes | `--fs-display/--lh-display` `--fs-page/--lh-page` (44/48) `--fs-drawer/--lh-drawer` (32/38) `--fs-h2/--lh-h2` (28/34) `--fs-h3/--lh-h3` (24/30) `--fs-dek/--lh-dek` (22/32) `--fs-row-title/--lh-row-title` (20/26) `--fs-label/--lh-label` (18/24) `--fs-body/--lh-body` (16/24) `--fs-ui/--lh-ui` (15/21) `--fs-ui-s/--lh-ui-s` (14/20) `--fs-meta/--lh-meta` (13/18) `--fs-caps/--lh-caps/--ls-caps` (11/16/0.08em) `--fs-mono-s` (12) `--fs-mono-xs` (11) |
| Space | `--s1` 4 `--s2` 8 `--s3` 12 `--s4` 16 `--s5` 24 `--s6` 32 `--s7` 48 `--s8` 64 `--s9` 96 `--s10` 128; `--gutter` 24; `--margin` (48 / 32 / 24 / 16 by breakpoint); `--content-max` 1280; `--measure` 68ch; `--measure-dek` 60ch |
| Shape | `--r0` `--r-chip` 2px `--r-input` 3px `--hairline` `--hairline-strong` `--colour-rule` 3px |
| Layers | `--z-rail` 10 `--z-sticky` 20 `--z-masthead` 30 `--z-sheet` 40 `--z-drawer` 50 `--z-toast` 60 |
| Motion | `--t-hover` 120ms `--t-toggle` 200ms `--t-drawer` 260ms `--ease`; all 0 under reduced motion |

Implementation detail worth knowing: `--c-tint`, `--c-border`, `--c-text` and `--mark-outline` are declared on
`*, ::before, ::after` (not on `:root`) so they recompute from the inherited `--c` on every element. You can
therefore use `background: var(--c-tint)` anywhere below an element that carries a data attribute.

Dark theme is `html[data-theme="dark"]`, set by the inline head script before any stylesheet loads from `?theme`,
then `localStorage["cuai-theme"]`, then `prefers-color-scheme`. Write `[data-theme="dark"] .your-class { … }` only
when a role token cannot express the difference (the spec names two such cases: the plate border and the drawer
backdrop below 1024).

## 3. Utilities and shared component classes (`site.css`)

Utilities: `.caps` (Inter 11/16 uppercase, 0.08em), `.mono`, `.serif`, `.measure`, `.muted` (`--fg-muted`),
`.num` (mono, tabular), `.visually-hidden`, `.clamp-1` `.clamp-2` `.clamp-3`, `.wrap` (content column with margins),
`.grid12` (+ `.span-8`, `.span-8c`), `.block` (vertical rhythm `--s9`, `--s7` below 1024), `.kicker`, `.h2`,
`.icon` (20 px stroke icon) `.icon--s` (14 px) `.icon--ext` (external-link arrow, inline), `.ext` (link that carries
an external icon), `.input` (text input), `.page-head` + `.page-title` (44/48 h1; `.page-title .num` for "· 1,788").

Shared components ready to use (markup produced by the helpers in section 4 where noted):

| Component | Classes | Notes |
|---|---|---|
| Masthead | `.masthead` `.masthead__inner` `.masthead__title` `.masthead__nav` `.masthead__links` `.nav__link` `.nav__dot` `.masthead__sep` `.theme-toggle` `.menu-btn` `.masthead__gh` `.only-sheet` | paste the skeleton; `initMasthead` wires it. No `.masthead--double` outside index |
| Skip link | `.skip-link` | first element in `<body>` after the sprite |
| Running head | `.running-head` | small caps 11 |
| Signature bar | `.sigbar` `.sigbar--sections` `.sigbar--polarity` `.sigbar__seg` `.sigbar__seg--empty` | `polarityBar(el, counts)` fills `.sigbar--polarity`; segments use `style="flex-grow:N"` |
| Count line | `.countline` | mono 13 muted |
| Buttons | `.btn` `.btn--arrow` `.btn--icon` (32 px square) `.btn--ghost` `.btn--sm` `.btn[aria-disabled="true"]` | icon inside via `icon("name")` |
| Marks | `.mark` `.mark--square` `.mark--square-hollow` `.mark--circle` `.mark--dash` (3 × 14) `.mark--dash-l` (3 × 18) `.mark--dot` (6 px) | `mark({shape, c})` |
| Chips | `.chip` `.chip--section` `.chip--sub` `.chip--op` `.chip--source` `.chip--polarity` `.chip--req` `.chip--plain` `.chip--kind` `.chip--removable` `.chip--filter` `.chip__text` `.chip__count` `.chip__x` `.is-on` `.is-zero` (55 %) | `chip({...})`; `[aria-pressed="true"]` renders as `.is-on` |
| Badges | `.badge` `.badge--cited` `.badge--zh` `.badge--report` (needs `data-c="report"`) `.badge--depth` `.badge--new` `.score` `.score--2` `.new` (6 px forest dot) | |
| Ledger base | `.ledger` `.ledger--short` `.ledger--reserve` `.ledger__month` `.ledger__row` `.ledger__row--short` `.ledger__row--late` `.ledger__date` `.ledger__body` `.ledger__kind` `.ledger__dash` `.ledger__title` `.ledger__summary` `.ledger__class` `.ledger__publisher` `.ledger__source` `.ledger__extra` `.ledger__more` `.is-expanded` | `renderLedgerRows`; stream.css adds sticky month heads, expansion content, compact density, the flash |
| Drawer base | `.drawer` `.drawer__band` `.drawer__body` `.drawer__close` `.drawer__crumb` `.drawer__label` `.drawer__title` `.drawer__meta` `.drawer__actions` `.drawer__section` `.drawer__nav` | native `<dialog class="drawer" data-section="s5">`; 520 / 440 / full by breakpoint; backdrop transparent ≥ 1024, scrim below; papers.css adds the content layout and `.notes` |
| Plate and dialog | `.plate` `.plate__btn` `.plate__img` `.plate__caption` `.dialog` `.dialog__close` | |
| Skeleton, empty, error, toast | `.skeleton__row` `.empty` `.empty__actions` `.error` `.error__retry` `.toast` | `toast(text)` creates the toast |
| Key | `.key` `.key__head` `.key__items` `.key__item` `.key__glyphs` | `renderKey(el)` |
| About tables | `.sections-table` `.enum-table` `.colour-key` `.bibtex` `.datalist` | reuse `.enum-table` for any small definition table |
| Footer | `.colophon` `.colophon__row` `.colophon__row--mono` | paste the skeleton; `initFooter` fills the dates |

Interactive-state conventions already in `site.css`: `:focus-visible` is a 2 px `--focus` outline with 2 px offset
on every element (do not remove it); hover transitions use `--t-hover`; `[aria-disabled="true"]` and `.is-disabled`
are 55 % opacity; `mark` elements are styled (`--mark-bg`, 1 px underline).

Breakpoints used by the shared CSS: `(max-width: 1439px)` margin 32, `(max-width: 1023px)` margin 24 and the
menu sheet, `(max-width: 767px)` margin 16 and the phone layouts. Use the same three queries in your page CSS.

## 4. JavaScript helpers

All ES modules; import with `import { … } from "./assets/js/common.js"` and `import * as T from "./assets/js/taxonomy.js"`.
Pages use top-level `await` inside `<script type="module">`.

### `common.js`

Constants: `REPO_URL`, `ISSUE_URL`, `LICENSE_URL`, `SITE_URL`, `PAPER_STATUS`, `THEME_KEY`, `PAGES`,
`KIND_LABELS`, `POLARITY_LABELS`, `SOURCE_LABELS`, `OP_LABELS`, `REQ_LABELS`, `registry` (`{taxonomy, stats}`,
filled by `loadTaxonomy()` and `loadStats()`).

```js
initPage() -> Promise<stats|null>          // initTheme + loadStats + initMasthead + initFooter + bindStats; never throws
initTheme(); initMasthead(stats); initFooter(stats)
loadStats() -> Promise<stats>              // data/stats.json, cache: "no-cache", memoised
loadStream(stats) -> Promise<stream|null>  // null without a request when stats.stream_items is 0
fetchJSON(path, {version, cache}) -> Promise<any>   // memoised per URL; appends ?v=version; throws on !ok
dataVersion() -> string                    // stats.generated or <meta name="data-version">; pass as {version}
readState() -> {hash, ...queryKeys}        // query merged with hash (no "#"); "theme" ignored; multi-values stay "a,b"
writeState(patch, {push=false}) -> url     // null/""/false removes a key; {hash} sets the hash; push stores {drawer:true}
linkTo(page, state) -> string              // page: "index"|"papers"|"stream"|"about" or a file name; keys sorted
fmtInt(n); fmtDate(iso, precision="day", {year}); fmtDateLong(iso); fmtMonth("2025-07"); fmtRelative(iso); monthKey(iso)
withinDays(iso, n); authorsLine(list); firstSentences(text, n)
bindStats(stats, extra) // fills [data-bind="stats.papers"], [data-bind="taxonomy.thesis|sentences:2"]; filters: int date month sentences:N firstkey lastkey or:X count; data-bind-attr="title" writes an attribute
esc(s); icon(name, cls="icon") -> html; fragment(html) -> DocumentFragment; el(html) -> Element
mark({shape, c, hollow, label}) -> html    // shape: square|square-hollow|circle|dash|dash-l|dot; c: any identity id
chip({kind, id, href, removable, asFilter, label, count, on, title}) -> html
   // kind: section|sub|op|source|polarity|req|plain|kind. asFilter -> <button aria-pressed data-kind data-id>;
   // href -> <a>; removable -> × button with data-remove=id. Delegate clicks on [data-kind][data-id] / [data-remove].
labelFor(kind, id); dataAttrFor(id)
renderLedgerRows(items, {mode:"short"|"full", groupBy:"date"|"verified"}) -> DocumentFragment  // <li> month heads + rows
renderLedgerRow(item, {mode, index, groupBy}) -> <li>   // full rows: fields 1-5 collapsed, an empty hidden .ledger__extra slot, a .ledger__more button (aria-expanded)
polarityBar(el, {good, bad, mixed}); polarityCounts(items)
openDrawer(dialog, {hash, returnTo}); closeDrawer(dialog, {homeHash})   // showModal + pushState({drawer:true}); Back closes; focus returns
debounce(fn, ms); onIdle(fn, timeout); idleChunks(array, size, fn) -> Promise; toast(text, ms=1500); copyText(text, label); reducedMotion()
```

### `taxonomy.js`

```js
await loadTaxonomy() -> taxonomy            // fills the live bindings below and registry.taxonomy
sections, operations, failureSources, requirements, taxonomy   // live bindings (empty before load)
subsectionById("s5_3") -> {id, number, title, slug, bullets, counts, section:"s5"}
sectionOf("s5_3"|"s5") -> section; titleOf(id); numberOf(id) ("§5" | "5.3"); fullTitle(id) ("5.3 Chain-of-Thought Monitoring")
operationOf("s5") -> operation|undefined; colourFor(id) -> hex; tokenFor(id) -> "--c-s5"; primaryCount(section)
chip, mark                                   // re-exported from common.js
renderToc(el); renderSectionBar(el, stats); renderMechanismMap(el, stats, counts); updateMechanismCounts(el, counts)
streamCounts(items) -> {sources, ops, subs, total}; renderYearHistogram(el, stats.years); renderKey(el)
renderColourKey(el); renderSectionsTable(el); fillZhCounts(el, summaries)
```

## 5. Data facts checked on 2026-10-17

`stats.json`: 1,788 papers, 174 reports, 240 cited, 56 subsections, 11 sections, `stream_items` 231,
`stream_updated` `2026-10-17T00:00:00Z`. `stream.json` exists with 231 items (97 bad, 93 good, 41 mixed; 227 day
precision, 4 month; all `verified_on` 2026-10-17, so every row currently shows the "New" dot; `added_by` is
`seed-sweep` throughout; dates 2024-02-01 to 2026-10-17). `summaries_zh.json` has 239 entries keyed by bib key,
each with `sid`. `grey.json` has no `has_zh` field yet (compute membership from the notes file, as the spec says).

## 6. Page skeleton

Copy this; replace the title, description, the page CSS link, the `<main>` and the module. Keep the order.

```html
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Papers · Controlling Untrusted AI</title>
<meta name="description" content="…">
<meta name="data-version" content="2026-10-17">
<meta name="color-scheme" content="light dark">
<meta name="theme-color" content="#FFFFFF" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#2E2E2E" media="(prefers-color-scheme: dark)">
<meta property="og:type" content="website">
<meta property="og:title" content="…">
<meta property="og:description" content="…">
<meta property="og:url" content="https://yminglai.github.io/controlling-untrusted-ai/papers.html">
<meta property="og:image" content="https://yminglai.github.io/controlling-untrusted-ai/assets/img/og.png">
<meta name="twitter:card" content="summary_large_image">
<script>(function(){try{var q=new URLSearchParams(location.search).get("theme");var t=(q==="dark"||q==="light")?q:localStorage.getItem("cuai-theme");if(t!=="dark"&&t!=="light"){t=matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light"}document.documentElement.setAttribute("data-theme",t)}catch(e){document.documentElement.setAttribute("data-theme","light")}})();</script>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400..700;1,6..72,400..500&amp;family=Inter:wght@400;500;600&amp;family=IBM+Plex+Mono&amp;display=swap">
<link rel="stylesheet" href="assets/css/tokens.css">
<link rel="stylesheet" href="assets/css/site.css">
<link rel="stylesheet" href="assets/css/papers.css">
<link rel="icon" href="assets/img/favicon.svg" type="image/svg+xml">
<link rel="preload" href="data/stats.json" as="fetch" crossorigin>
<link rel="preload" href="data/taxonomy.json?v=2026-10-17" as="fetch" crossorigin>
</head>
<body>
<!-- icon sprite: copy the <svg hidden> block verbatim from site/index.html (ids i-arrow-right, i-arrow-up-right,
     i-search, i-sliders, i-chevron-down, i-x, i-sun, i-moon, i-copy, i-check, i-link, i-file, i-list, i-clock,
     i-download, i-flag, i-menu, i-lock, i-eye, i-hand, i-dial, i-compass, i-shield-check, i-layers) -->
<a class="skip-link" href="#main">Skip to content</a>
<header class="masthead">
  <div class="wrap masthead__inner">
    <a class="masthead__title caps" href="index.html"><span class="long">Controlling Untrusted AI: A Survey</span><span class="short">Controlling Untrusted AI</span></a>
    <nav class="masthead__nav" aria-label="Site">
      <button class="menu-btn" type="button" aria-expanded="false" aria-controls="site-links"><svg class="icon" aria-hidden="true"><use href="#i-menu"/></svg>Menu</button>
      <ul class="masthead__links" id="site-links">
        <li><a class="nav__link" href="papers.html">Papers</a></li>
        <li><a class="nav__link" href="stream.html">Stream</a></li>
        <li><a class="nav__link" href="about.html">About</a></li>
        <li class="only-sheet"><a class="nav__link" href="https://github.com/yminglai/controlling-untrusted-ai" rel="noopener">GitHub</a></li>
      </ul>
      <span class="masthead__sep" role="presentation"></span>
      <button class="theme-toggle" type="button" aria-label="Switch to dark theme"><svg class="icon i-moon" aria-hidden="true"><use href="#i-moon"/></svg><svg class="icon i-sun" aria-hidden="true"><use href="#i-sun"/></svg></button>
      <a class="nav__link masthead__gh" href="https://github.com/yminglai/controlling-untrusted-ai" rel="noopener">GitHub</a>
    </nav>
  </div>
</header>
<main id="main">
  <div class="wrap">
    <!-- page content; one <h1>; <aside> for rails; headings unbroken -->
  </div>
</main>
<footer class="colophon">
  <div class="wrap">
    <p class="colophon__row colophon__row--mono">Data generated <span data-footer-generated>2026-10-17</span> · Stream updated <span data-footer-stream>17 Oct 2026</span></p>
    <p class="colophon__row"><a href="https://github.com/yminglai/controlling-untrusted-ai/issues/new?template=submit_item.yml" rel="noopener">Submit an item</a> <a href="about.html#cite">Cite</a> <a href="about.html#data">Data</a> <a href="https://github.com/yminglai/controlling-untrusted-ai" rel="noopener">GitHub</a> <span>No analytics, no cookies, no trackers. Typefaces served by Google Fonts.</span> <a href="https://github.com/yminglai/controlling-untrusted-ai/blob/main/LICENSE" rel="noopener">CC BY 4.0 for text and data</a></p>
  </div>
</footer>
<script type="module">
import { initPage, bindStats, readState, writeState, linkTo, fetchJSON, dataVersion } from "./assets/js/common.js";
import * as T from "./assets/js/taxonomy.js";
const [stats, tax] = await Promise.all([initPage(), T.loadTaxonomy().catch(() => null)]);
if (tax) bindStats(stats || {}, { taxonomy: tax });
// page logic; render from taxonomy first, then load papers.json / grey.json (papers) or stream.json (stream) after first paint
</script>
</body>
</html>
```

`initPage()` sets `aria-current="page"` on the nav link whose `href` matches the current file, adds the Stream dot
when `stats.stream_updated` is within seven days, wires the Menu sheet and the theme toggle, fills the footer dates,
and runs `bindStats(stats)` for `data-bind="stats.*"`.

## 7. Snippets of shared behaviour you will need

```js
// filter chips (stream facets, papers toggle chips): render, then delegate
el.innerHTML = chip({ kind: "op", id: "observe", asFilter: true, count: 128, on: state.op?.split(",").includes("observe") });
el.addEventListener("click", (e) => { const c = e.target.closest("[data-kind][data-id]"); if (c) toggle(c.dataset.kind, c.dataset.id); });

// drawer
const dlg = document.querySelector(".drawer");
dlg.dataset.section = paper.section;                     // colours the band
openDrawer(dlg, { hash: "paper/" + paper.key });         // pushState; Back closes
closeDrawer(dlg, { homeHash: paper.primary });           // or let Esc / backdrop / × call dialog.close()

// ledger rows on the stream page
ledger.replaceChildren(renderLedgerRows(filtered, { mode: "full", groupBy: state.sort === "verified" ? "verified" : "date" }));
// then fill .ledger__extra on expand and toggle .is-expanded + aria-expanded on .ledger__more

// a shared stream count for subsection heads (papers page)
const counts = T.streamCounts(stream.items); counts.subs["s5_3"]  // -> number of items filed under 5.3
```

## 8. Known gaps and notes for the shell owner

- `site.css` is about 29 KB uncompressed (spec budget: under 20 KB); it carries the drawer and ledger bases and the
  About tables. Compressed it is well under 10 KB. Trim only if the whole-page budget is missed.
- Footer and About link the licence to `REPO_URL/blob/main/LICENSE` because `LICENSE` sits at the repository root and
  the site is published from `site/`; the spec's relative `LICENSE` would 404 on GitHub Pages.
- `og:image` and `og:url` are absolute (crawlers require it); every other URL is relative.
- `pipeline/tests/test_contrast.py` exists since the 2026-10-17 review fixes (102 role pairs from `tokens.css`) and runs in
  `.github/workflows/pages.yml` with the data contract and collector tests.
- The "New" dot is suppressed when it would carry no information: on the stream page when more than half of all items were
  verified this week, on the landing when every one of the twelve rows is new (`renderLedgerRows({showNew})`). With the
  seed, where all 231 items carry `verified_on: 2026-10-17`, no dot shows until the collector adds later items. Earlier note:
  all 231 stream items carry `verified_on: 2026-10-17`, so every landing ledger row shows the "New" dot until the
  collector adds later items; this is the specified behaviour, not a bug.

## 9. Review fixes of 2026-10-17 (what changed in the shared files)

The four review passes (visual, data, accessibility and performance, design and copy) were applied in one fixing pass;
`design/REVIEW_SUMMARY.md` lists every finding and its outcome. Rule 1 above still holds for page builders; the shared
files were edited by the fixer and these are the additions a page builder may now rely on.

**Tokens.** `--control-border` (light `var(--gray)` 4.12:1 on white, dark `color-mix(gray 75%, white)` 5.45:1 on ink) is
the border of inputs, selects, the segmented control, buttons, badges and plain, requirement and subsection chips;
`--rule-strong` stays a hairline (masthead separator, `kbd` hint, chip separators). `--measure-dek` is 68ch. `--sticky-h`
is set on `<html>` by `papers.js` from the live height of the filter bar's first row (masthead 56 + row + 8) and read by
`scroll-padding-top` in `site.css` and the `scroll-margin-top` of `.sec` and `.sub`; other pages fall back to 72 px. In the
dark theme, marks and dashes inside `.is-expanded`, hovered rows and cards, `.pipeline`, `.notes__takeaway` and `.bibtex`
take `--mark-outline: color-mix(--c 55%, white)` because raw hues fall under 3:1 on the dark panel.

**Shared components.** Zero-count chips and rail rows are no longer faded: `.is-zero` sets `--fg-muted` and a dashed
border and keeps the control clickable. Below 1024 px every `.chip` is at least 32 px tall with a 44 px hit area from a
`::before` (so a positioned `.chip__x` or icon must stay `position: relative` to receive clicks), `.btn--icon`,
`.ledger__more` and the theme toggle are 44 px squares, `.btn--sm` is 36 px with a 44 px hit area. The drawer's close
button sits in a zero-height sticky strip (`.drawer__top`) at every width; the 440 px drawer applies from 1439 px down.
`@media (forced-colors: active)` keeps the colour marks and outlines pressed and checked states.

**common.js.** `chip({toggle})`: toggle filters (default) carry `aria-pressed` and are named by their visible text and
count; `toggle: false` renders an action button named "Filter by X" without a pressed state (the ledger's row chips).
`renderLedgerRows({showNew})` controls the "New" dot; in `groupBy: "verified"` the month head reads "· verified".
`polarityBar()` writes the counts into the bar's `aria-label`. `firstSentence(text)` is exported.

**taxonomy.js.** The year histogram uses a square-root scale with a 3 px floor; mechanism-map keywords clamp to three
lines and carry a `title`; the section bar's `aria-label` lists the counts; the About colour key omits the operation in
parentheses when it equals the section title; the sections table reads `counts.zh`.

**Data.** `grey.json` records carry `also` (cross-references, `score: null` when the second bib key of one document was
folded in) and `has_zh`; grey items that are arXiv papers are merged into `papers.json` (the paper becomes `selected`,
the grey subsection joins its `also`); `confidence` is `verified | likely | unverified`; every grey `url` is set.
`taxonomy.json` subsections carry `counts.zh`; 2.3 Insider Threats has no primary paper in the October outline and the
papers page renders an empty state for it. `stats.json` adds `source_generated`, `zh` and `stream_polarity`,
`stream_per_source`, `stream_per_op`, `stream_per_sub`; the landing reads these and `stream_recent.json` (twelve newest
items) instead of `stream.json`. `stream.json` carries `taxonomy_generated`; the collector warns and the tests fail when
it differs from `taxonomy.json`.

**Papers page.** Only `.filterbar__row1` is sticky; the chip rows scroll. The rail is one Tab stop (roving tabindex,
arrows move; chevrons are `tabindex="-1"`) and a second skip link "Skip to results" targets `#results-head`
(`tabindex="-1"`). Filter chips are built once and updated in place; removing an active chip moves focus to the next
chip, Clear, or the matching filter chip. Drawer Previous, counter and Next are persistent nodes in `papers.html`. The
rail sheet below 1024 sets `inert` on the rest of the page. The results head counts cited papers and reports together
(matching the chip); the subsection head keeps `counts.selected` (papers only). Reports without a URL show the venue
instead of a link (none remain in the data).

**Stream page.** The chronology `<svg>` is `role="group"`, its month links are `tabindex="-1"` and the "Jump to month"
select is the strip's single keyboard stop (visually hidden until focused above 767 px). In "Recently verified" sort a
strip column resolves to the first row of that event month. The expanded row shows evidence and domain labels and the
first sentence of the verification note with "Show full note". A failed fetch resets the live indicator and the count line.

**Not changed, by decision.** The headings "Who This Is For", "Who It Is For", "Submit an Item", "By the Numbers" and
"Reading the Marks" are DESIGN.md verbatim. "robustness" in the third readers paragraph is the paper's own wording (the EU
AI Act's term) bound from `outline.json` and is kept. `papers.json` is not split per section (BRIEF allows it; the file
loads after first paint and the split would touch every route); the collector's verification notes keep their full text
in the data and are shortened only in the UI.
