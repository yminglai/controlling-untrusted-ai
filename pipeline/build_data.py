#!/usr/bin/env python3
"""Build the site's data files from the paper repository.

Regenerate (from the project root, controlling-untrusted-ai/):

    python3 pipeline/build_data.py

Reads the read-only Overleaf clone (default: ../overleaf-ai-control next to the
project root; override with --overleaf PATH) and writes, under site/data/:

    taxonomy.json      parts, sections, operations, subsections, counts (indent=1)
    papers.json        1,788 arXiv papers                       (indent=None)
    grey.json          non-arXiv items, corpus grey + grey_v2   (indent=None)
    stats.json         headline numbers                         (indent=1)
    stream_recent.json the 12 newest stream items (when stream.json exists)

The field names and sort orders are those of SCHEMA.md. Output is deterministic
for a given --generated date (default: today). Pure standard library. The
script never modifies the Overleaf clone. Anomalies found in the sources are
printed to stdout, one per line, prefixed "ANOMALY:"; they do not stop the build.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import re
import sys
import unicodedata
from collections import Counter, OrderedDict
from pathlib import Path

# --------------------------------------------------------------------------- #
# Fixed vocabulary (BRIEF.md section map, SCHEMA.md enumerations)
# --------------------------------------------------------------------------- #

COLORS = {
    "ink": "#2E2E2E",
    "gray": "#7D7D7D",
    "coral": "#D95358",
    "terracotta": "#E27553",
    "blue": "#598DD2",
    "amber": "#E09A3B",
    "teal": "#65C2B9",
    "periwinkle": "#8D86E8",
    "forest": "#62A16E",
    "purple": "#A37CAD",
    "gold": "#D1B745",
}

# Section title (kebab-case) -> (operation ids, slug, colour). Keyed by title, not number, so a
# renumbered outline cannot mislabel a section: a title missing here gets no operation, a slug
# from its title and the neutral colour, and is reported as an anomaly. Section 7 carries both
# model-level operations; they take the section's colour, since colour is section identity.
SECTION_META = {
    "introduction": ((), "introduction", COLORS["gray"]),
    "failure-modes-of-deployed-agents": (("failures",), "failures", COLORS["coral"]),
    "preliminaries": ((), "preliminaries", COLORS["gray"]),
    "action-constraints": (("constrain",), "constrain", COLORS["terracotta"]),
    "monitoring": (("monitor",), "monitor", COLORS["blue"]),
    "intervention": (("intervene",), "intervene", COLORS["amber"]),
    "model-level-methods": (("steer", "train"), "model", COLORS["teal"]),
    "evaluation-methodology": (("evaluate",), "evaluate", COLORS["forest"]),
    "composition-and-assurance": (("deploy",), "deploy", COLORS["purple"]),
    "outlook": ((), "outlook", COLORS["gray"]),
}

# Chip labels of the control operations. "failures" (section 2) is not a control
# operation: it takes the section title as label and has no lever.
OPERATION_LABELS = {
    "constrain": "Constrain",
    "monitor": "Monitor",
    "intervene": "Intervene",
    "steer": "Steer",
    "train": "Train",
    "evaluate": "Evaluate",
    "deploy": "Deploy",
}

REQUIREMENTS = [
    {"id": "correct", "label": "Correct"},
    {"id": "compliant", "label": "Compliant"},
    {"id": "in-scope", "label": "In scope"},
    {"id": "within-budget", "label": "Within budget"},
    {"id": "safe", "label": "Safe"},
]

# The three tiers of the attack side (outline.json, Section 2 purpose). The field keeps
# its name "failure_sources" in taxonomy.json and in the stream items.
FAILURE_SOURCES = [
    {
        "id": "benign",
        "label": "Benign",
        "color": COLORS["coral"],
        "blurb": "The agent goes out of control with no attacker present.",
    },
    {
        "id": "external",
        "label": "External",
        "color": COLORS["amber"],
        "blurb": "An outsider redirects the agent through what it reads, calls, or remembers.",
    },
    {
        "id": "insider",
        "label": "Insider",
        "color": COLORS["purple"],
        "blurb": "Someone with legitimate partial access contributes to loss of control, whether a "
                 "person (data, weights, pipeline, credentials, oversight) or the model itself.",
    },
]

# Subsection ids of the 17 October 2026 outline (56 subsections) -> ids of the 19 October 01:13
# outline (11 sections, 36 subsections). Identity entries are kept so the table doubles as the
# list of ids that existed on 17 October. SID_MAP_2026_10_19 continues onto the current outline;
# SID_MAP_FROM_2026_10_17 is the composition, used for sources still on the 17 October structure
# (research/grey_v2.json) and by pipeline/remap_stream.py for a stream from that date.
# Targets follow the subsection titles of outline.json as of 2026-10-19 01:13:
#   s1 Control Problem, Scope, Methodology, Contributions; s2 Benign Failures, External Attacks,
#   Insider Threats, Multi-Agent Failures; s3 Threat Model, Control Protocols, Assessment Criteria;
#   s4 Confinement, Formal Enforcement, Information-Flow Control, Delegated Authority; s5
#   Observability, Automated Monitors, Untrusted Monitors, Human Oversight; s6 Approval Gates,
#   Resampling, Shutdown; s7 Instruction Hierarchies, Memory Management, Activation Steering;
#   s8 Safety Fine-Tuning, Adversarial Training, Representation-Level Methods; s9 Benchmarks, Control
#   Evaluations, Model Auditing; s10 Reference Architectures, Governance, Assurance; s11 Open
#   Problems, Conclusion.
SID_MAP_2026_10_17 = {
    "s1_1": "s1_1", "s1_2": "s1_1", "s1_3": "s1_2",
    "s2_1": "s2_1", "s2_2": "s2_2", "s2_3": "s2_3", "s2_4": "s2_3", "s2_5": "s3_1",
    "s3_1": "s3_1", "s3_2": "s3_1", "s3_3": "s3_3", "s3_4": "s3_3", "s3_5": "s3_2",
    "s4_1": "s4_1", "s4_2": "s4_1", "s4_3": "s4_2", "s4_4": "s4_3", "s4_5": "s4_4",
    "s5_1": "s5_1", "s5_2": "s5_2", "s5_3": "s5_2", "s5_4": "s5_2", "s5_5": "s5_3", "s5_6": "s5_4",
    "s6_1": "s6_1", "s6_2": "s6_1", "s6_3": "s6_2", "s6_4": "s6_3", "s6_5": "s6_3",
    "s7_1": "s7_1", "s7_2": "s7_2", "s7_3": "s7_1", "s7_4": "s7_3", "s7_5": "s7_3",
    "s8_1": "s8_1", "s8_2": "s8_1", "s8_3": "s8_1", "s8_4": "s8_2", "s8_5": "s8_3", "s8_6": "s8_1",
    "s9_1": "s9_1", "s9_2": "s9_1", "s9_3": "s9_2", "s9_4": "s9_2", "s9_5": "s9_3", "s9_6": "s9_1",
    "s10_1": "s10_1", "s10_2": "s10_2", "s10_3": "s10_3", "s10_4": "s10_3", "s10_5": "s10_3",
    "s11_1": "s11_1", "s11_2": "s11_1", "s11_3": "s11_1", "s11_4": "s11_1", "s11_5": "s11_2",
}

# Subsection ids of the 19 October 2026 01:13 outline (36 subsections) -> ids of the current
# outline (19 October 2026 01:29: 10 sections, 29 subsections). The three steering and the three
# training subsections became 7.1 Inference-Time Steering and 7.2 Training-Time Methods; 2.4
# Multi-Agent Failures folded into 2.3 Insider Threats (the model and its peers as insiders); 5.1
# Observability into 5.1 Automated Monitors; 10.2 Governance and 10.3 Assurance into 9.2 Safety
# Cases; sections 9 to 11 moved up by one.
SID_MAP_2026_10_19 = {
    "s1_1": "s1_1", "s1_2": "s1_2", "s1_3": "s1_3", "s1_4": "s1_4",
    "s2_1": "s2_1", "s2_2": "s2_2", "s2_3": "s2_3", "s2_4": "s2_3",
    "s3_1": "s3_1", "s3_2": "s3_2", "s3_3": "s3_3",
    "s4_1": "s4_1", "s4_2": "s4_2", "s4_3": "s4_3", "s4_4": "s4_4",
    "s5_1": "s5_1", "s5_2": "s5_1", "s5_3": "s5_2", "s5_4": "s5_3",
    "s6_1": "s6_1", "s6_2": "s6_2", "s6_3": "s6_3",
    "s7_1": "s7_1", "s7_2": "s7_1", "s7_3": "s7_1",
    "s8_1": "s7_2", "s8_2": "s7_2", "s8_3": "s7_2",
    "s9_1": "s8_1", "s9_2": "s8_2", "s9_3": "s8_3",
    "s10_1": "s9_1", "s10_2": "s9_2", "s10_3": "s9_2",
    "s11_1": "s10_1", "s11_2": "s10_2",
}


def compose_maps(*maps: dict) -> dict:
    """compose_maps(a, b)[x] == b[a[x]] for every key of a that every later map carries."""
    out = {}
    for key in maps[0]:
        value = key
        for m in maps:
            value = m.get(value)
            if value is None:
                break
        if value is not None:
            out[key] = value
    return out


SID_MAP_FROM_2026_10_17 = compose_maps(SID_MAP_2026_10_17, SID_MAP_2026_10_19)   # 56 -> 29

# Earlier structures a source can be filed on -> the map of its ids onto the current outline.
STRUCTURE_MAPS = {"2026-10-17": SID_MAP_FROM_2026_10_17, "2026-10-19": SID_MAP_2026_10_19}

# Ids from the retrieval-time outline (research/QUERIES.md) that still appear in the grey
# sources and did not exist on 17 October, as 17 October ids (then mapped on):
#   s2_6  shutdown avoidance, self-replication, collusion  -> s2_4 The Model as Insider      (now s2_3)
#   s2_7  compounding errors, irreversible side effects    -> s2_1 Benign Failures           (now s2_1)
#   s2_8  failure-mode taxonomy, control requirements      -> s2_5 From Failures to Control Requirements (now s3_1)
#   s6_6  human oversight, automation bias, review budgets -> s5_6 Human Review under a Budget (now s5_3)
# Every remap is reported as an anomaly so the sources can be fixed upstream.
SID_REMAP = {"s2_6": "s2_4", "s2_7": "s2_1", "s2_8": "s2_5", "s6_6": "s5_6"}

# Structure of research/grey_v2.json. Its sids are read as 17 October ids and mapped through
# SID_MAP_FROM_2026_10_17; set to "current" once the file is re-filed on the current outline.
GREY_V2_STRUCTURE = "2026-10-17"

# Cited grey items whose bib entry carries no URL. Publisher or DOI landing pages,
# each checked to resolve on 2026-10-17. Used only when the source URL is empty.
GREY_URL_FALLBACK = {
    "shavit2023practices": "https://cdn.openai.com/papers/practices-for-governing-agentic-ai-systems.pdf",
    "orseau2016safely": "https://intelligence.org/files/Interruptibility.pdf",
    "soares2015corrigibility": "https://intelligence.org/files/Corrigibility.pdf",
    "ligatti2005edit": "https://doi.org/10.1007/s10207-004-0046-8",
    "avizienis2004basic": "https://doi.org/10.1109/TDSC.2004.2",
    "sabelfeld2003language": "https://doi.org/10.1109/JSAC.2002.806121",
    "schneider2000enforceable": "https://doi.org/10.1145/353323.353382",
    "axelsson2000base": "https://doi.org/10.1145/357830.357849",
    "hardy1988confused": "https://doi.org/10.1145/54289.871709",
    "denning1987intrusion": "https://doi.org/10.1109/TSE.1987.232894",
    "denning1976lattice": "https://doi.org/10.1145/360051.360056",
    "saltzer1975protection": "https://doi.org/10.1109/PROC.1975.9939",
    "lampson1973note": "https://doi.org/10.1145/362375.362389",
    "anderson1972computer": "https://csrc.nist.gov/csrc/media/publications/conference-paper/1998/10/08/"
                            "proceedings-of-the-21st-nissc-1998/documents/early-cs-papers/ande72.pdf",
}

# Grey items whose sid in the sources names a subsection their subject does not match.
# The three vendor posts are prompt-injection defences, which belong to 2.2 External
# Attacks; their sid s2_3 is "Insider Threats". Every override is reported as an anomaly
# so the source can be fixed.
GREY_SID_OVERRIDE = {
    "anthropic2025promptinjection": "s2_2",
    "openai2025promptinjections": "s2_2",
    "google2025layereddefense": "s2_2",
}

# Grey confidence is a closed set (SCHEMA.md). Source notes are mapped onto it.
CONFIDENCE_MAP = {"verified": "verified", "existing bib entry": "verified", "likely": "likely", "unverified": "unverified"}
CONFIDENCE_VALUES = ("verified", "likely", "unverified")

# Placement reasons that are pipeline bookkeeping, rewritten for readers.
REASON_REWRITES = [
    (re.compile(r"^requested by name by the pass-\d agent\.?$", re.IGNORECASE), "Named in the section plan"),
]

# --------------------------------------------------------------------------- #
# Text helpers
# --------------------------------------------------------------------------- #

_CITE_LIKE = re.compile(
    r"\\(?:citep|citet|citealp|citealt|citeauthor|citeyearpar|citeyear|cite|"
    r"Cref|cref|autoref|eqref|ref|label|footnote)\*?"
    r"(?:\[[^\]]*\]){0,2}\{[^{}]*\}"
)
_HREF = re.compile(r"\\href\{[^{}]*\}\{([^{}]*)\}")
_WRAP = re.compile(
    r"\\(?:texttt|emph|textit|textbf|textsc|textrm|textsf|textnormal|mbox|url|text)"
    r"\{([^{}]*)\}"
)
_DOTS = re.compile(r"\\(?:ldots|dots)\b")
_OTHER_CMD = re.compile(r"\\[A-Za-z]+\*?")
_ESCAPES = [("\\_", "_"), ("\\&", "&"), ("\\%", "%"), ("\\#", "#"), ("\\$", "$")]
_LBRACE, _RBRACE = "\ue000", "\ue001"
_SPACE_BEFORE_PUNCT = re.compile(r"\s+([.,;:)\]!?])")
_SPACE_AFTER_OPEN = re.compile(r"([(\[])\s+")


def strip_latex(text: str | None) -> str:
    """Turn a LaTeX-flavoured outline string into plain text.

    Removes \\citep{}, \\cite{}, \\cref{} and friends; unwraps \\texttt{x},
    \\emph{x} and similar to x; unescapes \\_ \\& \\% \\# \\$; turns -- (and ---)
    into an en dash; normalises ``quotes'' and ~; drops stray braces and tidies
    whitespace. A bare % is kept (it is a percent sign in the outline, not a
    comment).
    """
    if not text:
        return ""
    t = str(text)
    t = _CITE_LIKE.sub("", t)
    t = _HREF.sub(r"\1", t)
    while True:
        new = _WRAP.sub(r"\1", t)
        if new == t:
            break
        t = new
    t = _DOTS.sub("...", t)
    # protect escaped braces, then remove remaining commands
    t = t.replace("\\{", _LBRACE).replace("\\}", _RBRACE)
    for src, dst in _ESCAPES:
        t = t.replace(src, dst)
    t = _OTHER_CMD.sub("", t)
    t = t.replace("---", "\u2013").replace("--", "\u2013")
    t = t.replace("``", "\u201c").replace("''", "\u201d")
    t = t.replace("~", " ")
    t = t.replace("{", "").replace("}", "")
    t = t.replace(_LBRACE, "{").replace(_RBRACE, "}")
    t = re.sub(r"\s+", " ", t)
    t = _SPACE_BEFORE_PUNCT.sub(r"\1", t)
    t = _SPACE_AFTER_OPEN.sub(r"\1", t)
    return t.strip()


_MATH_SPAN = re.compile(r"\$([^$\d][^$]{0,24})\$")
_SUPERSCRIPTS = {"2": "\u00b2", "3": "\u00b3", "n": "\u207f", "N": "\u1d3a"}


def clean_math(text: str | None) -> str:
    """Render the little inline TeX that survives in paper titles as plain text.

    "$τ$-bench" -> "τ-bench"; "E$^2$AT" -> "E²AT"; "AI-45$^{\\circ}$ Law" -> "AI-45° Law".
    Dollar amounts ("about $60") are untouched: a span only counts when it is
    closed and does not start with a digit.
    """
    if not text:
        return ""
    t = str(text)

    def inner(m: re.Match) -> str:
        x = m.group(1)
        x = re.sub(r"\^\{\\circ\}|\^\\circ", "\u00b0", x)
        x = re.sub(r"\^\{?([23nN])\}?", lambda k: _SUPERSCRIPTS[k.group(1)], x)
        x = re.sub(r"\\(?:mathrm|mathit|mathbf|text|textrm)\{([^{}]*)\}", r"\1", x)
        x = x.replace("\\circ", "\u00b0").replace("{", "").replace("}", "")
        return x.strip()

    t = _MATH_SPAN.sub(inner, t)
    return re.sub(r"\s{2,}", " ", t).strip()


def clean_reason(reason: str | None) -> str:
    r = (reason or "").strip()
    for pat, new in REASON_REWRITES:
        if pat.match(r):
            return new
    return r


def kebab(text: str) -> str:
    """ASCII kebab-case slug."""
    t = unicodedata.normalize("NFKD", text or "")
    t = t.encode("ascii", "ignore").decode("ascii").lower()
    t = t.replace("&", " and ")
    t = re.sub(r"[^a-z0-9]+", "-", t).strip("-")
    return t or "item"


def unique_slug(slug: str, used: set[str]) -> str:
    cand, n = slug, 2
    while cand in used:
        cand = f"{slug}-{n}"
        n += 1
    used.add(cand)
    return cand


def to_year(value) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if value is None:
        return None
    m = re.search(r"\b(1[89]\d{2}|2\d{3})\b", str(value))
    return int(m.group(1)) if m else None


def norm_url(url: str | None) -> str:
    u = (url or "").strip().lower()
    if not u:
        return ""
    u = re.sub(r"^https?://", "", u)
    u = re.sub(r"^www\.", "", u)
    u = u.split("#", 1)[0]
    return u.rstrip("/")


def norm_title(title: str | None) -> str:
    t = unicodedata.normalize("NFKD", title or "").lower()
    return re.sub(r"[^a-z0-9]+", " ", t).strip()


def label_for(key: str, short_label: str | None, title: str, labels: dict) -> str:
    if labels.get(key):
        return labels[key]
    if short_label:
        return short_label
    head = (title or "").split(":", 1)[0].strip()
    return head or (title or "")


def section_of(sid: str) -> str:
    return sid.split("_", 1)[0]


def as_list(value) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value if str(v).strip()]
    return [str(value)]


def arxiv_id_from_url(url: str | None) -> str | None:
    m = re.search(r"arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5})", url or "")
    return m.group(1) if m else None


# --------------------------------------------------------------------------- #
# Builders
# --------------------------------------------------------------------------- #

class Anomalies:
    def __init__(self) -> None:
        self.items: list[str] = []

    def add(self, msg: str) -> None:
        self.items.append(msg)


def current_sid(sid: str) -> str | None:
    """Map a 17 October (or older) subsection id onto the current outline; None if unknown."""
    return SID_MAP_FROM_2026_10_17.get(SID_REMAP.get(sid, sid))


def resolve_sid(sid, sid_pos: dict, what: str, anomalies: Anomalies, structure: str = "current") -> str:
    """Return a subsection id of the current taxonomy.

    structure "current": the id is taken as is when the taxonomy has it; otherwise it is tried
    as a stale id and the remap is reported. structure "2026-10-17" or "2026-10-19": the id is
    read as an id of that outline and mapped through STRUCTURE_MAPS. In every mode an id that
    does not land in the taxonomy is reported, so the tests catch it.
    """
    sid = (sid or "").strip()
    if structure != "current":
        table = STRUCTURE_MAPS[structure]
        key = SID_REMAP.get(sid, sid) if structure == "2026-10-17" else sid
        new = table.get(key)
        if new is None:
            anomalies.add(f"{what}: sid {sid!r} is not a {structure} id")
            return sid
        if new not in sid_pos:
            anomalies.add(f"{what}: sid {sid!r} maps to {new!r}, which is not in the taxonomy")
        return new
    if sid in sid_pos:
        return sid
    new = current_sid(sid)
    if new and new in sid_pos:
        anomalies.add(f"{what}: stale sid {sid!r} remapped to {new!r}")
        return new
    anomalies.add(f"{what}: sid {sid!r} not in taxonomy")
    return sid


def build_parts(outline: dict, sections: list[dict], anomalies: Anomalies) -> list[dict]:
    """Parts from outline.json as [{title, sections: [section ids]}]; stamps every section
    with its "part" index (None when the outline leaves a section out)."""
    by_id = {s["id"]: s for s in sections}
    parts = []
    for i, part in enumerate(outline.get("parts") or []):
        ids = []
        for num in part.get("sections") or []:
            sid = f"s{int(num)}"
            sec = by_id.get(sid)
            if sec is None:
                anomalies.add(f"parts: {part.get('title')!r} lists unknown section {num!r}")
                continue
            if sec.get("part") is not None:
                anomalies.add(f"parts: section {sid} listed in more than one part")
                continue
            sec["part"] = i
            ids.append(sid)
        parts.append({"title": strip_latex(part.get("title")), "sections": ids})
    for sec in sections:
        if sec.get("part") is None:
            sec["part"] = None
            if parts:
                anomalies.add(f"parts: section {sec['id']} is in no part")
    return parts


def build_operations(sections: list[dict], parts: list[dict]) -> list[dict]:
    """One entry per operation in section order (Section 7 carries steer and train). "lever" is
    the title of the operation's part, null for "failures", which is not a control operation.
    The colour is the section's: colour is section identity."""
    ops = []
    for sec in sections:
        for op in sec["operations"]:
            is_control = op in OPERATION_LABELS
            part = parts[sec["part"]] if is_control and sec.get("part") is not None else None
            ops.append(OrderedDict([
                ("id", op),
                ("label", OPERATION_LABELS.get(op, sec["title"])),
                ("section", sec["id"]),
                ("color", sec["color"]),
                ("lever", part["title"] if part else None),
            ]))
    return ops


