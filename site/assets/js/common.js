/* common.js: shared constants, data loading, theme, masthead, URL state, formatting, marks and chips,
   ledger rows, drawer helpers, toast. ES module, no dependencies. See design/IMPLEMENTATION_NOTES.md. */

export const REPO_URL = "https://github.com/yminglai/controlling-untrusted-ai";
export const ISSUE_URL = REPO_URL + "/issues/new?template=submit_item.yml";
export const LICENSE_URL = REPO_URL + "/blob/main/LICENSE";
export const SITE_URL = "https://ymingl.com/controlling-untrusted-ai/";
export const PAPER_STATUS = "Draft v0.2 · October 2026 · arXiv link to come";
export const THEME_KEY = "cuai-theme";
export const PAGES = { index: "index.html", papers: "papers.html", stream: "stream.html", about: "about.html" };

export const KIND_LABELS = {
  "incident": "Incident", "near-miss": "Near miss", "deployment": "Deployment", "safety-feature": "Safety feature",
  "evaluation": "Evaluation", "research": "Research", "policy": "Policy", "disclosure": "Disclosure"
};
export const POLARITY_LABELS = { good: "Good", bad: "Bad", mixed: "Mixed" };
export const SOURCE_LABELS = { mistakes: "Mistakes", manipulation: "Manipulation", misalignment: "Misalignment" };
export const OP_LABELS = { failures: "How Agents Fail", constrain: "Constrain", observe: "Observe", intervene: "Intervene", steer: "Steer", train: "Train", verify: "Verify", deploy: "Deploy and Assure" };
export const REQ_LABELS = { "correct": "Correct", "compliant": "Compliant", "in-scope": "In scope", "within-budget": "Within budget", "safe": "Safe" };

/* A registry other modules fill (taxonomy.js sets registry.taxonomy) so this module can label subsection ids
   without importing taxonomy.js. */
export const registry = { taxonomy: null, stats: null };

/* ---------- small DOM helpers ---------- */
export function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
export function icon(name, cls = "icon") {
  return `<svg class="${cls}" aria-hidden="true" focusable="false"><use href="#i-${name}"/></svg>`;
}
export function fragment(html) {
  const t = document.createElement("template");
  t.innerHTML = html.trim();
  return t.content;
}
export function el(html) { return fragment(html).firstElementChild; }

/* ---------- data loading ---------- */
const cache = new Map();
export function dataVersion() {
  const m = document.querySelector('meta[name="data-version"]');
  return (registry.stats && registry.stats.generated) || (m && m.content) || "";
}
/** fetchJSON("data/taxonomy.json", {version}) -> parsed JSON, memoised per URL. Throws on HTTP or parse failure; logs nothing. */
export function fetchJSON(path, { version, cache: cacheMode } = {}) {
  const url = version ? `${path}${path.includes("?") ? "&" : "?"}v=${encodeURIComponent(version)}` : path;
  if (cache.has(url)) return cache.get(url);
  const p = fetch(url, cacheMode ? { cache: cacheMode } : undefined).then((r) => {
    if (!r.ok) throw new Error(`${r.status} ${url}`);
    return r.json();
  });
  p.catch(() => cache.delete(url));
  cache.set(url, p);
  return p;
}
let statsPromise = null;
/** loadStats() -> stats.json, fetched once with cache: "no-cache". */
export function loadStats() {
  if (!statsPromise) {
    statsPromise = fetchJSON("data/stats.json", { cache: "no-cache" }).then((s) => { registry.stats = s; return s; });
    statsPromise.catch(() => { statsPromise = null; });
  }
  return statsPromise;
}
/** loadStream(stats) -> stream.json or null when stats.stream_items is 0 (no request is made). */
export function loadStream(stats) {
  if (!stats || !(stats.stream_items > 0)) return Promise.resolve(null);
  return fetchJSON("data/stream.json", { version: stats.stream_updated || stats.generated });
}

