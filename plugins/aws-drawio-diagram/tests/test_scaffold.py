import json
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1]
SKILL = PLUGIN / "skills" / "aws-drawio-diagram"


def test_manifests_are_valid_json_and_agree_on_name():
    a = json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_text())
    b = json.loads((PLUGIN / "plugin.json").read_text())
    assert a["name"] == b["name"] == "aws-drawio-diagram"
    assert a["version"] == b["version"] == "1.1.0"


def test_fixture_snapshots_exist_and_are_plausible():
    js = PLUGIN / "scripts" / "fixtures" / "Sidebar-AWS4.js"
    names = PLUGIN / "scripts" / "fixtures" / "aws4-stencil-names.txt"
    assert "addAWS4Palette" in js.read_text()
    lines = [l for l in names.read_text().splitlines() if l.strip()]
    assert len(lines) > 1000
    assert "lambda_function" in lines and "group_vpc" in lines
    assert (PLUGIN / "scripts" / "fixtures" / "SOURCE.md").exists()


def test_templates_copied():
    templates = sorted(p.name for p in (SKILL / "templates").glob("*.drawio"))
    assert templates == [
        "event-driven-processing.drawio",
        "serverless-rest-api.drawio",
        "static-website.drawio",
        "three-tier-web-app.drawio",
        "vpc-networking.drawio",
    ]


def test_marketplace_registers_plugin():
    root = PLUGIN.parents[1]
    mp = json.loads((root / ".claude-plugin" / "marketplace.json").read_text())
    names = {p["name"]: p for p in mp["plugins"]}
    assert "aws-drawio-diagram" in names
    assert names["aws-drawio-diagram"]["source"] == "./plugins/aws-drawio-diagram"
    assert "aws-drawio-diagram" in (root / "README.md").read_text()


def test_docs_and_licenses_present():
    for f in ("README.md", "README.en.md", "THIRD_PARTY_LICENSES.md", "LICENSE"):
        assert (PLUGIN / f).exists(), f
    tpl = (PLUGIN / "THIRD_PARTY_LICENSES.md").read_text()
    assert "Vidanov" in tpl and "Apache" in tpl and "AgentCore" in tpl
