"""Slack auth via browser session tokens (xoxc + xoxd). No app/admin approval needed.
See docs/AUTH.md for the two values to copy from app.slack.com DevTools."""
from __future__ import annotations
from .. import creds

def setup():
    xoxc = input("Slack xoxc- token (DevTools console): ").strip()
    xoxd = input("Slack xoxd- cookie (Application > Cookies > 'd'): ").strip()
    if xoxc.startswith("xoxc-") and xoxd.startswith("xoxd-"):
        creds.set_secret("slack_xoxc", xoxc); creds.set_secret("slack_xoxd", xoxd)
        print("Stored Slack tokens (read + draft only; never posts).")
    else:
        print("Those don't look right — skipped.")
