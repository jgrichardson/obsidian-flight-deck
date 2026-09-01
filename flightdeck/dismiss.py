"""Shared dismiss store: hide an item from the deck without acting on it.

Any panel can render a dismiss link by calling `link(scheme, item_id)` and
filtering its rows through `is_dismissed()`. Clicking the link should invoke
`flightdeck dismiss <id>`, which records the id here so the next refresh drops
that row.

Writes are locked and atomic: clicking several dismiss links at once fires
several processes, and an unlocked read-modify-write silently loses ids.
"""
from __future__ import annotations
import json, os

STORE = os.path.expanduser("~/.config/flightdeck/dismissed.json")


def _read():
    try:
        return set(str(x) for x in json.load(open(STORE)))
    except Exception:
        return set()


def is_dismissed(item_id) -> bool:
    return str(item_id) in _read()


def dismissed_ids() -> set:
    return _read()


def link(scheme, item_id) -> str:
    """Markdown for a dismiss link, or '' when no scheme is configured."""
    if not scheme:
        return ""
    return f"  <sub>[dismiss]({scheme}:{item_id})</sub>"


def add(ids) -> int:
    import fcntl
    os.makedirs(os.path.dirname(STORE), exist_ok=True)
    lock_path = STORE + ".lock"
    lock = open(lock_path, "w")
    fcntl.flock(lock, fcntl.LOCK_EX)
    try:
        cur = _read()
        cur.update(str(i).lstrip("#") for i in ids)
        tmp = STORE + ".tmp"
        json.dump(sorted(cur), open(tmp, "w"))
        os.replace(tmp, STORE)
        return len(cur)
    finally:
        fcntl.flock(lock, fcntl.LOCK_UN)
        lock.close()
