#!/usr/bin/env python3
"""Re-file the published stream onto the current outline.

    python3 pipeline/remap_stream.py [--data site/data]

Subsection ids are positional, so every revision of outline.json changes what an id means.
site/data/taxonomy.json carries a fingerprint of its subsection list (``structure``) and
stream.json records the fingerprint it was classified against (``taxonomy_structure``). When
the two differ, this script maps every item's ``subsections`` through the tables in
build_data.py (duplicates collapsed, order kept, unknown ids dropped), restamps the stream,
writes the items in the order of SCHEMA.md (date desc, then id desc), and rewrites
stream_recent.json and the stream_* fields of stats.json. Nothing else in an item changes,
except for a stream still on the 17 October 2026 vocabulary, whose ``failure_sources``
(mistakes -> benign, manipulation -> external, misalignment -> insider) and ``operations``
(observe -> monitor, verify -> evaluate) are renamed too.

The stream's structure is read from ``taxonomy_structure``. Streams from before that field
are recognised by ``taxonomy_generated``: 2026-10-17 is the 56-subsection outline, 2026-10-19
without a fingerprint the 36-subsection outline of 01:13 that day. A later outline needs a new
entry in STEPS carrying the fingerprint of the structure it replaces (the one this script
prints when it cannot map) and the map onto the next structure.

Every mapped id must exist in taxonomy.json; otherwise nothing is written and the missing ids
are listed. Idempotent: a stream already on the current structure is left alone. Exit code 0
on success (also when nothing changes), 2 when the stream cannot be mapped or a file cannot be
rewritten safely.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, OrderedDict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_data import SID_MAP_2026_10_17, SID_MAP_2026_10_19, stream_derivatives  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]

# Earlier structures, oldest first. Each step maps its ids onto the next step's structure; the
# last step maps onto the current taxonomy. "structure" is the fingerprint a stream.json carries
# when it was filed against that outline (None before the field existed); "stamp" recognises
# streams from before the field by taxonomy_generated.
STEPS = [
    {
        "name": "2026-10-17 (11 sections, 56 subsections)",
        "stamp": "2026-10-17", "structure": None,
        "sids": SID_MAP_2026_10_17,
        "failure_sources": {"mistakes": "benign", "manipulation": "external", "misalignment": "insider"},
        "operations": {"observe": "monitor", "verify": "evaluate"},
    },
    {
        "name": "2026-10-19 01:13 (11 sections, 36 subsections)",
        "stamp": "2026-10-19", "structure": "71715bf49db5",
        "sids": SID_MAP_2026_10_19,
    },
]


def _uniq(seq):
    out = []
    for x in seq:
        if x not in out:
            out.append(x)
    return out


def remap_item(item: dict, step: dict, unknown: Counter) -> dict:
    """The item with its vocabulary fields mapped one step forward; key order unchanged."""
    out = dict(item)
    if isinstance(item.get("subsections"), list):
        subs = []
        for sid in item["subsections"]:
            new = step["sids"].get(sid)
            if new is None:
                unknown[sid] += 1
            elif new not in subs:
                subs.append(new)
        out["subsections"] = subs
    for field in ("failure_sources", "operations"):
        table = step.get(field)
        if table and isinstance(item.get(field), list):
            out[field] = _uniq(table.get(v, v) for v in item[field])
    return out


def step_index(stream: dict) -> int | None:
    fp, stamp = stream.get("taxonomy_structure"), stream.get("taxonomy_generated")
    for i, step in enumerate(STEPS):
        if fp and step["structure"] == fp:
            return i
        if not fp and step["structure"] is None or not fp and step["stamp"] == stamp:
            if step["stamp"] == stamp:
                return i
    return None


def load(path: Path) -> tuple[dict, int | None]:
    """(parsed JSON, indent) after checking that the file round-trips byte for byte."""
    text = path.read_text(encoding="utf-8")
    data = json.loads(text)
    indent = 2 if text.startswith("{\n  ") else 1 if text.startswith("{\n ") else None
    if dumps(data, indent) != text:
        raise SystemExit(f"error: {path} does not round-trip through json with indent={indent}; not rewriting it")
    return data, indent


def dumps(data, indent: int | None) -> str:
    return json.dumps(data, ensure_ascii=False, indent=indent) + "\n"


def write_if_changed(path: Path, data, indent: int | None, before: str | None) -> bool:
    after = dumps(data, indent)
    if after == before:
        return False
    path.write_text(after, encoding="utf-8")
    return True


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", type=Path, default=ROOT / "site" / "data", help="directory with stream.json and taxonomy.json")
    args = ap.parse_args(argv)
    stream_path, recent_path = args.data / "stream.json", args.data / "stream_recent.json"
    taxonomy_path, stats_path = args.data / "taxonomy.json", args.data / "stats.json"
    for p in (stream_path, taxonomy_path):
        if not p.exists():
            print(f"error: {p} not found", file=sys.stderr)
            return 2
    tax = json.loads(taxonomy_path.read_text(encoding="utf-8"))
    target, generated = tax.get("structure"), tax.get("generated")
    known = {ss["id"] for s in tax.get("sections") or [] for ss in s.get("subsections") or []}
    if not target or not known:
        print(f"error: {taxonomy_path} carries no structure fingerprint or no subsections; rebuild it with build_data.py", file=sys.stderr)
        return 2

    stream, indent = load(stream_path)
    before = dumps(stream, indent)
    items = [it for it in stream.get("items") or []]
    if stream.get("taxonomy_structure") == target:
        print(f"stream.json: already filed against subsection list {target}; items left alone")
    else:
        i = step_index(stream)
        if i is None:
            print(f"error: stream.json is stamped taxonomy_structure={stream.get('taxonomy_structure')!r}, "
                  f"taxonomy_generated={stream.get('taxonomy_generated')!r}; no step in STEPS starts there "
                  f"(the current taxonomy is {target}, generated {generated})", file=sys.stderr)
            return 2
        unknown: Counter = Counter()
        changed = 0
        for step in STEPS[i:]:
            items = [remap_item(it, step, unknown) if isinstance(it, dict) else it for it in items]
        for old, new in zip(stream.get("items") or [], items):
            if old != new:
                changed += 1
        missing = sorted({sid for it in items if isinstance(it, dict) for sid in it.get("subsections") or []} - known,
                         key=lambda s: [int(x) for x in s[1:].split("_")])
        if missing:
            print(f"error: mapped ids not in {taxonomy_path.name} ({target}): {missing}; nothing written", file=sys.stderr)
            return 2
        empty = [it.get("id") for it in items if isinstance(it, dict) and not it.get("subsections")]
        if empty:
            print(f"error: {len(empty)} items would have no subsection: {empty[:10]}; nothing written", file=sys.stderr)
            return 2
        items.sort(key=lambda it: (it.get("date") or "", it.get("id") or ""), reverse=True)
        new_stream = OrderedDict()
        for k, v in stream.items():
            if k == "items":
                continue
            new_stream[k] = v
            if k == "taxonomy_generated":
                new_stream["taxonomy_structure"] = target
        new_stream["taxonomy_generated"] = generated
        new_stream["taxonomy_structure"] = target
        new_stream["items"] = items
        stream = new_stream
        print(f"stream.json: {len(items)} items, {changed} re-filed from {STEPS[i]['name']} onto {target}"
              + (f"; dropped unknown subsection ids {dict(unknown)}" if unknown else ""))
    wrote = write_if_changed(stream_path, stream, indent, before)
    print(f"stream.json: {'written' if wrote else 'unchanged'}")

    recent, counts = stream_derivatives(stream)
    rindent = None
    rbefore = None
    if recent_path.exists():
        _, rindent = load(recent_path)
        rbefore = recent_path.read_text(encoding="utf-8")
    rwrote = write_if_changed(recent_path, OrderedDict([("generated", stream.get("generated")), ("items", recent)]), rindent, rbefore)
    print(f"stream_recent.json: {len(recent)} items, {'written' if rwrote else 'unchanged'}")

    if stats_path.exists():
        stats, sindent = load(stats_path)
        sbefore = dumps(stats, sindent)
        stats["stream_items"] = len(stream.get("items") or [])
        stats["stream_updated"] = stream.get("generated")
        stats.update(counts)
        swrote = write_if_changed(stats_path, stats, sindent, sbefore)
        print(f"stats.json: stream fields {'written' if swrote else 'unchanged'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