def build_sections(outline: dict, anomalies: Anomalies) -> tuple[list[dict], list[str]]:
    """Sections and subsections from outline.json (parts and counts filled in later). Operations,
    slug and colour come from SECTION_META by section title; every operation must sit on exactly
    one section. The outline's section purposes are writer notes and are not emitted."""
    sections = []
    sid_order: list[str] = []
    used_section_slugs: set[str] = set()
    used_sub_slugs: set[str] = set()
    seen_ops: Counter = Counter()
    for sec in outline["sections"]:
        k = int(sec["number"])
        title = strip_latex(sec["title"])
        meta = SECTION_META.get(kebab(title))
        if meta is None:
            anomalies.add(f"section {k} {title!r}: title not in SECTION_META; emitted without operation, in gray")
            meta = ((), kebab(title), COLORS["gray"])
        ops, slug, color = meta
        seen_ops.update(ops)
        slug = unique_slug(slug, used_section_slugs)
        subs = []
        for j, sub in enumerate(sec.get("subsections") or [], start=1):
            sid = f"s{k}_{j}"
            sid_order.append(sid)
            subs.append({
                "id": sid,
                "number": f"{k}.{j}",
                "title": strip_latex(sub.get("title")),
                "slug": unique_slug(kebab(strip_latex(sub.get("title"))), used_sub_slugs),
                "counts": {"primary": 0, "selected": 0, "cross": 0, "grey": 0},
            })
        sections.append(OrderedDict([
            ("id", f"s{k}"),
            ("number", k),
            ("title", title),
            ("slug", slug),
            ("operations", list(ops)),
            ("color", color),
            ("part", None),
            ("subsections", subs),
        ]))
    expected = set(OPERATION_LABELS) | {"failures"}
    missing = sorted(expected - set(seen_ops))
    if missing:
        anomalies.add(f"operations with no section in this outline: {missing}")
    twice = sorted(o for o, n in seen_ops.items() if n > 1)
    if twice:
        anomalies.add(f"operations on more than one section: {twice}")
    return sections, sid_order


