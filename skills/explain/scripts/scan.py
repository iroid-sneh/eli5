#!/usr/bin/env python3
# eli5: ignore-file  (this file is full of detection patterns; scanning it would be noise)
"""
ELI5 scanner: collects plain, provable facts about a codebase WITHOUT any AI.

- Zero dependencies (Python 3.8+ standard library only).
- Read-only: never modifies the analysed project. The only thing it writes is the
  facts file (default: <repo>/.eli5/facts.json).
- Version-control access is read-only (ls-files / log / status) and can be turned off with --no-git.

Usage:
    python3 scan.py [REPO_PATH] [--out FILE] [--no-git] [--quiet]
"""
from __future__ import annotations

import argparse
import bisect
import datetime as _dt
import json
import os
import posixpath
import re
import subprocess
import sys
from collections import Counter, defaultdict

VERSION = 1
MAX_FILE_BYTES = 1_000_000
LIST_LIMIT = 150

IGNORE_DIRS = {
    "node_modules", ".git", ".hg", ".svn", "dist", "build", "out", ".next", ".nuxt",
    ".svelte-kit", ".output", ".turbo", ".vercel", ".cache", ".parcel-cache", "coverage",
    ".nyc_output", "vendor", "venv", ".venv", "__pycache__", ".pytest_cache", ".mypy_cache",
    ".tox", "target", "obj", ".gradle", ".idea", ".vscode", "Pods", ".dart_tool", ".expo",
    ".eli5", "bower_components", "jspm_packages", ".terraform", "tmp", ".tmp", ".yarn",
    "site-packages", ".angular", "DerivedData",
}
LOCKFILES = {
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "composer.lock", "Gemfile.lock",
    "poetry.lock", "Pipfile.lock", "Cargo.lock", "go.sum", "bun.lockb", "bun.lock",
    "packages.lock.json", "pubspec.lock", "uv.lock",
}
BINARY_EXT = set(
    "png jpg jpeg gif webp ico bmp tiff svgz psd ai sketch fig pdf zip gz tgz bz2 xz 7z rar "
    "jar war ear class dll so dylib exe bin o a lib pyc pyo whl mp3 mp4 mov avi mkv wav flac "
    "ogg webm woff woff2 ttf otf eot db sqlite sqlite3 map heic avif apk aab ipa dmg iso".split()
)
LANG = {
    "js": "JavaScript", "mjs": "JavaScript", "cjs": "JavaScript", "jsx": "JavaScript",
    "ts": "TypeScript", "tsx": "TypeScript", "mts": "TypeScript", "cts": "TypeScript",
    "py": "Python", "rb": "Ruby", "php": "PHP", "java": "Java", "kt": "Kotlin", "kts": "Kotlin",
    "scala": "Scala", "go": "Go", "rs": "Rust", "cs": "C#", "fs": "F#", "swift": "Swift",
    "m": "Objective-C", "mm": "Objective-C", "c": "C", "h": "C", "cpp": "C++", "cc": "C++",
    "hpp": "C++", "dart": "Dart", "ex": "Elixir", "exs": "Elixir", "erl": "Erlang",
    "clj": "Clojure", "lua": "Lua", "r": "R", "pl": "Perl", "sh": "Shell", "bash": "Shell",
    "zsh": "Shell", "ps1": "PowerShell", "sql": "SQL", "prisma": "Prisma", "graphql": "GraphQL",
    "gql": "GraphQL", "vue": "Vue", "svelte": "Svelte", "astro": "Astro", "html": "HTML",
    "htm": "HTML", "css": "CSS", "scss": "SCSS", "sass": "SCSS", "less": "Less",
    "md": "Markdown", "mdx": "Markdown", "json": "JSON", "yaml": "YAML", "yml": "YAML",
    "toml": "TOML", "xml": "XML", "tf": "Terraform", "sol": "Solidity",
}
NON_CODE_LANGS = {"Markdown", "JSON", "YAML", "TOML", "XML"}

TEST_RE = re.compile(
    r"(^|/)(__tests__|tests?|spec|specs|e2e|cypress|playwright)/|\.(test|spec)\.[cm]?[jt]sx?$"
    r"|(^|/)test_[^/]+\.py$|_test\.(py|go)$|Tests?\.(java|kt|cs)$|_spec\.rb$|Test\.php$",
    re.I,
)
AUTH_RE = re.compile(
    r"auth|protect|guard|login_?required|LoginRequired|permission|isAuthenticated|requireUser|"
    r"verifyToken|jwt|session|@UseGuards|@PreAuthorize|@Secured|\[Authorize|ensureLoggedIn|"
    r"withAuth|getServerSession|currentUser|requireAdmin|isAdmin|staff_member_required|"
    r"user_passes_test|middleware\(\s*['\"]auth",
    re.I,
)
SECRET_RES = [
    ("stripe_key", re.compile(r"\b[sr]k_(?:live|test)_[0-9a-zA-Z]{10,}")),
    ("razorpay_key", re.compile(r"\brzp_(?:live|test)_[0-9a-zA-Z]{8,}")),
    ("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("private_key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY")),
    ("google_api_key", re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b")),
    ("github_token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b")),
    ("slack_token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}")),
]
GENERIC_SECRET_RE = re.compile(
    r"\b(api[_-]?key|apikey|secret(?:[_-]?key)?|client[_-]?secret|password|passwd|pwd|"
    r"auth[_-]?token|access[_-]?token|jwt[_-]?secret|private[_-]?key)\b[\"']?\s*[:=]\s*[\"']([^\"'\s]{6,})[\"']",
    re.I,
)
PLACEHOLDER_VALUE_RE = re.compile(r"^(your[_-]|<.*>|x{3,}|\*{3,}|example|\.\.\.|\$\{|%\(|\{\{)", re.I)

RISK_LINE = [
    ("jwt_hardcoded_secret", re.compile(r"jwt\.(?:sign|verify|encode|decode)\([^,]+,\s*['\"`][^'\"`]+['\"`]"),
     "Login tokens (JWT) are signed with a secret written directly in the code"),
    ("cors_wildcard", re.compile(
        r"origin\s*:\s*['\"`]\*['\"`]|Access-Control-Allow-Origin['\"]?\s*[,:]\s*['\"]\*|"
        r"CORS_ALLOW_ALL_ORIGINS\s*=\s*True|CORS_ORIGIN_ALLOW_ALL\s*=\s*True|\bcors\(\s*\)"),
     "CORS lets every website call this server"),
    ("sql_string_building", re.compile(
        r"\b(SELECT|INSERT\s+INTO|UPDATE|DELETE\s+FROM)\b[^\n]*(\$\{|['\"`]\s*\+\s*\w|['\"]\s*%\s*[\w(]|\.format\()", re.I),
     "SQL text is glued together from variables (possible SQL injection)"),
    ("sql_string_building", re.compile(r"\bf([\"'])(?:(?!\1).)*?\b(SELECT|INSERT|UPDATE|DELETE)\b(?:(?!\1).)*?\{", re.I),
     "SQL text is glued together from variables (possible SQL injection)"),
    ("debug_mode_on", re.compile(r"^\s*DEBUG\s*=\s*True\b|\.run\([^)]*debug\s*=\s*True|APP_DEBUG\s*=\s*true", re.I),
     "Debug mode is switched on (leaks internals in production)"),
    ("client_controlled_amount", re.compile(
        r"(req\.body|request\.(?:json|data|form|POST|get_json\(\)))[\w.\[\]'\"]*\bamount\b|"
        r"\bamount\b\s*[:=]\s*(?:req\.body|request\.)", re.I),
     "The payment amount comes straight from the user's request"),
    ("blocking_call", re.compile(
        r"\b(readFileSync|writeFileSync|execSync|spawnSync|hashSync|compareSync|time\.sleep|Thread\.sleep)\b"),
     "Blocking call inside server code (everyone waits while it runs)"),
    ("unbounded_query", re.compile(
        r"\.find\(\s*(\{\s*\})?\s*\)\s*;?\s*$|\.findAll\(\s*\)|\.objects\.all\(\)|SELECT\s+\*\s+FROM\s+\w+\s*['\"`;]", re.I),
     "Loads every row with no limit (gets slow as data grows)"),
    ("eval_use", re.compile(r"\beval\(|new Function\(|\bexec\(\s*(?:request|req)\b"),
     "Runs text as code"),
    ("tls_check_disabled", re.compile(
        r"rejectUnauthorized\s*:\s*false|verify\s*=\s*False|InsecureSkipVerify:\s*true|NODE_TLS_REJECT_UNAUTHORIZED"),
     "Security certificate checks are turned off"),
]
LOOP_RE = re.compile(r"^\s*(for\b|while\b|async\s+for\b|[\w.\]\)]+\.(forEach|map)\()")
LOOP_QUERY_RE = re.compile(
    r"await\s+[\w.]+\.(find\w*|query|get|fetch|select|count|aggregate)\(|\.objects\.(get|filter)\(|"
    r"\.query\.(filter|get)\(|\bSELECT\b|::(find|where)\(|\.where\(")

