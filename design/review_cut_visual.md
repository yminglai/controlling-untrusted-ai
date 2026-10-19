# Visual review after the cut (2026-10-19)

Reviewer: visual lens. Site served from `site/` at http://localhost:8765/. No site file was edited.

## Method

- Headless Chrome 1440x900 and 1440x3000 in light and dark (`?theme=`), and a true 390-wide viewport through a
  390 px iframe wrapper centred in a 500 px window, cropped with `sips` (390x844 and 390x2400), for
  `index.html`, `papers.html`, `papers.html#sub=s5_2`, `papers.html#paper=greenblatt2024alignment`, `stream.html`,
  `stream.html#f=polarity:bad`, `404.html`. Extra captures: `stream.html?polarity=bad` (the canonical filter form),
  `papers.html#sub=s1_3` (empty subsection), `papers.html#s3` (section view), the drawer at a real 500 px window and
  with `--force-prefers-reduced-motion`. All captures are in `design/shots/rcv_*.png`.
- Console: `--enable-logging=stderr --v=0 --dump-dom` on the seven URLs plus a nested missing path
  (`/nope/deep/path.html`): zero `CONSOLE` lines on every page.
- Stale-label grep over `site/*.html`, `site/assets/js/*.js`, `site/assets/css/*.css` for Observe, Verify, Mistakes,
  Manipulation, Misalignment, About, mechanism map, Chinese/中文/zh: nothing reader-facing. The only traces are a CSS
  comment (`tokens.css:40`, "About essay 18/30") and the unreferenced `fig2_mechanism_map*` images (finding 11). The
  one stale term that does reach readers is "Malicious" inside the Section 2 purpose text (finding 1).
- Not a finding: in the iframe captures the drawer appears shifted 40 to 100 px to the right at 390 wide
  (`rcv_papers_greenblatt_390x844_light.png`). That is the slide-in transition caught mid-flight under virtual time;
  at a real 500 px window (`rcv_papers_greenblatt_500x844_light.png`) and with reduced motion forced
  (`rcv_papers_greenblatt_390x844_light_rm.png`) the drawer fills the viewport and the close button is fully visible.

## Findings

| # | Severity | File | Summary |
|---|---|---|---|
| 1 | major | site/assets/js/papers.js:463 | Section heads print the outline's writer notes (`purpose`) as reader prose |
| 2 | major | site/assets/js/papers.js:499, :728 | "Why here" / "Why it is here" expose pipeline notes (Critic (sweep), Named in the section plan, Seed) |
| 3 | minor | site/assets/js/stream.js:61 | `#f=polarity:bad` is not understood; the page renders unfiltered |
| 4 | minor | site/assets/js/papers.js:252, :470 | Two consecutive count lines say the same thing on every subsection and section view |
| 5 | minor | site/assets/js/papers.js:386 | "Reports and posts" chip is drawn pressed by default and reads as an active filter |
| 6 | minor | site/assets/js/common.js:206 | Masthead Stream dot is green while the stream page says amber "Collector last ran 2 days ago" |
| 7 | minor | site/stream.html:77 | The stream dek is process explanation, not content |
| 8 | minor | site/index.html:75 | Disabled "Read the Paper" pseudo-button repeats "arXiv link to come" |
| 9 | minor | site/assets/js/papers.js:323 | On phones the active section chip can sit under the strip's right fade |
| 10 | minor | site/assets/js/papers.js:683 | Drawer meta prints the internal "reading list #N" rank |
| 11 | minor | site/assets/img/ | 3 MB of unreferenced figure images and the `og.html` generator ship with the site |
| 12 | minor | site/assets/css/site.css | On short pages the colophon floats mid-screen (404 at 1440x900) |
| 13 | minor | site/assets/css/stream.css | At 390 wide the chip rows outweigh the text of every stream item |
| 14 | minor | site/stream.html:83 | "Submit an item" appears twice on the stream page (header and colophon) |

### 1. major · site/assets/js/papers.js:463 · section purpose text is writer-facing

Every section head renders `sec.purpose` from `taxonomy.json`, which is the outline's note to the section writer, not
paper prose. Section 1: "States the problem (...), says who the survey is for and how to read it, and positions it
against the adjacent reviews." Section 4: "State at the outset that the intent-independent defences surveyed here
(...) pass the two-level test by construction". Section 9: "Note that no benchmark or control setting yet covers the
human-insider tier". Section 2 still names the middle tier "Malicious:" while the taxonomy chip says "External". On
phones the Section 1 paragraph is 230 px of this before the first card.

Evidence: `design/shots/rcv_papers_1440x900_light.png` (§1), `design/shots/rcv_papers_s3_1440x1600_light.png` (§3),
`design/shots/rcv_papers_390x844_light.png`; `python3 -c "import json;[print(s['id'],s['purpose']) for s in json.load(open('site/data/taxonomy.json'))['sections']]"`.

