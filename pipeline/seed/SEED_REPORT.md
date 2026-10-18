# Seed report, 2026-10-17

Input: 261 candidate files in `pipeline/seed/items/`. Kept after the `relevant && verified` gate: 256. Merged away as further reports of an event already in the set: 25 items in 23 clusters. Published to `site/data/stream.json`: **231 items** (`generated` 2026-10-17T00:00:00Z, source `seed sweep 2026-10-17`), dates 2024-02-01 to 2026-10-17. `stats.json` now carries `stream_items: 231` and `stream_updated: "2026-10-17T00:00:00Z"`; no other field was touched.

## Counts

### By kind

| kind | items |
|---|---:|
| incident | 34 |
| near-miss | 1 |
| deployment | 31 |
| safety-feature | 43 |
| evaluation | 39 |
| research | 13 |
| policy | 28 |
| disclosure | 42 |

### By polarity

| polarity | items |
|---|---:|
| bad | 97 |
| good | 93 |
| mixed | 41 |

### By failure source

An item can carry several; `(none)` means the item is not about a failure. For items with polarity `good` the failure source is the one the control addresses.

| failure source | items |
|---|---:|
| mistakes | 40 |
| manipulation | 71 |
| misalignment | 47 |
| (none) | 90 |

### By operation

An item can carry several.

| operation | items |
|---|---:|
| constrain | 149 |
| observe | 128 |
| intervene | 97 |
| steer | 10 |
| train | 22 |
| verify | 71 |
| deploy | 85 |

### By section

`primary` counts each item once, under the section of its first (most specific) subsection; `any` counts an item under every section it touches.

| section | title | primary | any |
|---|---|---:|---:|
| s1 | Introduction | 0 | 2 |
| s2 | How Agents Fail | 82 | 136 |
| s3 | Problem Setting and Definitions | 0 | 16 |
| s4 | Constraining Agent Actions | 50 | 145 |
| s5 | Observing Agent Behaviour | 25 | 110 |
| s6 | Intervening on Actions | 17 | 85 |
| s7 | Steering at Inference Time | 1 | 11 |
| s8 | Training for Control Properties | 1 | 15 |
| s9 | Verifying Control Measures | 19 | 54 |
| s10 | Deployment and Assurance | 36 | 119 |
| s11 | Open Problems and Outlook | 0 | 7 |

### By subsection (any position)

| subsection | title | items |
|---|---|---:|
| s1_1 | Why Agents Cannot Be Trusted | 1 |
| s1_2 | The Control Gap | 1 |
| s2_1 | Compounding Mistakes | 29 |
| s2_2 | Prompt Injection and Memory Poisoning | 64 |
| s2_3 | Reward Hacking and Harness Tampering | 9 |
| s2_4 | Deception and Loss of Control | 38 |
| s2_5 | From Failures to Control Requirements | 1 |
| s3_1 | The Deployment Setting | 7 |
| s3_2 | Failure Sources and Threat Models | 7 |
| s3_3 | Five Questions for Every Mechanism | 1 |
| s3_4 | The Adversarial Case | 1 |
| s4_1 | Least Privilege | 91 |
| s4_2 | Sandboxing and Isolation | 46 |
| s4_3 | Formal Action Constraints | 8 |
| s4_4 | Information-Flow Control | 40 |
| s4_5 | Identity, Credentials, and Delegation | 47 |
| s5_1 | Logging and Provenance | 43 |
| s5_2 | Guardrails and Action Monitors | 51 |
| s5_3 | Chain-of-Thought Monitoring | 14 |
| s5_5 | Trusted and Untrusted Monitors | 4 |
| s5_6 | Human Review under a Budget | 16 |
| s6_1 | Approval Gates | 64 |
| s6_2 | Blocking, Editing, and Deferral | 9 |
| s6_4 | Shutdown and Fallback | 11 |
| s6_5 | Reversibility and Rollback | 9 |
| s7_1 | Instruction Design | 9 |
| s7_3 | Planning and Self-Correction | 2 |
| s8_1 | General Safety Training | 5 |
| s8_2 | Supervised and Preference Training | 3 |
| s8_3 | Reasoning-Based Safety | 1 |
| s8_4 | Adversarial Training | 6 |
| s8_6 | Safety Retention | 1 |
| s9_1 | Evaluation against Mistakes | 17 |
| s9_2 | Evaluation against Manipulation | 13 |
| s9_3 | Control Evaluations | 22 |
| s9_4 | Control Settings | 3 |
| s9_5 | White-Box Audits | 1 |
| s9_6 | Statistics and Reporting | 9 |
| s10_1 | Reference Architectures | 41 |
| s10_2 | Release Gates and Incident Feedback | 53 |
| s10_3 | Safety Cases | 6 |
| s10_4 | Policies and Regulation | 33 |
| s10_5 | Independent Assurance | 24 |
| s11_1 | Mistakes | 2 |
| s11_2 | Manipulation | 1 |
| s11_3 | Misalignment | 1 |
| s11_4 | Metrics, Reporting, and Cost | 4 |