INTEGRATIONS = [
    ("Stripe", "payments", r"['\"]stripe['\"]|^\s*import\s+stripe|\\Stripe\\|com\.stripe|stripe-go"),
    ("Razorpay", "payments", r"['\"]razorpay['\"]|^\s*import\s+razorpay|Razorpay\\|com\.razorpay"),
    ("PayPal", "payments", r"@paypal/|paypal-rest-sdk|paypalrestsdk|paypalcheckoutsdk|paypal-checkout"),
    ("Braintree", "payments", r"['\"]braintree['\"]|^\s*import\s+braintree"),
    ("Square", "payments", r"['\"]square['\"]|squareup"),
    ("Paddle", "payments", r"@paddle/|paddle-sdk"),
    ("Lemon Squeezy", "payments", r"(?i)lemonsqueezy"),
    ("Cashfree", "payments", r"(?i)cashfree"),
    ("PayU", "payments", r"(?i)\bpayu\b"),
    ("Paytm", "payments", r"(?i)paytmchecksum|paytm-pg|\bpaytm\b"),
    ("NextAuth / Auth.js", "auth", r"['\"]next-auth|['\"]@auth/"),
    ("Passport", "auth", r"['\"]passport(-[\w-]+)?['\"]"),
    ("Auth0", "auth", r"(?i)auth0"),
    ("Clerk", "auth", r"@clerk/"),
    ("JWT", "auth", r"['\"]jsonwebtoken['\"]|['\"]jose['\"]|^\s*import\s+jwt|PyJWT|tymon/jwt-auth|io\.jsonwebtoken"),
    ("Keycloak", "auth", r"(?i)keycloak"),
    ("Firebase", "backend", r"['\"]firebase(/[\w-]+)?['\"]|firebase-admin|firebase_admin|package:firebase_"),
    ("Supabase", "backend", r"@supabase/|^\s*from\s+supabase|supabase_flutter"),
    ("Prisma", "database", r"@prisma/client|['\"]prisma['\"]"),
    ("MongoDB / Mongoose", "database", r"['\"]mongoose['\"]|['\"]mongodb['\"]|pymongo|motor\.motor_asyncio|MongoClient"),
    ("PostgreSQL", "database", r"['\"]pg['\"]|['\"]postgres['\"]|psycopg|asyncpg|postgres(ql)?://"),
    ("MySQL", "database", r"['\"]mysql2?['\"]|pymysql|mysqlclient|mysql://"),
    ("SQLite", "database", r"sqlite3?['\"]|better-sqlite3|import sqlite3"),
    ("Redis", "cache", r"['\"]ioredis['\"]|['\"]redis['\"]|^\s*import\s+redis|Predis|redis://"),
    ("Drizzle", "database", r"drizzle-orm"),
    ("Sequelize", "database", r"['\"]sequelize['\"]"),
    ("TypeORM", "database", r"['\"]typeorm['\"]"),
    ("SQLAlchemy", "database", r"(?i)sqlalchemy"),
    ("BullMQ / Bull", "jobs", r"['\"]bullmq?['\"]"),
    ("Celery", "jobs", r"^\s*from\s+celery|^\s*import\s+celery|@shared_task"),
    ("RabbitMQ", "jobs", r"amqplib|['\"]amqp|^\s*import\s+pika"),
    ("Kafka", "jobs", r"kafkajs|confluent_kafka|kafka-python|spring-kafka"),
    ("AWS SQS", "jobs", r"client-sqs|SQSClient"),
    ("Schedulers / cron", "jobs", r"node-cron|node-schedule|['\"]agenda['\"]|@Scheduled|APScheduler|schedule\.every"),
    ("AWS S3", "storage", r"client-s3|S3Client|['\"]aws-sdk['\"]|boto3"),
    ("Cloudinary", "storage", r"(?i)cloudinary"),
    ("UploadThing", "storage", r"uploadthing"),
    ("Multer (file uploads)", "storage", r"['\"]multer['\"]"),
    ("Nodemailer (SMTP)", "email", r"['\"]nodemailer['\"]"),
    ("SendGrid", "email", r"(?i)sendgrid"),
    ("Mailgun", "email", r"(?i)mailgun"),
    ("Resend", "email", r"['\"]resend['\"]"),
    ("Postmark", "email", r"(?i)postmark"),
    ("AWS SES", "email", r"client-ses|SESClient"),
    ("Twilio", "sms", r"(?i)twilio"),
    ("OpenAI", "ai", r"['\"]openai['\"]|^\s*from\s+openai|^\s*import\s+openai"),
    ("Anthropic", "ai", r"@anthropic-ai/sdk|^\s*from\s+anthropic|^\s*import\s+anthropic"),
    ("Google Gemini", "ai", r"@google/generative-ai|@google/genai|google\.generativeai|google-genai"),
    ("LangChain", "ai", r"(?i)langchain"),
    ("Sentry", "monitoring", r"@sentry/|sentry_sdk|sentry-laravel"),
    ("PostHog", "analytics", r"(?i)posthog"),
    ("Mixpanel", "analytics", r"(?i)mixpanel"),
    ("Google Analytics", "analytics", r"gtag\(|googletagmanager|react-ga"),
    ("Socket.IO", "realtime", r"socket\.io"),
    ("Pusher", "realtime", r"['\"]pusher(-js)?['\"]"),
    ("Algolia", "search", r"algoliasearch"),
    ("Elasticsearch", "search", r"@elastic/elasticsearch|elasticsearch"),
    ("Meilisearch", "search", r"meilisearch"),
    ("GraphQL", "api", r"(?i)graphql|apollo"),
]
INTEGRATIONS = [(n, c, re.compile(p, re.M)) for n, c, p in INTEGRATIONS]

FRAMEWORKS = [
    (r"^next$", "Next.js"), (r"^react$", "React"), (r"^react-native$", "React Native"),
    (r"^expo$", "Expo"), (r"^vue$", "Vue"), (r"^nuxt3?$", "Nuxt"), (r"^@angular/core$", "Angular"),
    (r"^svelte$", "Svelte"), (r"^@sveltejs/kit$", "SvelteKit"), (r"^solid-js$", "Solid"),
    (r"^astro$", "Astro"), (r"^@remix-run/", "Remix"), (r"^electron$", "Electron"),
    (r"^express$", "Express"), (r"^fastify$", "Fastify"), (r"^koa$", "Koa"),
    (r"^@nestjs/core$", "NestJS"), (r"^hono$", "Hono"), (r"^@trpc/server$", "tRPC"),
    (r"^@apollo/server$|^apollo-server", "Apollo GraphQL"), (r"^tailwindcss$", "Tailwind CSS"),
    (r"^typescript$", "TypeScript"), (r"^vite$", "Vite"),
    (r"(?i)^django$", "Django"), (r"(?i)^djangorestframework$", "Django REST Framework"),
    (r"(?i)^flask$", "Flask"), (r"(?i)^fastapi$", "FastAPI"), (r"(?i)^streamlit$", "Streamlit"),
    (r"^laravel/framework$", "Laravel"), (r"^symfony/framework-bundle$", "Symfony"),
    (r"^rails$", "Ruby on Rails"), (r"^sinatra$", "Sinatra"), (r"spring-boot", "Spring Boot"),
    (r"^github\.com/gin-gonic/gin$", "Gin"), (r"^github\.com/labstack/echo", "Echo"),
    (r"^github\.com/gofiber/fiber", "Fiber"), (r"^actix-web$", "Actix Web"), (r"^axum$", "Axum"),
    (r"^Microsoft\.AspNetCore", "ASP.NET Core"), (r"^flutter$", "Flutter"),
]
TEST_FRAMEWORKS = [
    (r"^jest$", "Jest"), (r"^vitest$", "Vitest"), (r"^mocha$", "Mocha"),
    (r"^@playwright/test$", "Playwright"), (r"^cypress$", "Cypress"), (r"(?i)^pytest", "pytest"),
    (r"^phpunit/phpunit$", "PHPUnit"), (r"^pestphp/pest$", "Pest"), (r"^rspec", "RSpec"),
    (r"(?i)junit", "JUnit"), (r"(?i)^(xunit|nunit|mstest)", ".NET tests"),
    (r"^flutter_test$", "flutter_test"), (r"^@testing-library/", "Testing Library"),
]
FRAMEWORKS = [(re.compile(p), n) for p, n in FRAMEWORKS]
TEST_FRAMEWORKS = [(re.compile(p), n) for p, n in TEST_FRAMEWORKS]

