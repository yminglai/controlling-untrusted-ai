# Requests from the papers page to the shell and pipeline owners

Written 2026-10-17 by the papers-page implementer. Nothing here blocks the page; each item has a working
page-scoped workaround that can be removed once the shared change lands.

## 1. `grey.json[].has_zh` (pipeline)

**What.** Add `has_zh: true|false` to every item in `site/data/grey.json`, computed from `summaries_zh.json`
membership by bib key (50 of the 174 reports have notes today).

**Why.** Report cards cannot show the 中文 badge, and the "Chinese notes" filter cannot count reports, until the
549 KB notes file has been fetched. `papers.json` already carries the field. The page tolerates its absence:
`hasZh("grey", item)` falls back to the loaded notes file, and the badge appears on report cards after the first
drawer open or the first use of the "Chinese notes" filter.

**Proposed change.** In `pipeline/build_data.py`, when writing grey items: `item["has_zh"] = item["key"] in summaries`.
Record the field in `SCHEMA.md` under `grey.json`.

## 2. Pressed state for `.btn--icon` (site.css, optional)

**What.** `.btn--icon[aria-pressed="true"] { background: var(--fg); color: var(--bg); border-color: var(--fg); }`

**Why.** The density toggle (Full / Compact) is a pair of icon buttons with `aria-pressed`; the stream page's
density control is the same component. The rule now lives in `papers.css` scoped as
`.filterbar__density .btn--icon[aria-pressed="true"]`; moving it to `site.css` would let both pages share it.

## 3. Note on `closeDrawer` and the dialog `close` event (common.js, information only)

`openDrawer` restores history in a `close` listener. In the headless harness (an iframe scripted from a wrapper
page with `--virtual-time-budget`), Chrome deferred the dialog's `close` event until the next rendering
opportunity, so a programmatic `dialog.close()` left the hash at `#paper/<key>` until something else repainted.
A standalone page fires the event on the next frame, so real sessions are unaffected. The papers page routes the
× button and the backdrop click through `closeDrawer(dialog, {homeHash})` (which restores history synchronously)
and keeps the `close` listener for Escape. No change requested; recorded so the stream page can do the same.

## 4. Six bib keys exist in both `papers.json` and `grey.json` (pipeline, information only)

`benton2024sabotage`, `guo2026personalization`, `hadfieldmenell2016off`, `hubinger2019risks`,
`kaufman2025basharena`, `perez2022red` appear in both files. The page keeps separate maps and separate hash
prefixes (`#paper/<key>`, `#grey/<key>`), so nothing breaks, but `summaries_zh.json` is keyed by bib key alone and
cannot say which of the two an entry describes. Deduplicating in `build_data.py` (drop the grey copy when an
arXiv paper with the same key exists) would remove the ambiguity.
