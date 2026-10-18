# Data review: `site/data/*.json`, the JS that reads them, and the rendered pages

Reviewer lens: data correctness. Date: 2026-10-17. Nothing under `site/` or `overleaf-ai-control/` was modified.

## Method

- Python (`python3 -I`) cross-checks of `site/data/{taxonomy,papers,grey,summaries_zh,stats,stream}.json` against
  `overleaf-ai-control/outline.json`, `research/corpus_full.json`, `research/grey_v2.json`,
  `research/labels_method_style.json`, `research/summaries_zh.json`: counts, ids, titles, labels, `selected`, `also`,
  sort order, URL shape, enumerations, cross-references.
- Code reading of `site/assets/js/{papers,search,stream,taxonomy,common}.js` against `SCHEMA.md`.
- Headless Chrome `--dump-dom --virtual-time-budget=6000 --window-size=1440,900` on
  `papers.html#sub=s5_5` and `stream.html` (server already running on :8765, reused).
- A CDP script (Node 26 built-in WebSocket, `Page.navigate`, `Runtime.evaluate`) that scrolls each page until the
  card count stops growing, opens hashes, presses Back, and collects console errors. Scratch files live in the
  session scratchpad, not in the repo.

## Summary

| # | Severity | Where | One line |
|---|---|---|---|
| 1 | blocker | `site/data/taxonomy.json`, `papers.json` | Built 12:04 from an `outline.json`/`corpus_full.json` that the paper replaced at 15:20: 7 subsection titles, the §2 purpose, the thesis, 40 papers' `primary`, 23 papers' `also` and 2 bullets no longer match the paper |
| 2 | major | `site/data/stream.json` | 9 reward-hacking items are filed under `s2_3`, which the paper now calls "Insider Threats" (human insiders); a rebuild silently misfiles them |
| 3 | major | `pipeline/classify.py` | Collector rules hard-code the old §2 semantics (`s2_3` = reward hacking) so every future item is misfiled the same way |
| 4 | major | `site/data/grey.json` | 14 cited classics have `url: ""`; cards and drawers render `<a href="">source</a>` that reloads the page |
| 5 | major | `site/data/grey.json`, `papers.json` | 6 bib keys exist in both files; 3 arXiv papers appear twice in 3.5 with contradictory "Cited" status; 5 "reports and posts" are arXiv papers |
| 6 | major | `site/data/stats.json` | `cited: 240` double-counts one document (two bib keys, one URL); BRIEF says 239; two "Cited" cards for one report |
| 7 | minor | `site/data/grey.json` | 3 prompt-injection vendor posts are shelved under 2.3 "Reward Hacking and Harness Tampering" |
| 8 | minor | `site/data/grey.json` | `confidence: "existing bib entry"` (19 items) is rendered as badge text "Report · existing bib entry" |
| 9 | minor | `site/data/papers.json` | 10 titles carry raw LaTeX math (`$τ$-bench`, `$N$`, `$^{\circ}$`, `E$^2$AT`) |
| 10 | minor | `site/assets/js/papers.js` | 中文 badge and "Chinese notes" count ignore 50 grey notes until the notes file loads, then count 245 for 239 notes |
| 11 | minor | `site/data/summaries_zh.json` | `guo2026personalization` note says `s1_1`; the paper card sits in 2.2 |
| 12 | minor | `site/data/stream.json` | 2 summaries are 4 and 6 sentences against a two-sentence contract |

## What passed (so nobody re-checks it)

- `papers.json`: 1,788 items, keys and arXiv ids unique and identical to `corpus_full.json`; every `url` is
  `https://arxiv.org/abs/<id>` with a well-formed id; `year` is an integer; `section` matches `primary`; every
  `primary` and `also.sid` exists in `taxonomy.json`; no `also` equals `primary`; `label` equals
  `labels_method_style[key]` for all 1,788; `has_zh` equals membership in `summaries_zh.json`; file order follows the
  SCHEMA sort (title compared case-insensitively).
- `taxonomy.json`: 11 sections, 56 subsections, numbers `k.j` positional; `counts.{primary,selected,cross,grey}` equal
  recounts from `papers.json`/`grey.json` for all 56; colours and operation ids match BRIEF.
- `stats.json`: `papers`, `grey`, `years`, `per_section`, `stream_items`, `subsections`, `sections` all recomputed and equal.
- `summaries_zh.json`: 239 keys, same set as the source; all ten Chinese fields mapped to the SCHEMA names with
  identical values; every selected paper has a note.
