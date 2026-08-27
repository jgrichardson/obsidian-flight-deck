"""GitHub auth: store a token (classic or fine-grained, repo:read + PR read).
Easiest: `gh auth login` then this reuses the gh CLI automatically. Or paste a token."""
from __future__ import annotations
import shutil, subprocess
from .. import creds

def setup():
    if shutil.which("gh"):
        r = subprocess.run(["gh", "auth", "status"], capture_output=True, text=True)
        if r.returncode == 0:
            print("gh CLI is authenticated — panels will use it automatically. Nothing to store.")
            return
    tok = input("Paste a GitHub token (repo read + PR read): ").strip()
    if tok:
        creds.set_secret("github_token", tok)
        print("Stored GitHub token.")