ENV_RES = [re.compile(p) for p in [
    r"process\.env\.([A-Z_][A-Z0-9_]*)",
    r"process\.env\[\s*['\"`]([A-Z_][A-Z0-9_]*)['\"`]\s*\]",
    r"import\.meta\.env\.([A-Z_][A-Z0-9_]*)",
    r"os\.environ\.get\(\s*['\"]([A-Z_][A-Z0-9_]*)['\"]",
    r"os\.environ\[\s*['\"]([A-Z_][A-Z0-9_]*)['\"]\s*\]",
    r"os\.getenv\(\s*['\"]([A-Z_][A-Z0-9_]*)['\"]",
    r"\benv\(\s*['\"]([A-Z_][A-Z0-9_]*)['\"]",
    r"ENV\[\s*['\"]([A-Z_][A-Z0-9_]*)['\"]\s*\]",
    r"ENV\.fetch\(\s*['\"]([A-Z_][A-Z0-9_]*)['\"]",
    r"System\.getenv\(\s*\"([A-Z_][A-Z0-9_]*)\"",
    r"Environment\.GetEnvironmentVariable\(\s*\"([A-Z_][A-Z0-9_]*)\"",
    r"os\.Getenv\(\s*\"([A-Z_][A-Z0-9_]*)\"",
]]
ENV_BUILTINS = {"NODE_ENV", "CI", "HOME", "PATH", "PWD", "USER", "SHELL", "TZ", "LANG", "NEXT_RUNTIME",
                "VERCEL", "VERCEL_ENV", "VERCEL_URL", "DEBUG"}
ENV_EXAMPLE_RE = re.compile(r"(^|/)(\.env\.(example|sample|template|dist|defaults)|(example|sample)\.env|\.env\.[\w.-]*example)$")
ENV_FILE_RE = re.compile(r"(^|/)\.env(\.[\w.-]+)?$")

CRON_RE = re.compile(r"cron\.schedule\(|new\s+CronJob|@Scheduled|crontab\(|schedule\.every|add_job\(|beat_schedule|->(daily|hourly|everyMinute|cron)\(")
WORKER_RE = re.compile(r"new\s+Worker\(|@shared_task|@app\.task|@celery\.task|implements\s+ShouldQueue|@Async\b|@KafkaListener|@RabbitListener|consumer\.run\(")

ENTRY_LIKE_RE = re.compile(
    r"(^|/)(index|main|app|server|manage|wsgi|asgi|settings|urls|admin|apps|config|setup|conftest|page|layout|"
    r"route|loading|error|not-found|middleware|_app|_document|program|startup|[\w-]+\.config)\.[\w]+$|"
    r"(^|/)(migrations|scripts|bin|seeds?|public|static|tests?|__tests__|e2e|cypress|docs|examples?|fixtures|pages|app)/",
    re.I,
)
CRITICAL_RE = re.compile(r"pay|checkout|billing|order|auth|login|account|wallet|invoice|subscription|cart|refund", re.I)
SENSITIVE_PATH_RE = re.compile(r"admin|delete|remove|update|edit|users?\b|orders?|pay|refund|account|settings|dashboard|billing", re.I)
PUBLIC_PATH_RE = re.compile(r"login|signin|sign-in|signup|sign-up|register|webhook|health|callback|public|forgot|reset|verify|logout|status|ping", re.I)
EMPTY_BODY = r"\{\s*(?:(?://[^\n]*|/\*[\s\S]*?\*/)\s*)*\}"
KEYWORDS = {"if", "for", "while", "switch", "catch", "function", "else", "do", "try", "with", "return", "constructor", "super", "foreach", "elseif", "using", "lock", "fixed"}


# --------------------------------------------------------------------------- helpers

def snippet(s: str, n: int = 180) -> str:
    s = redact(s.strip())
    return s if len(s) <= n else s[: n - 1] + "…"


def mask(value: str) -> str:
    return (value[:4] if len(value) > 8 else value[:2]) + f"…[{len(value)} chars hidden]"


def redact(s: str) -> str:
    for _, rx in SECRET_RES:
        s = rx.sub(lambda m: mask(m.group(0)), s)
    def _g(m):
        val = m.group(2)
        if PLACEHOLDER_VALUE_RE.search(val):
            return m.group(0)
        return m.group(0).replace(val, mask(val))
    return GENERIC_SECRET_RE.sub(_g, s)


class LineIndex:
    def __init__(self, text: str):
        self.starts = [0] + [m.end() for m in re.finditer(r"\n", text)]

    def line(self, idx: int) -> int:
        return bisect.bisect_right(self.starts, idx)


class Collector:
    def __init__(self):
        self.lists = defaultdict(list)
        self.counts = Counter()
        self.seen = set()

    def add(self, name, item, limit=LIST_LIMIT):
        key = (name, item.get("file"), item.get("line"), item.get("kind"))
        if key in self.seen:
            return
        self.seen.add(key)
        self.counts[name] += 1
        if len(self.lists[name]) < limit:
            self.lists[name].append(item)


def run_git(root, args, timeout=20):
    try:
        out = subprocess.run(["git", "-C", root] + args, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                             timeout=timeout, check=True)
        return out.stdout.decode("utf-8", "replace")
    except Exception:
        return None


def glob_to_re(g: str):
    s, i = "", 0
    while i < len(g):
        c = g[i]
        if c == "*":
            if i + 1 < len(g) and g[i + 1] == "*":
                s += ".*"
                i += 1
                if i + 1 < len(g) and g[i + 1] == "/":
                    i += 1
            else:
                s += "[^/]*"
        elif c == "?":
            s += "[^/]"
        else:
            s += re.escape(c)
        i += 1
    return re.compile("^" + s + "$")


def load_gitignore(root):
    rules = []
    try:
        with open(os.path.join(root, ".gitignore"), encoding="utf-8", errors="replace") as fh:
            for raw in fh:
                l = raw.strip()
                if not l or l.startswith("#") or l.startswith("!"):
                    continue
                dir_only = l.endswith("/")
                l = l.rstrip("/")
                anchored = "/" in l
                l = l.lstrip("/")
                rules.append((glob_to_re(l), anchored, dir_only))
    except OSError:
        pass

    def ignored(rel, is_dir):
        for rx, anchored, dir_only in rules:
            if dir_only and not is_dir:
                continue
            if rx.match(rel if anchored else posixpath.basename(rel)):
                return True
        return False
    return ignored


def list_files(root, use_git):
    rels = None
    if use_git:
        out = run_git(root, ["ls-files", "-co", "--exclude-standard", "-z"], timeout=60)
        if out is not None:
            rels = [r for r in out.split("\0") if r]
    if rels is None:
        rels = []
        ignored = load_gitignore(root)
        for dirpath, dirnames, filenames in os.walk(root):
            rel_dir = os.path.relpath(dirpath, root).replace(os.sep, "/")
            rel_dir = "" if rel_dir == "." else rel_dir
            keep = []
            for d in dirnames:
                rd = f"{rel_dir}/{d}" if rel_dir else d
                full = os.path.join(dirpath, d)
                if d in IGNORE_DIRS or os.path.islink(full) or ignored(rd, True) \
                        or os.path.exists(os.path.join(full, "pyvenv.cfg")):
                    continue
                keep.append(d)
            dirnames[:] = sorted(keep)
            for f in sorted(filenames):
                rf = f"{rel_dir}/{f}" if rel_dir else f
                if not ignored(rf, False) and not os.path.islink(os.path.join(dirpath, f)):
                    rels.append(rf)
    return [r for r in rels if not any(seg in IGNORE_DIRS for seg in r.split("/")[:-1])]


def module_key(rel: str) -> str:
    parts = rel.split("/")
    if len(parts) == 1:
        return "(root files)"
    if parts[0] in ("packages", "apps", "services", "libs", "modules") and len(parts) >= 3:
        return "/".join(parts[:2])
    if parts[0] in ("src", "app", "lib", "server", "backend", "frontend", "client", "api", "web", "source", "internal", "pkg", "cmd") and len(parts) >= 3:
        return "/".join(parts[:2])
    if parts[0] == "src" and len(parts) >= 2:
        return "src"
    return parts[0]


# --------------------------------------------------------------------------- manifests

