import json
import subprocess
import sys
from pathlib import Path

import pytest

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


def test_planner_caps_bends_per_side_and_lets_roles_mix():
    def hub(n_targets, extra=()):
        nodes = [{"id": "b", "label": "Hub", "icon": "lambda", "group": "g"}]
        nodes += [{"id": f"t{i}", "label": f"T{i}", "icon": "s3", "group": "g"} for i in range(n_targets)]
        nodes += [dict(e) for e in extra]
        edges = [{"from": "b", "to": f"t{i}"} for i in range(n_targets)]
        return {"title": "hub", "groups": [{"id": "g", "label": "G"}], "nodes": nodes, "edges": edges}

    def placed(spec, cells):
        p = layout.Placement(spec)
        col = {nid: c for nid, (c, _) in cells.items()}
        lane = {nid: l for nid, (_, l) in cells.items()}
        return p.cost(col, lane)

    # three bends leaving the hub's bottom, all turning right: allowed
    cells = {"b": (2, 1), **{f"t{i}": (3, 2 + i) for i in range(3)}}
    cost, notes = placed(hub(3), cells)
    assert cost < layout.HARD, notes
    # a fourth: the planner routes one of them horizontally first, so it leaves the hub's right side instead
    cells["t3"] = (3, 5)
    p = layout.Placement(hub(4))
    p.col = {nid: c for nid, (c, _) in cells.items()}
    p.lane = {nid: l for nid, (_, l) in cells.items()}
    cost, notes = p.cost()
    assert cost < layout.HARD, notes
    assert sorted(p.routes.values()) == ["h", "v", "v", "v"]
    assert sum(1 for e in p.apply()["edges"] if e.get("route") == "h") == 1
    # with the right side owned by a straight edge, nothing can move there: a hard violation naming the cap
    spec = hub(4, extra=[{"id": "r", "label": "R", "icon": "sqs", "group": "g"}])
    spec["edges"].append({"from": "b", "to": "r"})
    cells["r"] = (3, 1)
    cost, notes = placed(spec, cells)
    assert cost >= layout.HARD and any("at most" in n for n in notes), notes
    # an arriving bend and a leaving bend on one side are separate lines now: not a violation
    spec = hub(1, extra=[{"id": "src", "label": "Src", "icon": "sqs", "group": "g"}])
    spec["edges"].append({"from": "src", "to": "b"})
    cells = {"b": (2, 1), "t0": (3, 2), "src": (1, 2)}
    p = layout.Placement(spec)
    col = {nid: c for nid, (c, _) in cells.items()}
    lane = {nid: l for nid, (_, l) in cells.items()}
    cost, notes = p.cost(col, lane)
    assert cost < layout.HARD, notes


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
    # the edge text is the What flows phrase, passed through verbatim (backticks stripped); the builder wraps it
    assert labels[("mobile", "apigw")] == "order requests" and labels[("sfn", "sns")] == "post status"
    assert labels[("sfn", "payment")] == "task invoke"
    assert labels[("sqs", "dlq")] == "messages that exceed maxReceiveCount"
    # a brief still carrying the 1.4 "Label" column: the column is ignored and named in a warning
    old = brief.replace("| # | From → To | What flows | Kind |", "| # | From → To | What flows | Kind | Label |").replace(
        "| 1 | mobile → apigw | order requests | sync |", "| 1 | mobile → apigw | order requests | sync | HTTPS |")
    spec2, warnings = sc.scaffold(old, STENCILS)
    assert any("'Label' column" in w and "ignored" in w for w in warnings), warnings
    assert {(e["from"], e["to"]): e.get("label") for e in spec2["edges"]}[("mobile", "apigw")] == "order requests"


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


def _edge_values(xml):
    import xml.etree.ElementTree as ET
    out = {}
    for c in ET.fromstring(xml).iter("mxCell"):
        if c.get("edge") == "1":
            out[(c.get("source"), c.get("target"))] = (c.get("value"), vd.parse_style(c.get("style")), c.find("mxGeometry").get("x"))
    return out


