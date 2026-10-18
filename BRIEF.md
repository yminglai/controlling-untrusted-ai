# Project brief: companion website for "Controlling Untrusted AI: A Survey"

This directory is the companion repository of the survey. It will be published from a personal
GitHub account as a static site (GitHub Pages). It must carry **no company branding** (no logos,
no employer names). Everything here is plain HTML, CSS and JavaScript plus Python scripts; there is
no bundler and no server.

## The two things the site does

1. **The paper collection.** Every paper the survey placed into its taxonomy, browsable by the
   survey's own structure (11 sections, 56 subsections), searchable, filterable, with a card per
   paper (method-style label, authors, year, one-line summary, arXiv link, cross-references, and
   for 239 papers a structured Chinese reading summary). 1,788 arXiv papers + ~150 verified
   non-arXiv ("grey") items. 239 are cited in the PDF; the rest are the full reading list.
2. **The live stream.** A continuously collected feed of real-world news about *deploying AI
   agents*, good and bad: incidents, near misses, successful deployments, new safety features,
   evaluations, policy. Every item is classified into the survey taxonomy (which failure source,
   which requirement, which control operation, which subsection) so the feed is a field-evidence
   companion to the paper. The feed is seeded once by a verified sweep and then refreshed by a
   scheduled collector (RSS + search + LLM classification) that writes `site/data/stream.json`.
   Readers can submit items via a GitHub issue template.

The site must make both parts first-class: a visitor should understand within five seconds that
this is (a) a survey with its full corpus and (b) a living tracker of agent deployment in the wild.

## The survey in one paragraph (use this vocabulary, do not invent new terms)

Deployed AI agents must meet their operator's requirements: be **correct, compliant, in scope,
within budget, and safe**. They cannot be trusted to meet them on their own, for three reasons
(**failure sources**): they make **mistakes**, they can be **manipulated** by what they read
(prompt injection, memory poisoning), and they may be **misaligned** (pursue objectives of their
own, deceive, resist oversight). **Control** is whatever makes the agent's actions meet the
requirements without taking the agent's good intentions on trust. It works through **two levers**:
change the deployment around the agent (**Constrain** what it can do, **Observe** what it does,
**Intervene** when something is off) or change the model (**Train** before deployment, **Steer** at
inference time). **Verify** tests either lever (control evaluations, red teams, audits, statistics).
**Deployment and Assurance** composes mechanisms into stacks, safety cases, policy, independent
assurance. Every mechanism is graded by a **two-level test**: L1, does it still work if the agent is
indifferent to the requirement; L2, does it still work if the agent tries to defeat it and knows how
it works. Audience: people deploying agents in production, researchers inside one mechanism
family, and evaluators/auditors/policy staff.

Title: **Controlling Untrusted AI: A Survey**. No subtitle. Authors: placeholder "[Authors]" for now.
Status: draft v0.2, October 2026, arXiv link to come. Heading style of the paper: Title Case noun
phrases of two to five words, no colons, no sentences. Prose style: plain, concrete, no hype.

## Section map (ids are the survey's subsection ids; colours are the site's tokens)

| id | Section | Operation | Colour token |
|---|---|---|---|
| s1 | Introduction | — | ink/gray |
| s2 | How Agents Fail | failures | coral `#D95358` |
| s3 | Problem Setting and Definitions | setting | gray `#7D7D7D` |
| s4 | Constraining Agent Actions | constrain | terracotta `#E27553` |
| s5 | Observing Agent Behaviour | observe | blue `#598DD2` |
| s6 | Intervening on Actions | intervene | amber `#E09A3B` |
| s7 | Steering at Inference Time | steer | teal `#65C2B9` |
| s8 | Training for Control Properties | train | periwinkle `#8D86E8` |
| s9 | Verifying Control Measures | verify | forest `#62A16E` |
| s10 | Deployment and Assurance | deploy | purple `#A37CAD` |
| s11 | Open Problems and Outlook | — | gray |