def parse_manifest(rel, text):
    base = posixpath.basename(rel)
    deps, scripts, kind, extra = [], {}, None, {}
    try:
        if base == "package.json":
            kind = "npm"
            data = json.loads(text)
            for k in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
                deps += list((data.get(k) or {}).keys())
            scripts = data.get("scripts") or {}
            extra = {k: data.get(k) for k in ("name", "main", "bin", "workspaces") if data.get(k)}
        elif re.match(r"requirements.*\.txt$", base):
            kind = "pip"
            for l in text.splitlines():
                l = l.split("#")[0].strip()
                if l and not l.startswith("-"):
                    deps.append(re.split(r"[=<>~!;\[ ]", l)[0])
        elif base == "pyproject.toml":
            kind = "python"
            for block in re.findall(r"dependencies\s*=\s*\[([\s\S]*?)\]", text):
                deps += [re.split(r"[=<>~!;\[ ]", s)[0] for s in re.findall(r"[\"']([^\"']+)[\"']", block)]
            for sec in re.findall(r"\[tool\.poetry\.(?:dev-)?dependencies\]([\s\S]*?)(?:\n\[|$)", text):
                deps += re.findall(r"^\s*([A-Za-z0-9_.-]+)\s*=", sec, re.M)
        elif base == "Pipfile":
            kind = "pipenv"
            for sec in re.findall(r"\[(?:dev-)?packages\]([\s\S]*?)(?:\n\[|$)", text):
                deps += re.findall(r"^\s*([A-Za-z0-9_.-]+)\s*=", sec, re.M)
        elif base == "composer.json":
            kind = "composer"
            data = json.loads(text)
            deps += list((data.get("require") or {}).keys()) + list((data.get("require-dev") or {}).keys())
            scripts = {k: v if isinstance(v, str) else " && ".join(map(str, v)) for k, v in (data.get("scripts") or {}).items()}
        elif base == "Gemfile":
            kind = "bundler"
            deps += re.findall(r"^\s*gem\s+['\"]([^'\"]+)['\"]", text, re.M)
        elif base == "go.mod":
            kind = "go"
            deps += re.findall(r"^\s*(?:require\s+)?([\w.\-]+/[\w.\-/]+)\s+v[\d.]+", text, re.M)
        elif base == "pom.xml":
            kind = "maven"
            deps += re.findall(r"<artifactId>([^<]+)</artifactId>", text)
        elif base in ("build.gradle", "build.gradle.kts"):
            kind = "gradle"
            deps += re.findall(r"(?:implementation|api|compile|runtimeOnly|testImplementation)\s*\(?\s*['\"]([^'\"]+)['\"]", text)
        elif base == "Cargo.toml":
            kind = "cargo"
            for sec in re.findall(r"\[(?:dev-)?dependencies\]([\s\S]*?)(?:\n\[|$)", text):
                deps += re.findall(r"^\s*([A-Za-z0-9_-]+)\s*=", sec, re.M)
        elif base == "pubspec.yaml":
            kind = "pub"
            deps += re.findall(r"^  ([a-z_][a-z0-9_]*):", text, re.M)
        elif base.endswith(".csproj"):
            kind = "nuget"
            deps += re.findall(r"PackageReference\s+Include=\"([^\"]+)\"", text)
    except (ValueError, AttributeError):
        return None
    if not kind:
        return None
    return {"file": rel, "type": kind, "deps": sorted(set(d for d in deps if d)), "scripts": scripts, **extra}


MANIFEST_NAMES = {"package.json", "pyproject.toml", "Pipfile", "composer.json", "Gemfile", "go.mod",
                  "pom.xml", "build.gradle", "build.gradle.kts", "Cargo.toml", "pubspec.yaml"}


def is_manifest(rel):
    b = posixpath.basename(rel)
    return b in MANIFEST_NAMES or re.match(r"requirements.*\.txt$", b) or b.endswith(".csproj")


# --------------------------------------------------------------------------- per-file analysis

def analyze_file(f, text, C, state):
    rel, lang, ext = f["rel"], f["lang"], f["ext"]
    lines = text.split("\n")
    f["loc"] = sum(1 for l in lines if l.strip())
    is_test = f["is_test"]
    is_code = lang is not None and lang not in NON_CODE_LANGS
    idx = LineIndex(text)

    def add(list_name, line_no, **extra):
        item = {"file": rel, "line": line_no, "text": snippet(lines[line_no - 1] if 0 < line_no <= len(lines) else "")}
        item.update(extra)
        C.add(list_name, item)

    # ---- secrets (all text files except example env files)
    if not ENV_EXAMPLE_RE.search(rel):
        for i, l in enumerate(lines, 1):
            for kind, rx in SECRET_RES:
                if rx.search(l):
                    add("secrets", i, kind=kind, in_test=is_test)
            m = GENERIC_SECRET_RE.search(l)
            if m and is_code and not PLACEHOLDER_VALUE_RE.search(m.group(2)) \
                    and not re.search(r"process\.env|os\.environ|getenv|env\(", l):
                add("secrets", i, kind="hardcoded_" + m.group(1).lower().replace("-", "_"), in_test=is_test)

    # ---- env vars
    if ENV_EXAMPLE_RE.search(rel):
        state["env_documented"].update(re.findall(r"^\s*(?:export\s+)?([A-Z_][A-Z0-9_]*)\s*=", text, re.M))
    elif ENV_FILE_RE.search(rel):
        state["env_committed"].append(rel)
    if is_code or posixpath.basename(rel).startswith("docker-compose"):
        for rx in ENV_RES:
            for m in rx.finditer(text):
                name = m.group(1)
                if name not in ENV_BUILTINS:
                    state["env_used"][name].append(f"{rel}:{idx.line(m.start())}")

    # ---- integrations (code + manifests)
    if is_code or f["is_manifest"]:
        for name, cat, rx in INTEGRATIONS:
            m = rx.search(text)
            if m:
                state["integrations"][name]["category"] = cat
                hits = state["integrations"][name]["where"]
                if len(hits) < 8:
                    hits.append(f"{rel}:{idx.line(m.start())}")

    if not is_code:
        return

    # ---- per-line detectors
    debug_count, loop_start = 0, None
    has_routes_before = len(state["routes"])
    for i, l in enumerate(lines, 1):
        if re.search(r"\b(TODO|FIXME|HACK|XXX)\b", l) and not is_test:
            add("todo", i)
        if re.search(r"not\s+(yet\s+)?implemented|NotImplementedError|NotImplementedException|unimplemented!|todo!\(", l, re.I):
            add("not_implemented", i)
        if not is_test and re.search(
                r"lorem ipsum|\b(mock|dummy|fake|sample|hard-?coded|placeholder)[_ ]?(data|users?|items?|products?|orders?|response|posts?|todos?|list|values?|prices?)\b", l, re.I):
            add("placeholder", i)
        if re.search(r"console\.(log|debug)\(|\bvar_dump\(|\bdd\(|System\.out\.println|fmt\.Println|\bdebugger\b", l):
            debug_count += 1
        if not is_test:
            for kind, rx, note in RISK_LINE:
                if rx.search(l):
                    add("risk_raw", i, kind=kind, note=note)
            if LOOP_RE.search(l):
                loop_start = i
            elif loop_start and i - loop_start <= 5 and LOOP_QUERY_RE.search(l):
                add("risk_raw", loop_start, kind="n_plus_one",
                    note="A database query runs inside a loop (one trip per item: slow with lots of data)")
                loop_start = None
        if CRON_RE.search(l):
            add("cron_jobs", i)
        if WORKER_RE.search(l):
            add("workers", i)
    if debug_count:
        state["debug_logs"][rel] = debug_count

    # ---- multi-line detectors
    for m in re.finditer(r"catch\s*(?:\([^)]*\))?\s*" + EMPTY_BODY, text):
        add("empty_catch", idx.line(m.start()))
    for m in re.finditer(r"\.catch\(\s*(?:\(\s*\w*\s*\)|\w+)?\s*=>\s*(?:\{\s*\}|null|undefined)\s*\)", text):
        add("empty_catch", idx.line(m.start()))
    for m in re.finditer(r"except[^:\n]*:\s*(?:#[^\n]*)?\n\s*pass\b", text):
        add("empty_catch", idx.line(m.start()))
    if ext in ("js", "jsx", "ts", "tsx", "mjs", "cjs", "php", "vue", "svelte"):
        for m in re.finditer(r"(?:async\s+)?function\s*\*?\s*(\w*)\s*\([^)]*\)\s*(?::\s*[^{;]+?)?" + EMPTY_BODY, text):
            add("empty_function", idx.line(m.start()), name=m.group(1) or "(anonymous)")
        for m in re.finditer(r"(\w+)\s*=\s*(?:async\s*)?\([^)]*\)\s*(?::\s*[^=;{]+)?=>\s*" + EMPTY_BODY, text):
            add("empty_function", idx.line(m.start()), name=m.group(1))
    if ext in ("js", "jsx", "ts", "tsx", "mjs", "cjs", "java", "kt", "cs", "php", "dart", "go", "swift"):
        rx = re.compile(r"^[ \t]*(?:(?:public|private|protected|static|async|override|virtual|final|abstract|internal|func)\s+)*"
                        r"(?:[\w<>\[\],.?]+\s+)?(\w+)\s*\([^)\n]*\)\s*(?::\s*[\w<>\[\]|, .?]+)?\s*" + EMPTY_BODY, re.M)
        for m in rx.finditer(text):
            if m.group(1).lower() not in KEYWORDS:
                add("empty_function", idx.line(m.start()), name=m.group(1))
    if ext == "py":
        for m in re.finditer(r"^[ \t]*(?:async\s+)?def\s+(\w+)\s*\([^)]*\)[^:\n]*:\s*(?:#[^\n]*)?\n(?:[ \t]*(?:#[^\n]*)?\n)*[ \t]+(?:pass|\.\.\.)[ \t]*(?:#[^\n]*)?$", text, re.M):
            add("empty_function", idx.line(m.start()), name=m.group(1))
        # function/class auth decorators (used to resolve Django url → view auth)
        for m in re.finditer(r"^((?:[ \t]*@[^\n]+\n)*)[ \t]*(?:async\s+)?def\s+(\w+)", text, re.M):
            state["py_defs"][m.group(2)].append({"file": rel, "line": idx.line(m.start(2)), "auth": bool(AUTH_RE.search(m.group(1)))})
        for m in re.finditer(r"^((?:[ \t]*@[^\n]+\n)*)[ \t]*class\s+(\w+)\s*\(([^)]*)\)", text, re.M):
            state["py_defs"][m.group(2)].append({"file": rel, "line": idx.line(m.start(2)), "auth": bool(AUTH_RE.search(m.group(1) + m.group(3)))})

    # ---- project-level flags
    fl = state["flags"]
    if re.search(r"['\"]stripe['\"]|^\s*import\s+stripe|new\s+Stripe\(|\\Stripe\\", text, re.M):
        fl["stripe"].append(rel)
    if re.search(r"constructEvent|construct_event", text):
        fl["stripe_verify"].append(rel)
    if re.search(r"razorpay", text, re.I):
        fl["razorpay"].append(rel)
    if re.search(r"validateWebhookSignature|verifyPaymentSignature|verify_payment_signature|verify_webhook_signature|createHmac|hmac\.new", text):
        fl["razorpay_verify"].append(rel)
    for i, l in enumerate(lines, 1):
        if re.search(r"webhook", l, re.I):
            fl["webhook_lines"].append((rel, i))
            break

    # ---- routes
    extract_routes(f, text, lines, idx, state)
    if len(state["routes"]) > has_routes_before:
        state["route_files"].add(rel)

    # ---- data models
    extract_models(f, text, idx, state)

    # ---- imports
    state["imports"][rel] = extract_imports(f, text)