def test_builder_draws_every_what_flows_phrase_wrapped_to_the_room_it_has():
    spec = _two_group_spec([
        {"from": "u", "to": "gw", "label": "order requests"},                   # outside → cloud: 121 px pocket, one line
        {"from": "gw", "to": "fn", "label": "invoke with the validated order"},  # inside one box: 162 px → wrapped to 2 lines
        {"from": "gw", "to": "auth", "label": "validate JWT", "dashed": True},   # vertical straight: beside the line
        {"from": "fn", "to": "cache", "label": "session lookup"},                # vertical inside the box: one line beside it
        {"from": "fn", "to": "db", "label": "put item"},                         # adjacent groups: wraps into the 61 px pocket
    ])
    # a fixed placement, so the test pins the label rules and not the planner's taste
    p = layout.Placement(spec, seed=1)
    p.col = {"u": 0, "gw": 1, "fn": 2, "auth": 1, "cache": 2, "db": 3}
    p.lane = {"u": 0, "gw": 0, "fn": 0, "auth": 1, "cache": 1, "db": 0}
    placed = p.apply()
    assert [g["id"] for g in placed["groups"]] == ["a", "b"], placed["groups"]   # "a" is one 2 × 2 box
    assert all(e.get("label") for e in placed["edges"])                          # the planner drops nothing
    xml = bd.build(placed)
    values = _edge_values(xml)
    assert values[("u", "gw")][0] == "order requests" and values[("u", "gw")][1]["verticalAlign"] == "bottom"
    assert values[("gw", "fn")][0] == "invoke with the<br>validated order"
    assert values[("gw", "auth")][0] == "validate JWT" and values[("gw", "auth")][1]["align"] in ("right", "left")
    assert values[("fn", "cache")][0] == "session lookup" and values[("fn", "cache")][1]["align"] in ("right", "left")
    assert values[("fn", "db")][0] == "put<br>item" and values[("fn", "db")][2] is not None      # slid into a pocket
    errors, warnings = vd.validate_text(xml, INDEX)
    assert errors == [] and warnings == [], warnings


def test_label_wrapping_helpers():
    assert bd.wrap_lines("Fetch dynamic credentials (optional)", 24) == ["Fetch dynamic", "credentials (optional)"]
    assert bd.label_lines("Fetch dynamic credentials (optional)", 29) == ["Fetch dynamic", "credentials (optional)"]  # balanced
    assert bd.label_lines("put item", 6) == ["put", "item"]
    assert bd.label_lines("StartExecution", 6) is None                       # a word wider than the line
    assert bd.label_lines("one two three four five six seven eight", 6) is None   # more than 3 lines
    assert bd.chars_that_fit(162) == 22 and bd.chars_that_fit(61) == 6 and bd.chars_that_fit(121) == 16


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
| # | From → To | What flows | Kind |
|---|---|---|---|
| 1 | u → a | HTTPS | sync |
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
| # | From → To | What flows | Kind |
|---|---|---|---|
| 1 | u → f | HTTPS | sync |
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
    shrunk = brief.replace("| 12 | ddb → s3 | PITR export | aux (dashed) |", "| 12 | ddb → s3 | PITR export | aux (not drawn) |")
    assert shrunk != brief
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


def _cross_border_spec(text, dashed=False):
    # fn (box a) → db (box b) on one lane: the text has two 61 px pockets, i.e. words of ≤ 6 characters
    spec = _two_group_spec([{"from": "u", "to": "gw"}, {"from": "gw", "to": "fn"}, {"from": "gw", "to": "auth", "dashed": True},
                            {"from": "fn", "to": "cache"},
                            {"from": "fn", "to": "db", "label": text, **({"dashed": True} if dashed else {})}])
    p = layout.Placement(spec, seed=1)
    p.col = {"u": 0, "gw": 1, "fn": 2, "auth": 1, "cache": 2, "db": 3}
    p.lane = {"u": 0, "gw": 0, "fn": 0, "auth": 1, "cache": 1, "db": 0}
    return p.apply()


