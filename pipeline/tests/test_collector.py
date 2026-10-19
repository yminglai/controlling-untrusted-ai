"""Offline tests for pipeline/collect_news.py and pipeline/classify.py.

Run:  python3 -m unittest discover -s pipeline/tests -v
No network access is needed; the LLM path is exercised against an in-process fake gateway.
"""
import json
import os
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import classify as clf  # noqa: E402
import collect_news as cn  # noqa: E402

RSS = b"""<?xml version="1.0"?><rss version="2.0" xmlns:dc="http://purl.org/dc/elements/1.1/">
<channel><title>Example Press</title>
<item><title>Coding agent &amp; the deleted database</title><link>https://example.com/a?utm_source=rss#top</link>
<pubDate>Thu, 16 Oct 2026 20:59:01 +0000</pubDate><description>&lt;p&gt;An AI agent deleted a production database. The vendor added rollback.&lt;/p&gt;</description></item>
<item><title>No date</title><link>https://example.com/b</link></item>
</channel></rss>"""
ATOM = b"""<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom"><title>Example Atom</title>
<entry><title>Prompt injection in a browser agent</title><link rel="alternate" type="text/html" href="https://example.org/p"/>
<link rel="self" href="https://example.org/self"/><published>2026-10-15T10:05:54Z</published><summary>Researchers hijacked the agent via a web page.</summary></entry>
</feed>"""
RDF = b"""<?xml version="1.0"?><rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns="http://purl.org/rss/1.0/" xmlns:dc="http://purl.org/dc/elements/1.1/">
<channel><title>RSS1</title></channel><item><title>Old item</title><link>https://example.net/o</link><dc:date>2026-10-01</dc:date><description>x</description></item></rdf:RDF>"""

FEED = {"id": "t", "publisher": "", "weight": 0.6, "evidence": "press"}


class ParsingTests(unittest.TestCase):
    def test_rss(self):
        e = cn.parse_feed(RSS, FEED)
        self.assertEqual(len(e), 2)
        self.assertEqual(e[0]["title"], "Coding agent & the deleted database")
        self.assertEqual(e[0]["publisher"], "Example Press")
        self.assertIn("deleted a production database", cn.clean_snippet(e[0]["snippet"]))

    def test_atom_picks_alternate_link(self):
        e = cn.parse_feed(ATOM, FEED)
        self.assertEqual(e[0]["url"], "https://example.org/p")
        self.assertEqual(e[0]["published"], "2026-10-15T10:05:54Z")

    def test_rdf(self):
        e = cn.parse_feed(RDF, FEED)
        self.assertEqual(e[0]["url"], "https://example.net/o")

    def test_dates(self):
        self.assertEqual(cn.parse_date("Thu, 08 Oct 26 12:00:00 +0000").date().isoformat(), "2026-10-08")
        self.assertEqual(cn.parse_date("2026-10-15T10:05:54Z").date().isoformat(), "2026-10-15")
        self.assertEqual(cn.parse_date("2026-10-01").date().isoformat(), "2026-10-01")
        self.assertIsNone(cn.parse_date("yesterday"))
        self.assertIsNone(cn.parse_date(None))


