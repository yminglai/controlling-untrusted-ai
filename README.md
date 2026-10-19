# Companion site for Controlling Untrusted AI: A Survey

The companion website of the survey *Controlling Untrusted AI: A Survey* (draft v0.2, October 2026;
arXiv link to come). A static site on GitHub Pages at `https://ymingl.com/controlling-untrusted-ai/`.

The site is three things: the paper, the papers arranged by the paper's structure, and the live stream.

1. **The paper collection.** Every paper the survey placed into its structure (1,788 arXiv papers and
   164 reports and posts from outside arXiv), browsable by the paper's four parts, 10 sections and 29
   subsections, searchable and filterable, with a card per paper and a detail drawer with
   cross-references. 239 items are cited in the PDF; the rest are the reading list behind it.
2. **The live stream.** News about deploying AI agents, good and bad: incidents, near misses,
   deployments, shipped safety features, evaluations, policy and vendor disclosures. Every item is filed
   under the paper's structure (attack tier, requirement, control operation, subsection). Items are
   collected from feeds and reader submissions, classified, and checked at the source before publication.

Plain HTML, CSS and JavaScript (ES modules, `fetch()` of JSON) plus Python scripts. No bundler, no
framework, no server, no analytics, no cookies, no trackers; the only third-party request is for the
typefaces (Google Fonts, with system fallbacks).

## Structure

The paper has four parts and 10 sections; subsection ids are positional (`s5_2` is the second
subsection of Section 5) and come from `site/data/taxonomy.json`, which also carries a fingerprint of
its subsection list (`structure`) so that a changed outline is detected.

| Part | Sections |
|---|---|
| Foundations | 1 Introduction · 2 Failure Modes of Deployed Agents · 3 Preliminaries |
| System-Level Control | 4 Action Constraints · 5 Monitoring · 6 Intervention |
| Model-Level Control | 7 Model-Level Methods |
| Evaluation and Assurance | 8 Evaluation Methodology · 9 Composition and Assurance · 10 Outlook |

The attack tiers are benign, external and insider; the control operations are constrain, monitor,
intervene (Sections 4 to 6), steer and train (both Section 7), evaluate (Section 8) and deploy
(Section 9).

## Repository layout

```
BRIEF.md  SCHEMA.md         the brief and the data contracts
design/                     the front-end spec, implementation notes and screenshots (shots/)
site/                       the published site: index.html  papers.html  stream.html  404.html
  assets/css/               tokens.css  site.css  papers.css  stream.css
  assets/js/                common.js  taxonomy.js  papers.js  stream.js  search.js
  assets/img/               favicon.svg, og.png
  data/                     taxonomy.json  papers.json  grey.json  stats.json  stream_recent.json  stream.json
pipeline/                   build_data.py  collect_news.py  classify.py  remap_stream.py  feeds.yml  seed/  tests/
.github/                    workflows/collect.yml  workflows/pages.yml  ISSUE_TEMPLATE/submit_item.yml
```

The front-end reads only the files under `site/data/`; their field names are fixed in `SCHEMA.md`.

## Local preview

```bash
python3 -m http.server 8765 --directory site     # then open http://localhost:8765/
```

All URLs are relative, so the site also works from `file://` and from a sub-path. Append `?theme=light`
or `?theme=dark` to any page to force a theme; otherwise the theme follows the system and the masthead
toggle (stored in `localStorage` under `cuai-theme`). Headless Chrome enforces a 500 px minimum window,
so a 390 px capture needs a wrapper page with a 390 × 844 `<iframe>` (`design/IMPLEMENTATION_NOTES.md`).

## Regenerating the paper data

`pipeline/build_data.py` reads the paper's repository (the read-only Overleaf clone) and rewrites
`taxonomy.json`, `papers.json`, `grey.json`, `stats.json` and `stream_recent.json` under `site/data/`.

```bash
python3 pipeline/build_data.py --overleaf PATH --generated 2026-10-19
python3 -m unittest discover -s pipeline/tests -v
```

Pure standard library (Python 3.12+); deterministic for a given `--generated` date; never writes to the
paper's repository. Each page carries today's numbers in its static HTML and re-binds them from
`stats.json` at runtime, so a regeneration needs no edit to the pages. When the outline changes, the
tests fail until `pipeline/remap_stream.py` has re-filed the stream onto the new subsection ids
(`taxonomy.structure` versus `stream.taxonomy_structure`); a new outline needs a new map in that script.

## The collector

`pipeline/collect_news.py` refreshes `site/data/stream.json`: it reads the feeds in `pipeline/feeds.yml`
and the open GitHub issues labelled `submission`, drops what is already in the stream, classifies each
candidate into the paper's structure with `pipeline/classify.py` (a language model through an
OpenAI-compatible endpoint, keyword fallback), fetches every kept URL to verify it, and merges the new
items in date order. Unverifiable items are not published; unconfirmed classifications carry
`needs_review: true` and show "Review pending" until an editor clears them.

```bash
python3 -m pip install requests pyyaml
python3 pipeline/collect_news.py --dry-run --no-llm --since 30 --limit 20
python3 pipeline/collect_news.py --since 10 --issues yminglai/controlling-untrusted-ai
```

Environment: `LLM_API_KEY`, `LLM_BASE_URL` (ending in `/v1`), optionally `LLM_MODEL` and `GITHUB_TOKEN`;
keys are read from the environment only. `.github/workflows/collect.yml` runs the collector every six
hours and commits `stream.json` and `stats.json` when they changed; `.github/workflows/pages.yml` publishes
`site/` after every push to `main` that touches it and after every successful collector run. Flags and the
review procedure are in `pipeline/README.md`.

## Submitting items

Readers submit through the issue form "Submit a stream item" (`.github/ISSUE_TEMPLATE/submit_item.yml`,
linked from every page as "Submit an item"). Corrections to existing items go through "Report a problem"
on an expanded stream row.

## Cite

Until the arXiv version appears, cite the draft as:

```bibtex
@article{authors2026controlling,
  title  = {Controlling Untrusted AI: A Survey},
  author = {[Authors]},
  year   = {2026},
  note   = {Draft v0.2, October 2026. arXiv link to come.},
  url    = {https://ymingl.com/controlling-untrusted-ai/}
}
```

## No branding

Published from a personal account; no logos, no employer names, no analytics. The author line is a
placeholder (`[Authors]`) until the arXiv version appears; the status line in `site/index.html` and the
BibTeX entry above are the places to update.

## Licence

Text and data (site pages, `site/data/`, `pipeline/seed/`, documentation) are released under CC BY 4.0;
the code (`site/assets/`, page markup, `pipeline/*.py`, workflows) under the MIT License. See `LICENSE`.
Paper records describe third-party works that keep their own licences; stream items link to their sources.
