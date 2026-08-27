"""Sanity-check config + connections."""
from __future__ import annotations
import os
from . import creds

def run(config):
    print(f"config: {config.path}")
    print(f"vault:  {config.vault}  {'OK' if os.path.isdir(config.vault) else 'MISSING'}")
    print(f"panels: {', '.join(p.get('name','?') for p in config.panels)}")
    for svc in ("github_token", "google", "slack_xoxc"):
        print(f"  cred {svc}: {'set' if creds.get_secret(svc) else '—'}")
