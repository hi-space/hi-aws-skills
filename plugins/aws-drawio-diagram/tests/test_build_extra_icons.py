import base64
import json
import sys
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1]
SKILL = PLUGIN / "skills" / "aws-drawio-diagram"
SCRIPTS = SKILL / "scripts"
sys.path.insert(0, str(SCRIPTS))

import build_extra_icons as bei  # noqa: E402

SVG = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><rect width="48" height="48" fill="#7B27FF"/></svg>'


def test_normalize():
    assert bei.normalize("Arch_Amazon-Bedrock-AgentCore_48.svg") == "bedrock_agentcore"
    assert bei.normalize("Res_AWS-Lambda_Lambda-Function_48.svg") == "lambda_function"
    assert bei.normalize("Res_Users_48_Light.svg") == "users"
    assert bei.normalize("Arch_Amazon-Simple-Storage-Service_48.svg") == "simple_storage_service"


def test_report_lists_only_unmatched(tmp_path):
    (tmp_path / "service").mkdir()
    (tmp_path / "service" / "Arch_AWS-Lambda_48.svg").write_bytes(SVG)
    (tmp_path / "service" / "Arch_Amazon-Made-Up_48.svg").write_bytes(SVG)
    out = bei.report(tmp_path, {"lambda"})
    assert out == [("service/Arch_Amazon-Made-Up_48.svg", "made_up")]


def test_image_style_has_no_semicolon_inside_data_uri():
    style = bei.image_style(SVG)
    assert style.startswith("shape=image;")
    assert "image=data:image/svg+xml," in style
    assert ";base64" not in style
    b64 = style.split("image=data:image/svg+xml,")[1].rstrip(";")
    assert base64.b64decode(b64) == SVG


def test_build_copies_and_renders(tmp_path):
    icons = tmp_path / "icons" / "resource" / "AI"
    icons.mkdir(parents=True)
    (icons / "Res_Amazon-Bedrock-AgentCore_Memory_48.svg").write_bytes(SVG)
    allow = [("resource/AI/Res_Amazon-Bedrock-AgentCore_Memory_48.svg", "AgentCore Memory")]
    assets = tmp_path / "assets"
    md = tmp_path / "aws-icons-extra.md"
    written = bei.build(tmp_path / "icons", allow, assets, md)
    assert (assets / "Res_Amazon-Bedrock-AgentCore_Memory_48.svg").read_bytes() == SVG
    text = md.read_text()
    assert "Do not edit by hand" in text
    assert "### AgentCore Memory" in text
    assert "shape=image;" in text and ";base64" not in text
    assert md in written


def test_read_allow_list(tmp_path):
    f = tmp_path / "extra-icons.txt"
    f.write_text("# comment\nresource/a/X_48.svg|X Thing\n\nresource/b/Y_48.svg | Y\n")
    assert bei.read_allow_list(f) == [("resource/a/X_48.svg", "X Thing"), ("resource/b/Y_48.svg", "Y")]


def test_shipped_extra_md_matches_allow_list():
    allow = bei.read_allow_list(SCRIPTS / "extra-icons.txt")
    assert len(allow) >= 11
    text = (SKILL / "references" / "aws-icons-extra.md").read_text()
    for rel, name in allow:
        assert f"### {name}" in text
        assert (SKILL / "assets" / "extra-icons" / Path(rel).name).exists()
