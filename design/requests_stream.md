# Requests from the stream page to the shell owner

Written 2026-10-17 by the stream implementer. None of these block the page: each is worked around in
`stream.css` or `stream.js`. They are recorded so the shared files can absorb them when convenient.

## 1. `site.css`: intrinsic size of a collapsed full ledger row

**What.** `.ledger__row { contain-intrinsic-size: 0 124px }` assumes the 124 px row of the spec. Measured against
today's `stream.json` (231 items, 1 to 4 subsection chips, titles up to 157 characters) a collapsed full row is
157 to 245 px, mean 171 px. The 47 px gap per row made deep links land short: `scrollIntoView` computes the
target position with placeholder heights, then rows above expand as they become relevant and push the target
down (observed 8,400 px short for `#2025-07` with a smooth scroll).

**Why.** Scrollbar length and anchor jumps are smaller when the placeholder matches the real height.

**Proposed.** In `site.css`: `.ledger__row { contain-intrinsic-size: 0 172px; }`. The stream page already
overrides to 172 px in `stream.css` and scrolls instantly with a two-frame correction, so this is a tidy-up.

## 2. `common.js`: `renderLedgerRows` cannot continue a chunk

**What.** `renderLedgerRows(items, …)` resets its month tracker on every call, so rendering the ledger in chunks of
60 (as the spec asks) would repeat the month head when a chunk starts mid-month, and the per-month count is taken
from the slice rather than from the whole list. The stream page therefore calls `renderLedgerRow` per item and
builds its own month heads (same markup: `<li class="ledger__month" id="YYYY-MM">… <span class="num muted">· N items</span></li>`).

**Proposed.** An optional third argument `{ startMonth, monthCounts }` on `renderLedgerRows`: skip the head when
the first item's month equals `startMonth`, and read counts from `monthCounts[key]` when given. Then `stream.js`
can drop its local `monthHead()`.

```js
export function renderLedgerRows(items, { mode = "full", groupBy = "date", now = Date.now(), startMonth = null, monthCounts = null } = {}) {
  let month = startMonth; …
  const count = monthCounts ? monthCounts[key] || 0 : items.filter(…).length;
```

## 3. `site.css`: the "New" dot on phones

**What.** `.ledger__date .new { display: block; margin: 6px 0 0 auto }` right-aligns the dot inside the date cell.
Below 768 the full row's date cell spans the whole row (`grid-column: 1 / -1; text-align: left`), so the dot
floats to the far right edge, detached from the date. The stream page overrides it to inline after the date
(`display: inline-block; margin-left: 6px`) at `(max-width: 767px)`; the landing's short rows are unaffected
because their date cell keeps its own column.

**Proposed.** Move the override into the `(max-width: 767px)` block of `site.css`:
`.ledger__row .ledger__date .new { display: inline-block; margin: 0 0 0 6px; vertical-align: 1px; }`.

## Notes, no change requested

- `stream.json` has every `verified_on` on 2026-10-17, so every row shows the New dot; the specified behaviour.
- The stream page implements its own small search (word-prefix, NFD-stripped, `<mark>` highlighting) because
  `assets/js/search.js` from the papers assignment did not exist when the page was built. If `search.js` lands with
  `buildIndex / search / highlight`, the stream can switch to it; the field list is title, summary, publisher,
  actors, tags.
- The chronology strip's `role="img"` SVG contains focusable `<a>` columns, as the spec draws it; the month inputs
  remain the accessible range control.
