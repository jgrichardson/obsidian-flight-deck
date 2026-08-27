"""Load and validate flightdeck.toml."""
from __future__ import annotations
import os, tomllib
from dataclasses import dataclass, field

DEFAULT_PATH = os.path.expanduser("~/.config/flightdeck/flightdeck.toml")

@dataclass
class Config:
    raw: dict
    path: str

    @property
    def vault(self) -> str:
        return os.path.expanduser(self.raw["vault"]["path"])

    @property
    def deck_file(self) -> str:
        return self.raw["vault"].get("deck_file", "00 Flight Deck.md")

    @property
    def panels(self) -> list[dict]:
        # ordered list of {name, ...panel-specific options}
        return self.raw.get("panels", [])

    def panel_opts(self, name: str) -> dict:
        for p in self.panels:
            if p.get("name") == name:
                return p
        return {}

def load(path: str | None = None) -> Config:
    path = path or os.environ.get("FLIGHTDECK_CONFIG") or DEFAULT_PATH
    if not os.path.isfile(path):
        raise SystemExit(f"No config at {path}. Run `flightdeck init` first.")
    with open(path, "rb") as f:
        raw = tomllib.load(f)
    if "vault" not in raw or "path" not in raw.get("vault", {}):
        raise SystemExit("Config must have [vault] path = \"...\"")
    return Config(raw=raw, path=path)