def build_papers(corpus: dict, labels: dict, sid_pos: dict, anomalies: Anomalies) -> list[dict]:
    out = []
    seen = Counter()
    empty_one_line = Counter()
    for p in corpus["papers"]:
        key = p.get("key") or ""
        seen[key] += 1
        year = to_year(p.get("year"))
        if year is None:
            anomalies.add(f"paper {key!r}: year {p.get('year')!r} not parseable")
        primary = resolve_sid(p.get("primary"), sid_pos, f"paper {key!r} primary", anomalies)
        also = []
        for a in p.get("also") or []:
            sid = resolve_sid(a.get("sid"), sid_pos, f"paper {key!r} also", anomalies)
            if sid not in sid_pos or sid == primary:
                continue
            also.append({"sid": sid, "score": a.get("score")})
        also.sort(key=lambda a: (-(a["score"] or 0), sid_pos.get(a["sid"], 10**6)))
        one_line = (p.get("one_line") or "").strip()
        if not one_line:
            empty_one_line[p.get("score")] += 1
        arxiv_id = (p.get("arxiv_id") or "").strip()
        if not arxiv_id:
            anomalies.add(f"paper {key!r}: no arxiv_id")
        out.append(OrderedDict([
            ("key", key),
            ("arxiv_id", arxiv_id),
            ("url", f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else ""),
            ("title", clean_math((p.get("title") or "").strip())),
            ("authors", as_list(p.get("authors"))),
            ("year", year),
            ("primary", primary),
            ("section", section_of(primary)),
            ("score", p.get("score")),
            ("selected", bool(p.get("selected"))),
            ("label", clean_math(label_for(key, p.get("short_label"), p.get("title") or "", labels))),
            ("one_line", clean_math(one_line)),
            ("reason", clean_reason(p.get("reason"))),
            ("also", also),
            ("reading_rank", p.get("reading_rank")),
        ]))
    dups = sorted(k for k, n in seen.items() if n > 1)
    if dups:
        anomalies.add(f"papers: duplicate keys {dups}")
    if empty_one_line:
        total = sum(empty_one_line.values())
        by_score = ", ".join(f"score {s}: {n}" for s, n in sorted(empty_one_line.items(), key=str))
        anomalies.add(f"papers: {total} with empty one_line ({by_score})")
    sort_papers(out, sid_pos)
    return out