- `stream.json`: 231 items, ids unique and `YYYY-MM-DD-<slug>` with the slug at most 80 chars, sorted by date
  descending, no duplicate `url` across `url` and `also_urls`, all URLs `http(s)://host/...`, every `kind`,
  `polarity`, `failure_sources`, `requirements`, `operations`, `domain`, `evidence`, `date_precision` inside the
  enumerations, 1 to 4 `subsections` each and all resolve, all 986 `related_papers` resolve to `papers.json` keys,
  all `verified: true` with a note, no future dates.
- Rendering (CDP, after scrolling to the end): `papers.html#sub=s5_5` normalises to `#s5_5` and renders 29 cards
  (18 primary + 11 cross, equal to the data); `#s8` renders 428 (356 + 68 cross + 4 reports, equal to the data);
  `stream.html` renders 231 rows, sentinel hidden at the end; `#item/<id>` for the 230th item renders, expands and
  scrolls to it with related-paper labels resolved; `#2025-07` scrolls to the month head; `?sub=s2&source=misalignment&polarity=bad`
  gives 23 (equal to the data); `?sub=s2_3` 9; `?paper=khan2026token` 5 (4 related + 1 via subsection); `?q=replit` 1.
- Routing: `#paper/<key>` opens the drawer on load; Back from a card opened inside `#s5_5` closes the drawer and
  restores `#s5_5`; drawer Next/Previous step through the visible list; unknown keys show "no paper with the key".
- Search: author surname (`Greenblatt`: 8 papers, 23 reports, 42 cross), label words (`untrusted monitor`: 12,
  equal to a data grep), arXiv id (`2312.06942`: 1). `#q=` is normalised to `?q=`.
- Console: zero errors from the site's own code on index, papers, stream, about (with `--disable-extensions`; the
  one exception seen earlier came from a Chrome extension content script, not the site).
- Field names in `papers.js`, `stream.js`, `common.js`, `taxonomy.js` match SCHEMA.md; section numbers come from
  the data, not from array indices.

## Findings

### 1. blocker. `site/data/taxonomy.json` (and `papers.json`): built from a superseded `outline.json`

- Files under `site/data/` are dated 2026-10-17 12:04:29. `overleaf-ai-control/outline.json` and
  `research/corpus_full.json` are dated 15:20:46 the same day, and the paper's own TeX
  (`content/2_how_agents_fail.tex`, `content/11_open_problems_and_outlook.tex`) now reads
  `\subsection{Benign Failures}`, `{Malicious Attacks}`, `{Insider Threats}`, `{The Model as Insider}` and, in §11,
  `{Benign Failures}`, `{Malicious Attacks}`, `{Insider Threats}`.
- `taxonomy.json` still says: `s2_1 Compounding Mistakes`, `s2_2 Prompt Injection and Memory Poisoning`,
  `s2_3 Reward Hacking and Harness Tampering`, `s2_4 Deception and Loss of Control`, `s11_1 Mistakes`,
  `s11_2 Manipulation`, `s11_3 Misalignment`. The §2 `purpose` ("four failure families ...") and `thesis`
  ("they make mistakes, they can be redirected ...") are the old paragraphs; the outline's are "three tiers of the
  attack side" and "On the attack side the survey distinguishes three tiers ...". `s9_3` and `s11_3` each lack one
  new bullet (the insider red-team bullet; the human-insider open problem).
- `papers.json`: 40 papers have `primary: s2_3` where `corpus_full.json` now says `s2_4` (the reward-hacking
  cluster moved into "The Model as Insider"); 23 papers' `also` differ (23 cross-references to `s2_3` removed,
  17 to `s2_4` added); 11 `reason` strings differ by whitespace only. In the new corpus no arXiv paper has `primary`
  or `also` `s2_3`, so a plain rebuild yields a 2.3 with 0 papers and only the 3 grey items of finding 7.
- Evidence: `stat -f '%Sm'` on both trees; `grep -rhoE '\\subsection\{[^}]+\}' overleaf-ai-control/content/*.tex`;
  scratch `check1.py`/`check5.py` (title, bullet, purpose, primary and also diffs).
- Consequence: a reader with the PDF open sees a different §2 and §11 on the site; the stream's subsection
  select, the rail, the About table and every card chip for 2.1 to 2.4 and 11.1 to 11.3 carry titles the paper no
  longer uses.
