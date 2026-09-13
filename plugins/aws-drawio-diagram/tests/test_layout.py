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
    # the scaffold passes every Label through; whether it fits is layout.py's call, per edge geometry
    assert labels[("mobile", "apigw")] == "HTTPS" and labels[("sfn", "sns")] == "on complete"
    assert labels[("apigw", "sqs")] == "order message"                                     # two words pass through
    assert labels[("sfn", "payment")] is None                                              # "—" stays unlabeled


def _two_group_spec(edges):
    # group "a" is a full 2 × 2 rectangle (gw, fn on the lane; auth, cache below) so layout draws it as ONE box —
    # a group whose cells do not fill a rectangle is split into several boxes, and edges between them cross a border
    return {
        "title": "labels",
        "groups": [{"id": "a", "label": "A"}, {"id": "b", "label": "B"}],
        "nodes": [{"id": "u", "label": "Users", "icon": "users", "outside": True},
                  {"id": "gw", "label": "API Gateway", "icon": "api_gateway", "group": "a"},
                  {"id": "fn", "label": "Lambda", "icon": "lambda", "group": "a"},
                  {"id": "auth", "label": "Cognito", "icon": "cognito", "group": "a"},
                  {"id": "cache", "label": "ElastiCache", "icon": "elasticache", "group": "a"},
                  {"id": "db", "label": "DynamoDB", "icon": "dynamodb", "group": "b"}],
        "edges": edges,
    }


def test_layout_keeps_labels_that_fit_and_says_why_it_drops_the_rest():
    spec = _two_group_spec([
        {"from": "u", "to": "gw", "label": "HTTPS"},                          # outside → cloud: ≤ 6 chars fits
        {"from": "gw", "to": "fn", "label": "invoke (proxy)"},                # inside one box: 14 chars fits
        {"from": "gw", "to": "auth", "label": "validate JWT", "dashed": True},# vertical straight: 12 chars fits
        {"from": "fn", "to": "cache", "label": "session lookup"},             # vertical straight: 14 > 12 → dropped
        {"from": "fn", "to": "db", "label": "put item"},                      # adjacent groups: 8 > 6 → dropped
    ])
    # a fixed placement, so the test pins the label rule and not the planner's taste
    p = layout.Placement(spec, seed=1)
    p.col = {"u": 0, "gw": 1, "fn": 2, "auth": 1, "cache": 2, "db": 3}
    p.lane = {"u": 0, "gw": 0, "fn": 0, "auth": 1, "cache": 1, "db": 0}
    placed = p.apply()
    assert [g["id"] for g in placed["groups"]] == ["a", "b"], placed["groups"]   # "a" is one 2 × 2 box
    labels = {(e["from"], e["to"]): e.get("label") for e in placed["edges"]}
    assert labels[("u", "gw")] == "HTTPS"
    assert labels[("gw", "fn")] == "invoke (proxy)"
    assert labels[("gw", "auth")] == "validate JWT"
    assert labels[("fn", "cache")] is None and labels[("fn", "db")] is None
    assert any("fn → db" in n and "put item" in n and "shorten" in n for n in p.dropped_labels), p.dropped_labels
    assert any("fn → cache" in n and "vertical" in n for n in p.dropped_labels), p.dropped_labels
    # and what layout keeps, the builder can place without a W7
    xml = bd.build(placed)
    errors, warnings = vd.validate_text(xml, INDEX)
    assert errors == [] and [w for w in warnings if w[:2] in vd.LAYOUT_DEFECTS] == [], warnings


def test_layout_prefers_a_straight_edge_for_a_labeled_relationship():
    # two labeled edges fight for the straight slot: the one with a label must not be the one that bends
    spec = _two_group_spec([
        {"from": "u", "to": "gw"},
        {"from": "gw", "to": "fn"},
        {"from": "fn", "to": "db", "label": "write"},
        {"from": "fn", "to": "auth", "dashed": True},
    ])
    placed, notes = layout.plan(spec, steps=3000)
    labels = {(e["from"], e["to"]): e.get("label") for e in placed["edges"]}
    assert labels[("fn", "db")] == "write", notes


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


