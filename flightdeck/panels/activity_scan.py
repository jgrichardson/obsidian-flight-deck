"""Detected-activity panel: surfaces things that look like they happened today,
scanned from your own Claude Code session transcripts. READ-ONLY by design --
it never writes into any standup note, it only lists candidates for you (or
Claude, when you ask it to prep your standup) to review and fold in by hand.

Claude Code writes an append-only transcript per session to
~/.claude/projects/<project-slug>/<session-id>.jsonl. This panel globs every
transcript across every project dir, seeks to a per-file checkpoint so it
never reparses the same bytes twice, and looks for two cheap signals:
  - a Bash tool_use command matching `gh pr merge` / `gh pr create` / `git push`
  - assistant text mentioning a PR number (#1234) near a verb like
    merged/shipped/opened/fixed/done

Entries never expire on their own -- they accumulate until explicitly marked
consumed (see mark_consumed()), so a Friday's activity is still visible on
Monday even if nobody looked at the deck over the weekend.

Options (in flightdeck.toml):
  [[panels]] name = "activity_scan"
  scan_dirs = ["~/.claude/projects/*"]   # glob patterns, default shown
  max_items = 20
"""
from __future__ import annotations
import glob, hashlib, json, os, re
from .base import Panel

DEFAULT_SCAN_GLOB = "~/.claude/projects/*"
STATE_FILE = os.path.expanduser("~/.config/flightdeck/activity-checkpoint.json")

PR_RE = re.compile(r"#(\d{2,6})\b")
VERB_RE = re.compile(r"\b(merged|shipped|opened|fixed|closed|done)\b", re.I)
CMD_RE = re.compile(r"\bgh pr (merge|create)\b|\bgit push\b")


def _load_state():
    try:
        return json.load(open(STATE_FILE))
    except Exception:
        return {"offsets": {}, "consumed": []}


def _save_state(state):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    tmp = STATE_FILE + ".tmp"
    json.dump(state, open(tmp, "w"))
    os.replace(tmp, STATE_FILE)


def _fingerprint(candidate):
    key = candidate.get("pr") or candidate["snippet"]
    return hashlib.sha1(key.encode()).hexdigest()[:16]


def _centered_snippet(text, match_pos, width=160):
    half = width // 2
    start = max(0, match_pos - half)
    end = min(len(text), match_pos + half)
    snippet = re.sub(r"\s+", " ", text[start:end]).strip()
    prefix = "…" if start > 0 else ""
    suffix = "…" if end < len(text) else ""
    return f"{prefix}{snippet}{suffix}"


def _extract_from_assistant_text(text, ts, cwd):
    vm = VERB_RE.search(text)
    pm = PR_RE.search(text)
    if not vm or not pm:
        return None
    return {"ts": ts, "cwd": cwd, "pr": pm.group(1), "snippet": _centered_snippet(text, pm.start())}


def _extract_from_bash(cmd, ts, cwd):
    cm = CMD_RE.search(cmd)
    if not cm:
        return None
    m = PR_RE.search(cmd)
    pr = m.group(1) if m else None
    return {"ts": ts, "cwd": cwd, "pr": pr, "snippet": _centered_snippet(cmd, cm.start())}


def scan(scan_globs, state):
    files = sorted({p for g in scan_globs for p in glob.glob(os.path.expanduser(os.path.join(g, "*.jsonl")))})
    offsets = state.setdefault("offsets", {})
    consumed = set(state.setdefault("consumed", []))
    candidates = []
    for path in files:
        try:
            size = os.path.getsize(path)
        except OSError:
            continue
        start = offsets.get(path, 0)
        if start > size:
            start = 0
        with open(path, "r", errors="ignore") as f:
            f.seek(start)
            for line in f:
                try:
                    d = json.loads(line)
                except Exception:
                    continue
                if d.get("type") != "assistant":
                    continue
                ts = d.get("timestamp", "")
                cwd = d.get("cwd", "")
                msg = d.get("message", {})
                for block in msg.get("content", []) or []:
                    cand = None
                    if block.get("type") == "text":
                        cand = _extract_from_assistant_text(block.get("text", ""), ts, cwd)
                    elif block.get("type") == "tool_use" and block.get("name") == "Bash":
                        cand = _extract_from_bash(block.get("input", {}).get("command", ""), ts, cwd)
                    if cand:
                        candidates.append(cand)
            offsets[path] = f.tell()
    seen = set()
    out = []
    for c in candidates:
        fp = _fingerprint(c)
        if fp in seen or fp in consumed:
            continue
        seen.add(fp)
        c["fp"] = fp
        out.append(c)
    return out, state


def mark_consumed(fingerprints):
    state = _load_state()
    consumed = set(state.setdefault("consumed", []))
    consumed.update(fingerprints)
    state["consumed"] = sorted(consumed)
    _save_state(state)


class ActivityScan(Panel):
    NAME = "activity_scan"
    CALLOUT = "note"
    TITLE = "Detected activity (unreviewed)"

    def render(self):
        scan_globs = self.ctx.opts.get("scan_dirs", [DEFAULT_SCAN_GLOB])
        max_items = int(self.ctx.opts.get("max_items", 20))
        state = _load_state()
        try:
            candidates, state = scan(scan_globs, state)
        except Exception:
            return None
        _save_state(state)
        if not candidates:
            return None
        candidates.sort(key=lambda c: c.get("ts", ""), reverse=True)
        L = ["*Not asserted fact -- check these against what actually happened.*", ""]
        for c in candidates[:max_items]:
            pr = f"#{c['pr']} · " if c.get("pr") else ""
            L.append(f"- {c.get('ts','')[:16]} — {pr}{c['snippet']}")
        return L