class NormalisationTests(unittest.TestCase):
    def test_url_key(self):
        a = cn.normalise_url("https://www.Example.com/a/?utm_source=x&id=2#frag")
        b = cn.normalise_url("http://example.com/a?id=2")
        self.assertEqual(a, b)
        self.assertEqual(cn.normalise_url("http://export.arxiv.org/abs/2610.22319v1"), cn.normalise_url("https://arxiv.org/pdf/2610.22319v2"))

    def test_clean_url_keeps_host_strips_tracking(self):
        self.assertEqual(cn.clean_url("https://www.example.com/a?utm_source=rss&q=1#x"), "https://www.example.com/a?q=1")

    def test_title_key(self):
        self.assertEqual(cn.title_key("The Agent deleted a Database!"), cn.title_key("agent deleted database"))

    def test_make_id(self):
        iid = cn.make_id("2025-07-18", "Replit's coding agent deleted a production database during a code freeze " * 3)
        self.assertTrue(iid.startswith("2025-07-18-replit-s-coding-agent"))
        self.assertLessEqual(len(iid), 80)
        self.assertNotIn("--", iid)

    def test_candidates_filter_old_and_dupes(self):
        import datetime as dt
        now = dt.datetime(2026, 10, 17, tzinfo=dt.timezone.utc)
        raw = cn.parse_feed(RSS, FEED) + cn.parse_feed(ATOM, FEED) + cn.parse_feed(RDF, FEED)
        for e in raw:
            e["_feed"] = FEED
        stream = {"items": [{"url": "https://example.org/p?utm_medium=feed", "title": "x", "id": "y"}]}
        counters = {"unparseable": 0, "too_old": 0, "duplicate": 0, "prefiltered": 0}
        c = cn.build_candidates(raw, stream, 10, now, counters)
        self.assertEqual([x["title"] for x in c], ["Coding agent & the deleted database"])
        self.assertEqual(counters, {"unparseable": 1, "too_old": 1, "duplicate": 1, "prefiltered": 0})
        self.assertEqual(c[0]["url"], "https://example.com/a")


class LimitAndDateTests(unittest.TestCase):
    def test_url_date(self):
        self.assertEqual(cn.url_date("https://www.kpbs.org/news/health/2025/12/11/lawsuit-claims"), "2025-12-11")
        self.assertIsNone(cn.url_date("https://example.com/2025/13/40/x"))
        self.assertIsNone(cn.url_date("https://example.com/a"))

    def test_round_robin(self):
        cands = [{"feed_id": "a", "n": i} for i in range(5)] + [{"feed_id": "b", "n": i} for i in range(2)] + [{"feed_id": "c", "n": 0}]
        out = cn.round_robin(cands, 6)
        self.assertEqual([(c["feed_id"], c["n"]) for c in out], [("a", 0), ("b", 0), ("c", 0), ("a", 1), ("b", 1), ("a", 2)])
        self.assertEqual(cn.round_robin(cands, 0), [])

    def test_dash_cleanup(self):
        self.assertEqual(cn.clean_snippet("tool \u2014 and falsely --- documented"), "tool - and falsely - documented")

    def test_negative_terms_and_non_latin(self):
        tax = clf.load_taxonomy()
        it = {"title": "Deepfake voice clone scam targets relatives", "snippet": "AI voice cloning used for fraud.", "url": "https://x", "publisher": "AI Incident Database"}
        self.assertFalse(clf.heuristic_classify(it, tax, 1.0)["relevant"])
        it = {"title": "AI coding agent went rogue and deleted files", "snippet": "", "url": "https://x", "publisher": "AI Incident Database"}
        r = clf.heuristic_classify(it, tax, 1.0)
        self.assertTrue(r["relevant"])
        self.assertEqual(r["failure_sources"], ["benign"])
        it = {"title": "Εξαρθρώθηκε εγκληματική οργάνωση με AI", "snippet": "agent deployment", "url": "https://x", "publisher": "P"}
        self.assertFalse(clf.heuristic_classify(it, tax, 1.0)["relevant"])


