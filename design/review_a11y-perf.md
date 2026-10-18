# Review: accessibility, performance, robustness (lens a11y-perf)

Reviewer run of 2026-10-17 against the site served from `site/` on `http://localhost:8765/`. No site file was edited.
Severity: blocker (must fix before publishing), major (a user group is blocked or an AA criterion fails on a primary
control), minor (AA edge case, degraded-state wording, or avoidable cost). Findings are ordered most severe first.

## 1. What was checked and how

| Check | Method | Result |
|---|---|---|
| Contrast of every text/background and UI pair in `tokens.css`, both themes | `python3` script reproducing `color-mix(in srgb)` as sRGB interpolation and WCAG 2.x luminance; 14 role pairs and 12 identities x 12 surfaces per theme (full tables in section 2) | 4 failing role pairs in light, 4 in dark; marks and rules below 3:1 for 5 hues on white |
| Console errors on every page | Headless Chrome `--headless=new --enable-logging=stderr --v=0 --virtual-time-budget=12000 --dump-dom`, 25 URLs: index (light, dark), papers (all, `#s5`, `#s5_3`, `?q=monitor`, `#paper/sharkey2025open` light and dark, legacy `#sub=s5_3`), stream (all, `?op=observe&polarity=bad`, `#item/<id>` light and dark, `?paper=<key>`, unknown `#item/`), about, 404, and the three degraded servers below | 0 console messages in all 25 runs |
| Relative URLs | `grep -rnE 'href="/|src="/|fetch\(['"'"'"]/|url\(/|import\(['"'"'"]/|action="/'` over `site/*.html`, `site/assets/js`, `site/assets/css` | none; only `og:url`, `og:image`, GitHub, arXiv and Google Fonts are absolute |
| Landmarks, heading order, alt text, labels, nameless buttons, duplicate ids, live regions | stdlib HTML parser over the 25 DOM dumps | header/nav/main/aside/footer on every page; one `h1` per page; no heading-level jumps; every `img` has `alt`; every input labelled; no nameless button; no duplicate ids. One defect: 33 focusable `<a>` inside an `svg role="img"` (finding 4) |
| Focus-visible, keyboard operability of drawer, sheets, chips, rail | Read of `common.js`, `papers.js`, `stream.js`, `site.css`, `papers.css`, `stream.css` | findings 1, 2, 7, 8, 9, 12 |
| `prefers-reduced-motion` | `tokens.css` zeroes `--t-*`; `site.css` kills transitions, shimmer and dialog fade; `stream.css` kills the flash and the sheet slide; `papers.css` the chevrons; JS gates `scrollIntoView` and `flash()` on `reducedMotion()` | no gap found |
| Missing or empty `stream.json` | Three copies of `site/` served on 8766 (file deleted), 8767 (0-byte file), 8768 (`{"items":[]}`), with `stats.json` still saying 231 items; DOM dumps and screenshots of index, stream and `papers.html#s5_3` on each | no console error, no blank page; wording and one disabled panel are off (findings 13, 14) |
| Payload sizes | `ls -l site/data`, `gzip -c | wc -c`, `curl -w` against the Google Fonts CSS | section 3; `papers.json` is not fetched on the landing; `stream.json` (652 KB, 170 KB gzip) is |

Artefacts (not part of the repo): `scratchpad/a11y/contrast.py`, `console/*.log`, `dom/*.html`, `shots/*.png`
(`m8766_index.png`, `m8766_stream.png`, `z8767_stream.png`, `e8768_index.png`, `e8768_stream.png`,
`e8768_papers_s5_3.png`, `stream_dark.png`, `stream_item_dark.png`, `papers_drawer_dark.png`, `papers_zero.png`).

## 2. Contrast tables

Role pairs. Threshold 4.5:1 for text, 3:1 for focus rings, borders and icons (WCAG 1.4.3, 1.4.11).

