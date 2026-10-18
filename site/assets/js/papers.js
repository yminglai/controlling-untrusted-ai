/* papers.js: the paper collection page (design/DESIGN.md section 5, design/IMPLEMENTATION_NOTES.md).
   Renders the rail, filter bar, section and subsection heads and cards from taxonomy.json, papers.json and
   grey.json; search via search.js; the detail drawer with cross-references, stream items and the Chinese
   reading notes (summaries_zh.json, loaded on first need). Hash: #s5, #s5_3, #paper/<key>, #grey/<key>;
   the forms #sec=s5, #sub=s5_3, #paper=<key>, #grey=<key>, #q=<text> are accepted and normalised. */
import {
  initPage, bindStats, readState, writeState, linkTo, fetchJSON, dataVersion, loadStream,
  esc, icon, el, fmtInt, fmtDate, authorsLine, chip, openDrawer, closeDrawer, debounce, onIdle, idleChunks,
  copyText, reducedMotion, POLARITY_LABELS
} from "./common.js";
import * as T from "./taxonomy.js";
import { createIndex, addToIndex, search, highlight } from "./search.js";

const $ = (s, r = document) => r.querySelector(s);
const SITE_TITLE = "Controlling Untrusted AI";
const CHUNK = 24;
const SUB_RE = /^s\d{1,2}_\d{1,2}$/, SEC_RE = /^s\d{1,2}$/;
const DEPTH_HINT = { "全文": "read in full", "部分": "read in part", "仅摘要": "abstract only", "仅题录": "metadata only" };
const NOTE_FIELDS = [
  ["positioning", "定位", "Positioning"], ["problem", "问题", "Problem"], ["method", "方法", "Method"],
  ["findings", "发现", "Findings"], ["deployer_takeaway", "部署启示", "Deployer takeaway"], ["limitations", "局限", "Limitations"],
  ["relation_to_subsection", "与小节关系", "Relation to this subsection"], ["doubts", "存疑", "Doubts"], ["terms", "术语", "Terms"]
];
const PAPER_FIELDS = [
  { name: "label", weight: 8 }, { name: "title", weight: 4 }, { name: "authors", weight: 2, get: (p) => (p.authors || []).join(" ") },
  { name: "one_line", weight: 1 }, { name: "reason", weight: 1 }, { name: "key", weight: 1 }, { name: "arxiv_id", weight: 1 },
  { name: "year", weight: 1, get: (p) => String(p.year || "") }
];
const GREY_FIELDS = [
  { name: "label", weight: 8 }, { name: "title", weight: 4 }, { name: "authors", weight: 2, get: (g) => (g.authors || []).join(" ") },
  { name: "venue", weight: 1 }, { name: "one_line", weight: 1 }, { name: "key", weight: 1 }
];
const YEAR_CHIPS = [["2026", "2026"], ["2025", "2025"], ["2024", "2024"], ["2023", "2023"], ["le2022", "2022 and earlier"]];

/* ---------- state ---------- */
const S = {
  stats: null, tax: null,
  papers: [], grey: [], loaded: false, loadError: false,
  byKey: new Map(), greyByKey: new Map(), primaryOf: new Map(), greyOf: new Map(), crossOf: new Map(),
  index: null, greyIndex: null, indexComplete: false, hitsQ: null, hits: null,
  zh: null, zhKeys: null, zhPromise: null,
  stream: null, streamBySub: null,
  view: null, r: null, io: null, sentinel: null,
  noWiden: false, drawerKey: null, firstRender: true, lastRoute: "", stickyH: 112, pendingFocus: null
};
const dom = {};

/* ---------- small helpers ---------- */
const plural = (n, one, many = one + "s") => `${fmtInt(n)} ${n === 1 ? one : many}`;
function push(map, k, v) { const a = map.get(k); if (a) a.push(v); else map.set(k, [v]); }
function queryState() { const st = readState(); delete st.hash; return st; }
function hrefFor(hash, patch = {}) { return linkTo("papers", { ...queryState(), ...patch, hash }); }
function hostOf(url) { try { return new URL(url).hostname.replace(/^www\./, ""); } catch (e) { return ""; } }
function sectionIdOf(item) { return item.section || (T.sectionOf(item.primary) || {}).id || "s1"; }
function hasZh(kind, item) { return !!(item.has_zh || (S.zhKeys && S.zhKeys.has(item.key))); }
function yearMatch(y, years) { return years.has(String(y)) || (years.has("le2022") && y <= 2022); }

/* ---------- route and filters ---------- */
function parseRoute(raw) {
  let h = raw || "";
  if (/^(sec|sub|paper|grey|q)=/.test(h)) {
    const p = new URLSearchParams(h);
    let hash = "";
    if (p.get("paper")) hash = "paper/" + p.get("paper");
    else if (p.get("grey")) hash = "grey/" + p.get("grey");
    else if (p.get("sub")) hash = p.get("sub");
    else if (p.get("sec")) hash = p.get("sec");
    const patch = { hash };
    if (p.get("q")) patch.q = p.get("q");
    writeState(patch);
    h = hash;
  }
  if (h.startsWith("paper/")) return { kind: "entity", type: "paper", key: h.slice(6) };
  if (h.startsWith("grey/")) return { kind: "entity", type: "grey", key: h.slice(5) };
  if (SUB_RE.test(h) && T.subsectionById(h)) return { kind: "sub", id: h };
  if (SEC_RE.test(h) && T.sectionOf(h)) return { kind: "sec", id: h };
  return { kind: "none" };
}
function readFilters() {
  const st = readState();
  return {
    q: String(st.q || "").trim(),
    cited: st.cited === "1", score3: st.score === "3", zh: st.zh === "1", grey: st.grey !== "0",
    years: new Set(String(st.years || "").split(",").filter((y) => YEAR_CHIPS.some((c) => c[0] === y))),
    sort: st.sort === "year" || st.sort === "title" ? st.sort : "survey",
    density: st.density === "compact" ? "compact" : "full",
    scope: st.scope === "sub" || st.scope === "sec" || st.scope === "all" ? st.scope : null
  };
}
function activeFilterCount(f) {
  return (f.q.length >= 2 ? 1 : 0) + (f.cited ? 1 : 0) + (f.score3 ? 1 : 0) + (f.zh ? 1 : 0) + (f.grey ? 0 : 1) + f.years.size;
}

/* ---------- data ---------- */
function indexData(papers, grey) {
  S.papers = papers; S.grey = grey;
  papers.forEach((p, i) => {
    p._i = i; S.byKey.set(p.key, p); push(S.primaryOf, p.primary, p);
    for (const a of p.also || []) push(S.crossOf, a.sid, { paper: p, score: a.score, kind: "paper" });
  });
  grey.forEach((g, i) => {
    g._i = i; S.greyByKey.set(g.key, g); push(S.greyOf, g.primary, g);
    for (const a of g.also || []) push(S.crossOf, a.sid, { paper: g, score: a.score, kind: "grey" });
  });
}
async function loadPapers() {
  S.loadError = false;
  try {
    const v = dataVersion();
    const [papers, grey] = await Promise.all([
      fetchJSON("data/papers.json", { version: v }),
      fetchJSON("data/grey.json", { version: v }).catch(() => [])
    ]);
    indexData(Array.isArray(papers) ? papers : [], Array.isArray(grey) ? grey : []);
    S.loaded = true; S.view = null;
    route();
    onIdle(() => buildSearchIndex());
    onIdle(() => loadStreamCounts(), 3000);
  } catch (e) {
    S.loadError = true; S.view = null;
    route();
  }
}
function buildSearchIndex() {
  if (S.index) return;
  S.index = createIndex(PAPER_FIELDS); S.greyIndex = createIndex(GREY_FIELDS);
  idleChunks(S.papers, 200, (slice) => { if (!S.indexComplete) addToIndex(S.index, slice); })
    .then(() => { if (!S.indexComplete) { addToIndex(S.greyIndex, S.grey); S.indexComplete = true; } });
}
function ensureIndex() {
  if (S.indexComplete) return;
  if (!S.index) { S.index = createIndex(PAPER_FIELDS); S.greyIndex = createIndex(GREY_FIELDS); }
  addToIndex(S.index, S.papers.slice(S.index.docs.length));
  if (!S.greyIndex.docs.length) addToIndex(S.greyIndex, S.grey);
  S.indexComplete = true;
}
function hitsFor(q) {
  if (S.hitsQ === q) return S.hits;
  ensureIndex();
  const a = search(S.index, q), b = search(S.greyIndex, q);
  S.hitsQ = q;
  S.hits = a ? { tokens: a.tokens, paper: new Map(a.results.map((x) => [x.item.key, x.score])), grey: new Map((b ? b.results : []).map((x) => [x.item.key, x.score])) } : null;
  return S.hits;
}
function loadNotesFile() {
  if (!S.zhPromise) {
    S.zhPromise = fetchJSON("data/summaries_zh.json", { version: dataVersion() }).then((z) => {
      S.zh = z && typeof z === "object" ? z : {};
      S.zhKeys = new Set(Object.keys(S.zh));
      return S.zh;
    });
    S.zhPromise.catch(() => { S.zhPromise = null; });
  }
  return S.zhPromise;
}
async function loadStreamCounts() {
  try {
    const stream = await loadStream(S.stats);
    if (!stream || !Array.isArray(stream.items)) return;
    S.stream = stream;
    S.streamBySub = T.streamCounts(stream.items).subs;
    fillStreamLinks(document);
    if (S.drawerKey && dom.drawer.open) {
      const [kind, key] = S.drawerKey.split(":");
      const item = kind === "grey" ? S.greyByKey.get(key) : S.byKey.get(key);
      const slot = $("#drawer-stream");
      if (item && slot) slot.innerHTML = streamHTML(kind, item);
    }
  } catch (e) { /* the stream is optional here */ }
}
function fillStreamLinks(root) {
  if (!S.streamBySub) return;
  for (const a of root.querySelectorAll("[data-stream-sub]")) {
    const n = S.streamBySub[a.dataset.streamSub] || 0;
    if (n > 0) { a.textContent = `${plural(n, "item")} in the stream`; a.hidden = false; }
  }
}
function streamItemsFor(kind, item) {
  if (!S.stream) return [];
  const key = item.key, home = item.primary;
  return S.stream.items.filter((it) => (it.related_papers || []).includes(key) || (it.subsections || []).includes(home));
}

