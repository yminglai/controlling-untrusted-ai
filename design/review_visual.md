# Visual QA review of the companion site

Reviewer lens: visual. Date: 2026-10-17. Target: `site/` served at `http://localhost:8765/` (the running `python3 -m http.server`).
Spec of record: `design/DESIGN.md` (with `design/IMPLEMENTATION_NOTES.md`). No site file was edited.

## Method

- Headless Chrome static captures of `index.html`, `papers.html`, `papers.html#s5_5` (and the `#sub=s5_5` form), `papers.html#paper/greenblatt2024alignment` (and the `#paper=` form), `stream.html`, `stream.html?polarity=bad` (and `#f=polarity:bad`), `about.html`, `404.html` at 1440×900, 1440×3500 (plus 1440×5200 for the landing), and a true 390-wide viewport (390×844, 390×3000, 390×7000; headless Chrome clamps the window to 500 px, so 390 was captured through a 390 px iframe and then re-verified with DevTools device emulation), in light and dark (`?theme=`). Tablet (768) captures of all four main pages.
- Console: `--enable-logging=stderr --dump-dom` on all ten URLs.
- Interactive states: the Claude Browser preview could not attach because port 8765 is held by a non-preview process and `.claude/launch.json` is outside this reviewer's write scope, so interactions were driven over the Chrome DevTools Protocol with a small Node script (`Input.dispatchMouseEvent`, `Input.dispatchKeyEvent`, `Input.insertText`, `Emulation.setDeviceMetricsOverride`, `Page.captureScreenshot`, `Runtime.evaluate`): card hover, keyboard Tab traces, `/`, search typing and Esc, drawer open/scroll/`j`/Esc, density and theme toggles, cross-reference chip and rail clicks, stream row expansion, chip filters, chronology hover/click, sort and density radios, Filters/Contents/Menu sheets at 390 and 768, the Figure 1 dialog, the About sections table, fonts blocked (`Network.setBlockedURLs` on Google Fonts) and `prefers-reduced-motion: reduce`.
- Contrast: recomputed from `tokens.css` for the derived pairs (chip counts on tints, `--c-text` glyphs, marks on panel surfaces, control borders, 55 % opacity states).
- Screenshots referenced below live in the session scratchpad `shots/` directory (file names given per finding).

## What passed

- Zero console messages on all ten URLs in headless Chrome (the only exception seen under CDP came from a Chrome extension content script in the test profile, not from the site).
- Both themes render consistently on every page; the dark theme keeps the section, failure-source and polarity hues legible on `--bg`; the live indicator, Cited badge, active chips and `--fg` on tints all meet 4.5:1 as the spec tabulates.
- With web fonts blocked, Georgia/Arial fallbacks load as `Newsreader Fallback`/`Inter Fallback` and the Spread starts at the same y (520 px): no layout shift.
- `prefers-reduced-motion: reduce` zeroes `--t-hover`, `--t-drawer` and the TOC transition.
- Theme toggle flips `data-theme`, `aria-label` and `localStorage`; the skip link is the first Tab stop; `/` focuses search; search updates the URL (`?q=monitor`), rail live counts ("2 / 66") and `<mark>` highlights; Esc clears and blurs.
- Drawer: opens with `showModal`, pushes `{drawer:true}` and the `#paper/<key>` hash, focuses the close button, `j` advances to the next paper and rewrites the hash, Esc closes and returns focus to the card's open button. Chinese notes render with the tinted takeaway panel and two-column terms at 1440, one column at 390.
- Stream: row expansion shows source line, related-paper label chips, slate verified check, note, tags, Copy link and Report a problem; chip filters write `?source=misalignment`, update the title ("· 47 of 231") and the facet counts; chronology click sets `#2025-08` and lands the month head just under the masthead; Recently-verified sort and compact density behave as specified; the 390 Filters sheet opens full-width, scrolls, locks body scroll and closes on Esc.
- Landing: TOC hover, mechanism-node hover (2 px inset) and focus (count link is its own Tab stop), Figure 1 dialog with Esc; 390 Menu sheet and TOC chevrons work.
- About: sections table expands, the 中文 column fills from `summaries_zh.json` on scroll, bibtex Copy button present.
- The alternative hash forms `#sub=s5_5` and `#paper=<key>` render identically to the canonical ones on the papers page.

## Findings

