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
    assert fz.png_size(tmp_path / "training-pipeline-ko.png") == (1920, 928)
    ko = (tmp_path / "training-pipeline-ko.svg").read_text(encoding="utf-8")
    assert "base64," in ko  # --png finalizes (embeds) too


def test_export_script_removed():
    assert not (PYGEN / "export.py").exists()


def test_canvas_has_no_html_method():
    sys.path.insert(0, str(PYGEN))
    import awsdiag
    assert not hasattr(awsdiag.Canvas, "html")
