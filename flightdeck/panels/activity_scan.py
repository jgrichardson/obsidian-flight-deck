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

A candidate with a PR number gets enriched with the real PR title and merge
state via `gh pr view` (run from the transcript's own cwd, so multi-repo work
resolves correctly); falls back to a raw text snippet when that lookup fails
or no PR number was found.

Entries never expire on their own -- they persist in a `pending` map in the
state file and are only removed when explicitly consumed, so a Friday's
activity is still visible on Monday even if nobody looked at the deck over
the weekend.

Set `link_scheme` to render a clickable "+standup" link per item. Clicking it
should invoke `flightdeck standup-add <fingerprint>`, which files that item as
a bullet at the END of your standup note (curated content above is never
touched) and marks it consumed. On macOS that means a tiny URL-handler app
registering the scheme; see docs/PANELS.md.

Options (in flightdeck.toml):
  [[panels]] name = "activity_scan"
  scan_dirs = ["~/.claude/projects/*"]   # glob patterns, default shown
  max_items = 20
  link_scheme = "fdstandup"              # omit to render no links
  standup_file = "Standup Today.md"      # vault-relative; target for standup-add
"""
from __future__ import annotations
import glob, hashlib, json, os, re, subprocess
from .base import Panel

STATE_WORD = {"MERGED": "merged", "OPEN": "open", "CLOSED": "closed"}


def _pr_info(pr, cwd):
    try:
        r = subprocess.run(["gh", "pr", "view", pr, "--json", "title,state"],
                           cwd=cwd or None, capture_output=True, text=True, timeout=10)
        if r.returncode != 0:
            return None
        d = json.loads(r.stdout)
        return {"title": d.get("title", ""), "state": STATE_WORD.get(d.get("state", ""), d.get("state", "").lower())}
    except Exception:
        return None

DEFAULT_SCAN_GLOB = "~/.claude/projects/*"
STATE_FILE = os.path.expanduser("~/.config/flightdeck/activity-checkpoint.json")

PR_RE = re.compile(r"#(\d{2,6})\b")
BARE_PR_RE = re.compile(r"\bgh pr (?:merge|view|close|comment|edit)\s+(\d{2,6})\b")
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
    m = PR_RE.search(cmd) or BARE_PR_RE.search(cmd)
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
    pending = state.setdefault("pending", {})
    for c in candidates:
        fp = _fingerprint(c)
        if fp in consumed or fp in pending:
            continue
        pending[fp] = {"ts": c.get("ts", ""), "cwd": c.get("cwd", ""),
                       "pr": c.get("pr"), "snippet": c.get("snippet", "")}
    for fp in list(pending):
        if fp in consumed:
            pending.pop(fp, None)
    out = [dict(v, fp=fp) for fp, v in pending.items()]
    return out, state


def mark_consumed(fingerprints):
    state = _load_state()
    consumed = set(state.setdefault("consumed", []))
    pending = state.setdefault("pending", {})
    consumed.update(fingerprints)
    for fp in fingerprints:
        pending.pop(fp, None)
    state["consumed"] = sorted(consumed)
    _save_state(state)


def add_to_standup(fingerprints, standup_path):
    """Turn detected items into standup bullets. Appends under a marked heading
    at the END of the note so curated content above is never touched, then marks
    them consumed. Returns the lines added."""
    state = _load_state()
    pending = state.get("pending", {})
    heading = "**Detected activity (added, not yet filed)**"
    added = []
    for fp in fingerprints:
        item = pending.get(fp)
        if not item:
            continue
        line = None
        if item.get("pr"):
            info = _pr_info(item["pr"], item.get("cwd"))
            if info and info.get("title"):
                line = f"- #{item['pr']} \u2014 {info['title']} ({info['state']})"
        if line is None:
            line = f"- {item.get('snippet', '')}".rstrip()
        added.append(line)
    if not added:
        return []
    body = ""
    if os.path.isfile(standup_path):
        body = open(standup_path, errors="ignore").read().rstrip("\n")
    if heading not in body:
        body += "\n\n" + heading
    body += "\n" + "\n".join(added)
    tmp = standup_path + ".tmp"
    open(tmp, "w").write(body + "\n")
    os.replace(tmp, standup_path)
    mark_consumed(fingerprints)
    return added


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
        cache = {}
        for c in candidates[:max_items]:
            info = None
            if c.get("pr"):
                key = (c["cwd"], c["pr"])
                if key not in cache:
                    cache[key] = _pr_info(c["pr"], c["cwd"])
                info = cache[key]
            scheme = self.ctx.opts.get("link_scheme")
            add = f" · [+standup]({scheme}:{c['fp']})" if scheme and c.get("fp") else ""
            if info and info["title"]:
                L.append(f"- #{c['pr']} — {info['title']} ({info['state']}){add}")
            else:
                pr = f"#{c['pr']} · " if c.get("pr") else ""
                L.append(f"- {c.get('ts','')[:16]} — {pr}{c['snippet']}{add}")
        return L