| Pair | Light | Dark | Where it is used |
|---|---|---|---|
| `--fg` on `--bg` | 13.58 | 11.29 | body |
| `--fg` on `--bg-panel` | 12.68 | 8.24 | hovered cards, expanded ledger rows, pipeline panel, bibtex |
| `--fg-muted` on `--bg` | 5.47 | 8.03 | all 13 px meta, 11 px caps |
| `--fg-muted` on `--bg-panel` | 5.11 | 5.86 | meta inside expanded rows and panels |
| `--bg` on `--fg` | 13.58 | 11.29 | `.chip.is-on`, `.badge--cited`, toast, checked segments |
| `--focus` on `--bg` | 3.41 | 5.64 | the global focus ring |
| `--focus` on `--bg-panel` | 3.18 | 4.11 | focus ring over panels |
| `--focus` on `--fg` | 3.99 | **2.00** | inset ring on a checked `.seg__opt` / `.facet__radio` span (finding 6) |
| `--rule-strong` on `--bg` | **1.69** | 3.30 | `.input`, `.btn`, `.seg`, `.chip--plain` borders (finding 5) |
| `--rule-strong` on `--bg-panel` | **1.58** | **2.41** | the same borders over panels |
| `--fg` at opacity .55 over `--bg` | **3.36** | 4.56 | `.chip.is-zero` label, `.rail .is-zero` titles (finding 3) |
| `--fg` at opacity .55 over `--bg-panel` | **3.29** | **3.73** | the same on hover |
| `--fg-muted` at opacity .55 over `--bg` | **2.25** | **3.54** | `.rail .is-zero > .rail__count`, `.chip.is-zero .chip__count` (finding 3) |

Per identity, light theme (`--c-tint` = 14 % of the hue on white). Columns: text `--fg` on the tint, `--fg-muted` on the
tint, `--c-text` on `--bg`, chip border `--c-border` on `--bg`, the raw hue on `--bg` (marks, 3 px rules, bars),
`--mark-outline` on `--bg`, the focus ring on the tint, and the hue on its own tint (the mechanism-map inset focus ring).

| Hue | fg/tint | muted/tint | c-text/bg | border/bg | hue/bg | outline/bg | focus/tint | hue/tint |
|---|---|---|---|---|---|---|---|---|
| gray (s1, s3, s11) | 11.58 | 4.66 | 6.54 | 5.80 | 4.12 | 5.80 | 2.90 | 3.51 |
| coral (s2, mistakes, bad) | 11.40 | 4.59 | 6.58 | 5.77 | 3.94 | 5.77 | 2.86 | 3.31 |
| terracotta (s4) | 11.78 | 4.74 | 5.42 | 4.66 | 3.04 | 4.66 | 2.95 | **2.64** |
| blue (s5, link) | 11.73 | 4.72 | 5.80 | 5.05 | 3.41 | 5.05 | 2.94 | **2.94** |
| amber (s6, manipulation) | 12.14 | 4.89 | 5.38 | 3.79 | **2.37** | 3.79 | 3.04 | **2.12** |
| teal (s7) | 12.31 | 4.96 | 4.97 | 3.43 | **2.11** | 3.43 | 3.09 | **1.91** |
| periwinkle (s8) | 11.84 | 4.77 | 5.46 | 4.72 | 3.13 | 4.72 | 2.97 | **2.73** |
| forest (s9, good) | 11.86 | 4.78 | 5.39 | 4.64 | 3.07 | 4.64 | 2.98 | **2.68** |
| purple (s10, misalignment) | 11.74 | 4.73 | 5.86 | 5.11 | 3.47 | 5.11 | 2.94 | 3.00 |
| gold (mixed) | 12.41 | 5.00 | 4.77 | 3.27 | **1.99** | 3.27 | 3.11 | **1.82** |
| sand (report) | 12.25 | 4.93 | 5.22 | 3.67 | **2.29** | 3.67 | 3.07 | **2.07** |
| slate (verified) | 12.03 | 4.84 | 4.93 | 4.20 | **2.72** | 4.20 | 3.02 | **2.41** |

Per identity, dark theme (`--c-tint` = 18 % of the hue on ink; `--c-border` is the hue itself; marks have no outline).