def test_contract_freezes_component_ids_and_relationship_pairs(tmp_path):
    brief = (SAMPLES / "order-pipeline.brief.md").read_text()
    b = tmp_path / "op.brief.md"
    b.write_text(brief)
    lock = tmp_path / "op.contract.json"
    # first run writes the contract
    errors, notes = bd.contract_check(brief, lock)
    assert errors == [] and lock.exists() and "written" in " ".join(notes)
    # unchanged brief: silent
    assert bd.contract_check(brief, lock) == ([], [])
    # a Drawer re-points a relationship (the llm-gateway loophole): ERROR naming both pairs
    rewired = brief.replace("| 9 | sfn → sns |", "| 9 | sfn → customer |")
    errors, _ = bd.contract_check(rewired, lock)
    assert any("sfn → sns" in e and "sfn → customer" in e for e in errors), errors
    # a component quietly dropped from the table: ERROR
    errors, _ = bd.contract_check(brief.replace("| dlq | SQS (`sqs`)", "| dlq_x | SQS (`sqs`)"), lock)
    assert any("dlq" in e for e in errors), errors
    # a row newly marked not drawn is allowed but reported, so the Reviewer sees the shrinkage
    shrunk = brief.replace("| 12 | ddb → s3 | periodic export | aux (dashed) |", "| 12 | ddb → s3 | periodic export | aux (not drawn) |")
    errors, notes = bd.contract_check(shrunk, lock)
    assert errors == [] and any("newly marked" in n and "ddb → s3" in n for n in notes), notes


def test_scaffold_and_builder_refuse_a_rewired_brief_end_to_end(tmp_path):
    brief = (SAMPLES / "order-pipeline.brief.md").read_text()
    (tmp_path / "op.brief.md").write_text(brief)
    r = subprocess.run([sys.executable, str(SCRIPTS / "scaffold_spec.py"), str(tmp_path / "op.brief.md"), str(tmp_path / "op.json")],
                       capture_output=True, text=True)
    assert r.returncode == 0 and (tmp_path / "op.contract.json").exists(), r.stdout
    (tmp_path / "op.brief.md").write_text(brief.replace("| 9 | sfn → sns |", "| 9 | sfn → customer |"))
    r = subprocess.run([sys.executable, str(SCRIPTS / "scaffold_spec.py"), str(tmp_path / "op.brief.md"), str(tmp_path / "op.json")],
                       capture_output=True, text=True)
    assert r.returncode == 1 and "contract" in r.stdout and "sfn → customer" in r.stdout, r.stdout
    r = subprocess.run([sys.executable, str(SCRIPTS / "build_diagram.py"), str(tmp_path / "op.json"), str(tmp_path / "op.drawio")],
                       capture_output=True, text=True)
    assert r.returncode == 1 and "contract" in r.stdout, r.stdout


def test_too_long_label_on_a_primary_edge_is_an_error_not_a_note():
    spec = _two_group_spec([
        {"from": "u", "to": "gw"}, {"from": "gw", "to": "fn"},
        {"from": "fn", "to": "db", "label": "put item"},                              # solid, adjacent groups: 8 > 6
        {"from": "fn", "to": "cache", "label": "session lookup", "dashed": True},     # dashed, vertical: 14 > 12
    ])
    p = layout.Placement(spec, seed=1)
    p.col = {"u": 0, "gw": 1, "fn": 2, "auth": 1, "cache": 2, "db": 3}
    p.lane = {"u": 0, "gw": 0, "fn": 0, "auth": 1, "cache": 1, "db": 0}
    p.apply()
    assert [d for d in p.too_long_primary if "fn → db" in d] and not [d for d in p.too_long_primary if "fn → cache" in d]
    assert any("or write —" in d for d in p.too_long_primary), p.too_long_primary


