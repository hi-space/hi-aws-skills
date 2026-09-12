import json
import subprocess
import sys
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1]
SKILL = PLUGIN / "skills" / "aws-drawio-diagram"
SCRIPTS = SKILL / "scripts"
SAMPLES = PLUGIN / "docs" / "samples"
sys.path.insert(0, str(SCRIPTS))

import build_diagram as bd  # noqa: E402
import layout  # noqa: E402
import scaffold_spec as sc  # noqa: E402
import validate_drawio as vd  # noqa: E402

INDEX = vd.load_index()
STENCILS = set(json.loads((SCRIPTS / "stencil-index.json").read_text())["stencils"])


def strip(spec):
    s = json.loads(json.dumps(spec))
    for n in s["nodes"]:
        n.pop("col", None)
        n.pop("lane", None)
    for g in s["groups"]:
        g.pop("cols", None)
        g.pop("lanes", None)
    return s


def test_auto_layout_places_the_shipped_samples_cleanly():
    for name in ("agentic-rag-chat", "order-pipeline", "iot-telemetry"):
        logical = strip(json.loads((SAMPLES / f"{name}.json").read_text()))
        assert layout.needs_layout(logical)
        placed, notes = layout.plan(logical, steps=3000)
        assert not [n for n in notes if not n.startswith("label dropped")], (name, notes)
        xml = bd.build(placed)
        errors, warnings = vd.validate_text(xml, INDEX)
        assert errors == [] and [w for w in warnings if w[:2] in vd.LAYOUT_DEFECTS] == [], (name, warnings)


def test_auto_layout_handles_a_hub_with_eight_neighbours():
    spec = {
        "title": "hub",
        "groups": [{"id": "g", "label": "Backend"}, {"id": "d", "label": "Data"}],
        "nodes": [{"id": "u", "label": "Users", "icon": "users", "outside": True},
                  {"id": "alb", "label": "ALB", "icon": "elastic_load_balancing", "group": "g"},
                  {"id": "api", "label": "FastAPI", "icon": "ecs_service", "group": "g"},
                  {"id": "rt", "label": "Runtime", "icon": "bedrock", "group": "g"},
                  {"id": "cog", "label": "Cognito", "icon": "cognito", "group": "g"},
                  {"id": "cw", "label": "CloudWatch", "icon": "cloudwatch_2", "group": "g"}]
                 + [{"id": f"s{i}", "label": f"Store {i}", "icon": "dynamodb", "group": "d"} for i in range(5)],
        "edges": [{"from": "u", "to": "alb", "label": "HTTPS"}, {"from": "alb", "to": "api"}, {"from": "api", "to": "rt"},
                  {"from": "api", "to": "cog"}, {"from": "api", "to": "cw", "dashed": True}]
                 + [{"from": "api", "to": f"s{i}"} for i in range(5)],
    }
    placed, notes = layout.plan(spec, steps=4000)
    assert not [n for n in notes if not n.startswith("label dropped")], notes
    xml = bd.build(placed)
    errors, warnings = vd.validate_text(xml, INDEX)
    assert errors == [] and [w for w in warnings if w[:2] in vd.LAYOUT_DEFECTS] == []
    ids = {n["id"] for n in placed["nodes"]}
    assert ids == {n["id"] for n in spec["nodes"]} and len(placed["edges"]) == len(spec["edges"])
    assert all(g["cols"] and g["lanes"] for g in placed["groups"])


def test_scaffold_reads_a_brief_into_a_logical_spec():
    brief = (SAMPLES / "order-pipeline.brief.md").read_text()
    spec, warnings = sc.scaffold(brief, STENCILS)
    assert warnings == []
    assert spec["layout"] == "auto"
    assert {n["id"] for n in spec["nodes"]} == {"mobile", "apigw", "cognito", "sqs", "dlq", "handler", "ddb", "sfn", "payment",
                                                "inventory", "sns", "customer", "cw", "s3"}
    assert len(spec["edges"]) == 13
    outside = {n["id"] for n in spec["nodes"] if n.get("outside")}
    assert outside == {"mobile", "customer"}
    dashed = {(e["from"], e["to"]) for e in spec["edges"] if e.get("dashed")}
    assert ("apigw", "cognito") in dashed and ("sqs", "dlq") in dashed and ("mobile", "apigw") not in dashed
    labels = {(e["from"], e["to"]): e.get("label") for e in spec["edges"]}
    assert labels[("mobile", "apigw")] == "HTTPS" and labels[("sfn", "sns")] is None      # "on completion": two words, dropped


def test_builder_plans_layout_and_checks_the_brief_end_to_end(tmp_path):
    brief = (SAMPLES / "order-pipeline.brief.md").read_text()
    (tmp_path / "op.brief.md").write_text(brief)
    r = subprocess.run([sys.executable, str(SCRIPTS / "scaffold_spec.py"), str(tmp_path / "op.brief.md"), str(tmp_path / "op.json")],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout
    r = subprocess.run([sys.executable, str(SCRIPTS / "build_diagram.py"), str(tmp_path / "op.json"), str(tmp_path / "op.drawio")],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout
    assert "auto layout: placed 14 nodes" in r.stdout and "brief check: 14 components → 14 nodes" in r.stdout
    assert (tmp_path / "op.layout.json").exists() and (tmp_path / "op.drawio").exists()


def test_brief_count_guard_catches_a_shrunken_table():
    brief = "# T\nComponents: 5 · Relationships: 4\n\n" + """## Components
| id | Service (stencil) | Role | Group |
|---|---|---|---|
| u | Users (`users`) | people | outside |
| a | API Gateway (`api_gateway`) | entry | G |

## Relationships
| # | From → To | What | Kind | Label |
|---|---|---|---|---|
| 1 | u → a | HTTPS | sync | HTTPS |
"""
    spec = {"nodes": [{"id": "u"}, {"id": "a"}], "edges": [{"from": "u", "to": "a"}]}
    errors, _ = bd.brief_check(brief, spec)
    assert any("declares 'Components: 5'" in e for e in errors)


def test_scaffold_checks_evidence_paths_against_the_repo(tmp_path):
    (tmp_path / "infra").mkdir()
    (tmp_path / "infra" / "main.tf").write_text("resource \"aws_lambda_function\" \"f\" {}\n")
    brief = f"""# T
Repo: {tmp_path}
Components: 2 · Relationships: 1

## Components
| id | Service (stencil) | Role | Group | Evidence | Provenance |
|---|---|---|---|---|---|
| u | Users (`users`) | people | outside | — | assumed |
| f | Lambda (`lambda`) | handler | G | infra/main.tf:1 (`aws_lambda_function.f`) | deployed |
| g | S3 (`s3`) | bucket | G | infra/storage/s3.tf:4 | deployed |

## Relationships
| # | From → To | What | Kind | Label |
|---|---|---|---|---|
| 1 | u → f | HTTPS | sync | HTTPS |
"""
    spec, warnings = sc.scaffold(brief, STENCILS)
    assert [w for w in warnings if "does not exist" in w] == ["g: evidence path 'infra/storage/s3.tf' does not exist under "
                                                              f"{tmp_path} — cite a file you opened"]
