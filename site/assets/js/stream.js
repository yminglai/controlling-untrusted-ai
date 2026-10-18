/* stream.js: the live stream page (design/DESIGN.md section 6). Conditional load of stream.json, facet counts against
   the other active groups, filtering and sorting, the chronology strip drawn from the filtered set with scroll-spy,
   chunked ledger rows with expansion and deep links, chip filters, related-paper labels via a lazy papers.json load,
   download and report links, empty, error and stale states. Filters live in the query string, position in the hash;
   every URL is built with linkTo / readState / writeState. No console output. */
import {
  initPage, bindStats, readState, writeState, linkTo, fetchJSON, dataVersion, loadStream,
  fmtInt, fmtDateLong, fmtMonth, fmtRelative, monthKey, esc, icon, chip, renderLedgerRows, firstSentence, withinDays,
  debounce, copyText, reducedMotion, ISSUE_URL, KIND_LABELS, POLARITY_LABELS, SOURCE_LABELS, OP_LABELS, REQ_LABELS
} from "./common.js";
import * as T from "./taxonomy.js";

const $ = (s, r = document) => r.querySelector(s);
const PAGE_TITLE = "Stream · Controlling Untrusted AI";
const CHUNK = 60;
const MULTI = ["polarity", "source", "op", "req", "kind", "evidence"];
const SINGLE = ["domain", "sub", "from", "to", "q", "paper"];
const FILTER_KEYS = [...MULTI, ...SINGLE];
const COUNTED = ["polarity", "source", "op", "req", "kind", "evidence", "domain", "sub"];
const DOMAINS = ["coding", "browsing", "customer-service", "finance", "email-and-office", "healthcare", "legal", "cyber", "research", "infrastructure", "consumer", "government", "multi-agent", "other"];
const EVIDENCE = ["first-party", "press", "researcher", "regulator", "court", "incident-database"];
const KINDS = Object.keys(KIND_LABELS);
const EVIDENCE_LABELS = { "first-party": "First-party", press: "Press", researcher: "Researcher", regulator: "Regulator", court: "Court", "incident-database": "Incident database" };
const DOMAIN_LABELS = { coding: "Coding", browsing: "Browsing", "customer-service": "Customer service", finance: "Finance", "email-and-office": "Email and office", healthcare: "Healthcare", legal: "Legal", cyber: "Cyber", research: "Research", infrastructure: "Infrastructure", consumer: "Consumer", government: "Government", "multi-agent": "Multi-agent", other: "Other" };
const HOUR = 3600000, DAY = 86400000;

/* ---------- module state ---------- */
let stats = null, tax = null, stream = null;
let items = [];                 // every item in the file
let byId = new Map();
let allMonths = [];             // YYYY-MM from the earliest item to the current UTC month
let state = null;               // parsed URL state
let list = [];                  // filtered and sorted
let monthCounts = {};           // per month head in the current sort
let rendered = 0, lastMonth = null;
let lastSignature = null;
const expanded = new Set();
const indexCache = new WeakMap();
let papersMap = null, papersPromise = null, papersFailed = false;
let sentinelIO = null, headIO = null, resizeRO = null;
let liveTimer = 0;
let showNewDots = true;          // false when more than half the items were verified this week: the dot would say nothing

const ledger = $("#ledger"), stateEl = $("#state"), sentinel = $("#sentinel"), facetsEl = $("#facets"),
  activeEl = $("#active"), resultsEl = $("#results"), chronoEl = $("#chronology"), pipelineEl = $("#pipeline"),
  mainEl = $("#stream-main"), toggleBtn = $("#facets-toggle"), toggleLabel = $("#facets-toggle-label"), scrim = $("#facets-scrim");
const mqSheet = matchMedia("(max-width: 1023px)");
const mqPhone = matchMedia("(max-width: 767px)");