def sort_papers(papers: list[dict], sid_pos: dict) -> None:
    """SCHEMA.md order: primary (section order), selected desc, score desc, reading_rank asc, year desc, title."""
    papers.sort(key=lambda r: (
        sid_pos.get(r["primary"], 10**6),
        not r["selected"],
        -(r["score"] or 0),
        r["reading_rank"] is None,
        r["reading_rank"] if r["reading_rank"] is not None else 0,
        -(r["year"] or 0),
        r["title"].lower(),
        r["key"],
    ))


def _confidence(value: str | None, key: str, anomalies: Anomalies) -> str:
    v = (value or "").strip().lower()
    if not v:
        return "unverified"
    if v in CONFIDENCE_MAP:
        return CONFIDENCE_MAP[v]
    anomalies.add(f"grey {key!r}: confidence {value!r} not in {CONFIDENCE_VALUES}, recorded as 'unverified'")
    return "unverified"


def _grey_record(key, title, authors, year, venue, url, sid, label, one_line, confidence, selected):
    url = (url or "").strip() or GREY_URL_FALLBACK.get(key, "")
    venue = (venue or "").strip()
    if not venue and arxiv_id_from_url(url):
        venue = "arXiv"
    return OrderedDict([
        ("key", key),
        ("title", clean_math((title or "").strip())),
        ("authors", as_list(authors)),
        ("year", year),
        ("venue", venue),
        ("url", url),
        ("primary", sid),
        ("section", section_of(sid)),
        ("label", clean_math(label)),
        ("one_line", clean_math((one_line or "").strip())),
        ("confidence", confidence),
        ("selected", bool(selected)),
        ("also", []),
    ])


