"""Sanity-check config + actually probe each connection."""
from __future__ import annotations
import json, os, shutil, subprocess, urllib.request
from . import creds

def _ok(b): return "OK" if b else "FAIL"

def run(config):
    print(f"config: {config.path}")
    print(f"vault:  {config.vault}  [{_ok(os.path.isdir(config.vault))}]")
    print(f"panels: {', '.join(p.get('name','?') for p in config.panels)}")
    print("connections:")
    # GitHub
    gh = shutil.which("gh")
    gh_ok = bool(gh) and subprocess.run(["gh", "auth", "status"], capture_output=True).returncode == 0
    if not gh_ok:
        gh_ok = bool(creds.get_secret("github_token"))
    print(f"  github:   [{_ok(gh_ok)}] {'gh CLI / token' if gh_ok else 'run: flightdeck setup github'}")
    # Google
    g = creds.get_secret("google")
    g_ok = False
    if g:
        try:
            import urllib.parse
            c = json.loads(g)
            data = urllib.parse.urlencode({"client_id": c["client_id"], "client_secret": c["client_secret"],
                                           "refresh_token": c["refresh_token"], "grant_type": "refresh_token"}).encode()
            g_ok = "access_token" in json.loads(urllib.request.urlopen("https://oauth2.googleapis.com/token", data=data, timeout=15).read())
        except Exception:
            g_ok = False
    print(f"  google:   [{_ok(g_ok)}] {'token refreshes' if g_ok else 'run: flightdeck setup google (or not configured)'}")
    # Slack
    sc, sd = creds.get_secret("slack_xoxc"), creds.get_secret("slack_xoxd")
    s_ok = False
    if sc and sd:
        try:
            import urllib.parse
            body = urllib.parse.urlencode({"token": sc, "_x_mode": "online"}).encode()
            req = urllib.request.Request("https://slack.com/api/auth.test", data=body,
                  headers={"Cookie": f"d={sd}", "Content-Type": "application/x-www-form-urlencoded", "User-Agent": "Mozilla/5.0"})
            s_ok = json.loads(urllib.request.urlopen(req, timeout=15).read()).get("ok", False)
        except Exception:
            s_ok = False
    print(f"  slack:    [{_ok(s_ok)}] {'auth valid' if s_ok else 'run: flightdeck setup slack (or not configured)'}")
