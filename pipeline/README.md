# Pipeline

Python scripts that produce everything under `site/data/`. Two independent halves:

| Script | Reads | Writes | Runs |
|---|---|---|---|
| `build_data.py` | the paper's tooling repository (`outline.json`, `research/*.json`) | `taxonomy.json`, `papers.json`, `grey.json`, `stats.json` | by hand, when the paper changes |
| `collect_news.py` (+ `classify.py`, `feeds.yml`) | RSS/Atom feeds, arXiv API, GitHub issues, `stream.json` | `stream.json`; the `stream_*` fields of `stats.json` | every 6 hours in CI (`.github/workflows/collect.yml`) and by hand |

The data contracts are in `../SCHEMA.md`. Nothing here is needed to serve the site; the front-end
only reads the JSON files.

## Running locally

```bash
cd controlling-untrusted-ai
python3 -m pip install requests pyyaml          # Python 3.12+; no other dependencies

# Dry run with the keyword classifier: nothing under site/data is touched.
python3 pipeline/collect_news.py --dry-run --no-llm --since 30 --limit 20
cat pipeline/seed/_collector_dry_run.json | python3 -m json.tool | head -80

# Dry run with the LLM classifier (needs the environment variables below).
python3 pipeline/collect_news.py --dry-run --limit 10

# Real run: merges into site/data/stream.json and updates stats.json.
python3 pipeline/collect_news.py --since 10 --issues yminglai/controlling-untrusted-ai

# Offline tests (feed parsing, dedupe, issue form parsing, heuristic rules, LLM JSON contract
# against an in-process fake gateway).
python3 -m unittest discover -s pipeline/tests -v
```

Flags of `collect_news.py`:

| Flag | Meaning |
|---|---|
| `--since N` | look-back window in days (default 10). Reader submissions ignore it. |
| `--limit N` | classify at most N candidates; candidates are ordered by feed weight, then date |
| `--dry-run` | write `pipeline/seed/_collector_dry_run.json` (new items, rejected items, per-feed report) and leave `site/data` alone |
| `--no-llm` | heuristic classifier only; every item gets `needs_review: true` |
| `--issues owner/repo` | also ingest open GitHub issues labelled `submission` |
| `--only id,id` | fetch only these feed ids from `feeds.yml` (debugging) |
| `--feeds PATH` | alternative feed list |
| `--batch-size N` | items per LLM call (default 8) |
| `--verbose` | more logging on stderr |

The script prints one line on stdout, `stream: <n> new items`, writes the same number to
`$GITHUB_OUTPUT` as `new_items` when that variable exists, and exits 0 even when nothing is new.

## Environment variables

| Variable | Used by | Notes |
|---|---|---|
| `LLM_API_KEY` | `classify.py` | bearer token for an OpenAI-compatible chat endpoint. Never printed, never written to disk. |
| `LLM_BASE_URL` | `classify.py` | base URL ending in `/v1`; the script posts to `$LLM_BASE_URL/chat/completions` |
| `LLM_MODEL` | `classify.py` | optional; default `anthropic/claude-opus-5-5` |
| `GITHUB_TOKEN` | `collect_news.py --issues` | optional; raises the GitHub API rate limit and lets the job read a private repo |
| `OUTLINE_JSON` | `classify.py` | optional path to the paper's `outline.json`, used only when `site/data/taxonomy.json` is missing |

No `temperature` is sent (the gateway used for the paper rejects anything but the default).
When `LLM_API_KEY` or `LLM_BASE_URL` is missing the collector logs one line and falls back to the
heuristic classifier; it never fails the run for that reason.

In GitHub Actions the first two come from repository secrets of the same name, `LLM_MODEL` from a
repository variable, and `GITHUB_TOKEN` is the job token (`issues: read`, `contents: write`).

## How the seed was made

The stream was seeded once, before the collector existed, by a verified sweep: a set of lenses
(`incidents-coding`, `incidents-injection`, `good-deployments`, `safety-features`, ...) each
produced a list of candidate events from search and from the survey's own grey literature; every
candidate URL was fetched, the date and the claims were confirmed from the page body, and the item
was classified by hand against the taxonomy. The sweep outputs live in `pipeline/seed/sweep_*.json`
and carry `added_by: "seed-sweep"` and the lens name in `lens`. Items that could not be verified
were not published. The collector appends to that seed; it never rewrites seed items.