| Hue | fg/tint | muted/tint | c-text/bg | hue on bg (= border, marks) | hue on `--bg-panel` | hue/tint |
|---|---|---|---|---|---|---|
| gray | 9.14 | 6.50 | 5.88 | 3.30 | **2.41** | **2.67** |
| coral | 9.34 | 6.65 | 5.65 | 3.45 | **2.51** | **2.85** |
| terracotta | 8.73 | 6.21 | 6.71 | 4.46 | 3.26 | 3.45 |
| blue | 8.85 | 6.30 | 6.43 | 3.99 | **2.91** | 3.13 |
| amber | 8.18 | 5.82 | 7.85 | 5.73 | 4.18 | 4.15 |
| teal | 7.93 | 5.64 | 8.45 | 6.45 | 4.70 | 4.53 |
| periwinkle | 8.68 | 6.17 | 6.76 | 4.34 | 3.17 | 3.33 |
| forest | 8.64 | 6.15 | 6.84 | 4.42 | 3.23 | 3.39 |
| purple | 8.85 | 6.30 | 6.41 | 3.91 | **2.85** | 3.07 |
| gold | 7.79 | 5.54 | 8.79 | 6.84 | 4.99 | 4.72 |
| sand | 8.05 | 5.73 | 8.12 | 5.92 | 4.32 | 4.22 |
| slate | 8.38 | 5.97 | 7.36 | 5.00 | 3.65 | 3.71 |

All chip text, all `--c-text` labels (`.live__label`, glyphs, the verified tick) and all `--fg-muted`-on-tint pairs
pass in both themes. The failures are the opacity trick, the light input borders, the dark inset focus ring, and
coloured objects that rely on hue alone without the 1 px outline.

## 3. Payload facts

| File | Raw | Gzip | Loaded by |
|---|---|---|---|
| `data/stats.json` | 525 B | 270 B | every page |
| `data/taxonomy.json` | 77.5 KB | 22.9 KB | every page except 404 |
| `data/stream.json` | 652 KB | 170 KB | **index (after idle, for 12 rows and three counts)**, stream, papers (idle +3 s, for the "N items in the stream" links) |
| `data/papers.json` | 1.30 MB | 359 KB | papers (eagerly, whatever the route), stream (only for `?paper=` or an expanded row with related papers) |
| `data/grey.json` | 90 KB | 22 KB | papers |
| `data/summaries_zh.json` | 562 KB | 222 KB | papers on first note or "Chinese notes" filter; **about (to compute 56 counts)** |
| `assets/img/fig1_why_control_web.jpg` | 203 KB (1600 x 995) | | index, `loading="lazy"`, displayed at most 853 px wide |
| Google Fonts CSS | 12 KB | | every page, render-blocking `<link rel="stylesheet">`; 0.20 to 0.40 s measured with `curl` from this machine; latin woff2: Newsreader 147 KB (plus italic), Inter 48 KB x 3 weights, Plex Mono 10 KB |
| CSS + JS, landing | 77 KB | 23 KB | tokens 7.2 + site 29.8 + common 25.7 + taxonomy 14.8 |

`papers.json` is not requested on the landing. `content-visibility: auto`, chunked rendering (24 cards / 60 rows per
chunk) and `.ledger--reserve` (no layout shift) are in place and work.

## 4. Findings

### Major

**1. Every filter chip on the papers page drops keyboard focus when activated.**
`site/assets/js/papers.js:388` (`renderChips`) rebuilds `dom.chips.innerHTML` on every `renderView`, and
`toggleChip -> setFilter -> route -> renderView` runs on each chip press (`papers.js:932-944`, `618-631`). The button
the user just pressed with Enter or Space is removed, focus falls to `<body>`, and the next Tab starts again at the
skip link; a keyboard user toggling "Cited in the PDF" then a year must tab through the masthead, the rail (11 to 67
stops) and the search bar to reach the second chip. Same pattern for the active-filter row (`papers.js:404`).
Evidence: code; the chips are `<button aria-pressed>` (`common.js:287`) so this is the primary keyboard path.
Fix: update the existing chip buttons in place (set `aria-pressed`, `is-zero`, `.chip__count` text, as `stream.js:216-224`
already does for the facets) and only rebuild when the set of chips changes; for the active row, move focus to the
next chip or to `#clear-filters` after a removal.

