# ELI5 Repo — Plan (v2: Claude skill edition)

> **One line:** Point it at any codebase, pick the topic you love (cricket, battle-royale games, cars, superhero movies, phones, cooking...), and it explains the whole project in that world: what each part does, how data moves, and **what is broken, half-done or risky**, with proof for every claim.

**What changed in v2:**
- **The Claude skill/plugin is THE product.** Claude (inside Claude Code) does all the thinking, so there are no API keys and no extra cost.
- **The helper scripts are pure Python 3 standard library.** No `pip install`, no `npm install`, no build step. Python 3.8+ ships with macOS and Linux.
- **The tool never runs repository operations** (`git init`, `commit`, `push`, branch changes, etc.). The owner creates the repo and pushes it themselves. The scanner only *reads* the analysed project's history (`git log`, `git status`) for handover notes, and `--no-git` turns even that off.
- **A polished README.md** is part of the deliverable.

---

## 0. Why this can stand out (research, Nov 2026)

| Existing tool | What it does well | What it misses |
|---|---|---|
| DeepWiki / deepwiki-open | Wiki + diagrams for GitHub repos | Written for engineers. No analogies. Doesn't tell you what's broken or half-built |
| PocketFlow Tutorial-Codebase-Knowledge (~12k stars) | Turns a repo into a beginner tutorial | Generic tone, no chosen theme, no health report, no proof links |
| Code2Tutorial | Friendly onboarding docs | Coverage gaps, missing setup steps |
| ExplainThisRepo, fraction12/explain | Plain-English EXPLAIN.md | No themes, no "what's unfinished", no handover view |
| "eli5" / "explaining-code" skills | Analogies for **one** snippet | Don't cover a whole repo |
| "check-code-complete" / "completeness-review" skills | Find TODOs and stubs | Raw lists for engineers. No story, no context |
| Aider repo-map, codegraph, treesitter-mcp | Code graphs for LLMs | Infrastructure, not explanations for people |

**Our wedge, which no current tool combines:**
1. **Theme engine.** The whole project is explained in one world the user picks, and the analogy stays consistent.
2. **"The Uncomfortable Truth".** An honest list of what's broken, half-built, risky or slow.
3. **Proof for every claim.** Every claim carries `file:line` + a quote. A verifier with no AI in it checks them all and computes a Trust Score.
4. **Handover mode.** Shows what the last developer was in the middle of.
5. **Three depths in one report:** 🧒 ELI5 · 🧑‍💻 New teammate · 🧠 Senior.
6. **Free.** Runs inside Claude Code with zero dependencies.

---

## 1. Rules (non-negotiable)

- **No servers, no database, no paid services, no API keys.** Claude Code is the brain.
- **Zero dependencies:** Python 3.8+ standard library only.
- **Read-only on the analysed project.** The only thing written is the `.eli5/` output folder.
- **No repository operations by the tool or during development.** The owner handles the repo and pushes.
- **Output is static files** (one self-contained HTML + Markdown) that can be opened locally or hosted anywhere for free.
- **About 60% of the facts come from deterministic scanning** (routes, models, env vars, TODOs, stubs, secrets, risk patterns, tests, import graph, history). Claude then reads only what matters, which keeps token use low.

---

## 2. Product surfaces

1. **Claude Code plugin** (primary): `/eli5:explain cricket`. Installable from this repo as a plugin marketplace.
2. **Standalone skill**: copy `skills/explain/` into `~/.claude/skills/`, then run `/explain cricket`.
3. **Natural language** also works: "explain this repo like I'm 5 using Formula 1" triggers the skill automatically.
4. *(Later)* A GitHub Action to regenerate on merge, and a VS Code hover extension.

---

## 3. Tech stack

- **Brain:** Claude, via the skill instructions (`SKILL.md` + `references/`).
- **Scanner / verifier / renderer:** Python 3.8+ stdlib (`re`, `json`, `os`, `subprocess`, `difflib`, `html`).
- **Parsing:** curated regex detectors per framework (Express, Next.js, NestJS, FastAPI, Flask, Django, Laravel, Spring, Rails, Go, ASP.NET), plus import-graph resolution for JS/TS, Python and PHP.
- **Diagrams:** Mermaid (loaded from a CDN in the HTML; falls back to plain text offline; renders natively on GitHub in Markdown).
- **HTML report:** a single file with vanilla JS/CSS, a depth toggle, a theme switcher, dark mode, search and severity filters.
- **Tests:** Python `unittest` against fixture repos with planted problems.

---

## 4. Repo structure

```
eli5/
├─ .claude-plugin/
│  ├─ plugin.json            # plugin manifest (name: eli5)
│  └─ marketplace.json       # lets users add this repo as a marketplace
├─ skills/explain/           # THE skill (self-contained; can be copied standalone)
│  ├─ SKILL.md               # the brain: step-by-step workflow for Claude
│  ├─ scripts/
│  │  ├─ scan.py             # deterministic facts → .eli5/facts.json
│  │  ├─ verify.py           # proof checker → trust score
│  │  └─ render.py           # report JSON → HTML + Markdown
│  ├─ references/
│  │  ├─ passes.md           # how to write each section
│  │  ├─ health-checklist.md # what to hunt for + severity rules
│  │  ├─ report-schema.md    # exact JSON shape Claude must write
│  │  ├─ themes.md           # built-in theme maps
│  │  └─ verifier.md         # instructions for the red-finding verifier
│  └─ assets/template.html   # report UI
├─ agents/eli5-verifier.md   # plugin subagent that re-checks 🔴 findings
├─ fixtures/                 # tiny repos with planted problems (shop, blog, todo)
├─ examples/                 # pre-generated reports (marketing + regression)
├─ tests/                    # unittest suite
├─ README.md
├─ LICENSE
└─ plan.md
```