/* ---------- matching ---------- */
function matchPaper(p, f, hits, skip = "") {
  if (skip !== "cited" && f.cited && !p.selected) return false;
  if (skip !== "score" && f.score3 && !(p.score >= 3)) return false;
  if (skip !== "zh" && f.zh && !hasZh("paper", p)) return false;
  if (skip !== "years" && f.years.size && !yearMatch(p.year, f.years)) return false;
  if (hits && !hits.paper.has(p.key)) return false;
  return true;
}
function matchGrey(g, f, hits, skip = "") {
  if (skip !== "grey" && !f.grey) return false;
  if (skip !== "cited" && f.cited && !g.selected) return false;
  if (skip !== "score" && f.score3) return false;
  if (skip !== "zh" && f.zh && !hasZh("grey", g)) return false;
  if (skip !== "years" && f.years.size && !yearMatch(g.year, f.years)) return false;
  if (hits && !hits.grey.has(g.key)) return false;
  return true;
}
function sortItems(list, f, hits, scoreOf) {
  const out = list.slice();
  if (f.sort === "year") out.sort((a, b) => (b.year || 0) - (a.year || 0) || a._i - b._i);
  else if (f.sort === "title") out.sort((a, b) => String(a.title).localeCompare(String(b.title)) || a._i - b._i);
  else if (hits) out.sort((a, b) => (scoreOf(b) || 0) - (scoreOf(a) || 0) || a._i - b._i);
  return out;
}
/** computeCounts(f, hits) -> per-subsection filtered lists and corpus totals (papers and reports in file order). */
function computeCounts(f, hits) {
  const subs = {};
  let corpus = 0, corpusGrey = 0;
  for (const s of T.sections) for (const ss of s.subsections) {
    const prim = (S.primaryOf.get(ss.id) || []).filter((p) => matchPaper(p, f, hits));
    const greys = (S.greyOf.get(ss.id) || []).filter((g) => matchGrey(g, f, hits));
    const cross = (S.crossOf.get(ss.id) || []).filter((x) => (x.kind === "grey" ? matchGrey(x.paper, f, hits) : matchPaper(x.paper, f, hits)));
    const cited = (S.primaryOf.get(ss.id) || []).filter((p) => p.selected).length;
    const citedGrey = (S.greyOf.get(ss.id) || []).filter((g) => g.selected).length;
    /* cited: primary papers only (the subsection head, SCHEMA counts.selected); citedAll: papers and reports (the results head, the chip) */
    subs[ss.id] = { prim, greys, cross, primTotal: (S.primaryOf.get(ss.id) || []).length, greyTotal: (S.greyOf.get(ss.id) || []).length, crossTotal: (S.crossOf.get(ss.id) || []).length, cited, citedAll: cited + citedGrey };
    corpus += prim.length; corpusGrey += greys.length;
  }
  return { subs, corpus, corpusGrey };
}

/* ---------- view ---------- */
function computeView(r, f) {
  let target = null, def = "all", routeKind = r.kind;
  if (r.kind === "sub") { target = r.id; def = "sub"; }
  else if (r.kind === "sec") { target = r.id; def = "sec"; }
  else if (r.kind === "entity" && r.item) { target = r.item.primary; def = "sub"; routeKind = "sub"; }
  let scope = f.scope || def;
  if (scope === "sub" && !(target && SUB_RE.test(target))) scope = target ? "sec" : "all";
  if (scope === "sec" && !target) scope = "all";
  const sec = target ? T.sectionOf(target) : null;
  const q = f.q.length >= 2 ? f.q : "";
  const hits = S.loaded && q ? hitsFor(q) : null;
  const anyPaperFilter = !!(q || f.cited || f.score3 || f.zh || f.years.size);
  const active = anyPaperFilter || !f.grey;
  const counts = S.loaded ? computeCounts(f, hits) : null;
  const subsOfScope = (s, sc) => (sc === "sub" ? s.subsections.filter((ss) => ss.id === target) : s.subsections);
  let secs = scope === "all" ? T.sections : [sec];
  let scopedTotal = 0, scopedPrim = 0, scopedGrey = 0, scopedGreyTotal = 0, scopedCited = 0, scopedCross = 0;
  if (counts) for (const s of secs) for (const ss of subsOfScope(s, scope)) {
    const c = counts.subs[ss.id];
    scopedTotal += c.prim.length; scopedPrim += c.primTotal; scopedGrey += c.greys.length; scopedGreyTotal += c.greyTotal; scopedCited += c.citedAll; scopedCross += c.cross.length;
  }
  let widened = false;
  if (counts && q && scope !== "all" && !S.noWiden && scopedTotal + scopedGrey < 3 && counts.corpus + counts.corpusGrey > scopedTotal + scopedGrey) {
    widened = true; secs = T.sections;
  }
  const eff = widened ? "all" : scope;
  const key = JSON.stringify([eff, target, widened, q, f.cited, f.score3, f.zh, f.grey, [...f.years].sort(), f.sort, f.density, S.loaded, S.loadError, S.zhKeys ? 1 : 0]);
  return {
    routeKind, scope, eff, def, target, sec, secs, f, q, hits, active, anyPaperFilter, counts, widened, key,
    subsOf: (s) => subsOfScope(s, eff),
    scoped: { match: scopedTotal, prim: scopedPrim, grey: scopedGrey, greyTotal: scopedGreyTotal, cited: scopedCited, cross: scopedCross },
    items: []
  };
}
function scopeName(v) {
  if (v.eff === "all") return "the whole corpus";
  return T.fullTitle(v.target.includes("_") && v.eff === "sec" ? v.sec.id : v.target);
}
function resultsHeadHTML(v) {
  if (S.loadError) return "The paper list could not be loaded.";
  if (!S.loaded) return "Loading the paper list.";
  const sn = esc(scopeName(v));
  const sc = v.scoped;
  if (!v.active) return `${plural(sc.prim, "paper")} in ${sn} · ${fmtInt(sc.cited)} cited in the PDF · ${plural(sc.greyTotal, "report")}`;
  let s = v.anyPaperFilter ? `${fmtInt(sc.match)} of ${plural(sc.prim, "paper")} match in ${sn}` : `${plural(sc.prim, "paper")} in ${sn}`;
  if (sc.grey) s += ` · ${plural(sc.grey, "report")}`;
  if (sc.cross && v.anyPaperFilter) s += ` · ${fmtInt(sc.cross)} cross-referenced`;
  const corpus = v.counts.corpus + v.counts.corpusGrey;
  if (v.widened) {
    const n = sc.match + sc.grey;
    const inner = n === 0 ? `No matches in ${esc(T.fullTitle(v.target))}` : `Only ${plural(n, "match", "matches")} in ${esc(T.fullTitle(v.target))}`;
    s = `${inner}; showing ${plural(corpus, "match", "matches")} in the whole corpus <button type="button" class="chip chip--plain filterbar__within" data-within="1">${icon("x", "icon icon--s")}<span class="chip__text">within ${esc(T.numberOf(v.target))} only</span></button>`;
  } else if (v.scope !== "all" && v.anyPaperFilter && corpus > sc.match + sc.grey) {
    s += ` · <a href="${esc(hrefFor(v.target, { scope: "all" }))}" data-scope-all="1">Also ${plural(corpus, "match", "matches")} in the whole corpus</a>`;
  }
  return s;
}