**2. The drawer's Previous / Next buttons lose focus on use, and j / k stop working afterwards.**
`site/assets/js/papers.js:726` (`renderDrawerNav`) replaces `nav.innerHTML`, and `fillDrawer` replaces
`dom.drawerBody.innerHTML` (`papers.js:705`), on every `stepDrawer` (`papers.js:728-738`). Pressing Enter on "Next"
removes the focused button; focus leaves the dialog's focusable content, so the `dlg` keydown listener for j / k
(`papers.js:910-915`) no longer receives key events until the user tabs back through the whole drawer (actions,
placed-in links, stream links, notes) to reach "Next" again. The `aria-live` counter inside the nav is also recreated
each time, so it may not announce. Evidence: code; `papers_drawer_dark.png` shows the nav ("1 of 55").
Fix: keep the two buttons and the counter as persistent nodes, toggle `aria-disabled` and set the counter's
`textContent`; after `fillDrawer`, if `document.activeElement` is not inside the dialog, focus the button that was
pressed (or `#drawer-label` with `tabindex="-1"`).

**3. Zero-count chips and rail items are still interactive but fall to 3.36:1 (labels) and 2.25:1 (counts) in light.**
`site/assets/css/site.css:195` (`.chip.is-zero { opacity: .55 }`) and `site/assets/css/papers.css:42`
(`.rail .is-zero > .rail__count, .rail__sub.is-zero, .rail__row.is-zero .rail__title { opacity: .55 }`) are applied
to buttons and links that remain clickable (`papers.js:849-852`, `stream.js:554-556`), so WCAG 1.4.3 applies and
fails: 13 px chip label 3.36:1, 13 px count 2.25:1, 17 px / 14 px rail titles 3.36:1 (dark: 4.56 / 3.54 / 4.56, and
3.73 over `--bg-panel` on hover). Evidence: `contrast.py` rows "fg @ opacity .55"; `papers_zero.png` shows the whole
rail and the "2022 and earlier 0" chip faded while a search is active. The disabled-control exemption does not apply:
nothing is `disabled` or `aria-disabled`.
Fix: express the zero state with colour, not opacity: `.chip.is-zero { color: var(--fg-muted); border-style: dashed }`
and `.chip.is-zero .chip__count { color: var(--fg-muted) }` (5.47:1 light, 8.03 dark); for the rail use
`color: var(--fg-muted)` on title and count; if a zero chip is meant to be inert, add `disabled` and the exemption holds.

**4. The chronology strip is an `svg role="img"` that contains 33 focusable links.**
`site/assets/js/stream.js:311` sets `role="img" aria-label="231 items from February 2024 to October 2026"` on the svg
and `stream.js:303` puts one `<a class="chronology__col" href="#YYYY-MM">` per month inside it (33 months in the current
data; the DOM dump has 33 distinct `data-month` links). `role="img"` has presentational children, so assistive
technology is told the links do not exist while the browser still tabs through all 33 of them, one unnamed stop per
month, before the first ledger row. Together with the facet rail that is about 85 Tab presses to reach the ledger,
against DESIGN.md 6.5 "Tab order is rail, active chips, strip, rows". Evidence: `domcheck.py` on `dom/stream.html`:
"focusable `<a>` inside svg[role=img]: 33"; `stream_dark.png` shows the strip.
Fix: give the svg `role="group" aria-label="Chronology, 231 items from ..."` (or `role="figure"`) so the named links
are exposed, and put `tabindex="-1"` on the month links while showing the "Jump to month" `<select>`
(`stream.js:310`, currently `display:none` above 767 px) at every width as the single keyboard stop.

### Minor

