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
