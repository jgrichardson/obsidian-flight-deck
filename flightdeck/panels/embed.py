"""Embed a standalone editable vault note as a card (used for Standup, Notes).
Options:
  [[panels]] name="embed" title="Standup" callout="tip" file="Flight Deck Standup Today.md"
The file is created empty on first run so the embed resolves."""
from __future__ import annotations
import os
from .base import Panel

class Embed(Panel):
    NAME = "embed"

    def render(self):
        self.CALLOUT = self.ctx.opts.get("callout", "pencil")
        self.TITLE = self.ctx.opts.get("title", "Notes")
        fn = self.ctx.opts.get("file")
        if not fn:
            return None
        path = os.path.join(self.ctx.config.vault, fn)
        if not os.path.exists(path):
            open(path, "w").write("- \n")
        base = fn[:-3] if fn.endswith(".md") else fn
        return [f"![[{base}]]"]
