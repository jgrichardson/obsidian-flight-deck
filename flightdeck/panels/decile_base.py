"""Decile Base panel: posts in a shared channel that @mention you and you
haven't replied to, plus a recent-activity digest from teammates.

Talks directly to the `decilehub` MCP server over HTTP JSON-RPC — the same
server your `mcp__decilehub__*` Claude Code tools use. No separate setup: if
you already have that MCP server configured (ask your team lead), Flight Deck
finds its token in `~/.claude.json` automatically. Falls back to a token
stored via `creds.set_secret("decilehub_token", ...)` for anyone running
Flight Deck outside a Claude Code project.

This is also a template for wiring any other Claude-Code-configured MCP
server's data into a panel — see docs/PANELS.md.

Options (in flightdeck.toml):
  [[panels]] name="decile_base"
  channel = "Group Dev"        # channel to watch (default: "Group Dev")
  mention_limit = 12           # max unreplied mentions to show
  recent_hours = 24            # activity digest window
"""
from __future__ import annotations
import json, os, re, urllib.request
from .base import Panel
from .. import dismiss

ENDPOINT = "https://decilehub.com/mcp"


def _mcp_token():
    try:
        cfg = json.load(open(os.path.expanduser("~/.claude.json")))
    except Exception:
        cfg = {}
    scopes = [cfg.get("mcpServers", {})] + [
        pv.get("mcpServers", {}) for pv in (cfg.get("projects") or {}).values()
    ]
    for sc in scopes:
        if "decilehub" in sc:
            try:
                return sc["decilehub"]["headers"]["Authorization"]
            except Exception:
                pass
    from .. import creds
    tok = creds.get_secret("decilehub_token")
    return f"Bearer {tok}" if tok else None


def _rpc(auth, name, args):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                        "params": {"name": name, "arguments": args}}).encode()
    req = urllib.request.Request(ENDPOINT, data=body,
          headers={"Authorization": auth, "Content-Type": "application/json",
                   "Accept": "application/json, text/event-stream"})
    out = json.loads(urllib.request.urlopen(req, timeout=25).read())
    return json.loads(out["result"]["content"][0]["text"])


def _me(auth):
    """Current user's {id, first_name} — never hardcode a user id here."""
    who = _rpc(auth, "whoami", {})
    user = who.get("user", who)
    return user.get("id"), (user.get("first_name") or user.get("name") or "").split()[0]


class DecileBase(Panel):
    NAME = "decile_base"
    CALLOUT = "question"
    TITLE = "Base"

    def render(self):
        auth = _mcp_token()
        if not auth:
            return None  # not configured — omit the card, no error
        channel = self.ctx.opts.get("channel", "Group Dev")
        mlimit = int(self.ctx.opts.get("mention_limit", 12))
        rhours = int(self.ctx.opts.get("recent_hours", 24))

        try:
            my_id, my_name = _me(auth)
            items = _rpc(auth, "base_inbox", {}).get("items", [])
        except Exception:
            return None  # any API hiccup: omit rather than break the deck

        mention_re = re.compile(rf"@{re.escape(my_name)}\b", re.I) if my_name else None

        mentions = []
        if mention_re:
            gd = [i for i in items
                  if i.get("channel_name") == channel and mention_re.search(i.get("content", ""))][:mlimit]
            for it in gd:
                try:
                    post = _rpc(auth, "get_base_post", {"id": it["post_id"]})["post"]
                except Exception:
                    continue
                if any(r.get("user_id") == my_id for r in post.get("replies", [])):
                    continue
                author = post.get("user", {})
                who = (author.get("first_name", "") + " " + author.get("last_name", "")).strip()
                if dismiss.is_dismissed(it["post_id"]):
                    continue
                d_link = dismiss.link(self.ctx.opts.get("dismiss_scheme"), it["post_id"])
                mentions.append(f"- [{post.get('title','')[:80]}]({post.get('url','')}) — {who} ({len(post.get('replies', []))} replies){d_link}")

        import datetime
        cutoff = self.ctx.now - datetime.timedelta(hours=rhours)
        recent = []
        for it in items:
            if it.get("channel_name") != channel:
                continue
            if (it.get("user") or {}).get("id") == my_id:
                continue
            ca = it.get("created_at", "")
            try:
                if datetime.datetime.fromisoformat(ca.replace("Z", "+00:00")).astimezone() < cutoff:
                    continue
            except Exception:
                continue
            author = it.get("user") or {}
            who = (author.get("first_name", "") + " " + author.get("last_name", "")).strip()
            if dismiss.is_dismissed(it.get("post_id")):
                continue
            d_link = dismiss.link(self.ctx.opts.get("dismiss_scheme"), it.get("post_id"))
            recent.append(f"- {it.get('content','')[:100]} — {who}{d_link}")

        L = [f"**Mentions you owe a reply ({len(mentions)})**", ""]
        L += mentions if mentions else ["- none"]
        L += ["", f"**{channel} activity (last {rhours}h)**", ""]
        L += recent[:20] if recent else ["- nothing new"]
        return L