---

## 5. Theme engine

1. The user types **any** topic. Built-in packs (cricket, football, cars, racing, battle-royale, superhero movies, restaurant, smartphone, school, city) give hand-tuned starting maps. Any other topic is mapped on the fly.
2. Claude builds the **theme map** once: real part → theme thing → why. **Every section must reuse it.**
3. **Three layers per text** (🧒 / 🧑‍💻 / 🧠), and every analogy ends with an "In real code:" pointer.
4. **Text only.** Franchises are referenced by general concepts only: no logos, art or long quotes.
5. **Theme switching is cheap.** The technical analysis (senior layer, findings, evidence) is reused, and only the theme map plus the 🧒/🧑‍💻 text is rewritten.

---

## 6. Pipeline (inside the skill)

1. **Scan** with `scan.py`, which writes `.eli5/facts.json` and prints a compact summary.
2. **Read** the README, entrypoints, routes, models, integrations, and the files behind every scanner hint.
3. **Theme map.**
4. **Write the report JSON** (`.eli5/reports/<theme>.json`): story, theme map, architecture, modules, journeys, data, findings, handover, run steps, glossary, FAQ.
5. **Verify** with `verify.py`: check every evidence file, line range and quote, auto-fix shifted line numbers, mark unproven claims, and compute the Trust Score. Claude fixes the failures and re-runs it.
6. **Double-check 🔴 findings** with the `eli5-verifier` subagent (or inline when used as a standalone skill).
7. **Render** with `render.py`: produces `.eli5/<theme>.html`, `.eli5/<theme>.md`, `.eli5/index.html` and `.eli5/README.eli5.md`.
8. **Reply** with a 5-line summary in theme language plus the paths.

Large repos (>400 code files): split modules across up to 5 parallel read-only subagents, then merge their results.

### Health findings
Each finding has: an ELI5 title, a technical title, severity (🔴 broken / 🟠 risky / 🟡 unfinished / 🔵 cleanup), confidence (verified / likely / guess), evidence, why it matters, and a fix. The full checklist is in `references/health-checklist.md`. It covers payments, auth, data, reliability, secrets, performance, tests, dead code, AI leftovers and spec drift.

---

## 7. Build phases (status)

- [x] **Phase 1: Scanner** (`scan.py`). Stack, modules, routes (+ auth hints), UI pages, models, integrations, env, smells, secrets (masked), risk hints, tests, import graph, history, run hints, docs/specs.
- [x] **Phase 2: Skill + plugin**. `SKILL.md`, references, verifier agent, plugin + marketplace manifests.
- [x] **Phase 3: Verifier + renderer**. Trust Score, single-file HTML, Markdown, theme switcher.
- [x] **Phase 4: Fixtures + tests**. Planted problems are detected; verifier and renderer are tested.
- [x] **Phase 5: Example report + README**.
- [ ] **Phase 6: Real-world tuning**. Run on 10 well-known OSS repos and tune detectors and prompts for false positives.
- [ ] **Phase 7: Launch** (free). Gallery of famous repos × themes on GitHub Pages; Show HN, r/ClaudeAI, dev.to, Claude skill directories, awesome-claude-code lists.
- [ ] **Phase 8 (later)**. GitHub Action, VS Code hover, quiz mode, multi-language output, more frameworks.

---

## 8. Quality bar

- Every planted fixture problem is found by the scanner (covered by tests).
- Trust Score ≥ 95% on fixtures.
- A non-developer reading only the 🧒 layer can answer: what does it do, what are the main parts, what's broken?
- A re-run with a new theme reuses the analysis and rewrites only the text.

## 9. Risks

| Risk | Answer |
|---|---|
| AI makes things up | Evidence quotes + verifier + confidence labels + Trust Score |
| Analogy misleads | 3 depth layers + "In real code:" pointers |
| Huge repos | Scanner first, read only hinted files, parallel subagents |
| Secrets in output | Scanner masks all secret values; the report never contains them |
| Copyright on themes | Text-only, general concepts |

## Sources used for research
- https://github.com/topics/deepwiki-alternative
- https://bitovi.com/blog/comparing-ai-documentation-engines-deepwiki-vs-code2tutorial
- https://gittrend.io/repo/The-Pocket/PocketFlow-Tutorial-Codebase-Knowledge
- https://github.com/fraction12/explain
- https://pypi.org/project/explainthisrepo/0.5.2/
- https://www.skillsdirectory.com/skills/coldteadotai-eli5
- https://smithery.ai/skills/whoabuddy/check-code-complete
- https://serverascode.com/2025/07/22/finding-plotholes-in-ai-assisted-code.html
- https://openrouter.ai/blog/tutorials/free-llm-apis-compared/
