/* taxonomy.js: helpers over data/taxonomy.json and the landing renderers (contents, section bar, mechanism map,
   year histogram, colour key) plus the About tables. Imports common.js; common.js never imports this file. */
import { fetchJSON, dataVersion, registry, esc, icon, fmtInt, linkTo, el, chip, mark, SOURCE_LABELS, OP_LABELS, POLARITY_LABELS } from "./common.js";
export { chip, mark };

/* live bindings, filled by loadTaxonomy() */
export let taxonomy = null;
export let sections = [];
export let operations = [];
export let failureSources = [];
export let requirements = [];
const byId = new Map();

/** loadTaxonomy() -> taxonomy.json (memoised); fills sections, operations, failureSources, requirements. */
export async function loadTaxonomy() {
  if (taxonomy) return taxonomy;
  const t = await fetchJSON("data/taxonomy.json", { version: dataVersion() });
  taxonomy = t;
  sections = t.sections || [];
  operations = t.operations || [];
  failureSources = t.failure_sources || [];
  requirements = t.requirements || [];
  byId.clear();
  for (const s of sections) { byId.set(s.id, s); for (const ss of s.subsections) byId.set(ss.id, { ...ss, section: s.id }); }
  registry.taxonomy = t;
  return t;
}
/** subsectionById("s5_3") -> {id, number, title, slug, bullets, counts, section: "s5"} or undefined */
export function subsectionById(id) { const x = byId.get(id); return x && x.subsections ? undefined : x; }
/** sectionOf("s5_3" | "s5") -> the section object */
export function sectionOf(id) {
  const x = byId.get(id);
  if (!x) return undefined;
  return x.subsections ? x : byId.get(x.section);
}
/** titleOf("s5") -> "Observing Agent Behaviour"; titleOf("s5_3") -> "Chain-of-Thought Monitoring" */
export function titleOf(id) { const x = byId.get(id); return x ? x.title : id; }
/** numberOf("s5") -> "§5"; numberOf("s5_3") -> "5.3" */
export function numberOf(id) { const x = byId.get(id); return !x ? "" : x.subsections ? `§${x.number}` : String(x.number); }
/** fullTitle("s5_3") -> "5.3 Chain-of-Thought Monitoring"; fullTitle("s5") -> "§5 Observing Agent Behaviour" */
export function fullTitle(id) { const x = byId.get(id); return x ? `${numberOf(id)} ${x.title}` : id; }
/** operationOf("s5") -> the operation object for a section id or undefined */
export function operationOf(sectionId) { return operations.find((o) => o.section === sectionId); }
const POLARITY_HEX = { good: "#62A16E", bad: "#D95358", mixed: "#D1B745" };
/** colourFor("s5" | "s5_3" | "observe" | "mistakes" | "bad") -> hex string from taxonomy.json (polarity from BRIEF.md) */
export function colourFor(id) {
  if (id in POLARITY_HEX) return POLARITY_HEX[id];
  const op = operations.find((o) => o.id === id); if (op) return op.color;
  const fs = failureSources.find((f) => f.id === id); if (fs) return fs.color;
  const s = sectionOf(id); return s ? s.color : "#7D7D7D";
}
/** tokenFor("s5") -> "--c-s5" (the CSS custom property for an identity) */
export function tokenFor(id) { return `--c-${id}`; }
export function primaryCount(section) { return section.subsections.reduce((n, ss) => n + (ss.counts ? ss.counts.primary : 0), 0); }