## Collector pipeline

1. **Feeds.** `feeds.yml` lists 38 enabled sources: press, vendor blogs, safety and security
   organisations, policy, two arXiv API queries, and a disabled `github-issues` entry that
   `--issues` activates. Each has a `weight` in 0..1, the prior that an entry is about deploying AI
   agents. Every URL was fetched and parsed on the date in its `checked` field; sources without a
   working feed are listed under `disabled:` with the reason. Feeds are fetched concurrently with a
   20 s timeout and an identifying `User-Agent`; arXiv queries run serially with a 3 s pause.
2. **Normalise.** RSS 2.0, Atom and RSS 1.0 are parsed with `xml.etree`. Each entry becomes
   `{title, url, date, publisher, snippet}`; HTML is stripped, tracking parameters and fragments are
   removed from the URL, dates are parsed from RFC 2822 or ISO 8601.
3. **Filter.** Drop entries older than `--since` days; already in `stream.json` by normalised URL
   (host without `www.`, no tracking params, arXiv version stripped) or by title key (first ten
   content words); duplicated inside the run; or failing the keyword prefilter (an AI term in title
   or snippet). Feeds with `weight >= 0.9` and reader submissions skip the prefilter. A date embedded
   in the article URL (`/2025/12/11/`) that is older than the feed date is kept as `url_date`: an
   aggregator such as the AI Incident Database re-dates old stories, and the event date wins.
   With `--limit`, candidates are taken round-robin over feeds in weight order, newest first, so one
   large feed cannot crowd out the rest.
4. **Submissions.** With `--issues owner/repo`, open issues labelled `submission` are read through
   the GitHub REST API. The issue-form markdown (`### Label` blocks) is parsed into a candidate with
   the submitter's answers as `hints` (polarity, failure source, operation, subsections) that the
   classifier may confirm or override. The collector never writes to GitHub.
5. **Classify.** Candidates go to `classify.classify()` in batches of 8 (see below). Items with
   `relevant: false` are rejected.
6. **Verify.** Each kept URL is requested (HEAD, then GET on 4xx/5xx). 2xx/3xx is verified;
   401/403/405/429 count as "exists but blocks bots" and are verified with a note saying so; 404,
   410, 5xx and connection errors reject the item. The note goes into `verification_note`.
7. **Assemble and merge.** `id = YYYY-MM-DD-<slug>` (ASCII, hyphens, 80 chars max, `-2` suffix on
   collision), `date_precision: "day"`, `added_by: "collector"` or `"submission"`,
   `lens: "feed:<feed id>"` or `"github-issue:<n>"`, `related_papers: []`. New items are merged with
   the existing ones, sorted by date descending, and `stats.json` gets `stream_items` and
   `stream_updated`.

### How classification maps to the taxonomy

`classify.py` loads the taxonomy from `site/data/taxonomy.json`, else from the paper's
`outline.json` (positional ids `s{section}_{subsection}`), else from a built-in copy of the 35
subsection titles, so CI works even before `build_data.py` has run.

**LLM classifier.** One chat call per batch. The system prompt is the survey paragraph from
`BRIEF.md` (the vocabulary of requirements, failure sources, operations, levers and the two-level
test) plus the compact taxonomy: every section with its operation and every subsection id and
title. The model returns strict JSON per item:

| Field | Values |
|---|---|
| `relevant` | is this about deploying or operating AI agents in the real world, good or bad |
| `kind` | `incident`, `near-miss`, `deployment`, `safety-feature`, `evaluation`, `research`, `policy`, `disclosure` |
| `polarity` | `bad`, `good`, `mixed` |
| `failure_sources` | subset of `benign`, `external`, `insider` (the failure tier); empty when not a failure |
| `requirements` | subset of `correct`, `compliant`, `in-scope`, `within-budget`, `safe` |
| `operations` | subset of `constrain`, `observe`, `intervene`, `steer`, `train`, `verify`, `deploy`: the operation that failed, was missing, or worked |
| `subsections` | 1 to 4 ids, most specific first |
| `domain`, `evidence`, `actors`, `tags`, `date`, `confidence`, `summary` | as in SCHEMA.md; `summary` is two factual sentences |