- Fix: re-run `pipeline/build_data.py` against the current clone and re-check with the same scripts; then apply
  findings 2 and 3 before publishing. Add the source `generated`/mtime of `outline.json` and `corpus_full.json` to
  `stats.json` so the footer can show "data from paper build of <date>" and a CI check can fail when the clone is
  newer than `site/data/`.

### 2. major. `site/data/stream.json`: 9 items rely on the old meaning of `s2_3`

- Items whose `subsections` include `s2_3`: `2026-10-17-openai-misalignment-reports-a-test-model-forged-tokens-on-a`,
  `2026-10-09-anthropic-discloses-claude-models-submitting-a-false-police-tip-...`,
  `2026-06-26-metr-finds-gpt-5-6-sol-s-detected-cheating-rate-...`, `2025-11-21-anthropic-reward-hacking-...`,
  `2025-06-05-metr-recent-frontier-models-are-reward-hacking-...`, `2025-04-16-metr-s-pre-deployment-evaluation-found-o3-reward-hacking-...`,
  `2025-02-18-palisade-research-shows-o1-preview-and-deepseek-r1-hack-a-chess-...`,
  `2024-09-12-openai-o1-system-card-o1-preview-used-an-exposed-docker-api-...`,
  `2024-08-13-sakana-s-ai-scientist-edited-its-own-code-to-extend-its-timeout-and`. All are model reward hacking,
  harness tampering or sandbagging; `failure_sources` is `misalignment` on all nine. Under the paper's current 2.3
  (human insiders with partial access) they are misfiled; the matching new home is `s2_4 The Model as Insider`.
- The 38 items under `s2_4` ("Deception and Loss of Control") still fit "The Model as Insider" but should be
  spot-checked; `s11_1`, `s11_2`, `s11_3` (2, 1, 1 items) keep their meaning.
- Evidence: scratch `check6.py` listing; `stream.html?sub=s2_3` shows "9 of 231 items match" under the label
  "2.3 Reward Hacking and Harness Tampering".
- Fix: move `s2_3` to `s2_4` in these nine items (keep order "most specific first"); record the taxonomy version the
  classification was made against (e.g. a top-level `taxonomy_generated` in `stream.json`, extend SCHEMA.md) so a
  mismatch with `taxonomy.json.generated` is visible to the collector and to a test.

### 3. major. `pipeline/classify.py`: rules encode the superseded §2

- `FALLBACK_TAXONOMY` (lines 80 to 83) lists "Compounding Mistakes", "Prompt Injection and Memory Poisoning",
  "Reward Hacking and Harness Tampering", "Deception and Loss of Control".
- `SUBSECTION_RULES` (lines 293 to 298) send `reward hack|harness|specification gaming|tamper|sandbagg` to `s2_3`
  and `decepti|scheming|...|sabotag` to `s2_4`; `fs_default` (line 479) maps `misalignment` to `s2_4`.
- Once `taxonomy.json` is rebuilt, the LLM prompt (built from `taxonomy.json`, line 35 and `load_taxonomy`) will
  describe `s2_3` as "Insider Threats" while the regex fallback keeps filing reward hacking there. Every collector
  run then repeats finding 2.
- Fix: retitle the fallback; change the `s2_3` rule to insider vocabulary (`insider`, `employee`, `contractor`,
  `credential`, `weights`, `fine-tun`, `data poison` by a person with access) and send the reward-hacking patterns to
  `s2_4`; add a unit test in `pipeline/tests/test_collector.py` that asserts the rule ids against the titles in
  `taxonomy.json` (`pytest` is not installed locally; the suite could not be run here).

### 4. major. `site/data/grey.json`: 14 cited items have an empty `url`

- Keys: `shavit2023practices`, `orseau2016safely`, `soares2015corrigibility`, `ligatti2005edit`,
  `avizienis2004basic`, `sabelfeld2003language`, `schneider2000enforceable`, `axelsson2000base`,
  `hardy1988confused`, `denning1987intrusion`, `denning1976lattice`, `saltzer1975protection`, `lampson1973note`,
  `anderson1972computer` (11 in `s3_5`, 1 in `s2_2`, 2 in `s2_4`). All come from `corpus_full.grey` with `url: ""`
  and `confidence: "existing bib entry"`; `build_data.py` only logs them as an anomaly.