def route_auth(lines, line_no, file_text):
    window = "\n".join(lines[max(0, line_no - 4): line_no])
    if AUTH_RE.search(window):
        return "yes"
    if re.search(r"\.use\(\s*[\w.]*(auth|protect|guard|jwt|session|requireUser|verifyToken)", file_text, re.I):
        return "file-level"
    return "no"


def extract_routes(f, text, lines, idx, state):
    rel, ext = f["rel"], f["ext"]
    routes = state["routes"]

    def push(method, path, line_no, fw, auth=None, handler=None):
        r = {"method": method, "path": path, "file": rel, "line": line_no, "framework": fw,
             "auth_hint": auth if auth is not None else route_auth(lines, line_no, text)}
        if handler:
            r["handler"] = handler
        routes.append(r)

    js = ext in ("js", "jsx", "ts", "tsx", "mjs", "cjs")
    if js:
        for m in re.finditer(r"\b(\w*[Rr]outer|app|server|routes?|fastify|instance)\.(get|post|put|patch|delete|all|use|options|head)\(\s*['\"`]([^'\"`]+)['\"`]", text):
            ln = idx.line(m.start())
            rest_of_call = text[m.end(): m.end() + 200].split("\n")[0]
            push(m.group(2).upper(), m.group(3), ln, "express-style", "yes" if AUTH_RE.search(rest_of_call) else None)
        idents = dict(re.findall(r"(?:const|let|var)\s+(\w+)\s*=\s*require\(\s*['\"]([^'\"]+)['\"]\s*\)", text))
        idents.update(dict(re.findall(r"import\s+(\w+)\s+from\s+['\"]([^'\"]+)['\"]", text)))
        for m in re.finditer(r"\.use\(\s*['\"`]([^'\"`]+)['\"`]\s*,\s*((?:[\w.]+\s*(?:\([^)]*\))?\s*,\s*)*)(\w+)\s*\)", text):
            if m.group(3) in idents:
                state["mounts"].append({"file": rel, "prefix": m.group(1), "spec": idents[m.group(3)],
                                        "middleware_auth": bool(AUTH_RE.search(m.group(2)))})
        prefix = ""
        pm = re.search(r"@Controller\(\s*['\"`]([^'\"`]*)['\"`]", text)
        if pm:
            prefix = "/" + pm.group(1).strip("/")
        for m in re.finditer(r"@(Get|Post|Put|Patch|Delete|All)\(\s*(?:['\"`]([^'\"`]*)['\"`])?\s*\)", text):
            push(m.group(1).upper(), (prefix + "/" + (m.group(2) or "").strip("/")).rstrip("/") or "/", idx.line(m.start()), "nestjs")
        mm = re.search(r"(?:^|/)app/((?:[^/]+/)*)route\.[cm]?[jt]sx?$", rel)
        if mm:
            path = "/" + "/".join(p for p in mm.group(1).strip("/").split("/") if p and not p.startswith("("))
            file_auth = "yes" if AUTH_RE.search(text) else "no"
            for em in re.finditer(r"export\s+(?:async\s+)?(?:function|const)\s+(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\b", text):
                push(em.group(1), path, idx.line(em.start()), "nextjs-app", file_auth)
        mp = re.search(r"(?:^|/)pages/api/(.+)\.[jt]sx?$", rel)
        if mp:
            path = "/api/" + re.sub(r"/?index$", "", mp.group(1))
            push("ANY", path, 1, "nextjs-pages", "yes" if AUTH_RE.search(text) else "no")
        # UI pages
        up = re.search(r"(?:^|/)app/((?:[^/]+/)*)page\.[jt]sx?$", rel)
        if up:
            state["ui_pages"].append({"path": "/" + "/".join(p for p in up.group(1).strip("/").split("/") if p and not p.startswith("(")), "file": rel})
        up2 = re.search(r"(?:^|/)pages/(?!api/|_)(.+)\.[jt]sx?$", rel)
        if up2:
            state["ui_pages"].append({"path": "/" + re.sub(r"/?index$", "", up2.group(1)), "file": rel})
        if re.search(r"createBrowserRouter|<Routes|createRouter|RouterModule|VueRouter", text):
            for m in re.finditer(r"<Route\b[^>]*\bpath=[\"'`{]+([^\"'`}]+)|\bpath\s*:\s*['\"`]([^'\"`]*)['\"`]", text):
                state["ui_pages"].append({"path": m.group(1) or m.group(2) or "/", "file": rel, "line": idx.line(m.start())})
    elif ext == "py":
        for m in re.finditer(r"@(\w+)\.(get|post|put|patch|delete|route|api_route|websocket)\(\s*['\"]([^'\"]+)['\"]([^)]*)\)", text):
            method = m.group(2).upper()
            if method in ("ROUTE", "API_ROUTE"):
                ms = re.findall(r"['\"](GET|POST|PUT|PATCH|DELETE)['\"]", m.group(4), re.I)
                method = ",".join(x.upper() for x in ms) or "GET"
            ln = idx.line(m.start())
            after = "\n".join(lines[ln - 1: ln + 3])
            auth = "yes" if AUTH_RE.search(after) or AUTH_RE.search("\n".join(lines[max(0, ln - 4): ln])) else "no"
            push(method, m.group(3), ln, "flask/fastapi", auth)
        if rel.endswith("urls.py"):
            for m in re.finditer(r"\b(?:re_)?path\(\s*r?['\"]([^'\"]*)['\"]\s*,\s*([\w.]+(?:\.as_view\(\))?)", text):
                handler = m.group(2)
                push("ANY", "/" + m.group(1), idx.line(m.start()), "django", "unknown", handler)
    elif ext == "php":
        for m in re.finditer(r"Route::(get|post|put|patch|delete|any|match|resource|apiResource)\(\s*['\"]([^'\"]+)['\"]", text):
            push(m.group(1).upper(), m.group(2), idx.line(m.start()), "laravel")
    elif ext in ("java", "kt"):
        for m in re.finditer(r"@(Get|Post|Put|Delete|Patch|Request)Mapping\(\s*(?:value\s*=\s*|path\s*=\s*)?\{?\s*\"([^\"]*)\"", text):
            push("ANY" if m.group(1) == "Request" else m.group(1).upper(), m.group(2), idx.line(m.start()), "spring")
    elif ext == "rb" and rel.endswith("routes.rb"):
        for m in re.finditer(r"^\s*(get|post|put|patch|delete|resources?|root)\b\s*(?:to:\s*)?['\":]*([\w/:#-]*)", text, re.M):
            push(m.group(1).upper(), m.group(2), idx.line(m.start()), "rails")
    elif ext == "go":
        for m in re.finditer(r"\.(GET|POST|PUT|PATCH|DELETE|HandleFunc|Handle|Get|Post|Put|Patch|Delete)\(\s*\"([^\"]+)\"", text):
            push("ANY" if "Handle" in m.group(1) else m.group(1).upper(), m.group(2), idx.line(m.start()), "go")
    elif ext == "cs":
        for m in re.finditer(r"\[Http(Get|Post|Put|Delete|Patch)\(\s*\"([^\"]*)\"\s*\)\]|\.Map(Get|Post|Put|Delete|Patch)\(\s*\"([^\"]+)\"", text):
            push((m.group(1) or m.group(3)).upper(), m.group(2) or m.group(4), idx.line(m.start()), "aspnet")