/* ---------- landing renderers ---------- */
/** renderSectionBar(el, stats): 11 segments proportional to stats.per_section. */
export function renderSectionBar(target, stats) {
  const per = (stats && stats.per_section) || {};
  target.innerHTML = sections.map((s) => `<span class="sigbar__seg" data-section="${s.id}" style="flex-grow:${per[s.id] || primaryCount(s) || 1}" title="§${s.number} ${esc(s.title)} · ${fmtInt(per[s.id] || primaryCount(s))}"></span>`).join("");
  target.setAttribute("aria-label", "Papers per section: " + sections.map((s) => `§${s.number} ${fmtInt(per[s.id] || primaryCount(s))}`).join(", "));
}
/** renderToc(el): the eleven contents rows of the landing. */
export function renderToc(target) {
  target.innerHTML = sections.map((s) => `<li class="toc__row" data-section="${s.id}">
    <span class="toc__rule" aria-hidden="true"></span>
    <span class="toc__num">§${s.number}</span>
    <h3 class="toc__title"><a href="${linkTo("papers", { hash: s.id })}">${esc(s.title)}</a></h3>
    <span class="toc__count" title="papers whose primary subsection is in this section">${fmtInt(primaryCount(s))}</span>
    <button type="button" class="toc__chevron" aria-expanded="false" aria-label="Show the subsections of §${s.number}">${icon("chevron-down", "icon icon--s")}</button>
    <p class="toc__subs">${s.subsections.map((ss) => `<a href="${linkTo("papers", { hash: ss.id })}">${ss.number} ${esc(ss.title)}</a>`).join(" · ")}</p>
  </li>`).join("");
  target.addEventListener("click", (e) => {
    const b = e.target.closest(".toc__chevron");
    if (!b) return;
    const row = b.closest(".toc__row");
    const open = row.classList.toggle("is-open");
    b.setAttribute("aria-expanded", String(open));
  });
}

const KEYWORDS = {
  s4: "permissions, sandboxes, action interfaces, information-flow limits",
  s5: "classifiers, action and reasoning monitors, probes, logs, human review",
  s6: "approve, clarify, block, edit, defer, resample, stop, recover",
  s8: "safety fine-tuning, preference learning, adversarial curricula, circuit breakers, unlearning, retention",
  s7: "instruction hierarchies, context and memory selection, self-critique, activation steering",
  s9: "control evaluations, red teams, white-box audits, statistics, safety cases",
  s10: "reference architectures, release gates, safety cases, policy, independent assurance"
};
const GLYPHS = { s4: "lock", s5: "eye", s6: "hand", s8: "dial", s7: "compass", s9: "shield-check", s10: "layers" };