### By year

| year | items |
|---|---:|
| 2024 | 24 |
| 2025 | 133 |
| 2026 | 74 |

### By domain

| domain | items |
|---|---:|
| coding | 46 |
| infrastructure | 26 |
| cyber | 23 |
| browsing | 22 |
| other | 19 |
| research | 18 |
| email-and-office | 16 |
| government | 16 |
| customer-service | 14 |
| consumer | 13 |
| finance | 9 |
| healthcare | 4 |
| multi-agent | 4 |
| legal | 1 |

### By evidence

| evidence | items |
|---|---:|
| first-party | 96 |
| researcher | 65 |
| press | 29 |
| incident-database | 21 |
| regulator | 18 |
| court | 2 |

### By lens

| lens | items |
|---|---:|
| misalignment-field | 33 |
| incidents-injection | 31 |
| policy | 31 |
| safety-features | 31 |
| good-deployments | 30 |
| month-by-month | 26 |
| incident-databases | 25 |
| incidents-coding | 24 |

## Merged items

Rule applied: one entry per event; the most primary source is kept (vendor disclosure or official report > researcher > incident database > press), the other URLs go to the new optional `also_urls` field, and `related_papers` and `tags` are the union of the cluster. Classification fields (kind, polarity, failure sources, operations, subsections) stay those of the kept source. The item date is the event date when the kept source states it, otherwise the earliest report in the cluster; every change is recorded in the item's `verification_note`.

1. **Replit agent deleted SaaStr's production database (July 2025)**  
   kept: `223.json` AI Incident Database, https://incidentdatabase.ai/cite/1152/  
   absorbed into also_urls: `076.json` eWeek, https://www.eweek.com/news/replit-ai-coding-assistant-failure/  
   absorbed into also_urls: `006.json` Fortune, https://fortune.com/2025/07/23/ai-coding-tool-replit-wiped-database-called-it-a-catastrophic-failure/  
   why: AI Incident Database entry (incident database > press); Fortune and eWeek are press reports of the same event; date 2025-07-18 (kept: AIID incident date, the earliest in the cluster).
2. **EchoLeak zero-click injection in Microsoft 365 Copilot (June 2025)**  
   kept: `225.json` AI Incident Database, https://incidentdatabase.ai/reports/5329/  
   absorbed into also_urls: `033.json` The Hacker News, https://thehackernews.com/2025/06/zero-click-ai-vulnerability-exposes.html  
   why: AI Incident Database report (incident database > press); The Hacker News is press; date 2025-06-11 (kept: earliest in the cluster).
3. **UK AISI evaluation of GPT-6 Astra supply-chain attacks (Sept 2026)**  
   kept: `094.json` UK AI Security Institute, https://www.aisi.gov.uk/research/evaluating-whether-gpt-6-astra-performs-unsanctioned-supply-chain-attacks  
   absorbed into also_urls: `193.json` UK AI Security Institute, https://www.aisi.gov.uk/blog/gpt-6-astra-performs-unsanctioned-supply-chain-attacks-in-simulations  
   why: AISI technical report over the AISI blog post summarising it (same publisher, same day); date 2026-09-28 (kept: same date).
4. **Amazon Kiro agent and the AWS Cost Explorer outage (Dec 2025)**  
   kept: `216.json` AI Incident Database, https://incidentdatabase.ai/cite/1442/  
   absorbed into also_urls: `020.json` Engadget, https://www.engadget.com/ai/13-hour-aws-outage-reportedly-caused-by-amazons-own-ai-tools-170930190.html  
   why: AI Incident Database entry (incident database > press); Engadget is press; date 2025-12-01 (kept: month precision in both).
