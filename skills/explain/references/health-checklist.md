# Health checklist: "The Uncomfortable Truth"

The scanner gives **hints**. A finding only goes in the report after you have **read the code** and can quote it.

## Severity

| Severity | Use when | Examples |
|---|---|---|
| 🔴 `broken` | Doesn't work, or is exploitable / loses money or data **as written** | Webhook trusts unsigned payloads; route deletes data with no auth; feature button calls an empty handler; SQL injection |
| 🟠 `risky` | Works today but will hurt: security weakness, data-loss risk, scaling cliff | Hardcoded secrets; CORS `*` with credentials; N+1 queries on hot paths; no rate limit on login; amount trusted from client |
| 🟡 `unfinished` | Clearly half-built or placeholder | Mock data in an API; TODO in a core path; `NotImplementedError`; feature in README missing from code |
| 🔵 `cleanup` | Hygiene, maintainability, docs | Undocumented env vars; no tests for a module; dead files; huge files; debug logs |

## Confidence

- `verified`: you read the code and the problem is certain from it alone.
- `likely`: the code strongly suggests it, but something outside the code could change it (e.g. a proxy adds auth, config sets a limit).
- `guess`: a weak signal. Prefer to leave guesses out unless they're important. Say what would confirm it.

## What to hunt for (and how to confirm)

### Half-built features (`unfinished` / `broken`)
- Empty handlers or functions behind real routes/buttons → 🔴 if a user can reach it, 🟡 if not wired up.
- Handlers returning hardcoded/mock data (`mockTodos`, `fakeUsers`, `return [{...}]`).
- `TODO`/`FIXME` in core flows (payments, auth, checkout, saving data). TODOs in comments elsewhere are 🔵 at most.
- `NotImplementedError`, `throw new Error('not implemented')`, `501` responses.
- **Promised vs built**: features listed in README/specs/plan files that you can't find in code. Each missing feature is a 🟡 with evidence quoting the promise, plus a note that no implementation was found.

### Payments
- Webhook doesn't verify signatures (Stripe `constructEvent`, Razorpay HMAC, PayPal verify) → 🔴.
- Amount/price taken from the request body instead of computed server-side → 🔴 if it's charged, 🟠 if only stored.
- No idempotency (double charges on retry), no handling of failed/refunded events → 🟠.
- Test keys hardcoded, or live keys in code → 🟠/🔴.
- Refund/cancel paths missing or stubbed → 🟡.
- Order marked paid on the client side, or before payment confirmation → 🔴.

### Auth & permissions
- Sensitive routes (delete, admin, update, other users' data) without auth middleware/decorators → 🔴. Check the router-level `use(...)`, mount points, decorators, global middleware and framework config before claiming this.
- Missing ownership checks (any logged-in user can edit any record: IDOR) → 🔴.
- Hardcoded JWT secret, no expiry, tokens in localStorage with XSS risk → 🟠.
- Passwords stored or compared in plain text, weak hashing (md5/sha1) → 🔴.
- No rate limiting on login/OTP → 🟠.

### Security
- SQL/NoSQL injection: string-built queries with user input → 🔴.
- `eval`/`exec` on input, command injection, path traversal in file serving → 🔴.
- CORS `*` (worse with credentials), TLS verification disabled, debug mode on in prod settings → 🟠.
- Secrets committed in code or committed `.env` files → 🟠 (🔴 if they look live). **Quote the line with the masked value only.** For evidence, quote a nearby non-secret part of the line, such as `const stripe = new Stripe(`.
- File uploads without type/size limits → 🟠.

### Data
- N+1 queries (a query inside a loop over results) → 🟠 on hot paths.
- Unbounded queries (`find()`, `objects.all()`, `SELECT *` without pagination) on lists that grow → 🟠.
- Missing indexes on foreign keys / frequently filtered fields (when visible in the schema) → 🔵/🟠.
- Multi-step writes without a transaction (e.g. create order + decrement stock) → 🟠.
- Stock/balance updates prone to race conditions → 🟠.
- Models with no migrations, or a schema that doesn't match the code → 🟡.

### Reliability
- Swallowed errors: `catch {}`, `.catch(() => {})`, `except: pass` → 🟠 if they hide failures in core flows, 🔵 otherwise.
- External calls (HTTP, email, payment) without timeouts/retries, or awaited inside request handlers → 🟠.
- Fire-and-forget promises whose failure loses data (e.g. a receipt email silently dropped) → 🟠/🔵.
- No input validation on write endpoints → 🟠.

### Performance / bottlenecks
- Blocking calls in request paths (`readFileSync`, `execSync`, sync hashing, `time.sleep`) → 🟠.
- Heavy work inside loops, repeated identical queries, no caching on obviously hot reads → 🟠/🔵.
- Huge files / god modules that everything imports (scanner `hub_files`, `large_files`) → 🔵 (explain the risk).

### Tests
- Critical modules (payments, auth, orders) with no tests → 🟠.
- No tests at all → 🟠 (one finding, not one per module).

### Config & docs
- Env vars used but not in `.env.example` → 🔵 (one grouped finding, listing the names).
- No setup instructions, or wrong ones → 🔵.
- Possibly unused files (scanner `possibly_unused_files`) → 🔵 grouped, after spot-checking 2–3 of them.

### AI-generated leftovers
- Placeholder text (lorem ipsum, "Your Company"), duplicated near-identical files, sample data shipped as real, commented-out blocks, inconsistent patterns between modules → 🟡/🔵.

## Writing a finding

- `title_eli5`: ≤14 words, **understandable on its own in one read**: theme hook + real consequence. ✅ "Anyone can fake a 'payment done' message, and the shop believes it." ❌ "The radio call is never checked" (a riddle).
- `title`: precise and technical. "Stripe webhook does not verify signatures".
- `explain`: what is happening, at three depths **plus `plain`**: one or two everyday sentences saying exactly what can happen and to whom.
- `why_it_matters`: the real-world consequence (money lost, data leaked, users stuck, slow at 10k rows), with a `plain` line too.
- `fix`: concrete. The 🧠 layer names the API, pattern or file to change.
- `evidence`: the exact quote(s) that show the problem. For "missing X" findings, quote the place where X should be (e.g. the webhook handler that has no verification), and say in the text what is absent.

## Don'ts

- Don't report scanner hints you haven't confirmed.
- Don't pad the list with style nits.
- Don't claim "no auth" before checking router-level and global middleware.
- Don't put secret values in the report.