def build_grey(corpus: dict, grey_v2: dict, labels: dict, sid_pos: dict,
               paper_keys: set[str], paper_arxiv: set[str], anomalies: Anomalies) -> list[dict]:
    records: list[dict] = []
    by_url: dict[str, dict] = {}
    by_title: dict[str, dict] = {}
    used_keys: set[str] = set()

    def register(rec: dict) -> None:
        u, t = norm_url(rec["url"]), norm_title(rec["title"])
        if u:
            by_url.setdefault(u, rec)
        if t:
            by_title.setdefault(t, rec)

    def take_key(key: str, origin: str) -> str:
        key = (key or "").strip() or "grey-item"
        if key in used_keys:
            new = unique_slug(key, used_keys)
            anomalies.add(f"grey: duplicate key {key!r} from {origin}, renamed to {new!r}")
            return new
        used_keys.add(key)
        return key

    def sid_for(raw_sid, key: str, what: str, structure: str = "current") -> str:
        if key in GREY_SID_OVERRIDE and GREY_SID_OVERRIDE[key] in sid_pos:
            anomalies.add(f"{what} {key!r}: sid {raw_sid!r} overridden to {GREY_SID_OVERRIDE[key]!r} (GREY_SID_OVERRIDE)")
            return GREY_SID_OVERRIDE[key]
        return resolve_sid(raw_sid, sid_pos, f"{what} {key!r}", anomalies, structure)

    # 1. corpus_full.grey: cited in the PDF. One record per document: when two bib
    #    keys point at the same URL the second becomes a cross-reference (`also`)
    #    of the first, so stats.cited counts distinct cited documents.
    for g in corpus.get("grey") or []:
        raw_key = (g.get("key") or "").strip()
        sid = sid_for(g.get("sid"), raw_key, "grey")
        u = norm_url((g.get("url") or "").strip() or GREY_URL_FALLBACK.get(raw_key, ""))
        hit = by_url.get(u) if u else None
        if hit is not None:
            if sid != hit["primary"] and all(a["sid"] != sid for a in hit["also"]):
                hit["also"].append({"sid": sid, "score": None})
                hit["also"].sort(key=lambda a: sid_pos.get(a["sid"], 10**6))
            anomalies.add(f"grey: {raw_key!r} shares its URL with {hit['key']!r}; merged, sid {sid!r} kept as a cross-reference")
            continue
        key = take_key(raw_key, "corpus_full.grey")
        year = to_year(g.get("year"))
        if year is None:
            anomalies.add(f"grey {key!r}: year {g.get('year')!r} not parseable")
        rec = _grey_record(
            key, g.get("title"), g.get("authors"), year, g.get("venue"), g.get("url"),
            sid, label_for(key, g.get("short_label"), g.get("title") or "", labels),
            g.get("one_line"), _confidence(g.get("confidence"), key, anomalies), True,
        )
        records.append(rec)
        register(rec)

    # 2. grey_v2.entries: the wider verified list (sids on the GREY_V2_STRUCTURE outline)
    merged_url = merged_title = dropped_dup = remapped = 0
    for e in grey_v2.get("entries") or []:
        u, t = norm_url(e.get("url")), norm_title(e.get("title"))
        hit = by_url.get(u) if u else None
        via = "url" if hit else None
        if hit is None and t:
            hit = by_title.get(t)
            via = "title" if hit else None
        if hit is not None:
            if via == "url":
                merged_url += 1
                if norm_title(hit["title"]) != t:
                    anomalies.add(
                        f"grey: merged {e.get('key_hint')!r} into {hit['key']!r} by URL "
                        f"with differing titles ({hit['title']!r} vs {e.get('title')!r})"
                    )
            else:
                merged_title += 1
                if norm_url(hit["url"]) != u:
                    anomalies.add(
                        f"grey: merged {e.get('key_hint')!r} into {hit['key']!r} by title; "
                        f"URLs differ ({hit['url'] or 'none'!r} vs {e.get('url')!r})"
                    )
            if not hit["selected"]:
                dropped_dup += 1  # duplicate inside grey_v2 itself
            # fill blanks from the v2 entry; never override a cited item's own values
            if not hit["url"] and e.get("url"):
                hit["url"] = e["url"].strip()
            if not hit["venue"] and e.get("venue_or_publisher"):
                hit["venue"] = e["venue_or_publisher"].strip()
            if not hit["one_line"] and e.get("one_line"):
                hit["one_line"] = e["one_line"].strip()
            if not hit["authors"] and e.get("authors"):
                hit["authors"] = as_list(e["authors"])
            if hit["year"] is None:
                hit["year"] = to_year(e.get("year"))
            register(hit)
            continue
        raw_key = (e.get("key_hint") or e.get("key") or "").strip()
        sid = sid_for(e.get("sid"), raw_key, "grey_v2", GREY_V2_STRUCTURE)
        if sid != (e.get("sid") or "").strip():
            remapped += 1
        key = take_key(raw_key, "grey_v2")
        year = to_year(e.get("year"))
        if year is None:
            anomalies.add(f"grey {key!r}: year {e.get('year')!r} not parseable")
        rec = _grey_record(
            key, e.get("title"), e.get("authors"), year, e.get("venue_or_publisher"),
            e.get("url"), sid, label_for(key, e.get("short_label"), e.get("title") or "", labels),
            e.get("one_line"), _confidence(e.get("confidence"), key, anomalies), False,
        )
        if (e.get("arxiv_id") or "").strip():
            rec["_arxiv"] = e["arxiv_id"].strip()
        records.append(rec)
        register(rec)

    anomalies.add(
        f"grey: {merged_url} grey_v2 entries merged into corpus items by URL, "
        f"{merged_title} by title, {dropped_dup} grey_v2 internal duplicates collapsed"
    )
    if remapped:
        anomalies.add(f"grey_v2: sids read as {GREY_V2_STRUCTURE} ids; {remapped} entries re-filed onto the current outline")
    no_url = [r["key"] for r in records if not r["url"]]
    if no_url:
        anomalies.add(f"grey: {len(no_url)} items without URL: {no_url}")
    no_line = [r["key"] for r in records if not r["one_line"]]
    if no_line:
        anomalies.add(f"grey: {len(no_line)} items with empty one_line: {no_line}")
    # Grey items that are arXiv papers (by key or arXiv id) are folded into the paper
    # record by merge_grey_into_papers(), which reports each merge.
    sort_grey(records, sid_pos)
    return records


