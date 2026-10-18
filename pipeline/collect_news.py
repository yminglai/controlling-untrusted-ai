#!/usr/bin/env python3
"""Scheduled collector for the live stream (site/data/stream.json).

Pipeline
  1. read pipeline/feeds.yml, fetch every enabled RSS / Atom / arXiv feed (requests + xml.etree)
  2. normalise entries: title, url, date, publisher, snippet
  3. drop entries older than --since days, already in stream.json (normalised URL or title key),
     duplicated inside the run, or failing the keyword prefilter (feeds with weight >= 0.9 skip it)
  4. optionally ingest reader submissions: GitHub issues labelled "submission" (--issues owner/repo)
  5. classify candidates in batches with pipeline/classify.py (LLM, heuristic fallback, or --no-llm)
  6. keep relevant items, verify that the URL responds, assign SCHEMA.md ids
  7. merge into stream.json (date desc) and update stream_items / stream_updated in stats.json

Flags
  --since N      look-back window in days (default 10)
  --limit N      classify at most N candidates (highest feed weight, newest first)
  --dry-run      write pipeline/seed/_collector_dry_run.json instead of touching site/data
  --no-llm       heuristic classifier only; every item gets needs_review: true
  --issues R     also read open issues labelled "submission" from GitHub repo R (owner/repo)
  --only a,b     restrict to these feed ids (testing)
  --feeds PATH   alternative feeds.yml
  --verbose      more logging on stderr

Exit code 0 on success (also when nothing is new), 2 on configuration errors.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import datetime as dt
import email.utils
import html
import json
import os
import re
import sys
import time
import unicodedata
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import requests
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import classify as clf  # noqa: E402
from build_data import stream_derivatives  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
FEEDS_YML = ROOT / "pipeline" / "feeds.yml"
STREAM_JSON = ROOT / "site" / "data" / "stream.json"
STATS_JSON = ROOT / "site" / "data" / "stats.json"
STREAM_RECENT_JSON = ROOT / "site" / "data" / "stream_recent.json"
DRY_RUN_JSON = ROOT / "pipeline" / "seed" / "_collector_dry_run.json"

UTC = dt.timezone.utc
NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "dc": "http://purl.org/dc/elements/1.1/",
    "content": "http://purl.org/rss/1.0/modules/content/",
    "rss1": "http://purl.org/rss/1.0/",
    "media": "http://search.yahoo.com/mrss/",
    "arxiv": "http://arxiv.org/schemas/atom",
}
DEFAULT_UA = "controlling-untrusted-ai-collector/0.1 (+https://github.com/yminglai/controlling-untrusted-ai)"
TRACKING_PARAMS = re.compile(r"^(utm_\w+|fbclid|gclid|mc_cid|mc_eid|ncid|cmpid|igshid|ref_src|oly_\w+|_hs\w+|guccounter|sr_share)$", re.I)
STOPWORDS = {"a", "an", "the", "of", "to", "in", "on", "for", "and", "or", "is", "are", "was", "with", "by", "at",
             "as", "its", "it", "from", "that", "this", "after", "over", "into", "how", "why", "what", "new"}

VERBOSE = False


def log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def vlog(msg: str) -> None:
    if VERBOSE:
        log(msg)


# --------------------------------------------------------------------------- text helpers

def strip_html(s: str) -> str:
    if not s:
        return ""
    s = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", s, flags=re.S | re.I)
    s = re.sub(r"<br\s*/?>|</p>|</div>|</li>", " ", s, flags=re.I)
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s)
    s = s.replace("\xa0", " ")
    return re.sub(r"\s+", " ", s).strip()


def clean_snippet(s: str, limit: int = 700) -> str:
    s = strip_html(s)
    s = re.sub(r"\s*(?:\u2014|\u2013|-{2,3})\s*", " - ", s)   # em/en dashes and --- to a plain hyphen
    s = re.sub(r"^(Comments|Article URL|Points):.*?(?=\s[A-Z])", "", s)  # hnrss boilerplate
    s = re.sub(r"\b(Read more|Continue reading|The post .* appeared first on .*)$", "", s, flags=re.I).strip()
    if len(s) > limit:
        s = s[:limit].rsplit(" ", 1)[0] + "..."
    return s


def slugify(title: str, max_len: int = 69) -> str:
    s = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    s = re.sub(r"-{2,}", "-", s)
    if len(s) > max_len:
        s = s[:max_len].rsplit("-", 1)[0] or s[:max_len]
    return s or "item"


def make_id(date: str, title: str) -> str:
    return f"{date}-{slugify(title, 80 - len(date) - 1)}"


def normalise_url(url: str) -> str:
    """Canonical form used for dedupe: lower-case host, no www., no tracking params, no fragment,
    arXiv version suffix removed."""
    if not url:
        return ""
    url = url.strip()
    try:
        parts = urlsplit(url)
    except ValueError:
        return url.lower()
    host = (parts.hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    if host == "export.arxiv.org":
        host = "arxiv.org"
    path = re.sub(r"/+$", "", parts.path or "")
    if host == "arxiv.org":
        path = path.replace("/pdf/", "/abs/")
        path = re.sub(r"v\d+$", "", path)
        path = re.sub(r"\.pdf$", "", path)
    query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if not TRACKING_PARAMS.match(k)]
    query.sort()
    return urlunsplit(("https" if parts.scheme in ("http", "https") else parts.scheme, host, path, urlencode(query), ""))


def clean_url(url: str) -> str:
    """The URL that is stored: original scheme/host, tracking params and fragment removed."""
    if not url:
        return ""
    parts = urlsplit(url.strip())
    query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if not TRACKING_PARAMS.match(k)]
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), ""))


def title_key(title: str) -> str:
    t = unicodedata.normalize("NFKD", title or "").encode("ascii", "ignore").decode().lower()
    toks = [w for w in re.findall(r"[a-z0-9]+", t) if w not in STOPWORDS]
    return "-".join(toks[:10])


URL_DATE = re.compile(r"/(20\d\d)/(0[1-9]|1[0-2])/(0[1-9]|[12]\d|3[01])(?:/|$)")


def url_date(url: str) -> str | None:
    """Event date embedded in a news URL (/2025/12/11/), used when an aggregator re-dates an old story."""
    m = URL_DATE.search(url or "")
    if not m:
        return None
    try:
        return dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3))).isoformat()
    except ValueError:
        return None


def parse_date(s: str | None) -> dt.datetime | None:
    if not s:
        return None
    s = s.strip()
    d = None
    try:
        d = email.utils.parsedate_to_datetime(s)
    except (TypeError, ValueError, IndexError):
        pass
    if d is None:
        try:
            d = dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
        except ValueError:
            m = re.search(r"(\d{4})-(\d{2})-(\d{2})", s)
            if m:
                try:
                    d = dt.datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
                except ValueError:
                    return None
    if d is None:
        return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=UTC)
    return d.astimezone(UTC)


# --------------------------------------------------------------------------- feed fetching and parsing

def load_feeds(path: Path, only: set[str] | None) -> tuple[dict, list[dict]]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    defaults = {"timeout": 20, "max_items_per_feed": 200, "user_agent": DEFAULT_UA}
    defaults.update(data.get("defaults") or {})
    feeds = []
    for f in data.get("feeds") or []:
        if not f.get("enabled", True) and f.get("type") != "github-issues":
            continue
        if only and f.get("id") not in only:
            continue
        feeds.append(f)
    return defaults, feeds


def fetch(url: str, timeout: int, ua: str, accept: str = "application/rss+xml, application/atom+xml, application/xml, text/xml, */*") -> requests.Response:
    return requests.get(url, timeout=timeout, headers={"User-Agent": ua, "Accept": accept}, allow_redirects=True)


def _first(el, *paths):
    for p in paths:
        node = el.find(p, NS)
        if node is not None:
            if node.text and node.text.strip():
                return node.text.strip()
            if p.endswith("link") and node.get("href"):
                return node.get("href").strip()
    return ""


def _atom_link(entry) -> str:
    best = ""
    for link in entry.findall("atom:link", NS):
        rel = link.get("rel", "alternate")
        href = (link.get("href") or "").strip()
        if not href:
            continue
        if rel == "alternate" and (link.get("type") in (None, "", "text/html")):
            return href
        if rel == "alternate" and not best:
            best = href
    if best:
        return best
    idt = (entry.findtext("atom:id", default="", namespaces=NS) or "").strip()
    return idt if idt.startswith("http") else ""


def parse_feed(content: bytes, feed: dict) -> list[dict]:
    """Parse RSS 2.0 / Atom / RSS 1.0 bytes into raw entries {title,url,published,snippet,publisher}."""
    root = ET.fromstring(content)
    tag = root.tag.lower()
    entries = []
    publisher = feed.get("publisher") or ""
    if tag.endswith("rss"):
        chan = root.find("channel")
        publisher = publisher or (chan.findtext("title") if chan is not None else "") or ""
        for it in root.findall("./channel/item"):
            link = _first(it, "link") or (it.findtext("guid") or "").strip()
            entries.append({
                "title": strip_html(it.findtext("title") or ""),
                "url": link,
                "published": _first(it, "pubDate", "dc:date", "atom:published", "atom:updated"),
                "snippet": it.findtext("description") or it.findtext("content:encoded", default="", namespaces=NS) or "",
                "publisher": publisher,
            })
    elif tag.endswith("feed"):
        publisher = publisher or (root.findtext("atom:title", default="", namespaces=NS) or "")
        for e in root.findall("atom:entry", NS):
            snippet = e.findtext("atom:summary", default="", namespaces=NS) or e.findtext("atom:content", default="", namespaces=NS) or ""
            entries.append({
                "title": strip_html(e.findtext("atom:title", default="", namespaces=NS) or ""),
                "url": _atom_link(e),
                "published": _first(e, "atom:published", "atom:updated", "dc:date"),
                "snippet": snippet,
                "publisher": publisher,
            })
    elif tag.endswith("rdf"):
        ch = root.find("rss1:channel", NS)
        publisher = publisher or (ch.findtext("rss1:title", default="", namespaces=NS) if ch is not None else "")
        for it in root.findall("rss1:item", NS):
            entries.append({
                "title": strip_html(it.findtext("rss1:title", default="", namespaces=NS) or ""),
                "url": (it.findtext("rss1:link", default="", namespaces=NS) or "").strip(),
                "published": _first(it, "dc:date"),
                "snippet": it.findtext("rss1:description", default="", namespaces=NS) or "",
                "publisher": publisher,
            })
    else:
        raise ValueError(f"unknown feed root <{root.tag}>")
    return entries


def fetch_feed(feed: dict, defaults: dict) -> tuple[dict, list[dict], str | None]:
    try:
        r = fetch(feed["url"], defaults["timeout"], defaults["user_agent"])
        if r.status_code >= 400:
            return feed, [], f"HTTP {r.status_code}"
        entries = parse_feed(r.content, feed)
        return feed, entries[: int(defaults["max_items_per_feed"])], None
    except requests.RequestException as e:
        return feed, [], f"{type(e).__name__}"
    except (ET.ParseError, ValueError) as e:
        return feed, [], f"parse error: {str(e)[:60]}"


def fetch_all(feeds: list[dict], defaults: dict) -> tuple[list[dict], dict]:
    """Fetch feeds concurrently (arXiv ones serially with a 3 s pause). Returns (raw entries, per-feed report)."""
    report = {}
    raw = []
    arxiv = [f for f in feeds if f.get("type") == "arxiv"]
    others = [f for f in feeds if f.get("type") not in ("arxiv", "github-issues")]
    with cf.ThreadPoolExecutor(max_workers=6) as ex:
        futs = [ex.submit(fetch_feed, f, defaults) for f in others]
        for fut in cf.as_completed(futs):
            feed, entries, err = fut.result()
            report[feed["id"]] = {"entries": len(entries), "error": err}
            for e in entries:
                e["_feed"] = feed
            raw.extend(entries)
    for i, f in enumerate(arxiv):
        if i:
            time.sleep(3)
        feed, entries, err = fetch_feed(f, defaults)
        report[feed["id"]] = {"entries": len(entries), "error": err}
        for e in entries:
            e["_feed"] = feed
        raw.extend(entries)
    return raw, report


# --------------------------------------------------------------------------- GitHub submissions

ISSUE_FIELDS = {
    "title": ("title", "headline"),
    "url": ("url", "link", "source url"),
    "date": ("date", "event date", "when"),
    "what_happened": ("what happened", "description", "summary"),
    "polarity": ("good or bad", "polarity", "outcome"),
    "failure_source": ("failure source", "which failure source"),
    "operation": ("operation", "which operation", "control operation"),
    "subsection": ("subsection", "optional subsection", "survey subsection"),
}


def parse_issue_body(body: str) -> dict:
    """Parse the markdown GitHub renders for an issue form: '### Label\\n\\nvalue' blocks."""
    out = {}
    if not body:
        return out
    sections = re.split(r"^###\s+", body.replace("\r\n", "\n"), flags=re.M)
    for sec in sections[1:]:
        head, _, val = sec.partition("\n")
        label = head.strip().lower().rstrip(":")
        val = val.strip()
        if val.lower() in ("_no response_", "none", "n/a", ""):
            val = ""
        for key, names in ISSUE_FIELDS.items():
            if label in names or any(label.startswith(n) for n in names):
                out[key] = val
                break
    return out


def issue_to_candidate(issue: dict) -> dict | None:
    f = parse_issue_body(issue.get("body") or "")
    url = (f.get("url") or "").strip()
    m = re.search(r"https?://\S+", url)
    if not m:
        return None
    url = m.group(0).rstrip(").,")
    title = (f.get("title") or "").strip() or re.sub(r"^\[?submission\]?:?\s*", "", issue.get("title") or "", flags=re.I).strip()
    if not title:
        return None
    date = None
    m = re.search(r"\d{4}-\d{2}-\d{2}", f.get("date") or "")
    if m:
        date = m.group(0)
    else:
        d = parse_date(issue.get("created_at"))
        date = d.date().isoformat() if d else dt.datetime.now(UTC).date().isoformat()
    pol = (f.get("polarity") or "").lower()
    polarity = "bad" if pol.startswith("bad") else "good" if pol.startswith("good") else "mixed" if pol.startswith("mixed") else None
    fs = (f.get("failure_source") or "").lower()
    failure_sources = [x for x in clf.FAILURE_SOURCES if re.search(rf"\b{x}\b", fs)]
    op = (f.get("operation") or "").lower()
    operations = [x for x in clf.OPERATIONS if re.search(rf"\b{x}\b", op)]
    sub = re.findall(r"s\d{1,2}_\d{1,2}", (f.get("subsection") or "").lower())
    hints = {k: v for k, v in {"polarity": polarity, "failure_sources": failure_sources,
                                "operations": operations, "subsections": sub}.items() if v}
    return {
        "title": title, "url": url, "date": date, "publisher": "Reader submission",
        "snippet": clean_snippet(f.get("what_happened") or "", 1200), "hints": hints,
        "weight": 1.0, "evidence": None, "added_by": "submission",
        "lens": f"github-issue:{issue.get('number')}", "feed_id": "github-submissions",
    }


def fetch_issues(repo: str, timeout: int, ua: str) -> tuple[list[dict], str | None]:
    url = f"https://api.github.com/repos/{repo}/issues"
    headers = {"Accept": "application/vnd.github+json", "User-Agent": ua, "X-GitHub-Api-Version": "2022-11-28"}
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    out = []
    try:
        page = 1
        while page <= 5:
            r = requests.get(url, headers=headers, timeout=timeout,
                             params={"state": "open", "labels": "submission", "per_page": 100, "page": page})
            if r.status_code >= 400:
                return out, f"HTTP {r.status_code}"
            batch = r.json()
            if not isinstance(batch, list):
                return out, "unexpected response"
            out.extend(i for i in batch if "pull_request" not in i)
            if len(batch) < 100:
                break
            page += 1
    except (requests.RequestException, ValueError) as e:
        return out, type(e).__name__
    return out, None


# --------------------------------------------------------------------------- candidates

def normalise_entry(e: dict, now: dt.datetime) -> dict | None:
    feed = e["_feed"]
    title = re.sub(r"\s+", " ", e.get("title") or "").strip()
    url = (e.get("url") or "").strip()
    if not title or not url.startswith("http"):
        return None
    d = parse_date(e.get("published"))
    if d is None:
        return None
    if d > now + dt.timedelta(days=1):
        d = now
    snippet = clean_snippet(e.get("snippet") or "")
    ud = url_date(url)
    if ud and ud >= d.date().isoformat():
        ud = None
    return {
        "title": title, "url": clean_url(url), "date": d.date().isoformat(), "published_at": d.isoformat(),
        "url_date": ud,
        "publisher": e.get("publisher") or feed.get("publisher") or "", "snippet": snippet,
        "feed_id": feed["id"], "weight": float(feed.get("weight", 0.5) or 0.5),
        "evidence": feed.get("evidence"), "added_by": "collector", "lens": f"feed:{feed['id']}",
    }


def round_robin(cands: list[dict], limit: int) -> list[dict]:
    """Take up to `limit` candidates, cycling over feeds in weight order so one large feed cannot
    crowd out the others; within a feed, newest first (the input is already sorted that way)."""
    by_feed: dict[str, list[dict]] = {}
    for c in cands:
        by_feed.setdefault(c["feed_id"], []).append(c)
    out: list[dict] = []
    while len(out) < limit and any(by_feed.values()):
        for fid in list(by_feed):
            if by_feed[fid]:
                out.append(by_feed[fid].pop(0))
                if len(out) >= limit:
                    break
            else:
                del by_feed[fid]
    return out


def existing_keys(stream: dict) -> tuple[set[str], set[str], set[str]]:
    urls, titles, ids = set(), set(), set()
    for it in stream.get("items", []):
        if it.get("url"):
            urls.add(normalise_url(it["url"]))
        if it.get("title"):
            titles.add(title_key(it["title"]))
        if it.get("id"):
            ids.add(it["id"])
    return urls, titles, ids


def prefilter(c: dict) -> bool:
    if c["weight"] >= 0.9 or c.get("hints") is not None:
        return True
    text = (c["title"] + " " + c["snippet"]).lower()
    return any(re.search(p, text, re.I) for p in clf.AI_TERMS)


def build_candidates(raw: list[dict], stream: dict, since_days: int, now: dt.datetime, counters: dict) -> list[dict]:
    cutoff = now - dt.timedelta(days=since_days)
    seen_urls, seen_titles, _ = existing_keys(stream)
    out = []
    for e in raw:
        c = normalise_entry(e, now)
        if c is None:
            counters["unparseable"] += 1
            continue
        if dt.datetime.fromisoformat(c["published_at"]) < cutoff:
            counters["too_old"] += 1
            continue
        nu, tk = normalise_url(c["url"]), title_key(c["title"])
        if nu in seen_urls or tk in seen_titles:
            counters["duplicate"] += 1
            continue
        seen_urls.add(nu)
        seen_titles.add(tk)
        if not prefilter(c):
            counters["prefiltered"] += 1
            continue
        out.append(c)
    return out


# --------------------------------------------------------------------------- verification and assembly

def verify_url(url: str, timeout: int, ua: str) -> tuple[bool, str]:
    headers = {"User-Agent": ua, "Accept": "text/html,application/xhtml+xml,*/*;q=0.8"}
    code = None
    err = None
    try:
        r = requests.head(url, headers=headers, timeout=timeout, allow_redirects=True)
        code = r.status_code
    except requests.RequestException as e:
        err = type(e).__name__
    if code is None or code in (405, 403, 400, 404, 501) or code >= 500:
        try:
            r = requests.get(url, headers=headers, timeout=timeout * 2, allow_redirects=True, stream=True)
            r.close()
            code = r.status_code
        except requests.RequestException as e:
            if code is None:
                return False, f"URL not reachable ({err or type(e).__name__})."
    if code < 400:
        return True, f"URL fetched (HTTP {code}) on collection; title and date taken from the publisher's feed."
    if code in (401, 403, 405, 429):
        return True, f"URL exists but answered HTTP {code} to the collector (bot protection); listed by the publisher's feed."
    return False, f"URL answered HTTP {code}."


def assemble(c: dict, r: dict, today: str, note: str, used_ids: set[str]) -> dict:
    date = r.get("date") if r.get("date") and r["date"] <= today and r["date"] >= "2015-01-01" else c["date"]
    base = make_id(date, c["title"])
    iid, n = base, 2
    while iid in used_ids:
        iid = f"{base[:76]}-{n}"
        n += 1
    used_ids.add(iid)
    return {
        "id": iid,
        "date": date,
        "date_precision": "day",
        "title": c["title"],
        "url": c["url"],
        "publisher": c["publisher"],
        "kind": r["kind"],
        "polarity": r["polarity"],
        "summary": r["summary"],
        "failure_sources": r["failure_sources"],
        "requirements": r["requirements"],
        "operations": r["operations"],
        "subsections": r["subsections"],
        "domain": r["domain"],
        "actors": r["actors"],
        "evidence": r["evidence"],
        "related_papers": [],
        "tags": r["tags"],
        "verified": True,
        "verified_on": today,
        "verification_note": note,
        "added_by": c.get("added_by", "collector"),
        "lens": c.get("lens"),
        "needs_review": bool(r.get("needs_review", True)),
    }


def load_json(path: Path, default):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except ValueError as e:
            log(f"warning: {path} is not valid JSON ({e}); starting from an empty structure")
    return default


def dump_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


# --------------------------------------------------------------------------- main

def main(argv=None) -> int:
    global VERBOSE
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--since", type=int, default=10, help="look-back window in days (default 10)")
    ap.add_argument("--limit", type=int, default=None, help="classify at most N candidates")
    ap.add_argument("--dry-run", action="store_true", help="write pipeline/seed/_collector_dry_run.json only")
    ap.add_argument("--no-llm", action="store_true", help="heuristic classifier only (needs_review: true)")
    ap.add_argument("--issues", metavar="OWNER/REPO", help="also ingest GitHub issues labelled 'submission'")
    ap.add_argument("--only", help="comma-separated feed ids to fetch (testing)")
    ap.add_argument("--feeds", type=Path, default=FEEDS_YML)
    ap.add_argument("--batch-size", type=int, default=8)
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args(argv)
    VERBOSE = args.verbose

    if not args.no_llm and not os.environ.get("LLM_API_KEY", "").strip():
        # Without a classifier key nothing is published: heuristic items would reach the live
        # stream unreviewed. Pass --no-llm explicitly to publish heuristic items (needs_review: true).
        log("no LLM_API_KEY in the environment: nothing collected or written (pass --no-llm to publish heuristic items)")
        return 0

    now = dt.datetime.now(UTC)
    today = now.date().isoformat()
    t0 = time.time()

    if not args.feeds.exists():
        log(f"error: feeds file {args.feeds} not found")
        return 2
    only = set(x.strip() for x in args.only.split(",") if x.strip()) if args.only else None
    defaults, feeds = load_feeds(args.feeds, only)
    feeds_to_fetch = [f for f in feeds if f.get("type") != "github-issues"]
    log(f"collector {today}: {len(feeds_to_fetch)} feeds, since={args.since}d, limit={args.limit}, "
        f"dry_run={args.dry_run}, llm={'off' if args.no_llm else 'on'}")

    stream = load_json(STREAM_JSON, {"generated": None, "sources": [], "items": []})
    stream.setdefault("items", [])
    stream.setdefault("sources", [])
    tax = clf.load_taxonomy()
    log(f"taxonomy: {tax['source']} ({len(tax['subsection_ids'])} subsections); stream has {len(stream['items'])} items")
    if stream.get("taxonomy_generated") and tax.get("generated") and stream["taxonomy_generated"] != tax["generated"]:
        log(f"warning: stream.json was classified against taxonomy {stream['taxonomy_generated']}, "
            f"the current taxonomy is {tax['generated']}; subsection ids may have changed meaning (see SCHEMA.md)")

    raw, report = fetch_all(feeds_to_fetch, defaults)
    failed = {k: v["error"] for k, v in report.items() if v["error"]}
    log(f"fetched {len(raw)} entries from {len(report) - len(failed)} feeds" + (f"; failed: {failed}" if failed else ""))

    counters = {"unparseable": 0, "too_old": 0, "duplicate": 0, "prefiltered": 0}
    candidates = build_candidates(raw, stream, args.since, now, counters)
    log(f"candidates after filters: {len(candidates)} ({counters})")

    # reader submissions
    submissions_report = None
    if args.issues:
        issues, err = fetch_issues(args.issues, defaults["timeout"], defaults["user_agent"])
        seen_urls, seen_titles, _ = existing_keys(stream)
        seen_urls |= {normalise_url(c["url"]) for c in candidates}
        added = 0
        for iss in issues:
            c = issue_to_candidate(iss)
            if c and normalise_url(c["url"]) not in seen_urls and title_key(c["title"]) not in seen_titles:
                seen_urls.add(normalise_url(c["url"]))
                candidates.append(c)
                added += 1
        submissions_report = {"repo": args.issues, "open_issues": len(issues), "added": added, "error": err}
        log(f"submissions from {args.issues}: {len(issues)} open, {added} new" + (f" (error: {err})" if err else ""))

    candidates.sort(key=lambda c: (c["weight"], c["date"]), reverse=True)
    if args.limit is not None:
        candidates = round_robin(candidates, max(0, args.limit))
        log(f"limited to {len(candidates)} candidates across {len({c['feed_id'] for c in candidates})} feeds")

    results = clf.classify(candidates, tax, use_llm=not args.no_llm, batch_size=args.batch_size, log=log) if candidates else []

    _, _, used_ids = existing_keys(stream)
    new_items, rejected = [], []
    for c, r in zip(candidates, results):
        if not r.get("relevant"):
            rejected.append({"title": c["title"], "url": c["url"], "feed": c["feed_id"], "reason": "not relevant",
                             "confidence": r.get("confidence")})
            continue
        ok, note = verify_url(c["url"], defaults["timeout"], defaults["user_agent"])
        if not ok:
            rejected.append({"title": c["title"], "url": c["url"], "feed": c["feed_id"], "reason": note})
            continue
        if args.no_llm:
            r["needs_review"] = True
        new_items.append(assemble(c, r, today, note, used_ids))
    log(f"classified {len(results)}: {len(new_items)} kept, {len(rejected)} rejected")

    merged = stream["items"] + new_items
    merged.sort(key=lambda it: (it.get("date") or "", it.get("id") or ""), reverse=True)
    generated = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    sources = list(stream.get("sources") or [])
    if "collector" not in sources:
        sources.append("collector")

    summary = {
        "generated": generated, "dry_run": args.dry_run,
        "args": {"since": args.since, "limit": args.limit, "no_llm": args.no_llm, "issues": args.issues, "only": sorted(only) if only else None},
        "feeds": report, "submissions": submissions_report, "raw_entries": len(raw), "filters": counters,
        "candidates": len(candidates), "new_items": len(new_items), "rejected": len(rejected),
        "stream_items_after_merge": len(merged), "seconds": round(time.time() - t0, 1),
    }

    if args.dry_run:
        dump_json(DRY_RUN_JSON, {**summary, "items": new_items, "rejected_items": rejected})
        log(f"dry run: wrote {DRY_RUN_JSON.relative_to(ROOT)} ({len(new_items)} items, {len(rejected)} rejected)")
    else:
        out_stream = {"generated": generated, "taxonomy_generated": tax.get("generated") or stream.get("taxonomy_generated"),
                      "sources": sources, "items": merged}
        if new_items:
            dump_json(STREAM_JSON, out_stream)
            log(f"wrote {STREAM_JSON.relative_to(ROOT)} ({len(merged)} items)")
        recent, stream_counts = stream_derivatives(out_stream)
        if new_items or not STREAM_RECENT_JSON.exists():
            dump_json(STREAM_RECENT_JSON, {"generated": generated, "items": recent})
            log(f"wrote {STREAM_RECENT_JSON.relative_to(ROOT)} ({len(recent)} items)")
        stats = load_json(STATS_JSON, None)
        if stats is None:
            stats = {"generated": today}
            log("warning: stats.json missing; writing stream fields only (run build_data.py for the paper counts)")
        if new_items or stats.get("stream_items") != len(merged) or any(stats.get(k) != v for k, v in stream_counts.items()):
            stats["stream_items"] = len(merged)
            stats["stream_updated"] = generated
            stats.update(stream_counts)
            dump_json(STATS_JSON, stats)
            log(f"updated {STATS_JSON.relative_to(ROOT)} (stream_items={len(merged)})")
    gh_out = os.environ.get("GITHUB_OUTPUT")
    if gh_out:
        with open(gh_out, "a", encoding="utf-8") as fh:
            fh.write(f"new_items={len(new_items)}\n")
    print(f"stream: {len(new_items)} new items")
    return 0


if __name__ == "__main__":
    sys.exit(main())