class IssueFormTests(unittest.TestCase):
    BODY = ("### Title\n\nAgent emailed confidential files\n\n### URL\n\nhttps://example.com/story\n\n### Date\n\n2026-10-02\n\n"
            "### What happened\n\nAn email agent forwarded a folder to an outside address after reading a poisoned calendar invite.\n\n"
            "### Good or bad\n\nbad\n\n### Which failure source\n\nexternal (prompt injection, memory poisoning, redirected by what it read, called, or remembered)\n\n"
            "### Which operation\n\nconstrain (confinement, formal enforcement, information-flow control, delegated authority)\n\n"
            "### Subsection (optional)\n\ns2_2, s4_3\n\n### Checks\n\n- [x] The URL is public\n")

    def test_parse_and_candidate(self):
        f = cn.parse_issue_body(self.BODY)
        self.assertEqual(f["url"], "https://example.com/story")
        c = cn.issue_to_candidate({"number": 7, "title": "[Submission]: x", "body": self.BODY, "created_at": "2026-10-03T00:00:00Z"})
        self.assertEqual(c["date"], "2026-10-02")
        self.assertEqual(c["hints"], {"polarity": "bad", "failure_sources": ["external"], "operations": ["constrain"], "subsections": ["s2_2", "s4_3"]})
        self.assertEqual(c["lens"], "github-issue:7")
        self.assertEqual(c["added_by"], "submission")

    def test_issue_template_uses_the_collector_vocabulary(self):
        """The dropdown options of .github/ISSUE_TEMPLATE/submit_item.yml must start with the ids the collector matches."""
        tpl = Path(__file__).resolve().parents[2] / ".github" / "ISSUE_TEMPLATE" / "submit_item.yml"
        if not tpl.exists():
            self.skipTest("issue template not present")
        import yaml
        form = yaml.safe_load(tpl.read_text(encoding="utf-8"))
        options = {f["id"]: [o.split(" ")[0] for o in f["attributes"]["options"]] for f in form["body"] if f.get("type") == "dropdown"}
        self.assertEqual(options["failure_source"][:3], clf.FAILURE_SOURCES)
        self.assertEqual(options["operation"][:7], clf.OPERATIONS)

    def test_missing_url_is_dropped(self):
        self.assertIsNone(cn.issue_to_candidate({"number": 1, "title": "t", "body": "### URL\n\n_No response_"}))


class HeuristicTests(unittest.TestCase):
    def setUp(self):
        self.tax = clf.load_taxonomy()

    def test_taxonomy_has_29_subsections(self):
        self.assertEqual(len(self.tax["subsection_ids"]), 29)
        self.assertIn("s4_4", self.tax["subsection_ids"])
        self.assertIn("s9_2", self.tax["subsection_ids"])
        self.assertNotIn("s10_3", self.tax["subsection_ids"])
        self.assertNotIn("s11_1", self.tax["subsection_ids"])
        self.assertEqual(next(s for s in self.tax["sections"] if s["id"] == "s7")["operations"], ["steer", "train"])

    def test_fallback_taxonomy_and_rules_agree(self):
        fallback_ids = {f"{sid}_{j}" for sid, _k, _t, subs in clf.FALLBACK_TAXONOMY for j in range(1, len(subs) + 1)}
        self.assertEqual(len(fallback_ids), 29)
        for sid, _pats in clf.SUBSECTION_RULES:
            self.assertIn(sid, fallback_ids, f"rule for unknown subsection {sid}")
        self.assertEqual(len({sid for sid, _ in clf.SUBSECTION_RULES}), len(clf.SUBSECTION_RULES), "one rule group per subsection")
        self.assertEqual({o for ops in clf.SECTION_OPERATIONS.values() for o in ops} - {"failures"}, set(clf.OPERATIONS))
        self.assertEqual(set(clf.OPERATION_SECTION), set(clf.OPERATIONS))

    def test_incident(self):
        it = {"title": "Coding agent deleted a production database", "snippet": "The AI agent wiped the database during a code freeze; the vendor added rollback.", "publisher": "Fortune", "url": "https://x"}
        r = clf.heuristic_classify(it, self.tax, 0.6)
        self.assertTrue(r["relevant"])
        self.assertEqual((r["kind"], r["polarity"]), ("incident", "bad"))
        self.assertIn("benign", r["failure_sources"])
        self.assertIn("s2_1", r["subsections"])
        self.assertEqual(r["domain"], "coding")
        self.assertTrue(r["needs_review"])
        self.assertTrue(1 <= len(r["subsections"]) <= 4)

    def test_irrelevant(self):
        it = {"title": "New chip-based tape measure for light", "snippet": "Researchers built a photonic device.", "publisher": "NIST", "url": "https://x"}
        self.assertFalse(clf.heuristic_classify(it, self.tax, 0.4)["relevant"])

    def test_enumerations_valid(self):
        it = {"title": "Browser agent hijacked by prompt injection on a web page, regulators warn", "snippet": "A lawsuit followed.", "publisher": "Wired", "url": "https://x"}
        r = clf.heuristic_classify(it, self.tax, 0.6)
        self.assertIn(r["kind"], clf.KINDS)
        self.assertIn(r["polarity"], clf.POLARITIES)
        self.assertTrue(set(r["failure_sources"]) <= set(clf.FAILURE_SOURCES))
        self.assertTrue(set(r["operations"]) <= set(clf.OPERATIONS))
        self.assertTrue(set(r["requirements"]) <= set(clf.REQUIREMENTS))
        self.assertIn(r["domain"], clf.DOMAINS)
        self.assertIn(r["evidence"], clf.EVIDENCE)