/* ---------- rail ---------- */
function renderRail() {
  dom.rail.innerHTML = `<ul class="rail__list">${T.sections.map((sec) => `
    <li class="rail__section" data-section="${sec.id}" data-sec="${sec.id}">
      <div class="rail__row">
        <a class="rail__link" href="${esc(hrefFor(sec.id))}" data-rail-item data-id="${sec.id}" data-hash="${sec.id}" tabindex="-1"><span class="rail__num num">§${sec.number}</span><span class="rail__title">${esc(sec.title)}</span></a>
        <span class="rail__count num" data-count="${sec.id}">${fmtInt(T.primaryCount(sec))}</span>
        <button type="button" class="rail__chevron" aria-expanded="false" aria-controls="rail-subs-${sec.id}" aria-label="Show the subsections of §${sec.number}" tabindex="-1">${icon("chevron-down", "icon icon--s")}</button>
      </div>
      <ul class="rail__subs" id="rail-subs-${sec.id}">${sec.subsections.map((ss) => `<li><a class="rail__sub" href="${esc(hrefFor(ss.id))}" data-rail-item data-id="${ss.id}" data-hash="${ss.id}" tabindex="-1"><span class="rail__num num">${ss.number}</span><span class="rail__title">${esc(ss.title)}</span><span class="rail__count num" data-count="${ss.id}">${fmtInt(ss.counts.primary)}</span></a></li>`).join("")}</ul>
    </li>`).join("")}</ul>`;
}
function setRailOpen(li, open) {
  li.classList.toggle("is-open", open);
  const b = li.querySelector(".rail__chevron");
  if (b) { b.setAttribute("aria-expanded", String(open)); b.setAttribute("aria-label", `${open ? "Hide" : "Show"} the subsections of ${li.querySelector(".rail__num").textContent}`); }
}
function updateRail(v) {
  const cur = v.target || null;
  const curSec = v.sec ? v.sec.id : null;
  for (const a of dom.rail.querySelectorAll("[data-rail-item]")) {
    const id = a.dataset.id;
    if (id === cur) a.setAttribute("aria-current", "location"); else a.removeAttribute("aria-current");
    a.href = hrefFor(id);
  }
  for (const li of dom.rail.querySelectorAll(".rail__section")) {
    if (li.dataset.sec === curSec) setRailOpen(li, true);
  }
  /* roving tabindex: the rail is one Tab stop (the current row, else §1); arrows move inside it */
  const stop = dom.rail.querySelector('[data-rail-item][aria-current="location"]') || (curSec && dom.rail.querySelector(`[data-rail-item][data-id="${curSec}"]`)) || dom.rail.querySelector("[data-rail-item]");
  for (const a of dom.rail.querySelectorAll("[data-rail-item]")) a.tabIndex = a === stop ? 0 : -1;
  const c = v.counts;
  for (const span of dom.rail.querySelectorAll("[data-count]")) {
    const id = span.dataset.count;
    const row = span.closest("a") || span.closest(".rail__row");
    if (c && v.anyPaperFilter) {
      let m = 0, tot = 0;
      if (SUB_RE.test(id)) { m = c.subs[id].prim.length; tot = c.subs[id].primTotal; }
      else for (const ss of T.sectionOf(id).subsections) { m += c.subs[ss.id].prim.length; tot += c.subs[ss.id].primTotal; }
      span.textContent = `${fmtInt(m)} / ${fmtInt(tot)}`;
      span.title = `${fmtInt(m)} of ${fmtInt(tot)} papers match`;
      row.classList.toggle("is-zero", m === 0);
    } else {
      const tot = SUB_RE.test(id) ? T.subsectionById(id).counts.primary : T.primaryCount(T.sectionOf(id));
      span.textContent = fmtInt(tot); span.removeAttribute("title"); row.classList.remove("is-zero");
    }
  }
  const curEl = dom.rail.querySelector('[aria-current="location"]') || (curSec ? dom.rail.querySelector(`[data-id="${curSec}"]`) : null);
  if (curEl) {
    const aside = dom.aside;
    const top = curEl.getBoundingClientRect().top - aside.getBoundingClientRect().top + aside.scrollTop;
    if (top < aside.scrollTop + 40 || top > aside.scrollTop + aside.clientHeight - 60) aside.scrollTop = Math.max(0, top - aside.clientHeight / 3);
  }
  for (const c2 of dom.stripChips.querySelectorAll("[data-id]")) c2.classList.toggle("is-on", c2.dataset.id === curSec);
  const curChip = dom.stripChips.querySelector(".is-on");
  if (curChip && dom.stripChips.clientWidth) {
    const cr = curChip.getBoundingClientRect(), sr = dom.stripChips.getBoundingClientRect();
    if (cr.left < sr.left || cr.right > sr.right) dom.stripChips.scrollLeft += cr.left - sr.left - 8;
  }
  stripEnd();
}
function stripEnd() {
  const el2 = dom.stripChips;
  el2.classList.toggle("is-end", el2.scrollLeft + el2.clientWidth >= el2.scrollWidth - 2);
}
function railKeydown(e) {
  const items = [...dom.rail.querySelectorAll("[data-rail-item]")].filter((a) => a.getClientRects().length > 0);
  const i = items.indexOf(document.activeElement);
  if (i < 0) return;
  const a = items[i];
  const li = a.closest(".rail__section");
  const isSec = a.classList.contains("rail__link");
  const go = (el2) => { for (const x of items) x.tabIndex = -1; el2.tabIndex = 0; el2.focus(); };
  switch (e.key) {
    case "ArrowDown": e.preventDefault(); go(items[i + 1] || items[0]); break;
    case "ArrowUp": e.preventDefault(); go(items[i - 1] || items[items.length - 1]); break;
    case "Home": e.preventDefault(); go(items[0]); break;
    case "End": e.preventDefault(); go(items[items.length - 1]); break;
    case "ArrowRight": e.preventDefault(); if (isSec) setRailOpen(li, true); break;
    case "ArrowLeft": e.preventDefault(); if (isSec) setRailOpen(li, false); else go(li.querySelector(".rail__link")); break;
    default: break;
  }
}
function renderStrip() {
  dom.stripChips.innerHTML = T.sections.map((s) => chip({ kind: "section", id: s.id, href: hrefFor(s.id), label: `§${s.number}`, title: `§${s.number} ${s.title}` })).join("");
  for (const a of dom.stripChips.querySelectorAll("a")) a.dataset.hash = a.dataset.id;
}
function setSheet(open) {
  dom.aside.classList.toggle("is-open", open);
  dom.scrim.hidden = !open;
  dom.stripContents.setAttribute("aria-expanded", String(open));
  /* the sheet is modal: the page behind it is inert while it is open */
  for (const el2 of document.querySelectorAll(".masthead, .colophon, .papers__head, .papers__main")) el2.inert = open;
  if (open) { const cur = dom.rail.querySelector('[aria-current="location"]') || dom.rail.querySelector("[data-rail-item]"); if (cur) cur.focus(); }
  else if (document.activeElement && dom.aside.contains(document.activeElement)) dom.stripContents.focus();
}

