#!/usr/bin/env python3
"""
ELI5 proof checker: makes sure every claim in a report is backed by real code. Uses no AI.

For every object in the report that has an "evidence" list, each evidence item
{file, line_start, line_end, quote} is checked:
  verified   - the quote is found at (or within 3 lines of) the given lines
  relocated  - the quote exists elsewhere in the file; line numbers are corrected
  fuzzy      - at least 85% of the quote's words appear around the given lines
  not_found / missing_file / bad_path / no_quote - the evidence failed

A claim with no passing evidence is marked "unproven": true, and a health finding
is downgraded to confidence "guess". Writes the results back into the report
(or to --out) and prints a Trust Score.

Usage:
    python3 verify.py REPORT.json [--root REPO] [--out FILE]
    (if REPORT lives in <repo>/.eli5/..., --root defaults to <repo>)
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
import sys

PASS = {"verified", "relocated", "fuzzy"}


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip().lower()


def words(s: str):
    return [w for w in re.findall(r"[a-z0-9_]+", (s or "").lower()) if len(w) > 1]


def locate(lines, q, nq, lo, hi):
    """Exact 1-based (first, last) line span of normalised quote q within lines[lo:hi], or None."""
    width = nq + 2
    for i in range(lo, hi):
        if q in norm("\n".join(lines[i:min(hi, i + width)])):
            # slide the start forward while the quote still fits -> first line of the quote
            while i + 1 < hi and q in norm("\n".join(lines[i + 1:min(hi, i + 1 + width)])):
                i += 1
            # shrink the end -> last line of the quote
            for j in range(i + 1, min(hi, i + width) + 1):
                if q in norm("\n".join(lines[i:j])):
                    return i + 1, j
            return i + 1, min(hi, i + width)
    return None


def guess_root(report_path: str):
    p = os.path.abspath(report_path)
    parts = p.split(os.sep)
    if ".eli5" in parts:
        i = len(parts) - 1 - parts[::-1].index(".eli5")
        return os.sep.join(parts[:i]) or os.sep
    return os.getcwd()


class Checker:
    def __init__(self, root: str):
        self.root = os.path.realpath(root)
        self.cache = {}

    def lines(self, rel: str):
        if rel in self.cache:
            return self.cache[rel]
        full = os.path.realpath(os.path.join(self.root, rel))
        if not (full == self.root or full.startswith(self.root + os.sep)):
            self.cache[rel] = "bad_path"
        elif not os.path.isfile(full):
            self.cache[rel] = None
        else:
            with open(full, "rb") as fh:
                raw = fh.read(4_000_000)
            self.cache[rel] = raw.decode("utf-8", "replace").replace("\r\n", "\n").split("\n")
        return self.cache[rel]

    def check(self, ev: dict) -> str:
        rel = str(ev.get("file") or "").strip().replace("\\", "/")
        while rel.startswith("./"):
            rel = rel[2:]
        m = re.match(r"^(.*?):(\d+)(?:-(\d+))?$", rel)  # tolerate "src/a.js:12-14"
        if m and not ev.get("line_start"):
            rel, ev["line_start"] = m.group(1), int(m.group(2))
            if m.group(3):
                ev["line_end"] = int(m.group(3))
        if not rel or rel.startswith("/") or rel.startswith("../") or os.path.isabs(rel):
            return "bad_path"
        ev["file"] = rel
        lines = self.lines(rel)
        if lines == "bad_path":
            return "bad_path"
        if lines is None:
            return "missing_file"
        quote = ev.get("quote") or ""
        try:
            ls = int(ev.get("line_start") or ev.get("line") or 1)
        except (TypeError, ValueError):
            ls = 1
        try:
            le = int(ev.get("line_end") or ls)
        except (TypeError, ValueError):
            le = ls
        ls, le = max(1, ls), max(ls, le)
        if not norm(quote):
            return "no_quote" if ls <= len(lines) else "not_found"
        q = norm(quote)
        nq = max(1, quote.strip().count("\n") + 1)
        lo, hi = max(0, ls - 1 - 3), min(len(lines), max(le, ls + nq - 1) + 3)
        if q in norm("\n".join(lines[lo:hi])):
            span = locate(lines, q, nq, lo, hi)
            if span:
                ev["line_start"], ev["line_end"] = span
            return "verified"
        span = locate(lines, q, nq, 0, len(lines))
        if span:
            ev["line_start"], ev["line_end"] = span
            return "relocated"
        qw = words(quote)
        if qw:
            window = set(words("\n".join(lines[lo:hi])))
            if sum(1 for w in qw if w in window) / len(qw) >= 0.85:
                return "fuzzy"
        return "not_found"


def walk(node, path, out):
    if isinstance(node, dict):
        if isinstance(node.get("evidence"), list):
            out.append((path, node))
        for k, v in node.items():
            if k != "evidence":
                walk(v, f"{path}.{k}" if path else k, out)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            walk(v, f"{path}[{i}]", out)


def verify(report: dict, root: str):
    chk = Checker(root)
    claims = []
    walk(report, "", claims)
    failures, proven = [], 0
    for path, claim in claims:
        good = 0
        for j, ev in enumerate(claim["evidence"]):
            if not isinstance(ev, dict):
                claim["evidence"][j] = ev = {"file": str(ev), "status": "no_quote"}
                failures.append((f"{path}.evidence[{j}]", ev))
                continue
            ev["status"] = chk.check(ev)
            if ev["status"] in PASS:
                good += 1
            else:
                failures.append((f"{path}.evidence[{j}]", ev))
        if good:
            proven += 1
            claim.pop("unproven", None)
        else:
            claim["unproven"] = True
            if "severity" in claim:
                claim["confidence"] = "guess"
        if "severity" in claim and claim.get("confidence") == "verified" and not good:
            claim["confidence"] = "guess"
    total = len(claims)
    score = round(100 * proven / total) if total else 0
    report.setdefault("meta", {})["trust"] = {
        "claims": total, "proven": proven, "unproven": total - proven, "score": score,
        "evidence_checked": sum(len(c["evidence"]) for _, c in claims),
        "evidence_failed": len(failures),
        "checked_at": _dt.datetime.now().isoformat(timespec="seconds"),
    }
    return report, failures


def main(argv=None):
    ap = argparse.ArgumentParser(description="ELI5 proof checker (no AI).")
    ap.add_argument("report")
    ap.add_argument("--root", help="repo root that evidence paths are relative to")
    ap.add_argument("--out", help="write the verified report here instead of in place")
    a = ap.parse_args(argv)
    with open(a.report, encoding="utf-8") as fh:
        try:
            report = json.load(fh)
        except json.JSONDecodeError as e:
            print(f"ERROR: {a.report} is not valid JSON: {e}")
            return 2
    root = os.path.abspath(a.root or guess_root(a.report))
    report, failures = verify(report, root)
    out = a.out or a.report
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1, ensure_ascii=False)
    t = report["meta"]["trust"]
    print(f"Trust score: {t['score']}%  ({t['proven']} of {t['claims']} claims backed by real code; "
          f"{t['evidence_failed']} of {t['evidence_checked']} evidence items failed)")
    if failures:
        print("\nFailed evidence (fix the quote/lines, or remove the claim, then re-run):")
        for path, ev in failures[:60]:
            print(f"  - {path}: {ev.get('status')}  {ev.get('file')}:{ev.get('line_start')}  quote={json.dumps((ev.get('quote') or '')[:80])}")
        if len(failures) > 60:
            print(f"  ... and {len(failures) - 60} more")
    print(f"\nVerified report written to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