**5. Light-theme control borders are 1.69:1 (1.58 on panels).**
`site/assets/css/tokens.css:23` sets `--rule-strong: var(--gray-mid)` (#C7C7C7) and it is the only boundary of
`.input` (`site.css:305`), `.seg` (`papers.css:55`), `.btn` (`site.css:87`), `.chip--plain`/`--req`/`--sub`
(`site.css:185-186`) and `.badge` (`site.css:198`). For the search, month and select inputs the border is the component
boundary (WCAG 1.4.11 asks 3:1); buttons and chips also carry text so they pass on the label. Dark passes (3.30) on
`--bg` but not over `--bg-panel` (2.41). Fix: a dedicated `--border-control: var(--gray)` (#7D7D7D, 4.12:1 on white,
3.30 on ink) for inputs, selects, the segmented control and chip borders; keep `--rule-strong` for hairlines.

**6. In dark, the inset focus ring on a checked segment is 2.00:1.**
`papers.css:62` (`.seg__opt input:focus-visible + span { outline: 2px solid var(--focus); outline-offset: -2px }`) and
`stream.css:61` (same for `.facet__radio`) draw the ring inside a span whose background is `--fg` when checked
(`papers.css:61`, `stream.css:60`). Dark `--focus` #82AADD on #EAEAEA is 2.00:1 (light: 3.99). The checked option is
exactly the one the user lands on when tabbing into the group. Fix: `outline-color: var(--bg)` for the checked span
(`input:checked:focus-visible + span`), or move the ring outside with `outline-offset: 2px` on the `.seg`.

**7. Mechanism-map focus and hover ring uses the hue on its own tint: 1.91 (teal) to 3.00 (purple).**
`site.css:122` (`.mech__node:has(:focus-visible) { box-shadow: inset 0 0 0 2px var(--c) }`) on a `--c-tint` surface;
the label's own outline (`--focus` on tint) is 2.86 to 2.98 in light. Fix: ring in `--c-border` (3.4 to 5.8 on white)
or `--fg`; dark already passes (3.07 to 4.72).

**8. Classification chips inside ledger rows claim `aria-pressed` but never reflect state and cannot toggle off.**
`common.js:333-335` renders source and operation chips with `asFilter: true` (`<button aria-pressed="false"
aria-label="Filter by X">`); `stream.js:590` calls `setMulti(g, id, true)` (always on) and `updateFacets`
(`stream.js:216-224`) only updates chips inside `fieldset[data-group]`. With `?op=observe` active, every row's "Observe"
chip still says `aria-pressed="false"` (0 of 52 rows pressed in `dom/stream_filtered.html` while the facet chip is
pressed). A toggle button whose state is wrong is worse than a plain action. Fix: render row chips as links
(`href: linkTo("stream", {op})`, as the subsection chips already are) or as buttons without `aria-pressed`.

**9. Three more places drop focus after a keyboard action.**
`stream.js:259` rebuilds the active-filter row on each render (pressing a chip's remove button drops focus to body);
`stream.js:334` `ledger.replaceChildren()` after a row chip press (plus a scroll to the top of the ledger,
`stream.js:590`); `papers.js:622` `dom.results.replaceChildren()` after an in-results link (`a[data-hash]`) is
followed. Fix: after each of these, move focus deliberately (next removable chip or "Clear all"; the results heading
`#results-head` / `#results` with `tabindex="-1"`).

**10. No `forced-colors` handling: marks, pressed states and custom radios disappear in Windows High Contrast.**
`grep forced-colors site/assets/css` finds nothing. `.mark`, `.ledger__dash`, `.sigbar__seg`, `.toc__rule` are
background-only (`site.css:74,175,215`); `.chip.is-on` / `[aria-pressed="true"]` and the checked `.seg__opt` /
`.facet__radio` convey state by background inversion only (`site.css:188`, `papers.css:61`, `stream.css:60`); the
radio inputs themselves are `opacity: 0` (`papers.css:57`, `stream.css:57`). Fix: `@media (forced-colors: active)`
with `forced-color-adjust: none` on `.mark` and the dashes, and a 2 px `border-color: Highlight` (or `outline`) for
pressed and checked states.

**11. Thin colour-only objects below 3:1 on white: amber 2.37, teal 2.11, gold 1.99, sand 2.29, slate 2.72.**
Marks are rescued by the 1 px `--mark-outline` (3.27 to 5.80), but the 6 px `.sigbar__seg` (`site.css:74`), the 3 px
section rules (`.toc__rule`, `.rail__row` border, `.section-head` border, `.drawer__band`, `.chip--sub` left border)
and the chronology bars (`stream.css:80`) have none. Where the colour is redundant with text this is fine under 1.4.1;
it is not redundant in the polarity sigbar (`role="img" aria-label="Items by polarity: good, bad, mixed"` without the
counts; the counts live only in `title` on hover, `common.js:355`) and in the chronology, where the gold "mixed"
segment sits between coral and forest. Dark: coral, gray, blue and purple fall to 2.4 to 2.9 on `--bg-panel` (expanded
rows, hovered cards, pipeline), where the `.ledger__dash` is the polarity signal (it does carry `aria-label`).
Fix: put the numbers in the sigbar `aria-label` ("93 good, 97 bad, 41 mixed") and in the strip's `aria-label`; add a
1 px `--bg` gap or `stroke` between stacked chronology segments; consider a `--mark-outline` on `.ledger__dash` in dark.

**12. The bottom sheets below 1024 px are not modal: focus and reading order continue behind the scrim.**
Papers rail sheet (`papers.js:353-359`, `papers.css:210-211`) and stream facets sheet (`stream.js:535-546`,
`stream.css:160-161`) open with a click-only scrim and `body { overflow: hidden }`; Esc closes them, but Tab leaves
the sheet into the obscured page and screen readers can read behind it. Fix: set `inert` on `main`'s siblings (or
`aria-hidden`) while open, or render the sheets as `<dialog>` with `showModal()` like the drawer.

**13. A failed `stream.json` fetch is presented as an empty ledger and a live collector.**
With `stats.json` saying 231 items and `stream.json` missing (8766) or 0 bytes (8767): the landing shows "No items yet"
and "The ledger opens with the first verified sweep." (`index.html:173-178`, `emptyLedger()` is used for both the
no-items and the error case, `index.html:184-185`), the masthead keeps the green "updated this week" dot, and the
stream header still reads "Live · updated 23 h ago · 231 items" above "The stream could not be loaded." (`stream.js:646`
sets the indicator from stats before `load()`). Evidence: `m8766_index.png`, `m8766_stream.png`, `z8767_stream.png`;
`dom/m_index.html` count line "No items yet". Fix: distinguish `null` (no items) from a thrown fetch in `index.html`
and render "The stream could not be loaded" with the "All items" link; in `renderError()` reset `#live` to the none
state and `#stream-sources` to "231 items · not loaded".

**14. With `items: []` the pipeline panel is disabled along with the facets.**
`renderNoStream()` sets `aria-disabled="true"` on `#facets` (`stream.js:490`) and `stream.css:32` applies
`opacity: .55; pointer-events: none` to it; at 1024 px and above the pipeline panel lives inside that aside
(`stream.js:213`, `placePipeline`), so its five links (feeds.yml, collect_news.py, classify.py, the workflow, About the
stream) are faded and unclickable in exactly the state where a reader wants to know how items will arrive. Evidence:
`dom/e_stream.html` (facets aria-disabled: true, pipeline inside aside); `e8768_stream.png`. Fix: in `renderNoStream`
move the pipeline into `#stream-main` (as below 1024) or scope the disabled rule to `.facet` elements.

**15. The landing downloads the whole stream (652 KB, 170 KB gzip) for twelve rows and three counts.**
`index.html:182-195` loads `stream.json` after idle via `loadStream(stats)` (`common.js:69`) to render 12 ledger rows,
the polarity bar and the per-operation / per-source counts of the mechanism map. First paint is not affected (the
request is deferred), but on a phone this is the largest transfer of the page after fonts. Fix: have
`pipeline/collect_news.py` also write `stream_recent.json` (the 12 newest items) and the counts into `stats.json`
(`polarity`, `per_op`, `per_source`), and read those on the landing; `stream.json` stays for the stream page.

**16. The Google Fonts stylesheet is render-blocking, cross-origin, and has no preconnect of its own.**
`index.html:22` (and the other four pages) is a plain `<link rel="stylesheet">` to `fonts.googleapis.com`; only
`fonts.gstatic.com` is preconnected (`index.html:21`). Measured from this machine the CSS alone is 0.20 to 0.40 s of
TTFB before first paint, and the selected axes fetch about 147 KB (Newsreader upright) plus italic, 3 x 48 KB (Inter)
and 10 KB (Plex Mono). `display=swap` and the metric fallbacks (`site.css:5-6`) are good. Fix: add
`<link rel="preconnect" href="https://fonts.googleapis.com">`, load the stylesheet non-blocking
(`<link rel="preload" as="style" onload="this.rel='stylesheet'">` with a `<noscript>` fallback), and consider
`Newsreader:ital,opsz,wght@0,6..72,400..600` if 700 is unused.

**17. Three avoidable data costs on the papers and about pages.**
(a) `papers.js:103-116` fetches the full `papers.json` (359 KB gzip) for every route, including `#s5_3` with 57 papers;
BRIEF.md allows a per-section split. (b) `about.html:166` fetches `summaries_zh.json` (222 KB gzip) only to count notes
per subsection for the sections table. (c) `fig1_why_control_web.jpg` is 1600 px / 203 KB for a slot of at most 853 px
(`index.html:118`). Fix: (a) `build_data.py` writes `papers/s1.json` ... `papers/s11.json` plus a small key -> section
index, `loadPapers` fetches the visible section first and the rest on idle; (b) add `counts.zh` per subsection to
`taxonomy.json`; (c) add a 1000 px rendition with `srcset`/`sizes`, keep the 1600 px file for the dialog.

**18. `#live` is an `aria-live="polite"` region rewritten every 60 seconds.**
`stream.js:180-181` re-runs `setLive`, which assigns `label.textContent` even when the string is unchanged; screen
readers that announce on any mutation will repeat "Live · updated 23 h ago" once a minute. Fix: assign only when
the text differs, or drop `aria-live` from `#live` (the state is static during a visit).

**19. Filter chips hide their counts from assistive technology.**
`common.js:287` gives every `asFilter` chip `aria-label="Filter by X"`, which replaces the visible "X 93" (label and
count). Sighted users see 93 items; screen-reader users hear "Filter by Good, toggle button, not pressed". Fix: drop
`aria-label` (the visible text already names the control) or include the count: `aria-label="Good, 93 items"`.

**20. The contrast test promised by the spec does not exist.**
DESIGN.md section 9 (`design/DESIGN.md:341`) names `pipeline/tests/test_contrast.py` as the thing that recomputes the
pairs; `pipeline/tests/` has only `test_build_data.py` and `test_collector.py`, and findings 3, 5, 6 and 7 would have
been caught by it. Fix: add the test (the script used here is 60 lines of stdlib Python) with the role pairs of
section 2 as assertions, run in `.github/workflows/pages.yml`.

## 5. What passed

Zero console messages in all 25 headless runs including the degraded servers; all URLs relative; landmarks and
heading order correct on every page and route (sub view promotes the subsection to `h2`, drawer `h2` -> `h3`);
descriptive `alt` on both figures; every input labelled; skip link, `aria-current`, `aria-expanded`/`aria-controls`
on menu, filter toggle, rail chevrons, "More" buttons; native `<dialog>` with `showModal()` for drawer and figure
(focus trap, Esc, Back closes, focus returned to the opener); Esc on an expanded row collapses it and refocuses;
`prefers-reduced-motion` honoured in CSS and JS; `content-visibility`, chunked rendering and reserved ledger height
keep scrolling and layout stable; `papers.json` is never fetched on the landing; dark theme text pairs all above 5.8:1.
