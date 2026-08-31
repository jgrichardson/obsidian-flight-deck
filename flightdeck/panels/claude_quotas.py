"""Claude usage panel: 5-hour and weekly quota percentage per account.

Reads small JSON cache files written by a statusline script — see
docs/CLAUDE_QUOTAS.md for the ~10-line snippet that populates them. If no
cache files exist, the card is omitted entirely (no error, no setup step
required to use the rest of the deck).

Cache file shape, one per account, glob-matched:
  ~/.claude/usage-cache/<account>.json
  {"account": "personal", "five_hour_pct": 3.2, "week_pct": 41.0, "ts": "2026-08-31T18:05:00-0400"}

Options (in flightdeck.toml):
  [[panels]] name = "claude_quotas"
  week_floor = 0        # optional; clamp displayed week% to at least this value
  max_age_minutes = 0   # optional; hide a stale entry older than this (0 = never hide)
"""
from __future__ import annotations
import datetime, glob, json, os
from .base import Panel

CACHE_DIR = os.path.expanduser("~/.claude/usage-cache")


def _pct(v, floor=None):
    try:
        n = round(float(v))
    except Exception:
        return None
    return max(n, floor) if floor is not None else n


class ClaudeQuotas(Panel):
    NAME = "claude_quotas"
    CALLOUT = "info"
    TITLE = "Claude quotas"

    def render(self):
        files = sorted(glob.glob(os.path.join(CACHE_DIR, "*.json")))
        if not files:
            return None
        floor = self.ctx.opts.get("week_floor")
        max_age = int(self.ctx.opts.get("max_age_minutes", 0) or 0)
        lines = []
        for path in files:
            try:
                q = json.load(open(path))
            except Exception:
                continue
            account = q.get("account") or os.path.splitext(os.path.basename(path))[0]
            five = _pct(q.get("five_hour_pct"))
            week = _pct(q.get("week_pct"), floor=floor)
            age_min = None
            try:
                ts = datetime.datetime.fromisoformat(q["ts"])
                age_min = int((self.ctx.now - ts).total_seconds() // 60)
            except Exception:
                pass
            if max_age and age_min is not None and age_min > max_age:
                continue
            five_s = f"{five}%" if five is not None else "—"
            week_s = f"{week}%" if week is not None else "—"
            age_s = f"{age_min}m ago" if age_min is not None else "no timestamp"
            lines.append(f"- **{account}** — 5h `{five_s}` · wk `{week_s}`  <span style=\"opacity:.6\">{age_s}</span>")
        return lines or None
