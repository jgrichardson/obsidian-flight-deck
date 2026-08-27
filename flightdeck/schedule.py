"""Install an auto-refresh: launchd on macOS, cron elsewhere."""
from __future__ import annotations
import os, subprocess, sys, shutil

def install(config):
    minutes = int(config.raw.get("schedule", {}).get("every_minutes", 5))
    fd = shutil.which("flightdeck") or sys.executable + " -m flightdeck.cli"
    if sys.platform == "darwin":
        label = "com.flightdeck.refresh"
        plist = os.path.expanduser(f"~/Library/LaunchAgents/{label}.plist")
        log = os.path.expanduser("~/Library/Logs/flightdeck.log")
        open(plist, "w").write(f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>{label}</string>
  <key>ProgramArguments</key><array><string>/bin/zsh</string><string>-lc</string><string>{fd} run</string></array>
  <key>StartInterval</key><integer>{minutes*60}</integer>
  <key>RunAtLoad</key><true/>
  <key>StandardOutPath</key><string>{log}</string><key>StandardErrorPath</key><string>{log}</string>
</dict></plist>''')
        subprocess.run(["launchctl", "bootout", f"gui/{os.getuid()}/{label}"], capture_output=True)
        subprocess.run(["launchctl", "bootstrap", f"gui/{os.getuid()}", plist])
        print(f"launchd installed: refresh every {minutes} min. Log: {log}")
    else:
        line = f"*/{minutes} * * * * {fd} run >> ~/.flightdeck.log 2>&1"
        print("Add this to your crontab (`crontab -e`):\n  " + line)