def test_builder_refuses_a_primary_label_that_does_not_fit(tmp_path):
    brief = (SAMPLES / "order-pipeline.brief.md").read_text()
    row = "| 2 | apigw → sqs | order message | sync | order message |"
    assert row in brief
    def run(text):
        (tmp_path / "op.brief.md").write_text(text)
        (tmp_path / "op.contract.json").unlink(missing_ok=True)
        (tmp_path / "op.drawio").unlink(missing_ok=True)
        r = subprocess.run([sys.executable, str(SCRIPTS / "scaffold_spec.py"), str(tmp_path / "op.brief.md"), str(tmp_path / "op.json")],
                           capture_output=True, text=True)
        if r.returncode:
            return r
        return subprocess.run([sys.executable, str(SCRIPTS / "build_diagram.py"), str(tmp_path / "op.json"), str(tmp_path / "op.drawio")],
                              capture_output=True, text=True)
    # 21 characters on a primary edge can fit nowhere: the scaffold already refuses, before layout luck decides
    r = run(brief.replace(row, "| 2 | apigw → sqs | order message | sync | order message payload |"))
    assert r.returncode == 1 and "can never fit" in r.stdout and "apigw → sqs" in r.stdout, r.stdout
    assert not (tmp_path / "op.drawio").exists()
    # the same text on an aux (dashed) edge is layout's business and at most a note
    aux_row = "| 11 | apigw → cw | metrics, logs | aux (dashed) | metrics |"
    assert aux_row in brief
    r = run(brief.replace(aux_row, "| 11 | apigw → cw | metrics, logs | aux (dashed) | metrics and access logs |"))
    assert r.returncode == 0 and "ERROR label" not in r.stdout, r.stdout
    # "—" is the explicit way out for a primary pair that explains itself
    r = run(brief.replace(row, "| 2 | apigw → sqs | order message | sync | — |"))
    assert r.returncode == 0, r.stdout


def test_builder_stops_on_a_planner_label_too_long_note(tmp_path, monkeypatch, capsys):
    # the planner treats a fitting primary label as a hard constraint, so end-to-end it rarely reports one;
    # the gate in the builder is still the last line — feed it the note directly
    spec = {"title": "t", "layout": "auto",
            "groups": [{"id": "g", "label": "G"}],
            "nodes": [{"id": "a", "label": "A", "icon": "lambda", "group": "g"}, {"id": "b", "label": "B", "icon": "sqs", "group": "g"}],
            "edges": [{"from": "a", "to": "b", "label": "enqueue order"}]}
    (tmp_path / "s.json").write_text(json.dumps(spec))
    real_plan = layout.plan
    def fake_plan(s, **kw):
        placed, notes = real_plan(s, **kw)
        return placed, notes + ["label too long: a → b ('enqueue order'): 13 characters is too long for an edge between "
                                "adjacent groups (max 6) — shorten the Label in the brief, or write — when the pair explains itself"]
    monkeypatch.setattr(layout, "plan", fake_plan)
    rc = bd.main([str(tmp_path / "s.json"), str(tmp_path / "s.drawio"), "--no-brief"])
    out = capsys.readouterr().out
    assert rc == 1 and "ERROR label" in out and "a → b" in out and "NOT CLEAN" in out, out
    assert not (tmp_path / "s.drawio").exists()


def test_scaffold_flags_a_primary_label_that_can_never_fit():
    brief = (SAMPLES / "order-pipeline.brief.md").read_text()
    row = "| 2 | apigw → sqs | order message | sync | order message |"
    spec, warnings = sc.scaffold(brief.replace(row, "| 2 | apigw → sqs | order message | sync | order message payload |"), STENCILS)
    assert any("can never fit" in w and "apigw → sqs" in w and "21 characters" in w for w in warnings), warnings
    # the same length on an aux edge is layout's business, not a brief defect
    aux_row = "| 11 | apigw → cw | metrics, logs | aux (dashed) | metrics |"
    _, warnings = sc.scaffold(brief.replace(aux_row, "| 11 | apigw → cw | metrics, logs | aux (dashed) | metrics and access logs |"), STENCILS)
    assert warnings == []
    assert sc.main([str(SAMPLES / "order-pipeline.brief.md"), "/tmp/_op_scaffold_check.json"]) == 0