def sort_grey(records: list[dict], sid_pos: dict) -> None:
    records.sort(key=lambda r: (
        sid_pos.get(r["primary"], 10**6),
        not r["selected"],
        -(r["year"] or 0),
        r["title"].lower(),
        r["key"],
    ))


def merge_grey_into_papers(papers: list[dict], grey: list[dict], sid_pos: dict,
                           anomalies: Anomalies) -> list[dict]:
    """A grey item that is the same work as an arXiv paper (same bib key, or the
    same arXiv id) is folded into the paper: the paper becomes selected (the PDF
    cites it), the grey sid becomes a cross-reference when it differs, and no
    second entity is emitted. Returns the remaining grey records."""
    by_key = {p["key"]: p for p in papers}
    by_arxiv = {p["arxiv_id"]: p for p in papers if p["arxiv_id"]}
    kept: list[dict] = []
    for g in grey:
        aid = g.pop("_arxiv", None) or arxiv_id_from_url(g["url"])
        p = by_key.get(g["key"]) or by_arxiv.get(aid or "")
        if p is None:
            kept.append(g)
            continue
        how = "key" if g["key"] in by_key else f"arXiv id {aid}"
        if g["selected"] and not p["selected"]:
            p["selected"] = True
        for sid in [g["primary"]] + [a["sid"] for a in g["also"]]:
            if sid != p["primary"] and all(a["sid"] != sid for a in p["also"]):
                p["also"].append({"sid": sid, "score": p["score"]})
        p["also"].sort(key=lambda a: (-(a["score"] or 0), sid_pos.get(a["sid"], 10**6)))
        anomalies.add(f"grey: {g['key']!r} is the paper {p['key']!r} (same {how}); merged into the paper record")
    sort_papers(papers, sid_pos)
    still = [g["key"] for g in kept if g["key"] in by_key]
    if still:
        raise SystemExit(f"error: grey keys still present in papers.json after merge: {still}")
    return kept


