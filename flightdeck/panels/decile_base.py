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
  refresh_minutes = 10         # reuse the last fetch for this long
  user_id = 123                # optional: skip `whoami` (needed with admin keys,
  first_name = "Greg"          #   which `whoami` rejects)

Flight Deck usually refreshes every couple of minutes, so this panel caches
what it fetches in ~/.config/flightdeck/decile-base-cache.json: your user and
the channel id are looked up once, the inbox is fetched at most once per
`refresh_minutes` and filtered to the watched channel server-side, and a
post's replies are only re-read when its reply count changes. If a fetch
fails, the last good data is shown instead of dropping the card.
"""
from __future__ import annotations
import json, os, re, time, urllib.request
from .base import Panel
from .. import dismiss

ENDPOINT = "https://decilehub.com/mcp"
CACHE_FILE = os.path.expanduser("~/.config/flightdeck/decile-base-cache.json")


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


def _channel_id(auth, name):
    for ch in _rpc(auth, "base_channels", {}).get("channels", []):
        if name in (ch.get("name"), ch.get("friendly_name")):
            return ch.get("id")
    return None


def _load_cache():
    try:
        return json.load(open(CACHE_FILE))
    except Exception:
        return {}


def _save_cache(cache):
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    tmp = CACHE_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(cache, f)
    os.replace(tmp, CACHE_FILE)


def _fetch(auth, channel, ttl, me=None):
    """Return (me_id, me_name, items, cache); network only when the cache is stale."""
    cache = _load_cache()
    if me:
        cache["me"] = list(me)
    elif not cache.get("me"):
        cache["me"] = list(_me(auth))
    if cache.get("channel") != channel or not cache.get("channel_id"):
        cache.update(channel=channel, channel_id=_channel_id(auth, channel), inbox=None, posts={})
    inbox = cache.get("inbox") or {}
    if time.time() - inbox.get("fetched_at", 0) >= ttl:
        args = {"per_page": 50}
        if cache["channel_id"]:
            args["channel_id"] = cache["channel_id"]
        try:
            items = _rpc(auth, "base_inbox", args).get("items", [])
            cache["inbox"] = {"fetched_at": time.time(), "items": items}
        except Exception:
            if not inbox:
                raise
    _save_cache(cache)
    me_id, me_name = cache["me"]
    return me_id, me_name, cache["inbox"]["items"], cache


def _post(auth, cache, item):
    """Post detail, re-read only when the item's reply count moved."""
    posts = cache.setdefault("posts", {})
    key, n = str(item["post_id"]), item.get("replies_count")
    hit = posts.get(key)
    if hit and n is not None and hit.get("n") == n:
        return hit["post"]
    post = _rpc(auth, "get_base_post", {"id": item["post_id"]})["post"]
    posts[key] = {"n": n, "post": {"title": post.get("title", ""), "url": post.get("url", ""),
                                   "user": post.get("user", {}),
                                   "replies": [{"user_id": r.get("user_id")} for r in post.get("replies", [])]}}
    return posts[key]["post"]


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

        ttl = 60 * float(self.ctx.opts.get("refresh_minutes", 10))

        try:
            me = None
            if self.ctx.opts.get("user_id") and self.ctx.opts.get("first_name"):
                me = (int(self.ctx.opts["user_id"]), str(self.ctx.opts["first_name"]))
            my_id, my_name, items, cache = _fetch(auth, channel, ttl, me)
        except Exception:
            return None  # any API hiccup with nothing cached: omit rather than break the deck

        mention_re = re.compile(rf"@{re.escape(my_name)}\b", re.I) if my_name else None

        mentions = []
        if mention_re:
            gd = [i for i in items
                  if i.get("channel_name") == channel and mention_re.search(i.get("content", ""))][:mlimit]
            for it in gd:
                try:
                    post = _post(auth, cache, it)
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

        try:
            live = {str(i.get("post_id")) for i in items}
            cache["posts"] = {k: v for k, v in cache.get("posts", {}).items() if k in live}
            _save_cache(cache)
        except Exception:
            pass

        L = [f"**Mentions you owe a reply ({len(mentions)})**", ""]
        L += mentions if mentions else ["- none"]
        L += ["", f"**{channel} activity (last {rhours}h)**", ""]
        L += recent[:20] if recent else ["- nothing new"]
        return L