- Rendered: `papers.html#s3_5` has 15 report cards of which 11 carry `<a class="card__ext ext" href="">source</a>`
  (`papers.js` 493 to 495, `hostOf("")` falls back to "source"); the drawer for `#grey/saltzer1975protection`
  shows a "Source" button with `href=""` (`papers.js` 698 to 700). Clicking either reloads `papers.html`.
- Fix: in `build_data.py` `_grey_record`/`build_grey` (lines 397 to 530) supply DOI or publisher URLs for these
  well-known papers (all have DOIs or stable publisher pages) or emit `url: null`; in `papers.js` omit the external
  link and button when `item.url` is empty and show the venue instead. SCHEMA.md should say `url` may be null for
  grey items or must be non-empty; today it implies always present.

### 5. major. `grey.json` and `papers.json`: one work, two entities, contradictory badges

- Six bib keys appear in both files: `perez2022red`, `hubinger2019risks`, `hadfieldmenell2016off` (grey `url` is
  the same arXiv abstract as the paper; grey `selected: true`, paper `selected: false`; both have `primary: s3_5`),
  `guo2026personalization` (grey = ACL 2026 page, `s1_1`, cited; paper = arXiv 2601.17887, `s2_2`, not cited),
  `benton2024sabotage` (grey = Anthropic news post, `s2_5`, not cited; paper = arXiv 2410.21514, `s9_3`, cited),
  `kaufman2025basharena` (grey = Redwood blog post about the paper; acceptable as a distinct document).
- Two further grey items are arXiv papers absent from `papers.json`: `mitchell2026ai` (2608.23642),
  `skaf2025steganographic` (2506.01926). BRIEF defines grey as non-arXiv.
- Rendered: `#paper/perez2022red` opens "LM-vs-LM Red Teaming · 2022 · arXiv 2202.03286 · score 3" with no Cited
  badge and "2 of 39" in 3.5; `#grey/perez2022red` opens the same title as "Report · existing bib entry · Cited",
  "13 of 39" in the same subsection. The reader sees the work twice and is told both that it is and is not cited.
- Knock-on: `hasZh` matches both cards, so the "Chinese notes" chip counts 245 while About says 239 notes
  (finding 10), and `stream.html?paper=<key>` and the drawer's "In the stream" list treat the two as one.
- Evidence: scratch `check5.py` "GREY KEY COLLISIONS" and "GREY arXiv items"; CDP `hash_paper_perez2022red` vs
  `hash_grey_perez2022red`.
- Fix (`build_data.py` `build_grey`, lines 418 to 530): when a corpus grey item resolves to an arXiv id that is in
  `papers.json`, drop the grey record and set the paper's `selected: true` (and add the grey `sid` to `also` when it
  differs); when it is the same work at another venue (`guo2026personalization`, `benton2024sabotage`) merge into the
  paper record (venue note, extra URL) rather than emitting a second entity; for arXiv items not in the corpus
  (`mitchell2026ai`, `skaf2025steganographic`) either add them to `papers.json` or keep them grey with an explicit
  `venue: "arXiv"`, but never both. Make the existing "keys also present in papers.json" anomaly a hard failure.

### 6. major. `site/data/stats.json`: `cited: 240` counts one document twice

- `corpus_full.grey` holds `bowman2025sabotagerisk` ("Anthropic's Summer 2025 Pilot Sabotage Risk Report",
  `s2_5`) and `bowman2025anthropic` ("Anthropic's Pilot Sabotage Risk Report", `s10_3`) with the identical URL
  `https://alignment.anthropic.com/2025/sabotage-risk-report/`. `build_data.py` keeps both on purpose (line 463
  logs "kept as separate bib keys") and `build_stats` (line 612) sums `selected` over both lists:
  191 papers + 49 grey = 240. BRIEF.md says 239 are cited in the PDF; 240 minus this duplicate is 239.
- Rendered: index.html statline, about.html and README.md all say "240 cited in the PDF"; papers.html shows two
  "Cited" report cards for the same URL (2.5 and 10.3).
- Fix: dedupe `corpus.grey` by normalised URL before counting (keep one key, carry the second `sid` as a cross
  reference), or fix the duplicate entry in `references.bib` upstream; make `stats.cited` the count of distinct
  cited documents and let `about.html`'s sentence read from it. SCHEMA.md line 102 can state that `selected` grey
  items are unique by URL.

### 7. minor. `site/data/grey.json`: three prompt-injection posts shelved under 2.3

