"""Install the CSS snippet that styles the deck + hides the Properties panel."""
from __future__ import annotations
import json, os

CSS = """/* Flight Deck — applies to notes with cssclasses: [flight-deck] */
.flight-deck { --file-line-width: 1050px; font-size: 1.05em; }
.flight-deck .callout { border-radius: 10px; padding: 12px 16px; margin-bottom: 16px; border-width: 2px; }
.flight-deck .callout-title { font-size: 1.12em; font-weight: 700; }
.flight-deck table { font-size: 0.97em; }
.flight-deck .metadata-container, .flight-deck .frontmatter-container,
.flight-deck .inline-title { display: none !important; }
"""

def install_css(vault: str) -> str | None:
    snip_dir = os.path.join(vault, ".obsidian", "snippets")
    os.makedirs(snip_dir, exist_ok=True)
    path = os.path.join(snip_dir, "flight-deck.css")
    open(path, "w").write(CSS)
    app = os.path.join(vault, ".obsidian", "appearance.json")
    try:
        d = json.load(open(app)) if os.path.isfile(app) else {}
    except Exception:
        d = {}
    sn = d.get("enabledCssSnippets") or []
    if "flight-deck" not in sn:
        sn.append("flight-deck"); d["enabledCssSnippets"] = sn
        json.dump(d, open(app, "w"), indent=2)
    return path