MODEL_RULES = [
    ("prisma", lambda f: f["ext"] == "prisma", re.compile(r"^model\s+(\w+)\s*\{", re.M)),
    ("mongoose", lambda f: f["ext"] in ("js", "ts", "mjs", "cjs"), re.compile(r"mongoose\.model\(\s*['\"](\w+)['\"]|\bmodel\(\s*['\"](\w+)['\"]\s*,\s*\w+")),
    ("sequelize", lambda f: f["ext"] in ("js", "ts", "mjs", "cjs"), re.compile(r"sequelize\.define\(\s*['\"](\w+)['\"]|class\s+(\w+)\s+extends\s+Model\b")),
    ("entity", lambda f: f["ext"] in ("ts", "java", "kt"), re.compile(r"@Entity\([^)]*\)\s*(?:export\s+)?(?:public\s+)?(?:data\s+)?class\s+(\w+)")),
    ("drizzle", lambda f: f["ext"] in ("ts", "js"), re.compile(r"(?:pgTable|mysqlTable|sqliteTable)\(\s*['\"](\w+)['\"]")),
    ("python-orm", lambda f: f["ext"] == "py", re.compile(r"^class\s+(\w+)\s*\(\s*(?:models\.Model|db\.Model|Base|DeclarativeBase|SQLModel[^)]*table\s*=\s*True[^)]*|Document|AbstractUser|AbstractBaseUser)\s*\)", re.M)),
    ("eloquent", lambda f: f["ext"] == "php", re.compile(r"class\s+(\w+)\s+extends\s+(?:Model|Authenticatable)\b")),
    ("activerecord", lambda f: f["ext"] == "rb", re.compile(r"class\s+(\w+)\s*<\s*(?:ApplicationRecord|ActiveRecord::Base)")),
    ("sql", lambda f: f["ext"] == "sql", re.compile(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[`\"\[]?(\w+)", re.I)),
]


def extract_models(f, text, idx, state):
    for kind, when, rx in MODEL_RULES:
        if not when(f):
            continue
        for m in rx.finditer(text):
            name = next((g for g in m.groups() if g), None)
            if name:
                state["models"].append({"name": name, "kind": kind, "file": f["rel"], "line": idx.line(m.start())})


def extract_imports(f, text):
    ext, out = f["ext"], []
    if ext in ("js", "jsx", "ts", "tsx", "mjs", "cjs", "vue", "svelte"):
        out = re.findall(r"(?:import\s[^'\"]*?from\s*|import\s*\(\s*|require\(\s*|export\s[^'\"]*?from\s*|import\s+)['\"]([^'\"]+)['\"]", text)
        return [("js", s) for s in out]
    if ext == "py":
        res = []
        for m in re.finditer(r"^\s*from\s+([.\w]+)\s+import\s+\(?([\w, \t*]+)", text, re.M):
            res.append(("py", m.group(1), [n.strip().split(" as ")[0] for n in m.group(2).split(",") if n.strip()]))
        for m in re.finditer(r"^\s*import\s+([\w.]+)", text, re.M):
            res.append(("py", m.group(1), []))
        return res
    if ext == "php":
        return [("php", s) for s in re.findall(r"^\s*use\s+([\w\\]+)\s*;", text, re.M)]
    return out


# --------------------------------------------------------------------------- graph

def build_graph(files_by_rel, imports):
    fileset = set(files_by_rel)

    def try_ext(b):
        if b in fileset:
            return b
        for e in (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".vue", ".svelte"):
            if b + e in fileset:
                return b + e
        for e in ("/index.ts", "/index.tsx", "/index.js", "/index.jsx"):
            if b + e in fileset:
                return b + e
        m = re.match(r"^(.*)\.(js|jsx|mjs)$", b)
        if m:
            for e in (".ts", ".tsx", ".mts"):
                if m.group(1) + e in fileset:
                    return m.group(1) + e
        return None

    def resolve(src, imp):
        kind = imp[0]
        if kind == "js":
            spec = imp[1]
            if spec.startswith("."):
                return [try_ext(posixpath.normpath(posixpath.join(posixpath.dirname(src), spec)))]
            if spec.startswith("@/") or spec.startswith("~/"):
                for pre in ("src/", "", "app/"):
                    r = try_ext(pre + spec[2:])
                    if r:
                        return [r]
            return []
        if kind == "py":
            mod, names = imp[1], imp[2]
            if mod.startswith("."):
                dots = len(mod) - len(mod.lstrip("."))
                d = posixpath.dirname(src)
                for _ in range(dots - 1):
                    d = posixpath.dirname(d)
                rest = mod[dots:].replace(".", "/")
                bases = [posixpath.join(d, rest) if rest else d]
            else:
                p = mod.replace(".", "/")
                bases = [p, "src/" + p, posixpath.join(posixpath.dirname(src), p)]
            found = []
            j = lambda b, x: f"{b}/{x}" if b else x
            for b in bases:
                b = posixpath.normpath(b) if b else ""
                b = "" if b == "." else b
                hit_names = [j(b, n + ".py") for n in names if j(b, n + ".py") in fileset]
                if hit_names:
                    found += hit_names
                    break
                for cand in ((b + ".py") if b else None, j(b, "__init__.py")):
                    if cand and cand in fileset:
                        found.append(cand)
                        break
                if found:
                    break
            return found
        if kind == "php":
            p = imp[1].replace("\\", "/")
            for cand in (re.sub(r"^App/", "app/", p) + ".php", p + ".php", "src/" + p + ".php"):
                if cand in fileset:
                    return [cand]
        return []

    edges = set()
    for src, imps in imports.items():
        for imp in imps:
            for dst in resolve(src, imp):
                if dst and dst != src:
                    edges.add((src, dst))
    return edges


# --------------------------------------------------------------------------- git (read-only)

def _commit(c):
    d = {k: c[k] for k in ("hash", "date", "author", "subject")}
    d["files"] = c["files"][:8]
    return d


def git_facts(root):
    if run_git(root, ["rev-parse", "--is-inside-work-tree"]) is None:
        return None
    log = run_git(root, ["log", "-n", "400", "--date=short", "--pretty=format:@@%h|%ad|%an|%s", "--name-only"], timeout=60) or ""
    prefix = (run_git(root, ["rev-parse", "--show-prefix"]) or "").strip()
    commits, cur = [], None
    for line in log.splitlines():
        if line.startswith("@@"):
            h, d, a, s = (line[2:].split("|", 3) + ["", "", "", ""])[:4]
            cur = {"hash": h, "date": d, "author": a, "subject": s, "files": []}
            commits.append(cur)
        elif line.strip() and cur is not None:
            p = line.strip()
            if prefix:
                if not p.startswith(prefix):
                    continue
                p = p[len(prefix):]
            cur["files"].append(p)
    hot = Counter(p for c in commits for p in c["files"] if os.path.exists(os.path.join(root, p)))
    authors = defaultdict(lambda: {"commits": 0, "areas": Counter(), "last": ""})
    for c in commits:
        a = authors[c["author"]]
        a["commits"] += 1
        a["last"] = a["last"] or c["date"]
        for p in c["files"]:
            a["areas"][module_key(p)] += 1
    wip_re = re.compile(r"\b(wip|todo|temp|tmp|half|partial|in progress|draft|fixme|hack|stub|quick ?fix|not working|broken)\b", re.I)
    status = run_git(root, ["status", "--porcelain"]) or ""
    branches = run_git(root, ["for-each-ref", "--sort=-committerdate", "refs/heads", "--format=%(refname:short)|%(committerdate:short)|%(subject)"]) or ""
    first = (run_git(root, ["log", "--max-parents=0", "--format=%ad", "--date=short"]) or "").strip().splitlines()
    return {
        "current_branch": (run_git(root, ["rev-parse", "--abbrev-ref", "HEAD"]) or "").strip(),
        "commits_scanned": len(commits),
        "first_commit_date": first[-1] if first else None,
        "last_commit_date": commits[0]["date"] if commits else None,
        "recent_commits": [_commit(c) for c in commits[:25]],
        "wip_commits": [_commit(c) for c in commits if wip_re.search(c["subject"])][:20],
        "hotspots": [{"file": p, "changes": n} for p, n in hot.most_common(20)],
        "authors": sorted([{"name": n, "commits": v["commits"], "last_commit": v["last"],
                            "top_areas": [m for m, _ in v["areas"].most_common(4)]} for n, v in authors.items()],
                          key=lambda x: -x["commits"])[:15],
        "uncommitted_changes": [l for l in status.splitlines() if l.strip()][:100],
        "branches": [dict(zip(("name", "last_commit", "subject"), (b.split("|", 2) + ["", ""])[:3])) for b in branches.splitlines()[:20]],
    }


# --------------------------------------------------------------------------- main scan

def scan(root, use_git=True):
    root = os.path.abspath(root)
    if not os.path.isdir(root):
        raise SystemExit(f"Not a folder: {root}")
    has_git = use_git and run_git(root, ["rev-parse", "--is-inside-work-tree"]) is not None
    rels = list_files(root, has_git)
    C = Collector()
    state = {
        "env_documented": set(), "env_committed": [], "env_used": defaultdict(list),
        "integrations": defaultdict(lambda: {"category": "", "where": []}),
        "debug_logs": {}, "routes": [], "route_files": set(), "ui_pages": [], "models": [],
        "imports": {}, "py_defs": defaultdict(list), "mounts": [],
        "flags": defaultdict(list),
    }
    files, manifests, skipped_large, lockfiles = [], [], [], []
    lang_loc = Counter()
    for rel in rels:
        base = posixpath.basename(rel)
        full = os.path.join(root, rel)
        if base in LOCKFILES:
            lockfiles.append(rel)
            continue
        ext = base.rsplit(".", 1)[-1].lower() if "." in base else ""
        if ext in BINARY_EXT or base.endswith((".min.js", ".min.css")) or not os.path.isfile(full):
            continue
        try:
            size = os.path.getsize(full)
        except OSError:
            continue
        if size > MAX_FILE_BYTES:
            skipped_large.append({"file": rel, "bytes": size})
            continue
        try:
            with open(full, "rb") as fh:
                raw = fh.read()
        except OSError:
            continue
        if b"\0" in raw[:8000]:
            continue
        text = raw.decode("utf-8", "replace").replace("\r\n", "\n")
        if "eli5: ignore-file" in text[:600]:
            continue
        f = {"rel": rel, "ext": ext, "lang": LANG.get(ext), "is_test": bool(TEST_RE.search(rel)),
             "is_manifest": bool(is_manifest(rel)), "loc": 0}
        if f["is_manifest"]:
            m = parse_manifest(rel, text)
            if m:
                manifests.append(m)
        analyze_file(f, text, C, state)
        files.append(f)
        if f["lang"]:
            lang_loc[f["lang"]] += f["loc"]

    files_by_rel = {f["rel"]: f for f in files}
    code_files = [f for f in files if f["lang"] and f["lang"] not in NON_CODE_LANGS]

    # ---- stack
    all_deps = sorted({d for m in manifests for d in m["deps"]})
    frameworks = sorted({n for d in all_deps for rx, n in FRAMEWORKS if rx.search(d)})
    test_fw = sorted({n for d in all_deps for rx, n in TEST_FRAMEWORKS if rx.search(d)})
    pm = sorted({{"package-lock.json": "npm", "yarn.lock": "yarn", "pnpm-lock.yaml": "pnpm", "bun.lockb": "bun", "bun.lock": "bun",
                  "poetry.lock": "poetry", "Pipfile.lock": "pipenv", "uv.lock": "uv", "composer.lock": "composer",
                  "Gemfile.lock": "bundler", "Cargo.lock": "cargo", "go.sum": "go modules"}.get(posixpath.basename(l), "") for l in lockfiles} - {""})

    # ---- django route auth resolution
    for r in state["routes"]:
        if r["framework"] == "django" and r.get("handler"):
            name = r["handler"].replace(".as_view()", "").split(".")[-1]
            defs = state["py_defs"].get(name) or []
            app_dir = posixpath.dirname(r["file"])
            d = next((x for x in defs if posixpath.dirname(x["file"]) == app_dir), defs[0] if defs else None)
            if d:
                r["auth_hint"] = "yes" if d["auth"] else "no"
                r["view"] = f"{d['file']}:{d['line']}"

    # ---- express-style mount prefixes: app.use('/payments', paymentRoutes)
    fileset = set(files_by_rel)
    for mt in state["mounts"]:
        base = posixpath.normpath(posixpath.join(posixpath.dirname(mt["file"]), mt["spec"]))
        target = next((c for c in (base, base + ".js", base + ".ts", base + ".mjs", base + "/index.js", base + "/index.ts") if c in fileset), None)
        if not target:
            continue
        for r in state["routes"]:
            if r["file"] == target and r["framework"] == "express-style" and r["method"] != "USE" and "mounted_at" not in r:
                r["mounted_at"] = mt["prefix"]
                r["path"] = (mt["prefix"].rstrip("/") + "/" + r["path"].lstrip("/")).rstrip("/") or "/"
                if mt["middleware_auth"] and r["auth_hint"] == "no":
                    r["auth_hint"] = "mount-level"

    # ---- graph & modules
    edges = build_graph(files_by_rel, state["imports"])
    indeg = Counter(d for _, d in edges)
    mod_edges = Counter((module_key(s), module_key(d)) for s, d in edges if module_key(s) != module_key(d))
    modules = defaultdict(lambda: {"files": 0, "loc": 0, "languages": Counter(), "test_files": 0, "routes": 0, "sample_files": []})
    for f in files:
        if not f["lang"] or f["lang"] in NON_CODE_LANGS:
            continue
        m = modules[module_key(f["rel"])]
        m["files"] += 1
        m["loc"] += f["loc"]
        m["languages"][f["lang"]] += 1
        if f["is_test"]:
            m["test_files"] += 1
        if len(m["sample_files"]) < 6 and not f["is_test"]:
            m["sample_files"].append(f["rel"])
    for r in state["routes"]:
        modules[module_key(r["file"])]["routes"] += 1

    test_files = [f["rel"] for f in files if f["is_test"]]
    tested_modules = {module_key(d) for s, d in edges if files_by_rel.get(s, {}).get("is_test")}
    test_blob = " ".join(test_files).lower()
    for name in list(modules):
        leaf = name.split("/")[-1].lower()
        if leaf and leaf not in ("(root files)", "src", "app") and re.search(r"\b" + re.escape(leaf.rstrip("s")), test_blob):
            tested_modules.add(name)
    module_list = []
    for name, m in sorted(modules.items(), key=lambda kv: -kv[1]["loc"]):
        if m["files"] == 0:
            continue
        only_tests = m["test_files"] == m["files"]
        module_list.append({
            "name": name, "files": m["files"], "loc": m["loc"],
            "languages": [l for l, _ in m["languages"].most_common(3)],
            "routes": m["routes"], "test_files": m["test_files"], "is_test_module": only_tests,
            "has_tests": only_tests or name in tested_modules or m["test_files"] > 0,
            "depends_on": sorted({d for (s, d) in mod_edges if s == name}),
            "used_by": sorted({s for (s, d) in mod_edges if d == name}),
            "sample_files": m["sample_files"],
        })
    no_tests = [m["name"] for m in module_list if not m["has_tests"] and not m["is_test_module"] and m["name"] != "(root files)"]
    orphans = []
    if len(edges) >= 10:
        for f in code_files:
            if f["ext"] in ("js", "jsx", "ts", "tsx", "mjs", "cjs") and not f["is_test"] and indeg[f["rel"]] == 0 \
                    and not ENTRY_LIKE_RE.search(f["rel"]) and not f["rel"].endswith(".d.ts"):
                orphans.append(f["rel"])

    # ---- risk hints (raw + project level)
    risks = []
    for r in C.lists["risk_raw"]:
        if r["kind"] == "blocking_call" and r["file"] not in state["route_files"]:
            continue
        risks.append(r)
    fl = state["flags"]
    if fl["stripe"] and fl["webhook_lines"] and not fl["stripe_verify"]:
        f0, l0 = next(((f, l) for f, l in fl["webhook_lines"] if f in fl["stripe"]), fl["webhook_lines"][0])
        risks.append({"kind": "stripe_webhook_unverified", "file": f0, "line": l0,
                      "text": snippet(read_line(root, f0, l0)),
                      "note": "Stripe is used and webhooks are mentioned, but the signature is never checked (no constructEvent) - anyone could fake a 'payment succeeded' message"})
    if fl["razorpay"] and not fl["razorpay_verify"]:
        f0 = fl["razorpay"][0]
        risks.append({"kind": "razorpay_unverified", "file": f0, "line": 1, "text": "",
                      "note": "Razorpay is used but no payment/webhook signature verification was found"})
    for r in state["routes"]:
        sensitive = SENSITIVE_PATH_RE.search(r["path"]) or r["method"] in ("DELETE", "PUT", "PATCH")
        if r["auth_hint"] == "no" and r["method"] != "USE" and sensitive and not PUBLIC_PATH_RE.search(r["path"]):
            risks.append({"kind": "sensitive_route_no_auth_hint", "file": r.get("view", f"{r['file']}:{r['line']}").split(":")[0],
                          "line": int(r.get("view", f"{r['file']}:{r['line']}").split(":")[1]),
                          "text": f"{r['method']} {r['path']}",
                          "note": "Sensitive-looking route with no visible login/permission check nearby (confirm by reading the code)"})
    payment_ints = [n for n, v in state["integrations"].items() if v["category"] == "payments"]
    crit_no_tests = [m for m in no_tests if CRITICAL_RE.search(m)]
    if payment_ints and not test_files:
        risks.append({"kind": "payments_without_tests", "file": "", "line": 0, "text": ", ".join(payment_ints),
                      "note": "Money is handled but the project has no automated tests at all"})

    env_used = {k: sorted(set(v))[:6] for k, v in sorted(state["env_used"].items())}
    documented = sorted(state["env_documented"])
    has_example = bool(documented) or any(ENV_EXAMPLE_RE.search(f["rel"]) for f in files)

    readme = next((f["rel"] for f in files if re.match(r"(?i)readme(\.\w+)?$", f["rel"])), None)
    specs = [f["rel"] for f in files if f["ext"] in ("md", "mdx", "txt") and not f["rel"].lower().startswith(("node_modules", "changelog"))
             and re.search(r"(?i)prd|spec|requirement|plan|roadmap|feature|todo|architecture|design", posixpath.basename(f["rel"]))][:30]
    readme_sections = []
    if readme:
        txt = open(os.path.join(root, readme), encoding="utf-8", errors="replace").read()
        readme_sections = [h.strip() for h in re.findall(r"^#{1,3}\s+(.+)$", txt, re.M)][:40]

    root_pkg = next((m for m in manifests if m["type"] == "npm" and "/" not in m["file"]), None)
    makefile = files_by_rel.get("Makefile")
    make_targets = []
    if makefile:
        make_targets = re.findall(r"^([A-Za-z][\w-]*):(?!=)", open(os.path.join(root, "Makefile"), encoding="utf-8", errors="replace").read(), re.M)[:30]
    docker = [f["rel"] for f in files if re.search(r"(?i)(^|/)dockerfile[^/]*$", f["rel"])]
    compose = [f["rel"] for f in files if re.search(r"(^|/)(docker-)?compose[^/]*\.ya?ml$", f["rel"])]
    compose_services = []
    for c in compose[:3]:
        t = open(os.path.join(root, c), encoding="utf-8", errors="replace").read()
        sm = re.search(r"^services:\s*\n((?:[ \t]+.*\n?|\s*\n)*)", t, re.M)
        if sm:
            compose_services += re.findall(r"^  ([\w.-]+):\s*$", sm.group(1), re.M)

    entry_files = [f["rel"] for f in code_files if f["rel"].count("/") <= 2 and re.search(
        r"(^|/)(main|index|app|server|manage|wsgi|asgi|program|Program|Application)\.(py|js|ts|mjs|go|java|kt|cs|rb|php|dart)$", f["rel"])][:20]

    facts = {
        "tool": "eli5-repo", "version": VERSION,
        "generated_at": _dt.datetime.now().isoformat(timespec="seconds"),
        "project": os.path.basename(root),
        "stats": {
            "files_scanned": len(files), "code_files": len(code_files),
            "lines_of_code": sum(f["loc"] for f in code_files),
            "languages": dict(lang_loc.most_common(12)),
            "skipped_large_files": skipped_large[:20],
        },
        "stack": {"frameworks": frameworks, "test_frameworks": test_fw, "package_managers": pm,
                  "manifests": [dict({k: v for k, v in m.items() if k != "deps"}, dep_count=len(m["deps"])) for m in manifests][:30],
                  "dependencies": all_deps[:400]},
        "entrypoints": {
            "files": entry_files,
            "package_main": root_pkg.get("main") if root_pkg else None,
            "package_bin": root_pkg.get("bin") if root_pkg else None,
            "cron_jobs": C.lists["cron_jobs"][:30], "workers": C.lists["workers"][:30],
        },
        "modules": module_list[:60],
        "routes": state["routes"][:400],
        "route_count": len(state["routes"]),
        "ui_pages": state["ui_pages"][:200],
        "data": {
            "models": state["models"][:300],
            "migration_files": sum(1 for f in files if re.search(r"(^|/)migrations?/", f["rel"])),
        },
        "integrations": [{"name": n, **v} for n, v in sorted(state["integrations"].items(), key=lambda kv: (kv[1]["category"], kv[0]))],
        "env": {
            "used": env_used,
            "documented_in_example": documented,
            "has_example_file": has_example,
            "used_but_not_documented": [k for k in env_used if k not in state["env_documented"]],
            "documented_but_unused": [k for k in documented if k not in env_used],
            "env_files_committed": state["env_committed"],
        },
        "smells": {
            "todo": C.lists["todo"], "not_implemented": C.lists["not_implemented"],
            "empty_catch": C.lists["empty_catch"], "empty_function": C.lists["empty_function"],
            "placeholder": C.lists["placeholder"],
            "debug_logs": {"total": sum(state["debug_logs"].values()),
                           "top_files": [{"file": k, "count": v} for k, v in Counter(state["debug_logs"]).most_common(10)]},
            "large_files": [{"file": f["rel"], "loc": f["loc"]} for f in sorted(code_files, key=lambda x: -x["loc"]) if f["loc"] > 400][:20],
        },
        "secrets": C.lists["secrets"],
        "risk_hints": risks[:300],
        "tests": {
            "test_files": len(test_files), "frameworks": test_fw,
            "modules_without_tests": no_tests[:60],
            "critical_modules_without_tests": crit_no_tests,
            "sample_test_files": test_files[:15],
        },
        "graph": {
            "import_edges": len(edges),
            "module_edges": [{"from": s, "to": d, "imports": n} for (s, d), n in mod_edges.most_common(80)],
            "hub_files": [{"file": p, "imported_by": n} for p, n in indeg.most_common(15)],
            "possibly_unused_files": orphans[:50],
        },
        "docs": {"readme": readme, "readme_sections": readme_sections, "spec_like_files": specs},
        "run": {
            "package_scripts": (root_pkg or {}).get("scripts", {}),
            "other_scripts": {m["file"]: m["scripts"] for m in manifests if m["scripts"] and m is not root_pkg},
            "make_targets": make_targets, "dockerfiles": docker, "compose_files": compose,
            "compose_services": compose_services,
        },
        "git": git_facts(root) if has_git else None,
        "counts": dict(C.counts),
        "limits": {"list_limit": LIST_LIMIT, "note": "Lists are capped; 'counts' has the true totals."},
    }
    return facts


def read_line(root, rel, line_no):
    try:
        with open(os.path.join(root, rel), encoding="utf-8", errors="replace") as fh:
            for i, l in enumerate(fh, 1):
                if i == line_no:
                    return l
    except OSError:
        pass
    return ""


def summarize(facts, out_path):
    s, c = facts["stats"], facts["counts"]
    sev = Counter(r["kind"] for r in facts["risk_hints"])
    L = [
        f"ELI5 scan of '{facts['project']}': {s['files_scanned']} files, {s['code_files']} code files, {s['lines_of_code']:,} lines of code",
        "Languages: " + ", ".join(f"{k} ({v:,})" for k, v in list(s["languages"].items())[:6]),
        "Stack: " + (", ".join(facts["stack"]["frameworks"]) or "(not detected)"),
        "Tests: " + f"{facts['tests']['test_files']} test files" + (f" ({', '.join(facts['tests']['frameworks'])})" if facts["tests"]["frameworks"] else ""),
        "",
        f"Modules ({len(facts['modules'])}): " + ", ".join(f"{m['name']} [{m['files']}f]" for m in facts["modules"][:15]),
        f"Entry files: {', '.join(facts['entrypoints']['files'][:8]) or '-'}",
        f"Routes: {facts['route_count']}  |  UI pages: {len(facts['ui_pages'])}  |  Data models: {len(facts['data']['models'])} (+{facts['data']['migration_files']} migration files)",
        "Integrations: " + (", ".join(f"{i['name']} ({i['category']})" for i in facts["integrations"]) or "-"),
        "",
        "Hints to investigate (scanner only - confirm by reading code):",
        f"  TODO/FIXME: {c.get('todo', 0)}  | not-implemented: {c.get('not_implemented', 0)}  | empty functions: {c.get('empty_function', 0)}"
        f"  | swallowed errors: {c.get('empty_catch', 0)}  | placeholder/mock data: {c.get('placeholder', 0)}",
        f"  Possible secrets in code: {c.get('secrets', 0)}  | env files committed: {len(facts['env']['env_files_committed'])}"
        f"  | env vars used but undocumented: {len(facts['env']['used_but_not_documented'])}",
        "  Risk hints: " + (", ".join(f"{k} x{v}" for k, v in sev.most_common()) or "none"),
        f"  Modules without tests: {len(facts['tests']['modules_without_tests'])}"
        + (f" (critical: {', '.join(facts['tests']['critical_modules_without_tests'])})" if facts['tests']['critical_modules_without_tests'] else ""),
        f"  Possibly unused files: {len(facts['graph']['possibly_unused_files'])}  | large files (>400 loc): {len(facts['smells']['large_files'])}",
    ]
    g = facts.get("git")
    if g:
        L += ["", f"History: branch {g['current_branch']}, {g['commits_scanned']} commits scanned, "
                  f"{g['first_commit_date']} -> {g['last_commit_date']}, {len(g['uncommitted_changes'])} uncommitted changes, "
                  f"{len(g['wip_commits'])} WIP-looking commits, authors: " + ", ".join(a["name"] for a in g["authors"][:5])]
    else:
        L += ["", "History: not available (not a repository, or --no-git)"]
    L += ["", f"Full facts: {out_path}"]
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser(description="ELI5 scanner: deterministic facts about a codebase (no AI, read-only).")
    ap.add_argument("repo", nargs="?", default=".")
    ap.add_argument("--out", help="output JSON path (default: <repo>/.eli5/facts.json)")
    ap.add_argument("--no-git", action="store_true", help="do not read version-control history")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args(argv)
    facts = scan(a.repo, use_git=not a.no_git)
    out = os.path.abspath(a.out or os.path.join(a.repo, ".eli5", "facts.json"))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(facts, fh, indent=1, ensure_ascii=False)
    if not a.quiet:
        print(summarize(facts, out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
