"""Assemble enabled panels into the deck markdown and write it to the vault."""
from __future__ import annotations
import datetime, os
from .panels import REGISTRY, load_optional
from .panels.base import Ctx

def build(config) -> str:
    load_optional()
    now = datetime.datetime.now().astimezone()
    L = ["---", "cssclasses: [flight-deck]", "---", "",
         f"*{now:%a %Y-%m-%d %H:%M %Z} · derived*", ""]
    for spec in config.panels:
        name = spec.get("name")
        cls = REGISTRY.get(name)
        if not cls:
            L += [f"> [!warning]+ Unknown panel", f"> - `{name}` is not registered", ""]
            continue
        panel = cls(Ctx(config=config, opts=spec, now=now))
        try:
            L += panel.card()
        except Exception as e:
            L += [f"> [!warning]+ {getattr(panel,'TITLE',name)} (error)", f"> - {e}", ""]
    return "\n".join(L) + "\n"

def write(config) -> str:
    body = build(config)
    out = os.path.join(config.vault, config.deck_file)
    os.makedirs(config.vault, exist_ok=True)
    open(out, "w").write(body)
    return out
