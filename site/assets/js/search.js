/* search.js: a small prefix search shared by the papers and stream pages (design/DESIGN.md 5.4).
   Fields are lower-cased, NFD-normalised with diacritics stripped, non-alphanumerics replaced by spaces and stored
   with a leading space; a query token matches when it is a word prefix in some field (field.includes(" " + token)).
   Rank: sum over tokens of the best field weight. ES module, imports only esc() from common.js. */
import { esc } from "./common.js";

const MARKS = /\p{M}+/gu;
const NON_ALNUM = /[^\p{L}\p{N}]+/gu;

/** normalize("Chain-of-Thought Émile") -> " chain of thought emile " */
export function normalize(s) {
  const t = String(s ?? "").normalize("NFD").replace(MARKS, "").toLowerCase().replace(NON_ALNUM, " ").trim();
  return t ? ` ${t} ` : "";
}

/** tokenize("Monitor  CoT") -> ["monitor", "cot"]; empty array when the query is shorter than two characters. */
export function tokenize(query) {
  const q = String(query ?? "").trim();
  if (q.length < 2) return [];
  return normalize(q).trim().split(" ").filter(Boolean);
}

/** createIndex([{name, weight, get}]) -> an empty index; add items with addToIndex. */
export function createIndex(fields) {
  return { fields: fields.map((f) => ({ name: f.name, weight: f.weight || 1, get: f.get || null })), docs: [] };
}

/** addToIndex(index, items): appends items in order (file order is the tie-break at search time). */
export function addToIndex(index, items) {
  for (const it of items || []) {
    index.docs.push({ item: it, f: index.fields.map((fd) => normalize(fd.get ? fd.get(it) : it[fd.name])) });
  }
  return index;
}

/** buildIndex(items, fields) -> index (createIndex + addToIndex in one call). */
export function buildIndex(items, fields) {
  return addToIndex(createIndex(fields), items);
}

/** search(index, "cot monitor") -> {tokens, results: [{item, score, order}]} ranked by score then file order;
    null when the query is too short. Every token must be a word prefix in some field of the item. */
export function search(index, query) {
  const tokens = tokenize(query);
  if (!tokens.length) return null;
  const needles = tokens.map((t) => " " + t);
  const out = [];
  const docs = index.docs, weights = index.fields.map((f) => f.weight);
  for (let i = 0; i < docs.length; i++) {
    const d = docs[i];
    let score = 0, ok = true;
    for (let t = 0; t < needles.length; t++) {
      let best = 0;
      for (let k = 0; k < d.f.length; k++) {
        if (weights[k] > best && d.f[k] && d.f[k].includes(needles[t])) best = weights[k];
      }
      if (!best) { ok = false; break; }
      score += best;
    }
    if (ok) out.push({ item: d.item, score, order: i });
  }
  out.sort((a, b) => b.score - a.score || a.order - b.order);
  return { tokens, results: out };
}

/** highlight("Chain-of-Thought Monitoring", ["chain", "mon"]) -> escaped HTML with <mark> around word-prefix matches.
    Matching is case- and diacritic-insensitive and respects the same word boundaries as the index. */
export function highlight(text, tokens) {
  const s = String(text ?? "");
  if (!s || !tokens || !tokens.length) return esc(s);
  const norm = [], map = [];
  let pos = 0;
  for (const ch of s) {
    const n = ch.normalize("NFD").replace(MARKS, "").toLowerCase().replace(NON_ALNUM, " ");
    for (const c of n) { norm.push(c); map.push(pos); }
    pos += ch.length;
  }
  const ns = norm.join("");
  const ranges = [];
  for (const tok of tokens) {
    if (!tok) continue;
    let from = 0;
    for (;;) {
      const j = ns.indexOf(tok, from);
      if (j < 0) break;
      if (j === 0 || ns[j - 1] === " ") {
        const a = map[j];
        const lastStart = map[j + tok.length - 1];
        const b = lastStart + (s.codePointAt(lastStart) > 0xffff ? 2 : 1);
        ranges.push([a, b]);
      }
      from = j + 1;
    }
  }
  if (!ranges.length) return esc(s);
  ranges.sort((x, y) => x[0] - y[0]);
  const merged = [];
  for (const r of ranges) {
    const last = merged[merged.length - 1];
    if (last && r[0] <= last[1]) last[1] = Math.max(last[1], r[1]); else merged.push([r[0], r[1]]);
  }
  let out = "", i = 0;
  for (const [a, b] of merged) { out += esc(s.slice(i, a)) + "<mark>" + esc(s.slice(a, b)) + "</mark>"; i = b; }
  return out + esc(s.slice(i));
}
