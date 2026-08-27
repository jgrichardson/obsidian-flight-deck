"""Slack drafts panel (read-only listing). Requires `flightdeck setup slack`.
Lists your unsent Slack drafts. This package never posts to Slack."""
from __future__ import annotations
import json, urllib.parse, urllib.request
from .base import Panel
from .. import creds

class SlackDrafts(Panel):
    NAME = "slack_drafts"; CALLOUT = "note"; TITLE = "Slack drafts"
    def render(self):
        xoxc, xoxd = creds.get_secret("slack_xoxc"), creds.get_secret("slack_xoxd")
        if not xoxc or not xoxd:
            return None
        try:
            body = urllib.parse.urlencode({"token": xoxc, "is_active": "true", "limit": "50",
                                           "_x_reason": "client-v2-boot-team", "_x_mode": "online"}).encode()
            req = urllib.request.Request("https://slack.com/api/drafts.list", data=body,
                  headers={"Cookie": f"d={xoxd}", "Content-Type": "application/x-www-form-urlencoded",
                           "User-Agent": "Mozilla/5.0"})
            drafts = json.loads(urllib.request.urlopen(req, timeout=20).read()).get("drafts", [])
        except Exception:
            return None
        if not drafts:
            return ["- none unsent"]
        L = []
        for d in drafts:
            txt = ""
            for b in d.get("blocks", []):
                for el in b.get("elements", []):
                    for e in el.get("elements", []):
                        if e.get("type") == "text":
                            txt += e.get("text", "")
            L.append(f"- {txt[:90] or '(empty)'}")
        return L