Severity scale: blocker (page unusable or broken for a core task), major (a core task is impaired or a spec requirement with user impact is missed), minor (visible defect with a bounded consequence). Lines are 1-indexed in the file named.

| # | Severity | File | Line | Summary |
|---|---|---|---|---|
| 1 | major | site/assets/css/papers.css | 46 | Sticky filter bar is 165 px (two rows); fixed chrome at 1440×900 is 222 px, not 56+48 |
| 2 | major | site/assets/css/papers.css | 86 | Hash navigation lands the subsection head under the sticky stack (scroll-margin 120 px, `scrollToResults` assumes 48 px bar) |
| 3 | major | site/assets/css/papers.css | 162 | Drawer close button scrolls out of view at ≥768 (absolute, not sticky) |
| 4 | major | site/assets/css/site.css | 183 | Tap targets at 390/768 are 18 to 36 px against the 44 px requirement (chips, More button, card links, chevrons) |
| 5 | minor | site/assets/css/site.css | 140 | Mechanism-map bar counts sit below the label baseline (`margin-top:auto` leaks from the node rule) |
| 6 | minor | site/papers.html | 98 | Search placeholder clipped mid-word ("summari") at 1440; same string clips at 390 on 404.html |
| 7 | minor | site/assets/js/papers.js | 264 | "Cited in the PDF 240" chip vs "191 cited in the PDF" head on one screen; "Chinese notes" jumps 195 → 245 and disagrees with About's 239 (six keys duplicated across papers.json and grey.json) |
| 8 | minor | site/data/papers.json (pipeline/build_data.py) | — | 116 cards show "Why here: Requested by name by the pass-2 agent" |
| 9 | minor | site/assets/css/papers.css | 214 | 390 section strip clips the §5 chip under the Contents button with no scroll affordance |
| 10 | minor | site/assets/css/tokens.css | 68 | Dark theme: raw marks on `--bg-panel` fall to 2.4 to 2.9:1 (expanded rows, hovered cards, pipeline panel) |
| 11 | minor | site/assets/css/site.css | 195 | Zero-count chips and rail rows at 55 % opacity drop to 3.36:1 (label) and 2.27:1 (count) in light |
| 12 | minor | site/assets/css/tokens.css | 23 | Light-theme control borders (`--rule-strong` #C7C7C7) are 1.69:1 on white |
| 13 | minor | site/assets/js/taxonomy.js | 167 | Year histogram collapses 2016 to 2022 into 1 px dashes; seven years indistinguishable |
| 14 | minor | site/assets/js/stream.js | 306 | Chronology strip never labels 2024; first column reads "Feb" with no year |
| 15 | minor | site/assets/js/papers.js | 488 | Score digit has only a `title`; unexplained "3"/"2" on touch and for assistive tech |
| 16 | minor | site/assets/js/papers.js | 339 | Rail has arrow keys but no roving tabindex: about 44 Tab stops before the first card |
| 17 | minor | site/assets/css/site.css | 339 | At exactly 1024 px the drawer is 520 px with transparent backdrop (spec 440 px) |
| 18 | minor | site/assets/css/site.css | 79 | Spread starts at y=520 at 1440×900 (spec ≈380); 2.5 ledger rows above the fold |
| 19 | minor | site/assets/js/taxonomy.js | 112 | Mechanism-map keywords clamp mid-word ("self-…", "information…") with no tooltip |

### 1. Sticky filter bar takes 222 px of every viewport (major)

- File: `site/assets/css/papers.css:46` (`.filterbar { position: sticky; top: 56px; … }`) with `:69` (`.filterbar__row2 { display:block }`) and `:47` (`.filterbar__row1 { min-height:48px; padding:8px 0 }`).
- Evidence: CDP measurement on `papers.html` at 1440×900: `{masthead:57, filterbar:165, filterbarTop:178, sticky_total:222}`. `shots/i_papers_scrolled_sticky.png` (scrolled 1500 px): cards start at y=222, the masthead, search row, nine chips and the year chips all stay fixed. At 390 with Filters open (`shots/j_p390_filters.png`) the bar grows to about 330 px and is still sticky.
- Consequence: a quarter of a 900 px laptop viewport is permanently chrome while reading cards; on a 768-tall laptop it is 29 %. DESIGN.md 5.3 specifies a 48 px sticky bar.
- Fix: make only `.filterbar__row1` sticky and let `.filterbar__row2` scroll with the page (`.filterbar { position: static } .filterbar__row1 { position: sticky; top: 56px; z-index: var(--z-sticky); background: var(--bg); }`), or add `.filterbar.is-scrolled .filterbar__row2 { display:none }` toggled by a scroll listener once `scrollY > 200`, with the active-filter summary moved into the "Filters (N)" button label at every width.

### 2. Hash navigation hides the target head under the sticky stack (major)

- Files: `site/assets/css/papers.css:86` and `:93` (`.sec, .sub { scroll-margin-top: 120px }`), `site/assets/js/papers.js:632-634` (`scrollToResults` subtracts `56 - 48 - 8`) and `:636-640` (`scrollToTarget` uses `scrollIntoView({block:"start"})`).
- Evidence: from `papers.html#s5` → click rail 5.3 → click the first cross-reference chip (`a.chip--sub`, to `#s8_3`): `{hash:"#s8_3", targetTop:185, stickyBottom:221}`. `shots/i_papers_after_chip_click.png`: only the count line "50 papers · 5 cited in the PDF · 9 cross-referenced here · 1 report" is visible under the filter bar; the "8.3 Reasoning-Based Safety" title is behind it. Compare `shots/i_papers_after_rail_sub_click.png` where the re-render happened to land correctly (289 > 237) because the page was at scroll 0.
- Consequence: every chip link ("also in 2.4"), "Next · 5.4" link and drawer "Placed in" link that changes the hash while the page is scrolled hides the heading the reader just asked for; they must scroll up 40 to 100 px to see where they landed. Both hard-coded offsets encode the spec's 48 px bar, not the built 165 px bar.
- Fix: measure the live sticky height and feed it to CSS: `const h = 56 + document.querySelector('.filterbar').offsetHeight + 8; document.documentElement.style.setProperty('--sticky-h', h + 'px')` in a `ResizeObserver` on `.filterbar`, then `.sec, .sub { scroll-margin-top: var(--sticky-h, 120px) }` and use the same value in `scrollToResults`. If finding 1 is fixed to a 48 px bar, 120 px becomes correct again.

### 3. Drawer close button scrolls away (major)

- File: `site/assets/css/papers.css:162` (`.drawer__top { position:absolute; top:14px; right:14px }`) overriding `site/assets/css/site.css:240`; the sticky variant exists only in `@media (max-width: 767px)` at `papers.css:249`.
- Evidence: `papers.html#paper/greenblatt2024alignment` at 1440×900: dialog `scrollHeight 2853`, after `scrollTop = 1400` the close button rect is `{top:-1372, visibleInViewport:false}`. `shots/j_drawer_scrolled_1440.png` and `shots/j_drawer_1024.png` show the notes with no × anywhere; only the 6 px band stays. At 390 (`shots/j_drawer_390_scrolled.png`) the sticky bar keeps the × at y=20, as intended.
- Consequence: a reader deep in the Chinese notes has no visible way to close the drawer; Esc works, and at ≥1024 a click on the transparent backdrop works, but neither is discoverable, and at 768 to 1023 the scrim invites a click but the × is gone.
- Fix: apply the mobile rule at all widths: `.drawer__top { position: sticky; top: 6px; display:flex; justify-content:flex-end; padding: 8px var(--s5); background: var(--bg); z-index:1 }` (remove the absolute positioning), or render a "Close" text button inside the sticky `.drawer__nav` footer next to Previous/Next.

### 4. Touch targets below 44 px at 390 and 768 (major)

- Files: `site/assets/css/site.css:183` (`.chip` min-height 22 px), `:66` (`.btn--icon` 32 px, used by `.ledger__more`), `:346` (`.toc__chevron` 44×30), `site/assets/css/papers.css:122` (`.card__open`, 24 px line), `:216` (`.strip__chips .chip` 28 px), `site/assets/css/stream.css:164` (`.facets .chip` 36 px in the sheet).
- Evidence (CDP, 390×844, mobile emulation): stream `{more:"32x32", chip:"115x22", subchip:"230x22", filters:"95x38", jump:"358x35"}`; papers `{filtersBtn:"90x36", stripChip:"45x28", contents:"100x30", cardOpen:"90x24", cardExt:"142x18", alsoChip:"37x20", covers:"194x22", streamLink:"129x18"}`; index `toc chevron 44x30`; 768 facets sheet `chip 108x36`. `shots/j_s390.png`, `shots/j_p390.png`, `shots/stream_390x3000_light.png` (three rows of 22 px chips with 6 px gaps per item).
- Consequence: DESIGN.md 9 requires 44 px targets at 390 and 768. The classification chips are the stream's primary filter affordance and the subsection chips its link back to the papers; at 22 px with 6 px gaps mis-taps are routine. The More chevron (32 px) is the only way to expand a row.
- Fix: in `@media (max-width: 1023px)`: `.chip { min-height: 32px; padding-inline: 10px; position: relative } .chip::before { content:""; position:absolute; inset:-6px }` (44 px hit area without changing the visual rhythm), `.ledger__more, .filterbar .btn--icon { width:44px; height:44px }`, `.toc__chevron { height:44px }`, `.ledger__class { gap: 10px 8px }`, `.card__ext, .sub-head__stream, .sub-head__covers summary { min-height:44px; display:inline-flex; align-items:center }`.

### 5. Mechanism-map bar counts misaligned (minor)

- File: `site/assets/css/site.css:140` (`.mech__counts { margin-top:auto; … padding-top:4px }`) applied inside `.mech__bar` (`:122`, a centred flex row).
- Evidence: `shots/crop_mech_light.png` and `crop_mech_dark.png`: "213 papers" sits about 8 px below the baseline of "How Agents Fail"; "130 papers · 85 items" likewise under "Deploy and Assure". Visible in `shots/index_1440x3500_light.png` and `index_390x7000_light.png`.
- Fix: `.mech__bar .mech__counts { margin-top:0; padding-top:0; align-self:center; }`.

### 6. Search placeholder clipped (minor)

- Files: `site/papers.html:98`, `site/404.html:91`; CSS `site/assets/css/papers.css:48-49` (320 px input, 30 px padding each side).
- Evidence: CDP `{inputWidth:318, padL:"30px", padR:"30px", textWidth:267}`: 267 px of text in 258 px. `shots/papers_1440x900_light.png` reads "Search titles, labels, authors, summari"; `shots/404_390x844_light.png` reads "Search titles, labels, authors, sur".
- Fix: shorten to "Search titles, labels, authors" (or "Search papers"), or set `.filterbar__search { width: 352px }`; on 404 add `.input::placeholder { text-overflow: ellipsis }`.

### 7. Counts disagree on the same screen (minor)

- Files: `site/assets/js/papers.js:264` (results head counts `cited` over papers only), `:386` (chip counts over papers and reports), `:936` (zh chip recount after `loadNotesFile`); data: `site/data/grey.json` shares six keys with `site/data/papers.json`.
- Evidence: whole-corpus view: chips "Cited in the PDF 240 · Chinese notes 195 · Reports and posts 174", head "1,788 papers in the whole corpus · 191 cited in the PDF · 174 reports" (`shots/papers_1440x900_light.png`). After clicking "Chinese notes": chip "245", head "195 of 1,788 papers match · 50 reports" (`shots/i_papers_zh_filter.png`), while `about.html#notes` says 239. Python over the data: 239 note keys, 195 in papers, 50 in grey, 6 in both (`benton2024sabotage`, `guo2026personalization`, `hadfieldmenell2016off`, `hubinger2019risks`, `kaufman2025basharena`, `perez2022red`), so those six items also render twice (as a paper card and as a report card).
- Fix: in `resultsHeadHTML` count cited items over papers and reports (`sc.cited + sc.citedGrey`) so 240 matches the chip, or phrase it "191 papers and 49 reports cited"; in `pipeline/build_data.py` drop grey entries whose key exists in papers.json (or rename their keys) so the notes count reads 239 and nothing is listed twice.

### 8. Pipeline jargon on 116 cards (minor)

- File: `site/data/papers.json` (`reason` field), produced by `pipeline/build_data.py` from `research/corpus_full.json`.
- Evidence: cards 4 and 5 of 1.1 in `shots/papers_1440x3500_light.png` and several in `shots/papers_s5_5_1440x3500_dark.png` read "Why here: Requested by name by the pass-2 agent"; 116 of 1,788 papers carry that reason (python count).
- Fix: in `build_data.py`, map reasons matching `/pass-\d agent/` to a reader-facing sentence ("Named in the section plan") or set `reason` to empty so the card omits the "Why here" line.

### 9. Mobile section strip clips with no affordance (minor)

- File: `site/assets/css/papers.css:214` (`.strip__chips { overflow-x:auto; scrollbar-width:none }`), `:215` hides the WebKit scrollbar.
- Evidence: CDP `{scrollW:588, clientW:250}`; `shots/papers_390x844_light.png`, `shots/j_p390.png`: the §5 chip is cut in half by the Contents button and §6 to §11 are not hinted.
- Fix: `mask-image: linear-gradient(90deg, #000 calc(100% - 24px), transparent)` on `.strip__chips`, plus `scroll-snap-type: x proximity` and `scroll-padding-inline: 8px`; or show the current section's chip first.

### 10. Dark-theme marks on panel surfaces under 3:1 (minor)

- File: `site/assets/css/tokens.css:68-71` (`[data-theme="dark"] … --mark-outline: transparent`), surfaces at `site/assets/css/stream.css:96` (`.ledger__row.is-expanded { background: var(--bg-panel) }`), `papers.css:115` (card hover), `:22` (rail hover), `stream.css:140` (pipeline panel).
- Evidence: CDP on the expanded dark row: `{rowBg: rgb(67,67,67), dash: rgb(217,83,88), chipMark: rgb(163,124,173)}`; computed ratios on #434343: coral 2.51, purple 2.85, blue 2.90, gray 2.40, periwinkle 3.16, forest 3.22 (amber, teal, gold, sand, slate pass). `shots/j_s_expanded_dark.png`.
- Fix: `[data-theme="dark"] .is-expanded .mark, [data-theme="dark"] .is-expanded .ledger__dash, [data-theme="dark"] .card:hover .mark { outline: 1px solid color-mix(in srgb, var(--c) 55%, white) }`, or set `--bg-panel` in dark to `color-mix(in srgb, var(--ink) 94%, white)` (#3A3A3A, coral 2.9 → still short, so prefer the outline).

### 11. 55 % opacity states fall below AA (minor)

- Files: `site/assets/css/site.css:195` (`.chip.is-zero { opacity:.55 }`), `:21` (`[aria-disabled], .is-disabled`), `site/assets/css/papers.css:42` (rail `.is-zero`).
- Evidence: "2023 0" chip in `shots/papers_s5_5_1440x900_light.png`; computed: `--fg` at .55 on white 3.36:1, `--fg-muted` at .55 on white 2.27:1 (dark: 4.53 and 3.53). These chips remain clickable per DESIGN.md 6.3, so they are not exempt as disabled controls.
- Fix: fade only the mark and the count (`.is-zero .mark, .is-zero .chip__count { opacity:.55 }`) and keep the label at `--fg-muted` (5.49:1), or raise the opacity to .7 (≈4.6:1 for `--fg`).

### 12. Control borders at 1.69:1 in light (minor)

- Files: `site/assets/css/tokens.css:23` (`--rule-strong: var(--gray-mid)` = #C7C7C7), used for `.btn` (`site.css:87`), `.input` (`:305`), `.badge` (`:198`), `.chip--plain`/`.chip--sub` (`:185-186`), `.seg` (`papers.css:55`).
- Evidence: computed 1.69:1 on white (dark theme uses `--gray` on ink, 3.30:1, fine). In `shots/papers_1440x900_light.png` the search field boundary and the segmented control edges are faint; on a bright display the search box reads as floating placeholder text.
- Fix: add `--control-border: color-mix(in srgb, var(--gray) 85%, var(--ink))` (≈#747474, 4.6:1) and use it for `.input`, `.seg`, `.btn` and `.chip--plain` borders; keep `--rule-strong` for hairlines and the kbd hint.

### 13. Year histogram flattens seven years (minor)

- File: `site/assets/js/taxonomy.js:162-168` (linear scale to `max`, 1 px floor).
- Evidence: `shots/crop_numbers_1440.png`: "≤2016" through 2022 render as identical 1 px dashes although they hold 2 to 32 papers; only 2023 to 2026 have visible bars.
- Fix: `const h = Math.max(b.n ? 3 : 0, Math.round(Math.sqrt(b.n / max) * chartH))` (square-root scale with a 3 px floor), keeping the `<title>` tooltips; or draw the small years as a labelled "<40" band.

### 14. Chronology strip never shows 2024 (minor)

- File: `site/assets/js/stream.js:306-307` (year label only when `isJan(i)`).
- Evidence: CDP label sequence `["Feb","May","Aug","Nov","2025","May",…]`; `shots/stream_1440x900_light.png`. The ledger starts in February 2024, so the first ten columns carry no year.
- Fix: for `i === 0` when not January emit `<text class="chronology__year">${m.slice(0,4)}</text>` beneath or instead of the month label, and keep the month label at `i % 3 === 0`.

### 15. Score digit unexplained on touch (minor)

- File: `site/assets/js/papers.js:488` (`<span class="score" title="score 3, must cite">3</span>`).
- Evidence: `shots/papers_390x844_light.png`: marks row reads "CITED  3  中文  arXiv 2604.03968 ↗"; `title` never shows on touch devices.
- Fix: `<span class="score" aria-label="score 3, must cite" title="…"><span class="visually-hidden">score </span>3</span>`, or render "score 3" in the compact mono.

### 16. Rail is not a single Tab stop (minor)

- File: `site/assets/js/papers.js:339-343` (arrow keys implemented) with no `tabindex="-1"` on non-current rail items or chevrons.
- Evidence: CDP Tab trace on `papers.html`: t1 skip link, t2 masthead title, t3 Papers, t6 theme toggle, t8 rail §1 link, t12 rail §3 link, t24 rail §9 link, t38 "Reports and posts" chip; focusable elements before the first card: 44. `shots/j_tab24.png` (focus ring on §9 in the rail).
- Fix: roving tabindex on `.rail` (only the current or first row at `tabindex="0"`, chevrons `-1`, arrows move focus as already coded), and a second skip link "Skip to results" to `#results-head`.

### 17. Drawer 520 px at exactly 1024 (minor)

- File: `site/assets/css/site.css:339-340` (`@media (max-width: 1023px) .drawer { width:440px }`).
- Evidence: CDP at 1024×768: `{w:520, backdrop:"rgba(0, 0, 0, 0)"}`; `shots/j_drawer_1024.png` shows the drawer covering the card column from x=504 while the rail is still 240 px. DESIGN.md 5.1: "At 1024: rail 240, drawer 440".
- Fix: move the 440 px rule to `@media (max-width: 1439px)` (the same breakpoint that sets the 240 px rail) and keep the scrim rule at 1023.

### 18. Spread begins at 520 px (minor)

- File: `site/assets/css/site.css:79-81` (`.title-block` padding, `.dek` at `--measure-dek` 60ch, 22/32) and `site/index.html:81` (two bound sentences).
- Evidence: CDP `spread top 520.19` at 1440×900 (spec ≈380); `shots/index_1440x900_light.png` shows four TOC rows and two and a half ledger rows above the fold.
- Fix: `--measure-dek: 72ch` (dek wraps to three lines), `.title-block { padding: var(--s4) 0 var(--s5) }`, `.title-block__title { margin-bottom: var(--s3) }`; together about 90 px.

### 19. Mechanism-map keywords clamp mid-word (minor)

- File: `site/assets/js/taxonomy.js:112` (`<p class="mech__keys clamp-2">`), `site/assets/css/site.css:139`.
- Evidence: `shots/crop_mech_light.png`: Constrain "…action interfaces, information…", Observe "…reasoning monitors, probes,…", Steer "…memory selection, self-…"; no `title`.
- Fix: add `title="${esc(KEYWORDS[sec.id])}"` to `.mech__keys`, or allow three lines in the three narrow nodes (`.mech__keys { -webkit-line-clamp: 3 }` with `min-height: 128px`).

## Notes outside the findings

- `stream.html#f=polarity:bad` is not a URL form the stream page understands; it renders the unfiltered ledger (identical capture to `stream.html`). The canonical `stream.html?polarity=bad` works and was reviewed. The papers page does normalise its `#sub=`/`#paper=` legacy forms.
- Every landing ledger row and stream row shows the "New" dot because all 231 items carry `verified_on: 2026-10-17`; this is the specified behaviour until the collector adds later items.
- The headless screenshots at 1440 show the papers main column stopping at 760 px with about 310 px of white on the right; DESIGN.md 5.1 reserves this for the drawer overlay, so it is not reported.
