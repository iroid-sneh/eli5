#!/usr/bin/env python3
"""
ELI5 renderer: turns a report JSON into a single self-contained HTML page + Markdown. Uses no AI.

Every report in the same reports/ folder is re-rendered so the theme switcher
in each page lists all themes generated so far.

Output (default out-dir = the .eli5 folder that holds reports/):
    <out>/<theme-slug>.html     one page per theme
    <out>/<theme-slug>.md       Markdown version (renders on GitHub, Mermaid included)
    <out>/index.html            copy of the page for the report you just rendered
    <out>/README.eli5.md        copy of the Markdown for that report

Usage:
    python3 render.py REPORT.json [--out-dir DIR] [--root REPO]
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "..", "assets", "template.html")
PASS = {"verified", "relocated", "fuzzy", None}
SEV = {"broken": "🔴 Broken", "risky": "🟠 Risky", "unfinished": "🟡 Unfinished", "cleanup": "🔵 Cleanup"}
STATUS = {"done": "✅ Working", "partial": "🟡 Partly built", "stub": "🔴 Not really built", "unknown": "❔ Unclear"}


def slugify(s: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (s or "theme").lower()).strip("-")
    return s[:48] or "theme"


def layer(v, depth="eli5"):
    if v is None:
        return ""
    if isinstance(v, str):
        return v
    return v.get(depth) or v.get("teammate") or v.get("eli5") or v.get("senior") or ""


def cell(s) -> str:
    return str(s or "").replace("|", "\\|").replace("\n", " ")


def default_out_dir(report_path):
    d = os.path.dirname(os.path.abspath(report_path))
    return os.path.dirname(d) if os.path.basename(d) == "reports" else d


def guess_root(out_dir):
    return os.path.dirname(out_dir) if os.path.basename(out_dir) == ".eli5" else None


# --------------------------------------------------------------------------- markdown

def md_report(r, out_dir, root):
    M = r.get("meta", {})

    def link(e):
        lines = ""
        if e.get("line_start"):
            lines = f":{e['line_start']}" + (f"-{e['line_end']}" if e.get("line_end") and e["line_end"] != e["line_start"] else "")
        label = f"`{e.get('file')}{lines}`"
        if M.get("source_url_base"):
            anchor = f"#L{e['line_start']}" + (f"-L{e['line_end']}" if e.get("line_end") else "") if e.get("line_start") else ""
            return f"[{label}]({M['source_url_base'].rstrip('/')}/{e.get('file')}{anchor})"
        if root:
            rel = os.path.relpath(os.path.join(root, e.get("file", "")), out_dir).replace(os.sep, "/")
            anchor = f"#L{e['line_start']}" if e.get("line_start") else ""
            return f"[{label}]({rel}{anchor})"
        return label

    def evs(o):
        good = [e for e in (o or {}).get("evidence", []) if isinstance(e, dict) and e.get("status") in PASS]
        return ("\n\n📎 Proof: " + " · ".join(link(e) for e in good)) if good else ""

    def unproven(o):
        return " ⚠️ *(no proof found)*" if isinstance(o, dict) and o.get("unproven") else ""

    def layered(v):
        if isinstance(v, str) or v is None:
            return v or ""
        out = layer(v, "eli5")
        if v.get("plain"):
            out += f"\n\n> 👉 **In plain words:** {v['plain']}"
        extra = []
        if v.get("teammate") and v.get("teammate") != out:
            extra.append(f"<details><summary>🧑‍💻 Teammate version</summary>\n\n{v['teammate']}\n\n</details>")
        if v.get("senior"):
            extra.append(f"<details><summary>🧠 Senior version</summary>\n\n{v['senior']}\n\n</details>")
        return out + ("\n\n" + "\n".join(extra) if extra else "")

    o = []
    o.append(f"# 🧒 {M.get('project', 'This project')}, explained like you're 5")
    o.append(f"*Theme: **{M.get('theme', '?')}***" + (f" · generated {str(M.get('generated_at', ''))[:10]}" if M.get("generated_at") else ""))
    t = M.get("trust")
    if t:
        o.append(f"> **Trust score: {t['score']}%**: {t['proven']} of {t['claims']} claims are backed by real code (checked without AI).")
    else:
        o.append("> ⚠️ This report has not been verified yet.")
    o.append("\n## 📖 The story\n\n" + layered(r.get("story")))

    if r.get("theme_map"):
        o.append(f"\n## 🎭 The cast\n\n| Real part | In {cell(M.get('theme'))} it's… | Why |\n|---|---|---|")
        for x in r["theme_map"]:
            o.append(f"| **{cell(x.get('part'))}**{(' (`' + cell(x.get('real')) + '`)') if x.get('real') else ''} | {cell(x.get('is'))} | {cell(x.get('why'))} |")

    a = r.get("architecture")
    if a:
        o.append("\n## 🗺️ The big picture\n\n" + layered(a.get("explain")) + evs(a))
        if a.get("mermaid"):
            o.append(f"\n```mermaid\n{a['mermaid']}\n```")

    if r.get("modules"):
        o.append("\n## 🧩 The parts")
        for m in r["modules"]:
            o.append(f"\n### {m.get('name')} · {STATUS.get(m.get('status'), STATUS['unknown'])}{unproven(m)}")
            if m.get("theme_role"):
                o.append(f"**{m['theme_role']}**" + (f" · `{m['path']}`" if m.get("path") else ""))
            o.append("\n" + layered(m.get("explain")) + evs(m))

    if r.get("journeys"):
        o.append("\n## 🚶 Journeys")
        for j in r["journeys"]:
            o.append(f"\n### {layer(j.get('title'))}")
            if j.get("summary"):
                o.append(layer(j["summary"]))
            for i, s in enumerate(j.get("steps", []), 1):
                step = s if isinstance(s, dict) else {"text": s}
                good = [e for e in step.get("evidence", []) if isinstance(e, dict) and e.get("status") in PASS]
                o.append(f"{i}. {layer(step.get('text'))}{unproven(step)}" + (f" ({', '.join(link(e) for e in good)})" if good else ""))
            if j.get("mermaid"):
                o.append(f"\n```mermaid\n{j['mermaid']}\n```")

    d = r.get("data")
    if d and (d.get("explain") or d.get("entities")):
        o.append("\n## 📦 What it remembers\n\n" + layered(d.get("explain")) + evs(d))
        for e in d.get("entities", []):
            o.append(f"- **{e.get('name')}**" + (f" ({e['theme_role']})" if e.get("theme_role") else "") + f": {layer(e.get('explain'))}")
        if d.get("mermaid"):
            o.append(f"\n```mermaid\n{d['mermaid']}\n```")

    F = sorted(r.get("findings", []), key=lambda f: list(SEV).index(f.get("severity")) if f.get("severity") in SEV else 9)
    o.append("\n## 🚨 The uncomfortable truth")
    if F:
        counts = {k: sum(1 for f in F if f.get("severity") == k) for k in SEV}
        o.append(" · ".join(f"{SEV[k]}: **{v}**" for k, v in counts.items()))
        o.append("\n| # | Severity | What's wrong | Confidence |\n|---|---|---|---|")
        for i, f in enumerate(F, 1):
            o.append(f"| {i} | {SEV.get(f.get('severity'), f.get('severity'))} | {cell(f.get('title_eli5') or f.get('title'))} | {cell(f.get('confidence'))}{' ⚠️' if f.get('unproven') else ''} |")
        for i, f in enumerate(F, 1):
            o.append(f"\n### {i}. {SEV.get(f.get('severity'), '')}: {f.get('title_eli5') or f.get('title')}{unproven(f)}")
            if f.get("title") and f.get("title") != f.get("title_eli5"):
                o.append(f"*{f['title']}*")
            o.append("\n" + layered(f.get("explain")))
            if f.get("why_it_matters"):
                w = f["why_it_matters"]
                o.append("\n**Why it matters:** " + layer(w) + (f" *({w['plain']})*" if isinstance(w, dict) and w.get("plain") and w.get("plain") != layer(w) else ""))
            if f.get("fix"):
                o.append("\n**🛠 How to fix:** " + layer(f["fix"], "senior"))
            o.append(evs(f).strip())
    else:
        o.append("No problems were found.")

    h = r.get("handover")
    if h and (h.get("summary") or h.get("in_progress") or h.get("people")):
        o.append("\n## 🤝 Handover notes\n\n" + layered(h.get("summary")))
        if h.get("in_progress"):
            o.append("\n**Work left half-way:**")
            for w in h["in_progress"]:
                o.append(f"- **{layer(w.get('title'))}**: {layer(w.get('explain'))}{unproven(w)}" + evs(w).replace("\n\n", " "))
        if h.get("people"):
            o.append("\n| Person | Knows about | Last active |\n|---|---|---|")
            for p in h["people"]:
                o.append(f"| {cell(p.get('name'))} | {cell(', '.join(p.get('areas', [])))} | {cell(p.get('last_active'))} |")

    ru = r.get("run")
    if ru and (ru.get("steps") or ru.get("missing")):
        o.append("\n## ▶️ How to run it")
        for i, s in enumerate(ru.get("steps", []), 1):
            o.append(f"{i}. {layer(s.get('text'))}" + (f"\n   ```\n   {s['command']}\n   ```" if s.get("command") else ""))
        if ru.get("missing"):
            o.append("\n**Missing or unclear:**")
            o += [f"- {layer(m)}" for m in ru["missing"]]

    if r.get("glossary"):
        o.append(f"\n## 📚 Glossary\n\n| Word | In {cell(M.get('theme'))} words | What it really is |\n|---|---|---|")
        for g in r["glossary"]:
            o.append(f"| **{cell(g.get('term'))}** | {cell(g.get('eli5'))} | {cell(g.get('real'))} |")
    if r.get("faq"):
        o.append("\n## ❓ Questions people ask")
        for f in r["faq"]:
            o.append(f"\n**{f.get('q')}**\n\n{layer(f.get('a'))}{evs(f)}")
    o.append("\n---\n*Made with ELI5 Repo. Every 📎 link points at the exact code behind a claim.*\n")
    return "\n".join(o)


# --------------------------------------------------------------------------- html

def html_report(r, template):
    data = json.dumps(r, ensure_ascii=False)
    data = data.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    M = r.get("meta", {})
    title = f"{M.get('project', 'Project')} explained"
    title = title.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return template.replace("__TITLE__", title).replace("/*__ELI5_DATA__*/", data)


def load(p):
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def render(report_path, out_dir=None, root=None):
    out_dir = os.path.abspath(out_dir or default_out_dir(report_path))
    root = os.path.abspath(root) if root else guess_root(out_dir)
    os.makedirs(out_dir, exist_ok=True)
    with open(TEMPLATE, encoding="utf-8") as fh:
        template = fh.read()
    report_dir = os.path.dirname(os.path.abspath(report_path))
    paths = sorted(set(glob.glob(os.path.join(report_dir, "*.json"))) | {os.path.abspath(report_path)})
    reports = []
    for p in paths:
        try:
            r = load(p)
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(r, dict) or "meta" not in r or not r["meta"].get("theme"):
            continue
        reports.append((p, r))
    themes = [{"slug": slugify(r["meta"]["theme"]), "theme": r["meta"]["theme"], "file": slugify(r["meta"]["theme"]) + ".html"} for _, r in reports]
    written, current = [], None
    for p, r in reports:
        slug = slugify(r["meta"]["theme"])
        r["__themes"], r["__slug"] = themes, slug
        html = html_report(r, template)
        md = md_report(r, out_dir, root)
        for name, content in ((slug + ".html", html), (slug + ".md", md)):
            with open(os.path.join(out_dir, name), "w", encoding="utf-8") as fh:
                fh.write(content)
        written.append(slug)
        if os.path.abspath(p) == os.path.abspath(report_path):
            current = (html, md, r)
    if current is None:
        raise SystemExit(f"Could not render {report_path}: it needs a meta.theme field and valid JSON.")
    with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(current[0])
    with open(os.path.join(out_dir, "README.eli5.md"), "w", encoding="utf-8") as fh:
        fh.write(current[1])
    return out_dir, written, current[2]


def main(argv=None):
    ap = argparse.ArgumentParser(description="ELI5 renderer: report JSON -> HTML + Markdown (no AI).")
    ap.add_argument("report")
    ap.add_argument("--out-dir")
    ap.add_argument("--root", help="repo root (for relative code links in Markdown)")
    a = ap.parse_args(argv)
    out_dir, written, r = render(a.report, a.out_dir, a.root)
    if not r.get("meta", {}).get("trust"):
        print("⚠️  This report has not been verified. Run verify.py first so the Trust Score is shown.")
    slug = slugify(r["meta"]["theme"])
    print(f"Rendered {len(written)} theme(s): {', '.join(written)}")
    print(f"Open:      {os.path.join(out_dir, 'index.html')}")
    print(f"Markdown:  {os.path.join(out_dir, 'README.eli5.md')}")
    print(f"This theme: {os.path.join(out_dir, slug + '.html')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