def test_scaffold_numbers_edges_from_the_brief_hash_column():
    brief = (SAMPLES / "order-pipeline.brief.md").read_text()
    spec, _ = sc.scaffold(brief, STENCILS)
    nums = {(e["from"], e["to"]): e.get("num") for e in spec["edges"]}
    assert nums[("mobile", "apigw")] == 1 and nums[("sqs", "dlq")] == 13 and nums[("sfn", "payment")] == 7
    assert all(isinstance(n, int) for n in nums.values())


KO_GUIDE = """# 주문 파이프라인

모바일 앱의 주문을 API Gateway가 받아 SQS에 넣고 Lambda가 처리한다.

## 단계별 흐름
1. **Mobile client → API Gateway** — 앱이 HTTPS로 REST 요청을 보낸다.
2. **API Gateway → SQS** — 주문 메시지를 큐에 넣고 202를 돌려준다.

## 서비스
| 서비스 | 역할 |
|---|---|
| Mobile client | 고객 앱 |
| API Gateway | REST 진입점 |
| SQS | 주문 큐 |

## 설계 결정
- 큐로 비동기 경계를 둔다.
"""
KO_BRIEF = """# T
Language: ko
Components: 3 · Relationships: 2

## Components
| id | Service (stencil) | Role | Group |
|---|---|---|---|
| mobile | Mobile client (`mobile_client`, resource) | app | outside |
| apigw | API Gateway (`api_gateway`) | entry | API |
| sqs | SQS (`sqs`) | queue | API |

## Relationships
| # | From → To | What flows | Kind | Label |
|---|---|---|---|---|
| 1 | mobile → apigw | requests | sync | HTTPS |
| 2 | apigw → sqs | order message | sync | order message |
"""


def test_check_guide_accepts_a_korean_guide_that_covers_every_relationship():
    import check_guide as cg
    errors, summary = cg.check_guide(KO_GUIDE, KO_BRIEF)
    assert errors == [] and "2 relationships → 2 steps" in summary and "ko" in summary, (errors, summary)


def test_check_guide_rejects_wrong_language_missing_steps_and_missing_services():
    import check_guide as cg
    english = KO_GUIDE.replace("앱이 HTTPS로 REST 요청을 보낸다", "The app sends REST requests over HTTPS").replace(
        "주문 메시지를 큐에 넣고 202를 돌려준다", "puts the order on the queue and returns 202").replace(
        "모바일 앱의 주문을 API Gateway가 받아 SQS에 넣고 Lambda가 처리한다", "Orders from the mobile app enter through API Gateway into SQS")
    errors, _ = cg.check_guide(english, KO_BRIEF)
    assert any("Language: ko" in e for e in errors), errors
    # step 2 missing → the relationship it should describe is named
    errors, _ = cg.check_guide(KO_GUIDE.replace("2. **API Gateway → SQS** — 주문 메시지를 큐에 넣고 202를 돌려준다.\n", ""), KO_BRIEF)
    assert any("apigw → sqs" in e and "step 2" in e for e in errors), errors
    # step exists but names the wrong endpoint
    errors, _ = cg.check_guide(KO_GUIDE.replace("2. **API Gateway → SQS**", "2. **API Gateway → DynamoDB**"), KO_BRIEF)
    assert any("step 2" in e and "SQS" in e for e in errors), errors
    # a component absent from the guide
    errors, _ = cg.check_guide(KO_GUIDE.replace("SQS", "큐"), KO_BRIEF)                # SQS named nowhere in the guide
    assert any("'sqs'" in e and "Services" in e for e in errors), errors


def test_check_guide_cli_on_the_shipped_sample():
    r = subprocess.run([sys.executable, str(SCRIPTS / "check_guide.py"), str(SAMPLES / "order-pipeline.guide.md"),
                        str(SAMPLES / "order-pipeline.brief.md")], capture_output=True, text=True)
    assert r.returncode == 0 and "guide check" in r.stdout and "✓" in r.stdout, r.stdout