def fill_counts(sections: list[dict], papers: list[dict], grey: list[dict]) -> None:
    index = {sub["id"]: sub for sec in sections for sub in sec["subsections"]}
    for p in papers:
        sub = index.get(p["primary"])
        if sub is not None:
            sub["counts"]["primary"] += 1
            if p["selected"]:
                sub["counts"]["selected"] += 1
        for a in p["also"]:
            s2 = index.get(a["sid"])
            if s2 is not None:
                s2["counts"]["cross"] += 1
    for g in grey:
        sub = index.get(g["primary"])
        if sub is not None:
            sub["counts"]["grey"] += 1
        for a in g.get("also") or []:
            s2 = index.get(a["sid"])
            if s2 is not None:
                s2["counts"]["cross"] += 1


def structure_fingerprint(sections: list[dict]) -> str:
    """Twelve hex digits over the ordered subsection ids and titles. Two outlines of one day get
    different fingerprints, so taxonomy.structure and stream.taxonomy_structure tell them apart."""
    text = "\n".join(f"{ss['id']}\t{ss['title']}" for sec in sections for ss in sec["subsections"])
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]


def source_date(corpus: dict, path: Path) -> str | None:
    """stats.source_generated: corpus_full.generated, or the file's modification date when that
    is later (the corpus was re-filed on 19 October 2026 without a new stamp)."""
    stamp = str(corpus.get("generated") or "")[:10] or None
    try:
        mtime = _dt.date.fromtimestamp(path.stat().st_mtime).isoformat()
    except OSError:
        return stamp
    return max(stamp, mtime) if stamp else mtime


def build_taxonomy(outline: dict, parts: list[dict], sections: list[dict], generated: str) -> dict:
    return OrderedDict([
        ("title", strip_latex(outline.get("title")) or "Controlling Untrusted AI: A Survey"),
        ("thesis", strip_latex(outline.get("thesis"))),
        ("readers", [strip_latex(r) for r in outline.get("readers") or [] if strip_latex(r)]),
        ("generated", generated),
        ("structure", structure_fingerprint(sections)),
        ("requirements", REQUIREMENTS),
        ("failure_sources", FAILURE_SOURCES),
        ("operations", build_operations(sections, parts)),
        ("parts", parts),
        ("sections", sections),
    ])


RECENT_N = 12


def stream_derivatives(stream: dict | None) -> tuple[list[dict], dict]:
    """(the RECENT_N newest items, counts by polarity / failure source / operation / subsection)
    for stream_recent.json and the stream_* fields of stats.json. Shared with collect_news.py and
    remap_stream.py. Items are ordered as stream.json is written: date desc, then id desc."""
    items = [it for it in (stream or {}).get("items") or [] if isinstance(it, dict) and it.get("id") and it.get("date")]
    items.sort(key=lambda it: (it.get("date") or "", it.get("id") or ""), reverse=True)
    polarity = OrderedDict((k, 0) for k in ("good", "bad", "mixed"))
    per_source: Counter = Counter()
    per_op: Counter = Counter()
    per_sub: Counter = Counter()
    for it in items:
        if it.get("polarity") in polarity:
            polarity[it["polarity"]] += 1
        per_source.update(it.get("failure_sources") or [])
        per_op.update(it.get("operations") or [])
        per_sub.update(it.get("subsections") or [])
    counts = OrderedDict([
        ("stream_polarity", polarity),
        ("stream_per_source", OrderedDict(sorted(per_source.items()))),
        ("stream_per_op", OrderedDict(sorted(per_op.items()))),
        ("stream_per_sub", OrderedDict(sorted(per_sub.items(), key=lambda kv: [int(x) for x in kv[0][1:].split("_")]))),
    ])
    return items[:RECENT_N], counts


def build_stats(generated: str, structure: str, source_generated: str | None, papers: list[dict], grey: list[dict],
                sections: list[dict], stream_path: Path, anomalies: Anomalies) -> dict:
    cited = sum(1 for p in papers if p["selected"]) + sum(1 for g in grey if g["selected"])
    years = Counter(str(p["year"]) if p["year"] is not None else "unknown" for p in papers)
    years_sorted = OrderedDict(
        sorted(years.items(), key=lambda kv: (kv[0] == "unknown", -int(kv[0]) if kv[0] != "unknown" else 0))
    )
    per_section = OrderedDict((sec["id"], 0) for sec in sections)
    for p in papers:
        if p["section"] in per_section:
            per_section[p["section"]] += 1
    stream_items, stream_updated, stream = 0, None, None
    if stream_path.exists():
        try:
            stream = json.loads(stream_path.read_text(encoding="utf-8"))
            stream_items = len(stream.get("items") or [])
            stream_updated = stream.get("generated")
            if stream.get("taxonomy_structure") != structure:
                anomalies.add(f"stream.json is filed against subsection list {stream.get('taxonomy_structure') or 'unknown (no taxonomy_structure)'}; "
                              f"this build is {structure}: run pipeline/remap_stream.py")
        except (OSError, ValueError) as exc:
            anomalies.add(f"stream.json unreadable: {exc}")
    _, stream_counts = stream_derivatives(stream)
    return OrderedDict([
        ("generated", generated),
        ("source_generated", source_generated),
        ("papers", len(papers)),
        ("grey", len(grey)),
        ("cited", cited),
        ("subsections", sum(len(sec["subsections"]) for sec in sections)),
        ("sections", len(sections)),
        ("years", years_sorted),
        ("per_section", per_section),
        ("stream_items", stream_items),
        ("stream_updated", stream_updated),
        *stream_counts.items(),
    ])


