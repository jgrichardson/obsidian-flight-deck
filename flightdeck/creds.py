"""Credential storage: macOS Keychain when available, else a 0600 file.
Never prints secret values."""
from __future__ import annotations
import json, os, subprocess, sys

FILE = os.path.expanduser("~/.config/flightdeck/credentials.json")

def _mac() -> bool:
    return sys.platform == "darwin"

def set_secret(name: str, value: str) -> None:
    if _mac():
        subprocess.run(["security", "add-generic-password", "-U", "-s", f"flightdeck-{name}",
                        "-a", os.environ.get("USER", "flightdeck"), "-w", value],
                       check=True, capture_output=True)
        return
    os.makedirs(os.path.dirname(FILE), exist_ok=True)
    d = _read_file()
    d[name] = value
    with open(FILE, "w") as f:
        json.dump(d, f)
    os.chmod(FILE, 0o600)

def get_secret(name: str) -> str | None:
    if _mac():
        r = subprocess.run(["security", "find-generic-password", "-s", f"flightdeck-{name}", "-w"],
                           capture_output=True, text=True)
        return r.stdout.strip() if r.returncode == 0 and r.stdout.strip() else None
    return _read_file().get(name)

def _read_file() -> dict:
    try:
        return json.load(open(FILE))
    except Exception:
        return {}
