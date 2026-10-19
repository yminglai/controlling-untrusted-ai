# Review, data lens: 2026-10-19

Scope: `site/data/*.json` against `overleaf-ai-control/outline.json` and `research/corpus_full.json`;
`papers.js`, `stream.js`, `taxonomy.js`, `common.js` for stale vocabulary; the three pipeline tests;
headless Chrome on `papers.html#sub=s5_2` and `stream.html`. No site file was edited.

## Findings

### 1. CRITICAL: the whole of `site/data` encodes a paper structure that no longer exists

File: `site/data/taxonomy.json` (and with it `papers.json`, `stats.json`, `stream.json`, `stream_recent.json`).

Summary: the site was built at 01:27:58; `outline.json` and `research/corpus_full.json` were rewritten at
01:29:53. The paper now has 10 sections and 29 subsections; the site carries 11 and 36.

Evidence (python3 cross-check):

- Parts now: Foundations (1-3), System-Level Control (4-6), Model-Level Control (7), Evaluation and
  Assurance (8-10). Site: Model-Level Control (7, 8), "Evaluation, Deployment, and Outlook" (9-11).
- Section titles differ from §7 on: 7 Model-Level Methods (7.1 Inference-Time Steering, 7.2 Training-Time
  Methods); 8 Evaluation Methodology (Benchmarks, Control Evaluations, Model Auditing); 9 Composition and
  Assurance (Reference Architectures, Safety Cases); 10 Outlook (Open Problems, Conclusion).
- §2 has 3 subsections (no 2.4 Multi-Agent Failures); §5 has 3 (no 5.1 Observability; 5.1 is now
  Automated Monitors).
- Seven site ids have no counterpart: `s2_4, s5_4, s7_3, s9_3, s10_3, s11_1, s11_2`.
- Primary counts disagree in 19 of 36 subsections (e.g. `s5_1` site 24 vs corpus 197; `s7_2` 32 vs 356;
  `s8_1` 250 vs 137). 1,158 of 1,788 papers carry a different `primary` in the current corpus; 4 differ in
  `selected`.
- `pipeline/tests/test_build_data.py` stops at its first assertion: "the paper clone is newer than
  site/data: run python3 pipeline/build_data.py".
- 224 of 231 stream items cite a subsection id whose meaning changed (`s5_*` and later, or a removed id).

Fix: rebuild from the 19 October 01:29 outline, but only after findings 2 and 3; a plain
`python3 pipeline/build_data.py` today produces wrong operations and orphan ids.

### 2. CRITICAL: `build_data.py` keys operations and colours by section number

File: `pipeline/build_data.py`, `SECTION_META` (lines 53-65), used in `build_sections()` (line 448).

Summary: the number → (operation, slug, colour) table is for 11 sections; on the 10-section outline a
rebuild mislabels four sections.

Evidence: with the current table, §7 Model-Level Methods becomes `steer`/teal and `train` disappears
from `operations`; §8 Evaluation Methodology becomes `train`/periwinkle; §9 Composition and Assurance
becomes `evaluate`/forest; §10 Outlook becomes `deploy`/purple (a control operation with a lever). The 22
stream items tagged `train` would then point at no section; `evaluate` chips would link to Composition
and Assurance, `deploy` chips to Outlook. `test_build_data.py` would then fail on `N_SECTIONS,
N_SUBSECTIONS = 11, 36` (line 28), `OPERATION_IDS` (line 74) and the part titles (lines 80-81), so the
error is caught but not prevented.

Fix: stop keying by number. Key `SECTION_META` by the outline's section title (or a slug of it) and
decide the §7 operation once: either one operation for Model-Level Methods or `steer` and `train` both
mapped to `s7` (the stream and `OP_LABELS` keep both ids). Then §8 → `evaluate`, §9 → `deploy`,
§10 → none. Update the test constants to 10/29, the operation list, and the part titles
`["Foundations", "System-Level Control", "Model-Level Control", "Evaluation and Assurance"]`.

### 3. HIGH: the 56 → 36 id map now points at ids that do not exist; no 36 → 29 map

File: `pipeline/build_data.py` `SID_MAP_2026_10_17` (lines 123-135), `GREY_V2_STRUCTURE`, `resolve_sid()`;
`pipeline/remap_stream.py`.

Summary: everything that still arrives on the 17 October ids (`research/grey_v2.json`, 155 entries) is
mapped onto the 19 October 01:13 ids, six of which vanished at 01:29; the published stream has no map
from the 36 ids to the 29.

Evidence: map targets missing from the new outline: `s5_4, s7_3, s9_3, s10_3, s11_1, s11_2`. 47 of 155
grey_v2 entries land on them (`s10_3` 28, `s11_1` 6, `s7_3` 5, `s11_2` 3, `s9_3` 3, `s5_4` 2).
`resolve_sid(..., structure="2026-10-17")` returns the mapped id without checking `sid_pos`, so a rebuild
emits grey records whose `primary` is not in the taxonomy. `remap_stream.py` only knows the 56 → 36 step
and is idempotent on `taxonomy_generated == "2026-10-19"`, so it would do nothing. `corpus_full.grey` also
still carries one retrieval-time id (`s2_8`), covered by `SID_REMAP`.