Fix: delete the `${sec.purpose ? ... : ""}` line in `renderSectionHead` (papers.js:463) and the
`.section-head__purpose` rule in `papers.css`. If the field should go for good, stop emitting `purpose` in
`pipeline/build_data.py` and remove it from SCHEMA.md.

### 2. major · site/assets/js/papers.js:499 and :728 · "Why here" shows pipeline notes

Cards without a `one_line` (149 papers) print `reason` behind "Why here:", and the drawer prints it for every paper
under "Why it is here". The field is the corpus pipeline's placement note: 113 start "Critic (sweep): critic
(title-resolved): ...", 104 are exactly "Named in the section plan", 62 start "Seed;", 76 mention "sweep"; others read
"Requested; ..." or "Moved here by the critic and adjudication round: ...".

Evidence: `design/shots/rcv_papers_1440x3000_light.png` (cards "Against Full Autonomy" and "AI Deception Survey":
"Why here: Named in the section plan"), `design/shots/rcv_papers_greenblatt_1440x900_light.png` ("WHY IT IS HERE:
Seed; canonical alignment-faking demonstration"); counts from
`python3 -c "import json,collections;p=json.load(open('site/data/papers.json'));print(collections.Counter(r['reason'].split(':')[0] for r in p if r['reason'].startswith(('Critic','Named','Seed'))))"`.

Fix: remove the `card__line--why` branch (papers.js:499; an empty summary is better than a pipeline note) and the
`drawer__why` section (papers.js:728). Keep `reason` in the search index if wanted, but never render it.

### 3. minor · site/assets/js/stream.js:61 · `#f=polarity:bad` renders the unfiltered ledger

`parseState()` reads filters only from query keys (`?polarity=bad`). The hash form in the brief's URL list is ignored
silently: 231 items, no active chip, good items visible. `papers.js` does normalise its legacy `#sub=` and `#paper=`
forms, so the two pages disagree on what a hash may carry.

Evidence: `design/shots/rcv_stream_bad_1440x900_light.png` (identical to `rcv_stream_1440x900_light.png`) versus
`design/shots/rcv_stream_qbad_1440x900_light.png` (97 of 231 items, "Bad" active chip).

Fix: in `parseState()` map `#f=key:value[,key:value]` onto the query keys before reading them (mirroring the
`#sub=`/`#paper=` normalisation in papers.js:55-66), then `writeState()` the canonical URL; or make sure no link
anywhere emits the `#f=` form and drop it from the brief.

### 4. minor · site/assets/js/papers.js:252 and :470 · duplicate count lines

The results head and the subsection head sit 50 px apart and repeat each other: "173 papers in 5.2 Automated
Monitors · 20 cited in the PDF · 2 reports" then "173 papers · 20 cited in the PDF · 33 cross-referenced here · 2
reports". On an empty subsection it is "0 papers ... 0 reports" twice.

Evidence: `design/shots/rcv_papers_s5_2_1440x900_light.png`, `design/shots/rcv_papers_s1_3_1440x900_light.png`,
`design/shots/rcv_papers_s3_1440x1600_light.png` (section view: "54 papers in §3 Preliminaries ..." above the head).

Fix: hide `#results-head` when the route is a single section or subsection with no filter or query active (keep it for
search and filtered views where it is the only summary), or drop the count line from the sub-head.

### 5. minor · site/assets/js/papers.js:386 · "Reports and posts" chip pressed by default

The include-grey toggle defaults to on and is rendered `aria-pressed="true"` with the dark `is-on` fill, in a row of
filter chips that are all off. It reads as an active filter on an unfiltered page.

Evidence: `design/shots/rcv_papers_1440x900_light.png`, `design/shots/rcv_papers_s5_2_1440x900_dark.png`.

Fix: render the chip unpressed in its default state and pressed only once the user changes it (invert `on` for this
chip: `on: !f.grey`, label "Without reports and posts"), or move the toggle next to the density buttons.

### 6. minor · site/assets/js/common.js:206 · masthead dot and stream status disagree

The nav dot is green whenever `stream_updated` is within 7 days ("updated this week"); the stream page's own
indicator turns amber after 48 hours ("Collector last ran 2 days ago", `stream.js:175`). Today both show at once.

Evidence: `design/shots/rcv_stream_1440x900_light.png` (green dot top right, amber status line).

Fix: cut the dot, or colour it from the same thresholds as `setLive()` (green under 48 h, amber to 7 days, none
beyond).

### 7. minor · site/stream.html:77 · stream dek is explanation

"Collected from feeds and reader submissions, classified into the paper's structure, checked at the source before
publication." describes the pipeline. The landing page introduces the stream with a count line only.

Evidence: `design/shots/rcv_stream_1440x900_light.png`, `design/shots/rcv_stream_390x844_light.png`.

Fix: delete `<p class="stream__dek">` and its CSS rule; the status line and the item count carry the page.

### 8. minor · site/index.html:75 · disabled "Read the Paper" button

A greyed `<a>` without `href` (`aria-disabled`, `role="link"`) sits first in the action row while the status line
above already says "arXiv link to come". On phones it takes the first slot and pushes "Open the Stream" to a second
row.

Evidence: `design/shots/rcv_index_1440x900_light.png`, `design/shots/rcv_index_390x844_light.png`.

Fix: remove the anchor until the arXiv link exists; add it back with a real `href` then.

### 9. minor · site/assets/js/papers.js:323 · active chip under the strip fade

The strip scrolls the active section chip into view only when it is fully outside the strip box; the mask
(`papers.css:200`) fades the last 28 px, so a chip that ends within those 28 px stays faded. Seen on 5.2 at 390 wide
where §5, the active chip, is half transparent.

Evidence: `design/shots/rcv_papers_s5_2_390x2400_dark.png` (§5 faded) versus
`design/shots/rcv_papers_s5_2_390x844_light.png` and `design/shots/rcv_papers_s5_2_500x844_light.png` (§5 clear).

Fix: `if (cr.left < sr.left || cr.right > sr.right - 28)` in the scroll test, or `scroll-padding-inline-end: 28px` on
`.strip__chips` and scroll the chip with `scrollIntoView({ inline: "center" })`.

### 10. minor · site/assets/js/papers.js:683 · "reading list #N" in the drawer meta

The mono meta line prints `reading list #1` for the 788 papers that carry `reading_rank`, an internal ordering of the
writer's reading list.

Evidence: `design/shots/rcv_papers_greenblatt_1440x900_light.png` ("2024 · arXiv 2412.14093 · score 3 · cited in the
PDF · reading list #1").

Fix: drop the `reading_rank` part from the meta line; the rank already drives the survey sort order.

### 11. minor · site/assets/img/ · unreferenced assets shipped

`fig1_why_control.jpg` (368 K), `fig1_why_control_1000.jpg` (121 K), `fig1_why_control_web.jpg` (198 K),
`fig2_mechanism_map.jpeg` (2.2 M), `fig2_mechanism_map_web.jpg` (292 K) and `og.html` (the og-image generator) are in
`site/assets/img/` and no page, script or stylesheet references them.

Evidence: `grep -rn "fig1_\|fig2_\|og.html" site/*.html site/assets/js/*.js site/assets/css/*.css` returns nothing;
`ls -la site/assets/img`.

Fix: delete the six files; keep `favicon.svg` and `og.png`. Move `og.html` under `design/` if the generator is wanted.

### 12. minor · site/assets/css/site.css · colophon floats on short pages

On the 404 page at 1440x900 the colophon sits at y 605 with 300 px of empty page below it.

Evidence: `design/shots/rcv_404_1440x900_light.png`, `design/shots/rcv_404_1440x900_dark.png`.

Fix: `body { min-height: 100dvh; display: flex; flex-direction: column; } main { flex: 1 0 auto; }` in site.css.

### 13. minor · site/assets/css/stream.css · chip rows dominate items on phones

At 390 wide each ledger item carries three to five rows of 36 px chips (tier, operation, requirement, subsection), so a
collapsed item is about 350 px tall and the chips outweigh the title and summary.

Evidence: `design/shots/rcv_stream_390x2400_dark.png`, `design/shots/rcv_stream_bad_390x2400_light.png`.

Fix: at `max-width: 767px` show only the tier and subsection chips in the collapsed row and reveal operation and
requirement chips in the expanded state (`.ledger__row:not(.is-expanded) .chip[data-op], ... [data-req] { display: none }`).

### 14. minor · site/stream.html:83 · "Submit an item" twice

The stream header has a "Submit an item" button and the colophon on the same page repeats the link.

Evidence: `design/shots/rcv_stream_1440x3000_light.png` (header button at y 275, colophon link at the foot).

Fix: keep the colophon link (it is on every page) and drop the header `.stream__actions` block.

## Checked and clean

- Console: 0 messages on index, papers (3 routes), stream (2 routes), 404, nested missing path.
- Masthead and colophon are identical on all four pages; `aria-current` underline on Papers and Stream is correct;
  no About link; GitHub link moves into the Menu sheet on phones.
- Empty subsections (1.3, 1.4, 3.3) render the head with an italic empty state and a "Browse the whole corpus" button;
  no empty boxes.
- Dark theme: no inverted or missing colours on any page; section bar, polarity bar, chips and marks keep their
  identities. Amber `live--stale` label is 4.8:1 on white and well above AA on dark.
- Landing at 390: title, dek, two spreads and the short ledger all fit; no horizontal overflow.
- 404 at 390: fits, buttons wrap cleanly.
