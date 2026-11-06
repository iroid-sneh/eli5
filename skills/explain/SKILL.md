---
name: explain
description: Explain any codebase "like I'm 5" using a theme the user loves (cricket, cars, a battle-royale game, superhero movies, cooking, phones, anything). Produces an interactive HTML report + Markdown covering what the project does, its parts, user journeys, stored data, an honest health report of broken / half-built / risky / slow code with file:line proof for every claim, handover notes and setup steps. Use when the user asks to explain, understand, onboard onto, audit, review the state of, or take over a repo / project / codebase, or says "ELI5 this repo", "explain like I'm 5", "explain this project using <topic>".
argument-hint: "[theme] [path] [--depth eli5|teammate|senior] [--quick]"
---

# ELI5 Repo: explain a codebase in the user's favourite world

You turn an unfamiliar codebase into a story told in a theme the user loves, **without hiding the truth**: what works, what is half-built, what is broken, what is risky, with proof for every claim.

`SKILL_DIR` means the folder containing this SKILL.md (the base directory shown when the skill loaded).
Scripts are plain Python 3.8+ with no dependencies: `python3 "$SKILL_DIR/scripts/<name>.py"`. If `python3` is missing, try `python`.

Arguments given: `$ARGUMENTS`

## Hard rules

1. **Read-only.** Never modify the user's project. Write only inside `<repo>/.eli5/`.
2. **No repository operations.** Never run commands that change version-control state: no init, add, commit, push, pull, checkout, branch, stash or reset. The scanner reads history itself; you don't need to.
3. **Proof or it didn't happen.** Every claim about the code carries `evidence` with an exact quote. If you can't prove it, say "I couldn't confirm this" or leave it out.
4. **Honesty over niceness.** If payments are fake, auth is missing or a feature is a stub, say so plainly in the 🧒 layer too. Never soften a 🔴.
5. **One theme map, used everywhere.** Never mix metaphors.
6. **Never reveal secrets.** The scanner masks them. Don't open `.env` files to read values; refer to secrets by name and location only.
7. **The theme is a teaching tool, not decoration.** Every analogy must make the real thing *easier* to understand. If a sentence needs decoding, it has failed, so rewrite it. Each 🧒 explanation is followed by a plain-words line saying what really happens (see "Writing rules").

## Step 0: Parse the request

- **theme**: the first free-text words, e.g. `/eli5:explain formula 1`. If none was given, ask once, suggesting cricket, football, cars, a battle-royale game, superhero movies, cooking or smartphones. If the user doesn't care, use "a city".
- **path**: a folder argument if given, else the current working directory.
- **--depth**: the default tab in the report (`eli5` by default).
- **--quick**: smaller report (≤8 modules, ≤3 journeys, skip glossary and FAQ). Use it for a fast first look.
- If `<repo>/.eli5/reports/` already has a report for *another* theme, this is a **theme switch**. See "Theme switch" below.

Tell the user in one line what you're doing: "Scanning the project, then explaining it as cricket 🏏".

## Step 0.5: Learn the theme first (before touching the code)

You can't explain *in* a world you don't know well. Write a short **theme brief** for yourself before anything else:

1. **Pin down exactly what the user means.** "Suits" is the TV legal drama, "PUBG" is a specific battle-royale game, and "IPL" is a specific cricket league. If the name could mean two very different things and context doesn't settle it, ask once.
2. **Is it a specific world or a general topic?**
   - **Specific world** (a TV show, film or series, a game, a book, a league, a team, a band): you **must** use its real characters, places, objects and famous situations by name. "The managing partner" is wrong for Suits. **Jessica Pearson** is right.
   - **General topic** (cricket, cooking, cars, school): use the real vocabulary that people who love it use (DRS, third umpire, follow-on), not vague words.
3. **Collect the cast** (8–15 entries): main characters with **what they are famous for** (personality, job, signature habit), key places, iconic objects and well-known situations. Only use details a fan would immediately recognise. If you're unsure of a detail, look it up (WebSearch, if available) or leave it out. Never invent lore.
4. Use `references/themes.md` for built-in packs and the worked examples of how to cast a specific world.

