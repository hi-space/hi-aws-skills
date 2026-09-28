"""Every shipped SVG asset parses, passes the contract, and no HTML wrapper file survives."""
from pathlib import Path

import pytest
from conftest import SKILL, load_script

sc = load_script("self_check")
ASSETS = SKILL / "assets"
ALLOWED_HTML = {"index.html", "icons.html", "aws-icons.html", "template-motion.html", "example-policy-trace-animated.html"}


def test_three_svg_templates_exist():
    for name in ("template.svg", "template-dark.svg", "template-terminal.svg"):
        assert (ASSETS / name).exists(), name
        assert not (ASSETS / name.replace(".svg", ".html")).exists(), name


@pytest.mark.parametrize("path", sorted(ASSETS.glob("*.svg")), ids=lambda p: p.name)
def test_svg_asset_passes_contract(path: Path):
    assert sc.verify(path) == []


@pytest.mark.parametrize("path", sorted(ASSETS.glob("template*.svg")), ids=lambda p: p.name)
def test_templates_declare_local_fonts_only(path: Path):
    text = path.read_text(encoding="utf-8")
    assert "local('Amazon Ember')" in text and "base64," not in text


def test_no_stray_html_in_assets():
    stray = {p.name for p in ASSETS.glob("*.html")} - ALLOWED_HTML
    assert stray == set()
