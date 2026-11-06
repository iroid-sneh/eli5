"""The scanner must find every problem planted in the fixture projects."""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "skills", "explain", "scripts"))
import scan  # noqa: E402

FIX = os.path.join(ROOT, "fixtures")


def kinds(facts):
    return {(r["kind"], r["file"]) for r in facts["risk_hints"]}


def where(items):
    return {(i["file"], i["line"]) for i in items}


class ShopFixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.f = scan.scan(os.path.join(FIX, "shop"), use_git=False)

    def test_stack_and_integrations(self):
        self.assertIn("Express", self.f["stack"]["frameworks"])
        names = {i["name"] for i in self.f["integrations"]}
        self.assertTrue({"Stripe", "MongoDB / Mongoose", "JWT", "Nodemailer (SMTP)"} <= names)

    def test_routes_get_mount_prefix_and_auth_hints(self):
        routes = {(r["method"], r["path"]): r["auth_hint"] for r in self.f["routes"]}
        self.assertEqual(routes[("POST", "/payments/checkout")], "yes")
        self.assertEqual(routes[("POST", "/payments/webhook")], "no")
        self.assertEqual(routes[("DELETE", "/products/:id")], "no")

    def test_planted_payment_problems(self):
        k = kinds(self.f)
        self.assertIn(("stripe_webhook_unverified", "src/routes/payments.js"), k)
        self.assertIn(("client_controlled_amount", "src/routes/payments.js"), k)
        self.assertIn(("payments_without_tests", ""), k)

    def test_planted_auth_and_security_problems(self):
        k = kinds(self.f)
        self.assertIn(("sensitive_route_no_auth_hint", "src/routes/products.js"), k)
        self.assertIn(("jwt_hardcoded_secret", "src/middleware/auth.js"), k)
        self.assertIn(("cors_wildcard", "src/server.js"), k)

    def test_planted_data_problems(self):
        k = kinds(self.f)
        self.assertIn(("n_plus_one", "src/routes/orders.js"), k)
        self.assertIn(("unbounded_query", "src/routes/products.js"), k)

    def test_stub_and_swallowed_error(self):
        self.assertIn(("src/routes/payments.js", 29), where(self.f["smells"]["empty_function"]))
        self.assertIn(("src/routes/payments.js", 30), where(self.f["smells"]["todo"]))
        self.assertIn(("src/routes/orders.js", 15), where(self.f["smells"]["empty_catch"]))

    def test_secret_found_and_masked(self):
        s = [x for x in self.f["secrets"] if x["kind"] == "stripe_key"]
        self.assertEqual(len(s), 1)
        self.assertNotIn("DEMO1234FAKE", s[0]["text"])
        self.assertIn("hidden", s[0]["text"])

    def test_env_vars(self):
        self.assertEqual(set(self.f["env"]["used_but_not_documented"]), {"SMTP_HOST", "SMTP_USER", "SMTP_PASS"})

    def test_models_and_graph(self):
        self.assertEqual({m["name"] for m in self.f["data"]["models"]}, {"Order", "Product"})
        edges = {(e["from"], e["to"]) for e in self.f["graph"]["module_edges"]}
        self.assertIn(("src/routes", "src/models"), edges)


class BlogFixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.f = scan.scan(os.path.join(FIX, "blog"), use_git=False)

    def test_django_detected(self):
        self.assertIn("Django", self.f["stack"]["frameworks"])
        self.assertEqual({m["name"] for m in self.f["data"]["models"]}, {"Post", "Comment"})

    def test_django_view_auth_resolution(self):
        routes = {r["path"]: r["auth_hint"] for r in self.f["routes"] if r["framework"] == "django"}
        self.assertEqual(routes["/posts/new/"], "yes")          # @login_required
        self.assertEqual(routes["/admin/posts/<int:pk>/delete/"], "no")

    def test_planted_problems(self):
        k = kinds(self.f)
        self.assertIn(("sql_string_building", "blog/views.py"), k)
        self.assertIn(("n_plus_one", "blog/views.py"), k)
        self.assertIn(("debug_mode_on", "mysite/settings.py"), k)
        self.assertIn(("sensitive_route_no_auth_hint", "blog/views.py"), k)
        self.assertTrue(self.f["smells"]["not_implemented"])
        self.assertIn("blog/views.py", {x["file"] for x in self.f["smells"]["empty_catch"]})


class TodoFixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.f = scan.scan(os.path.join(FIX, "todo"), use_git=False)

    def test_nextjs_routes_and_pages(self):
        self.assertIn("Next.js", self.f["stack"]["frameworks"])
        self.assertEqual({(r["method"], r["path"]) for r in self.f["routes"]}, {("GET", "/api/todos"), ("POST", "/api/todos")})
        self.assertEqual({p["path"] for p in self.f["ui_pages"]}, {"/", "/dashboard"})

    def test_planted_problems(self):
        self.assertIn("app/api/todos/route.ts", {x["file"] for x in self.f["smells"]["placeholder"]})
        self.assertIn("app/page.tsx", {x["file"] for x in self.f["smells"]["placeholder"]})
        self.assertIn("lib/stats.ts", {x["file"] for x in self.f["smells"]["empty_catch"]})
        self.assertEqual(self.f["env"]["used_but_not_documented"], ["DATABASE_URL"])
        self.assertEqual(self.f["tests"]["test_files"], 0)
        self.assertEqual([m["name"] for m in self.f["data"]["models"]], ["Todo"])


class Safety(unittest.TestCase):
    def test_scanner_is_read_only(self):
        """Scanning must not create or change anything inside the scanned project."""
        target = os.path.join(FIX, "todo")

        def snapshot():
            out = {}
            for d, _, files in os.walk(target):
                for n in files:
                    p = os.path.join(d, n)
                    out[p] = os.path.getmtime(p)
            return out
        before = snapshot()
        scan.scan(target, use_git=False)
        self.assertEqual(before, snapshot())


if __name__ == "__main__":
    unittest.main()
