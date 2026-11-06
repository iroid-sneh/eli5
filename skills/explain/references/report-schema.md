# Report JSON schema

Write the report to `<repo>/.eli5/reports/<theme-slug>.json`. Here `theme-slug` is the theme in lowercase with non-alphanumerics replaced by `-`, for example `formula-1`.

## Building blocks

**Layered text.** Every explanation field is an object with three depths:

```json
{ "eli5": "Pure theme language. Short sentences.", "teammate": "Theme + real technical names.", "senior": "Plain technical, paths, trade-offs." }
```

A plain string is also accepted. It is shown at every depth, so use it only for things that don't change by depth.

**Evidence.** Every claim that states something about the code carries `evidence`:

```json
"evidence": [
  { "file": "src/routes/payments.js", "line_start": 19, "line_end": 24, "quote": "router.post('/webhook', async (req, res) => {" }
]
```

- `file` is relative to the repo root, with forward slashes.
- `quote` is copied **exactly** from the file: 1–3 lines, with whitespace differences allowed. It is the proof, so never paraphrase it.
- Use the smallest quote that proves the claim. One strong quote beats three weak ones.
- `verify.py` adds `status` to each evidence item and `unproven: true` to claims without valid proof. Never write those fields yourself.

## Full shape

```json
{
  "meta": {
    "project": "tiny-shop",
    "theme": "cricket",
    "generated_at": "2026-11-06T18:00:00",
    "default_depth": "eli5",
    "source_url_base": "https://github.com/OWNER/REPO/blob/main",   // optional: only if the user gave a URL
    "stats": { "files": 12, "lines_of_code": 140, "languages": ["JavaScript"], "frameworks": ["Express"] }
  },

  "story": { "eli5": "...", "teammate": "...", "senior": "..." },          // 3–6 sentences: what it is, who it's for, the state it's in

  "theme_map": [                                                           // 6–14 rows, reused everywhere
    { "part": "Payments", "real": "Stripe via src/routes/payments.js", "is": "The ticket counter", "why": "Real money turns into a seat at the match" }
  ],

  "architecture": {
    "explain": { "eli5": "...", "teammate": "...", "senior": "..." },
    "mermaid": "flowchart LR\n  U[Fans / app users] --> S[Server]\n  ...",
    "evidence": [ ... ]
  },

  "modules": [                                                             // 4–20 cards, most important first
    {
      "name": "Payments",
      "path": "src/routes/payments.js",
      "theme_role": "The ticket counter",
      "status": "partial",                                                 // done | partial | stub | unknown
      "explain": { "eli5": "...", "teammate": "...", "senior": "..." },
      "depends_on": ["Orders", "Stripe"],
      "evidence": [ ... ]
    }
  ],

  "journeys": [                                                            // 2–7 key flows, end to end
    {
      "title": { "eli5": "A fan buys a ticket", "teammate": "Checkout → payment → webhook", "senior": "POST /orders → POST /payments/checkout → Stripe webhook" },
      "summary": { "eli5": "...", "teammate": "...", "senior": "..." },
      "steps": [
        { "text": { "eli5": "...", "teammate": "...", "senior": "..." }, "evidence": [ ... ] }
      ],
      "mermaid": "sequenceDiagram\n  participant U as User\n  ..."        // optional
    }
  ],

  "data": {
    "explain": { "eli5": "...", "teammate": "...", "senior": "..." },
    "entities": [ { "name": "Order", "theme_role": "Scorecard", "explain": { ... }, "evidence": [ ... ] } ],
    "mermaid": "erDiagram\n  USER ||--o{ ORDER : places\n  ...",
    "evidence": [ ... ]
  },

  "findings": [                                                            // every real problem; see health-checklist.md
    {
      "id": "F1",
      "severity": "broken",                                                // broken | risky | unfinished | cleanup
      "confidence": "verified",                                            // verified (you read the code and it's certain) | likely | guess
      "category": "payments",                                              // payments | auth | security | data | performance | reliability | unfinished | tests | config | dead-code | docs
      "title_eli5": "Anyone can shout 'he paid!' and the ticket counter believes them",
      "title": "Stripe webhook does not verify signatures",
      "explain": { "eli5": "...", "teammate": "...", "senior": "..." },
      "why_it_matters": { "eli5": "...", "teammate": "...", "senior": "..." },
      "fix": { "eli5": "...", "teammate": "...", "senior": "Use stripe.webhooks.constructEvent(rawBody, sig, STRIPE_WEBHOOK_SECRET) with express.raw()." },
      "evidence": [ ... ]
    }
  ],

  "handover": {
    "summary": { "eli5": "...", "teammate": "...", "senior": "..." },
    "in_progress": [
      { "title": "Refunds", "explain": { ... }, "files": ["src/routes/payments.js"], "evidence": [ ... ] }
    ],
    "people": [ { "name": "Asha", "areas": ["payments", "orders"], "last_active": "2026-10-30" } ]
  },

  "run": {
    "steps": [ { "text": { "eli5": "...", "teammate": "...", "senior": "..." }, "command": "npm install" } ],
    "missing": [ "STRIPE_WEBHOOK_SECRET is needed but not listed in .env.example" ]
  },

  "glossary": [ { "term": "Webhook", "eli5": "The umpire's radio call telling the scorer what just happened", "real": "An HTTP call another service makes to us when something happens" } ],

  "faq": [ { "q": "Can I take real payments with this today?", "a": { "eli5": "...", "teammate": "...", "senior": "..." }, "evidence": [ ... ] } ]
}
```

## Rules

- **JSON only**: no comments in the real file (the `//` notes above are for you), no trailing commas.
- Sections may be empty arrays or omitted when they truly don't apply (e.g. no `handover` without history).
  `story`, `theme_map`, `modules` and `findings` are always present.
- Mermaid: keep diagrams under ~20 nodes. Use simple ids (`A`, `PAY`) with labels in brackets: `PAY[Ticket counter / payments]`.
  Avoid parentheses, quotes and `;` inside labels; they break Mermaid.
- People in `handover.people` come only from the scanner's history data. Never invent names.
- **Never put a secret value in the report**, even a masked one beyond what the scanner printed.