/* ---------- filter bar ---------- */
function countChip(v, kind, val) {
  if (!v.counts) return null;
  const f = v.f, hits = v.hits;
  let n = 0;
  for (const s of v.secs) for (const ss of v.subsOf(s)) {
    for (const p of S.primaryOf.get(ss.id) || []) {
      if (kind === "grey") continue;
      if (kind === "years") { if (matchPaper(p, f, hits, "years") && yearMatch(p.year, new Set([val]))) n++; }
      else if (kind === "cited") { if (matchPaper(p, f, hits, "cited") && p.selected) n++; }
      else if (kind === "score") { if (matchPaper(p, f, hits, "score") && p.score >= 3) n++; }
      else if (kind === "zh") { if (matchPaper(p, f, hits, "zh") && hasZh("paper", p)) n++; }
    }
    for (const g of S.greyOf.get(ss.id) || []) {
      if (kind === "grey") { if (matchGrey(g, f, hits, "grey")) n++; }
      else if (kind === "years") { if (matchGrey(g, f, hits, "years") && yearMatch(g.year, new Set([val]))) n++; }
      else if (kind === "cited") { if (matchGrey(g, f, hits, "cited") && g.selected) n++; }
      else if (kind === "zh") { if (matchGrey(g, f, hits, "zh") && hasZh("grey", g)) n++; }
    }
  }
  return n;
}
function renderChips(v) {
  const f = v.f;
  const defs = [
    ["cited", "Cited in the PDF", f.cited, "cited"], ["score", "Score 3", f.score3, "score"], ["zh", "Chinese notes", f.zh, "zh"], ["grey", "Reports and posts", f.grey, "grey"],
    null,
    ...YEAR_CHIPS.map(([id, label]) => ["year:" + id, label, f.years.has(id), "years", id])
  ];
  /* the chip buttons are built once and updated in place, so the button the user just pressed keeps focus */
  if (!dom.chips.childElementCount) {
    dom.chips.innerHTML = defs.map((d) => (d ? chip({ kind: "plain", id: d[0], label: d[1], asFilter: true, on: d[2], count: 0 }) : '<span class="filterbar__sep" role="presentation"></span>')).join("");
  }
  for (const d of defs) {
    if (!d) continue;
    const [id, , on, kind, val] = d;
    const b = dom.chips.querySelector(`[data-id="${CSS.escape(id)}"]`);
    if (!b) continue;
    const n = countChip(v, kind, val);
    b.setAttribute("aria-pressed", String(on));
    b.classList.toggle("is-zero", n === 0 && !on);
    const cnt = b.querySelector(".chip__count");
    if (cnt) cnt.textContent = n == null ? "" : fmtInt(n);
  }
  const active = [];
  if (f.q.length >= 2) active.push(chip({ kind: "plain", id: "q", label: `“${f.q}”`, removable: true }));
  if (f.cited) active.push(chip({ kind: "plain", id: "cited", label: "Cited in the PDF", removable: true }));
  if (f.score3) active.push(chip({ kind: "plain", id: "score", label: "Score 3", removable: true }));
  if (f.zh) active.push(chip({ kind: "plain", id: "zh", label: "Chinese notes", removable: true }));
  if (!f.grey) active.push(chip({ kind: "plain", id: "grey", label: "Without reports and posts", removable: true }));
  for (const [id, label] of YEAR_CHIPS) if (f.years.has(id)) active.push(chip({ kind: "plain", id: "year:" + id, label, removable: true }));
  dom.active.hidden = !active.length;
  dom.active.innerHTML = active.length ? `<span class="caps muted">Active</span>${active.map((a) => a.replace('class="chip ', 'class="chip is-on ')).join("")}<button type="button" class="btn btn--ghost btn--sm" id="clear-filters">Clear</button>` : "";
  if (S.pendingFocus) {
    /* a × button was pressed in the active row: move focus to the next removable chip, Clear, or the matching filter chip */
    const xs = dom.active.querySelectorAll("[data-remove]");
    const t = xs[Math.min(S.pendingFocus.index, xs.length - 1)] || dom.active.querySelector("#clear-filters") || dom.chips.querySelector(`[data-id="${CSS.escape(S.pendingFocus.id)}"]`) || dom.q;
    S.pendingFocus = null;
    if (t) t.focus({ preventScroll: true });
  }
  const n = activeFilterCount(f);
  dom.filterN.textContent = n ? ` (${n})` : "";
  dom.toggle.classList.toggle("is-active", n > 0);
}
function syncControls(v) {
  const f = v.f;
  if (document.activeElement !== dom.q) dom.q.value = f.q;
  const hasSub = !!(v.target && SUB_RE.test(v.target));
  const hasSec = !!v.target;
  for (const r of dom.scope.querySelectorAll("input")) {
    const can = r.value === "all" || (r.value === "sec" && hasSec) || (r.value === "sub" && hasSub);
    r.disabled = !can;
    r.closest(".seg__opt").classList.toggle("is-disabled", !can);
    r.checked = r.value === v.scope;
  }
  dom.sort.value = f.sort;
  for (const b of dom.density.querySelectorAll("[data-density]")) b.setAttribute("aria-pressed", String(b.dataset.density === f.density));
  dom.results.dataset.density = f.density;
}
function updateCrumb(v) {
  if (v.eff === "all" && !v.target) { dom.crumb.innerHTML = `<span class="muted">Whole corpus · ${plural(T.sections.length, "section")} · ${plural(T.sections.reduce((n, s) => n + s.subsections.length, 0), "subsection")}</span>`; return; }
  const sec = v.sec;
  let html = `<a href="${esc(hrefFor(sec.id))}" data-hash="${sec.id}">§${sec.number} ${esc(sec.title)}</a>`;
  if (v.target && SUB_RE.test(v.target)) html += ` <span class="papers__crumb-sep" aria-hidden="true">›</span> <a href="${esc(hrefFor(v.target))}" data-hash="${v.target}">${esc(T.fullTitle(v.target))}</a>`;
  if (v.widened) html += ` <span class="muted">· widened to the whole corpus</span>`;
  dom.crumb.innerHTML = html;
}
function updateTitle(v = S.view) {
  if (S.drawerKey && dom.drawer.open) return;
  let t = `Papers · ${SITE_TITLE}`;
  if (v && v.target) {
    const id = v.eff === "sec" ? v.sec.id : v.target;
    t = `${T.fullTitle(id)} · ${t}`;
  }
  document.title = t;
}