class ValidateTests(unittest.TestCase):
    def test_validate_coerces(self):
        tax = clf.load_taxonomy()
        it = {"title": "t", "snippet": "s", "url": "https://x"}
        fb = clf.heuristic_classify(it, tax)
        raw = {"relevant": "true", "kind": "Incident", "polarity": "BAD", "summary": "Sentence one is here. Sentence two is here. Sentence three.",
               "failure_sources": "external, manipulation, bogus", "operations": ["constrain", "observe", "nope"], "subsections": ["S4_2", "s99_1", "s4_5"],
               "domain": "coding", "evidence": "press", "actors": {"vendor": "Acme", "model": None}, "tags": ["a", "b"], "date": "2026-10-01", "confidence": 0.9}
        r = clf.validate(raw, it, tax, fb)
        self.assertEqual(r["kind"], "incident")
        self.assertEqual(r["polarity"], "bad")
        self.assertEqual(r["failure_sources"], ["external"])      # the old word "manipulation" is no longer accepted
        self.assertEqual(r["operations"], ["constrain"])          # nor is "observe"
        self.assertEqual(r["subsections"], ["s4_2"])
        self.assertEqual(r["summary"], "Sentence one is here. Sentence two is here.")
        self.assertEqual(r["actors"], {"vendor": "Acme", "deployer": None, "model": None})
        self.assertFalse(r["needs_review"])
        self.assertEqual(r["classifier"], "llm")

    def test_parse_json_loose(self):
        self.assertEqual(clf.parse_json_loose('```json\n{"items": [{"index": 1}]}\n```'), {"items": [{"index": 1}]})
        self.assertEqual(clf.parse_json_loose('Sure: {"items": [{"index": 2}]} done'), {"items": [{"index": 2}]})
        self.assertIsNone(clf.parse_json_loose("nothing here"))