/* ---------- URL state ---------- */
const IGNORED_QUERY = new Set(["theme"]);
/** readState() -> {hash, ...queryKeys}; multi-values stay comma strings; `theme` is ignored. */
export function readState() {
  const q = new URLSearchParams(location.search);
  const state = {};
  for (const [k, v] of q) if (!IGNORED_QUERY.has(k) && v !== "") state[k] = v;
  state.hash = decodeURIComponent(location.hash.replace(/^#/, ""));
  return state;
}
function buildURL(file, state) {
  const q = new URLSearchParams();
  const keys = Object.keys(state).filter((k) => k !== "hash").sort();
  for (const k of keys) {
    let v = state[k];
    if (Array.isArray(v)) v = v.filter((x) => x != null && x !== "").join(",");
    if (v === undefined || v === null || v === "" || v === false) continue;
    q.set(k, String(v));
  }
  const qs = q.toString();
  const hash = state.hash ? "#" + state.hash : "";
  return `${file}${qs ? "?" + qs : ""}${hash}`;
}
/** writeState(patch, {push}) merges patch into the current state (null/""/false removes a key; `hash` sets the hash)
    and calls replaceState (default) or pushState. Keeps a `theme` query param if present. */
export function writeState(patch, { push = false, historyState = null } = {}) {
  const cur = readState();
  const next = { ...cur, ...patch };
  const theme = new URLSearchParams(location.search).get("theme");
  if (theme) next.theme = theme;
  const file = location.pathname.split("/").pop() || "index.html";
  const url = buildURL(file, next);
  const st = historyState || (push ? { drawer: true } : history.state);
  if (push) history.pushState(st, "", url); else history.replaceState(st, "", url);
  return url;
}
/** linkTo("papers", {hash: "s5_3", q: "monitor"}) -> "papers.html?q=monitor#s5_3". Page is a key of PAGES or a file name. */
export function linkTo(page, state = {}) {
  const file = PAGES[page] || page;
  return buildURL(file, state);
}

/* ---------- formatting ---------- */
const nf = new Intl.NumberFormat("en-GB");
export function fmtInt(n) { return n == null || isNaN(n) ? "" : nf.format(n); }
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const MONTHS_LONG = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
function parts(iso) {
  const m = /^(\d{4})-(\d{2})(?:-(\d{2}))?/.exec(String(iso || ""));
  return m ? { y: +m[1], mo: +m[2], d: m[3] ? +m[3] : 1 } : null;
}
/** fmtDate("2026-10-17", "day") -> "17 Oct"; precision "month" -> "Oct"; "year" -> "2026"; {year:true} appends the year. */
export function fmtDate(iso, precision = "day", { year = false } = {}) {
  const p = parts(iso);
  if (!p) return "";
  if (precision === "year") return String(p.y);
  if (precision === "month") return year ? `${MONTHS[p.mo - 1]} ${p.y}` : MONTHS[p.mo - 1];
  return `${p.d} ${MONTHS[p.mo - 1]}${year ? " " + p.y : ""}`;
}
/** fmtDateLong("2026-10-17T00:00:00Z") -> "17 Oct 2026" */
export function fmtDateLong(iso) { return fmtDate(iso, "day", { year: true }); }
/** fmtMonth("2025-07") -> "July 2025" */
export function fmtMonth(yyyymm) { const p = parts(yyyymm); return p ? `${MONTHS_LONG[p.mo - 1]} ${p.y}` : ""; }
/** fmtRelative(iso) -> "3 h ago", "3 days ago", "just now"; falls back to the long date beyond 30 days. */
export function fmtRelative(iso, now = Date.now()) {
  const t = Date.parse(iso);
  if (isNaN(t)) return "";
  const s = Math.max(0, (now - t) / 1000);
  if (s < 90) return "just now";
  if (s < 3600) return `${Math.round(s / 60)} min ago`;
  if (s < 48 * 3600) return `${Math.round(s / 3600)} h ago`;
  const d = Math.round(s / 86400);
  if (d <= 30) return `${d} days ago`;
  return fmtDateLong(iso);
}
/** withinDays(iso, 7) -> true when iso is at most n days before now. */
export function withinDays(iso, n, now = Date.now()) {
  const t = Date.parse(iso);
  return !isNaN(t) && now - t <= n * 86400000 && t <= now + 86400000;
}
export function monthKey(iso) { return String(iso || "").slice(0, 7); }
function surname(name) {
  const s = String(name || "").trim();
  if (!s) return "";
  if (s.includes(",")) return s.split(",")[0].trim();
  const w = s.split(/\s+/);
  return w[w.length - 1];
}
/** authorsLine(["Mikhail Terekhov", "Alexander Panfilov", "Daniil Dzenhaliou", "X Y"]) -> "Terekhov, Panfilov, Dzenhaliou +1";
    50 or more authors -> "Terekhov and 264 more". */
export function authorsLine(list) {
  const a = Array.isArray(list) ? list.filter(Boolean) : [];
  if (!a.length) return "";
  if (a.length >= 50) return `${surname(a[0])} and ${fmtInt(a.length - 1)} more`;
  const head = a.slice(0, 3).map(surname).join(", ");
  return a.length > 3 ? `${head} +${a.length - 3}` : head;
}
export function firstSentences(text, n = 2) {
  const s = String(text || "").match(/[^.!?]+[.!?]+(\s|$)/g) || [String(text || "")];
  return s.slice(0, n).join("").trim();
}
/** firstSentence("URL fetched; date confirmed. Same event as 006.") -> "URL fetched; date confirmed." (a full stop followed by a capital or the end) */
export function firstSentence(text) {
  const t = String(text || "").trim();
  const m = /^[\s\S]*?[.!?](?=\s+[A-Z"'(\[]|$)/.exec(t);
  return m ? m[0] : t;
}

/* ---------- theme ---------- */
export function currentTheme() { return document.documentElement.getAttribute("data-theme") === "dark" ? "dark" : "light"; }
export function setTheme(t, { store = true } = {}) {
  document.documentElement.setAttribute("data-theme", t);
  if (store) { try { localStorage.setItem(THEME_KEY, t); } catch (e) { /* storage unavailable */ } }
  for (const b of document.querySelectorAll(".theme-toggle")) b.setAttribute("aria-label", t === "dark" ? "Switch to light theme" : "Switch to dark theme");
}
/** initTheme(): wires every .theme-toggle; the inline head script has already set data-theme before paint. */
export function initTheme() {
  setTheme(currentTheme(), { store: false });
  for (const b of document.querySelectorAll(".theme-toggle")) b.addEventListener("click", () => setTheme(currentTheme() === "dark" ? "light" : "dark"));
  try {
    const mq = matchMedia("(prefers-color-scheme: dark)");
    mq.addEventListener("change", (e) => { if (!localStorage.getItem(THEME_KEY) && !new URLSearchParams(location.search).get("theme")) setTheme(e.matches ? "dark" : "light", { store: false }); });
  } catch (e) { /* no matchMedia */ }
}

/* ---------- masthead ---------- */
/** initMasthead(stats): aria-current on the nav, the Stream dot when stats.stream_updated is within 7 days, the Menu sheet. */
export function initMasthead(stats) {
  const file = location.pathname.split("/").pop() || "index.html";
  for (const a of document.querySelectorAll(".masthead .nav__link")) {
    const target = (a.getAttribute("href") || "").split(/[?#]/)[0];
    if (target === file) a.setAttribute("aria-current", "page"); else a.removeAttribute("aria-current");
  }
  const streamLink = document.querySelector('.masthead .nav__link[href^="stream.html"]');
  if (streamLink && stats && stats.stream_updated && withinDays(stats.stream_updated, 7) && !streamLink.querySelector(".nav__dot")) {
    streamLink.insertAdjacentHTML("beforeend", '<span class="nav__dot" aria-hidden="true"></span><span class="visually-hidden"> updated this week</span>');
  }
  const head = document.querySelector(".masthead");
  const btn = document.querySelector(".menu-btn");
  if (head && btn) {
    const close = () => { head.classList.remove("is-open"); btn.setAttribute("aria-expanded", "false"); };
    btn.addEventListener("click", () => { const open = !head.classList.contains("is-open"); head.classList.toggle("is-open", open); btn.setAttribute("aria-expanded", String(open)); });
    document.addEventListener("keydown", (e) => { if (e.key === "Escape" && head.classList.contains("is-open")) { close(); btn.focus(); } });
    document.addEventListener("click", (e) => { if (head.classList.contains("is-open") && !head.contains(e.target)) close(); });
  }
}

/* ---------- data binding ---------- */
function resolve(ctx, path) {
  return path.split(".").reduce((o, k) => (o == null ? undefined : o[k]), ctx);
}
function applyFilter(v, f) {
  const [name, arg] = f.split(":");
  switch (name) {
    case "int": return fmtInt(v);
    case "date": return fmtDateLong(v);
    case "month": return fmtMonth(v);
    case "sentences": return firstSentences(v, +arg || 2);
    case "firstkey": return v && typeof v === "object" ? String(Object.keys(v).map(Number).filter((n) => !isNaN(n)).sort((a, b) => a - b)[0] ?? "") : "";
    case "lastkey": return v && typeof v === "object" ? String(Object.keys(v).map(Number).filter((n) => !isNaN(n)).sort((a, b) => b - a)[0] ?? "") : "";
    case "or": return v == null || v === "" ? arg : v;
    case "count": return v && typeof v === "object" ? fmtInt(Array.isArray(v) ? v.length : Object.keys(v).length) : "";
    default: return v;
  }
}
/** bindStats(stats, extra): fills every [data-bind="stats.papers"], [data-bind="taxonomy.thesis|sentences:2"].
    Paths resolve against {stats, ...extra}; numbers are formatted with fmtInt unless a filter says otherwise. */
export function bindStats(stats, extra = {}) {
  const ctx = { stats, ...extra };
  for (const node of document.querySelectorAll("[data-bind]")) {
    const [path, ...filters] = node.dataset.bind.split("|");
    let v = resolve(ctx, path.trim());
    if (v === undefined) continue;
    for (const f of filters) v = applyFilter(v, f.trim());
    if (typeof v === "number") v = fmtInt(v);
    if (v == null) continue;
    if (node.dataset.bindAttr) node.setAttribute(node.dataset.bindAttr, String(v)); else node.textContent = String(v);
  }
}

/* ---------- marks and chips ---------- */
const SECTION_RE = /^s\d{1,2}$/, SUB_RE = /^s\d{1,2}_\d{1,2}$/;
export function dataAttrFor(id) {
  if (id in OP_LABELS) return `data-op="${id}"`;
  if (id in SOURCE_LABELS) return `data-source="${id}"`;
  if (id in POLARITY_LABELS) return `data-polarity="${id}"`;
  if (SECTION_RE.test(id)) return `data-section="${id}"`;
  if (SUB_RE.test(id)) return `data-section="${id.split("_")[0]}"`;
  return `data-c="${esc(id)}"`;
}
/** mark({shape: "square"|"square-hollow"|"circle"|"dash"|"dash-l"|"dot", c: "s5"|"observe"|"mistakes"|"bad"|"report"}) -> HTML string */
export function mark({ shape = "square", c = "gray", hollow = false, label = "" } = {}) {
  const cls = `mark mark--${hollow ? "square-hollow" : shape}`;
  return `<span class="${cls}" ${dataAttrFor(c)} ${label ? `role="img" aria-label="${esc(label)}"` : 'aria-hidden="true"'}></span>`;
}
export function labelFor(kind, id) {
  if (kind === "op") return OP_LABELS[id] || id;
  if (kind === "source") return SOURCE_LABELS[id] || id;
  if (kind === "polarity") return POLARITY_LABELS[id] || id;
  if (kind === "req") return REQ_LABELS[id] || id;
  if (kind === "kind") return KIND_LABELS[id] || id;
  const tax = registry.taxonomy;
  if (tax) {
    for (const s of tax.sections) {
      if (s.id === id) return kind === "section" ? `§${s.number} ${s.title}` : s.title;
      for (const ss of s.subsections) if (ss.id === id) return `${ss.number} ${ss.title}`;
    }
  }
  return id;
}
/** chip({kind, id, href, removable, asFilter, toggle, label, count, on}) -> HTML string.
    kind: "section" | "sub" | "op" | "source" | "polarity" | "req" | "plain" | "kind".
    href -> <a>; asFilter -> <button>: a toggle (aria-pressed, named by its visible text and count) by default, or with
    toggle:false an action button ("Filter by X", no pressed state: the ledger's row chips); removable -> the × button (data-remove=id). */
export function chip({ kind = "plain", id = "", href = "", removable = false, asFilter = false, toggle = true, label, count, on = false, title = "" } = {}) {
  const text = label ?? labelFor(kind, id);
  const shape = kind === "source" ? "circle" : kind === "polarity" ? "dash" : "square";
  const hasMark = kind === "section" || kind === "op" || kind === "source" || kind === "polarity";
  const attr = kind === "plain" || kind === "req" || kind === "kind" ? "" : dataAttrFor(id);
  const cls = ["chip", `chip--${kind}`, removable ? "chip--removable" : "", asFilter ? "chip--filter" : "", on ? "is-on" : ""].filter(Boolean).join(" ");
  const inner = `${hasMark ? `<span class="mark mark--${shape}" aria-hidden="true"></span>` : ""}<span class="chip__text">${esc(text)}</span>${count != null ? `<span class="chip__count">${fmtInt(count)}</span>` : ""}${asFilter ? icon("sliders", "icon icon--sliders") : ""}${removable ? `<button type="button" class="chip__x" data-remove="${esc(id)}" aria-label="Remove ${esc(text)}">${icon("x")}</button>` : ""}`;
  const t = title ? ` title="${esc(title)}"` : "";
  if (asFilter) return `<button type="button" class="${cls}" ${attr} data-kind="${kind}" data-id="${esc(id)}"${toggle ? ` aria-pressed="${on}"` : ` aria-label="Filter by ${esc(text)}"`}${t}>${inner}</button>`;
  if (href) return `<a class="${cls}" ${attr} data-kind="${kind}" data-id="${esc(id)}" href="${esc(href)}"${t}>${inner}</a>`;
  return `<span class="${cls}" ${attr} data-kind="${kind}" data-id="${esc(id)}"${t}>${inner}</span>`;
}

/* ---------- ledger rows (shared by index and stream) ---------- */
/** renderLedgerRows(items, {mode: "short"|"full", groupBy: "date"|"verified"}) -> DocumentFragment of <li> month heads and rows.
    Chunked callers pass {startMonth, monthCounts, startIndex}: the month head is skipped while the first items belong to
    startMonth (the month already headed by the previous chunk) and each head reads its count from monthCounts[key]
    (the whole list) instead of the slice. */
export function renderLedgerRows(items, { mode = "full", groupBy = "date", now = Date.now(), startMonth = null, monthCounts = null, startIndex = 0, showNew = true } = {}) {
  const frag = document.createDocumentFragment();
  const keyOf = (x) => monthKey(groupBy === "verified" ? x.verified_on : x.date);
  let month = startMonth;
  items.forEach((it, i) => {
    const key = keyOf(it);
    if (key !== month) {
      month = key;
      const count = monthCounts ? monthCounts[key] || 0 : items.filter((x) => keyOf(x) === key).length;
      const late = mode === "short" && startIndex + i >= 8 ? " ledger__row--late" : "";
      frag.appendChild(el(`<li class="ledger__month${late}"${mode === "full" ? ` id="${esc(key)}"` : ""} role="presentation">${esc(fmtMonth(key))}${groupBy === "verified" ? ' <span class="muted">· verified</span>' : ""}${mode === "full" ? ` <span class="num muted">· ${fmtInt(count)} ${count === 1 ? "item" : "items"}</span>` : ""}</li>`));
    }
    frag.appendChild(renderLedgerRow(it, { mode, index: startIndex + i, groupBy, now, showNew }));
  });
  return frag;
}
/** renderLedgerRow(item, {mode, index}) -> <li> element. Full rows carry fields 1 to 5 of DESIGN.md 6.4 collapsed; stream.js adds expansion. */
export function renderLedgerRow(it, { mode = "full", index = 0, groupBy = "date", now = Date.now(), showNew = true } = {}) {
  const isNew = showNew && it.verified_on && withinDays(it.verified_on, 7, now);
  const prec = it.date_precision || "day";
  const dateTitle = prec === "month" ? ' title="date known to the month"' : prec === "year" ? ' title="date known to the year"' : ` title="${esc(it.date)}"`;
  const kind = KIND_LABELS[it.kind] || it.kind || "";
  if (mode === "short") {
    return el(`<li class="ledger__row ledger__row--short${index >= 8 ? " ledger__row--late" : ""}" data-polarity="${esc(it.polarity)}" data-id="${esc(it.id)}">
      <div class="ledger__date"${dateTitle}>${esc(fmtDate(it.date, prec))}</div>
      <div class="ledger__body">
        <div class="ledger__kind"><span class="ledger__dash" role="img" aria-label="${esc(POLARITY_LABELS[it.polarity] || it.polarity)}"></span>${esc(kind)}</div>
        <div class="ledger__title clamp-2">${isNew ? '<span class="new" aria-hidden="true"></span><span class="visually-hidden">new this week </span>' : ""}<a href="${esc(linkTo("stream", { hash: "item/" + it.id }))}">${esc(it.title)}</a></div>
        <div class="ledger__publisher">${esc(it.publisher || "")}</div>
      </div></li>`);
  }
  const showVerified = groupBy === "verified";
  const dateCell = showVerified
    ? `<span class="caps muted">verified</span><br>${esc(fmtDate(it.verified_on, "day"))}`
    : esc(fmtDate(it.date, prec));
  const chips = [
    ...(it.failure_sources || []).map((s) => chip({ kind: "source", id: s, asFilter: true, toggle: false })),
    ...(it.operations || []).map((o) => chip({ kind: "op", id: o, asFilter: true, toggle: false })),
    ...(it.requirements || []).map((r) => chip({ kind: "req", id: r })),
    ...(it.subsections || []).map((s) => chip({ kind: "sub", id: s, href: linkTo("papers", { hash: s }) }))
  ].join("");
  return el(`<li class="ledger__row" id="item-${esc(it.id)}" data-polarity="${esc(it.polarity)}" data-id="${esc(it.id)}">
    <div class="ledger__date"${dateTitle}>${dateCell}${isNew ? '<span class="new" aria-hidden="true"></span><span class="visually-hidden">new this week</span>' : ""}</div>
    <div class="ledger__body">
      <div class="ledger__kind"><span class="ledger__dash" role="img" aria-label="${esc(POLARITY_LABELS[it.polarity] || it.polarity)}"></span>${esc(kind)}</div>
      <h3 class="ledger__title clamp-2"><a class="ext" href="${esc(it.url)}" rel="noopener" target="_blank">${esc(it.title)}${icon("arrow-up-right", "icon icon--ext")}</a></h3>
      <p class="ledger__summary clamp-2">${esc(it.summary || "")}</p>
      <div class="ledger__class">${chips}</div>
      <div class="ledger__extra" hidden></div>
    </div>
    <button type="button" class="btn--icon ledger__more" aria-expanded="false" aria-label="More about this item">${icon("chevron-down")}</button>
  </li>`);
}
/** polarityBar(el, {good, bad, mixed}) renders the 3-segment signature bar; one --rule segment when counts are empty. */
export function polarityBar(target, counts) {
  const total = counts ? (counts.good || 0) + (counts.bad || 0) + (counts.mixed || 0) : 0;
  target.setAttribute("aria-label", total ? `Items by polarity: ${fmtInt(counts.good || 0)} good, ${fmtInt(counts.bad || 0)} bad, ${fmtInt(counts.mixed || 0)} mixed` : "Items by polarity: none yet");
  if (!total) { target.innerHTML = '<span class="sigbar__seg sigbar__seg--empty"></span>'; return; }
  target.innerHTML = ["good", "bad", "mixed"].filter((k) => counts[k] > 0)
    .map((k) => `<span class="sigbar__seg" data-polarity="${k}" style="flex-grow:${counts[k]}" title="${POLARITY_LABELS[k]} · ${fmtInt(counts[k])}"></span>`).join("");
}
export function polarityCounts(items) {
  const c = { good: 0, bad: 0, mixed: 0 };
  for (const it of items || []) if (it.polarity in c) c[it.polarity]++;
  return c;
}

/* ---------- drawers ---------- */
let drawerOpen = null;
/** openDrawer(dialog, {hash}) -> showModal(), pushState({drawer:true}) with the entity hash; Back closes it. */
export function openDrawer(dialog, { hash, returnTo } = {}) {
  if (!dialog) return;
  dialog.__returnTo = returnTo || document.activeElement;
  if (!dialog.open) dialog.showModal();
  drawerOpen = dialog;
  if (hash !== undefined) writeState({ hash }, { push: true });
  dialog.addEventListener("close", onDialogClose, { once: true });
}
function onDialogClose(e) {
  const d = e.target;
  if (drawerOpen === d) drawerOpen = null;
  if (history.state && history.state.drawer) history.back();
  const r = d.__returnTo;
  if (r && typeof r.focus === "function") r.focus();
}
/** closeDrawer(dialog, {homeHash}) -> history.back() when the open pushed a state, else replaceState to the home hash. */
export function closeDrawer(dialog, { homeHash } = {}) {
  if (!dialog || !dialog.open) return;
  dialog.removeEventListener("close", onDialogClose);
  drawerOpen = null;
  dialog.close();
  if (history.state && history.state.drawer) history.back();
  else if (homeHash !== undefined) writeState({ hash: homeHash });
  const r = dialog.__returnTo;
  if (r && typeof r.focus === "function") r.focus();
}
window.addEventListener("popstate", () => {
  if (drawerOpen && drawerOpen.open && !(history.state && history.state.drawer)) {
    drawerOpen.removeEventListener("close", onDialogClose);
    const d = drawerOpen; drawerOpen = null; d.close();
    const r = d.__returnTo; if (r && typeof r.focus === "function") r.focus();
  }
});

/* ---------- utilities ---------- */
export function debounce(fn, ms = 150) {
  let t = 0;
  const d = (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); };
  d.cancel = () => clearTimeout(t);
  return d;
}
export function onIdle(fn, timeout = 1500) {
  if ("requestIdleCallback" in window) return requestIdleCallback(fn, { timeout });
  return setTimeout(() => fn({ didTimeout: true, timeRemaining: () => 8 }), 0);
}
/** idleChunks(array, 200, (slice, start) => ...) processes the array in idle-time chunks; resolves when done. */
export function idleChunks(array, size, fn) {
  return new Promise((resolve) => {
    let i = 0;
    const step = () => {
      const end = Math.min(i + size, array.length);
      fn(array.slice(i, end), i);
      i = end;
      if (i < array.length) onIdle(step); else resolve();
    };
    if (!array.length) resolve(); else onIdle(step);
  });
}
let toastEl = null, toastTimer = 0;
/** toast("Copied") shows a 1.5 s toast with aria-live="polite". */
export function toast(text, ms = 1500) {
  if (!toastEl) {
    toastEl = el('<div class="toast" role="status" aria-live="polite" hidden></div>');
    document.body.appendChild(toastEl);
  }
  toastEl.textContent = text;
  toastEl.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { toastEl.hidden = true; }, ms);
}
export async function copyText(text, label = "Copied") {
  try { await navigator.clipboard.writeText(text); toast(label); return true; }
  catch (e) { toast("Copy failed"); return false; }
}
export function reducedMotion() { return matchMedia("(prefers-reduced-motion: reduce)").matches; }

/* ---------- footer ---------- */
/** initFooter(stats): fills the colophon's generated and stream-updated dates. */
export function initFooter(stats) {
  const g = document.querySelector("[data-footer-generated]");
  const s = document.querySelector("[data-footer-stream]");
  if (g && stats) g.textContent = stats.generated || "";
  if (s) {
    const u = stats && stats.stream_updated;
    s.textContent = u ? fmtDateLong(u) : "not yet";
    if (u) s.setAttribute("title", u);
  }
}
/** initPage(): theme, stats, masthead, footer; returns the stats promise (null on failure, never throws). */
export async function initPage() {
  initTheme();
  let stats = null;
  try { stats = await loadStats(); } catch (e) { stats = null; }
  initMasthead(stats);
  initFooter(stats);
  if (stats) bindStats(stats);
  return stats;
}