Allowed: character, place and object names, roles, personalities, and famous situations described in your own words, plus a very short signature catchphrase at most. Not allowed: logos, images, lyrics, scripts or long quotes.

## Step 1: Scan (no AI, ~seconds)

```bash
python3 "$SKILL_DIR/scripts/scan.py" "<repo>"
```

This prints a compact summary and writes `<repo>/.eli5/facts.json`. Read the summary, then read the parts of `facts.json` you need. It contains stack, modules, entrypoints, routes (with `auth_hint`), UI pages, data models, integrations, env vars, smells (TODO, stubs, empty functions, swallowed errors, placeholders), masked secrets, `risk_hints`, tests, the import graph, history (hotspots, WIP commits, uncommitted changes, authors), docs and run hints.

**Scanner output is hints, not truth.** Every finding you report must be confirmed by reading the actual code.

## Step 2: Understand (read the code that matters)

Read in this order. Skim, don't read everything:
1. README, docs and any `spec_like_files` (these say what the project *promises*).
2. Entry files, and the route files for the main flows.
3. Models/schema files.
4. One or two files per integration (payments, auth, email, storage).
5. **Every file behind a scanner hint** you intend to report (risk_hints, stubs, not_implemented, secrets, routes with `auth_hint: "no"`).
6. Hotspot files and files touched by WIP commits or uncommitted changes (for handover).

**Big repos** (more than ~400 code files, or more than 60k lines): group modules into up to 5 batches and launch parallel **read-only** subagents (e.g. `Explore`). Give each one the module list, the relevant slice of facts.json, and the instructions in `references/passes.md` §Module cards and `references/health-checklist.md`. Ask them to return module cards + candidate findings as JSON with exact evidence quotes. Then merge and de-duplicate their results yourself.

## Step 3: Cast the project (build the theme map)

Map **only the parts this project actually has** (6–14 rows) to entries from your theme brief: real part → theme character/place/thing → why it fits.

**Casting rules:**
- **Cast by what the thing does, not by importance.** The match must teach something. Louis Litt is obsessed with billable hours, so he plays usage limits and billing: the reader instantly gets "counts and charges for every use". A character with no behavioural link teaches nothing.
- **One character or place per part, and the same one everywhere.** Never move a character to a new role mid-report.
- **The `why` names the trait that makes it fit**, e.g. "Donna knows everything and decides who gets to see Harvey, just like the router decides which code handles each request."
- **Keep the project's own names.** If the app has its own names (an AI persona, a product name), keep them and attach the cast role once, e.g. "Vela (the app's AI, played here by Harvey Specter)". Never let a project name and a theme name blur together.
- **Problems can be cast too**, using famous moments from the world. In Suits, a hidden betrayer inside the firm is Daniel Hardman; a secret that could bring the firm down is Mike's fake law degree. Use them only when the parallel is genuinely accurate.

## Step 4: Write the report JSON

Follow `references/report-schema.md` exactly. Follow `references/passes.md` for how to write each section and `references/health-checklist.md` for findings. Save to `<repo>/.eli5/reports/<theme-slug>.json` with the Write tool. Fill `meta.stats` from facts.json.

### Writing rules (these matter more than anything else)

Each explanation is a layered object: `{ "eli5", "plain", "teammate", "senior" }`.

- 🧒 **eli5**: the story in the theme. Sentences ≤15 words.
  - **One metaphor per idea, and never a metaphor for a metaphor.** ❌ "A mole hid in the firm's files and the safe combinations sit in a drawer." ✅ "Like Daniel Hardman secretly stealing from the firm, someone hid harmful code inside the login settings file. It ran for six months."
  - Use the cast by name. Say what the character *does* in this project, not only who they are.
- 👉 **plain**: **required on story, every module, and every finding's `explain`** (optional on `why_it_matters`, where it is shown as a short inline line). One or two sentences in everyday words with no theme and no jargon, saying what really happens to real people: "Anyone who knows the default admin password can open the admin panel and read every user's private chats." A parent who has never seen the show or the code must understand it.
- 🧑‍💻 **teammate**: plain English first, technical names second. Define every term the first time it appears. Max ~5 sentences. Explain how the pieces connect.
- 🧠 **senior**: no theme. Precise and technical; names the trade-offs and exact locations.

