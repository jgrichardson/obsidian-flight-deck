"""Waiting-on panel — who owes you. Scans a directory tree of markdown files for
bullets under a heading containing 'waiting', or lines like 'WAITING ON <NAME>: ...'.
Options:
  [[panels]] name="waiting_on"
  source_dir = "~/claude-projects"   # scanned recursively for *.md
  people = ["Alice","Bob"]           # optional; only these names attributed"""
from __future__ import annotations
import os, re
from .base import Panel

class WaitingOn(Panel):
    NAME = "waiting_on"
    CALLOUT = "question"
    TITLE = "Waiting on"

    def render(self):
        src = os.path.expanduser(self.ctx.opts.get("source_dir", ""))
        if not src or not os.path.isdir(src):
            return None
        people = set(self.ctx.opts.get("people", []))
        by_person = {}
        for root, _dirs, files in os.walk(src):
            for fn in files:
                if not fn.endswith(".md"):
                    continue
                in_wait = False
                for line in open(os.path.join(root, fn), errors="ignore").read().split("\n"):
                    h = re.match(r"^#{1,6}\s+(.*)", line)
                    if h:
                        in_wait = "waiting" in h[1].lower(); continue
                    m = re.search(r"WAITING ON ([A-Z][A-Za-z /]+?)\s*:\s*(.+)", line)
                    if m:
                        self._add(by_person, people, m[1].title().strip(), m[2].strip())
                    elif in_wait:
                        b = re.match(r"^\s*[-*]\s+(.*)", line)
                        if not b or "~~" in b[1]:
                            continue
                        pm = re.match(r"^([A-Z][a-z]+(?:\s*/\s*[A-Z][a-z]+)*)\s*:\s*(.+)", b[1])
                        if pm:
                            self._add(by_person, people, pm[1], pm[2])
        if not by_person:
            return ["- nothing recorded"]
        L = []
        for name in sorted(by_person, key=lambda n: -len(by_person[n])):
            L.append(f"**{name}**")
            for t in by_person[name]:
                L.append(f"- {t}")
        return L

    def _add(self, by, people, who, text):
        for n in re.split(r"[/,]", who):
            n = n.strip()
            if not people or n in people:
                by.setdefault(n, []).append(text.strip())