Fix: add `SID_MAP_2026_10_19` (36 → 29) and compose it after the 17 October map for grey_v2. A first
cut from the titles: `s2_4 → s2_3`; `s5_1, s5_2 → s5_1`; `s5_3 → s5_2`; `s5_4 → s5_3`;
`s7_1, s7_2, s7_3 → s7_1`; `s8_1, s8_2, s8_3 → s7_2`; `s9_1 → s8_1`; `s9_2 → s8_2`; `s9_3 → s8_3`;
`s10_1 → s9_1`; `s10_2, s10_3 → s9_2`; `s11_1 → s10_1`; `s11_2 → s10_2`. Make `resolve_sid` check the
mapped id against `sid_pos` in both modes. Re-run `remap_stream.py` with the new map keyed on the new
structure stamp (finding 4); `stats.stream_per_sub` loses nine keys as a consequence.

### 4. HIGH: structure stamps are day-granular, so the drift is invisible to the tests

File: `site/data/taxonomy.json` `generated`; `site/data/stream.json` `taxonomy_generated`;
`site/data/stats.json` `source_generated`; `pipeline/tests/test_collector.py` (lines 345-347).

Summary: two outline revisions on the same day share one stamp, and the corpus did not bump its own.

Evidence: `taxonomy.generated == stream.taxonomy_generated == "2026-10-19"`, so `test_collector.py`
passes (28 tests OK) while 224 items point at re-numbered subsections. The build_data comment dates its map
to "outline.json as of 2026-10-19 01:13"; the outline changed again at 01:29. `corpus_full.json.generated`
is still `2026-10-16` although its `primary` fields were re-filed on 19 October, so
`stats.source_generated` reports 2026-10-16. Only the mtime check in `test_build_data.py` noticed.

Fix: stamp the structure, not the day: write a fingerprint of the ordered subsection titles (or the
outline's mtime to the second) into `taxonomy.json` and compare that in the collector and in
`test_collector.py`; when `corpus.generated` is older than the file's mtime, record the mtime in
`stats.source_generated`.

### 5. LOW: same-day order differs between `stream_recent.json`, `stream.json` and `stream.html`

File: `pipeline/build_data.py` `stream_derivatives()` (line 786); `site/assets/js/stream.js` `compare()`.

Summary: three tiebreaks for items with equal dates.

Evidence: `stream_recent.json` positions 4 and 5 (both 2026-10-01: OECD AIM, Apollo Research) are
swapped relative to `stream.json`; build sorts `(date, id)` desc, the file is in sweep order, the page
sorts by date then title. The landing and the stream page show the two 1 October items in different
orders.

Fix: one rule (date desc, then id) in `stream_derivatives()` and in `compare()`; keep `stream.json`
written in that order.

### 6. LOW: documentation and fallback copy describe the superseded structure

File: `SCHEMA.md` ("Changed 2026-10-19": 11 sections, 36 subsections, parts), `pipeline/build_data.py`
comment block (lines 111-122), `site/index.html` line 86 fallback text "11 sections · 36 subsections",
`site/assets/js/taxonomy.js` line 64 comment "11 segments".

Summary: all four state 11/36; the code behind them iterates the data, so only the words are wrong.

Fix: rewrite to 10/29 and the four part titles when rebuilding; the `index.html` numbers are overwritten by
`bindStats` at runtime and can be dropped to plain placeholders.

## Checks that passed

- `papers.json`: 1,788 items; every `primary`, `section` and `also[].sid` exists in `taxonomy.json`;
  key set equals the corpus. `grey.json`: 164 items, confidence set `{verified: 162, likely: 2}`, no
  empty `url`, all ids resolve.
- `stream.json`: 231 items; `failure_sources` within `benign | external | insider`; `operations` within
  the seven ids; requirements, kinds, polarities, evidence, domains, `date_precision` all within the closed
  sets; 1-4 subsections per item, all present in the taxonomy; no duplicate ids or URLs; sorted by date
  desc; every item `verified`; `related_papers` keys resolve; `taxonomy_generated` matches
  `taxonomy.generated`.
- `stream_recent.json`: 12 items, the same set as the 12 newest, newest first, byte-identical to their
  `stream.json` records.
- `stats.json`: `papers`, `grey`, `cited` (239), `sections`, `subsections`, `years`, `per_section`,
  `stream_items`, `stream_updated`, `stream_polarity`, `stream_per_source`, `stream_per_op`,
  `stream_per_sub` all equal the recomputed values. Taxonomy `counts.selected/cross/grey` equal the values
  recomputed from `papers.json` and `grey.json`.
- Front-end: no `bullets`, `observe`, `verify`, `mistakes`, `manipulation`, `misalignment` or
  `about.html` in the four JS files or the HTML; `OP_LABELS` and `SOURCE_LABELS` are filled from
  `taxonomy.json`; the stream facets derive operation, tier, requirement and subsection lists from the
  taxonomy, so no item is dropped under the current vocabulary. `#sub=s5_2` and `#s5_2` are both parsed.
- Tests: `test_collector.py` 28 OK (two summary-length anomalies, informational); `test_contrast.py`
  102 pairs OK; `test_build_data.py` fails only on the staleness guard (finding 1).
- Headless Chrome, zero console errors on both pages. `papers.html#sub=s5_2`: head "173 papers · 20
  cited in the PDF · 33 cross-referenced here · 2 reports" equals the data; 22 cards in the first chunk
  (CHUNK = 24 render units: one section head, one subsection head, 22 cards) with the lazy-load sentinel
  present. `stream.html`: "231 items"; 60 rows in the first chunk (CHUNK = 60) with the sentinel present;
  facet counts 93/97/41, 40/71/47, 149/128 equal `stats.json`.