# --------------------------------------------------------------------------- #
# Cross-checks that only produce anomaly lines
# --------------------------------------------------------------------------- #

def cross_checks(overleaf: Path, corpus: dict, outline: dict, labels: dict,
                 papers: list[dict], grey: list[dict], anomalies: Anomalies) -> None:
    paper_keys = {p["key"] for p in papers}
    grey_keys = {g["key"] for g in grey}

    v2_keys = set()
    try:
        v2_keys = {e.get("key_hint") for e in json.loads((overleaf / "research" / "grey_v2.json").read_text(encoding="utf-8")).get("entries", [])}
    except (OSError, ValueError):
        pass
    orphan_labels = sorted(k for k in labels if k not in paper_keys and k not in grey_keys and k not in v2_keys)
    if orphan_labels:
        anomalies.add(f"labels_method_style: {len(orphan_labels)} keys not in any source: {orphan_labels}")

    # corpus_full.subsections titles are stale by design (BRIEF.md); count how many differ
    outline_titles = {}
    for sec in outline["sections"]:
        for j, sub in enumerate(sec.get("subsections") or [], start=1):
            outline_titles[f"s{int(sec['number'])}_{j}"] = strip_latex(sub.get("title"))
    stale = 0
    for s in corpus.get("subsections") or []:
        t = re.sub(r"^\d+\.\d+\s+", "", s.get("title") or "")
        if norm_title(t) != norm_title(outline_titles.get(s.get("id"), "")):
            stale += 1
    if stale:
        anomalies.add(f"corpus_full.subsections: {stale} of {len(corpus.get('subsections') or [])} titles differ from outline.json (expected; outline.json used)")

    # ground truth for "cited": \citation keys in main.aux, if present
    aux = overleaf / "main.aux"
    if aux.exists():
        cited_aux: set[str] = set()
        for m in re.finditer(r"\\citation\{([^}]*)\}", aux.read_text(encoding="utf-8", errors="replace")):
            cited_aux.update(k.strip() for k in m.group(1).split(",") if k.strip())
        selected = {p["key"] for p in papers if p["selected"]} | {g["key"] for g in grey if g["selected"]}
        formula = sum(1 for p in papers if p["selected"]) + sum(1 for g in grey if g["selected"])
        extra = sorted(selected - cited_aux)
        missing_sel = sorted(cited_aux - selected)
        if len(cited_aux) != formula or extra or missing_sel:
            anomalies.add(
                f"cited: formula (selected papers + selected grey) = {formula}; main.aux has {len(cited_aux)} unique "
                f"citation keys; selected but not cited in aux: {extra}; cited in aux but not selected: {missing_sel}"
            )


# --------------------------------------------------------------------------- #
# I/O
# --------------------------------------------------------------------------- #

def load_json(path: Path):
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def dump(path: Path, obj, indent) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(obj, ensure_ascii=False, indent=indent)
    path.write_text(text + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    root = Path(__file__).resolve().parents[1]
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--overleaf", type=Path, default=root.parent / "overleaf-ai-control",
                    help="read-only Overleaf clone of the paper")
    ap.add_argument("--out", type=Path, default=root / "site" / "data", help="output directory")
    ap.add_argument("--generated", default=_dt.date.today().isoformat(), help="date stamp YYYY-MM-DD")
    ap.add_argument("--quiet", action="store_true", help="do not print anomalies")
    args = ap.parse_args(argv)

    ov: Path = args.overleaf
    if not (ov / "outline.json").exists():
        print(f"error: outline.json not found under {ov}", file=sys.stderr)
        return 2

    outline = load_json(ov / "outline.json")
    corpus = load_json(ov / "research" / "corpus_full.json")
    grey_v2 = load_json(ov / "research" / "grey_v2.json")
    labels = load_json(ov / "research" / "labels_method_style.json")

    anomalies = Anomalies()
    sections, sid_order = build_sections(outline, anomalies)
    parts = build_parts(outline, sections, anomalies)
    sid_pos = {sid: i for i, sid in enumerate(sid_order)}

    papers = build_papers(corpus, labels, sid_pos, anomalies)
    paper_keys = {p["key"] for p in papers}
    paper_arxiv = {p["arxiv_id"] for p in papers if p["arxiv_id"]}
    grey = build_grey(corpus, grey_v2, labels, sid_pos, paper_keys, paper_arxiv, anomalies)
    grey = merge_grey_into_papers(papers, grey, sid_pos, anomalies)
    fill_counts(sections, papers, grey)
    taxonomy = build_taxonomy(outline, parts, sections, args.generated)
    stats = build_stats(args.generated, taxonomy["structure"], source_date(corpus, ov / "research" / "corpus_full.json"),
                        papers, grey, sections, args.out / "stream.json", anomalies)
    cross_checks(ov, corpus, outline, labels, papers, grey, anomalies)

    out: Path = args.out
    dump(out / "taxonomy.json", taxonomy, 1)
    dump(out / "papers.json", papers, None)
    dump(out / "grey.json", grey, None)
    dump(out / "stats.json", stats, 1)
    if (out / "stream.json").exists():
        try:
            recent, _ = stream_derivatives(json.loads((out / "stream.json").read_text(encoding="utf-8")))
            stream_meta = json.loads((out / "stream.json").read_text(encoding="utf-8"))
            dump(out / "stream_recent.json", OrderedDict([("generated", stream_meta.get("generated")), ("items", recent)]), None)
        except (OSError, ValueError):
            pass

    print(f"wrote {out}: papers={len(papers)} grey={len(grey)} "
          f"subsections={stats['subsections']} cited={stats['cited']}")
    if not args.quiet:
        for a in anomalies.items:
            print("ANOMALY:", a)
    return 0


if __name__ == "__main__":
    sys.exit(main())