/** streamCounts(items) -> {sources: {mistakes: n, ...}, ops: {constrain: n, ...}, subs: {s4_1: n, ...}} */
export function streamCounts(items) {
  const c = { sources: {}, ops: {}, subs: {}, total: (items || []).length };
  for (const it of items || []) {
    for (const s of it.failure_sources || []) c.sources[s] = (c.sources[s] || 0) + 1;
    for (const o of it.operations || []) c.ops[o] = (c.ops[o] || 0) + 1;
    for (const s of it.subsections || []) c.subs[s] = (c.subs[s] || 0) + 1;
  }
  return c;
}
function itemsLink(href, n) {
  return n == null ? "" : ` · <a href="${href}">${fmtInt(n)} ${n === 1 ? "item" : "items"}</a>`;
}
function node(sec, stats, counts, extraClass = "") {
  const op = operationOf(sec.id);
  const papers = (stats && stats.per_section && stats.per_section[sec.id]) || primaryCount(sec);
  const n = counts && op ? (counts.ops[op.id] || 0) : null;
  return `<div class="mech__node ${extraClass}" data-section="${sec.id}">
    <div class="mech__top"><span class="mech__num">§${sec.number}</span><span class="mech__glyph">${icon(GLYPHS[sec.id] || "layers")}</span></div>
    <a class="mech__label" href="${linkTo("papers", { hash: sec.id })}">${esc(op ? op.label : sec.title)}</a>
    <p class="mech__keys clamp-3" title="${esc(KEYWORDS[sec.id] || "")}">${esc(KEYWORDS[sec.id] || "")}</p>
    <p class="mech__counts"><span>${fmtInt(papers)} papers</span><span data-stream-slot="${op ? op.id : ""}">${op ? itemsLink(linkTo("stream", { op: op.id }), n) : ""}</span></p>
  </div>`;
}
function bar(sec, stats, counts, withMarks) {
  const op = operationOf(sec.id);
  const papers = (stats && stats.per_section && stats.per_section[sec.id]) || primaryCount(sec);
  const marks = withMarks ? `<ul class="mech__sources">${failureSources.map((f) => `<li><a class="mech__source" href="${linkTo("stream", { source: f.id })}" data-source="${f.id}">${mark({ shape: "circle", c: f.id })}<span>${esc(f.label)}</span><span class="mech__counts" data-stream-slot="source:${f.id}">${counts ? itemsLink("", counts.sources[f.id] || 0).replace(/<a[^>]*>|<\/a>/g, "") : ""}</span></a></li>`).join("")}</ul>` : "";
  return `<div class="mech__bar" data-section="${sec.id}">
    <span class="mech__num">§${sec.number}</span>
    <a class="mech__label" href="${linkTo("papers", { hash: sec.id })}">${esc(op ? op.label : sec.title)}</a>
    <span class="mech__counts">${fmtInt(papers)} papers${!withMarks && op ? `<span data-stream-slot="${op.id}">${itemsLink(linkTo("stream", { op: op.id }), counts ? counts.ops[op.id] || 0 : null)}</span>` : ""}</span>
    ${marks}
  </div>`;
}
/** renderMechanismMap(el, stats, streamCounts): Figure 2 as a grid of links (DESIGN.md block 4). streamCounts may be null. */
export function renderMechanismMap(target, stats, counts = null) {
  const S = (id) => sectionOf(id);
  target.innerHTML = `
    ${bar(S("s2"), stats, counts, true)}
    <p class="mech__lever">Lever 1<b>Change the Deployment</b></p>
    ${node(S("s4"), stats, counts)}${node(S("s5"), stats, counts)}${node(S("s6"), stats, counts)}
    ${node(S("s9"), stats, counts, "mech__node--tall")}
    <p class="mech__lever">Lever 2<b>Change the Model</b></p>
    ${node(S("s8"), stats, counts, "mech__node--wide")}${node(S("s7"), stats, counts)}
    ${bar(S("s10"), stats, counts, false)}`;
}
/** updateMechanismCounts(el, streamCounts): fills the "· N items" slots once stream.json has loaded. */
export function updateMechanismCounts(target, counts) {
  if (!counts) return;
  for (const slot of target.querySelectorAll("[data-stream-slot]")) {
    const key = slot.dataset.streamSlot;
    if (!key) continue;
    if (key.startsWith("source:")) {
      const n = counts.sources[key.slice(7)] || 0;
      slot.textContent = ` · ${fmtInt(n)} ${n === 1 ? "item" : "items"}`;
    } else {
      slot.innerHTML = itemsLink(linkTo("stream", { op: key }), counts.ops[key] || 0);
    }
  }
}
/** renderYearHistogram(el, stats.years): 320 × 56 inline SVG, bars in --fg per year from 2016 (earlier folded). */
export function renderYearHistogram(target, years) {
  const keys = Object.keys(years || {}).map(Number).filter((n) => !isNaN(n));
  if (!keys.length) { target.innerHTML = ""; return; }
  const last = Math.max(...keys, 2026);
  const first = 2016;
  const bins = [];
  for (let y = first; y <= last; y++) bins.push({ y, n: 0, label: y === first ? "≤2016" : String(y) });
  for (const y of keys) { const b = bins.find((x) => x.y === Math.max(first, y)); if (b) b.n += years[y]; }
  const W = 320, H = 56, chartH = 40, gap = 2;
  const bw = (W - gap * (bins.length - 1)) / bins.length;
  const max = Math.max(...bins.map((b) => b.n), 1);
  const ticks = [2016, 2020, 2024, 2026].filter((t) => t >= first && t <= last);
  /* square-root scale with a 3 px floor: the 908-paper 2026 bar would otherwise flatten 2016 to 2022 (2 to 32 papers) into a baseline */
  const bars = bins.map((b, i) => {
    const h = Math.max(b.n ? 3 : 0, Math.round(Math.sqrt(b.n / max) * chartH));
    return `<rect x="${(i * (bw + gap)).toFixed(1)}" y="${chartH - h}" width="${bw.toFixed(1)}" height="${h}"><title>${b.label} · ${fmtInt(b.n)} papers</title></rect>`;
  }).join("");
  const labels = ticks.map((t) => {
    const i = t - first; const x = i * (bw + gap) + bw / 2;
    const anchor = i === 0 ? "start" : i === bins.length - 1 ? "end" : "middle";
    const xx = i === 0 ? 0 : i === bins.length - 1 ? W : x;
    return `<text x="${xx.toFixed(1)}" y="${H - 2}" text-anchor="${anchor}">${t === first ? "≤2016" : t}</text>`;
  }).join("");
  const total = bins.reduce((n, b) => n + b.n, 0);
  target.innerHTML = `<svg class="statline__chart" viewBox="0 0 ${W} ${H}" width="${W}" height="${H}" role="img" aria-label="Papers per year, ${fmtInt(total)} papers from ${Math.min(...keys)} to ${last}">${bars}${labels}</svg>`;
}
/** renderKey(el): the colour legend ("Reading the Marks"). */
export function renderKey(target) {
  const ops = operations.filter((o) => o.lever !== null);
  target.innerHTML = `<p class="key__head caps">Reading the Marks</p><div class="key__items">
    <span class="key__item"><span class="key__glyphs">${failureSources.map((f) => mark({ shape: "circle", c: f.id })).join("")}</span>failure source (mistakes, manipulation, misalignment)</span>
    <span class="key__item"><span class="key__glyphs">${ops.map((o) => mark({ shape: "square", c: o.id })).join("")}</span>section or operation</span>
    <span class="key__item"><span class="key__glyphs">${["good", "bad", "mixed"].map((p) => mark({ shape: "dash", c: p })).join("")}</span>polarity (good, bad, mixed)</span>
  </div>`;
}