5. **Claude Code terraform destroy at DataTalks.Club (Feb 2026)**  
   kept: `024.json` Alexey Grigorev (Alexey On Data), https://aishippingblog.com/p/how-i-dropped-our-production-database  
   absorbed into also_urls: `209.json` AI Incident Database, https://incidentdatabase.ai/cite/1424/  
   why: the deployer's own write-up (first-party > incident database); date 2026-02-26 (set to the event date 26 February 2026 stated in the write-up (also the AIID date)).
6. **Claude Code auto mode (March 2026)**  
   kept: `133.json` Anthropic, https://www.anthropic.com/engineering/claude-code-auto-mode  
   absorbed into also_urls: `248.json` Anthropic, https://claude.com/blog/auto-mode  
   why: Anthropic engineering post with the evaluation numbers over the launch announcement (both first-party); date 2026-03-24 (set to the launch announcement date, the earliest report).
7. **Amazon v. Perplexity over the Comet shopping agent (Nov 2025)**  
   kept: `218.json` AIAAIC Repository, https://www.aiaaic.org/aiaaic-repository/ai-algorithmic-and-automation-incidents/perplexity-ai-shopping-agent-accused-of-violating-amazon-terms-of-service  
   absorbed into also_urls: `243.json` Payments Dive, https://www.paymentsdive.com/news/amazon-sues-perplexity-ai-shopping-agents/804923/  
   absorbed into also_urls: `180.json` Retail Insight Network, https://www.retail-insight-network.com/news/amazon-sues-perplexity-agentic-ai/  
   why: AIAAIC repository entry (incident database > press); Payments Dive and Retail Insight Network are press; date 2025-11-04 (kept: earliest in the cluster).
8. **CurXecute, Cursor's MCP prompt-injection CVEs (Aug 2025)**  
   kept: `037.json` Tenable, https://www.tenable.com/blog/faq-cve-2025-54135-cve-2025-54136-vulnerabilities-in-cursor-curxecute-mcpoison  
   absorbed into also_urls: `010.json` The Hacker News, https://thehackernews.com/2025/08/cursor-ai-code-editor-fixed-flaw.html  
   why: Tenable FAQ (researcher > press); The Hacker News is press; date 2025-08-01 (set to the earliest report, 1 August 2025).
9. **GTG-1002 espionage campaign through Claude Code (Nov 2025)**  
   kept: `018.json` Anthropic, https://www.anthropic.com/news/disrupting-AI-espionage  
   absorbed into also_urls: `217.json` AI Incident Database, https://incidentdatabase.ai/cite/1263/  
   why: Anthropic's own disclosure (first-party > incident database); date 2025-11-13 (kept: same date).
10. **Taco Bell rethinks voice AI drive-thru (Aug 2025)**  
   kept: `099.json` GIGAZINE (reporting a Wall Street Journal interview), https://gigazine.net/gsc_news/en/20250831-taco-bell-rethinks-voice-ai-drive-through  
   absorbed into also_urls: `237.json` Sherwood News, https://www.sherwood.news/culture/taco-bell-is-rethinking-its-ai-drive-thrus-amid-glitches-and-trolls-ordering  
   why: both are press reports of one Wall Street Journal interview; the fuller account kept; date 2025-08-28 (set to the earliest report, 28 August 2025).
11. **Calendar-invite promptware against Gemini assistants (Aug 2025)**  
   kept: `039.json` arXiv, https://arxiv.org/abs/2508.12175  
   absorbed into also_urls: `222.json` MITRE ATLAS, https://atlas.mitre.org/studies/AML.CS0063  
   why: the researchers' paper (researcher > incident database); MITRE ATLAS CS0063 records the same exercise; date 2025-08-06 (set to the ATLAS exercise date 6 August 2025 (Black Hat USA presentation)).
12. **Zenity's Microsoft 365 Copilot demonstrations at Black Hat 2024**  
   kept: `029.json` TechTarget (SearchSecurity), https://www.techtarget.com/searchsecurity/news/366602358/Zenity-CTO-on-dangers-of-Microsoft-Copilot-prompt-injections  
   absorbed into also_urls: `230.json` AIAAIC Repository, https://www.aiaaic.org/aiaaic-repository/ai-algorithmic-and-automation-incidents/microsoft-copilot-can-be-turned-into-automated-phishing-machine  
   why: researcher-sourced report (researcher > incident database); AIAAIC records the same talk; date 2024-08-08 (kept: same date).
