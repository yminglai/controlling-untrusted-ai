#!/usr/bin/env python3
"""Re-file the published stream onto the current outline.

    python3 pipeline/remap_stream.py [--data site/data] [--seed pipeline/seed/items]

Subsection ids are positional, so every revision of outline.json changes what an id means.
site/data/taxonomy.json carries a fingerprint of its subsection list (``structure``) and
stream.json records the fingerprint it was classified against (``taxonomy_structure``). When the
two differ, this script rebuilds the classification of every item from the original one: the
seed sweep of 17 October 2026 in pipeline/seed/items/*.json (one file per item, matched by id or
URL; fields ``subsections``, ``failure_sources`` and ``operations`` in that day's vocabulary of
56 subsection ids and the tiers mistakes / manipulation / misalignment). STEP maps that
vocabulary directly onto the current outline: subsection ids through build_data.SID_MAP_2026_10_17
(duplicates collapsed, order kept, unknown ids dropped), tiers through its ``failure_sources``
table; the operations constrain / observe / intervene / steer / train / verify / deploy are the
paper's section titles and are kept as they are. No other field of an item changes. The stream
is then restamped, written in the order of SCHEMA.md (date desc, then id desc), and
stream_recent.json and the stream_* fields of stats.json are rewritten.

STEP carries the fingerprint of the structure its map lands on (``target``). When taxonomy.json
has another fingerprint the outline changed after this map was written: the script prints both
fingerprints and exits with 2, and a new map onto the new structure is needed before the stream
can be published again (the tests compare stream.taxonomy_structure with taxonomy.structure).

Every mapped id must exist in taxonomy.json, every item must keep at least one subsection and
have a seed record, and the tiers and operations must be those of taxonomy.json; otherwise
nothing is written and the problems are listed. Idempotent: a stream already on the current
structure is left alone. Exit code 0 on success (also when nothing changes), 2 when the stream
cannot be mapped or a file cannot be rewritten safely.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, OrderedDict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_data import SID_MAP_2026_10_17, stream_derivatives  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]

# The one map: from the seed classification onto the current structure. "target" is the
# taxonomy.structure the map lands on; a taxonomy.json with another fingerprint needs a new map.
STEP = {
    "name": "seed sweep 2026-10-17 (11 sections, 56 subsections; tiers mistakes, manipulation, misalignment)",
    "seed": ROOT / "pipeline" / "seed" / "items",
    "target": "1ef18ee6f954",   # outline.json of 2026-10-21: 11 sections, 35 subsections
    "sids": SID_MAP_2026_10_17,
    "failure_sources": {"mistakes": "benign", "manipulation": "external", "misalignment": "insider"},
}

REFILED_FIELDS = ("subsections", "failure_sources", "operations")


def _uniq(seq):
    out = []
    for x in seq:
        if x not in out:
            out.append(x)
    return out


def load_seed(directory: Path) -> tuple[dict, dict]:
    """(items by id, items by URL) from the one-file-per-item seed; the first file wins on a clash."""
    by_id: dict[str, dict] = {}
    by_url: dict[str, dict] = {}
    for path in sorted(directory.glob("*.json")):
        item = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(item, dict):
            continue
        if item.get("id"):
            by_id.setdefault(item["id"], item)
        if item.get("url"):
            by_url.setdefault(item["url"], item)
    return by_id, by_url


def refile_item(item: dict, seed: dict, step: dict, unknown: Counter) -> dict:
    """The item with subsections, failure_sources and operations rebuilt from its seed record and
    mapped through step; every other field and the key order are unchanged."""
    out = dict(item)
    subs = []
    for sid in seed.get("subsections") or []:
        new = step["sids"].get(sid)
        if new is None:
            unknown[sid] += 1
        elif new not in subs:
            subs.append(new)
    out["subsections"] = subs
    table = step["failure_sources"]
    out["failure_sources"] = _uniq(table.get(v, v) for v in seed.get("failure_sources") or [])
    out["operations"] = _uniq(seed.get("operations") or [])
    return out


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


def sid_key(sid: str) -> list[int]:
    return [int(x) for x in sid[1:].split("_")]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", type=Path, default=ROOT / "site" / "data", help="directory with stream.json and taxonomy.json")
    ap.add_argument("--seed", type=Path, default=STEP["seed"], help="directory with the seed items (one JSON file per item)")
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
    tiers = {f["id"] for f in tax.get("failure_sources") or []}
    ops = {o["id"] for o in tax.get("operations") or [] if o.get("lever") is not None}
    if not target or not known or not tiers or not ops:
        print(f"error: {taxonomy_path} carries no structure fingerprint, subsections, tiers or operations; rebuild it with build_data.py", file=sys.stderr)
        return 2

    stream, indent = load(stream_path)
    before = dumps(stream, indent)
    items = list(stream.get("items") or [])
    if stream.get("taxonomy_structure") == target:
        print(f"stream.json: already filed against subsection list {target}; items left alone")
    else:
        if target != STEP["target"]:
            print(f"error: taxonomy.json is {target} (generated {generated}); STEP maps the seed onto {STEP['target']}. "
                  f"The outline changed: write a map onto the new structure and set STEP['target'] to {target}", file=sys.stderr)
            return 2
        if not args.seed.is_dir():
            print(f"error: seed directory {args.seed} not found", file=sys.stderr)
            return 2
        by_id, by_url = load_seed(args.seed)
        unknown: Counter = Counter()
        no_seed = []
        new_items = []
        for it in items:
            if not isinstance(it, dict):
                new_items.append(it)
                continue
            seed = by_id.get(it.get("id")) or by_url.get(it.get("url"))
            if seed is None:
                no_seed.append(it.get("id"))
                new_items.append(it)
                continue
            new_items.append(refile_item(it, seed, STEP, unknown))
        if no_seed:
            print(f"error: {len(no_seed)} items have no seed record (by id or url): {no_seed[:10]}; nothing written", file=sys.stderr)
            return 2
        missing = sorted({sid for it in new_items for sid in it.get("subsections") or []} - known, key=sid_key)
        if missing:
            print(f"error: mapped ids not in {taxonomy_path.name} ({target}): {missing}; nothing written", file=sys.stderr)
            return 2
        empty = [it.get("id") for it in new_items if not it.get("subsections")]
        if empty:
            print(f"error: {len(empty)} items would have no subsection: {empty[:10]}; nothing written", file=sys.stderr)
            return 2
        bad_tiers = sorted({v for it in new_items for v in it.get("failure_sources") or []} - tiers)
        bad_ops = sorted({v for it in new_items for v in it.get("operations") or []} - ops)
        if bad_tiers or bad_ops:
            print(f"error: values outside taxonomy.json: failure_sources {bad_tiers}, operations {bad_ops}; nothing written", file=sys.stderr)
            return 2
        changed = Counter()
        for old, new in zip(items, new_items):
            for field in REFILED_FIELDS:
                if old.get(field) != new.get(field):
                    changed[field] += 1
            if old != new:
                changed["items"] += 1
            if any(old.get(k) != new.get(k) for k in old if k not in REFILED_FIELDS) or set(old) != set(new):
                print(f"error: item {old.get('id')} changed outside {REFILED_FIELDS}; nothing written", file=sys.stderr)
                return 2
        items = new_items
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
        print(f"stream.json: {len(items)} items re-filed from the {STEP['name']} onto {target}: "
              f"{changed['items']} items changed, {changed['subsections']} changed subsections, "
              f"{changed['failure_sources']} changed failure_sources, {changed['operations']} changed operations"
              + (f"; dropped unknown seed subsection ids {dict(unknown)}" if unknown else ""))
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
