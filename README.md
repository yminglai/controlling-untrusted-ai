# Companion site for Controlling Untrusted AI: A Survey

The companion website of the survey *Controlling Untrusted AI: A Survey* (draft v0.2, October 2026;
arXiv link to come). Published as a static site on GitHub Pages at
`https://ymingl.com/controlling-untrusted-ai/` (the account's GitHub Pages custom domain; project sites are
served under it, so the repository needs no CNAME of its own).

The site does two things.

1. **The paper collection.** Every paper the survey placed into its taxonomy (1,788 arXiv papers and
   164 reports and posts from outside arXiv), browsable by the paper's own 11 sections and 56
   subsections, searchable and filterable, with a card per paper (method-style label, authors, year,
   one-line summary, placement reason, cross-references). 239 items are cited in the PDF; the rest are
   the reading list behind it.
2. **The live stream.** A continuously collected feed of real-world news about deploying AI agents,
   good and bad: incidents, near misses, deployments, shipped safety features, evaluations, policy and
   vendor disclosures. Every item is classified into the survey taxonomy (failure source, requirement,
   control operation, subsection), so the feed is a field-evidence companion to the paper. The stream
   was seeded by a verified sweep and is refreshed by a scheduled collector; readers can submit items.

Everything is plain HTML, CSS and JavaScript (ES modules, `fetch()` of JSON) plus Python scripts.
There is no bundler, no framework, no server, no analytics, no cookies and no trackers; the only
third-party request is for the typefaces (Google Fonts, with system fallbacks).

## Repository layout

```
BRIEF.md  SCHEMA.md         the brief and the data contracts (read these first)
design/                     DESIGN.md (the front-end spec), concepts, judge reports, implementation
                            notes, change requests, screenshots (shots/)
site/                       the published site: index.html  papers.html  stream.html  about.html  404.html
  assets/css/               tokens.css  site.css  papers.css  stream.css
  assets/js/                common.js  taxonomy.js  papers.js  stream.js  search.js
  assets/img/               the two figures of the paper, favicon.svg, og.png (+ og.html that made it)
  data/                     taxonomy.json  papers.json  grey.json  stats.json  stream_recent.json  stream.json
pipeline/                   build_data.py  collect_news.py  classify.py  feeds.yml  seed/  tests/  README.md
.github/                    workflows/collect.yml  workflows/pages.yml  ISSUE_TEMPLATE/submit_item.yml
```

The front-end reads only the files under `site/data/`; their field names are fixed in `SCHEMA.md`.
`design/DESIGN.md` is the specification the pages follow; `design/IMPLEMENTATION_NOTES.md` lists the
shared tokens, utilities and helpers a page may use.

## Local preview

Serve the `site/` directory with any static server, for example:

```bash
cd controlling-untrusted-ai
python3 -m http.server 8765 --directory site
# open http://localhost:8765/
```

All URLs are relative, so the site also works from `file://` and from a sub-path such as
`https://ymingl.com/controlling-untrusted-ai/`. Append `?theme=light` or `?theme=dark` to any page to force a
theme for screenshots; otherwise the theme follows the system and the masthead toggle (stored in
`localStorage` under `cuai-theme`).

To check a page the way the reviewers do (headless Chrome, zero console errors):

```bash
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
"$CHROME" --headless=new --disable-gpu --hide-scrollbars --window-size=1440,900 \
  --virtual-time-budget=4000 --screenshot=/tmp/index.png http://localhost:8765/
"$CHROME" --headless=new --disable-gpu --window-size=1440,900 --virtual-time-budget=5000 \
  --enable-logging=stderr --v=0 --dump-dom http://localhost:8765/ 2>&1 >/dev/null | grep CONSOLE
```

Headless Chrome enforces a 500 px minimum window, so a true 390 px capture needs a wrapper page with a
390 × 844 `<iframe>`; `design/IMPLEMENTATION_NOTES.md` section 1 describes the recipe.

## Regenerating the paper data

`pipeline/build_data.py` reads the paper's repository (the read-only Overleaf clone: `outline.json`,
`research/corpus_full.json`, `research/grey_v2.json`, `research/labels_method_style.json`) and rewrites
`taxonomy.json`, `papers.json`, `grey.json` and `stats.json` under `site/data/`.

```bash
python3 pipeline/build_data.py                      # clone expected at ../overleaf-ai-control
python3 pipeline/build_data.py --overleaf PATH      # or point at it
python3 pipeline/build_data.py --generated 2026-10-17 --quiet
```