/* ---------- heads and cards ---------- */
function sectionHTML(sec, withHead) {
  const op = T.operationOf(sec.id);
  const head = withHead ? `<header class="section-head">
      <h2 class="section-head__title"><span class="section-head__num num">§${sec.number}</span> ${esc(sec.title)}</h2>
      ${op ? `<p class="section-head__op">${chip({ kind: "op", id: op.id, href: linkTo("stream", { op: op.id }), title: `${op.label} items in the stream` })}</p>` : ""}
      ${sec.purpose ? `<p class="section-head__purpose">${esc(sec.purpose)}</p>` : ""}
    </header>` : "";
  return `<section class="sec" id="${sec.id}" data-section="${sec.id}" aria-label="§${sec.number} ${esc(sec.title)}">${head}</section>`;
}
function subHTML(ss, sec, v, c) {
  const H = v.eff === "sub" ? "h2" : "h3";
  const n = S.streamBySub ? S.streamBySub[ss.id] || 0 : 0;
  const counts = c ? `${plural(c.primTotal, "paper")} · ${fmtInt(c.cited)} cited in the PDF · ${fmtInt(c.crossTotal)} cross-referenced here · ${plural(c.greyTotal, "report")}` : `${plural(ss.counts.primary, "paper")} · ${fmtInt(ss.counts.selected)} cited in the PDF · ${fmtInt(ss.counts.cross)} cross-referenced here · ${plural(ss.counts.grey, "report")}`;
  return `<section class="sub" id="${ss.id}" data-section="${sec.id}" aria-labelledby="h-${ss.id}">
    <header class="sub-head">
      <${H} class="sub-head__title" id="h-${ss.id}"><span class="sub-head__num num">${ss.number}</span> ${esc(ss.title)}</${H}>
      <p class="sub-head__counts">${counts}</p>
      ${ss.bullets && ss.bullets.length ? `<details class="sub-head__covers"><summary>${icon("chevron-down", "icon icon--s")}What this subsection covers</summary><p class="sub-head__plan">From the authors' section plan: the points this subsection is written to make.</p><ul>${ss.bullets.map((b) => `<li>${esc(b)}</li>`).join("")}</ul></details>` : ""}
      <a class="sub-head__stream" href="${esc(linkTo("stream", { sub: ss.id }))}" data-stream-sub="${ss.id}"${n ? "" : " hidden"}>${n ? `${plural(n, "item")} in the stream` : ""}</a>
    </header>
    <div class="cards" data-slot="prim"></div>
  </section>`;
}
function groupHTML(u) {
  const label = u.where === "grey" ? `Reports and posts (${fmtInt(u.n)})` : `Also placed here (${fmtInt(u.n)})`;
  return `<details class="runin runin--${u.where}"${u.where === "grey" ? " open" : ""}><summary class="runin__summary">${icon("chevron-down", "icon icon--s")}${label}</summary><div class="cards" data-slot="${u.where}"></div></details>`;
}
function alsoChips(item, excludeSid) {
  const list = (item.also || []).filter((a) => a.sid !== excludeSid && T.subsectionById(a.sid));
  if (!list.length) return "";
  const shown = list.slice(0, 3).map((a) => chip({ kind: "sub", id: a.sid, href: hrefFor(a.sid), label: T.numberOf(a.sid), title: `${T.fullTitle(a.sid)}${a.score != null ? ` · score ${a.score}` : ""}` }).replace("<a ", `<a data-hash="${a.sid}" `)).join("");
  const more = list.length > 3 ? `<span class="card__more muted">+${list.length - 3}</span>` : "";
  return `<span class="card__also"><span class="muted">also in</span>${shown}${more}</span>`;
}
function cardHTML(u, v) {
  const item = u.item, isPaper = u.kind === "paper", cross = u.where === "cross";
  const tokens = v.hits ? v.hits.tokens : null;
  const hl = (s) => (tokens ? highlight(s, tokens) : esc(s));
  const sec = sectionIdOf(item);
  const by = authorsLine(item.authors);
  const line = item.one_line
    ? `<p class="card__line clamp-3">${hl(item.one_line)}</p>`
    : item.reason ? `<p class="card__line card__line--why clamp-3"><span class="card__why">Why here:</span> ${hl(item.reason)}</p>` : "";
  const marks = [];
  if (item.selected) marks.push('<span class="badge badge--cited">Cited</span>');
  if (isPaper) marks.push(item.score >= 3 ? '<span class="score" title="score 3, must cite"><span class="visually-hidden">score </span>3<span class="visually-hidden">, must cite</span></span>' : '<span class="score score--2" title="score 2, relevant"><span class="visually-hidden">score </span>2<span class="visually-hidden">, relevant</span></span>');
  if (hasZh(u.kind, item)) marks.push('<span class="badge badge--zh" title="Structured reading notes in Chinese">中文</span>');
  if (!isPaper) marks.push(`<span class="badge badge--report" data-c="report">Report${item.confidence && item.confidence !== "verified" ? ` · ${esc(item.confidence)}` : ""}</span>`);
  const also = alsoChips(item, u.sub.id);
  if (also) marks.push(also);
  const ext = isPaper
    ? `<a class="card__ext ext" href="${esc(item.url)}" rel="noopener" target="_blank">arXiv ${esc(item.arxiv_id)}${icon("arrow-up-right", "icon icon--ext")}</a>`
    : item.url ? `<a class="card__ext ext" href="${esc(item.url)}" rel="noopener" target="_blank">${esc(hostOf(item.url) || "source")}${icon("arrow-up-right", "icon icon--ext")}</a>`
    : `<span class="card__venue muted" title="${esc(item.venue || "")}">${esc(item.venue || "no link")}</span>`;
  marks.push(ext);
  const markEl = cross
    ? `<span class="mark mark--square-hollow" aria-hidden="true"></span><span class="card__from num" title="primary subsection ${esc(T.fullTitle(item.primary))}">from ${esc(T.numberOf(item.primary))}</span>`
    : '<span class="mark mark--square" aria-hidden="true"></span>';
  return `<article class="card${cross ? " card--cross" : ""}${isPaper ? "" : " card--report"}" data-section="${sec}" data-kind="${u.kind}" data-key="${esc(item.key)}">
    <div class="card__head">${markEl}<p class="card__label"><button type="button" class="card__open" aria-label="Open ${esc(item.label)}: ${esc(item.title)}">${hl(item.label)}</button></p></div>
    <p class="card__title clamp-2">${hl(item.title)}</p>
    <p class="card__byline clamp-1">${hl(by)}${by ? " · " : ""}<span class="num">${esc(item.year)}</span>${!isPaper && item.venue ? ` · ${esc(item.venue)}` : ""}</p>
    ${line}
    <div class="card__marks">${marks.join("")}</div>
  </article>`;
}
function emptyHTML(v) {
  const where = v.eff === "all" ? "the whole corpus" : T.fullTitle(v.target);
  if (!v.active) {
    return `<div class="empty" role="status"><p>No papers are placed in ${esc(where)} in this draft of the survey.</p>${v.eff !== "all" ? `<div class="empty__actions"><a class="btn btn--sm" href="${esc(hrefFor(v.target, { scope: "all" }))}" data-scope-all="1">Browse the whole corpus</a></div>` : ""}</div>`;
  }
  const what = v.q ? `No papers match “${esc(v.q)}” in ${esc(where)}.` : `No papers match these filters in ${esc(where)}.`;
  return `<div class="empty" role="status"><p>${what}</p><div class="empty__actions"><button type="button" class="btn btn--sm" id="empty-clear">Clear filters</button>${v.eff !== "all" ? `<a class="btn btn--sm" href="${esc(hrefFor(v.target, { scope: "all" }))}" data-scope-all="1">Search the whole corpus</a>` : ""}</div></div>`;
}
function errorHTML() {
  return `<div class="error" role="alert"><p>The paper list could not be loaded.</p><div class="error__retry"><button type="button" class="btn btn--sm" id="retry">Retry</button></div></div>`;
}

/* ---------- units and chunked rendering ---------- */
function buildUnits(v) {
  const units = [];
  const f = v.f, hits = v.hits;
  const scoreP = (p) => (hits ? hits.paper.get(p.key) : 0), scoreG = (g) => (hits ? hits.grey.get(g.key) : 0);
  const withHead = v.eff !== "sub";
  let lastSub = null;
  for (const sec of v.secs) {
    const subUnits = [];
    for (const ss of v.subsOf(sec)) {
      const c = v.counts.subs[ss.id];
      const prim = sortItems(c.prim, f, hits, scoreP);
      const greys = sortItems(c.greys, f, hits, scoreG);
      const kindOf = new Map(c.cross.map((x) => [x.paper, x.kind || "paper"]));
      const cross = sortItems(c.cross.map((x) => x.paper), f, hits, (it) => (kindOf.get(it) === "grey" ? scoreG(it) : scoreP(it)));
      const n = prim.length + greys.length + cross.length;
      if (v.active && n === 0 && v.eff !== "sub") continue;
      subUnits.push({ t: "sub", sub: ss, sec, c });
      for (const p of prim) subUnits.push({ t: "card", kind: "paper", item: p, sub: ss, where: "prim" });
      if (greys.length) { subUnits.push({ t: "group", sub: ss, where: "grey", n: greys.length }); for (const g of greys) subUnits.push({ t: "card", kind: "grey", item: g, sub: ss, where: "grey" }); }
      if (cross.length) { subUnits.push({ t: "group", sub: ss, where: "cross", n: cross.length }); for (const p of cross) subUnits.push({ t: "card", kind: kindOf.get(p) || "paper", item: p, sub: ss, where: "cross" }); }
      lastSub = ss;
    }
    if (subUnits.length || !v.active) { units.push({ t: "sec", sec, withHead }); units.push(...subUnits); }
  }
  v.items = units.filter((u) => u.t === "card").map((u) => ({ kind: u.kind, item: u.item }));
  if (!v.items.length) {
    const head = [];
    if (v.eff === "sub") { head.push({ t: "sec", sec: v.sec, withHead: false }); head.push({ t: "sub", sub: T.subsectionById(v.target), sec: v.sec, c: v.counts.subs[v.target] }); }
    else if (v.eff === "sec") head.push({ t: "sec", sec: v.sec, withHead: true });
    return [...head, { t: "empty" }];
  }
  if (v.eff !== "all" && lastSub) {
    const next = nextOf(v, lastSub);
    if (next) units.push({ t: "next", next });
  }
  return units;
}
function nextOf(v, lastSub) {
  if (v.eff === "sub") {
    const sec = v.sec, i = sec.subsections.findIndex((x) => x.id === lastSub.id);
    if (i >= 0 && i + 1 < sec.subsections.length) return sec.subsections[i + 1].id;
    const si = T.sections.indexOf(sec);
    return si + 1 < T.sections.length ? T.sections[si + 1].subsections[0].id : null;
  }
  const si = T.sections.indexOf(v.sec);
  return si + 1 < T.sections.length ? T.sections[si + 1].id : null;
}
function renderChunk() {
  const r = S.r; if (!r) return;
  const units = r.units, v = S.view;
  const end = Math.min(r.i + CHUNK, units.length);
  let buf = "", target = null;
  const flush = () => { if (buf && target) target.insertAdjacentHTML("beforeend", buf); buf = ""; target = null; };
  for (; r.i < end; r.i++) {
    const u = units[r.i];
    if (u.t === "card") {
      const c = r.containers.get(u.sub.id + ":" + u.where);
      if (c !== target) { flush(); target = c; }
      buf += cardHTML(u, v);
      continue;
    }
    flush();
    if (u.t === "sec") { r.secEl = el(sectionHTML(u.sec, u.withHead)); dom.results.appendChild(r.secEl); }
    else if (u.t === "sub") {
      const subEl = el(subHTML(u.sub, u.sec, v, u.c));
      (r.secEl || dom.results).appendChild(subEl);
      r.subEl = subEl;
      r.containers.set(u.sub.id + ":prim", subEl.querySelector('[data-slot="prim"]'));
    } else if (u.t === "group") {
      const g = el(groupHTML(u));
      r.subEl.appendChild(g);
      r.containers.set(u.sub.id + ":" + u.where, g.querySelector(".cards"));
    } else if (u.t === "empty") dom.results.insertAdjacentHTML("beforeend", emptyHTML(v));
    else if (u.t === "next") dom.results.insertAdjacentHTML("beforeend", `<p class="sub-head__next">Next · <a href="${esc(hrefFor(u.next))}" data-hash="${u.next}">${esc(T.fullTitle(u.next))}</a>${icon("arrow-right", "icon icon--s")}</p>`);
  }
  flush();
  if (r.i < units.length) {
    if (!S.sentinel) { S.sentinel = el('<div class="sentinel" aria-hidden="true"></div>'); }
    dom.results.appendChild(S.sentinel);
    if (!S.io) {
      S.io = new IntersectionObserver((es) => { if (es.some((e) => e.isIntersecting)) renderChunk(); }, { rootMargin: "800px 0px" });
      S.io.observe(S.sentinel);
    }
  } else if (S.sentinel) {
    if (S.io) { S.io.disconnect(); S.io = null; }
    S.sentinel.remove(); S.sentinel = null;
  }
}
function ensureRendered(id) {
  let guard = 0;
  while (S.r && S.r.i < S.r.units.length && !document.getElementById(id) && guard++ < 200) renderChunk();
}
function renderSkeleton(v) {
  const frag = [];
  const list = v.target ? (SUB_RE.test(v.target) && v.eff !== "sec" ? [T.subsectionById(v.target)] : v.sec.subsections) : T.sections[0].subsections;
  for (const ss of list) {
    const sec = T.sectionOf(ss.id);
    frag.push(`<section class="sub" data-section="${sec.id}"><header class="sub-head"><p class="sub-head__title"><span class="sub-head__num num">${ss.number}</span> ${esc(ss.title)}</p></header><div class="skeleton" aria-hidden="true"><div class="skeleton__row"></div><div class="skeleton__row"></div><div class="skeleton__row"></div></div></section>`);
  }
  dom.results.innerHTML = frag.join("");
}
function renderView(v, { scroll = false } = {}) {
  S.view = v;
  if (S.io) { S.io.disconnect(); S.io = null; }
  S.sentinel = null; S.r = null;
  dom.results.replaceChildren();
  syncControls(v); renderChips(v); updateRail(v); updateCrumb(v); updateTitle(v);
  dom.resultsHead.innerHTML = resultsHeadHTML(v);
  if (S.loadError) { dom.results.innerHTML = errorHTML(); return; }
  if (!S.loaded) { renderSkeleton(v); return; }
  const units = buildUnits(v);
  S.r = { units, i: 0, containers: new Map(), secEl: null, subEl: null };
  renderChunk();
  if (scroll) scrollToResults();
}
function scrollToResults() {
  const top = dom.results.getBoundingClientRect().top + window.scrollY - (S.stickyH || 112);
  if (window.scrollY > top) window.scrollTo({ top: Math.max(0, top), behavior: "auto" });
}
/** The sticky stack is the masthead (56) plus the live height of the filter bar's first row; published as --sticky-h on
    <html> so scroll-margin-top and scroll-padding-top land hash targets below it at every width. */
function observeSticky() {
  const row = dom.filterbar.querySelector(".filterbar__row1");
  const set = () => {
    const h = Math.round(row.getBoundingClientRect().height) || 48;
    S.stickyH = 56 + h + 8;
    document.documentElement.style.setProperty("--sticky-h", `${S.stickyH}px`);
  };
  set();
  if ("ResizeObserver" in window) new ResizeObserver(set).observe(row);
}
/** After a re-render removed the focused element, put focus on the results head (tabindex -1) so Tab continues from the list. */
function settleFocus() {
  const a = document.activeElement;
  if (!a || a === document.body) dom.resultsHead.focus({ preventScroll: true });
}
function scrollToTarget(id) {
  ensureRendered(id);
  const t = document.getElementById(id);
  if (t) t.scrollIntoView({ block: "start", behavior: reducedMotion() ? "auto" : "smooth" });
}

/* ---------- drawer ---------- */
function metaLine(kind, item) {
  const parts = [String(item.year || "")];
  if (kind === "paper") { parts.push(`arXiv ${item.arxiv_id}`); parts.push(`score ${item.score}`); }
  else parts.push(item.venue || hostOf(item.url));
  if (item.selected) parts.push("cited in the PDF");
  if (kind === "paper" && item.reading_rank != null) parts.push(`reading list #${item.reading_rank}`);
  return parts.filter(Boolean).map(esc).join(" · ");
}
function authorsHTML(list) {
  const a = Array.isArray(list) ? list.filter(Boolean) : [];
  if (!a.length) return "";
  if (a.length <= 12) return `<p class="drawer__authors">${a.map(esc).join(", ")}</p>`;
  return `<p class="drawer__authors"><span>${a.slice(0, 12).map(esc).join(", ")}</span><span class="drawer__authors-rest" hidden>, ${a.slice(12).map(esc).join(", ")}</span> <button type="button" class="drawer__authors-more">Show all ${fmtInt(a.length)} authors</button></p>`;
}
function placedHTML(item) {
  const home = item.primary;
  const rows = [`<li>${chipLink(home, "home")}</li>`];
  for (const a of item.also || []) if (T.subsectionById(a.sid)) rows.push(`<li>${chipLink(a.sid, a.score != null ? `score ${a.score}` : "cross-reference")}</li>`);
  return `<ul class="drawer__placed">${rows.join("")}</ul>`;
  function chipLink(sid, note) {
    const sec = T.sectionOf(sid);
    return `<a href="${esc(hrefFor(sid))}" data-hash="${sid}" data-section="${sec.id}"><span class="mark mark--square" aria-hidden="true"></span><span>${esc(T.fullTitle(sid))}</span><span class="muted num"> · ${esc(note)}</span></a>`;
  }
}
function streamHTML(kind, item) {
  const items = streamItemsFor(kind, item);
  if (!items.length) return "";
  const rows = items.slice(0, 5).map((it) => `<li data-polarity="${esc(it.polarity)}"><span class="num muted">${esc(fmtDate(it.date, it.date_precision || "day", { year: true }))}</span><span class="mark mark--dash" role="img" aria-label="${esc(POLARITY_LABELS[it.polarity] || it.polarity)}"></span><a href="${esc(linkTo("stream", { hash: "item/" + it.id }))}">${esc(it.title)}</a></li>`).join("");
  return `<section class="drawer__section drawer__stream"><h3>In the stream</h3><p class="muted">${plural(items.length, "item")} filed under this paper or its subsection.</p><ul>${rows}</ul><p><a href="${esc(linkTo("stream", { paper: item.key }))}">All ${fmtInt(items.length)} in the stream${icon("arrow-right", "icon icon--s")}</a></p></section>`;
}
function notesHTML(z, sid) {
  const depth = z.reading_depth || "";
  const hint = DEPTH_HINT[depth] || "";
  const field = (k, zh, en) => {
    const v = z[k];
    if (v == null || v === "" || (Array.isArray(v) && !v.length)) return "";
    let dd;
    if (k === "findings") dd = `<ol>${(Array.isArray(v) ? v : [v]).map((x) => `<li>${esc(x)}</li>`).join("")}</ol>`;
    else if (k === "terms") dd = `<dl class="notes__terms">${(Array.isArray(v) ? v : [v]).map((t) => { const i = String(t).indexOf(" = "); const en2 = i >= 0 ? t.slice(0, i) : t, zh2 = i >= 0 ? t.slice(i + 3) : ""; return `<div><dt lang="en">${esc(en2)}</dt><dd>${esc(zh2)}</dd></div>`; }).join("")}</dl>`;
    else dd = esc(Array.isArray(v) ? v.join("；") : v);
    const cls = k === "deployer_takeaway" ? ' class="notes__takeaway"' : k === "doubts" ? ' class="notes__doubts"' : "";
    return `<dt>${zh} <span class="caps muted" lang="en">${en}</span></dt><dd${cls}>${dd}</dd>`;
  };
  return `<section class="drawer__section notes-wrap"><h3>Reading notes (中文)</h3>
    <p class="notes__head">${depth ? `<span class="badge badge--depth" lang="zh-Hans">${esc(depth)}</span>${hint ? ` <span class="muted">${esc(hint)}</span>` : ""}` : ""}</p>
    <p class="notes__intro">Structured reading notes; the depth marks how much of the paper was read.</p>
    <section lang="zh-Hans" class="notes"><dl>${NOTE_FIELDS.map(([k, zh, en]) => field(k, zh, en)).join("")}</dl>
    <p class="notes__meta num" lang="en">阅读深度 ${esc(depth)} · text depth ${esc(z.text_depth || "")} · ${esc(sid)}</p></section></section>`;
}
function fillDrawer(kind, item) {
  const dlg = dom.drawer;
  const sec = T.sectionOf(item.primary) || T.sectionOf(sectionIdOf(item));
  dlg.dataset.section = sec ? sec.id : sectionIdOf(item);
  const crumb = sec ? `<a href="${esc(hrefFor(sec.id))}" data-hash="${sec.id}">§${sec.number} ${esc(sec.title)}</a> <span aria-hidden="true">›</span> <a href="${esc(hrefFor(item.primary))}" data-hash="${item.primary}">${esc(T.fullTitle(item.primary))}</a>` : "";
  const link = new URL(linkTo("papers", { hash: (kind === "grey" ? "grey/" : "paper/") + item.key }), location.href).href;
  const actions = kind === "paper"
    ? `<a class="btn btn--sm ext" href="${esc(item.url)}" rel="noopener" target="_blank">arXiv abstract${icon("arrow-up-right", "icon icon--ext")}</a><a class="btn btn--sm ext" href="https://arxiv.org/pdf/${esc(item.arxiv_id)}" rel="noopener" target="_blank">PDF${icon("arrow-up-right", "icon icon--ext")}</a>`
    : item.url ? `<a class="btn btn--sm ext" href="${esc(item.url)}" rel="noopener" target="_blank">${esc(hostOf(item.url) || "Source")}${icon("arrow-up-right", "icon icon--ext")}</a>` : "";
  const badges = [];
  if (item.selected) badges.push('<span class="badge badge--cited">Cited</span>');
  if (kind === "grey") badges.push(`<span class="badge badge--report" data-c="report">Report${item.confidence && item.confidence !== "verified" ? ` · ${esc(item.confidence)}` : ""}</span>`);
  if (hasZh(kind, item)) badges.push('<span class="badge badge--zh">中文</span>');
  dom.drawerBody.innerHTML = `
    <p class="drawer__crumb">${crumb}</p>
    <h2 class="drawer__label" id="drawer-label" tabindex="-1">${esc(item.label)}</h2>
    <p class="drawer__title">${esc(item.title)}</p>
    ${authorsHTML(item.authors)}
    <p class="drawer__meta">${metaLine(kind, item)}${badges.length ? ` <span class="drawer__badges">${badges.join(" ")}</span>` : ""}</p>
    <div class="drawer__actions">${actions}<button type="button" class="btn btn--sm" data-copy="key" data-value="${esc(item.key)}">${icon("copy", "icon icon--s")}Copy key</button><button type="button" class="btn btn--sm" data-copy="link" data-value="${esc(link)}">${icon("link", "icon icon--s")}Copy link</button></div>
    ${item.one_line ? `<p class="drawer__summary">${esc(item.one_line)}</p>` : ""}
    ${kind === "paper" && item.reason ? `<section class="drawer__section drawer__why"><h3>Why it is here</h3><p>${esc(item.reason)}</p></section>` : ""}
    <section class="drawer__section"><h3>Placed in</h3>${placedHTML(item)}</section>
    <div id="drawer-stream">${streamHTML(kind, item)}</div>
    <div id="drawer-notes"></div>`;
  renderDrawerNav(kind, item);
  dlg.scrollTop = 0;
}
function renderDrawerNav(kind, item) {
  /* Previous, the counter and Next are persistent nodes (papers.html), so a keyboard user's focus survives each step */
  const items = (S.view && S.view.items) || [];
  const i = items.findIndex((x) => x.kind === kind && x.item.key === item.key);
  const nav = dom.drawerNav;
  if (i < 0 || items.length < 2) { nav.hidden = true; return; }
  nav.hidden = false;
  dom.drawerPrev.setAttribute("aria-disabled", String(i === 0));
  dom.drawerNext.setAttribute("aria-disabled", String(i === items.length - 1));
  const pos = `${fmtInt(i + 1)} of ${fmtInt(items.length)}`;
  if (dom.drawerPos.textContent !== pos) dom.drawerPos.textContent = pos;
}
function stepDrawer(delta) {
  if (!S.drawerKey || !S.view) return;
  const [kind, key] = S.drawerKey.split(":");
  const items = S.view.items;
  const i = items.findIndex((x) => x.kind === kind && x.item.key === key);
  const nb = items[i + delta];
  if (i < 0 || !nb) return;
  openEntity(nb.kind, nb.item, { replace: true });
  const card = document.querySelector(`.card[data-kind="${nb.kind}"][data-key="${CSS.escape(nb.item.key)}"]`);
  if (card) card.scrollIntoView({ block: "nearest", behavior: "auto" });
  const a = document.activeElement;
  if (!a || a === document.body || !dom.drawer.contains(a)) {
    const btn = delta > 0 ? dom.drawerNext : dom.drawerPrev;
    (btn.getAttribute("aria-disabled") === "true" ? $("#drawer-label") || btn : btn).focus({ preventScroll: true });
  } else if (a.getAttribute && a.getAttribute("aria-disabled") === "true") {
    const other = a === dom.drawerNext ? dom.drawerPrev : dom.drawerNext;
    (other.getAttribute("aria-disabled") === "true" ? $("#drawer-label") || other : other).focus({ preventScroll: true });
  }
}
async function loadNotesInto(kind, item) {
  const slot = $("#drawer-notes");
  if (!slot) return;
  const known = hasZh(kind, item);
  if (!known && S.zhKeys) { slot.innerHTML = ""; return; }
  if (!known && kind === "paper") { slot.innerHTML = ""; return; }
  slot.innerHTML = `<section class="drawer__section notes-wrap"><h3>Reading notes (中文)</h3><div class="skeleton" aria-hidden="true"><div class="skeleton__row"></div><div class="skeleton__row"></div><div class="skeleton__row"></div><div class="skeleton__row"></div><div class="skeleton__row"></div></div></section>`;
  try {
    const z = await loadNotesFile();
    if (S.drawerKey !== kind + ":" + item.key) return;
    const note = z[item.key];
    slot.innerHTML = note ? notesHTML(note, item.primary) : "";
    if (note && !item.has_zh) { const b = dom.drawerBody.querySelector(".drawer__badges"); if (b && !b.querySelector(".badge--zh")) b.insertAdjacentHTML("beforeend", ' <span class="badge badge--zh">中文</span>'); }
  } catch (e) {
    if (S.drawerKey === kind + ":" + item.key) slot.innerHTML = `<section class="drawer__section notes-wrap"><h3>Reading notes (中文)</h3><p class="error">The reading notes could not be loaded.</p></section>`;
  }
}
/** closeEntity(): the × button and the backdrop. Uses the shell's closeDrawer so history is restored even where the
    dialog's close event is late; Esc goes through the native close event and the listener in wire(). */