def test_primary_text_with_no_room_is_an_error_dashed_text_is_dropped_with_a_note():
    with pytest.raises(bd.LabelError) as exc:
        bd.build(_cross_border_spec("StartExecution"))                 # one 14-character word, 6 fit per line
    assert len(exc.value.problems) == 1 and "fn → db" in exc.value.problems[0] and "condense" in exc.value.problems[0]
    b = bd.Builder(_cross_border_spec("StartExecution", dashed=True), json.loads(bd.INDEX.read_text()))
    xml = b.build()
    assert any("label dropped" in n and "fn → db" in n for n in b.notes), b.notes
    assert _edge_values(xml)[("fn", "db")][0] is None and vd.validate_text(xml, INDEX) == ([], [])
    # the same meaning in pocket-sized words is drawn
    xml = bd.build(_cross_border_spec("start saga"))
    assert _edge_values(xml)[("fn", "db")][0] == "start<br>saga" and vd.validate_text(xml, INDEX) == ([], [])


def test_builder_cli_stops_on_a_primary_text_with_no_room(tmp_path, capsys):
    (tmp_path / "s.json").write_text(json.dumps(_cross_border_spec("StartExecution")))
    rc = bd.main([str(tmp_path / "s.json"), str(tmp_path / "s.drawio"), "--no-brief"])
    out = capsys.readouterr().out
    assert rc == 1 and "ERROR label" in out and "fn → db" in out and "NOT CLEAN" in out, out
    assert not (tmp_path / "s.drawio").exists()


def test_scaffold_flags_a_what_flows_phrase_that_can_never_fit(tmp_path):
    brief = (SAMPLES / "order-pipeline.brief.md").read_text()
    row = "| 2 | apigw → sqs | order message | sync |"
    assert row in brief
    # a 26-character word is wider than any line: the scaffold refuses, before layout luck decides where the edge lands
    spec, warnings = sc.scaffold(brief.replace(row, "| 2 | apigw → sqs | OrderMessagePayloadEnvelope | sync |"), STENCILS)
    assert any("can never fit" in w and "apigw → sqs" in w and "condense" in w for w in warnings), warnings
    # four lines of text neither
    _, warnings = sc.scaffold(brief.replace(row, "| 2 | apigw → sqs | every accepted order as one message on the queue with its idempotency key and the caller identity | sync |"), STENCILS)
    assert any("can never fit" in w for w in warnings), warnings
    # the same on an aux edge is the builder's business (dropped with a note), not a brief defect
    aux_row = "| 11 | apigw → cw | metrics, logs | aux (dashed) |"
    _, warnings = sc.scaffold(brief.replace(aux_row, "| 11 | apigw → cw | AccessLogsAndExecutionMetrics | aux (dashed) |"), STENCILS)
    assert warnings == []
    # "—" means: no text on this edge
    spec, _ = sc.scaffold(brief.replace(row, "| 2 | apigw → sqs | — | sync |"), STENCILS)
    assert "label" not in next(e for e in spec["edges"] if (e["from"], e["to"]) == ("apigw", "sqs"))
    # end to end: the scaffold exits 1 and writes no diagram
    (tmp_path / "op.brief.md").write_text(brief.replace(row, "| 2 | apigw → sqs | OrderMessagePayloadEnvelope | sync |"))
    r = subprocess.run([sys.executable, str(SCRIPTS / "scaffold_spec.py"), str(tmp_path / "op.brief.md"), str(tmp_path / "op.json")],
                       capture_output=True, text=True)
    assert r.returncode == 1 and "can never fit" in r.stdout, r.stdout
    assert sc.main([str(SAMPLES / "order-pipeline.brief.md"), "/tmp/_op_scaffold_check.json"]) == 0


def test_planner_closes_empty_columns():
    spec = _two_group_spec([{"from": "u", "to": "gw"}, {"from": "gw", "to": "fn"}, {"from": "fn", "to": "db"}])
    p = layout.Placement(spec, seed=1)
    p.col = {"u": 0, "gw": 1, "fn": 2, "auth": 1, "cache": 2, "db": 5}        # columns 3 and 4 hold nothing
    p.lane = {"u": 0, "gw": 0, "fn": 0, "auth": 1, "cache": 1, "db": 0}
    p.compact_columns()
    assert p.col["db"] == 3 and p.col["u"] == 0 and p.max_col == 3