class _FakeGateway(BaseHTTPRequestHandler):
    calls = []

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        payload = json.loads(self.rfile.read(n))
        _FakeGateway.calls.append({"path": self.path, "auth": self.headers.get("Authorization"), "payload": payload})
        user = payload["messages"][1]["content"]
        count = user.count("### Item ")
        items = []
        for i in range(1, count + 1):
            items.append({"index": i, "relevant": i != 2, "kind": "incident", "polarity": "bad",
                          "summary": "A deployed agent did something harmful. The vendor responded with a fix.",
                          "failure_sources": ["external"], "requirements": ["in-scope"], "operations": ["constrain", "monitor"],
                          "subsections": ["s2_2", "s4_3"], "domain": "email-and-office", "evidence": "press",
                          "actors": {"vendor": "V", "deployer": None, "model": "M"}, "tags": ["prompt injection"], "date": None, "confidence": 0.8})
        body = json.dumps({"choices": [{"message": {"content": "```json\n" + json.dumps({"items": items}) + "\n```"}}]}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


class LLMContractTests(unittest.TestCase):
    def test_against_fake_gateway(self):
        srv = HTTPServer(("127.0.0.1", 0), _FakeGateway)
        th = threading.Thread(target=srv.serve_forever, daemon=True)
        th.start()
        old = {k: os.environ.get(k) for k in ("LLM_API_KEY", "LLM_BASE_URL", "LLM_MODEL")}
        os.environ["LLM_API_KEY"] = "test-key-not-real"
        os.environ["LLM_BASE_URL"] = f"http://127.0.0.1:{srv.server_port}/v1"
        os.environ["LLM_MODEL"] = "fake/model"
        try:
            tax = clf.load_taxonomy()
            items = [{"title": f"Item {i} about an email agent", "snippet": "Prompt injection via calendar invite.", "url": f"https://x/{i}", "publisher": "P", "date": "2026-10-10"} for i in range(3)]
            res = clf.classify(items, tax, use_llm=True, batch_size=2)
            self.assertEqual(len(res), 3)
            self.assertEqual([r["relevant"] for r in res], [True, False, True])
            self.assertEqual(res[0]["subsections"], ["s2_2", "s4_3"])
            self.assertEqual(res[0]["failure_sources"], ["external"])
            self.assertEqual(res[0]["operations"], ["constrain", "monitor"])
            self.assertEqual(res[0]["classifier"], "llm")
            self.assertFalse(res[0]["needs_review"])
            self.assertEqual(len(_FakeGateway.calls), 2)
            call = _FakeGateway.calls[0]
            self.assertEqual(call["path"], "/v1/chat/completions")
            self.assertEqual(call["auth"], "Bearer test-key-not-real")
            self.assertNotIn("temperature", call["payload"])
            self.assertEqual(call["payload"]["model"], "fake/model")
            system = call["payload"]["messages"][0]["content"]
            self.assertIn("Controlling Untrusted AI", system)
            self.assertIn("s4_1 Confinement", system)
            self.assertIn("three tiers", system)
            for word in ("benign", "external", "insider", "monitor", "evaluate"):
                self.assertIn(word, system)
            for word in ("mistakes'", "manipulation'", "misalignment'", "'observe'", "'verify'"):
                self.assertNotIn(word, system, f"old vocabulary {word} still in the prompt")
        finally:
            srv.shutdown()
            srv.server_close()
            for k, v in old.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v


class TaxonomyConsistencyTests(unittest.TestCase):
    """Subsection ids are positional: a renamed outline changes what an id means. These
    checks fail when the collector's built-in copy, its regex rules or the published
    stream disagree with site/data/taxonomy.json."""
    TAXONOMY = Path(__file__).resolve().parents[2] / "site" / "data" / "taxonomy.json"
    STREAM = Path(__file__).resolve().parents[2] / "site" / "data" / "stream.json"

    def _titles(self):
        data = json.loads(self.TAXONOMY.read_text(encoding="utf-8"))
        return data, {ss["id"]: ss["title"] for s in data["sections"] for ss in s["subsections"]}

    def test_fallback_titles_match_taxonomy_json(self):
        if not self.TAXONOMY.exists():
            self.skipTest("taxonomy.json not built")
        _, titles = self._titles()
        for sid, _k, _title, subs in clf.FALLBACK_TAXONOMY:
            for j, t in enumerate(subs, 1):
                self.assertEqual(titles[f"{sid}_{j}"], t, f"{sid}_{j}: FALLBACK_TAXONOMY title differs from taxonomy.json")

    def test_rule_ids_follow_section_two_semantics(self):
        if not self.TAXONOMY.exists():
            self.skipTest("taxonomy.json not built")
        _, titles = self._titles()
        rules = dict(clf.SUBSECTION_RULES)
        for sid in rules:
            self.assertIn(sid, titles, f"rule for unknown subsection {sid}")
        self.assertEqual(titles["s2_2"], "External Attacks")
        self.assertEqual(titles["s2_3"], "Insider Threats")
        self.assertNotIn("s2_4", titles)
        # 2.3 covers the human insider, the model as the limiting case of an insider, and colluding agents
        self.assertTrue(any("insider" in p for p in rules["s2_3"]), "s2_3 rules must carry insider vocabulary")
        self.assertTrue(any("reward hack" in p for p in rules["s2_3"]), "reward hacking is the model-as-insider case, s2_3")
        self.assertTrue(any("collu" in p for p in rules["s2_3"]), "collusion between agents is filed under s2_3")
        tax = clf.load_taxonomy()
        r = clf.heuristic_classify({"title": "Model reward hacked its coding harness in production RL",
                                    "snippet": "The agent tampered with the test harness to pass.", "url": "https://x"}, tax, 0.6)
        self.assertIn("s2_3", r["subsections"])
        self.assertIn("insider", r["failure_sources"])
        r2 = clf.heuristic_classify({"title": "Rogue employee stole model weights from an AI lab",
                                     "snippet": "An insider with privileged access exfiltrated the weights.", "url": "https://x"}, tax, 0.6)
        self.assertIn("s2_3", r2["subsections"])
        self.assertIn("insider", r2["failure_sources"])
        r3 = clf.heuristic_classify({"title": "Two AI agents colluded through steganographic messages to bypass their monitor",
                                     "snippet": "A multi-agent pipeline hid a covert channel from the untrusted monitor.", "url": "https://x"}, tax, 0.6)
        self.assertIn("s2_3", r3["subsections"])
        r4 = clf.heuristic_classify({"title": "Email agent hijacked by prompt injection in a calendar invite leaked files",
                                     "snippet": "Indirect prompt injection exfiltrated data from the inbox.", "url": "https://x"}, tax, 0.6)
        self.assertIn("s2_2", r4["subsections"])
        self.assertEqual(r4["failure_sources"][0], "external")

    def test_stream_taxonomy_version(self):
        if not (self.TAXONOMY.exists() and self.STREAM.exists()):
            self.skipTest("data not built")
        data, titles = self._titles()
        stream = json.loads(self.STREAM.read_text(encoding="utf-8"))
        self.assertEqual(stream.get("taxonomy_structure"), data.get("structure"),
                         "stream.json was classified against another subsection list; run pipeline/remap_stream.py")
        self.assertEqual(stream.get("taxonomy_generated"), data.get("generated"),
                         "stream.json was classified against another taxonomy; re-file the items")
        self.assertEqual(clf.load_taxonomy().get("structure"), data.get("structure"))
        for it in stream["items"]:
            self.assertTrue(1 <= len(it["subsections"]) <= 4, it["id"])
            for sid in it["subsections"]:
                self.assertIn(sid, titles, f"{it['id']}: {sid}")
            self.assertTrue(set(it["failure_sources"]) <= set(clf.FAILURE_SOURCES), f"{it['id']}: {it['failure_sources']}")
            self.assertTrue(set(it["operations"]) <= set(clf.OPERATIONS), f"{it['id']}: {it['operations']}")

    ABBR = (r"(?:Inc|No|Nos|U\.S|N\.D|S\.D|E\.D|W\.D|Cal|Jr|Sr|Dr|Mr|Ms|Mrs|vs|e\.g|i\.e|approx|Corp|Ltd|Co|St|Gov|Sen|Rep|Fig|Vol|pp"
            r"|et al|D\.C|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec|v|art|para|Art|Sec|cf|ca|a\.m|p\.m|Prof|Univ|Dept|Ph\.D"
            r"|LLC|U\.K|E\.U)\.")

    @classmethod
    def sentence_count(cls, text: str) -> int:
        import re
        t = re.sub(r"\s+", " ", (text or "").strip())
        t = re.sub(cls.ABBR + r"(?=\s)", lambda m: m.group(0)[:-1] + "․", t)
        t = re.sub(r"\b([A-Z])\.(?=\s?[A-Z]\b)", r"\1․", t)
        t = re.sub(r"(\d)\.(\d)", r"\1․\2", t)
        return len([p for p in re.split(r"(?<=[.!?])[\"')\]]*\s+(?=[\"'(\[]?[A-Z0-9])", t) if p.strip()])

    def test_stream_summaries_are_two_sentences(self):
        """SCHEMA.md: two factual sentences. Quotes and initials can fool the splitter, so a
        count of three is reported, more than three fails."""
        if not self.STREAM.exists():
            self.skipTest("stream.json not built")
        stream = json.loads(self.STREAM.read_text(encoding="utf-8"))
        over, warn = [], []
        for it in stream["items"]:
            n = self.sentence_count(it.get("summary", ""))
            if n > 3:
                over.append((it["id"], n))
            elif n == 3:
                warn.append(it["id"])
            self.assertLessEqual(len(it.get("summary", "")), 1400, f"{it['id']}: summary over 1,400 characters")
        for w in warn:
            print(f"ANOMALY: summary may exceed two sentences: {w}")
        self.assertFalse(over, f"summaries over two sentences: {over}")


if __name__ == "__main__":
    unittest.main()