13. **Tracebit's Gemini CLI silent command execution (July 2025)**  
   kept: `036.json` Tracebit, https://tracebit.com/blog/code-exec-deception-gemini-ai-cli-hijack  
   absorbed into also_urls: `009.json` BleepingComputer, https://bleepingcomputer.com/news/security/flaw-in-gemini-cli-ai-coding-assistant-allowed-stealthy-code-execution  
   why: Tracebit's own disclosure over BleepingComputer's report of it; date 2025-07-28 (kept: same date).
14. **Invariant Labs' GitHub MCP toxic agent flow (May 2025)**  
   kept: `003.json` Invariant Labs, https://invariantlabs.ai/blog/mcp-github-vulnerability  
   absorbed into also_urls: `226.json` AI Incident Database, https://incidentdatabase.ai/reports/5264/  
   why: Invariant Labs' own disclosure (researcher > incident database); date 2025-05-26 (kept: same date).
15. **Rules File Backdoor against Cursor and Copilot (March 2025)**  
   kept: `000.json` Pillar Security, https://www.pillar.security/blog/new-vulnerability-in-github-copilot-and-cursor-how-hackers-can-weaponize-code-agents  
   absorbed into also_urls: `227.json` MITRE ATLAS, https://atlas.mitre.org/studies/AML.CS0041  
   why: Pillar Security's own disclosure (researcher > incident database); MITRE ATLAS CS0041 records the same exercise; date 2025-03-18 (kept: same date).
16. **Wiper prompt in the Amazon Q Developer extension (July 2025)**  
   kept: `224.json` AI Incident Database, https://incidentdatabase.ai/cite/1158/  
   absorbed into also_urls: `008.json` 404 Media, https://www.404media.co/hacker-plants-computer-wiping-commands-in-amazons-ai-coding-agent/  
   why: AI Incident Database entry (incident database > press); 404 Media is press; date 2025-07-17 (kept: AIID incident date, the earliest in the cluster).
17. **Nx s1ngularity supply-chain attack on local coding agents (Aug 2025)**  
   kept: `014.json` Wiz, https://www.wiz.io/blog/s1ngularity-supply-chain-attack  
   absorbed into also_urls: `221.json` AI Incident Database, https://incidentdatabase.ai/cite/1210/  
   why: Wiz's investigation (researcher > incident database); date 2025-08-26 (set to the event date 26 August 2025 stated by Wiz; the AIID entry carries 21 August, which precedes the malicious releases).
18. **OpenClaw agent trashed Summer Yue's inbox (Feb 2026)**  
   kept: `247.json` Simon Willison's Weblog, https://simonwillison.net/2026/Feb/23/summer-yue/  
   absorbed into also_urls: `210.json` AI Incident Database, https://incidentdatabase.ai/cite/1542/  
   why: post quoting the deployer's own account (first-party > incident database); date 2026-02-23 (kept: same date).
19. **Moltbook database exposure (Feb 2026)**  
   kept: `022.json` Wiz, https://www.wiz.io/blog/exposed-moltbook-database-reveals-millions-of-api-keys  
   absorbed into also_urls: `246.json` GIGAZINE, https://gigazine.net/gsc_news/en/20260202-moltbook-database-leaked  
   why: Wiz's investigation (researcher > press); GIGAZINE is press; date 2026-02-02 (kept: same date).
20. **OpenAI evaluation agents and the Hugging Face compromise (July 2026)**  
   kept: `093.json` METR, https://metr.org/blog/2026-08-26-openai-hugging-face-incident-investigation/  
   absorbed into also_urls: `199.json` AI Incident Database, https://incidentdatabase.ai/cite/1604/  
   why: METR's independent investigation (researcher > incident database); date 2026-07-11 (set to the AIID incident date 11 July 2026, the earliest in the cluster (METR dates the experiments 26 June to 13 July)).
21. **AI agents sending attack payloads to Library and Archives Canada (2026)**  
   kept: `256.json` Transluce, https://transluce.org/us-canada-gov  
   absorbed into also_urls: `202.json` AI Incident Database, https://incidentdatabase.ai/cite/1731/  
   why: Transluce's own report (researcher > incident database); date 2026-05-28 (set to the AIID incident date 28 May 2026, when the requests were captured).