/* ---------- helpers ---------- */
function human(id) { return String(id || "").replace(/-/g, " ").replace(/^\w/, (c) => c.toUpperCase()); }
function escapeRe(s) { return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"); }
function currentMonthUTC() { const d = new Date(); return `${d.getUTCFullYear()}-${String(d.getUTCMonth() + 1).padStart(2, "0")}`; }
function nextMonth(k) { let [y, m] = k.split("-").map(Number); m++; if (m > 12) { m = 1; y++; } return `${y}-${String(m).padStart(2, "0")}`; }
function monthsBetween(a, b) { const out = []; let k = a; let guard = 0; while (k <= b && guard++ < 1200) { out.push(k); k = nextMonth(k); } return out; }
function sortKeyOf(it) { return state && state.sort === "verified" ? monthKey(it.verified_on || it.date) : monthKey(it.date); }
function hostOf(url) { try { return new URL(url).hostname.replace(/^www\./, ""); } catch (e) { return url; } }
function reportUrl(id) { return ISSUE_URL + "&title=" + encodeURIComponent("[Submission]: Correction to " + id); }
function itemUrl(id) { return new URL(linkTo("stream", { hash: "item/" + id }), location.href).href; }

/* ---------- URL state ---------- */
function parseState() {
  const s = readState();
  const st = { hash: s.hash || "", sort: s.sort === "verified" ? "verified" : "date", density: s.density === "compact" ? "compact" : "full" };
  for (const k of MULTI) st[k] = s[k] ? String(s[k]).split(",").map((x) => x.trim()).filter(Boolean) : [];
  for (const k of SINGLE) st[k] = s[k] ? String(s[k]) : "";
  return st;
}
function hasFilters(st) { return FILTER_KEYS.some((k) => Array.isArray(st[k]) ? st[k].length : st[k]); }
function activeCount(st) { return FILTER_KEYS.reduce((n, k) => n + (Array.isArray(st[k]) ? st[k].length : st[k] ? 1 : 0), 0); }
function signature(st) { return FILTER_KEYS.map((k) => `${k}=${Array.isArray(st[k]) ? st[k].join(",") : st[k]}`).join("&") + `&sort=${st.sort}&density=${st.density}`; }
function setMulti(group, id, on) {
  const cur = new Set(state[group]);
  if (on === undefined) on = !cur.has(id);
  if (on) cur.add(id); else cur.delete(id);
  writeState({ [group]: [...cur].join(",") || null });
  render();
}
function setSingle(key, value) { writeState({ [key]: value || null }); render(); }
function clearFilters() {
  const patch = {}; for (const k of FILTER_KEYS) patch[k] = null;
  writeState(patch); render();
}

/* ---------- search ---------- */
function norm(s) { return " " + String(s || "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[^\p{L}\p{N}]+/gu, " ").trim(); }
function tokens(q) { return norm(q).trim().split(/\s+/).filter((t) => t.length >= 2); }
function indexFor(it) {
  let idx = indexCache.get(it);
  if (!idx) {
    const a = it.actors || {};
    idx = norm([it.title, it.summary, it.publisher, a.vendor, a.deployer, a.model, ...(it.tags || [])].filter(Boolean).join(" "));
    indexCache.set(it, idx);
  }
  return idx;
}
function searchMatch(it, toks) { if (!toks.length) return true; const idx = indexFor(it); return toks.every((t) => idx.includes(" " + t)); }
function highlightText(text, toks) {
  const s = String(text || "");
  if (!toks.length) return esc(s);
  let re;
  try { re = new RegExp(`(?<![\\p{L}\\p{N}])(?:${toks.map(escapeRe).join("|")})`, "giu"); } catch (e) { return esc(s); }
  let out = "", last = 0;
  for (const m of s.matchAll(re)) { out += esc(s.slice(last, m.index)) + "<mark>" + esc(m[0]) + "</mark>"; last = m.index + m[0].length; }
  return out + esc(s.slice(last));
}
function applyHighlight(row, toks) {
  const a = row.querySelector(".ledger__title a");
  const tn = a && Array.from(a.childNodes).find((n) => n.nodeType === 3);
  if (tn) { const span = document.createElement("span"); span.innerHTML = highlightText(tn.textContent, toks); tn.replaceWith(...span.childNodes); }
  const p = row.querySelector(".ledger__summary");
  if (p) p.innerHTML = highlightText(p.textContent, toks);
}

/* ---------- matching ---------- */
function valuesOf(it, g) {
  switch (g) {
    case "polarity": return [it.polarity];
    case "source": return it.failure_sources || [];
    case "op": return it.operations || [];
    case "req": return it.requirements || [];
    case "kind": return [it.kind];
    case "evidence": return [it.evidence];
    case "domain": return [it.domain];
    case "sub": return it.subsections || [];
  }
  return [];
}
function matchGroup(it, g, st, toks) {
  const v = st[g];
  if (!v || (Array.isArray(v) && !v.length)) return true;
  switch (g) {
    case "polarity": case "kind": case "evidence": return v.includes(valuesOf(it, g)[0]);
    case "source": case "op": case "req": return valuesOf(it, g).some((x) => v.includes(x));
    case "domain": return it.domain === v;
    case "sub": return (it.subsections || []).some((x) => x === v || (!v.includes("_") && x.startsWith(v + "_")));
    case "from": return monthKey(it.date) >= v;
    case "to": return monthKey(it.date) <= v;
    case "paper": {
      if ((it.related_papers || []).includes(v)) return true;
      const p = papersMap && papersMap.get(v);
      return !!(p && (it.subsections || []).includes(p.primary));
    }
    case "q": return searchMatch(it, toks);
  }
  return true;
}
function matches(it, st, skip, toks) {
  for (const g of FILTER_KEYS) { if (g === skip) continue; if (!matchGroup(it, g, st, toks)) return false; }
  return true;
}
function compare(a, b) {
  if (state.sort === "verified") {
    const va = a.verified_on || "", vb = b.verified_on || "";
    if (va !== vb) return va < vb ? 1 : -1;
  }
  if (a.date !== b.date) return a.date < b.date ? 1 : -1;
  return String(a.title).localeCompare(String(b.title));
}
function facetCounts(st, toks) {
  const c = {};
  for (const g of COUNTED) {
    const m = (c[g] = {});
    for (const it of items) if (matches(it, st, g, toks)) for (const v of valuesOf(it, g)) if (v) m[v] = (m[v] || 0) + 1;
  }
  return c;
}

/* ---------- live indicator ---------- */
function setLive(iso, noneText = "The ledger opens with the first verified sweep") {
  const live = $("#live"), label = $("#live-label");
  const put = (t) => { if (label.textContent !== t) label.textContent = t; };   /* aria-live: write only when the text changes */
  live.classList.remove("live--fresh", "live--stale", "live--stalled", "live--none");
  if (!iso || isNaN(Date.parse(iso))) { live.classList.add("live--none"); put(noneText); live.removeAttribute("title"); return; }
  const age = Date.now() - Date.parse(iso);
  let cls, text;
  if (age < 48 * HOUR) { cls = "live--fresh"; text = `Live · updated ${fmtRelative(iso)}`; }
  else if (age <= 7 * DAY) { cls = "live--stale"; text = `Collector last ran ${fmtRelative(iso)}`; }
  else { cls = "live--stalled"; text = `Collector stalled since ${fmtDateLong(iso)}`; }
  live.classList.add(cls); put(text); live.setAttribute("title", iso);
  clearTimeout(liveTimer);
  if (age < 48 * HOUR) liveTimer = setTimeout(() => setLive(iso), 60000);
}

/* ---------- facets ---------- */
function group(key, legend, ids, chipKind, labels) {
  return `<fieldset class="facet" data-group="${key}"><legend class="facet__legend caps">${legend}</legend><div class="facet__options">${ids.map((id) => chip({ kind: chipKind, id, asFilter: true, count: 0, label: labels ? labels[id] || human(id) : undefined })).join("")}</div></fieldset>`;
}
function radio(name, value, label, checked) {
  return `<label class="facet__radio"><input type="radio" name="${name}" value="${value}" data-group="${name}"${checked ? " checked" : ""}><span>${label}</span></label>`;
}
function buildFacets() {
  const ops = (T.operations.length ? T.operations.filter((o) => o.lever !== null).map((o) => o.id) : Object.keys(OP_LABELS).filter((o) => o !== "failures"));
  const srcs = T.failureSources.length ? T.failureSources.map((f) => f.id) : Object.keys(SOURCE_LABELS);
  const reqs = T.requirements.length ? T.requirements.map((r) => r.id) : Object.keys(REQ_LABELS);
  const subs = T.sections.map((s) => `<optgroup label="§${s.number} ${esc(s.title)}">${s.subsections.map((ss) => `<option value="${ss.id}" data-label="${ss.number} ${esc(ss.title)}">${ss.number} ${esc(ss.title)}</option>`).join("")}</optgroup>`).join("");
  facetsEl.innerHTML = `
    <div class="facets__bar"><span class="caps">Filters</span><button type="button" class="btn--icon facets__close" aria-label="Close filters">${icon("x")}</button></div>
    <h2 class="visually-hidden">Filters</h2>
    <div class="facet facet--search" role="search">
      <label class="facet__legend caps" for="f-q">Search</label>
      <div class="facet__search">${icon("search")}<input class="input" type="search" id="f-q" data-group="q" placeholder="Search the stream" title="Searches titles, summaries, publishers, actors and tags" autocomplete="off" spellcheck="false"><kbd aria-hidden="true">/</kbd></div>
    </div>
    ${group("polarity", "Polarity", ["good", "bad", "mixed"], "polarity")}
    ${group("source", "Failure source", srcs, "source")}
    ${group("op", "Operation", ops, "op")}
    ${group("req", "Requirement", reqs, "req")}
    ${group("kind", "Kind", KINDS, "kind")}
    <div class="facet"><label class="facet__legend caps" for="f-domain">Domain</label><select class="input facet__select" id="f-domain" data-group="domain"><option value="">All domains</option>${DOMAINS.map((d) => `<option value="${d}" data-label="${DOMAIN_LABELS[d] || human(d)}">${DOMAIN_LABELS[d] || human(d)}</option>`).join("")}</select></div>
    <details class="facet facet--more"><summary class="facet__legend caps">More</summary>${group("evidence", "Evidence", EVIDENCE, "plain", EVIDENCE_LABELS)}</details>
    <div class="facet"><label class="facet__legend caps" for="f-sub">Subsection</label><select class="input facet__select" id="f-sub" data-group="sub"><option value="">All subsections</option>${subs}</select></div>
    <fieldset class="facet facet--range"><legend class="facet__legend caps">Date range</legend><div class="facet__row"><label>From<input class="input" type="month" id="f-from" data-group="from" pattern="\\d{4}-\\d{2}" placeholder="YYYY-MM" aria-label="From month"></label><label>To<input class="input" type="month" id="f-to" data-group="to" pattern="\\d{4}-\\d{2}" placeholder="YYYY-MM" aria-label="To month"></label></div></fieldset>
    <fieldset class="facet"><legend class="facet__legend caps">Sort</legend><div class="facet__radios">${radio("sort", "date", "Date", true)}${radio("sort", "verified", "Recently verified")}</div></fieldset>
    <fieldset class="facet"><legend class="facet__legend caps">Density</legend><div class="facet__radios">${radio("density", "full", "Full", true)}${radio("density", "compact", "Compact")}</div></fieldset>`;
  if (!mqSheet.matches) facetsEl.appendChild(pipelineEl);
}
function updateFacets(st, counts) {
  for (const fs of facetsEl.querySelectorAll("fieldset[data-group]")) {
    const g = fs.dataset.group, m = counts[g] || {};
    for (const c of fs.querySelectorAll(".chip--filter")) {
      const id = c.dataset.id, n = m[id] || 0, on = st[g].includes(id);
      c.setAttribute("aria-pressed", String(on));
      c.classList.toggle("is-zero", n === 0 && !on);
      const cnt = c.querySelector(".chip__count"); if (cnt) cnt.textContent = fmtInt(n);
    }
  }
  for (const g of ["domain", "sub"]) {
    const sel = $(`#f-${g}`), m = counts[g] || {};
    if (!sel) continue;
    for (const o of sel.querySelectorAll("option[value]")) if (o.value) o.textContent = `${o.dataset.label} (${fmtInt(m[o.value] || 0)})`;
    sel.value = st[g];
    if (sel.value !== st[g]) sel.value = "";
  }
  const q = $("#f-q"); if (q && q.value !== st.q && document.activeElement !== q) q.value = st.q;
  const from = $("#f-from"), to = $("#f-to");
  if (from && from.value !== st.from) from.value = st.from;
  if (to && to.value !== st.to) to.value = st.to;
  for (const r of facetsEl.querySelectorAll('input[type="radio"]')) r.checked = st[r.name] === r.value;
  const n = activeCount(st);
  toggleLabel.textContent = n ? `Filters (${fmtInt(n)})` : "Filters";
}
function activeChip(g, kind, id, label, prefix) {
  const html = chip({ kind, id, removable: true, label });
  const withPrefix = prefix ? html.replace('<span class="chip__text">', `<span class="chip__prefix">${esc(prefix)} · </span><span class="chip__text">`) : html;
  return `<span class="facets__active-item" data-group="${g}" data-id="${esc(id)}">${withPrefix}</span>`;
}
function renderActive(st) {
  const parts = [];
  for (const id of st.polarity) parts.push(activeChip("polarity", "polarity", id));
  for (const id of st.source) parts.push(activeChip("source", "source", id));
  for (const id of st.op) parts.push(activeChip("op", "op", id));
  for (const id of st.req) parts.push(activeChip("req", "req", id));
  for (const id of st.kind) parts.push(activeChip("kind", "kind", id));
  if (st.domain) parts.push(activeChip("domain", "plain", st.domain, DOMAIN_LABELS[st.domain] || human(st.domain), "Domain"));
  for (const id of st.evidence) parts.push(activeChip("evidence", "plain", id, EVIDENCE_LABELS[id] || human(id), "Evidence"));
  if (st.sub) parts.push(activeChip("sub", st.sub.includes("_") ? "sub" : "section", st.sub));
  if (st.paper) { const p = papersMap && papersMap.get(st.paper); parts.push(activeChip("paper", "plain", st.paper, p ? p.label : st.paper, "Paper")); }
  if (st.from) parts.push(activeChip("from", "plain", st.from, `From ${fmtMonth(st.from)}`));
  if (st.to) parts.push(activeChip("to", "plain", st.to, `To ${fmtMonth(st.to)}`));
  if (st.q) parts.push(activeChip("q", "plain", st.q, `“${st.q}”`));
  activeEl.innerHTML = parts.length ? parts.join("") + `<button type="button" class="btn btn--ghost btn--sm facets__clear">Clear all</button>` : "";
}
function updateResults(st) {
  const total = items.length, n = list.length;
  const filtered = hasFilters(st);
  resultsEl.textContent = !total ? "" : filtered ? `${fmtInt(n)} of ${fmtInt(total)} items match` : `${fmtInt(total)} items`;
  document.title = filtered && total ? `${PAGE_TITLE} · ${fmtInt(n)} of ${fmtInt(total)}` : PAGE_TITLE;
}

/* ---------- chronology strip ---------- */
function renderChronology() {
  const months = allMonths;
  if (!months.length) {
    chronoEl.classList.add("chronology--bare");
    chronoEl.innerHTML = `<svg viewBox="0 0 800 24" preserveAspectRatio="none" role="img" aria-label="No items yet"><line class="chronology__base" x1="0" y1="20" x2="800" y2="20"/></svg>`;
    return;
  }
  chronoEl.classList.remove("chronology--bare");
  const W = Math.max(240, Math.floor(chronoEl.clientWidth) || 800);
  const H = mqSheet.matches ? 56 : 72, area = H - 16, gap = 2, n = months.length;
  const colW = Math.max(6, (W - gap * (n - 1)) / n);
  const total = colW * n + gap * (n - 1);
  const per = {};
  for (const it of list) { const k = monthKey(it.date); const c = per[k] || (per[k] = { bad: 0, mixed: 0, good: 0 }); if (it.polarity in c) c[it.polarity]++; }
  const sum = (c) => c ? c.bad + c.mixed + c.good : 0;
  const max = Math.max(1, ...months.map((m) => sum(per[m])));
  const isJan = (i) => months[i].endsWith("-01");
  const cols = [], labels = [];
  months.forEach((m, i) => {
    const x = i * (colW + gap), c = per[m], t = sum(c);
    let body;
    if (!t) body = `<rect class="chronology__tick" x="${x.toFixed(2)}" y="${area - 2}" width="${colW.toFixed(2)}" height="2"/>`;
    else {
      const h = Math.max(2, Math.round((t / max) * area));
      let y = area; body = "";
      for (const k of ["bad", "mixed", "good"]) {
        if (!c[k]) continue;
        const hk = Math.max(1, Math.round((c[k] / t) * h));
        y -= hk;
        body += `<rect class="chronology__bar" data-polarity="${k}" x="${x.toFixed(2)}" y="${Math.max(0, y)}" width="${colW.toFixed(2)}" height="${hk}"/>`;
      }
    }
    const title = `${fmtMonth(m)} · ${c ? c.bad : 0} bad · ${c ? c.mixed : 0} mixed · ${c ? c.good : 0} good`;
    cols.push(`<a class="chronology__col" href="#${m}" data-month="${m}" tabindex="-1" aria-label="${esc(title)}"><title>${esc(title)}</title><rect class="chronology__hit" x="${x.toFixed(2)}" y="0" width="${colW.toFixed(2)}" height="${area}"/>${body}<rect class="chronology__current" x="${x.toFixed(2)}" y="${area + 1}" width="${colW.toFixed(2)}" height="2"/></a>`);
    const cx = x + colW / 2;
    const anchor = i === 0 ? "start" : i === n - 1 ? "end" : "middle";
    const lx = i === 0 ? x : i === n - 1 ? x + colW : cx;
    if (isJan(i)) labels.push(`<text class="chronology__year" x="${lx.toFixed(2)}" y="${H - 2}" text-anchor="${anchor}">${m.slice(0, 4)}</text>`);
    else if (i === 0) labels.push(`<text class="chronology__year" x="${lx.toFixed(2)}" y="${H - 2}" text-anchor="${anchor}">${fmtMonth(m).slice(0, 3)} ${m.slice(0, 4)}</text>`);
    else if (i % 3 === 0 && !(i > 0 && isJan(i - 1)) && !(i < n - 1 && isJan(i + 1))) labels.push(`<text class="chronology__label" x="${lx.toFixed(2)}" y="${H - 2}" text-anchor="${anchor}">${fmtMonth(m).slice(0, 3)}</text>`);
  });
  const summary = `${fmtInt(list.length)} items from ${fmtMonth(months[0])} to ${fmtMonth(months[n - 1])}`;
  const jump = `<select class="input chronology__jump" id="chronology-jump" aria-label="Jump to month"><option value="">Jump to month</option>${months.slice().reverse().filter((m) => sum(per[m])).map((m) => `<option value="${m}">${fmtMonth(m)} · ${fmtInt(sum(per[m]))}</option>`).join("")}</select>`;
  chronoEl.innerHTML = `<svg viewBox="0 0 ${total.toFixed(2)} ${H}" width="${total.toFixed(2)}" height="${H}" role="group" aria-label="${esc(summary)}"><line class="chronology__base" x1="0" y1="${area + 0.5}" x2="${total.toFixed(2)}" y2="${area + 0.5}"/>${cols.join("")}${labels.join("")}</svg>${jump}`;
  updateCurrentMonth();
}
function setCurrentMonth(key) {
  for (const a of chronoEl.querySelectorAll(".chronology__col")) a.classList.toggle("is-current", a.dataset.month === key);
}
function updateCurrentMonth() {
  if (state && state.sort === "verified") {
    /* heads group by verification month here, the strip by event month: follow the first row at the top of the viewport */
    const rows = [...ledger.querySelectorAll(".ledger__row")];
    const head = ledger.querySelector(".ledger__month");
    const line = 56 + (head ? head.offsetHeight : 48) + 8;   /* the first line of content under the sticky month head */
    const cur = rows.find((r) => r.getBoundingClientRect().top >= line - 24) || rows[rows.length - 1];
    const it = cur && byId.get(cur.dataset.id);
    setCurrentMonth(it ? monthKey(it.date) : null);
    return;
  }
  const heads = Array.from(ledger.querySelectorAll(".ledger__month"));
  if (!heads.length) { setCurrentMonth(null); return; }
  let cur = heads[0];
  /* a head sitting just under the masthead (56 px) owns the rows at the top of the viewport */
  for (const h of heads) { if (h.getBoundingClientRect().top <= 104) cur = h; else break; }
  setCurrentMonth(cur.id);
}
function observeHeads() {
  if (!("IntersectionObserver" in window)) return;
  if (!headIO) headIO = new IntersectionObserver(() => updateCurrentMonth(), { rootMargin: "-56px 0px 0px 0px", threshold: [0, 1] });
  for (const h of ledger.querySelectorAll(".ledger__month:not([data-observed])")) { h.dataset.observed = "1"; headIO.observe(h); }
}

/* ---------- ledger ---------- */
function renderLedger(toIndex) {
  if (headIO) { headIO.disconnect(); headIO = null; }
  ledger.replaceChildren(); rendered = 0; lastMonth = null;
  ledger.classList.toggle("ledger--compact", state.density === "compact");
  stateEl.innerHTML = "";
  if (!items.length) return;
  if (!list.length) {
    ledger.hidden = true; sentinel.hidden = true;
    stateEl.innerHTML = `<div class="empty">Nothing in the ledger matches these filters<div class="empty__actions"><button type="button" class="btn facets__clear">Clear all</button></div></div>`;
    return;
  }
  ledger.hidden = false;
  appendChunk(Math.max(CHUNK, (toIndex ?? -1) + 1 + 8));
}
function appendChunk(n = CHUNK) {
  const end = Math.min(list.length, rendered + n);
  if (end <= rendered) { sentinel.hidden = true; return; }
  const toks = tokens(state.q);
  const groupBy = state.sort === "verified" ? "verified" : "date";
  /* the shared renderer continues the previous chunk: no repeated month head, counts from the whole list */
  const frag = renderLedgerRows(list.slice(rendered, end), { mode: "full", groupBy, startMonth: lastMonth, monthCounts, startIndex: rendered, showNew: showNewDots });
  for (const row of frag.querySelectorAll(".ledger__row")) {
    const it = byId.get(row.dataset.id);
    if (toks.length) applyHighlight(row, toks);
    if (it && expanded.has(it.id)) expandRow(row, it);
  }
  lastMonth = sortKeyOf(list[end - 1]);
  ledger.appendChild(frag);
  rendered = end;
  sentinel.hidden = rendered >= list.length;
  observeHeads();
}
function ensureRendered(index) { if (index >= rendered) appendChunk(index - rendered + 1 + 8); }

function renderExtra(it) {
  const a = it.actors || {};
  const actors = [a.vendor && `${a.vendor} (vendor)`, a.deployer && `${a.deployer} (deployer)`, a.model && `${a.model} (model)`].filter(Boolean).join(", ");
  const source = [it.publisher, EVIDENCE_LABELS[it.evidence] || human(it.evidence), DOMAIN_LABELS[it.domain] || human(it.domain), actors].filter(Boolean).map(esc).join(" · ");
  const also = (it.also_urls || []).length ? `<p class="ledger__source">Also reported by ${it.also_urls.map((u) => `<a class="ext" href="${esc(u)}" rel="noopener" target="_blank">${esc(hostOf(u))}${icon("arrow-up-right", "icon icon--ext")}</a>`).join(", ")}</p>` : "";
  const related = (it.related_papers || []).length ? `<div class="ledger__related"><span class="ledger__extra-label caps">Related papers</span>${it.related_papers.map((k) => paperChip(k)).join("")}</div>` : "";
  const by = String(it.added_by || "").replace(/-/g, " ");
  const note = String(it.verification_note || "").trim();
  const first = firstSentence(note);
  const noteHTML = !note ? "" : first.length >= note.length - 1 ? `<p class="ledger__note">${esc(note)}</p>`
    : `<details class="ledger__note"><summary><span class="ledger__note-first">${esc(first)}</span><span class="ledger__note-more">Show full note</span><span class="ledger__note-less">Hide full note</span></summary><p>${esc(note)}</p></details>`;
  const verified = `<p class="ledger__verified" data-c="verified">${icon("check", "icon icon--s")}<span>verified ${esc(fmtDateLong(it.verified_on))}${by ? ` · ${esc(by)}` : ""}</span>${it.needs_review ? '<span class="ledger__pending caps">Review pending</span>' : ""}</p>${noteHTML}`;
  const tags = (it.tags || []).length ? `<p class="ledger__tags">${it.tags.map(esc).join(" · ")}</p>` : "";
  const actions = `<div class="ledger__actions"><button type="button" class="btn btn--sm" data-copy="${esc(it.id)}">${icon("link", "icon icon--s")} Copy link</button><a class="btn btn--sm" href="${esc(reportUrl(it.id))}" target="_blank" rel="noopener">${icon("flag", "icon icon--s")} Report a problem</a></div>`;
  return `<p class="ledger__source">${source}</p>${also}${related}${verified}${tags}${actions}`;
}
function paperChip(key) {
  const p = papersMap && papersMap.get(key);
  const href = linkTo("papers", { hash: "paper/" + key });
  if (p) return `<a class="chip chip--sub ledger__paper" data-section="${esc(p.section)}" data-key="${esc(key)}" href="${esc(href)}" title="${esc(p.title)}"><span class="chip__text">${esc(p.label || p.title)}</span></a>`;
  return `<a class="chip chip--sub ledger__paper" data-key="${esc(key)}" href="${esc(href)}"><span class="chip__text mono">${esc(key)}</span></a>`;
}
function fillPapers(root = ledger) {
  if (!papersMap) return;
  for (const a of root.querySelectorAll(".ledger__paper[data-key]")) {
    const p = papersMap.get(a.dataset.key);
    if (!p) continue;
    a.setAttribute("data-section", p.section); a.setAttribute("title", p.title);
    const t = a.querySelector(".chip__text"); t.classList.remove("mono"); t.textContent = p.label || p.title;
  }
}
function loadPapers() {
  if (papersMap) return Promise.resolve(papersMap);
  if (papersFailed) return Promise.resolve(null);
  if (!papersPromise) {
    papersPromise = fetchJSON("data/papers.json", { version: dataVersion() })
      .then((arr) => { papersMap = new Map((arr || []).map((p) => [p.key, p])); return papersMap; })
      .catch(() => { papersFailed = true; papersPromise = null; return null; });
  }
  return papersPromise;
}
function expandRow(row, it) {
  if (!row) return;
  it = it || byId.get(row.dataset.id);
  row.classList.add("is-expanded"); expanded.add(row.dataset.id);
  const more = row.querySelector(".ledger__more");
  if (more) { more.setAttribute("aria-expanded", "true"); more.setAttribute("aria-label", "Less about this item"); }
  const extra = row.querySelector(".ledger__extra");
  if (extra && !extra.dataset.filled && it) { extra.innerHTML = renderExtra(it); extra.dataset.filled = "1"; }
  if (extra) extra.hidden = false;
  if (!papersMap && it && (it.related_papers || []).length) loadPapers().then(() => fillPapers(row));
}
function collapseRow(row) {
  if (!row) return;
  row.classList.remove("is-expanded"); expanded.delete(row.dataset.id);
  const more = row.querySelector(".ledger__more");
  if (more) { more.setAttribute("aria-expanded", "false"); more.setAttribute("aria-label", "More about this item"); }
  const extra = row.querySelector(".ledger__extra"); if (extra) extra.hidden = true;
}
function scrollToEl(target) {
  /* Instant, then corrected over two frames: rows above the target are content-visibility placeholders that
     expand as they become relevant, which would leave a smooth scroll short of the target. */
  const go = () => target.scrollIntoView({ block: "start", behavior: "auto" });
  go();
  requestAnimationFrame(() => { go(); requestAnimationFrame(go); });
  setTimeout(() => { go(); updateCurrentMonth(); }, 160);
}
function flash(row) {
  if (reducedMotion()) return;
  row.classList.remove("is-flash"); void row.offsetWidth; row.classList.add("is-flash");
  setTimeout(() => row.classList.remove("is-flash"), 1000);
}

/* ---------- hash entities: #item/<id> and #YYYY-MM ---------- */
function applyHash() {
  const h = state.hash;
  if (!h || !items.length) return;
  if (h.startsWith("item/")) {
    const id = h.slice(5);
    const idx = list.findIndex((it) => it.id === id);
    if (idx < 0) { if (byId.has(id) && hasFilters(state)) clearFilters(); return; }
    ensureRendered(idx);
    const row = document.getElementById("item-" + id);
    if (!row) return;
    expandRow(row, list[idx]);
    scrollToEl(row); flash(row);
  } else if (/^\d{4}-\d{2}$/.test(h)) {
    const t = monthTarget(h);
    if (!t) return;
    ensureRendered(t.idx);
    const head = document.getElementById(t.id);
    if (head) { scrollToEl(head); setCurrentMonth(h); }
  }
}
/** #YYYY-MM resolves to the month head in date sort; in "Recently verified" sort the heads group by verification month,
    so the strip's event month lands on the first row whose event date falls in that month. */
function monthTarget(h) {
  let idx = list.findIndex((it) => sortKeyOf(it) === h);
  if (idx >= 0) return { idx, id: h };
  if (state.sort === "verified") {
    idx = list.findIndex((it) => monthKey(it.date) === h);
    if (idx >= 0) return { idx, id: "item-" + list[idx].id };
  }
  return null;
}

/* ---------- render ---------- */
function render({ force = false } = {}) {
  state = parseState();
  if (state.paper && !papersMap && !papersFailed) loadPapers().then((m) => { if (m) render({ force: true }); });
  const sig = signature(state);
  if (!force && sig === lastSignature) { applyHash(); return; }
  lastSignature = sig;
  const toks = tokens(state.q);
  list = items.filter((it) => matches(it, state, null, toks)).sort(compare);
  monthCounts = {};
  for (const it of list) { const k = sortKeyOf(it); monthCounts[k] = (monthCounts[k] || 0) + 1; }
  updateFacets(state, facetCounts(state, toks));
  renderActive(state);
  updateResults(state);
  renderChronology();
  let target = -1;
  if (state.hash.startsWith("item/")) target = list.findIndex((it) => it.id === state.hash.slice(5));
  else if (/^\d{4}-\d{2}$/.test(state.hash)) { const t = monthTarget(state.hash); target = t ? t.idx : -1; }
  renderLedger(target);
  applyHash();
}

/* ---------- states ---------- */
function showSkeleton() {
  ledger.hidden = true; sentinel.hidden = true;
  stateEl.innerHTML = `<div class="stream__skeleton" aria-hidden="true"><div class="skeleton__row"></div><div class="skeleton__row"></div><div class="skeleton__row"></div></div>`;
}
function renderNoStream() {
  items = []; list = []; allMonths = [];
  setLive(null);
  $("#stream-sources").textContent = "No items yet";
  $("#download").hidden = true;
  facetsEl.setAttribute("aria-disabled", "true");
  for (const x of facetsEl.querySelectorAll("input, select, button")) x.disabled = true;
  toggleBtn.setAttribute("aria-disabled", "true"); toggleBtn.disabled = true;
  renderChronology();
  resultsEl.textContent = "";
  ledger.hidden = true; sentinel.hidden = true; activeEl.innerHTML = "";
  stateEl.innerHTML = `<div class="empty">The ledger opens with the first verified sweep.<div class="empty__actions"><a class="btn btn--arrow" href="${ISSUE_URL}" target="_blank" rel="noopener">Submit an item ${icon("arrow-up-right")}</a></div></div>`;
  $("#pipeline-counts").textContent = "0 items · 0 seed sweep · 0 collector · 0 reader submissions";
  document.title = PAGE_TITLE;
}
function renderError() {
  ledger.hidden = true; sentinel.hidden = true;
  setLive(null, "The stream could not be loaded");
  $("#stream-sources").textContent = `${fmtInt((stats && stats.stream_items) || 0)} items · not loaded`;
  $("#download").hidden = true;
  stateEl.innerHTML = `<div class="error" role="alert">The stream could not be loaded.<div class="error__retry"><button type="button" class="btn" id="retry">Retry</button></div></div>`;
  $("#retry").addEventListener("click", () => load());
}
function fillHeader() {
  const n = items.length;
  const sources = Array.isArray(stream.sources) && stream.sources.length ? stream.sources.join(", ") : "seed sweep";
  $("#stream-sources").innerHTML = `${fmtInt(n)} items · sources: ${esc(sources)}`;
  $("#download").hidden = false;
  let seed = 0, collector = 0, reader = 0;
  for (const it of items) { const by = String(it.added_by || ""); if (by.startsWith("seed")) seed++; else if (by === "collector") collector++; else reader++; }
  $("#pipeline-counts").textContent = `${fmtInt(n)} items · ${fmtInt(seed)} seed sweep · ${fmtInt(collector)} collector · ${fmtInt(reader)} reader submissions`;
  setLive(stream.generated || (stats && stats.stream_updated));
}

/* ---------- loading ---------- */
async function load() {
  showSkeleton();
  try {
    stream = stats ? await loadStream(stats) : await fetchJSON("data/stream.json", { version: dataVersion() });
  } catch (e) { renderError(); return; }
  if (!stream || !Array.isArray(stream.items) || !stream.items.length) { renderNoStream(); return; }
  items = stream.items.filter((it) => it && it.id && it.date);
  byId = new Map(items.map((it) => [it.id, it]));
  showNewDots = items.filter((it) => withinDays(it.verified_on, 7)).length * 2 <= items.length;
  const first = items.reduce((m, it) => (monthKey(it.date) < m ? monthKey(it.date) : m), monthKey(items[0].date));
  const now = currentMonthUTC();
  const last = items.reduce((m, it) => (monthKey(it.date) > m ? monthKey(it.date) : m), now);
  allMonths = monthsBetween(first, last);
  fillHeader();
  lastSignature = null;
  render({ force: true });
}

/* ---------- sheet (below 1024) ---------- */
function setInert(on) {
  /* the sheet is modal: the rest of the page is inert while it is open */
  for (const el of document.querySelectorAll(".masthead, .colophon, .stream__head, #stream-main")) el.inert = on;
}
function openSheet() {
  facetsEl.classList.add("is-open"); toggleBtn.setAttribute("aria-expanded", "true"); scrim.hidden = false;
  document.body.classList.add("stream--sheet-open");
  setInert(true);
  const first = facetsEl.querySelector("input, select, button:not(.facets__close)");
  if (first) first.focus({ preventScroll: true });
}
function closeSheet({ refocus = true } = {}) {
  if (!facetsEl.classList.contains("is-open")) return;
  facetsEl.classList.remove("is-open"); toggleBtn.setAttribute("aria-expanded", "false"); scrim.hidden = true;
  document.body.classList.remove("stream--sheet-open");
  setInert(false);
  if (refocus) toggleBtn.focus();
}
function placePipeline() {
  if (mqSheet.matches) { if (pipelineEl.parentElement !== mainEl) mainEl.appendChild(pipelineEl); }
  else { closeSheet({ refocus: false }); if (pipelineEl.parentElement !== facetsEl) facetsEl.appendChild(pipelineEl); }
}

/* ---------- events ---------- */
function visibleFacetChip(group, id) {
  const c = facetsEl.querySelector(`fieldset[data-group="${group}"] .chip--filter[data-id="${CSS.escape(id)}"]`);
  return c && c.offsetParent ? c : null;
}
function wire() {
  facetsEl.addEventListener("click", (e) => {
    const c = e.target.closest(".chip--filter");
    if (c) { const fs = c.closest("[data-group]"); if (fs) setMulti(fs.dataset.group, c.dataset.id); return; }
    if (e.target.closest(".facets__close")) closeSheet();
  });
  facetsEl.addEventListener("change", (e) => {
    const t = e.target;
    if (t.matches("select[data-group]")) setSingle(t.dataset.group, t.value);
    else if (t.matches('input[type="month"][data-group]')) { if (!t.value || /^\d{4}-\d{2}$/.test(t.value)) setSingle(t.dataset.group, t.value); }
    else if (t.matches('input[type="radio"][name="sort"]')) { writeState({ sort: t.value === "verified" ? "verified" : null }); render(); }
    else if (t.matches('input[type="radio"][name="density"]')) { writeState({ density: t.value === "compact" ? "compact" : null }); render(); }
  });
  const q = $("#f-q");
  const onSearch = debounce(() => { writeState({ q: q.value.trim() || null }); render(); }, 150);
  q.addEventListener("input", onSearch);
  q.addEventListener("keydown", (e) => { if (e.key === "Escape") { e.preventDefault(); onSearch.cancel(); q.value = ""; writeState({ q: null }); render(); q.blur(); } });
  q.addEventListener("search", () => { onSearch.cancel(); writeState({ q: q.value.trim() || null }); render(); });

  activeEl.addEventListener("click", (e) => {
    const x = e.target.closest("[data-remove]");
    if (x) {
      const item = x.closest(".facets__active-item"), g = item.dataset.group, id = item.dataset.id;
      const idx = [...activeEl.querySelectorAll("[data-remove]")].indexOf(x);
      if (MULTI.includes(g)) setMulti(g, id, false); else setSingle(g, "");
      /* the row was rebuilt: focus the next removable chip, else Clear all, else the matching facet chip or the Filters button */
      const xs = activeEl.querySelectorAll("[data-remove]");
      const t = xs[Math.min(idx, xs.length - 1)] || activeEl.querySelector(".facets__clear") || visibleFacetChip(g, id) || (toggleBtn.offsetParent ? toggleBtn : $("#f-q"));
      if (t) t.focus({ preventScroll: true });
      return;
    }
    if (e.target.closest(".facets__clear")) { clearFilters(); (toggleBtn.offsetParent ? toggleBtn : $("#f-q")).focus({ preventScroll: true }); }
  });
  stateEl.addEventListener("click", (e) => { if (e.target.closest(".facets__clear")) clearFilters(); });

  ledger.addEventListener("click", (e) => {
    const more = e.target.closest(".ledger__more");
    if (more) { const row = more.closest(".ledger__row"); if (row.classList.contains("is-expanded")) collapseRow(row); else expandRow(row); return; }
    const copy = e.target.closest("[data-copy]");
    if (copy) { copyText(itemUrl(copy.dataset.copy), "Link copied"); return; }
    const c = e.target.closest(".chip--filter[data-kind][data-id]");
    if (c) {
      const g = c.dataset.kind === "source" ? "source" : c.dataset.kind === "op" ? "op" : null;
      if (g) {
        setMulti(g, c.dataset.id, true);
        const top = mainEl.getBoundingClientRect().top + window.scrollY - 72;
        if (window.scrollY > top) window.scrollTo({ top, behavior: reducedMotion() ? "auto" : "smooth" });
        (visibleFacetChip(g, c.dataset.id) || resultsEl).focus({ preventScroll: true });
      }
    }
  });
  ledger.addEventListener("keydown", (e) => {
    if (e.key !== "Escape") return;
    if (e.target.matches("input, select, textarea")) return;
    const row = e.target.closest(".ledger__row.is-expanded");
    if (row) { e.preventDefault(); collapseRow(row); const more = row.querySelector(".ledger__more"); if (more) more.focus(); }
  });

  chronoEl.addEventListener("click", (e) => {
    const a = e.target.closest("a.chronology__col");
    if (!a) return;
    e.preventDefault();
    writeState({ hash: a.dataset.month }); state.hash = a.dataset.month; applyHash();
  });
  chronoEl.addEventListener("change", (e) => {
    const sel = e.target.closest(".chronology__jump");
    if (!sel || !sel.value) return;
    writeState({ hash: sel.value }); state.hash = sel.value; applyHash(); sel.value = "";
  });

  toggleBtn.addEventListener("click", () => { if (facetsEl.classList.contains("is-open")) closeSheet(); else openSheet(); });
  scrim.addEventListener("click", () => closeSheet());
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && facetsEl.classList.contains("is-open")) { closeSheet(); return; }
    if (e.key === "/" && !e.ctrlKey && !e.metaKey && !e.altKey && !e.target.matches("input, select, textarea, [contenteditable]")) {
      e.preventDefault();
      if (mqSheet.matches && !facetsEl.classList.contains("is-open")) openSheet();
      $("#f-q").focus(); $("#f-q").select();
    }
  });
  mqSheet.addEventListener("change", () => { placePipeline(); if (items.length) renderChronology(); });
  mqPhone.addEventListener("change", () => { if (items.length) renderChronology(); });
  if ("ResizeObserver" in window) {
    let lastW = 0;
    const onResize = debounce(() => { const w = Math.floor(chronoEl.clientWidth); if (w && w !== lastW) { lastW = w; if (items.length) renderChronology(); } }, 80);
    resizeRO = new ResizeObserver(onResize); resizeRO.observe(chronoEl);
  }
  if ("IntersectionObserver" in window) {
    sentinelIO = new IntersectionObserver((entries) => { if (entries.some((x) => x.isIntersecting) && !sentinel.hidden) appendChunk(); }, { rootMargin: "800px 0px" });
    sentinelIO.observe(sentinel);
  } else {
    window.addEventListener("scroll", () => { if (!sentinel.hidden && sentinel.getBoundingClientRect().top < innerHeight + 800) appendChunk(); }, { passive: true });
  }
  window.addEventListener("scroll", () => { if (items.length) requestAnimationFrame(updateCurrentMonth); }, { passive: true });
  window.addEventListener("popstate", () => { if (items.length) render(); });
}

/* ---------- boot ---------- */
const [s, t] = await Promise.all([initPage(), T.loadTaxonomy().catch(() => null)]);
stats = s; tax = t;
if (tax) bindStats(stats || {}, { taxonomy: tax });
buildFacets();
placePipeline();
wire();
setLive(stats && stats.stream_updated);
state = parseState();
if (stats && !(stats.stream_items > 0)) renderNoStream();
else load();
