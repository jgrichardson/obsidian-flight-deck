import os, tempfile
from flightdeck import config as cfgmod, render
from flightdeck.panels.base import Panel
from flightdeck.panels import REGISTRY

class Dummy(Panel):
    NAME = "dummy"; CALLOUT = "note"; TITLE = "Dummy"
    def render(self): return ["- hello"]

def test_render_writes_deck(tmp_path):
    REGISTRY["dummy"] = Dummy
    cfg = cfgmod.Config(raw={"vault": {"path": str(tmp_path)},
                             "panels": [{"name": "dummy"}]}, path="x")
    out = render.write(cfg)
    assert os.path.isfile(out)
    body = open(out).read()
    assert "cssclasses: [flight-deck]" in body
    assert "[!note]+ Dummy" in body
    assert "- hello" in body

def test_unknown_panel_is_warned(tmp_path):
    cfg = cfgmod.Config(raw={"vault": {"path": str(tmp_path)},
                             "panels": [{"name": "does_not_exist"}]}, path="x")
    body = render.build(cfg)
    assert "Unknown panel" in body

def test_cli_imports():
    import flightdeck.cli  # noqa
    assert hasattr(flightdeck.cli, "main")

def test_write_is_noop_when_vault_missing(tmp_path):
    missing = str(tmp_path / "does-not-exist")
    cfg = cfgmod.Config(raw={"vault": {"path": missing},
                             "panels": [{"name": "dummy"}]}, path="x")
    assert render.write(cfg) is None
    assert not os.path.isdir(missing)

def test_decile_base_omits_card_without_token(tmp_path, monkeypatch):
    from flightdeck.panels.decile_base import DecileBase
    from flightdeck.panels.base import Ctx
    monkeypatch.setattr("flightdeck.panels.decile_base._mcp_token", lambda: None)
    panel = DecileBase(Ctx(config=None, opts={}, now=None))
    assert panel.render() is None
    assert panel.card() == []

def test_claude_quotas_omits_card_without_cache(tmp_path, monkeypatch):
    from flightdeck.panels import claude_quotas
    from flightdeck.panels.base import Ctx
    monkeypatch.setattr(claude_quotas, "CACHE_DIR", str(tmp_path / "no-such-dir"))
    panel = claude_quotas.ClaudeQuotas(Ctx(config=None, opts={}, now=None))
    assert panel.render() is None
    assert panel.card() == []

def test_claude_quotas_reads_cache(tmp_path):
    import json, datetime
    from flightdeck.panels import claude_quotas
    from flightdeck.panels.base import Ctx
    now = datetime.datetime.now().astimezone()
    cache = tmp_path / "usage-cache"; cache.mkdir()
    (cache / "personal.json").write_text(json.dumps(
        {"account": "personal", "five_hour_pct": 3.2, "week_pct": 41.0, "ts": now.isoformat()}))
    orig = claude_quotas.CACHE_DIR
    claude_quotas.CACHE_DIR = str(cache)
    try:
        panel = claude_quotas.ClaudeQuotas(Ctx(config=None, opts={}, now=now))
        lines = panel.render()
    finally:
        claude_quotas.CACHE_DIR = orig
    assert lines is not None
    assert "personal" in lines[0]
    assert "3%" in lines[0]

def _write_transcript(path, lines):
    with open(path, "w") as f:
        for d in lines:
            f.write(__import__("json").dumps(d) + "\n")

def test_activity_scan_omits_card_when_nothing_found(tmp_path, monkeypatch):
    from flightdeck.panels import activity_scan
    from flightdeck.panels.base import Ctx
    monkeypatch.setattr(activity_scan, "STATE_FILE", str(tmp_path / "state.json"))
    empty_dir = tmp_path / "no-projects"
    panel = activity_scan.ActivityScan(Ctx(config=None, opts={"scan_dirs": [str(empty_dir)]}, now=None))
    assert panel.render() is None
    assert panel.card() == []

def test_activity_scan_extracts_and_checkpoints(tmp_path, monkeypatch):
    from flightdeck.panels import activity_scan
    from flightdeck.panels.base import Ctx
    monkeypatch.setattr(activity_scan, "STATE_FILE", str(tmp_path / "state.json"))
    proj = tmp_path / "projects" / "myproj"; proj.mkdir(parents=True)
    transcript = proj / "session1.jsonl"
    _write_transcript(transcript, [
        {"type": "assistant", "timestamp": "2026-09-01T14:00:00Z", "cwd": "/repo",
         "message": {"content": [{"type": "tool_use", "name": "Bash",
                                   "input": {"command": "gh pr merge 18963 --squash"}}]}},
        {"type": "assistant", "timestamp": "2026-09-01T14:05:00Z", "cwd": "/repo",
         "message": {"content": [{"type": "text", "text": "Done, #18964 merged cleanly."}]}},
        {"type": "user", "timestamp": "2026-09-01T14:06:00Z", "message": {"content": []}},
    ])
    opts = {"scan_dirs": [str(tmp_path / "projects" / "*")]}
    panel = activity_scan.ActivityScan(Ctx(config=None, opts=opts, now=None))
    lines = panel.render()
    assert lines is not None
    joined = "\n".join(lines)
    assert "18963" in joined
    assert "18964" in joined

    panel2 = activity_scan.ActivityScan(Ctx(config=None, opts=opts, now=None))
    assert panel2.render() is None

def test_activity_scan_enriches_with_real_pr_title(tmp_path, monkeypatch):
    from flightdeck.panels import activity_scan
    from flightdeck.panels.base import Ctx
    monkeypatch.setattr(activity_scan, "STATE_FILE", str(tmp_path / "state.json"))
    monkeypatch.setattr(activity_scan, "_pr_info",
                        lambda pr, cwd: {"title": "fix(mgmt-fees): source Fee Summary from the GL", "state": "merged"})
    proj = tmp_path / "projects" / "myproj"; proj.mkdir(parents=True)
    _write_transcript(proj / "session1.jsonl", [
        {"type": "assistant", "timestamp": "2026-09-01T14:00:00Z", "cwd": "/repo",
         "message": {"content": [{"type": "tool_use", "name": "Bash",
                                   "input": {"command": "gh pr merge 18902 --squash"}}]}},
    ])
    opts = {"scan_dirs": [str(tmp_path / "projects" / "*")]}
    panel = activity_scan.ActivityScan(Ctx(config=None, opts=opts, now=None))
    lines = panel.render()
    assert lines is not None
    joined = "\n".join(lines)
    assert "#18902 — fix(mgmt-fees): source Fee Summary from the GL (merged)" in joined