**Banned in eli5/plain:** vague quantity words ("some", "a few", "mostly", "various", "certain") when the real number or name is known; words like "issues", "stuff", "things", "well run" or "robust"; unexplained jargon; riddle titles. Use concrete facts: *how many*, *who* is affected, *what* happens.

**Titles** (`title_eli5`) must make sense on their own in one read: theme hook + real consequence. ❌ "The shredder skips the photo drawers." ✅ "When a user deletes their account, their photos are never deleted."

## Step 4.5: Clarity review (re-read before verifying)

Read only the 🧒 and 👉 text of the story, the module cards and the findings, imagining two readers: a 10-year-old fan of the theme who knows nothing about code, and a parent who has never seen the theme. Fix every sentence where:
- either reader would ask "what does that actually mean?"
- a metaphor is stacked on another metaphor
- a theme character is named but their role in *this* project isn't clear
- a vague word hides a known fact (a number, a name, a consequence)
- a 🔴/🟠 finding's plain line doesn't say who gets hurt and how

## Step 5: Verify the proof (no AI)

```bash
python3 "$SKILL_DIR/scripts/verify.py" "<repo>/.eli5/reports/<theme-slug>.json"
```

This checks every evidence quote against the real files, auto-corrects shifted line numbers, marks claims without proof as `unproven`, and computes the **Trust Score**. If it lists failed evidence, open those files, fix the quotes (or remove claims you can't prove), and run it again. Aim for ≥95%.

## Step 6: Double-check every 🔴 broken finding

For each `severity: "broken"` finding, get an independent check:
- In the plugin, launch the **`eli5-verifier`** subagent with the finding JSON and the repo path.
- Otherwise, launch a general-purpose subagent with the instructions in `references/verifier.md`, or do that check yourself if subagents aren't available.

Apply the verdicts:
- **rejected** → remove the finding or downgrade it.
- **downgrade** → change the severity.
- **confirmed** → keep it.

Re-run verify.py if you changed evidence.

## Step 7: Render

```bash
python3 "$SKILL_DIR/scripts/render.py" "<repo>/.eli5/reports/<theme-slug>.json"
```

This writes `<repo>/.eli5/index.html` (interactive: depth toggle, theme switcher, search, filters, dark mode), `<theme-slug>.html`, `<theme-slug>.md` and `README.eli5.md`.

## Step 8: Reply to the user

Keep it short and in the theme's voice:
- 2–3 sentence ELI5 story of the project.
- The top 3 problems (🔴/🟠), one line each, with `file:line`.
- Trust Score.
- How to open it: the path to `.eli5/index.html` (on macOS, offer `open <path>`).
- Optional: "Want it as another theme? Just say `/eli5:explain <theme>`."
- If `.eli5/` might be committed by accident, mention they can add `.eli5/` to their ignore file. Don't edit it yourself.

## Theme switch (cheap re-run)

If a report for another theme already exists and the code hasn't changed much:
1. Re-run the scan (fast) to confirm nothing big changed.
2. Load the existing report. **Keep** the `senior` text, statuses, findings (severity, confidence, evidence), journeys structure, run steps and handover facts.
3. Do Step 0.5 for the new theme, then **rewrite** only `theme_map`, every `eli5` and `teammate` text, `title_eli5`, `theme_role`, glossary `eli5`, and `meta.theme`. Keep the `plain` lines; they don't depend on the theme.
4. Save as a new `<new-theme-slug>.json`, then verify → render. The theme dropdown in the page will list both themes.

## Quality checklist (before rendering)

- [ ] A non-developer reading only 🧒 + 👉 can say what the app does, its main parts, and what's broken.
- [ ] For a specific show/game/film, the real characters and places are used by name, each cast for a matching trait.
- [ ] Story, every module and every finding have a `plain` line.
- [ ] No riddle titles, no stacked metaphors, no vague quantity words.
- [ ] Every finding has severity, confidence, evidence, why it matters, and a fix.
- [ ] Nothing in the report is invented: no made-up features, people, numbers or files.
- [ ] The theme map is used consistently everywhere.
- [ ] Module statuses are honest (`partial`/`stub` where true).
- [ ] No secret values anywhere.