- `anthropic2025promptinjection`, `openai2025promptinjections`, `google2025layereddefense` come from
  `grey_v2.json` with `sid: s2_3` and are the only grey items in `s2_3`. Under the current site title ("Reward
  Hacking and Harness Tampering") and under the paper's new one ("Insider Threats") they are misplaced; they belong
  to `s2_2` (Malicious Attacks) or the defence subsections (`s4_4`, `s5_2`).
- Fix: correct `sid` upstream in `grey_v2.json` or add an explicit override table in `build_data.py` next to
  `SID_REMAP` (line 117) with the anomaly logged.

### 8. minor. `site/data/grey.json`: `confidence: "existing bib entry"` surfaces as UI text

- 19 items carry this value (and 2 carry `likely`); SCHEMA.md shows only `verified`. `papers.js` line 490 and 703
  print any non-`verified` value: cards and drawers read "Report · existing bib entry", which tells the reader
  nothing about verification.
- Fix: in `build_data.py` map provenance notes to a closed set (`verified | likely | unverified`) and keep the
  provenance in a separate field if wanted; list the set in SCHEMA.md; `papers.js` shows a badge only for
  `likely`/`unverified`.

### 9. minor. `site/data/papers.json`: raw LaTeX math in 10 titles

- `yao2024bench` "$τ$-bench", `barres20252` "$τ^2$-Bench", `narasimhan2026rec` "$τ$-Rec", `zavattari2026one`
  "One Human, $N$ Agents", `lab2025safework` "AI-45$^{\circ}$ Law", `lu2025e` "E$^2$AT", and four more flagged by
  the `\\[a-zA-Z]+|\{|\}|\$` scan. `build_data.py` has `strip_latex` (line 159) but `build_papers` stores the raw
  title (line 363). `esc()` in the front end escapes HTML only, so the dollars render literally on cards, in the
  drawer and in `document.title`.
- Fix: run a math-aware cleanup on titles and labels in `build_papers` (`$x$` to `x`, `^{\circ}` to `°`, `^2` to `²`).

### 10. minor. `site/assets/js/papers.js`: Chinese-notes badge and count exclude grey until the notes file loads

- `hasZh("grey", g)` (line 55) is false while `S.zhKeys` is null, so on first paint no report card shows the 中文
  badge (CDP: 0 `.card--report .badge--zh` on the whole-corpus view although 50 grey keys have notes) and the
  "Chinese notes" chip (lines 371, 377) counts 195. After the file loads the chip says 245 (195 papers + 50 grey,
  six of them the duplicated keys of finding 5) against 239 notes on About.
- Fix: add `has_zh` to `grey.json` (extend SCHEMA.md) and use it like `papers.has_zh`; resolve finding 5 so a note is
  claimed by exactly one card.

### 11. minor. `site/data/summaries_zh.json`: `guo2026personalization.sid` is `s1_1`, the paper card is in `s2_2`

- The note was written for the grey (ACL) placement in 1.1; the arXiv card has `primary: s2_2`. The drawer for
  `#paper/guo2026personalization` shows the crumb "§2 › 2.2 Prompt Injection and Memory Poisoning" and the notes
  footer "s1_1" (`papers.js` line 690), and the 与小节关系 paragraph discusses 1.1.
- Fix: falls out of the merge in finding 5; until then show the paper's own `primary` in the notes footer.

### 12. minor. `site/data/stream.json`: two summaries break the two-sentence contract

- `2025-06-11-court-certifies-age-bias-collective-action-over-workday-s-ai` has 6 sentences (about 1,000 chars);
  `2025-09-29-openai-launches-instant-checkout-so-chatgpt-can-buy-from-etsy-and` has 4. SCHEMA.md asks for "Two
  factual sentences". The collapsed row clamps to two lines, but the expanded row and the index ledger show the wall.
- Fix: trim both to two sentences; add a length check to `pipeline/tests/test_collector.py`.

## Notes that are not findings

- `grey_v2.json` carries 8 entries with subsection ids that do not exist (`s2_6`, `s2_7`, `s2_8`, `s6_6`);
  `build_data.py` remaps them (`SID_REMAP`, line 117) and the mappings look right. Fix upstream when convenient.
- 15 `good` items carry non-empty `failure_sources` (safety features and policies about a failure source). This
  reads as intended ("the failure the control addresses"); SCHEMA.md's "empty for items that are not about a
  failure" could say so explicitly.
- `stream.generated` equals the seed date, so the header reads "Live · updated N h ago" until the first collector
  run; after 7 days it will read "Collector stalled since 17 Oct 2026", which is accurate.