function closeEntity() {
  const dlg = dom.drawer;
  if (!dlg.open) return;
  S.drawerKey = null;
  const pushed = !!(history.state && history.state.drawer);
  closeDrawer(dlg, { homeHash: S.view && S.view.target ? S.view.target : "" });
  if (!pushed) { S.lastRoute = location.search + location.hash; updateTitle(); }
}
function openEntity(kind, item, { push = false, replace = false, returnTo } = {}) {
  const dlg = dom.drawer;
  const hash = (kind === "grey" ? "grey/" : "paper/") + item.key;
  S.drawerKey = kind + ":" + item.key;
  fillDrawer(kind, item);
  if (!dlg.open) openDrawer(dlg, { hash: push ? hash : undefined, returnTo });
  else if (replace) writeState({ hash });
  document.title = `${item.label} · Papers · ${SITE_TITLE}`;
  loadNotesInto(kind, item);
}

/* ---------- routing ---------- */
function route({ force = false } = {}) {
  const st = readState();
  const r = parseRoute(st.hash);
  const f = readFilters();
  S.lastRoute = location.search + location.hash;
  if (r.kind === "entity") {
    if (!S.loaded) {
      if (!S.view || force) renderView(computeView({ kind: "none" }, f));
      return;
    }
    const item = r.type === "grey" ? S.greyByKey.get(r.key) : S.byKey.get(r.key);
    if (!item) {
      writeState({ hash: S.view && S.view.target ? S.view.target : "" });
      S.lastRoute = location.search + location.hash;
      if (!S.view) renderView(computeView({ kind: "none" }, f));
      dom.resultsHead.innerHTML = `${resultsHeadHTML(S.view)} · <span class="muted">no paper with the key “${esc(r.key)}”</span>`;
      return;
    }
    let v = S.view;
    const want = computeView(v ? { kind: v.routeKind, id: v.target, item } : { kind: "entity", item }, f);
    if (!v || v.key !== want.key || force) { renderView(want); v = want; }
    if (S.drawerKey !== r.type + ":" + item.key || !dom.drawer.open) openEntity(r.type, item, { push: false });
    return;
  }
  if (dom.drawer.open) { S.drawerKey = null; dom.drawer.close(); }
  const v = computeView(r, f);
  const prev = S.view;
  if (!prev || prev.key !== v.key || force) {
    renderView(v, { scroll: !S.firstRender && !!prev && (prev.target !== v.target || prev.eff !== v.eff) });
  } else { S.view.routeKind = v.routeKind; updateRail(v); updateCrumb(v); updateTitle(v); }
  if (v.target && (v.eff === "all" || (v.eff === "sec" && SUB_RE.test(v.target))) && !S.firstRender && S.loaded) scrollToTarget(v.target);
  S.firstRender = false;
}
function navigateHash(hash) {
  writeState({ hash }, { push: true, historyState: {} });
  route();
}
function setFilter(patch) {
  S.noWiden = false;
  writeState(patch);
  route();
}

