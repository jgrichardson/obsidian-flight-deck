"""flightdeck — a config-driven Obsidian dashboard.

Commands:
  flightdeck init                 scaffold config + vault files + CSS
  flightdeck setup <service>      connect github | google | slack
  flightdeck run                  build the deck now
  flightdeck install-schedule     auto-refresh every N minutes (macOS launchd / cron)
  flightdeck doctor               check config + connections
  flightdeck standup-add <id>...  file a detected-activity item as a standup bullet
"""
from __future__ import annotations
import os, sys, shutil
from . import config as cfgmod

EXAMPLE_TOML = r"""# ── Flight Deck config ─────────────────────────────────────────────
# Copy to ~/.config/flightdeck/flightdeck.toml (or run `flightdeck init`).

[vault]
path = "~/Obsidian/MyVault"        # your Obsidian vault folder
deck_file = "00 Flight Deck.md"    # note the deck is written to

[schedule]
every_minutes = 5                  # auto-refresh interval

# ── Panels (ordered top → bottom). Delete any you don't want. ──────

[[panels]]
name = "embed"
title = "Standup"
callout = "tip"
file = "Flight Deck Standup Today.md"   # an editable note you curate

[[panels]]
name = "embed"
title = "My notes"
callout = "pencil"
file = "Flight Deck Notes.md"

[[panels]]
name = "status"
# Add ANY Statuspage-based service — not just these two.
[[panels.services]]
label = "GitHub"
url = "https://www.githubstatus.com"
[[panels.services]]
label = "Claude"
url = "https://status.claude.com"

[[panels]]
name = "waiting_on"
source_dir = "~/projects"          # scanned recursively for "Waiting on" items
# people = ["Alice", "Bob"]        # optional attribution filter

[[panels]]
name = "github_prs"
repos = ["your-org/your-repo"]
base_branch = "main"
active_projects = ["Billing", "Onboarding"]   # optional; else all labels show
[panels.github_prs.project_labels]            # optional regex -> project
"bill|invoice" = "Billing"
"onboard|signup" = "Onboarding"

[[panels]]
name = "decile_base"
channel = "Group Dev"

[[panels]]
name = "claude_quotas"

# Optional OAuth panels (uncomment after `flightdeck setup google/slack`):
# [[panels]]
# name = "calendar"
# [[panels]]
# name = "email"
# [[panels]]
# name = "slack_drafts"

# Read-only: surfaces PR/merge mentions found in your own Claude Code session
# transcripts, for you to review before writing your standup. Never writes to
# any note itself.
# [[panels]]
# name = "activity_scan"
# link_scheme = "fdstandup"          # renders a clickable +standup link per item
# standup_file = "Standup Today.md"  # where `flightdeck standup-add` files them
"""


def _init():
    if sys.platform == "darwin" and not os.path.isdir("/Applications/Obsidian.app"):
        print("Heads up: Obsidian.app not found in /Applications — Flight Deck writes into an Obsidian vault, so `flightdeck run` will no-op until you install it and set [vault] path to a real vault.")
    dst = cfgmod.DEFAULT_PATH
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if os.path.exists(dst):
        print(f"Config already exists at {dst}")
    else:
        open(dst, "w").write(EXAMPLE_TOML)
        print(f"Wrote example config to {dst} — edit it (set your vault path + repos).")
    print("Next: `flightdeck setup github`, then `flightdeck run`.")

def _setup(service):
    from .auth import github, google, slack
    {"github": github.setup, "google": google.setup, "slack": slack.setup}.get(service, lambda: print(
        "Unknown service. Use: github | google | slack"))()

def _run():
    from . import render, obsidian
    c = cfgmod.load()
    if not os.path.isdir(c.vault):
        print(f"No-op: vault not found at {c.vault} — check [vault] path in {c.path}, or install Obsidian and open this vault once.")
        return
    obsidian.install_css(c.vault)
    out = render.write(c)
    print(f"Wrote {out}")

def _schedule():
    from . import schedule
    schedule.install(cfgmod.load())

def _doctor():
    from . import doctor
    doctor.run(cfgmod.load())

def _standup_add(ids):
    from .panels import activity_scan
    c = cfgmod.load()
    opts = c.panel_opts("activity_scan")
    note = opts.get("standup_file")
    if not note:
        for p in c.panels:
            if p.get("name") == "embed" and "standup" in (p.get("title", "") or "").lower():
                note = p.get("file")
                break
    if not note:
        print("No standup note configured. Set standup_file on the activity_scan panel."); return
    path = note if os.path.isabs(note) else os.path.join(c.vault, note)
    added = activity_scan.add_to_standup(ids, path)
    if not added:
        print("nothing to add (already filed, or unknown id)"); return
    print(f"added to {path}:")
    for a in added:
        print(" ", a)

def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__); return
    cmd = args[0]
    if cmd == "init": _init()
    elif cmd == "setup" and len(args) > 1: _setup(args[1])
    elif cmd == "run": _run()
    elif cmd == "install-schedule": _schedule()
    elif cmd == "doctor": _doctor()
    elif cmd == "standup-add" and len(args) > 1: _standup_add(args[1:])
    else: print(__doc__)

if __name__ == "__main__":
    main()
