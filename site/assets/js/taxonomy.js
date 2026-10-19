/* taxonomy.js: helpers over data/taxonomy.json and the landing renderers (contents by part, section bar).
   Imports common.js; common.js never imports this file. */
import { fetchJSON, dataVersion, registry, esc, icon, fmtInt, linkTo, el, chip, mark, SOURCE_LABELS, OP_LABELS } from "./common.js";
export { chip, mark };

/* live bindings, filled by loadTaxonomy() */
export let taxonomy = null;
export let parts = [];
export let sections = [];
export let operations = [];
export let failureSources = [];
export let requirements = [];
const byId = new Map();

/** loadTaxonomy() -> taxonomy.json (memoised); fills parts, sections, operations, failureSources, requirements and
    the shared label maps, so every chip label comes from the paper's data. */
export async function loadTaxonomy() {
  if (taxonomy) return taxonomy;
  const t = await fetchJSON("data/taxonomy.json", { version: dataVersion() });
  taxonomy = t;
  sections = t.sections || [];
  operations = t.operations || [];
  failureSources = t.failure_sources || [];
  requirements = t.requirements || [];
  parts = Array.isArray(t.parts) && t.parts.length ? t.parts : [{ title: "", sections: sections.map((s) => s.id) }];
  byId.clear();
  for (const s of sections) { byId.set(s.id, s); for (const ss of s.subsections) byId.set(ss.id, { ...ss, section: s.id }); }
  for (const o of operations) if (o.id && o.label) OP_LABELS[o.id] = o.label;
  for (const f of failureSources) if (f.id && f.label) SOURCE_LABELS[f.id] = f.label;
  registry.taxonomy = t;
  return t;
}
/** subsectionById("s5_2") -> {id, number, title, slug, counts, section: "s5"} or undefined */
export function subsectionById(id) { const x = byId.get(id); return x && x.subsections ? undefined : x; }
/** sectionOf("s5_2" | "s5") -> the section object */
export function sectionOf(id) {
  const x = byId.get(id);
  if (!x) return undefined;
  return x.subsections ? x : byId.get(x.section);
}
/** sectionsOfPart(part) -> the part's section objects in order */
export function sectionsOfPart(part) { return (part.sections || []).map((id) => byId.get(id)).filter((s) => s && s.subsections); }
/** titleOf("s5") -> "Monitoring"; titleOf("s5_2") -> "Automated Monitors" */
export function titleOf(id) { const x = byId.get(id); return x ? x.title : id; }
/** numberOf("s5") -> "§5"; numberOf("s5_2") -> "5.2" */
export function numberOf(id) { const x = byId.get(id); return !x ? "" : x.subsections ? `§${x.number}` : String(x.number); }
/** fullTitle("s5_2") -> "5.2 Automated Monitors"; fullTitle("s5") -> "§5 Monitoring" */
export function fullTitle(id) { const x = byId.get(id); return x ? `${numberOf(id)} ${x.title}` : id; }
/** operationsOf("s5") -> the operation objects of a section in order ([] for §1, §3, §10; two for §7) */
export function operationsOf(sectionId) { return operations.filter((o) => o.section === sectionId); }
const POLARITY_HEX = { good: "#62A16E", bad: "#D95358", mixed: "#D1B745" };
/** colourFor("s5" | "s5_2" | "monitor" | "benign" | "bad") -> hex string from taxonomy.json (polarity from BRIEF.md) */
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
/** renderSectionBar(el, stats): one segment per section, proportional to stats.per_section. */
export function renderSectionBar(target, stats) {
  const per = (stats && stats.per_section) || {};
  target.innerHTML = sections.map((s) => `<span class="sigbar__seg" data-section="${s.id}" style="flex-grow:${per[s.id] || primaryCount(s) || 1}" title="§${s.number} ${esc(s.title)} · ${fmtInt(per[s.id] || primaryCount(s))}"></span>`).join("");
  target.setAttribute("aria-label", "Papers per section: " + sections.map((s) => `§${s.number} ${fmtInt(per[s.id] || primaryCount(s))}`).join(", "));
}
/** renderToc(el): the paper's contents on the landing, grouped by part; every title links into papers.html. */
export function renderToc(target) {
  const row = (s) => `<li class="toc__row" data-section="${s.id}">
    <span class="toc__rule" aria-hidden="true"></span>
    <span class="toc__num">§${s.number}</span>
    <h4 class="toc__title"><a href="${linkTo("papers", { hash: s.id })}">${esc(s.title)}</a></h4>
    <span class="toc__count" title="papers whose primary subsection is in this section">${fmtInt(primaryCount(s))}</span>
    <button type="button" class="toc__chevron" aria-expanded="false" aria-label="Show the subsections of §${s.number}">${icon("chevron-down", "icon icon--s")}</button>
    <p class="toc__subs">${s.subsections.map((ss) => `<a href="${linkTo("papers", { hash: ss.id })}">${ss.number} ${esc(ss.title)} <span class="num">${fmtInt(ss.counts ? ss.counts.primary : 0)}</span></a>`).join(" · ")}</p>
  </li>`;
  target.innerHTML = parts.map((p) => `<li class="toc__part">
    ${p.title ? `<h3 class="toc__part-title caps">${esc(p.title)}</h3>` : ""}
    <ol class="toc__sections">${sectionsOfPart(p).map(row).join("")}</ol>
  </li>`).join("");
  target.addEventListener("click", (e) => {
    const b = e.target.closest(".toc__chevron");
    if (!b) return;
    const row2 = b.closest(".toc__row");
    const open = row2.classList.toggle("is-open");
    b.setAttribute("aria-expanded", String(open));
  });
}
/** streamCounts(items) -> {sources: {benign: n, ...}, ops: {constrain: n, ...}, subs: {s4_1: n, ...}} */
export function streamCounts(items) {
  const c = { sources: {}, ops: {}, subs: {}, total: (items || []).length };
  for (const it of items || []) {
    for (const s of it.failure_sources || []) c.sources[s] = (c.sources[s] || 0) + 1;
    for (const o of it.operations || []) c.ops[o] = (c.ops[o] || 0) + 1;
    for (const s of it.subsections || []) c.subs[s] = (c.subs[s] || 0) + 1;
  }
  return c;
}
export { el, SOURCE_LABELS, OP_LABELS };