def test_scaffold_numbers_edges_from_the_brief_hash_column():
    brief = (SAMPLES / "order-pipeline.brief.md").read_text()
    spec, _ = sc.scaffold(brief, STENCILS)
    nums = {(e["from"], e["to"]): e.get("num") for e in spec["edges"]}
    assert nums[("mobile", "apigw")] == 1 and nums[("sqs", "dlq")] == 13 and nums[("sfn", "payment")] == 7
    assert all(isinstance(n, int) for n in nums.values())


KO_GUIDE = """# 주문 파이프라인

모바일 앱의 주문을 API Gateway가 받아 SQS에 넣고 Lambda가 처리한다.

## 단계별 흐름
1. **Mobile client → API Gateway** — 앱이 HTTPS로 REST 요청을 보낸다. (라벨 `requests`)
2. **API Gateway → SQS** — 주문 메시지를 큐에 넣고 202를 돌려준다. (라벨 `order message`)

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
| # | From → To | What flows | Kind |
|---|---|---|---|
| 1 | mobile → apigw | requests | sync |
| 2 | apigw → sqs | order message | sync |
"""


def test_check_guide_accepts_a_korean_guide_that_covers_every_relationship():
    import check_guide as cg
    errors, summary = cg.check_guide(KO_GUIDE, KO_BRIEF)
    assert errors == [] and "2 relationships → 2 steps" in summary and "ko" in summary, (errors, summary)


def test_check_guide_rejects_wrong_language_missing_steps_and_missing_services():
    import check_guide as cg
    english = KO_GUIDE.replace("앱이 HTTPS로 REST 요청을 보낸다", "The app sends REST requests over HTTPS").replace(
        "주문 메시지를 큐에 넣고 202를 돌려준다", "puts the order on the queue and returns 202").replace(
        "모바일 앱의 주문을 API Gateway가 받아 SQS에 넣고 Lambda가 처리한다", "Orders from the mobile app enter through API Gateway into SQS").replace(
        "라벨", "label")
    errors, _ = cg.check_guide(english, KO_BRIEF)
    assert any("Language: ko" in e for e in errors), errors
    # step 2 missing → the relationship it should describe is named
    errors, _ = cg.check_guide(KO_GUIDE.replace("2. **API Gateway → SQS** — 주문 메시지를 큐에 넣고 202를 돌려준다. (라벨 `order message`)\n", ""), KO_BRIEF)
    assert any("apigw → sqs" in e and "step 2" in e for e in errors), errors
    # step exists but names the wrong endpoint
    errors, _ = cg.check_guide(KO_GUIDE.replace("2. **API Gateway → SQS**", "2. **API Gateway → DynamoDB**"), KO_BRIEF)
    assert any("step 2" in e and "SQS" in e for e in errors), errors
    # a component absent from the guide
    errors, _ = cg.check_guide(KO_GUIDE.replace("SQS", "큐"), KO_BRIEF)                # SQS named nowhere in the guide
    assert any("'sqs'" in e and "Services" in e for e in errors), errors
    # a step that does not quote the text drawn on its arrow
    errors, _ = cg.check_guide(KO_GUIDE.replace(" (라벨 `order message`)", ""), KO_BRIEF)
    assert any("step 2" in e and "order message" in e and "edge text" in e for e in errors), errors
    # "—" rows and rows not drawn are exempt from the quote rule
    dash = KO_BRIEF.replace("| 2 | apigw → sqs | order message | sync |", "| 2 | apigw → sqs | — | sync |")
    assert cg.check_guide(KO_GUIDE.replace(" (라벨 `order message`)", ""), dash)[0] == []


def test_check_guide_cli_on_the_shipped_sample():
    r = subprocess.run([sys.executable, str(SCRIPTS / "check_guide.py"), str(SAMPLES / "order-pipeline.guide.md"),
                        str(SAMPLES / "order-pipeline.brief.md")], capture_output=True, text=True)
    assert r.returncode == 0 and "guide check" in r.stdout and "✓" in r.stdout, r.stdout
