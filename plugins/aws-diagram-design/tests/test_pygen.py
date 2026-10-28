"""pygen builds standalone SVG that passes finalize checks; export.py is gone."""
import subprocess
import sys
from pathlib import Path

import pytest
from conftest import SCRIPTS, load_script

PYGEN = SCRIPTS / "pygen"
fz = load_script("finalize")


def build(tmp_path, *extra):
    return subprocess.run([sys.executable, str(PYGEN / "build.py"), str(PYGEN), "--out", str(tmp_path), *extra], capture_output=True, text=True)


def test_build_writes_svg_per_language(tmp_path):
    r = build(tmp_path)
    assert r.returncode == 0, r.stderr
    names = sorted(p.name for p in tmp_path.iterdir())
    assert names == ["training-pipeline-en.svg", "training-pipeline-ko.svg"]
    text = (tmp_path / "training-pipeline-en.svg").read_text(encoding="utf-8")
    assert text.startswith('<?xml version="1.0" encoding="UTF-8"?>') and "local('Amazon Ember')" in text


def test_built_svg_passes_checks(tmp_path):
    build(tmp_path)
    for p in tmp_path.glob("*.svg"):
        assert fz.run_checks(p) == [], p.name


def test_build_png_flag_renders_both_languages(tmp_path):
    pytest.importorskip("playwright")
    r = build(tmp_path, "--png")
    assert r.returncode == 0, r.stderr
    assert fz.png_size(tmp_path / "training-pipeline-ko.png") == (1920, 832)
    ko = (tmp_path / "training-pipeline-ko.svg").read_text(encoding="utf-8")
    assert "base64," in ko  # --png finalizes (embeds) too


def test_export_script_removed():
    assert not (PYGEN / "export.py").exists()


def test_canvas_has_no_html_method():
    sys.path.insert(0, str(PYGEN))
    import awsdiag
    assert not hasattr(awsdiag.Canvas, "html")


def test_no_legend_by_default_and_sublabel_in_ember_sans(tmp_path):
    """2.1.0: the example spec draws no legend strip, and the node sublabel shares the name's Ember family and size (16px)."""
    build(tmp_path)
    svg = (tmp_path / "training-pipeline-en.svg").read_text(encoding="utf-8")
    assert 'viewBox="0 0 960 416"' in svg
    assert "Focal step" not in svg and "Data flow" not in svg  # legend texts absent
    sub = [l for l in svg.splitlines() if "raw/ · checkpoints/" in l]
    assert len(sub) == 1 and 'font-size="16"' in sub[0] and "'Amazon Ember','Noto Sans KR'" in sub[0]
    assert "Amazon Ember Mono" not in sub[0]


def test_legend_is_opt_in(tmp_path):
    sys.path.insert(0, str(PYGEN))
    import awsdiag
    c = awsdiag.Canvas(400, 200, "t", "T", "D", "en")
    c.node(40, 40, 184, 64, "Amazon S3", "bucket", icon="S3", kind="store")
    assert c.check() == [] and 'stroke-width="0.8"' not in c.svg()  # no separator hairline, no strip
    c.legend([("store", "Storage")])
    assert c.check() == [] and "Storage" in c.svg()  # node bottom 104 clears h-60 = 140; strip drawn only now
    c2 = awsdiag.Canvas(400, 200, "t", "T", "D", "en")
    c2.node(40, 120, 184, 64, "Amazon S3", "bucket", icon="S3", kind="store")
    assert c2.check() == []
    c2.legend([("store", "Storage")])
    assert any("legend strip" in w for w in c2.check())