Pure standard library (Python 3.12+). Output is deterministic for a given `--generated` date. The
script never writes to the paper's repository, preserves the `stream_items` and `stream_updated`
fields of `stats.json` (they belong to the collector) and prints every anomaly it finds in the sources
as `ANOMALY: ...` lines without stopping. Run the offline tests afterwards:

```bash
python3 -m unittest discover -s pipeline/tests -v
```

Each page writes today's numbers into its static HTML and re-binds them from `stats.json` at runtime
(`data-bind` attributes), so a regeneration needs no edit to the pages; the data files are fetched with
`?v=<stats.generated>` so browsers pick up the new versions.

## The collector and the GitHub Action

`pipeline/collect_news.py` refreshes `site/data/stream.json`. It reads the RSS and Atom feeds and arXiv
queries listed in `pipeline/feeds.yml` (each with a weight, the prior that an entry is about deploying
agents), optionally the open GitHub issues labelled `submission`, drops anything already in the stream
(by normalised URL and by title), classifies each candidate into the taxonomy with
`pipeline/classify.py` (a language model through an OpenAI-compatible chat endpoint, with a keyword
classifier as fallback), fetches every kept URL to verify it, and merges the new items in date order.
Items that cannot be verified are not published. Items whose classification is unconfirmed carry
`needs_review: true` and show "Review pending" on the site until an editor clears them.

```bash
python3 -m pip install requests pyyaml
python3 pipeline/collect_news.py --dry-run --no-llm --since 30 --limit 20   # touches nothing under site/
python3 pipeline/collect_news.py --since 10 --issues yminglai/controlling-untrusted-ai
```

Environment: `LLM_API_KEY` and `LLM_BASE_URL` (the endpoint ending in `/v1`), optionally `LLM_MODEL`
and `GITHUB_TOKEN`. Keys are read from the environment only and are never printed or written to disk.
Without the LLM variables the collector falls back to the keyword classifier and marks everything for
review. Flags, the classification contract, the review procedure and how the seed was made are
documented in `pipeline/README.md`.

`.github/workflows/collect.yml` runs the collector every six hours (and on manual dispatch, with
`since`, `limit` and `no_llm` inputs), then commits `site/data/stream.json` and `site/data/stats.json`
when they changed. It needs the repository secrets `LLM_API_KEY` and `LLM_BASE_URL` and the repository
variable `LLM_MODEL`; the job token provides `GITHUB_TOKEN` (`contents: write`, `issues: read`).

## Submitting items

Readers submit through the issue form "Submit a stream item" (`.github/ISSUE_TEMPLATE/submit_item.yml`,
linked from every page as "Submit an item"): a public URL, a date, two to four factual sentences, good
or bad, the failure source and the operation. The collector picks up open issues with the `submission`
label on its next run, classifies and verifies them, and adds them with `needs_review: true`; the
editor confirms the classification and closes the issue with the item id. Corrections to existing
items go through the "Report a problem" button on an expanded stream row, which opens an issue titled
`[Submission]: Correction to <id>`.

## Deploying to GitHub Pages

The site is published from the `site/` directory by `.github/workflows/pages.yml` with the official
Pages actions: on every push to `main` that touches `site/`, on manual dispatch, and after every
successful "Collect stream" run (`workflow_run`, because commits made with the job token do not fire
push workflows). The workflow checks that every `site/data/*.json` parses before uploading.

One-time setup in the repository: Settings → Pages → Source: "GitHub Actions". Nothing else is
needed; there is no build step. `site/404.html` is served for unknown paths; it resolves its assets
from the site root even for nested paths such as `/<repo>/stream/`. `og:url` and `og:image` in the
page heads are absolute (crawlers require it) and point at `https://ymingl.com/controlling-untrusted-ai/`;
change them if the site moves.

## No branding

This repository is published from a personal account and carries no company branding: no logos, no
employer names, no analytics. The author line is a placeholder (`[Authors]`) until the arXiv version
appears; `PAPER_STATUS` in `site/assets/js/common.js` and the status lines in `index.html` and
`about.html` are the places to update.

## Licence

Text and data (site pages, `site/data/`, `pipeline/seed/`, documentation) are released under
CC BY 4.0; the code (`site/assets/`, page markup, `pipeline/*.py`, workflows) under the MIT License.
See `LICENSE`. Paper records describe third-party works that keep their own licences; stream items
link to their original sources.