Failure sources: mistakes coral `#D95358`, manipulation amber `#E09A3B`, misalignment purple `#A37CAD`.
Polarity of stream items: good forest `#62A16E`, bad coral `#D95358`, mixed gold `#D1B745`.
Neutrals (from the paper's class file): ink `#2E2E2E`, gray `#7D7D7D`, medium gray `#C7C7C7`,
light gray `#EAEAEA`, panel `#F7F7F7`, white, link `#598DD2`. Extra accents available: sky
`#6FCBEF`, pink `#E072AF`, gold `#D1B745`, sand `#C7A678`, slate `#75A4B5`. Use these tokens only.
Colour is a functional signal in this project (section identity, failure source, polarity); do not
go monochrome. Both a light and a dark theme are wanted; verify contrast.

The two figures of the paper are available as rasters for reference and may be shown on the site:
`site/assets/img/fig1_why_control.jpg` (the control gap, four operations, three failure sources) and
`site/assets/img/fig2_mechanism_map.jpeg` (two levers, verify, five questions).

## Source data (read-only; absolute paths; never modify these files)

Overleaf clone of the paper: `/Users/minglai.yang/Desktop/Scale_AI_LaTeX_Paper_Template/overleaf-ai-control/`

- `outline.json`: title, thesis, readers, 11 sections with `number`, `title`, `purpose`, subsections
  with `title`, `bullets`, `key_refs`, `further_refs`. Subsection ids are positional: section k,
  subsection j => `s{k}_{j}` (e.g. the second subsection of section 5 is `s5_2`).
- `research/corpus_full.json`: `{generated, counts, subsections:[{id,title,section}], papers:[...], grey:[...]}`.
  1,788 papers with `pid, arxiv_id, key, title, authors[], year, primary (sid), score (3 must-cite / 2 relevant),
  selected (bool, cited in the PDF), short_label, one_line, reason, also:[{sid,score,reason}], reading_rank, seed`.
  `grey` = 49 selected non-arXiv items `{sid,key,title,authors,year,short_label,venue,url,confidence,one_line}`.
  NOTE: `subsections[].title` and `counts.per_section` carry OLD long titles; take current titles from `outline.json`.
- `research/grey_v2.json`: `{entries:[155 items], unresolved:[12 strings]}`; entries have
  `sid, key_hint, title, authors, year, month, venue_or_publisher, url, confidence, verification_source, ...`.
- `research/labels_method_style.json`: `{bibkey: "Method-Style Label"}` for 1,935 items (prefer over short_label).
- `research/summaries_zh.json`: list of 239 structured Chinese summaries keyed by `key` (bib key):
  fields `定位, 问题, 方法, 发现[], 部署启示, 局限, 与小节关系, 阅读深度, 术语[], 存疑, title, year, sid, label, text_depth, url, arxiv_id`.
- `research/evidence/<sid>.md`: abstract-level evidence cards per subsection (claims, numbers, caveats).
- `research/BRIEFS.md`, `research/READING_LIST.md`: writer briefs and the full reading list (markdown).
- `references.bib`: 248 entries, keys `<lastname><year><firstword>`.
- `main.pdf`: current 67-page skeleton build (not for the site yet; the site links a PDF placeholder).

## Constraints

- Static, no build step for the front-end. ES modules, `fetch()` of JSON under `site/data/`. All
  URLs **relative** so the site works at `https://<user>.github.io/<repo>/` and from `file://` or a
  local `python3 -m http.server`. No analytics, no trackers, no cookies.
- Dependencies only via CDN with pinned versions, and only if they earn their place (a tiny search
  library is fine; a framework is not). Google Fonts is acceptable; provide system-font fallbacks.
- Performance: first paint under 1 s on a laptop; `papers.json` (~1 MB) may be loaded lazily or
  split per section; Chinese summaries loaded on demand.
- Accessibility: keyboard-navigable, visible focus, semantic landmarks, contrast AA in both themes,
  `prefers-reduced-motion` respected.
- Robustness: reviewers will test with headless Chrome. The site must render with zero console errors.
- No company branding, no logos, no employer names. Author line is a placeholder.
- The user's taste: colour as functional signal; editorial, paper-like typography; short noun-phrase
  headings; polished, "fancy" but credible to an academic/security audience. Avoid AI-sounding copy
  (no "delve", "landscape", "unlock", "robust", em-dashes). Avoid stock illustrations.

## Local tooling available

Python 3.14 (`requests`, `pyyaml` installed; `feedparser` NOT installed: use `requests` + `xml.etree`
or vendor a minimal RSS parser). Node 26 (no packages installed; do not add a build). Headless Chrome:
`"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --screenshot=/path/out.png --window-size=1440,900 --hide-scrollbars http://localhost:8765/`
(also `--dump-dom`, `--virtual-time-budget=5000`). Static server: `python3 -m http.server 8765 --directory site`
from this directory (check whether one already runs on 8765 before starting another; reuse it).
LLM gateway for the collector (same as the paper's scripts): OpenAI-compatible
`POST $LLM_BASE_URL/chat/completions` (default `https://litellm-proxy.ml.scale.com/v1`) with
`Authorization: Bearer $LLM_API_KEY`, model from `$LLM_MODEL` (default `anthropic/claude-opus-5-5`);
the gateway rejects `temperature != 1`. Never print or commit key values; read them from the
environment only. GitHub account for the eventual repo: `yminglai` (do not create or push anything).

## Directory layout (fixed; agents write only to the paths assigned to them)

```
controlling-untrusted-ai/
  BRIEF.md  SCHEMA.md  README.md  LICENSE
  design/            concept_*.md, judge_*.md, DESIGN.md (the spec the front-end follows)
  site/              index.html  papers.html  stream.html  about.html  404.html
    assets/css/      tokens.css  site.css  papers.css  stream.css
    assets/js/       common.js  taxonomy.js  papers.js  stream.js  search.js (as needed)
    assets/img/      figures, favicon, og image
    data/            taxonomy.json  papers.json  grey.json  summaries_zh.json  stream.json  stats.json
  pipeline/          build_data.py (paper repo -> site/data)  collect_news.py  classify.py  feeds.yml
                     seed/ (sweep outputs)  tests/
  .github/           workflows/collect.yml  ISSUE_TEMPLATE/submit_item.yml
```
