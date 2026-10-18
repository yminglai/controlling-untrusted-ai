#!/usr/bin/env python3
"""Checks for the files that pipeline/build_data.py writes to site/data/.

Run from the project root after a build:

    python3 pipeline/build_data.py
    python3 pipeline/tests/test_build_data.py

Plain asserts; exit code 0 means every check passed. Soft findings (for example
a Chinese summary whose key is in neither papers.json nor grey.json) are printed
as "ANOMALY:" lines instead of failing.
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "site" / "data"
OVERLEAF = ROOT.parent / "overleaf-ai-control"   # the read-only paper clone; absent in CI
sys.path.insert(0, str(ROOT / "pipeline"))

from build_data import clean_bullets, kebab, strip_latex  # noqa: E402

ALLOWED_COLOURS = {
    "#2E2E2E", "#7D7D7D", "#C7C7C7", "#EAEAEA", "#F7F7F7", "#FFFFFF",
    "#D95358", "#E27553", "#598DD2", "#E09A3B", "#65C2B9", "#8D86E8",
    "#62A16E", "#A37CAD", "#6FCBEF", "#E072AF", "#D1B745", "#C7A678", "#75A4B5",
}
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LATEX_LEFTOVER = re.compile(r"\\[A-Za-z]+|--|[{}]")
SUMMARY_FIELDS = [
    "positioning", "problem", "method", "findings", "deployer_takeaway", "limitations",
    "relation_to_subsection", "reading_depth", "terms", "doubts", "sid", "text_depth",
]
YEAR_MIN, YEAR_MAX = 1970, 2027


def load(name: str):
    with (DATA / name).open(encoding="utf-8") as fh:
        return json.load(fh)


def check_year(y, what: str) -> None:
    assert isinstance(y, int) and not isinstance(y, bool), f"{what}: year {y!r} is not an int"
    assert YEAR_MIN <= y <= YEAR_MAX, f"{what}: year {y} outside {YEAR_MIN}-{YEAR_MAX}"


def main() -> int:
    anomalies: list[str] = []
    tax = load("taxonomy.json")
    papers = load("papers.json")
    grey = load("grey.json")
    summaries = load("summaries_zh.json")
    stats = load("stats.json")

    # ---- taxonomy ------------------------------------------------------- #
    sections = tax["sections"]
    subs = [ss for s in sections for ss in s["subsections"]]
    assert len(sections) == 11, f"expected 11 sections, got {len(sections)}"
    assert len(subs) == 56, f"expected 56 subsections, got {len(subs)}"
    sids = [ss["id"] for ss in subs]
    assert len(set(sids)) == 56, "subsection ids are not unique"
    sid_pos = {sid: i for i, sid in enumerate(sids)}
    op_ids = {o["id"] for o in tax["operations"]}
    assert tax["title"] == "Controlling Untrusted AI: A Survey"
    assert tax["thesis"].strip() and len(tax["readers"]) == 3
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", tax["generated"])
    assert [r["id"] for r in tax["requirements"]] == ["correct", "compliant", "in-scope", "within-budget", "safe"]
    assert [f["id"] for f in tax["failure_sources"]] == ["mistakes", "manipulation", "misalignment"]
    assert all(f["blurb"].strip() and f["color"] in ALLOWED_COLOURS for f in tax["failure_sources"])
    assert len(tax["operations"]) == 8
    for o in tax["operations"]:
        assert o["section"] in {s["id"] for s in sections}, f"operation {o['id']} points at unknown section"
        assert o["color"] in ALLOWED_COLOURS

    section_slugs = Counter()
    sub_slugs = Counter()
    for s in sections:
        assert s["id"] == f"s{s['number']}", s["id"]
        assert s["title"].strip(), f"{s['id']}: empty title"
        assert SLUG.match(s["slug"]), f"{s['id']}: slug {s['slug']!r} not kebab-case"
        assert s["color"] in ALLOWED_COLOURS, f"{s['id']}: colour {s['color']} not a token"
        assert s["purpose"].strip(), f"{s['id']}: empty purpose"
        section_slugs[s["slug"]] += 1
        if s["id"] in ("s1", "s3", "s11"):
            assert s["operation"] is None and s["color"] == "#7D7D7D", f"{s['id']}: should be neutral"
        else:
            assert s["operation"] in op_ids, f"{s['id']}: operation {s['operation']!r} unknown"
            op = next(o for o in tax["operations"] if o["id"] == s["operation"])
            assert op["section"] == s["id"] and op["color"] == s["color"], f"{s['id']}: operation mismatch"
        for j, ss in enumerate(s["subsections"], start=1):
            assert ss["id"] == f"s{s['number']}_{j}", f"positional id mismatch: {ss['id']}"
            assert ss["number"] == f"{s['number']}.{j}", ss["number"]
            assert ss["title"].strip(), f"{ss['id']}: empty title"
            assert SLUG.match(ss["slug"]), f"{ss['id']}: slug {ss['slug']!r} not kebab-case"
            sub_slugs[ss["slug"]] += 1
            assert isinstance(ss["bullets"], list)
            for b in ss["bullets"]:
                assert b.strip(), f"{ss['id']}: empty bullet"
                assert not LATEX_LEFTOVER.search(b), f"{ss['id']}: LaTeX left in bullet: {b[:80]!r}"
                assert not re.match(r"(?i)(literature pass|references to start from|further reading)", b), \
                    f"{ss['id']}: housekeeping bullet not removed"
            assert set(ss["counts"]) == {"primary", "selected", "cross", "grey", "zh"}, ss["id"]
            assert not LATEX_LEFTOVER.search(s["purpose"]), f"{s['id']}: LaTeX left in purpose"
    assert all(n == 1 for n in section_slugs.values()), "section slugs not unique"
    assert all(n == 1 for n in sub_slugs.values()), "subsection slugs not unique"

    # ---- papers --------------------------------------------------------- #
    keys = [p["key"] for p in papers]
    dup = [k for k, n in Counter(keys).items() if n > 1]
    assert not dup, f"duplicate keys in papers.json: {dup[:10]}"
    paper_keys = set(keys)
    fields = ["key", "arxiv_id", "url", "title", "authors", "year", "primary", "section", "score",
              "selected", "label", "one_line", "reason", "also", "reading_rank", "has_zh"]
    empty_one_line = 0
    for p in papers:
        assert list(p) == fields, f"{p.get('key')}: field order {list(p)}"
        assert p["key"].strip(), "paper without key"
        assert p["title"].strip(), f"{p['key']}: empty title"
        assert p["primary"] in sid_pos, f"{p['key']}: primary {p['primary']!r} not in taxonomy"
        assert p["section"] == p["primary"].split("_")[0], f"{p['key']}: section mismatch"
        for a in p["also"]:
            assert a["sid"] in sid_pos, f"{p['key']}: also sid {a['sid']!r} not in taxonomy"
            assert a["sid"] != p["primary"], f"{p['key']}: also duplicates primary"
        check_year(p["year"], p["key"])
        assert re.fullmatch(r"\d{4}\.\d{4,5}(v\d+)?", p["arxiv_id"]), f"{p['key']}: arxiv_id {p['arxiv_id']!r}"
        assert p["url"] == f"https://arxiv.org/abs/{p['arxiv_id']}", f"{p['key']}: url"
        assert isinstance(p["authors"], list) and p["authors"], f"{p['key']}: authors"
        assert p["score"] in (2, 3), f"{p['key']}: score {p['score']}"
        assert isinstance(p["selected"], bool)
        assert p["label"].strip(), f"{p['key']}: empty label"
        assert p["reading_rank"] is None or isinstance(p["reading_rank"], int)
        assert p["has_zh"] == (p["key"] in summaries), f"{p['key']}: has_zh inconsistent"
        if not p["one_line"]:
            empty_one_line += 1
    if empty_one_line:
        anomalies.append(f"papers: {empty_one_line} papers with empty one_line")

    def paper_sort_key(p):
        return (sid_pos[p["primary"]], not p["selected"], -p["score"],
                p["reading_rank"] is None, p["reading_rank"] if p["reading_rank"] is not None else 0,
                -p["year"], p["title"].lower(), p["key"])
    assert [p["key"] for p in papers] == [p["key"] for p in sorted(papers, key=paper_sort_key)], \
        "papers.json is not in the specified sort order"

    # ---- grey ----------------------------------------------------------- #
    gkeys = [g["key"] for g in grey]
    gdup = [k for k, n in Counter(gkeys).items() if n > 1]
    assert not gdup, f"duplicate keys in grey.json: {gdup}"
    grey_keys = set(gkeys)
    gfields = ["key", "title", "authors", "year", "venue", "url", "primary", "section", "label",
               "one_line", "confidence", "selected", "also", "has_zh"]
    paper_arxiv = {p["arxiv_id"] for p in papers}
    for g in grey:
        assert list(g) == gfields, f"{g.get('key')}: field order {list(g)}"
        assert g["key"].strip() and g["title"].strip(), f"{g.get('key')}: empty key or title"
        assert g["primary"] in sid_pos, f"{g['key']}: primary {g['primary']!r} not in taxonomy"
        assert g["section"] == g["primary"].split("_")[0], f"{g['key']}: section mismatch"
        check_year(g["year"], g["key"])
        assert isinstance(g["authors"], list)
        assert isinstance(g["selected"], bool)
        assert g["label"].strip(), f"{g['key']}: empty label"
        assert g["confidence"] in ("verified", "likely", "unverified"), f"{g['key']}: confidence {g['confidence']!r}"
        assert re.match(r"https?://", g["url"]), f"{g['key']}: empty url or url without scheme"
        for a in g["also"]:
            assert set(a) == {"sid", "score"} and a["sid"] in sid_pos and a["sid"] != g["primary"], f"{g['key']}: also {a}"
        assert g["has_zh"] == (g["key"] in summaries), f"{g['key']}: has_zh inconsistent"
        m = re.search(r"arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5})", g["url"])
        assert not (m and m.group(1) in paper_arxiv), f"{g['key']}: arXiv paper {m.group(1)} emitted as a report"
        assert not LATEX_LEFTOVER.search(g["title"]) and "$" not in g["title"], f"{g['key']}: LaTeX left in title"
    # One record per document: no two grey items share a URL.
    seen_urls = Counter(g["url"].lower().rstrip("/") for g in grey)
    dup_urls = {u: [g["key"] for g in grey if g["url"].lower().rstrip("/") == u] for u, n in seen_urls.items() if n > 1}
    assert not dup_urls, f"grey items sharing one URL: {dup_urls}"
    collide = sorted(grey_keys & paper_keys)
    assert not collide, f"grey keys also in papers.json: {collide}"
    for p in papers:
        assert "$" not in p["title"] and "$" not in p["label"], f"{p['key']}: TeX math left in title or label"
        assert not re.search(r"pass-\d agent", p["reason"]), f"{p['key']}: pipeline wording in reason"

    # ---- summaries ------------------------------------------------------ #
    orphan = [k for k in summaries if k not in paper_keys and k not in grey_keys]
    assert not orphan, f"summaries_zh: {len(orphan)} keys in neither papers.json nor grey.json: {orphan}"
    for k, s in summaries.items():
        assert list(s) == SUMMARY_FIELDS, f"summary {k}: fields {list(s)}"
        assert isinstance(s["findings"], list) and isinstance(s["terms"], list), k
        assert s["sid"] in sid_pos, f"summary {k}: sid {s['sid']!r} not in taxonomy"
    assert list(summaries) == sorted(summaries), "summaries_zh.json keys are not sorted"

    # ---- counts --------------------------------------------------------- #
    exp = {sid: Counter() for sid in sids}
    for p in papers:
        exp[p["primary"]]["primary"] += 1
        if p["selected"]:
            exp[p["primary"]]["selected"] += 1
        if p["has_zh"]:
            exp[p["primary"]]["zh"] += 1
        for a in p["also"]:
            exp[a["sid"]]["cross"] += 1
    for g in grey:
        exp[g["primary"]]["grey"] += 1
        if g["has_zh"]:
            exp[g["primary"]]["zh"] += 1
        for a in g["also"]:
            exp[a["sid"]]["cross"] += 1
    for ss in subs:
        for name in ("primary", "selected", "cross", "grey", "zh"):
            assert ss["counts"][name] == exp[ss["id"]][name], \
                f"{ss['id']}: counts.{name} {ss['counts'][name]} != {exp[ss['id']][name]}"

    # ---- stats ---------------------------------------------------------- #
    assert stats["papers"] == len(papers) and stats["grey"] == len(grey)
    assert stats["subsections"] == 56 and stats["sections"] == 11
    assert stats["cited"] == sum(p["selected"] for p in papers) + sum(g["selected"] for g in grey)
    assert sum(stats["years"].values()) == len(papers)
    assert list(stats["years"]) == sorted(stats["years"], key=lambda y: -int(y)), "years not descending"
    assert list(stats["per_section"]) == [s["id"] for s in sections]
    assert sum(stats["per_section"].values()) == len(papers)
    assert stats["generated"] == tax["generated"]
    assert isinstance(stats["stream_items"], int)
    assert stats["zh"] == sum(p["has_zh"] for p in papers) + sum(g["has_zh"] for g in grey) == len(summaries)
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", stats["source_generated"] or ""), "stats.source_generated missing"
    for k in ("stream_polarity", "stream_per_source", "stream_per_op", "stream_per_sub"):
        assert isinstance(stats.get(k), dict), f"stats.{k} missing"
    assert set(stats["stream_polarity"]) == {"good", "bad", "mixed"}
    assert set(stats["stream_per_sub"]) <= set(sids), "stats.stream_per_sub has ids outside the taxonomy"

    # ---- stream files ---------------------------------------------------- #
    if (DATA / "stream.json").exists():
        stream = load("stream.json")
        assert stream.get("taxonomy_generated") == tax["generated"], \
            f"stream.json classified against taxonomy {stream.get('taxonomy_generated')!r}, taxonomy.json is {tax['generated']!r}"
        assert stats["stream_items"] == len(stream["items"]) and stats["stream_updated"] == stream["generated"]
        assert sum(stats["stream_polarity"].values()) == len(stream["items"])
        for it in stream["items"]:
            for sid in it["subsections"]:
                assert sid in sid_pos, f"stream item {it['id']}: subsection {sid!r} not in taxonomy"
        assert (DATA / "stream_recent.json").exists(), "stream_recent.json missing"
        recent = load("stream_recent.json")
        assert recent["generated"] == stream["generated"]
        assert len(recent["items"]) == min(12, len(stream["items"]))
        dates = [it["date"] for it in recent["items"]]
        assert dates == sorted(dates, reverse=True), "stream_recent.json not newest first"
        assert {it["id"] for it in recent["items"]} <= {it["id"] for it in stream["items"]}

    # ---- freshness against the paper clone (local only) ------------------ #
    if OVERLEAF.exists():
        sources = [OVERLEAF / "outline.json", OVERLEAF / "research" / "corpus_full.json",
                   OVERLEAF / "research" / "grey_v2.json", OVERLEAF / "research" / "summaries_zh.json",
                   OVERLEAF / "research" / "labels_method_style.json"]
        newest = max(p.stat().st_mtime for p in sources if p.exists())
        built = (DATA / "taxonomy.json").stat().st_mtime
        assert newest <= built, "the paper clone is newer than site/data: run python3 pipeline/build_data.py"
        with (OVERLEAF / "research" / "corpus_full.json").open(encoding="utf-8") as fh:
            corpus_generated = json.load(fh).get("generated")
        assert stats["source_generated"] == corpus_generated, \
            f"stats.source_generated {stats['source_generated']!r} != corpus_full.generated {corpus_generated!r}"
        with (OVERLEAF / "outline.json").open(encoding="utf-8") as fh:
            outline = json.load(fh)
        for sec in outline["sections"]:
            for j, sub in enumerate(sec.get("subsections") or [], start=1):
                sid = f"s{int(sec['number'])}_{j}"
                assert strip_latex(sub.get("title")) == next(ss["title"] for ss in subs if ss["id"] == sid), \
                    f"{sid}: title differs from outline.json"

    # ---- unit checks on the LaTeX stripper ------------------------------ #
    assert strip_latex(r"\texttt{a\_b} \citep{x,y} in Sections 4--9 \emph{now}.") == "a_b in Sections 4–9 now."
    assert strip_latex(r"keep 2% budget and \cref{tab:x}") == "keep 2% budget and"
    assert strip_latex(r"``q'' \textbf{\emph{n}} \href{http://x}{t} \{b\}") == "“q” n t {b}"
    assert clean_bullets(["Literature pass: 35 papers", "References to start from: a", "Further reading: b", "Keep"]) == ["Keep"]
    assert kebab("Identity, Credentials, & Delegation") == "identity-credentials-and-delegation"

    print(f"OK: sections={len(sections)} subsections={len(subs)} papers={len(papers)} grey={len(grey)} "
          f"summaries={len(summaries)} cited={stats['cited']}")
    for a in anomalies:
        print("ANOMALY:", a)
    return 0


if __name__ == "__main__":
    sys.exit(main())