/* ---------- About renderers ---------- */
/** renderColourKey(el): one row per section, failure source and polarity with the real mark, token name and meaning. */
export function renderColourKey(target) {
  const rows = [];
  for (const s of sections) { const op = operationOf(s.id); rows.push([mark({ shape: "square", c: s.id }), `--c-${s.id}`, `§${s.number} ${esc(s.title)}${op && op.label !== s.title ? ` (${esc(op.label)})` : ""}`]); }
  for (const f of failureSources) rows.push([mark({ shape: "circle", c: f.id }), `--c-${f.id}`, `Failure source: ${esc(f.label)}`]);
  for (const p of ["good", "bad", "mixed"]) rows.push([mark({ shape: "dash", c: p }), `--c-${p}`, `Polarity: ${POLARITY_LABELS[p].toLowerCase()}`]);
  target.innerHTML = `<table class="colour-key"><thead><tr><th>Mark</th><th>Token</th><th>Meaning</th></tr></thead><tbody>${rows.map((r) => `<tr><td>${r[0]}</td><td>${r[1]}</td><td>${r[2]}</td></tr>`).join("")}</tbody></table>`;
}
/** renderSectionsTable(el): the 56-row table in eleven <details> groups; zh counts fill via fillZhCounts. */
export function renderSectionsTable(target) {
  target.innerHTML = sections.map((s) => {
    const tot = s.subsections.reduce((a, ss) => ({ primary: a.primary + ss.counts.primary, selected: a.selected + ss.counts.selected, cross: a.cross + ss.counts.cross, grey: a.grey + ss.counts.grey }), { primary: 0, selected: 0, cross: 0, grey: 0 });
    return `<details class="sections-table__group" data-section="${s.id}">
      <summary class="sections-table__summary"><span class="sections-table__rule" aria-hidden="true"></span><span class="num muted">§${s.number}</span><span class="sections-table__title">${esc(s.title)}</span><span class="sections-table__totals">${fmtInt(tot.primary)} primary · ${fmtInt(tot.selected)} cited · ${fmtInt(tot.grey)} reports</span><span class="sections-table__chev">${icon("chevron-down")}</span></summary>
      <table><thead><tr><th>Subsection</th><th class="n">Primary</th><th class="n">Cited</th><th class="n">Cross</th><th class="n">Reports</th><th class="n">中文</th></tr></thead><tbody>
      ${s.subsections.map((ss) => `<tr><td><a href="${linkTo("papers", { hash: ss.id })}">${ss.number} ${esc(ss.title)}</a></td><td class="n">${fmtInt(ss.counts.primary)}</td><td class="n">${fmtInt(ss.counts.selected)}</td><td class="n">${fmtInt(ss.counts.cross)}</td><td class="n">${fmtInt(ss.counts.grey)}</td><td class="n num" data-zh="${ss.id}">${ss.counts.zh != null ? fmtInt(ss.counts.zh) : "·"}</td></tr>`).join("")}
      </tbody></table></details>`;
  }).join("");
}
/** fillZhCounts(el, summaries): writes per-subsection counts of Chinese notes into [data-zh] cells. */
export function fillZhCounts(target, summaries) {
  const c = {};
  for (const k of Object.keys(summaries || {})) { const sid = summaries[k].sid; if (sid) c[sid] = (c[sid] || 0) + 1; }
  for (const td of target.querySelectorAll("[data-zh]")) td.textContent = fmtInt(c[td.dataset.zh] || 0);
}
export { el, SOURCE_LABELS, OP_LABELS };
