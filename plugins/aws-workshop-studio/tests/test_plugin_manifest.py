import json
import re
from pathlib import Path

import pytest

PLUGIN = Path(__file__).resolve().parents[1]


def test_manifests_are_valid_json_and_agree():
    a = json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_text())
    b = json.loads((PLUGIN / "plugin.json").read_text())
    assert a["name"] == b["name"] == "aws-workshop-studio"
    assert a["version"] == b["version"] == "0.3.0"
    assert a["skills"] == b["skills"]
    assert a["commands"] == b["commands"]
    assert a["agents"] == b["agents"]


def test_declared_components_exist():
    m = json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_text())
    for rel in m["skills"]:
        assert (PLUGIN / rel / "SKILL.md").exists(), rel
    for rel in m["commands"] + m["agents"]:
        assert (PLUGIN / rel).exists(), rel


def test_no_nested_marketplace_manifest():
    assert not (PLUGIN / ".claude-plugin" / "marketplace.json").exists()


def test_agent_references_use_plugin_namespace():
    files = [
        PLUGIN / "references" / "pipeline-contract.md",
        PLUGIN / "commands" / "workshop-walkthrough.md",
        PLUGIN / "assets" / "workshop-pipeline.workflow.mjs",
    ]
    for f in files:
        text = f.read_text()
        assert "aws-workshop-studio:participant-walker" in text, f
        assert not re.search(r"(?<![\w-])workshop-scaffold:participant-walker", text), f


def test_readmes_point_at_this_marketplace():
    for name in ("README.md", "README.en.md"):
        text = (PLUGIN / name).read_text()
        assert "aws-workshop-studio@hi-aws-skills" in text, name
        assert "claude plugin install workshop-scaffold\n" not in text, name


def test_docs_present():
    for f in ("README.md", "README.en.md", "UPSTREAM.md", "THIRD_PARTY_LICENSES.md"):
        assert (PLUGIN / f).exists(), f
    assert "50e370add8ce024380aa69b200d3e5b20640f85b" in (PLUGIN / "UPSTREAM.md").read_text()


def test_marketplace_registers_plugin():
    root = PLUGIN.parents[1]
    mp_file = root / ".claude-plugin" / "marketplace.json"
    if not mp_file.exists():
        pytest.skip("not in the source repo (installed plugin copy has no marketplace.json)")
    mp = json.loads(mp_file.read_text())
    names = {p["name"]: p for p in mp["plugins"]}
    assert "aws-workshop-studio" in names
    assert names["aws-workshop-studio"]["source"] == "./plugins/aws-workshop-studio"
    assert "aws-workshop-studio" in (root / "README.md").read_text()


def test_insight_first_layer_present():
    # INV-9: rationale reference, overview template, scaffold markers, gate + check enforcement
    assert (PLUGIN / "references" / "architecture-rationale.md").exists()
    assert (PLUGIN / "references" / "templates" / "overview.md").exists()
    ov = (PLUGIN / "assets" / "scaffold" / "docs" / "start" / "overview.md").read_text()
    for m in ("arch:diagram", "arch:why", "arch:services", "arch:adoption"):
        assert f"<!-- {m} -->" in ov, m
    assert "images/diagrams/" in ov
    assert "03a-architecture-rationale.md" in (PLUGIN / "scripts" / "gate.sh").read_text()
    assert "arch:adoption" in (PLUGIN / "scripts" / "workshop-check.sh").read_text()
    contract = (PLUGIN / "references" / "pipeline-contract.md").read_text()
    for g in ("INV-9", "GATE-3f", "GATE-4e"):
        assert g in contract, g
    assert "insight-gap" in (PLUGIN / "references" / "persona-rubric.md").read_text()
    for t in ("scene.md", "feature.md"):
        assert "Why th" in (PLUGIN / "references" / "templates" / t).read_text(), t


def test_architecture_diagrams_delegate_to_aws_diagram_skills():
    recipes = (PLUGIN / "references" / "diagram-recipes.md").read_text()
    assert "aws-diagram-design" in recipes and "aws-drawio-diagram" in recipes
    assert "overview-architecture.png" in recipes
    skill = (PLUGIN / "skills" / "workshop-scaffold" / "SKILL.md").read_text()
    assert "aws-diagram-design" in skill and "INV-9" in skill
    wf = (PLUGIN / "assets" / "workshop-pipeline.workflow.mjs").read_text()
    assert "03a-architecture-rationale.md" in wf and "aws-diagram-design" in wf
