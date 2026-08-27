"""System status panel — data-driven. Add ANY Statuspage-based service by URL.
Options:
  [[panels]] name="status"
  [[panels.services]] label="GitHub" url="https://www.githubstatus.com"
  [[panels.services]] label="Claude" url="https://status.claude.com"
  [[panels.services]] label="Your Service" url="https://status.example.com"
Reads <url>/api/v2/summary.json (the Statuspage standard). No auth."""
from __future__ import annotations
import json, urllib.request
from .base import Panel

DOT = {"none": "\U0001f7e2", "minor": "\U0001f7e1", "major": "\U0001f7e0",
       "critical": "\U0001f534", "maintenance": "\U0001f535", "unknown": "⚪"}

class Status(Panel):
    NAME = "status"
    CALLOUT = "info"
    TITLE = "System status"

    def _fetch(self, url):
        try:
            req = urllib.request.Request(url.rstrip("/") + "/api/v2/summary.json",
                                         headers={"User-Agent": "Mozilla/5.0 flight-deck"})
            d = json.loads(urllib.request.urlopen(req, timeout=12).read())
        except Exception:
            return None
        ind = d.get("status", {}).get("indicator", "unknown")
        incidents = [i.get("name", "") for i in d.get("incidents", []) if i.get("status") != "resolved"]
        return {"indicator": ind, "incidents": incidents}

    def render(self):
        services = self.ctx.opts.get("services", [])
        if not services:
            return None
        L = []
        for svc in services:
            st = self._fetch(svc["url"])
            if not st:
                L.append(f"- [{svc['label']}]({svc['url']}): ⚪ unknown")
                continue
            note = (" — " + "; ".join(st["incidents"])) if st["incidents"] else " — all operational"
            L.append(f"- [{svc['label']}]({svc['url']}): {DOT.get(st['indicator'],'⚪')} {st['indicator']}{note}")
        return L
