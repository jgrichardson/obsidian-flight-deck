"""Panel plugin interface. A panel fetches data and renders markdown.
Add a panel: subclass Panel, set NAME, implement render(); register it in
flightdeck/panels/__init__.py REGISTRY. Enable it in flightdeck.toml [[panels]]."""
from __future__ import annotations
from dataclasses import dataclass

@dataclass
class Ctx:
    config: object          # flightdeck.config.Config
    opts: dict              # this panel's [[panels]] options
    now: object             # aware datetime

class Panel:
    NAME = "base"
    # Obsidian callout type for the card (tip/info/note/question/calendar/mail/abstract/pencil)
    CALLOUT = "note"
    TITLE = "Panel"

    def __init__(self, ctx: Ctx):
        self.ctx = ctx

    def render(self) -> list[str]:
        """Return markdown lines for the card body (WITHOUT the callout wrapper).
        Return [] to omit the card entirely (e.g. not configured)."""
        raise NotImplementedError

    def card(self) -> list[str]:
        body = self.render()
        if body is None:
            return []
        out = [f"> [!{self.CALLOUT}]+ {self.TITLE}"]
        for ln in body:
            out.append(ln if ln.startswith(">") else "> " + ln)
        out.append("")
        return out