`validate()` lower-cases and checks every enumeration, drops unknown subsection ids, trims lists,
and fills anything invalid from the heuristic result; an item with an invalid `kind`, `polarity`,
`summary`, no valid subsection, or `confidence < 0.5` gets `needs_review: true`. Fenced or
prefixed JSON is accepted; if a batch returns nothing parseable the whole batch falls back to the
heuristic classifier. The call is retried three times on 429/5xx and network errors.

**Heuristic classifier** (`--no-llm`, or fallback). Keyword rules in `classify.py`:
`KIND_RULES`, `FAILURE_RULES`, `OPERATION_RULES`, `SUBSECTION_RULES` (most specific first, with a
preference for subsections in the sections of the detected operations), `DOMAIN_RULES`,
`REQUIREMENT_RULES`, `TAG_RULES`. Strong incident words (deleted, breach, leak, exfiltrated, ...)
force `incident`/`bad`, or `near-miss` when the text says the action was caught or blocked.
`NEGATIVE_TERMS` (deepfakes, AI-generated art, funding news) reject items that have no agent term,
and titles that are mostly non-Latin are rejected because the keyword rules cannot read them (the
LLM path classifies them and marks them `needs_review`). The `evidence` default comes from the
feed. The summary is the first two sentences of the snippet. Every heuristic result has
`needs_review: true`.

### `needs_review`

`needs_review` (boolean) is the one field the collector adds beyond SCHEMA.md. It marks items whose
classification has not been confirmed: everything from the heuristic path, LLM results that failed
validation or had low confidence, and all reader submissions until an editor looks at them. The
front-end may show these with a lighter badge or hide them behind a toggle; it must not treat the
field as absent.

## Reviewing items

1. Open `site/data/stream.json` and search for `"needs_review": true`, or open
   `pipeline/seed/_collector_dry_run.json` after a dry run to see what the next real run would add
   and why candidates were rejected (`rejected_items`, with reason).
2. Check the URL, fix `date`, `kind`, `polarity`, `failure_sources`, `operations`, `subsections`,
   `domain`, `actors`, and rewrite `summary` as two factual sentences from the source if needed.
   Add `related_papers` by bib key from `papers.json` when a paper speaks directly to the event.
3. Set `needs_review` to `false` (or delete the item). Keep `id` unchanged so later runs still
   recognise it; the collector dedupes by URL and title, not by id.
4. To exclude an item, delete it. Unverifiable items are never published, so `verified: false`
   is not a state the file should contain. If a deleted item keeps coming back, lower the feed's
   weight in `feeds.yml` or add a negative keyword to `NEGATIVE_TERMS` in `classify.py`.
5. Reader submissions: once the item is in the stream, close the issue with a link to the item id.

## Regenerating the paper data

```bash
python3 pipeline/build_data.py            # see `--help` for the source path option
```

`build_data.py` reads the paper's tooling repository (read-only) and rewrites `taxonomy.json`, `papers.json`,
`grey.json` and `stats.json`. It preserves the `stream_items` and
`stream_updated` fields of `stats.json`, which belong to the collector; if it did not, run
`python3 pipeline/collect_news.py --since 0` afterwards to restore them (that run fetches feeds but
adds nothing new). Field definitions are in `../SCHEMA.md`.

## Files

```
pipeline/
  build_data.py        paper repo -> site/data (taxonomy, papers, grey, stats)
  collect_news.py      feeds + submissions -> stream.json (this document)
  classify.py          LLM and heuristic classifiers, taxonomy loader, validation
  feeds.yml            curated sources with weights and check dates
  seed/                sweep_*.json (the seed), _collector_dry_run.json (last dry run)
  tests/               offline unit tests (python3 -m unittest discover -s pipeline/tests)
```
