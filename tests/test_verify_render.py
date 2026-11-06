"""The proof checker must catch bad evidence and fix shifted lines; the renderer must escape everything."""
import copy
import json
import os
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "skills", "explain", "scripts"))
import render  # noqa: E402
import verify  # noqa: E402

SHOP = os.path.join(ROOT, "fixtures", "shop")


def report(evidence, severity=None):
    claim = {"name": "x", "evidence": evidence}
    if severity:
        claim.update(severity=severity, confidence="verified")
    return {"meta": {"project": "p", "theme": "cricket"}, "findings": [claim] if severity else [], "modules": [] if severity else [claim]}


class Verify(unittest.TestCase):
    def run_one(self, ev, severity=None):
        r, failures = verify.verify(report([ev], severity), SHOP)
        claim = (r["findings"] or r["modules"])[0]
        return claim, claim["evidence"][0], r["meta"]["trust"]

    def test_exact_quote_verified_with_exact_lines(self):
        _, ev, t = self.run_one({"file": "src/routes/payments.js", "line_start": 18, "line_end": 22,
                                 "quote": "router.post('/webhook', async (req, res) => {"})
        self.assertEqual(ev["status"], "verified")
        self.assertEqual((ev["line_start"], ev["line_end"]), (19, 19))   # tightened to the real line
        self.assertEqual(t["score"], 100)

    def test_multiline_quote_span(self):
        _, ev, _ = self.run_one({"file": "src/routes/payments.js", "line_start": 27,
                                 "quote": "async function refundOrder(req, res) {\n  // TODO: implement refunds\n}"})
        self.assertEqual((ev["status"], ev["line_start"], ev["line_end"]), ("verified", 29, 31))

    def test_wrong_lines_are_relocated(self):
        _, ev, _ = self.run_one({"file": "src/routes/payments.js", "line_start": 2, "quote": "router.post('/refund', requireAuth, refundOrder);"})
        self.assertEqual((ev["status"], ev["line_start"]), ("relocated", 27))

    def test_invented_quote_fails_and_finding_downgraded(self):
        claim, ev, t = self.run_one({"file": "src/routes/payments.js", "line_start": 5, "quote": "stripe.webhooks.constructEvent(req.body"}, severity="broken")
        self.assertEqual(ev["status"], "not_found")
        self.assertTrue(claim["unproven"])
        self.assertEqual(claim["confidence"], "guess")
        self.assertEqual(t["score"], 0)

    def test_missing_file_and_path_escape(self):
        _, ev, _ = self.run_one({"file": "src/nope.js", "line_start": 1, "quote": "x"})
        self.assertEqual(ev["status"], "missing_file")
        _, ev, _ = self.run_one({"file": "../../etc/passwd", "line_start": 1, "quote": "root"})
        self.assertEqual(ev["status"], "bad_path")

    def test_file_with_line_suffix_is_tolerated(self):
        _, ev, _ = self.run_one({"file": "src/server.js:9", "quote": "app.use(cors());"})
        self.assertEqual((ev["file"], ev["status"], ev["line_start"]), ("src/server.js", "verified", 9))


def read(p):
    with open(p, encoding="utf-8") as fh:
        return fh.read()


class Render(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_html_escapes_hostile_content_and_md_links(self):
        evil = "</script><img src=x onerror=alert(1)>"
        r = {"meta": {"project": evil, "theme": "cricket", "trust": {"score": 90, "proven": 9, "claims": 10}},
             "story": {"eli5": evil}, "theme_map": [], "modules": [],
             "findings": [{"severity": "broken", "confidence": "verified", "title_eli5": evil, "title": "t",
                           "evidence": [{"file": "src/server.js", "line_start": 9, "line_end": 9, "quote": "app.use(cors());", "status": "verified"}]}]}
        os.makedirs(os.path.join(self.tmp, "reports"))
        p = os.path.join(self.tmp, "reports", "cricket.json")
        with open(p, "w") as fh:
            json.dump(r, fh)
        render.render(p, self.tmp, SHOP)
        html = read(os.path.join(self.tmp, "index.html"))
        self.assertNotIn("<img src=x", html)
        self.assertEqual(html.count("</script>"), 3)   # only the page's own three script tags
        md = read(os.path.join(self.tmp, "README.eli5.md"))
        self.assertIn("src/server.js#L9", md)

    def test_theme_switcher_lists_all_reports(self):
        os.makedirs(os.path.join(self.tmp, "reports"))
        for theme in ("cricket", "Formula 1"):
            with open(os.path.join(self.tmp, "reports", render.slugify(theme) + ".json"), "w") as fh:
                json.dump({"meta": {"project": "p", "theme": theme}, "findings": []}, fh)
        render.render(os.path.join(self.tmp, "reports", "formula-1.json"))
        self.assertTrue(os.path.exists(os.path.join(self.tmp, "cricket.html")))
        html = read(os.path.join(self.tmp, "formula-1.html"))
        self.assertIn('"file": "cricket.html"', html)

    def test_example_report_is_fully_proven(self):
        r = json.loads(read(os.path.join(ROOT, "examples", "shop-cricket", "reports", "cricket.json")))
        r, failures = verify.verify(copy.deepcopy(r), SHOP)
        self.assertEqual(failures, [])
        self.assertEqual(r["meta"]["trust"]["score"], 100)


if __name__ == "__main__":
    unittest.main()
