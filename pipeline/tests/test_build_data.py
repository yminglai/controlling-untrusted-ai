#!/usr/bin/env python3
"""Checks for the files that pipeline/build_data.py writes to site/data/.

Run from the project root after a build:

    python3 pipeline/build_data.py
    python3 pipeline/tests/test_build_data.py

Plain asserts; exit code 0 means every check passed. Soft findings (for example
papers whose one_line is empty) are printed as "ANOMALY:" lines instead of failing.
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "site" / "data"
sys.path.insert(0, str(ROOT / "pipeline"))

from build_data import PAPER_TOOLING, kebab, source_date, strip_latex, structure_fingerprint  # noqa: E402

N_SECTIONS, N_SUBSECTIONS = 11, 35   # outline.json of 2026-10-21
PART_TITLES = ["The Problem", "Control Outside the Model", "Control Inside the Model", "Verification, Deployment, and Outlook"]
NEUTRAL_SECTIONS = {"s1", "s3", "s11"}   # no operation, gray
SECTION_OPERATIONS = {"s2": ["failures"], "s4": ["constrain"], "s5": ["observe"], "s6": ["intervene"],
                      "s7": ["steer"], "s8": ["train"], "s9": ["verify"], "s10": ["deploy"]}
OPERATION_IDS = ["failures", "constrain", "observe", "intervene", "steer", "train", "verify", "deploy"]
TIER_IDS = ["benign", "external", "insider"]

ALLOWED_COLOURS = {
    "#2E2E2E", "#7D7D7D", "#C7C7C7", "#EAEAEA", "#F7F7F7", "#FFFFFF",
    "#D95358", "#E27553", "#598DD2", "#E09A3B", "#65C2B9", "#8D86E8",
    "#62A16E", "#A37CAD", "#6FCBEF", "#E072AF", "#D1B745", "#C7A678", "#75A4B5",
}
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LATEX_LEFTOVER = re.compile(r"\\[A-Za-z]+|--|[{}]")
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
    stats = load("stats.json")

    # ---- taxonomy ------------------------------------------------------- #
    sections = tax["sections"]
    subs = [ss for s in sections for ss in s["subsections"]]
    assert len(sections) == N_SECTIONS, f"expected {N_SECTIONS} sections, got {len(sections)}"
    assert len(subs) == N_SUBSECTIONS, f"expected {N_SUBSECTIONS} subsections, got {len(subs)}"
    sids = [ss["id"] for ss in subs]
    assert len(set(sids)) == N_SUBSECTIONS, "subsection ids are not unique"
    sid_pos = {sid: i for i, sid in enumerate(sids)}
    op_ids = {o["id"] for o in tax["operations"]}
    assert tax["title"] == "Controlling Untrusted AI: A Survey"
    assert tax["thesis"].strip() and len(tax["readers"]) == 3
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", tax["generated"])
    assert tax["structure"] == structure_fingerprint(sections), "taxonomy.structure is not the fingerprint of its subsection list"
    assert [r["id"] for r in tax["requirements"]] == ["correct", "compliant", "in-scope", "within-budget", "safe"]
    assert [f["id"] for f in tax["failure_sources"]] == TIER_IDS
    assert all(f["blurb"].strip() and f["color"] in ALLOWED_COLOURS for f in tax["failure_sources"])
    assert [o["id"] for o in tax["operations"]] == OPERATION_IDS
    assert {o["id"]: o["label"] for o in tax["operations"]} == {
        "failures": "How Agents Fail", "constrain": "Constrain", "observe": "Observe", "intervene": "Intervene",
        "steer": "Steer", "train": "Train", "verify": "Verify", "deploy": "Deploy"}

    # parts: every section in exactly one part, in section order; "part" is the index into parts
    parts = tax["parts"]
    assert [p["title"] for p in parts] == PART_TITLES, [p["title"] for p in parts]
    listed = [sid for p in parts for sid in p["sections"]]
    assert listed == [s["id"] for s in sections], f"parts do not cover the sections once each in order: {listed}"
    for i, p in enumerate(parts):
        for sid in p["sections"]:
            assert next(s for s in sections if s["id"] == sid)["part"] == i, f"{sid}: part index != {i}"
    for o in tax["operations"]:
        sec = next(s for s in sections if s["id"] == o["section"])
        assert o["color"] == sec["color"] and o["color"] in ALLOWED_COLOURS, f"operation {o['id']}: colour is not its section's"
        assert o["id"] in sec["operations"], f"operation {o['id']}: section {sec['id']} does not list it"
        if o["id"] == "failures":
            assert o["lever"] is None, "failures is not a control operation and has no lever"
        else:
            assert o["lever"] == parts[sec["part"]]["title"], f"operation {o['id']}: lever {o['lever']!r} is not its part title"
    # every operation sits on exactly one section, in section order
    assert [o for s in sections for o in s["operations"]] == OPERATION_IDS, [s["operations"] for s in sections]

    section_slugs = Counter()
    sub_slugs = Counter()
    for s in sections:
        assert s["id"] == f"s{s['number']}", s["id"]
        assert s["title"].strip(), f"{s['id']}: empty title"
        assert SLUG.match(s["slug"]), f"{s['id']}: slug {s['slug']!r} not kebab-case"
        assert s["color"] in ALLOWED_COLOURS, f"{s['id']}: colour {s['color']} not a token"
        assert "purpose" not in s, f"{s['id']}: the outline's writer notes are not reader content"
        section_slugs[s["slug"]] += 1
        assert isinstance(s["operations"], list), s["id"]
        if s["id"] in NEUTRAL_SECTIONS:
            assert s["operations"] == [] and s["color"] == "#7D7D7D", f"{s['id']}: should be neutral"
        else:
            assert s["operations"] == SECTION_OPERATIONS[s["id"]], f"{s['id']}: operations {s['operations']}"
            for op_id in s["operations"]:
                assert op_id in op_ids, f"{s['id']}: operation {op_id!r} unknown"
                op = next(o for o in tax["operations"] if o["id"] == op_id)
                assert op["section"] == s["id"] and op["color"] == s["color"], f"{s['id']}: operation mismatch"
        for j, ss in enumerate(s["subsections"], start=1):
            assert ss["id"] == f"s{s['number']}_{j}", f"positional id mismatch: {ss['id']}"
            assert ss["number"] == f"{s['number']}.{j}", ss["number"]
            assert ss["title"].strip(), f"{ss['id']}: empty title"
            assert not LATEX_LEFTOVER.search(ss["title"]), f"{ss['id']}: LaTeX left in title"
            assert SLUG.match(ss["slug"]), f"{ss['id']}: slug {ss['slug']!r} not kebab-case"
            sub_slugs[ss["slug"]] += 1
            assert "bullets" not in ss, f"{ss['id']}: author plan notes are not reader content"
            assert set(ss["counts"]) == {"primary", "selected", "cross", "grey"}, ss["id"]
    assert all(n == 1 for n in section_slugs.values()), "section slugs not unique"
    assert all(n == 1 for n in sub_slugs.values()), "subsection slugs not unique"

    # ---- papers --------------------------------------------------------- #
    keys = [p["key"] for p in papers]
    dup = [k for k, n in Counter(keys).items() if n > 1]
    assert not dup, f"duplicate keys in papers.json: {dup[:10]}"
    paper_keys = set(keys)
    fields = ["key", "arxiv_id", "url", "title", "authors", "year", "primary", "section", "score",
              "selected", "label", "one_line", "reason", "also", "reading_rank"]
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
               "one_line", "confidence", "selected", "also"]
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

    # ---- counts --------------------------------------------------------- #
    exp = {sid: Counter() for sid in sids}
    for p in papers:
        exp[p["primary"]]["primary"] += 1
        if p["selected"]:
            exp[p["primary"]]["selected"] += 1
        for a in p["also"]:
            exp[a["sid"]]["cross"] += 1
    for g in grey:
        exp[g["primary"]]["grey"] += 1
        for a in g["also"]:
            exp[a["sid"]]["cross"] += 1
    for ss in subs:
        for name in ("primary", "selected", "cross", "grey"):
            assert ss["counts"][name] == exp[ss["id"]][name], \
                f"{ss['id']}: counts.{name} {ss['counts'][name]} != {exp[ss['id']][name]}"

    # ---- stats ---------------------------------------------------------- #
    assert stats["papers"] == len(papers) and stats["grey"] == len(grey)
    assert stats["subsections"] == N_SUBSECTIONS and stats["sections"] == N_SECTIONS
    assert stats["papers"] == 1788, f"expected 1,788 papers, got {stats['papers']}"
    for sec in ("s2", "s4", "s5", "s6", "s7", "s8", "s9", "s10"):
        assert stats["per_section"][sec] > 0, f"{sec}: no papers"
    assert stats["cited"] == sum(p["selected"] for p in papers) + sum(g["selected"] for g in grey)
    assert sum(stats["years"].values()) == len(papers)
    assert list(stats["years"]) == sorted(stats["years"], key=lambda y: -int(y)), "years not descending"
    assert list(stats["per_section"]) == [s["id"] for s in sections]
    assert sum(stats["per_section"].values()) == len(papers)
    assert stats["generated"] == tax["generated"]
    assert isinstance(stats["stream_items"], int)
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", stats["source_generated"] or ""), "stats.source_generated missing"
    for k in ("stream_polarity", "stream_per_source", "stream_per_op", "stream_per_sub"):
        assert isinstance(stats.get(k), dict), f"stats.{k} missing"
    assert set(stats["stream_polarity"]) == {"good", "bad", "mixed"}
    assert set(stats["stream_per_sub"]) <= set(sids), "stats.stream_per_sub has ids outside the taxonomy"
    assert set(stats["stream_per_source"]) <= set(TIER_IDS), "stats.stream_per_source has values outside the tiers"
    assert set(stats["stream_per_op"]) <= set(OPERATION_IDS) - {"failures"}, "stats.stream_per_op has unknown operations"

    # ---- stream files ---------------------------------------------------- #
    if (DATA / "stream.json").exists():
        stream = load("stream.json")
        assert stream.get("taxonomy_structure") == tax["structure"], \
            f"stream.json filed against subsection list {stream.get('taxonomy_structure')!r}, taxonomy.json is {tax['structure']!r}: run pipeline/remap_stream.py"
        assert stream.get("taxonomy_generated") == tax["generated"], \
            f"stream.json classified against taxonomy {stream.get('taxonomy_generated')!r}, taxonomy.json is {tax['generated']!r}"
        order = [(it["date"], it["id"]) for it in stream["items"]]
        assert order == sorted(order, reverse=True), "stream.json is not in date desc, id desc order"
        assert stats["stream_items"] == len(stream["items"]) and stats["stream_updated"] == stream["generated"]
        assert sum(stats["stream_polarity"].values()) == len(stream["items"])
        for it in stream["items"]:
            assert 1 <= len(it["subsections"]) <= 4, f"stream item {it['id']}: {len(it['subsections'])} subsections"
            for sid in it["subsections"]:
                assert sid in sid_pos, f"stream item {it['id']}: subsection {sid!r} not in taxonomy"
            assert set(it["failure_sources"]) <= set(TIER_IDS), f"stream item {it['id']}: failure_sources {it['failure_sources']}"
            assert set(it["operations"]) <= set(OPERATION_IDS) - {"failures"}, f"stream item {it['id']}: operations {it['operations']}"
        assert (DATA / "stream_recent.json").exists(), "stream_recent.json missing"
        recent = load("stream_recent.json")
        assert recent["generated"] == stream["generated"]
        assert len(recent["items"]) == min(12, len(stream["items"]))
        dates = [it["date"] for it in recent["items"]]
        assert dates == sorted(dates, reverse=True), "stream_recent.json not newest first"
        assert {it["id"] for it in recent["items"]} <= {it["id"] for it in stream["items"]}

    # ---- freshness against the paper's tooling repository (local only) --- #
    if PAPER_TOOLING.exists():
        sources = [PAPER_TOOLING / "outline.json", PAPER_TOOLING / "research" / "corpus_full.json",
                   PAPER_TOOLING / "research" / "grey_v2.json", PAPER_TOOLING / "research" / "labels_method_style.json"]
        newest = max(p.stat().st_mtime for p in sources if p.exists())
        built = (DATA / "taxonomy.json").stat().st_mtime
        assert newest <= built, "the paper's tooling repository is newer than site/data: run python3 pipeline/build_data.py"
        with (PAPER_TOOLING / "research" / "corpus_full.json").open(encoding="utf-8") as fh:
            expected_source = source_date(json.load(fh), PAPER_TOOLING / "research" / "corpus_full.json")
        assert stats["source_generated"] == expected_source, \
            f"stats.source_generated {stats['source_generated']!r} != {expected_source!r} (corpus_full.generated or its file date)"
        with (PAPER_TOOLING / "outline.json").open(encoding="utf-8") as fh:
            outline = json.load(fh)
        for sec in outline["sections"]:
            assert strip_latex(sec["title"]) == next(s["title"] for s in sections if s["number"] == int(sec["number"])), \
                f"section {sec['number']}: title differs from outline.json"
            for j, sub in enumerate(sec.get("subsections") or [], start=1):
                sid = f"s{int(sec['number'])}_{j}"
                assert strip_latex(sub.get("title")) == next(ss["title"] for ss in subs if ss["id"] == sid), \
                    f"{sid}: title differs from outline.json"

    # ---- unit checks on the LaTeX stripper ------------------------------ #
    assert strip_latex(r"\texttt{a\_b} \citep{x,y} in Sections 4--9 \emph{now}.") == "a_b in Sections 4–9 now."
    assert strip_latex(r"keep 2% budget and \cref{tab:x}") == "keep 2% budget and"
    assert strip_latex(r"``q'' \textbf{\emph{n}} \href{http://x}{t} \{b\}") == "“q” n t {b}"
    assert kebab("Identity, Credentials, & Delegation") == "identity-credentials-and-delegation"

    print(f"OK: sections={len(sections)} subsections={len(subs)} papers={len(papers)} grey={len(grey)} "
          f"cited={stats['cited']}")
    for a in anomalies:
        print("ANOMALY:", a)
    return 0


if __name__ == "__main__":
    sys.exit(main())
