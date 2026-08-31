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