/* ---------- wiring ---------- */
function wire() {
  const onSearch = debounce(() => {
    const v = dom.q.value.trim();
    S.noWiden = false;
    writeState({ q: v || null });
    route();
  }, 150);
  dom.q.addEventListener("input", onSearch);
  dom.q.addEventListener("keydown", (e) => {
    if (e.key === "Escape") { e.preventDefault(); onSearch.cancel(); dom.q.value = ""; setFilter({ q: null }); dom.q.blur(); }
    if (e.key === "Enter") { e.preventDefault(); onSearch.cancel(); setFilter({ q: dom.q.value.trim() || null }); }
  });
  dom.scope.addEventListener("change", (e) => {
    const val = e.target.value;
    const v = S.view;
    setFilter({ scope: v && val === v.def ? null : val });
  });
  dom.sort.addEventListener("change", () => setFilter({ sort: dom.sort.value === "survey" ? null : dom.sort.value }));
  dom.density.addEventListener("click", (e) => {
    const b = e.target.closest("[data-density]"); if (!b) return;
    setFilter({ density: b.dataset.density === "compact" ? "compact" : null });
  });
  dom.toggle.addEventListener("click", () => {
    const open = dom.filterbar.classList.toggle("is-open");
    dom.toggle.setAttribute("aria-expanded", String(open));
  });
  dom.chips.addEventListener("click", (e) => {
    const c = e.target.closest("[data-kind][data-id]"); if (!c) return;
    toggleChip(c.dataset.id);
  });
  dom.active.addEventListener("click", (e) => {
    const x = e.target.closest("[data-remove]");
    if (x) { removeChip(x.dataset.remove); return; }
    if (e.target.closest("#clear-filters")) clearFilters();
  });
  dom.rail.addEventListener("click", (e) => {
    const b = e.target.closest(".rail__chevron");
    if (b) { const li = b.closest(".rail__section"); setRailOpen(li, !li.classList.contains("is-open")); return; }
    const a = e.target.closest("a[data-hash]");
    if (a) { e.preventDefault(); navigateHash(a.dataset.hash); if (dom.aside.classList.contains("is-open")) setSheet(false); }
  });
  dom.rail.addEventListener("keydown", railKeydown);
  dom.stripContents.addEventListener("click", () => setSheet(!dom.aside.classList.contains("is-open")));
  dom.aside.querySelector(".rail__close").addEventListener("click", () => setSheet(false));
  dom.scrim.addEventListener("click", () => setSheet(false));
  dom.stripChips.addEventListener("click", (e) => { const a = e.target.closest("a[data-hash]"); if (a) { e.preventDefault(); navigateHash(a.dataset.hash); } });
  dom.stripChips.addEventListener("scroll", stripEnd, { passive: true });
  dom.results.addEventListener("click", (e) => {
    const open = e.target.closest(".card__open");
    if (open) {
      const card = open.closest(".card");
      const kind = card.dataset.kind, key = card.dataset.key;
      const item = kind === "grey" ? S.greyByKey.get(key) : S.byKey.get(key);
      if (item) openEntity(kind, item, { push: true, returnTo: open });
      return;
    }
    const a = e.target.closest("a[data-hash]");
    if (a) { e.preventDefault(); navigateHash(a.dataset.hash); settleFocus(); return; }
    if (e.target.closest("#empty-clear")) { clearFilters(); return; }
    if (e.target.closest("#retry")) { S.loadError = false; S.view = null; renderView(computeView(parseRoute(readState().hash), readFilters())); loadPapers(); return; }
    const sa = e.target.closest("[data-scope-all]");
    if (sa) { e.preventDefault(); setFilter({ scope: "all" }); }
  });
  dom.resultsHead.addEventListener("click", (e) => {
    const sa = e.target.closest("[data-scope-all]");
    if (sa) { e.preventDefault(); setFilter({ scope: "all" }); return; }
    if (e.target.closest("[data-within]")) { S.noWiden = true; route({ force: true }); }
  });
  dom.crumb.addEventListener("click", (e) => { const a = e.target.closest("a[data-hash]"); if (a) { e.preventDefault(); navigateHash(a.dataset.hash); } });
  const dlg = dom.drawer;
  dlg.addEventListener("click", (e) => {
    if (e.target === dlg) { closeEntity(); return; }
    if (e.target.closest("#drawer-close")) { closeEntity(); return; }
    if (e.target.closest("#drawer-prev")) { if (dom.drawerPrev.getAttribute("aria-disabled") !== "true") stepDrawer(-1); return; }
    if (e.target.closest("#drawer-next")) { if (dom.drawerNext.getAttribute("aria-disabled") !== "true") stepDrawer(1); return; }
    const cp = e.target.closest("[data-copy]");
    if (cp) { copyText(cp.dataset.value, cp.dataset.copy === "key" ? "Key copied" : "Link copied"); return; }
    const more = e.target.closest(".drawer__authors-more");
    if (more) { const rest = more.parentElement.querySelector(".drawer__authors-rest"); if (rest) rest.hidden = false; more.remove(); return; }
    const a = e.target.closest("a[data-hash]");
    if (a) {
      /* Re-scope behind the drawer: replace the drawer's history entry (so the shell's close handler does not
         call history.back()) and close; route() then renders the new scope. */
      e.preventDefault();
      writeState({ hash: a.dataset.hash }, { push: false, historyState: {} });
      S.drawerKey = null; dlg.close();
      route();
      settleFocus();
    }
  });
  dlg.addEventListener("keydown", (e) => {
    if (e.target && /^(INPUT|TEXTAREA|SELECT)$/.test(e.target.tagName)) return;
    if (e.key === "j") { e.preventDefault(); stepDrawer(1); }
    else if (e.key === "k") { e.preventDefault(); stepDrawer(-1); }
  });
  dlg.addEventListener("close", () => {
    S.drawerKey = null;
    const h = readState().hash;
    if (!(history.state && history.state.drawer) && /^(paper|grey)\//.test(h)) writeState({ hash: S.view && S.view.target ? S.view.target : "" });
    updateTitle();
  });
  document.addEventListener("keydown", (e) => {
    const tag = e.target && e.target.tagName;
    const typing = /^(INPUT|TEXTAREA|SELECT)$/.test(tag) || (e.target && e.target.isContentEditable);
    if (e.key === "/" && !typing && !dlg.open && !e.metaKey && !e.ctrlKey && !e.altKey) { e.preventDefault(); dom.q.focus(); dom.q.select(); }
    else if (e.key === "Escape" && dom.aside.classList.contains("is-open")) setSheet(false);
  });
  /* popstate fires before hashchange on Back and Forward; route() records the URL it handled so the second event is a no-op. */
  const onNav = () => { if (location.search + location.hash !== S.lastRoute) route(); };
  window.addEventListener("popstate", onNav);
  window.addEventListener("hashchange", onNav);
}
function toggleChip(id) {
  const f = readFilters();
  if (id === "cited") setFilter({ cited: f.cited ? null : "1" });
  else if (id === "score") setFilter({ score: f.score3 ? null : "3" });
  else if (id === "zh") setFilter({ zh: f.zh ? null : "1" });
  else if (id === "grey") setFilter({ grey: f.grey ? "0" : null });
  else if (id.startsWith("year:")) {
    const y = id.slice(5);
    const ys = new Set(f.years);
    if (ys.has(y)) ys.delete(y); else ys.add(y);
    setFilter({ years: ys.size ? YEAR_CHIPS.map((c) => c[0]).filter((c) => ys.has(c)).join(",") : null });
  }
}
function removeChip(id) {
  const xs = [...dom.active.querySelectorAll("[data-remove]")];
  S.pendingFocus = { index: Math.max(0, xs.findIndex((x) => x.dataset.remove === id)), id };
  if (id === "q") { dom.q.value = ""; setFilter({ q: null }); return; }
  if (id === "grey") { setFilter({ grey: null }); return; }
  toggleChip(id);
}
function clearFilters() {
  dom.q.value = "";
  setFilter({ q: null, cited: null, score: null, zh: null, grey: null, years: null });
}

/* ---------- main ---------- */
async function main() {
  Object.assign(dom, {
    rail: $("#rail"), aside: $("#rail-aside"), scrim: $("#rail-scrim"), stripChips: $("#strip-chips"), stripContents: $("#strip-contents"),
    filterbar: $("#filterbar"), q: $("#q"), scope: $("#scope"), sort: $("#sort"), density: $(".filterbar__density"), toggle: $("#filterbar-toggle"), filterN: $("#filterbar-n"),
    chips: $("#chips"), active: $("#active-chips"), resultsHead: $("#results-head"), results: $("#results"), crumb: $("#crumb"),
    drawer: $("#drawer"), drawerBody: $("#drawer-body"), drawerNav: $("#drawer-nav"),
    drawerPrev: $("#drawer-prev"), drawerNext: $("#drawer-next"), drawerPos: $("#drawer-pos")
  });
  const [stats, tax] = await Promise.all([initPage(), T.loadTaxonomy().catch(() => null)]);
  S.stats = stats; S.tax = tax;
  if (!tax) {
    dom.resultsHead.textContent = "The contents could not be loaded.";
    dom.results.innerHTML = `<div class="error" role="alert"><p>The survey's table of contents could not be loaded.</p><div class="error__retry"><button type="button" class="btn btn--sm" id="retry-tax">Retry</button></div></div>`;
    $("#retry-tax").addEventListener("click", () => location.reload());
    return;
  }
  bindStats(stats || {}, { taxonomy: tax });
  if (stats && stats.stream_per_sub) S.streamBySub = stats.stream_per_sub;   /* "N items in the stream" before stream.json loads */
  renderRail(); renderStrip(); wire(); observeSticky();
  S.lastRoute = location.search + location.hash;
  route();
  await loadPapers();
}
main();