22. **Claude Haiku 4.5 false police tip and other unintended actions (2026)**  
   kept: `258.json` Anthropic, https://www.anthropic.com/research/investigating-unintended-model-actions  
   absorbed into also_urls: `198.json` AI Incident Database, https://incidentdatabase.ai/cite/1751/  
   why: Anthropic's own disclosure (first-party > incident database); AIID 1751 records one of its cases; date 2026-10-09 (kept: the disclosure date, because the primary source does not date the event (AIID assigns 18 July 2026)).
23. **UK AISI unsanctioned agent actions during cyber testing (July 2026)**  
   kept: `191.json` UK AI Security Institute, https://www.aisi.gov.uk/blog/incident-report-unsanctioned-agent-behaviour-during-cyber-testing  
   absorbed into also_urls: `197.json` AI Incident Database, https://incidentdatabase.ai/cite/1633/  
   why: AISI's own incident report (first-party > incident database); date 2026-07-26 (set to 26 July 2026, the start of the actions per the AIID entry (AISI's monitoring flagged them on 28 July)).

## Dropped items

- `067.json` `2025-03-10-openai-chain-of-thought-monitors-catch-reward-hacking`  
  https://openai.com/index/chain-of-thought-monitoring/  
  verified: false. Page text could not be read on 2026-10-17: openai.com returned HTTP 403 to automated fetches (WebFetch twice, curl once) and the Wayback Machine was offline then blocked (503 on the availability API, 403 on the 2026-10-12 snapshot). Date 2025-03-10, publisher and URL match the paper's grey list entry openai2025detecting (research/grey_v2.json), which the paper team verified against the OpenAI inde
- `098.json` `2025-08-21-commonwealth-bank-reverses-ai-voice-bot-job-cuts-and-admits`  
  https://www.canberratimes.com.au/story/9046323/commonwealth-bank-reverses-ai-chatbot-job-cuts-admits-error/  
  relevant: false. the page describes a customer-service voice bot with no tools, actions or transactions, and the event is a deployer's workforce-assessment error and reversal rather than an agent failure, a control mechanism, or an evaluation of an action-taking agent; classification is provided so the parent can override.
- `107.json` `2025-05-14-uk-governments-consult-tool-analyses-over-2000-consultation`  
  https://www.gov.uk/government/news/government-built-humphrey-ai-tool-reviews-responses-to-consultation-for-first-time-in-bid-to-save-millions  
  relevant: false. Consult is a batch text-analysis tool that assigns themes to written responses and takes no actions through tools, code, browsing or transactions, so it falls outside the stream's agent criterion. Classification kept because the control pattern (parallel human baseline, published accuracy metric, gated rollout, human review of themes under a budget) maps cleanly onto s10_2, s9_1 and s5_6 should an
- `114.json` `2025-08-18-mit-nanda-report-finds-95-of-enterprise-generative-ai-pilots-show`  
  https://fortune.com/2025/08/18/mit-report-95-percent-generative-ai-pilots-at-companies-failing-cfo/  
  relevant: false. the report covers enterprise generative AI pilots in general (generic tools such as ChatGPT); agents that take actions appear only as a forward-looking aside, not as the subject of the findings.
- `167.json` `2025-02-01-oecd-proposes-a-common-reporting-framework-for-ai-incidents-and-hazards`  
  https://read.oecd-ilibrary.org/en/publications/towards-a-common-reporting-framework-for-ai-incidents_f326d4ac-en.html  
  verified: false. Not verified from the source page. The candidate URL and its oecd.org and doi.org mirrors returned HTTP 403 behind a Cloudflare challenge to WebFetch (two attempts) and to curl with browser headers; the Wayback Machine has no snapshot of the URL (availability API empty, /web/2026/ form 404); the web-search budget was exhausted in this run. Existence and current use of the framework were corroborat

## Fixes applied

