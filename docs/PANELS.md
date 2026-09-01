# Writing a panel

A panel is a small class that fetches data and returns markdown. ~30 lines.

```python
# flightdeck/panels/weather.py
from .base import Panel
import json, urllib.request

class Weather(Panel):
    NAME = "weather"          # the name you use in flightdeck.toml
    CALLOUT = "info"          # Obsidian callout type (tip/info/note/question/…)
    TITLE = "Weather"

    def render(self):
        # self.ctx.opts  -> this panel's [[panels]] options from the config
        # self.ctx.config, self.ctx.now  -> config + aware datetime
        city = self.ctx.opts.get("city", "SF")
        # ... fetch ...
        return [f"- {city}: 72°F, clear"]   # markdown lines, or None to omit the card
```

Register it:

```python
# flightdeck/panels/__init__.py
from .weather import Weather
REGISTRY[Weather.NAME] = Weather
```

Enable it:

```toml
[[panels]]
name = "weather"
city = "Denver"
```

## Conventions
- Return `None` from `render()` to omit the card entirely (e.g. not configured / no creds).
- Return markdown lines **without** the callout wrapper — `card()` adds it.
- Keep it stdlib-only (`urllib.request` for HTTP) so installs stay dependency-free.
- Read secrets with `from .. import creds; creds.get_secret("your_key")`.
- Tables render great in Obsidian; use them for lists of rows.

## Built-in panels to copy from
- `status.py` — data-driven list of endpoints (the simplest extensible pattern).
- `github_prs.py` — external API + tables + a per-row classifier.
- `waiting_on.py` — scans local markdown.
- `embed.py` — embeds an editable note.
- `decile_base.py` — talks to a Claude Code MCP server directly; a template for wiring any
  MCP-backed data source into a panel without a separate auth flow.
- `claude_quotas.py` — reads small JSON cache files instead of calling an API; a template for a
  panel backed by another local process (see `docs/CLAUDE_QUOTAS.md`).
- `activity_scan.py` — scans append-only log files with byte-offset checkpointing so repeated
  runs never reparse old data; a template for a panel backed by a growing local data source.
