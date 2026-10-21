#!/usr/bin/env python3
"""Classify candidate stream items into the survey taxonomy.

Two classifiers share one output contract (see SCHEMA.md, `stream.json`):

* ``llm_classify_batch``  calls an OpenAI-compatible chat endpoint
  (``$LLM_BASE_URL/chat/completions``, bearer ``$LLM_API_KEY``, model ``$LLM_MODEL``,
  no ``temperature`` parameter) with the survey paragraph and the compact taxonomy,
  and asks for strict JSON per item.
* ``heuristic_classify``  is a keyword classifier used when the gateway is not
  configured, fails, or returns unusable JSON. Its results carry
  ``needs_review: true``.

``classify(items, taxonomy)`` is the public entry point used by collect_news.py.
Each input item is a dict with at least ``title`` and ``url``; ``snippet``,
``publisher``, ``date`` (YYYY-MM-DD), ``evidence`` and ``hints`` are optional.

Standalone use::

    python3 pipeline/classify.py --input candidates.json [--no-llm]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
TAXONOMY_JSON = ROOT / "site" / "data" / "taxonomy.json"
OUTLINE_JSON = Path(
    os.environ.get("OUTLINE_JSON")
    or Path(os.environ.get("PAPER_TOOLING") or ROOT.parent / "ai-control-tooling") / "outline.json"
)

DEFAULT_MODEL = "anthropic/claude-opus-5-5"
LLM_TIMEOUT = 120
LLM_RETRIES = 3

# --------------------------------------------------------------------------- vocabulary

SURVEY_PARAGRAPH = (
    "Deployed AI agents must meet the requirements their deployer places on them: be correct, compliant, "
    "in scope, within budget, and safe. They cannot be trusted to do so on their own. On the attack side "
    "the survey distinguishes three tiers: benign failures (the agent goes out of control with no "
    "attacker present), external attacks (an outsider redirects the agent through what it reads, calls, "
    "or remembers), and insider threats (someone with legitimate partial access contributes to loss of "
    "control, whether a person with access to data, weights, pipeline, credentials, or oversight, or the "
    "model itself). Control is whatever makes the agent's actions meet the requirements without taking "
    "the agent's good intentions on trust. On the defence side the survey separates control outside the "
    "model (Constrain what the agent can do, Observe what it does, Intervene when something is off) from "
    "control inside the model (Steer at inference time, Train before deployment); guarantees come from "
    "outside the model, while measures inside it lower the base rate the outside layer must catch. "
    "Verify tests either side (benchmarks, control evaluations, model auditing). Deployment and Assurance "
    "assembles mechanisms into reference architectures, governance, and safety cases. For every mechanism "
    "the survey records the threat model under which it holds, in particular whether it survives an agent "
    "or insider that actively tries to defeat it, what it costs in safety and usefulness, and what "
    "evidence supports it."
)

KINDS = ["incident", "near-miss", "deployment", "safety-feature", "evaluation", "research", "policy", "disclosure"]
POLARITIES = ["bad", "good", "mixed"]
FAILURE_SOURCES = ["benign", "external", "insider"]   # the three attack tiers; the field keeps its name
REQUIREMENTS = ["correct", "compliant", "in-scope", "within-budget", "safe"]
OPERATIONS = ["constrain", "observe", "intervene", "steer", "train", "verify", "deploy"]
DOMAINS = [
    "coding", "browsing", "customer-service", "finance", "email-and-office", "healthcare", "legal",
    "cyber", "research", "infrastructure", "consumer", "government", "multi-agent", "other",
]
EVIDENCE = ["first-party", "press", "researcher", "regulator", "court", "incident-database"]

# One operation per section; the ids are the section titles (Deployment and Assurance is "deploy").
SECTION_OPERATIONS = {
    "s2": ["failures"], "s4": ["constrain"], "s5": ["observe"], "s6": ["intervene"],
    "s7": ["steer"], "s8": ["train"], "s9": ["verify"], "s10": ["deploy"],
}
OPERATION_SECTION = {o: s for s, ops in SECTION_OPERATIONS.items() for o in ops if o != "failures"}

# Positional ids and titles from outline.json (2026-10-21), kept here so the collector works without
# the paper's tooling repository. pipeline/tests/test_collector.py checks these against site/data/taxonomy.json.
FALLBACK_TAXONOMY = [
    ("s1", 1, "Introduction", ["The Control Problem", "Scope", "Methodology", "Contributions"]),
    ("s2", 2, "How Agents Fail", ["Benign Failures", "Malicious Attacks", "Insider Threats"]),
    ("s3", 3, "Setting", ["Threat Model", "Control Protocols", "Assessment Criteria"]),
    ("s4", 4, "Constrain", ["Confinement", "Formal Enforcement", "Information-Flow Control", "Delegated Authority"]),
    ("s5", 5, "Observe", ["Automated Monitors", "Untrusted Monitors", "Human Oversight"]),
    ("s6", 6, "Intervene", ["Approval Gates", "Resampling", "Shutdown"]),
    ("s7", 7, "Steer", ["Instruction Hierarchies", "Memory Management", "Activation Steering"]),
    ("s8", 8, "Train", ["Safety Fine-Tuning", "Adversarial Training", "Representation-Level Methods"]),
    ("s9", 9, "Verify", ["Benchmarks", "Control Evaluations", "Model Auditing"]),
    ("s10", 10, "Deployment and Assurance", ["Reference Architectures", "Governance", "Safety Cases"]),
    ("s11", 11, "Open Problems", ["Gaps by Failure Tier", "Cost and Organisational Constraints", "Conclusion"]),
]


# --------------------------------------------------------------------------- taxonomy loading

def _tax_from_sections(sections):
    out = {"sections": [], "subsection_ids": set(), "subsection_titles": {}}
    for s in sections:
        sec = {
            "id": s["id"], "number": s.get("number"), "title": s["title"],
            "operations": list(s.get("operations") or ([s["operation"]] if s.get("operation") else SECTION_OPERATIONS.get(s["id"], []))),
            "subsections": [],
        }
        for ss in s.get("subsections", []):
            sub = {"id": ss["id"], "number": ss.get("number"), "title": ss["title"]}
            sec["subsections"].append(sub)
            out["subsection_ids"].add(ss["id"])
            out["subsection_titles"][ss["id"]] = ss["title"]
        out["sections"].append(sec)
    return out


def load_taxonomy(path: Path | None = None) -> dict:
    """Load the taxonomy from site/data/taxonomy.json, else outline.json, else the built-in copy."""
    candidates = [path] if path else [TAXONOMY_JSON]
    for p in candidates:
        if p and Path(p).exists():
            try:
                data = json.loads(Path(p).read_text(encoding="utf-8"))
                tax = _tax_from_sections(data["sections"])
                tax["source"] = str(p)
                tax["generated"] = data.get("generated")
                tax["structure"] = data.get("structure")
                if tax["subsection_ids"]:
                    return tax
            except (OSError, ValueError, KeyError, TypeError):
                pass
    if OUTLINE_JSON.exists():
        try:
            data = json.loads(OUTLINE_JSON.read_text(encoding="utf-8"))
            sections = []
            for s in data["sections"]:
                k = int(s["number"])
                sections.append({
                    "id": f"s{k}", "number": k, "title": s["title"],
                    "subsections": [
                        {"id": f"s{k}_{j}", "number": f"{k}.{j}", "title": ss["title"]}
                        for j, ss in enumerate(s.get("subsections", []), 1)
                    ],
                })
            tax = _tax_from_sections(sections)
            tax["source"] = str(OUTLINE_JSON)
            tax["generated"] = None
            tax["structure"] = None
            return tax
        except (OSError, ValueError, KeyError, TypeError):
            pass
    sections = []
    for sid, k, title, subs in FALLBACK_TAXONOMY:
        sections.append({
            "id": sid, "number": k, "title": title,
            "subsections": [{"id": f"{sid}_{j}", "number": f"{k}.{j}", "title": t} for j, t in enumerate(subs, 1)],
        })
    tax = _tax_from_sections(sections)
    tax["source"] = "built-in"
    tax["generated"] = None
    tax["structure"] = None
    return tax


def compact_taxonomy(tax: dict) -> str:
    lines = []
    for s in tax["sections"]:
        ops = s.get("operations") or []
        head = f"{s['id']} {s['title']}" + (f" [operations: {', '.join(ops)}]" if ops else "")
        subs = "; ".join(f"{ss['id']} {ss['title']}" for ss in s["subsections"])
        lines.append(f"{head}: {subs}")
    return "\n".join(lines)


# --------------------------------------------------------------------------- helpers

def _text(item: dict) -> str:
    return " ".join(str(item.get(k) or "") for k in ("title", "snippet", "summary")).lower()


def _has(text: str, *patterns: str) -> bool:
    return any(re.search(p, text, re.I) for p in patterns)


def _uniq(seq):
    seen, out = set(), []
    for x in seq:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def two_sentences(text: str, fallback: str = "") -> str:
    text = re.sub(r"\s+", " ", (text or "").strip())
    if not text:
        return fallback
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(])", text)
    out = " ".join(parts[:2]).strip()
    if len(out) > 420:
        out = out[:417].rsplit(" ", 1)[0] + "..."
    if out and out[-1] not in ".!?":
        out += "."
    return out


# --------------------------------------------------------------------------- heuristic classifier

AI_TERMS = (
    r"\bai\b", r"\ba\.i\.", r"artificial intelligence", r"\bllms?\b", r"language models?", r"\bagents?\b", r"agentic",
    r"chatbot", r"copilot", r"\bgpt", r"chatgpt", r"claude", r"gemini", r"openai", r"anthropic", r"deepmind",
    r"model context protocol", r"\bmcp\b", r"prompt injection", r"jailbreak", r"\bassistants?\b", r"autonomous",
    r"\bbot\b", r"\bbots\b", r"codex", r"cursor\b", r"replit", r"devin\b",
)
AGENT_TERMS = (
    r"\bagents?\b", r"agentic", r"copilot", r"autonomous", r"tool[- ]use", r"tool[- ]calling", r"computer[- ]use",
    r"browser agent", r"coding agent", r"\bmcp\b", r"model context protocol", r"operator\b", r"codex", r"claude code",
    r"\bassistant", r"chatbot", r"\bbot\b", r"workflow automation", r"\bai system",
    r"\bmodels? (?:hacked|breached|exploited|autonomously|took|performed|executed|deleted|sent|submitted)",
)
DEPLOY_TERMS = (
    r"deploy", r"production", r"rolled? out", r"launch", r"ships?\b", r"shipped", r"now available", r"customers?",
    r"enterprise", r"in the wild", r"real[- ]world", r"incident", r"outage", r"breach", r"leak", r"deleted",
    r"exploit", r"vulnerab", r"attack", r"injection", r"lawsuit", r"regulat", r"fine[ds]?\b", r"guardrail",
    r"sandbox", r"permission", r"monitor", r"audit", r"red[- ]team", r"evaluation", r"benchmark", r"system card",
    r"postmortem", r"advisory", r"cve-", r"patch", r"policy", r"\bact\b", r"\blaw\b", r"safety",
)
BAD_TERMS = (
    r"breach", r"leak", r"deleted", r"wiped", r"destroy", r"hack", r"exploit", r"vulnerab", r"malicious", r"attack",
    r"injection", r"poison", r"jailbr", r"lawsuit", r"sued", r"fined?\b", r"penalt", r"fail", r"outage", r"hallucinat",
    r"rogue", r"went wrong", r"mistake", r"error", r"bug\b", r"scam", r"fraud", r"abuse", r"misuse", r"harm",
    r"unauthori[sz]ed", r"exfiltrat", r"compromis", r"backdoor", r"ransom", r"sabotag", r"decepti", r"scheming",
    r"blackmail", r"resist", r"shutdown", r"loss of control", r"recall", r"ban\b", r"banned", r"warn",
)
GOOD_TERMS = (
    r"launch", r"introduc", r"announc", r"ships?\b", r"shipped", r"rolls? out", r"now available", r"new feature",
    r"guardrail", r"protection", r"mitigat", r"defen[cs]e", r"sandbox", r"permission", r"approval", r"isolation",
    r"monitor", r"audit", r"certif", r"passes", r"improv", r"safer", r"safety case", r"framework", r"standard",
    r"guidance", r"best practice", r"success", r"saves", r"adopt",
)
SEVERE_TERMS = (
    r"deleted", r"wiped", r"destroy", r"breach", r"leak", r"hack", r"exploit", r"lawsuit", r"\bfined\b", r"outage",
    r"exfiltrat", r"compromis", r"blackmail", r"went rogue", r"stole", r"stolen", r"drained", r"unauthori[sz]ed",
)
KIND_RULES = [
    ("policy", (r"\bregulat", r"\blaw\b", r"\bbill\b", r"\bact\b", r"lawsuit", r"\bcourt", r"\bjudge\b", r"\bfine[ds]?\b",
                r"regulator", r"standard\b", r"compliance", r"executive order", r"legislat", r"\bban\b", r"enforcement",
                r"commission", r"parliament", r"congress", r"senate", r"ftc\b", r"\beu\b", r"nist\b")),
    ("disclosure", (r"\bcve-\d", r"advisory", r"postmortem", r"post-mortem", r"patched", r"vulnerability disclos",
                    r"security update", r"disclosed", r"bug bounty", r"responsible disclosure", r"incident report")),
    ("evaluation", (r"benchmark", r"evaluat", r"red[- ]team", r"system card", r"model card", r"study finds",
                    r"audit", r"assessment", r"capabilit(?:y|ies) (?:eval|test|report)")),
    ("research", (r"\barxiv\b", r"\bpaper\b", r"we propose", r"we present", r"we introduce", r"we study", r"framework for",
                  r"preprint", r"survey\b")),
    ("safety-feature", (r"guardrail", r"permission", r"sandbox", r"approval", r"isolation", r"kill switch", r"safeguard",
                        r"protection", r"content filter", r"allowlist", r"least privilege", r"human[- ]in[- ]the[- ]loop",
                        r"monitoring", r"new safety", r"safety feature", r"classifier", r"rollback", r"audit log")),
    ("near-miss", (r"caught", r"blocked", r"prevented", r"stopped before", r"near[- ]miss", r"averted", r"flagged",
                   r"intercepted", r"detected before")),
    ("incident", BAD_TERMS),
    ("deployment", (r"deploy", r"rolls? out", r"launch", r"now available", r"customers", r"in production", r"adopt",
                    r"introduc", r"announc", r"ships?\b", r"releas", r"available to")),
]
FAILURE_RULES = {
    # external: an outsider redirects the agent through what it reads, calls, or remembers
    "external": (r"prompt injection", r"injection", r"poison", r"jailbr", r"manipulat", r"hijack", r"malicious (?:instruction|prompt|content|email|document|website|link|page)",
                 r"indirect prompt", r"untrusted (?:content|input|data)", r"social engineer", r"exfiltrat", r"zero-click", r"\brce\b",
                 r"supply[- ]chain", r"compromised (?:tool|server|plugin|extension|dependency|package)"),
    # insider: a person with legitimate partial access, or the model itself pursuing objectives of its own
    "insider": (r"decepti", r"scheming", r"sabotag", r"reward hack", r"specification gaming", r"resist(?:s|ed|ing)? (?:shutdown|oversight)",
                r"self-preserv", r"blackmail", r"misalign", r"alignment faking", r"sandbagg", r"power[- ]seeking", r"loss of control",
                r"hidden objective", r"collu", r"disobey", r"ignored? (?:instructions|the stop)", r"tamper",
                r"\binsiders?\b", r"rogue (?:employee|engineer|developer|contractor|admin)", r"disgruntled",
                r"(?:stole|stolen|theft of|exfiltrat\w+) (?:the )?(?:model )?weights", r"weight (?:theft|exfiltration)",
                r"abus\w+ (?:their|his|her) (?:privileged |admin )?access", r"backdoor"),
    # benign: the agent goes out of control with no attacker present
    "benign": (r"mistake", r"error", r"bug\b", r"hallucinat", r"deleted", r"wiped", r"wrong", r"incorrect", r"misread", r"misunderst",
               r"accident", r"unintend", r"fabricat", r"made up", r"misfire", r"went rogue", r"loop", r"runaway", r"overspen", r"cost"),
}
OPERATION_RULES = {
    "constrain": (r"sandbox", r"isolat", r"permission", r"least privilege", r"allowlist", r"whitelist", r"scope[ds]? (?:token|credential)",
                  r"credential", r"oauth", r"identity", r"access control", r"capabilit(?:y|ies) restrict", r"information[- ]flow",
                  r"taint", r"container", r"read-only", r"restrict"),
    "observe": (r"monitor", r"logging", r"\blogs?\b", r"observab", r"detect", r"guardrail", r"classifier", r"provenance", r"telemetry",
                r"audit log", r"chain[- ]of[- ]thought", r"probe", r"flagged", r"human review", r"oversight"),
    "intervene": (r"approval", r"confirm", r"block", r"blocked", r"rollback", r"roll back", r"revert", r"kill switch", r"shut ?down",
                  r"pause", r"halt", r"stopped", r"intercept", r"quarantine", r"human[- ]in[- ]the[- ]loop", r"undo", r"fallback"),
    "steer": (r"system prompt", r"instruction hierarch", r"steering", r"prompting", r"context engineering", r"preference", r"activation"),
    "train": (r"fine[- ]tun", r"rlhf", r"training", r"trained to", r"post-training", r"safety training", r"adversarial training",
              r"unlearn", r"constitution"),
    "verify": (r"evaluat", r"benchmark", r"red[- ]team", r"audit", r"test(?:ed|ing|s)?\b", r"system card", r"assessment", r"control evaluation",
               r"pentest", r"capability", r"measur", r"study"),
    "deploy": (r"regulat", r"\blaw\b", r"policy", r"\bact\b", r"standard", r"safety case", r"framework", r"governance", r"certif",
               r"incident report", r"disclosure", r"postmortem", r"release", r"assurance", r"third[- ]party", r"compliance", r"architecture"),
}
SUBSECTION_RULES = [
    # most specific first; (subsection id, patterns); ids of outline.json 2026-10-21 (11 sections, 35 subsections)
    # 2.2 Malicious Attacks: an outsider redirects the agent through what it reads, calls, or remembers
    ("s2_2", (r"prompt injection", r"indirect prompt", r"memory poison", r"poison", r"zero-click", r"malicious (?:email|document|website|page|content|instruction)", r"tool poisoning",
            r"supply[- ]chain", r"compromised (?:tool|server|plugin|extension|dependency|package)")),
    # 2.3 Insider Threats: a person with legitimate partial access, the model itself as the limiting case, and agents
    # colluding or drifting through delegation
    ("s2_3", (r"multi-?agent", r"agent swarm", r"agents? (?:collud|talking|negotiat|coordinat)", r"collu", r"steganograph", r"covert (?:channel|communication|signal)",
            r"agent-to-agent", r"\ba2a\b", r"delegation chain", r"orchestrat\w+ (?:agents|pipeline)", r"team of agents", r"fleet of agents", r"\binsiders?\b", r"rogue (?:employee|engineer|developer|contractor|admin)",
            r"disgruntled", r"\bemployee\b.*(?:stole|leak|exfiltrat|sabotag|misus)", r"(?:stole|stolen|theft of|exfiltrat\w+) (?:the )?(?:model )?weights", r"weight (?:theft|exfiltration)",
            r"credential (?:theft|abuse|misuse)", r"abus\w+ (?:their|his|her) (?:privileged |admin )?access", r"backdoor(?:ed)? (?:the )?model", r"planted a backdoor",
            r"poison\w* (?:the )?training data by", r"reward hack", r"harness", r"specification gaming", r"gamed the", r"tamper", r"sandbagg", r"decepti", r"scheming",
            r"blackmail", r"resist(?:s|ed|ing)? (?:shutdown|oversight)", r"self-preserv", r"alignment faking", r"loss of control", r"power[- ]seeking", r"sabotag")),
    # 2.1 Benign Failures: no attacker present
    ("s2_1", (r"deleted", r"wiped", r"destroy", r"hallucinat", r"wrong", r"mistake", r"error", r"compound", r"went rogue", r"runaway", r"loop", r"fabricat", r"made up",
            r"incorrect")),
    # 4.4 Delegated Authority: identity, credentials, delegation, egress
    ("s4_4", (r"credential", r"oauth", r"identity", r"token(?:s)? (?:leak|stolen|exposed|scoped)", r"delegat", r"api key", r"secrets?\b", r"authenticat", r"non-human identit",
            r"egress")),
    # 4.3 Information-Flow Control
    ("s4_3", (r"information[- ]flow", r"exfiltrat", r"data leak", r"taint", r"\bdlp\b", r"leaked? (?:data|files|secrets)", r"markdown image", r"render(?:ed|ing)? (?:links|images)",
            r"capabilit(?:y|ies)[- ]based")),
    # 4.2 Formal Enforcement: schemas, typed tool calls, verified actions
    ("s4_2", (r"formal", r"policy language", r"schema", r"typed (?:action|tool)", r"structured action", r"verified action", r"constraint language", r"constrained decoding",
            r"grammar")),
    # 4.1 Confinement: least privilege, permissions, sandboxing, isolation
    ("s4_1", (r"sandbox", r"isolat", r"container", r"virtual machine", r"\bvm\b", r"browser isolation", r"ephemeral", r"least privilege", r"permission", r"allowlist",
            r"whitelist", r"access control", r"scope[ds]?\b", r"read-only", r"restrict(?:ed|s)? (?:tools|actions|access)", r"privilege")),
    # 5.1 Automated Monitors: guardrails, action and output classifiers, chain-of-thought monitors, probes, logging and provenance
    ("s5_1", (r"chain[- ]of[- ]thought", r"reasoning trace", r"\bcot\b", r"thinking tokens", r"activation probe", r"\bprobes?\b", r"linear probe", r"internal(?:s)? (?:of|detect)",
            r"guardrail", r"action monitor", r"classifier", r"content filter", r"real[- ]time (?:detect|block|monitor)", r"input filter", r"output filter", r"firewall",
            r"logging", r"\blogs?\b", r"provenance", r"audit trail", r"telemetry", r"observab", r"trace(?:s|ability)")),
    # 5.2 Untrusted Monitors: monitors as attack surfaces, collusion
    ("s5_2", (r"trusted monitor", r"untrusted monitor", r"monitor(?:ing)? (?:model|the agent)", r"\bmonitor\b", r"anti-collusion", r"paraphras")),
    # 5.3 Human Oversight
    ("s5_3", (r"human review", r"human oversight", r"review budget", r"escalat", r"reviewers?\b", r"human[- ]in[- ]the[- ]loop", r"automation bias")),
    # 6.1 Approval Gates: approve, clarify, block, edit, defer
    ("s6_1", (r"approval", r"confirm(?:ation)? (?:step|prompt|before)", r"ask(?:s|ed)? (?:for )?permission", r"consent", r"require(?:s|d)? (?:user )?approval", r"human[- ]in[- ]the[- ]loop",
            r"block(?:ed|s|ing)?\b", r"intercept", r"quarantin", r"defer", r"edit(?:ed|s)? the action", r"refus", r"deny", r"denied")),
    # 6.3 Shutdown: kill switches, interruptibility, fallback, rollback, recovery
    ("s6_3", (r"kill switch", r"shut ?down", r"shutdown", r"halt", r"pause[ds]?\b", r"disable[ds]?\b", r"fallback", r"off switch", r"suspend", r"interrupt", r"rollback",
            r"roll back", r"revert", r"undo", r"restor", r"backup", r"reversib", r"recover")),
    # 6.2 Resampling
    ("s6_2", (r"resampl", r"incriminat", r"re-?run", r"second opinion")),
    # 7.3 Activation Steering: steering vectors, activation patching
    ("s7_3", (r"activation steering", r"steering vector", r"activation patching", r"\bactivations?\b", r"steer(?:ing|ed)? (?:the )?model")),
    # 7.2 Memory Management: long-term memory, personalised context, memory authorisation
    ("s7_2", (r"memory\b", r"memories", r"context", r"preference", r"persona", r"in-context", r"personali[sz]", r"long-term", r"remember")),
    # 7.1 Instruction Hierarchies: system and policy prompts, plan-then-execute, self-correction, interpretability as a control instrument
    ("s7_1", (r"system prompt", r"instruction hierarch", r"prompt design", r"instructions?\b", r"spec\b", r"model spec", r"policy prompt", r"self-correct", r"planning",
            r"reflection", r"plan(?:s|ning)? (?:before|ahead)", r"plan-then-execute", r"verif(?:y|ies) its own", r"mechanistic", r"interpretab", r"circuit\b",
            r"feature(?:s)? (?:found|discover)")),
    # 8.2 Adversarial Training
    ("s8_2", (r"adversarial training", r"robustness training", r"trained against", r"anti-scheming", r"jailbreak training", r"tamper-resist",
            r"adversarial(?:ly)? (?:train|fine)")),
    # 8.3 Representation-Level Methods: circuit breakers, representation rerouting, unlearning, weight editing
    ("s8_3", (r"unlearn", r"representation (?:training|rerouting|engineering)", r"circuit breaker", r"weight editing", r"model editing", r"representation[- ]level")),
    # 8.1 Safety Fine-Tuning and its durability
    ("s8_1", (r"rlhf", r"preference training", r"dpo\b", r"supervised fine", r"sft\b", r"reward model", r"safety training", r"post-training", r"constitution",
            r"refusal training", r"trained to refuse", r"alignment training", r"fine[- ]tun", r"training", r"deliberative", r"reasoning[- ]based safety",
            r"safety reasoning", r"chain-of-thought training", r"scalable oversight", r"pretraining data", r"data curation", r"safety retention",
            r"fine-tuning (?:removes|undoes|breaks)", r"safety degrad")),
    # 9.2 Control Evaluations and their settings
    ("s9_2", (r"control evaluation", r"control protocol", r"untrusted model", r"trusted editing", r"ai control", r"control setting", r"testbed", r"environment(?:s)? for",
            r"simulat")),
    # 9.3 Model Auditing: white-box audits, auditing games, model diffing
    ("s9_3", (r"white-box", r"audit(?:ing)? the model", r"interpretability audit", r"model internals", r"hidden objective", r"auditing game", r"model diffing")),
    # 9.1 Benchmarks, metrics and reporting
    ("s9_1", (r"injection (?:benchmark|eval|test)", r"red[- ]team", r"jailbreak (?:benchmark|eval|test|rate)", r"attack success", r"adversarial (?:eval|test|robust)",
            r"pentest", r"penetration test", r"ctf\b", r"benchmark", r"evaluat", r"system card", r"model card", r"capabilit", r"test(?:ed|ing|s)?\b", r"study", r"measur",
            r"reliab", r"statistic", r"confidence interval", r"reporting", r"metric", r"pass@", r"success rate", r"variance")),
    # 10.3 Safety Cases: frontier safety frameworks, regulation, independent assurance
    ("s10_3", (r"regulat", r"\blaw\b", r"\bbill\b", r"\bact\b", r"legislat", r"executive order", r"lawsuit", r"\bcourt", r"\bfine[ds]?\b", r"ftc\b", r"\beu\b",
            r"ban(?:ned|s)?\b", r"compliance", r"enforcement", r"treaty", r"standard", r"safety case", r"risk assessment", r"frontier safety framework", r"preparedness",
            r"responsible scaling", r"safety framework", r"third[- ]party", r"independent (?:audit|assur|evaluat|test)", r"external (?:audit|evaluat|test)", r"certif",
            r"accredit", r"assurance")),
    # 10.2 Governance: release gates, incident reporting and response
    ("s10_2", (r"incident report", r"incident response", r"postmortem", r"post-mortem", r"release gate", r"staged rollout", r"disclos", r"advisory", r"cve-", r"patch",
            r"recall", r"lessons learned", r"feedback", r"governance", r"change (?:review|management|control)", r"versioned", r"regression (?:eval|test)")),
    # 10.1 Reference Architectures
    ("s10_1", (r"reference architecture", r"defen[cs]e in depth", r"architecture", r"security stack", r"blueprint", r"design pattern", r"best practice", r"guidance", r"playbook",
            r"framework", r"control stack", r"layered defen[cs]e")),
    # 3.1 Threat Model: the deployment setting
    ("s3_1", (r"deploy", r"production", r"rolls? out", r"launch", r"enterprise", r"customers", r"adopt", r"in use", r"agents? (?:for|that|to)\b")),
]
DOMAIN_RULES = [
    ("coding", (r"\bcode\b", r"coding", r"github", r"copilot", r"cursor\b", r"replit", r"\bide\b", r"repositor", r"pull request", r"developer", r"software engineer", r"claude code", r"codex", r"devin\b", r"npm\b", r"pypi", r"package", r"\bci\b", r"devops")),
    ("browsing", (r"browser", r"web agent", r"\boperator\b", r"comet\b", r"browsing", r"web page", r"website", r"navigat", r"atlas\b", r"shopping agent", r"web search")),
    ("email-and-office", (r"email", r"e-mail", r"gmail", r"outlook", r"calendar", r"office 365", r"microsoft 365", r"copilot studio", r"slack", r"notion", r"google (?:docs|drive|workspace)", r"spreadsheet", r"documents?\b", r"inbox")),
    ("customer-service", (r"customer (?:service|support|care)", r"support (?:bot|agent|chat)", r"help ?desk", r"call cent", r"chatbot", r"contact cent", r"customer-facing", r"refund")),
    ("finance", (r"bank", r"trading", r"payment", r"crypto", r"wallet", r"fintech", r"invest", r"financial", r"insurance", r"loan", r"stock", r"treasury", r"accounting", r"invoice", r"fraud")),
    ("healthcare", (r"health", r"hospital", r"medical", r"clinic", r"patient", r"\bfda\b", r"pharma", r"diagnos", r"therap")),
    ("legal", (r"\blegal\b", r"law firm", r"attorney", r"lawyer", r"court filing", r"\bcourt\b", r"litigat", r"contract review", r"hallucinated cases", r"fake citations")),
    ("cyber", (r"malware", r"ransomware", r"pentest", r"penetration", r"cyberattack", r"hacker", r"threat actor", r"\bcve-", r"vulnerab", r"exploit", r"phishing", r"security researcher", r"zero-day", r"offensive", r"\bsoc\b", r"intrusion", r"espionage", r"cyber")),
    ("infrastructure", (r"cloud", r"kubernetes", r"\baws\b", r"azure", r"gcp\b", r"database", r"server", r"infrastructure", r"data cent", r"terraform", r"\bsre\b", r"production (?:system|database|environment)", r"\bapi\b", r"\bmcp server")),
    ("government", (r"government", r"federal", r"agency", r"public sector", r"military", r"defen[cs]e department", r"pentagon", r"\bdod\b", r"\bgsa\b", r"ministry", r"municipal", r"welfare", r"benefits system", r"immigration", r"police")),
    ("research", (r"\bresearch\b", r"scientif", r"laborator", r"experiment", r"academ", r"universit", r"paper\b", r"arxiv", r"benchmark", r"study")),
    ("multi-agent", (r"multi-agent", r"multiagent", r"agent swarm", r"agents? (?:talking|collud|negotiat)", r"orchestrat", r"agent-to-agent", r"\ba2a\b", r"team of agents", r"fleet of agents")),
    ("consumer", (r"smartphone", r"\bsiri\b", r"alexa", r"consumer", r"\bapp\b", r"users?\b", r"personal assistant", r"companion", r"teen", r"children", r"kids", r"social media", r"instagram", r"tiktok", r"\bmeta\b", r"whatsapp", r"character\.ai")),
]
REQUIREMENT_RULES = {
    "safe": (r"harm", r"safety", r"dangerous", r"injur", r"death", r"suicide", r"weapon", r"bio", r"child", r"violence", r"physical", r"unsafe", r"risk"),
    "compliant": (r"regulat", r"\blaw\b", r"policy", r"violat", r"compliance", r"gdpr", r"privacy", r"consent", r"terms of service", r"licen[cs]", r"copyright", r"legal", r"\bban\b", r"rule"),
    "in-scope": (r"unauthori[sz]ed", r"beyond", r"outside", r"scope", r"deleted", r"destructive", r"without permission", r"without asking", r"not asked", r"exfiltrat", r"leak", r"went rogue", r"escalat", r"overreach", r"did not have permission"),
    "correct": (r"wrong", r"error", r"hallucinat", r"incorrect", r"bug\b", r"fabricat", r"made up", r"inaccura", r"mistake", r"fake", r"false", r"misinform", r"quality", r"reliab", r"accura"),
    "within-budget": (r"\bcost", r"spend", r"spent", r"tokens?\b", r"\$[0-9]", r"bill(?:ed|ing)?\b", r"budget", r"infinite loop", r"runaway", r"compute", r"expensive", r"latency", r"quota", r"rate limit"),
}


NEGATIVE_TERMS = (
    r"deepfake", r"deep fake", r"voice[- ]clon", r"face[- ]swap", r"ai[- ]generated (?:image|art|essay|novel|book|music|video|song|photo|paper)",
    r"literary", r"prize", r"plagiar", r"nudif", r"undress", r"synthetic (?:image|media|voice)", r"\bimage generator", r"text-to-image",
    r"ai slop", r"ai art", r"chatbot (?:companion|girlfriend|boyfriend)", r"funding round", r"raises \$", r"valuation", r"\bipo\b",
)


def mostly_latin(title: str) -> bool:
    letters = [c for c in (title or "") if c.isalpha()]
    if not letters:
        return True
    return sum(1 for c in letters if c.isascii()) / len(letters) >= 0.6


def heuristic_relevant(item: dict, weight: float = 0.5) -> tuple[bool, float]:
    text = _text(item)
    ai = _has(text, *AI_TERMS)
    agent = _has(text, *AGENT_TERMS)
    deploy = _has(text, *DEPLOY_TERMS)
    if item.get("hints"):            # reader submissions are relevant by construction
        return True, 0.7
    if not mostly_latin(item.get("title") or ""):
        return False, 0.1            # the heuristic cannot read it; the LLM path decides for itself
    if _has(text, *NEGATIVE_TERMS) and not agent:
        return False, 0.2
    if weight >= 0.9:
        return ai, 0.55 if ai else 0.2
    if agent and deploy:
        return True, min(0.6, 0.3 + weight / 2)
    if ai and deploy and _has(text, r"agent", r"copilot", r"autonomous", r"assistant", r"\bbot", r"\bmcp\b", r"tool"):
        return True, min(0.5, 0.25 + weight / 2)
    return False, 0.15


def heuristic_classify(item: dict, tax: dict, weight: float = 0.5) -> dict:
    """Keyword classifier. Always sets needs_review=True."""
    text = _text(item)
    hints = item.get("hints") or {}
    relevant, conf = heuristic_relevant(item, weight)

    bad = sum(1 for p in BAD_TERMS if re.search(p, text, re.I))
    good = sum(1 for p in GOOD_TERMS if re.search(p, text, re.I))
    severe = _has(text, *SEVERE_TERMS)
    caught = _has(text, r"caught", r"blocked", r"prevented", r"stopped before", r"near[- ]miss", r"averted", r"intercepted")
    polarity = hints.get("polarity")
    if polarity not in POLARITIES:
        if severe:
            polarity = "mixed" if good > bad + 2 else "bad"
        elif bad and good and abs(bad - good) <= 1:
            polarity = "mixed"
        elif bad > good:
            polarity = "bad"
        elif good:
            polarity = "good"
        else:
            polarity = "mixed"

    kind = hints.get("kind")
    if kind not in KINDS:
        kind = None
        src = (item.get("publisher") or "").lower()
        if "arxiv" in src or "arxiv.org" in (item.get("url") or ""):
            kind = "research"
        elif severe and not _has(text, r"\bcve-\d", r"advisory", r"postmortem", r"post-mortem", r"patched"):
            kind = "near-miss" if caught else "incident"
        else:
            for k, pats in KIND_RULES:
                if _has(text, *pats):
                    kind = k
                    break
        if kind is None:
            kind = "deployment" if polarity == "good" else "incident"
        if kind == "incident" and polarity == "good":
            kind = "safety-feature" if _has(text, r"guardrail", r"sandbox", r"permission", r"approval", r"monitor", r"protection") else "deployment"
        if kind == "deployment" and polarity == "bad" and bad >= 2:
            kind = "incident"

    failure_sources = [f for f in (hints.get("failure_sources") or []) if f in FAILURE_SOURCES]
    if not failure_sources:
        for f, pats in FAILURE_RULES.items():
            if _has(text, *pats):
                failure_sources.append(f)
        if polarity == "good" and kind in ("deployment", "safety-feature", "policy") and not _has(text, r"against", r"prevent", r"protect", r"mitigat", r"defen"):
            failure_sources = []
        if kind in ("incident", "near-miss") and not failure_sources:
            failure_sources = ["benign"]
    failure_sources = _uniq(failure_sources)[:3]

    operations = [o for o in (hints.get("operations") or []) if o in OPERATIONS]
    if not operations:
        scored = []
        for o, pats in OPERATION_RULES.items():
            n = sum(1 for p in pats if re.search(p, text, re.I))
            if n:
                scored.append((n, o))
        scored.sort(reverse=True)
        operations = [o for _, o in scored[:3]]
        if not operations:
            operations = {"policy": ["deploy"], "disclosure": ["deploy", "observe"], "evaluation": ["verify"],
                          "research": ["verify"], "safety-feature": ["constrain"], "incident": ["constrain", "observe"],
                          "near-miss": ["observe", "intervene"], "deployment": ["deploy"]}.get(kind, ["deploy"])
    operations = _uniq(operations)[:4]

    subsections = [s for s in (hints.get("subsections") or []) if s in tax["subsection_ids"]]
    if not subsections:
        hits = []
        for sid, pats in SUBSECTION_RULES:
            n = sum(1 for p in pats if re.search(p, text, re.I))
            if n and sid in tax["subsection_ids"]:
                hits.append((n, sid))
        # prefer subsections whose section matches a detected operation / failure source
        pref = {OPERATION_SECTION[o] for o in operations if o in OPERATION_SECTION}
        if failure_sources:
            pref.add("s2")
        hits.sort(key=lambda t: (-(t[0] + (1 if t[1].split("_")[0] in pref else 0)), SUBSECTION_RULES_INDEX[t[1]]))
        subsections = [sid for _, sid in hits[:4]]
        fs_default = {"external": "s2_2", "insider": "s2_3", "benign": "s2_1"}
        for f in failure_sources:
            if fs_default[f] in tax["subsection_ids"] and fs_default[f] not in subsections:
                subsections.append(fs_default[f])
        subsections = subsections[:4]
        if not subsections:
            subsections = ["s3_1"] if "s3_1" in tax["subsection_ids"] else [sorted(tax["subsection_ids"])[0]]
    subsections = _uniq(subsections)[:4]

    requirements = [r for r in (hints.get("requirements") or []) if r in REQUIREMENTS]
    if not requirements:
        for r, pats in REQUIREMENT_RULES.items():
            if _has(text, *pats):
                requirements.append(r)
        if not requirements:
            requirements = ["safe"] if polarity == "bad" else (["compliant"] if kind == "policy" else ["safe"])
    requirements = _uniq(requirements)[:4]

    domain = hints.get("domain") if hints.get("domain") in DOMAINS else None
    if not domain:
        best, best_n = "other", 0
        for d, pats in DOMAIN_RULES:
            n = sum(1 for p in pats if re.search(p, text, re.I))
            if n > best_n:
                best, best_n = d, n
        domain = best

    evidence = item.get("evidence") if item.get("evidence") in EVIDENCE else None
    if not evidence:
        src = (item.get("publisher") or "").lower()
        if "incident database" in src:
            evidence = "incident-database"
        elif _has(text, r"\bcourt\b", r"ruling", r"judge", r"lawsuit"):
            evidence = "court"
        elif _has(src, r"nist", r"cisa", r"eu ai act", r"commission", r"regulator", r"ofcom", r"ico\b"):
            evidence = "regulator"
        elif _has(src, r"arxiv", r"research", r"metr", r"redwood", r"palisade", r"forum", r"lesswrong", r"owasp", r"schneier", r"willison", r"import ai"):
            evidence = "researcher"
        elif _has(src, r"openai", r"anthropic", r"google", r"deepmind", r"microsoft", r"github", r"cloudflare", r"meta\b", r"amazon"):
            evidence = "first-party"
        else:
            evidence = "press"

    tags = []
    for pat, tag in TAG_RULES:
        if re.search(pat, text, re.I):
            tags.append(tag)
    tags = _uniq(tags)[:5]

    summary = two_sentences(item.get("snippet") or "", fallback=two_sentences(item.get("title") or ""))

    return {
        "relevant": relevant,
        "confidence": round(conf, 2),
        "kind": kind,
        "polarity": polarity,
        "summary": summary,
        "failure_sources": failure_sources,
        "requirements": requirements,
        "operations": operations,
        "subsections": subsections,
        "domain": domain,
        "evidence": evidence,
        "actors": {"vendor": None, "deployer": None, "model": None},
        "tags": tags,
        "date": item.get("url_date") or None,
        "needs_review": True,
        "classifier": "heuristic",
    }


SUBSECTION_RULES_INDEX = {sid: i for i, (sid, _) in enumerate(SUBSECTION_RULES)}
TAG_RULES = [
    (r"prompt injection", "prompt injection"), (r"memory poison", "memory poisoning"), (r"jailbr", "jailbreak"),
    (r"exfiltrat|data leak|leaked", "data exfiltration"), (r"deleted|wiped|destroy", "destructive action"),
    (r"rollback|roll back|revert", "rollback"), (r"sandbox", "sandbox"), (r"permission|least privilege", "permissions"),
    (r"approval|human[- ]in[- ]the[- ]loop", "approval gate"), (r"monitor", "monitoring"), (r"\bmcp\b|model context protocol", "mcp"),
    (r"browser", "browser agent"), (r"coding agent|copilot|claude code|codex|cursor", "coding agent"),
    (r"credential|oauth|api key|token", "credentials"), (r"red[- ]team", "red team"), (r"benchmark|evaluat", "evaluation"),
    (r"regulat|\blaw\b|\bact\b|legislat", "regulation"), (r"lawsuit|court", "litigation"), (r"cve-|vulnerab|exploit", "vulnerability"),
    (r"hallucinat|fabricat", "hallucination"), (r"decepti|scheming|blackmail", "deception"), (r"shutdown|kill switch", "shutdown"),
    (r"system card|model card", "system card"), (r"open[- ]weight|open[- ]source model", "open weights"), (r"supply[- ]chain|npm|pypi|package", "supply chain"),
    (r"zero-click", "zero-click"), (r"guardrail|classifier|filter", "guardrails"), (r"\bcost|spend|tokens", "cost"),
]


# --------------------------------------------------------------------------- LLM classifier

def llm_config() -> dict | None:
    key = os.environ.get("LLM_API_KEY", "").strip()
    base = os.environ.get("LLM_BASE_URL", "").strip().rstrip("/")
    if not key or not base:
        return None
    return {"key": key, "base": base, "model": os.environ.get("LLM_MODEL", "").strip() or DEFAULT_MODEL}


def build_system_prompt(tax: dict) -> str:
    return (
        "You classify news items for the companion website of the survey \"Controlling Untrusted AI: A Survey\". "
        "Use only the survey's vocabulary.\n\nSURVEY\n" + SURVEY_PARAGRAPH + "\n\nTAXONOMY (section id, title, operation; subsection ids and titles)\n"
        + compact_taxonomy(tax)
        + "\n\nTASK\nFor each numbered item decide whether it is about deploying or operating AI agents or LLM-based systems in the real world, "
        "good or bad: incidents, near misses, deployments, shipped control mechanisms, evaluations of deployed or deployable agents, "
        "policy, vendor disclosures, or research with direct deployment relevance. Pure product marketing, funding news, opinion without a concrete "
        "event, and items not about AI systems are not relevant.\n\n"
        "Return ONLY a JSON object {\"items\": [...]} with exactly one object per input item, in input order. Fields:\n"
        "- index: the item number\n"
        "- relevant: true or false\n"
        f"- kind: one of {KINDS}\n"
        f"- polarity: one of {POLARITIES} (bad = a failure or harm; good = a success or a control that worked or shipped; mixed otherwise)\n"
        "- summary: two short factual sentences in English (about 350 characters in total, never more than 450) based only on the given text, no speculation, no hype, no em-dashes\n"
        f"- failure_sources: subset of {FAILURE_SOURCES}, the attack tier (benign = the agent itself failed, no attacker; "
        "external = an outsider redirected it through what it read, called, or remembered; insider = a person with legitimate "
        "partial access, or the model itself pursuing its own objective); empty if the item is not about a failure\n"
        f"- requirements: subset of {REQUIREMENTS} (the requirement at stake)\n"
        f"- operations: subset of {OPERATIONS} (the operation that failed, was missing, or worked)\n"
        "- subsections: 1 to 4 subsection ids from the taxonomy, most specific first\n"
        f"- domain: one of {DOMAINS}\n"
        f"- evidence: one of {EVIDENCE}\n"
        "- actors: {\"vendor\": string or null, \"deployer\": string or null, \"model\": string or null}\n"
        "- tags: 2 to 5 short lowercase noun phrases\n"
        "- date: \"YYYY-MM-DD\" when the text or url_date gives the event date and it differs from the publication date, else null\n"
        "- confidence: number from 0 to 1\n"
        "When relevant is false the other fields may be null. No markdown, no commentary."
    )


def build_user_prompt(items: list[dict]) -> str:
    blocks = []
    for i, it in enumerate(items, 1):
        lines = [f"### Item {i}", f"title: {it.get('title','')}", f"publisher: {it.get('publisher','')}",
                 f"published: {it.get('date','')}", f"url: {it.get('url','')}"]
        if it.get("url_date"):
            lines.append(f"url_date: {it['url_date']}")
        snippet = re.sub(r"\s+", " ", (it.get("snippet") or "").strip())
        if snippet:
            lines.append(f"text: {snippet[:1500]}")
        if it.get("hints"):
            lines.append("submitter_hints: " + json.dumps(it["hints"], ensure_ascii=False))
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def _chat(cfg: dict, messages: list[dict], max_tokens: int, log=None) -> str:
    url = cfg["base"] + "/chat/completions"
    headers = {"Authorization": f"Bearer {cfg['key']}", "Content-Type": "application/json",
               "User-Agent": "controlling-untrusted-ai-collector/0.1"}
    payload = {"model": cfg["model"], "messages": messages, "max_tokens": max_tokens}
    last = None
    for attempt in range(1, LLM_RETRIES + 1):
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=LLM_TIMEOUT)
            if r.status_code in (429, 500, 502, 503, 504):
                last = f"HTTP {r.status_code}"
                time.sleep(min(30, 3 * attempt ** 2))
                continue
            r.raise_for_status()
            data = r.json()
            content = data["choices"][0]["message"]["content"]
            if isinstance(content, list):  # some gateways return content blocks
                content = "".join(part.get("text", "") for part in content if isinstance(part, dict))
            return content
        except requests.RequestException as e:
            last = type(e).__name__
            time.sleep(min(30, 3 * attempt ** 2))
        except (KeyError, IndexError, ValueError, TypeError) as e:
            last = f"bad response shape: {type(e).__name__}"
            break
    raise RuntimeError(f"LLM call failed after {LLM_RETRIES} attempts ({last})")


def parse_json_loose(text: str) -> dict | None:
    """Accept fenced, prefixed, or slightly damaged JSON; recover per-item objects as a last resort."""
    if not text:
        return None
    t = text.strip()
    t = re.sub(r"^```(?:json)?\s*", "", t)
    t = re.sub(r"\s*```$", "", t)
    try:
        return json.loads(t)
    except ValueError:
        pass
    start, end = t.find("{"), t.rfind("}")
    if start != -1 and end > start:
        try:
            return json.loads(t[start:end + 1])
        except ValueError:
            pass
    items = []
    for m in re.finditer(r"\{[^{}]*\"index\"\s*:\s*\d+[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", t, re.S):
        try:
            items.append(json.loads(m.group(0)))
        except ValueError:
            continue
    return {"items": items} if items else None


def _as_list(v):
    if v is None:
        return []
    if isinstance(v, str):
        return [x.strip() for x in re.split(r"[,;]", v) if x.strip()]
    if isinstance(v, (list, tuple)):
        return [str(x).strip() for x in v if x is not None]
    return []


def validate(raw: dict, item: dict, tax: dict, fallback: dict) -> dict:
    """Coerce an LLM object into the contract; fill anything invalid from the heuristic fallback."""
    out = dict(fallback)
    out["classifier"] = "llm"
    out["needs_review"] = False
    rel = raw.get("relevant")
    if isinstance(rel, str):
        rel = rel.strip().lower() in ("true", "yes", "1")
    out["relevant"] = bool(rel)
    try:
        out["confidence"] = round(max(0.0, min(1.0, float(raw.get("confidence", 0.6)))), 2)
    except (TypeError, ValueError):
        out["confidence"] = 0.6
    if not out["relevant"]:
        return out

    k = str(raw.get("kind") or "").strip().lower()
    if k in KINDS:
        out["kind"] = k
    else:
        out["needs_review"] = True
    p = str(raw.get("polarity") or "").strip().lower()
    if p in POLARITIES:
        out["polarity"] = p
    else:
        out["needs_review"] = True
    s = raw.get("summary")
    if isinstance(s, str) and len(s.strip()) >= 20:
        out["summary"] = two_sentences(s)
    else:
        out["needs_review"] = True

    fs = [x.lower() for x in _as_list(raw.get("failure_sources")) if x.lower() in FAILURE_SOURCES]
    out["failure_sources"] = _uniq(fs)
    rq = [x.lower() for x in _as_list(raw.get("requirements")) if x.lower() in REQUIREMENTS]
    out["requirements"] = _uniq(rq) or fallback["requirements"]
    ops = [x.lower() for x in _as_list(raw.get("operations")) if x.lower() in OPERATIONS]
    out["operations"] = _uniq(ops)[:4] or fallback["operations"]
    subs = [re.sub(r"[^a-z0-9_]", "", x.lower()) for x in _as_list(raw.get("subsections"))]
    subs = [x for x in subs if x in tax["subsection_ids"]]
    if subs:
        out["subsections"] = _uniq(subs)[:4]
    else:
        out["subsections"] = fallback["subsections"]
        out["needs_review"] = True
    d = str(raw.get("domain") or "").strip().lower()
    out["domain"] = d if d in DOMAINS else fallback["domain"]
    e = str(raw.get("evidence") or "").strip().lower()
    out["evidence"] = e if e in EVIDENCE else fallback["evidence"]
    actors = raw.get("actors") if isinstance(raw.get("actors"), dict) else {}
    out["actors"] = {k: (str(actors.get(k)).strip() if actors.get(k) not in (None, "", "null") else None)
                     for k in ("vendor", "deployer", "model")}
    tags = [t.lower()[:40] for t in _as_list(raw.get("tags")) if t]
    out["tags"] = _uniq(tags)[:5] or fallback["tags"]
    date = raw.get("date")
    out["date"] = date if isinstance(date, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", date) else (item.get("url_date") or None)
    if not mostly_latin(item.get("title") or ""):
        out["needs_review"] = True
    if out["confidence"] < 0.5:
        out["needs_review"] = True
    return out


def llm_classify_batch(items: list[dict], tax: dict, cfg: dict, log=None) -> list[dict | None]:
    """Return one raw dict per item (None where the model gave nothing usable). Raises on transport failure."""
    messages = [{"role": "system", "content": build_system_prompt(tax)},
                {"role": "user", "content": build_user_prompt(items)}]
    content = _chat(cfg, messages, max_tokens=700 * len(items) + 400, log=log)
    data = parse_json_loose(content)
    if not data:
        raise RuntimeError("LLM returned no parseable JSON")
    objs = data.get("items") if isinstance(data, dict) else data
    if isinstance(data, dict) and objs is None and "index" in data:
        objs = [data]
    if not isinstance(objs, list):
        raise RuntimeError("LLM JSON has no items list")
    out: list[dict | None] = [None] * len(items)
    for pos, obj in enumerate(objs):
        if not isinstance(obj, dict):
            continue
        try:
            idx = int(obj.get("index", pos + 1)) - 1
        except (TypeError, ValueError):
            idx = pos
        if 0 <= idx < len(items) and out[idx] is None:
            out[idx] = obj
    return out


# --------------------------------------------------------------------------- public entry point

def classify(items: list[dict], taxonomy: dict | None = None, use_llm: bool = True,
             batch_size: int = 8, log=None) -> list[dict]:
    """Classify items. Returns a list aligned with ``items``; every element has the full contract."""
    log = log or (lambda *a, **k: None)
    tax = taxonomy or load_taxonomy()
    results: list[dict] = []
    fallbacks = [heuristic_classify(it, tax, float(it.get("weight", 0.5) or 0.5)) for it in items]
    cfg = llm_config() if use_llm else None
    if use_llm and not cfg:
        log("LLM_API_KEY / LLM_BASE_URL not set; using the heuristic classifier")
    if not cfg:
        return fallbacks
    log(f"LLM classifier: model={cfg['model']} batches of {batch_size}")
    for start in range(0, len(items), batch_size):
        batch = items[start:start + batch_size]
        fb = fallbacks[start:start + batch_size]
        try:
            raws = llm_classify_batch(batch, tax, cfg, log=log)
        except RuntimeError as e:
            log(f"  batch {start // batch_size + 1}: {e}; heuristic fallback")
            results.extend(fb)
            continue
        got = 0
        for it, raw, f in zip(batch, raws, fb):
            if raw is None:
                results.append(f)
            else:
                results.append(validate(raw, it, tax, f))
                got += 1
        log(f"  batch {start // batch_size + 1}: {got}/{len(batch)} classified by the model")
        if start + batch_size < len(items):
            time.sleep(1.0)
    return results


def main(argv=None):
    ap = argparse.ArgumentParser(description="Classify candidate stream items (reads a JSON list).")
    ap.add_argument("--input", required=True, help="JSON file: list of {title,url,snippet,publisher,date,...}")
    ap.add_argument("--no-llm", action="store_true", help="heuristic classifier only")
    ap.add_argument("--batch-size", type=int, default=8)
    ap.add_argument("--taxonomy", help="path to taxonomy.json (default site/data/taxonomy.json, then outline.json)")
    args = ap.parse_args(argv)
    items = json.loads(Path(args.input).read_text(encoding="utf-8"))
    tax = load_taxonomy(Path(args.taxonomy) if args.taxonomy else None)
    res = classify(items, tax, use_llm=not args.no_llm, batch_size=args.batch_size,
                   log=lambda m: print(m, file=sys.stderr))
    print(json.dumps(res, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