- `id` regenerated for every item with the collector's `make_id()` (date + ASCII slug, 80 characters at most); 122 ids changed. 48 of the 261 seed ids were longer than 80 characters and most others slugged apostrophes differently from the collector. Nothing referenced the old ids.
- `044.json`: summary: 'with best-in-class security guardrails' -> 'with advanced security guardrails' (marketing phrase)
- `069.json`: summary: 'is not robust to sandbagging' -> 'does not protect against sandbagging' (house style, no 'robust')
- `091.json`: summary: 'a robust measurement' -> 'a reliable measurement' (house style, no 'robust')
- `172.json`: summary: 'outlines state-of-the-art practices' -> 'outlines current best practices' (marketing phrase)
- `189.json`: summary: 'against more robust models particularly likely to transfer to less robust ones' -> 'against more resistant models particularly likely to transfer to less resistant ones' (house style, no 'robust')
- `234.json`: summary: 'with enterprise-grade authentication and authorization' -> 'with authentication and authorization' (marketing phrase)
- `003.json`: kind: research -> disclosure (a researcher's vulnerability disclosure; matches the other researcher disclosures in the set)
- `also_urls` added to SCHEMA.md as an optional stream-item field.

## Validation

Every published item passed: enumerations exact (`kind`, `polarity`, `evidence`, `date_precision`, `domain`, failure sources, requirements, operations); every subsection id exists in `taxonomy.json` (1 to 4 per item, no repeats); every `related_papers` key exists in `papers.json` or `grey.json` (no unknown keys were found, so none had to be dropped); dates and `verified_on` valid and not after 2026-10-17; ids unique and slug-form; URLs unique; summaries of exactly two sentences (three flagged by the splitter were false positives: a quoted sentence in the Claude Code junctions item, "N.D. Cal." in the Workday item, the initial "A." in the Operator groceries item); no marketing vocabulary or em dashes after the six rewrites above.

## Taxonomy consistency

- Every incident and near-miss has at least one failure source and one operation (no adjustments needed).
- Every policy item lists `deploy` or `verify` among its operations (no adjustments needed).
- Every safety-feature item has polarity `good` or `mixed` (no adjustments needed).
- 15 items with polarity `good` carry a non-empty `failure_sources`. They were kept: for a control, a standard or an evaluation that found nothing, the field names the failure source the item addresses, which is what the site's failure-source filter needs. Files: `034`, `063`, `079`, `084`, `088`, `134`, `141`, `166`, `168`, `181`, `184`, `195`, `214`, `219`, `252`.
- Kind for unsanctioned-but-contained actions (UK AISI July 2026 cyber testing kept as `incident` per AISI's own incident report; the Amazon Q wiper and the Library and Archives Canada probes as `near-miss`) follows the kept source's framing; the line between `incident` and `near-miss` is a judgment call for this family and is worth a second look by the authors.
- `evidence` labels follow the sweep: executive statements relayed by press (Klarna, Coinbase, Microsoft, Google code-share figures) are `first-party`; a few researcher disclosures reported by security press are `researcher`. Not changed.

## Known gaps

- Thin domains: healthcare (4), legal (1), finance (9). Only 1 near-miss item remains after merging (three of the four near-miss candidates were further reports of events kept under another kind); the sweep mostly found events after harm, and vendors rarely publish caught-in-time cases. 2024 has 24 items against 133 for 2025 and 74 for 2026 (to 17 October).
- The 2026 series of frontier-lab evaluation agents acting outside their sandboxes is covered by several entries that overlap but document different scopes and were kept apart: the OECD AIM umbrella entry (UK and Australia, more than 100 organisations), AIID 1707 (Australia's Medicare statistics portal), AIID 1668 (DSEWiki coordination), AIID 1629 (Anthropic and Irregular, 9,000 targets), The Decoder on OpenAI's misalignment reports, and the merged METR / AIID 1604 Hugging Face entry. A reader scanning June to October 2026 will see the same storyline from several angles.
- Two candidates could not be verified and were dropped, not rejected: OpenAI's chain-of-thought monitoring post (openai.com returned 403 to fetchers) and the OECD common reporting framework for AI incidents (Cloudflare challenge). Both are worth a manual re-fetch and re-submission.
- Several incident-database items carry editor-assigned dates (AIID infers an incident date when the primary source gives none); the `verification_note` says so in each case.
- The collector's `existing_keys()` in `pipeline/collect_news.py` dedupes on `url`, `title` and `id` only. It should also read `also_urls`, otherwise a feed that carries, for example, the Fortune Replit article would re-add it as a new item.
- Primary sources behind some kept items are paywalled or client-rendered (404 Media, MITRE ATLAS, Business Insider); the notes record how each was confirmed.
- Section 7 (Steering) and section 8 (Training) have few field items (10 items list `steer`, 22 list `train`; 1 and 1 items have their first subsection there) because deployment news rarely reports model-side changes; the collector should weight vendor safety-training posts higher.
