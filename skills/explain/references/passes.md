# How to write each section

The report is read by three kinds of people at once: a curious non-developer, a new teammate, and a senior engineer taking over. Each section serves all three through the depth layers.

## Story (`story`)
- **What it is, who it's for, and what state it's in**, in 3–6 sentences.
- The 🧒 version must make a 10-year-old nod: "This app is a cricket stadium where fans buy tickets for matches…"
- Include the honest headline: "Most of the stadium is built, but the ticket counter can be tricked and refunds don't exist yet."
- Source: README + routes + UI pages + models. If the README and the code disagree, trust the code and mention the gap.

## Theme map (`theme_map`)
- 6–14 rows, covering only parts that exist in *this* project.
- `part` is the generic role (Frontend, API/server, Auth, Database, Payments, Background jobs, Email, Cache, Tests, Config…).
- `real` is the concrete tech + where it lives ("Stripe · `src/routes/payments.js`").
- `is` is the theme thing, short and vivid. `why` is a one-line reason the analogy fits.
- Extra conventions are allowed: "a bug" = X, "a security hole" = Y, so findings can reuse them.

## Big picture (`architecture`)
- One Mermaid `flowchart LR` (or `TD`) with ≤20 nodes. Use theme+real labels: `PAY[Ticket counter · Stripe]`.
- Show users/clients → entry → main modules → data stores → external services.
- The explanation walks the diagram left to right.
- Evidence: the entry file + main wiring (e.g. where routers are mounted).

## Module cards (`modules`)
- Use the scanner's `modules` list as the starting point, but name cards by **what they do** ("Payments", "Orders"), not by folder.
- 4–20 cards, most important first. Merge tiny folders, and split a giant folder by responsibility.
- `status`, which must be honest:
  - `done`: works end to end as far as you can tell from code.
  - `partial`: some paths work; some are stubbed, mocked, TODO or missing pieces (say which in the text).
  - `stub`: exists in name only (empty handlers, mock data, `NotImplemented`).
  - `unknown`: you couldn't tell (say why).
- Each card: what it does, what it receives and returns, who it talks to (`depends_on`), and anything surprising.
- Evidence: 1–3 quotes showing the core of the module.

## Journeys (`journeys`)
- Pick the 2–7 flows that matter most to the product (sign up, log in, buy, post, search, admin action…).
- Trace each one **through the real code**: route → handler → service → model → external call → response.
- One step per hop. Each step has evidence.
- If a journey breaks mid-way (stub, missing auth, fake data), the step must say so: "⚠️ Here the story stops: refunds are an empty box."
- An optional `sequenceDiagram` helps for the 1–2 most important flows.

## Data (`data`)
- What is stored, in plain words, and how the pieces relate.
- `entities` should cover only the important models (≤12), each with a theme role.
- Mermaid `erDiagram` with only the key relationships.
- Mention gaps: no migrations, models that no code uses, a schema that doesn't match the code.

## Findings (`findings`)
See `health-checklist.md`. Order by severity and impact. Quality beats quantity: 12 solid findings are better than 40 noisy ones. Group repeated issues into one finding with several evidence items ("8 places swallow errors silently").

## Handover (`handover`)
Use the scanner's `git` section (hotspots, recent commits, WIP commits, uncommitted changes, branches, authors).
- `summary`: what was happening most recently, and what a newcomer should look at first.
- `in_progress`: half-done work. Signals include WIP-like commit messages, uncommitted changes, TODOs in recently changed files, stubs next to finished code, and stale branches. Each item needs evidence from the code.
- `people`: only names that appear in history, with the areas they touched most. Never invent people or guess roles.
- No history available → describe in-progress work from code signals only, and say history wasn't available.

## Run steps (`run`)
- Derive steps from manifests, package scripts, the Makefile, Docker/compose files and README.
- Each step has a `command` where applicable. Commands must be real ones from the project.
- `missing` lists what someone will trip on: env vars used but not documented (scanner `env.used_but_not_documented`), services needed (DB, Redis), missing README steps, no seed data.

## Glossary (`glossary`) & FAQ (`faq`)
- Glossary: 8–20 project-specific terms (domain words + tech names), each with a theme-language meaning and a real meaning.
- FAQ: 4–8 questions a new owner would ask. "Can it take real payments today?", "Is it safe to deploy?", "What should I fix first?", "Where do I add a new X?". Answer honestly, with evidence.

## Tone
- Warm, concrete, a bit playful, never condescending.
- Honest: the 🧒 layer must still say when something is broken.
- No filler, no marketing words, no "robust/seamless/leverages".
