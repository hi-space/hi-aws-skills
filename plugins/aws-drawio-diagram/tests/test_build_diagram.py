import json
import sys
from pathlib import Path

import pytest

PLUGIN = Path(__file__).resolve().parents[1]
SKILL = PLUGIN / "skills" / "aws-drawio-diagram"
SCRIPTS = SKILL / "scripts"
SAMPLES = PLUGIN / "docs" / "samples"
sys.path.insert(0, str(SCRIPTS))

import build_diagram as bd  # noqa: E402
import validate_drawio as vd  # noqa: E402

INDEX = vd.load_index()


def spec(**over):
    base = {
        "title": "T",
        "groups": [{"id": "g", "label": "G", "cols": [1, 2], "lanes": [0, 1]}],
        "nodes": [
            {"id": "u", "label": "Users", "icon": "users", "col": 0, "lane": 1, "outside": True},
            {"id": "a", "label": "API Gateway", "icon": "api_gateway", "col": 1, "lane": 1, "group": "g"},
            {"id": "b", "label": "Lambda", "icon": "lambda", "col": 2, "lane": 1, "group": "g"},
            {"id": "c", "label": "Cognito", "icon": "cognito", "col": 1, "lane": 0, "group": "g"},
        ],
        "edges": [{"from": "u", "to": "a", "label": "HTTPS"}, {"from": "a", "to": "b"}, {"from": "a", "to": "c", "dashed": True}],
    }
    base.update(over)
    return base


def styles(xml: str) -> dict[str, dict[str, str]]:
    import xml.etree.ElementTree as ET
    return {c.get("id"): vd.parse_style(c.get("style")) for c in ET.fromstring(xml).iter("mxCell")}


@pytest.mark.parametrize("name", ["agentic-rag-chat", "order-pipeline", "iot-telemetry"])
def test_shipped_sample_specs_build_clean(name):
    xml = bd.build(json.loads((SAMPLES / f"{name}.json").read_text()))
    errors, warnings = vd.validate_text(xml, INDEX)
    assert errors == [] and warnings == []
    # the committed .drawio is the build output of the committed spec
    assert (SAMPLES / f"{name}.drawio").read_text() == xml


def test_grid_and_group_arithmetic():
    b = bd.Builder(spec(), json.loads(bd.INDEX.read_text()))
    assert b.cx(0) == 140 and b.cx(1) == 380 and b.cx(2) == 620
    assert b.ly(0) == 260 and b.ly(1) == 430
    x, y, w, h = b.group_rect(b.groups["g"])
    assert (x, w) == (280, 440)                 # two columns: 200 + 40 + 200
    assert (y, h) == (260 - 39 - 60, 170 + 78 + 60 + 46)


def test_row_break_inserted_between_stacked_groups():
    s = spec(groups=[{"id": "g", "label": "G", "cols": [1, 2], "lanes": [0, 1]},
                     {"id": "h", "label": "H", "cols": [1], "lanes": [2]}])
    s["nodes"].append({"id": "d", "label": "CloudWatch", "icon": "cloudwatch_2", "col": 1, "lane": 2, "group": "h"})
    b = bd.Builder(s, json.loads(bd.INDEX.read_text()))
    assert b.row_breaks == [2]
    assert b.ly(2) == 260 + 340 + 50


def test_node_labels_are_bold_13():
    st = styles(bd.build(spec()))
    for nid in ("u", "a", "b", "c"):
        assert st[nid]["fontSize"] == "13" and st[nid]["fontStyle"] == "1", nid
    img = spec()
    img["nodes"][2] = {"id": "b", "label": "Memory", "image": "Res_Amazon-Bedrock-AgentCore_Memory_48.svg",
                       "col": 2, "lane": 1, "group": "g"}
    st = styles(bd.build(img))
    assert st["b"]["fontSize"] == "13" and st["b"]["fontStyle"] == "1"


def test_labels_always_below_with_container_background():
    xml = bd.build(spec())
    st = styles(xml)
    for nid in ("u", "a", "b", "c"):
        assert st[nid]["verticalLabelPosition"] == "bottom" and st[nid]["align"] == "center", nid
        assert "labelPosition" not in st[nid]
    assert st["u"]["labelBackgroundColor"] == "#FFFFFF"           # outside the cloud
    assert st["a"]["labelBackgroundColor"] == "#F7F8FA"           # inside a role group
    # bottom-touching edges attach under the label, not on the icon edge
    e_ac = styles(xml)["e3"]                                        # a (lane 1) → c (lane 0): enters c's bottom
    assert e_ac["entryY"] == "1.282" and e_ac["entryPerimeter"] == "0"
    assert e_ac["exitY"] == "0"


def test_long_labels_wrap_and_lower_the_bottom_port():
    s = spec()
    s["nodes"][3]["label"] = "OpenSearch Serverless (vector index)"
    xml = bd.build(s)
    assert 'value="OpenSearch Serverless&lt;br&gt;(vector index)"' in xml
    assert styles(xml)["e3"]["entryY"] == "1.513"
    assert bd.Builder.wrap("Kinesis Data Streams") == "Kinesis Data Streams"   # 20 chars: one line
    assert bd.Builder.wrap("Amazon OpenSearch Service domain") == "Amazon OpenSearch<br>Service domain"


def test_fan_out_uses_vertical_exit_and_horizontal_entry():
    # b at (2,1) fans out to e at (3,0): exit top, one bend, enter left. Nothing sits on either leg.
    s = spec(groups=[{"id": "g", "label": "G", "cols": [1, 2, 3], "lanes": [0, 1]}])
    s["nodes"].append({"id": "e", "label": "Payment", "icon": "lambda", "col": 3, "lane": 0, "group": "g"})
    s["edges"].append({"from": "b", "to": "e"})
    xml = bd.build(s)
    st = styles(xml)
    fan = st["e4"]
    assert (fan["exitX"], fan["exitY"], fan["entryX"], fan["entryY"]) == ("0.5", "0", "0", "0.5")
    # corner pinned at (source centre x, target centre y) so the first leg is always vertical
    assert '<Array as="points"><mxPoint x="620" y="260"/></Array>' in xml
    errors, warnings = vd.validate_text(xml, INDEX)
    assert errors == [] and warnings == []


def test_outside_label_is_shifted_off_the_cloud_border():
    xml = bd.build(spec())
    import xml.etree.ElementTree as ET
    cells = {c.get("id"): c for c in ET.fromstring(xml).iter("mxCell")}
    assert float(cells["e1"].find("mxGeometry").get("x")) < 0            # slid toward the users, off the cloud border
    # users sit OUTSIDE_GAP further left than the grid column, so the pocket outside the cloud holds real text
    assert float(cells["u"].find("mxGeometry").get("x")) == 140 - 39 - bd.OUTSIDE_GAP
    assert vd.validate_text(xml, INDEX) == ([], [])


def test_image_node_and_no_cloud():
    s = spec(cloud=False)
    s["nodes"].append({"id": "m", "label": "Memory", "image": "Res_Amazon-Bedrock-AgentCore_Memory_48.svg",
                       "col": 2, "lane": 0, "group": "g"})
    xml = bd.build(s)
    assert 'id="cloud"' not in xml and "shape=image" in xml and "data:image/svg+xml," in xml
    assert vd.validate_text(xml, INDEX)[0] == []


@pytest.mark.parametrize("mutate, message", [
    (lambda s: s["nodes"][1].update(icon="lambda_supreme"), "unknown stencil"),
    (lambda s: s["nodes"][1].pop("group"), "no 'group'"),
    (lambda s: s["nodes"][1].update(col=2), "share cell"),
    (lambda s: s["nodes"][1].update(col=4), "outside group"),
    (lambda s: s["groups"].append({"id": "h", "label": "H", "cols": [2], "lanes": [1]}), "overlap"),
    (lambda s: s["edges"].append({"from": "a", "to": "zzz"}), "must name a node"),
    (lambda s: s["edges"].append({"from": "b", "to": "b", "dashed": True}), "cannot connect to itself"),
])
def test_spec_errors(mutate, message):
    s = spec()
    mutate(s)
    with pytest.raises(bd.SpecError, match=message):
        bd.build(s)


def test_cli(tmp_path):
    import subprocess
    p = tmp_path / "s.json"
    p.write_text(json.dumps(spec()))
    out = tmp_path / "s.drawio"
    r = subprocess.run([sys.executable, str(SCRIPTS / "build_diagram.py"), str(p), str(out)], capture_output=True, text=True)
    assert r.returncode == 0 and out.exists() and "0 errors, 0 warnings" in r.stdout
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps(spec(nodes=[])))
    r = subprocess.run([sys.executable, str(SCRIPTS / "build_diagram.py"), str(bad), str(out)], capture_output=True, text=True)
    assert r.returncode == 1 and "ERROR spec" in r.stdout


def test_builder_rejects_far_bends_and_shared_sides():
    s = spec(groups=[{"id": "g", "label": "G", "cols": [1, 2, 3, 4], "lanes": [0, 1, 2]}])
    s["nodes"].append({"id": "far", "label": "Far", "icon": "s3", "col": 4, "lane": 0, "group": "g"})
    s["edges"].append({"from": "b", "to": "far"})                    # (2,1) → (4,0): a long L, both legs empty → fine
    assert vd.validate_text(bd.build(s), INDEX) == ([], [])
    s["nodes"] += [{"id": "k1", "label": "K1", "icon": "sns", "col": 2, "lane": 0, "group": "g"},   # blocks the trunk
                   {"id": "k2", "label": "K2", "icon": "sqs", "col": 3, "lane": 1, "group": "g"}]   # blocks the other L
    s["edges"] += [{"from": "c", "to": "k1"}, {"from": "k2", "to": "far"}]
    with pytest.raises(bd.SpecError, match="cannot be joined"):
        bd.build(s)
    s["edges"] = s["edges"][:-3]
    s["nodes"] = s["nodes"][:-3]
    s["nodes"].append({"id": "dn", "label": "Down", "icon": "sns", "col": 3, "lane": 2, "group": "g"})
    s["nodes"].append({"id": "up", "label": "Up", "icon": "sqs", "col": 3, "lane": 0, "group": "g"})
    s["edges"] += [{"from": "b", "to": "dn"}, {"from": "b", "to": "up"}]  # one leaves bottom, one leaves top: fine
    assert vd.validate_text(bd.build(s), INDEX) == ([], [])
    s["nodes"].append({"id": "dn2", "label": "Down2", "icon": "s3", "col": 1, "lane": 2, "group": "g"})
    s["edges"].append({"from": "b", "to": "dn2"})                    # second bend leaving the bottom: its own line
    xml = bd.build(s)
    assert vd.validate_text(xml, INDEX) == ([], [])
    # the lone top bend keeps the centre; the two bottom bends fan out 20 px apart, each on the side it turns to
    assert xml.count('<mxPoint x="620" y="') == 1
    assert xml.count('<mxPoint x="610" y="') == 1 and xml.count('<mxPoint x="630" y="') == 1
    s["nodes"].append({"id": "st", "label": "Straight", "icon": "kinesis", "col": 2, "lane": 2, "group": "g"})
    s["edges"].append({"from": "b", "to": "st"})                     # straight down between the two trunks
    with pytest.raises(bd.SpecError, match="one of them is straight|runs through"):
        bd.build(s)


def hub_spec(targets, edges=None, lanes=(0, 1, 2, 3, 4)):
    """A hub b at (2, 1) inside one wide group; `targets` are (id, col, lane) triples, each fed from b."""
    nodes = [{"id": "b", "label": "Hub", "icon": "lambda", "col": 2, "lane": 1, "group": "g"}]
    nodes += [{"id": i, "label": i.upper(), "icon": "s3", "col": c, "lane": l, "group": "g"} for i, c, l in targets]
    return {"title": "T", "groups": [{"id": "g", "label": "G", "cols": [1, 2, 3], "lanes": list(lanes)}],
            "nodes": nodes, "edges": edges if edges is not None else [{"from": "b", "to": i} for i, _, _ in targets]}


def crossings(paths):
    """Pairs of edges whose polylines cross (a horizontal leg of one cutting a vertical leg of the other)."""
    hits = []
    ids = sorted(paths)
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            for x1, y1, x2, y2 in bd.Builder.segments(paths[a]):
                for u1, v1, u2, v2 in bd.Builder.segments(paths[b]):
                    h, v = ((x1, y1, x2, y2), (u1, v1, u2, v2)) if y1 == y2 else ((u1, v1, u2, v2), (x1, y1, x2, y2))
                    if h[1] != h[3] or v[0] != v[2]:
                        continue
                    if min(h[0], h[2]) < v[0] < max(h[0], h[2]) and min(v[1], v[3]) < h[1] < max(v[1], v[3]):
                        hits.append((a, b))
    return hits


def test_split_trunks_give_every_bend_its_own_line_without_crossings():
    # Three bends leave the hub's bottom: two turn left (lanes 2 and 3), one turns right (lane 2).
    s = hub_spec([("l1", 1, 2), ("l2", 1, 3), ("r1", 3, 2)])
    b = bd.Builder(s, json.loads(bd.INDEX.read_text()))
    xml = b.build()
    assert vd.validate_text(xml, INDEX) == ([], [])
    st = styles(xml)
    # left-turners on the left, the right-turner on the right; the nearest left turn takes the outermost line
    ports = {eid: float(st[eid]["exitX"]) for eid in ("e1", "e2", "e3")}
    assert ports["e1"] < ports["e2"] == 0.5 < ports["e3"]                       # l1, l2 | r1
    assert [round((p - 0.5) * bd.ICON) for p in (ports["e1"], ports["e2"], ports["e3"])] == [-20, 0, 20]
    # the corner of each L sits on its own trunk, and the three lines never cross
    corners = {eid: xml.split(f'id="{eid}"')[1].split("mxPoint x=\"")[1].split('"')[0] for eid in ports}
    assert corners == {"e1": "600", "e2": "620", "e3": "640"}
    node_xy = {nid: (b.cx(n["col"]) - bd.ICON // 2, b.ly(n["lane"]) - bd.ICON // 2) for nid, n in b.nodes.items()}
    label_h = {nid: b.label_h(n) for nid, n in b.nodes.items()}
    offs = b.side_offsets()
    paths = {}
    for i, e in enumerate(s["edges"], 1):
        d, _, _, kind = b.edge_geometry(e, offs[f"e{i}"])
        paths[f"e{i}"] = b.edge_path(e, d, kind, node_xy, label_h, offs[f"e{i}"])
    assert crossings(paths) == []
    # every edge asks draw.io to hop over lines it crosses elsewhere
    assert all(st[eid]["jumpStyle"] == "arc" for eid in ports)


def test_fan_in_splits_the_arriving_lines_too():
    # Two sources in column 2 (one above, one below) bend into the target's left side at (3, 1).
    s = hub_spec([("s1", 2, 0), ("s2", 2, 2), ("t", 3, 1)],
                 edges=[{"from": "s1", "to": "t"}, {"from": "s2", "to": "t"}], lanes=(0, 1, 2))
    s["nodes"] = [n for n in s["nodes"] if n["id"] != "b"]
    xml = bd.build(s)
    assert vd.validate_text(xml, INDEX) == ([], [])
    st = styles(xml)
    assert (st["e1"]["entryX"], st["e2"]["entryX"]) == ("0", "0")
    assert float(st["e1"]["entryY"]) < 0.5 < float(st["e2"]["entryY"])          # from above enters higher


def test_arriving_and_leaving_bends_may_share_a_side():
    # b → dn leaves the bottom and turns right; src → b comes along lane 2 and climbs into the bottom (route h).
    s = hub_spec([("dn", 3, 2), ("src", 1, 2)],
                 edges=[{"from": "b", "to": "dn"}, {"from": "src", "to": "b", "route": "h"}], lanes=(0, 1, 2))
    xml = bd.build(s)
    assert vd.validate_text(xml, INDEX) == ([], [])
    st = styles(xml)
    assert float(st["e1"]["exitX"]) > 0.5 > float(st["e2"]["entryX"])


def test_more_than_three_bends_on_one_side_is_a_spec_error():
    s = hub_spec([("l1", 1, 2), ("l2", 1, 3), ("r1", 3, 2)])
    bd.build(s)                                                       # three fit
    s["nodes"].append({"id": "r2", "label": "R2", "icon": "s3", "col": 3, "lane": 3, "group": "g"})
    s["edges"].append({"from": "b", "to": "r2"})
    with pytest.raises(bd.SpecError, match="at most 3"):
        bd.build(s)


def test_bends_reach_two_lanes_down_when_the_column_is_empty():
    # A hub (b at col 2, lane 0) with five neighbours: left/right straight, three bends leaving the bottom side by
    # side, one of them two lanes down. The hub's own column stays empty below it.
    s = spec(groups=[{"id": "g", "label": "G", "cols": [1, 2, 3], "lanes": [0, 1, 2]}],
             nodes=[{"id": "u", "label": "Users", "icon": "users", "col": 0, "lane": 0, "outside": True},
                    {"id": "a", "label": "ALB", "icon": "elastic_load_balancing", "col": 1, "lane": 0, "group": "g"},
                    {"id": "b", "label": "FastAPI", "icon": "ecs_service", "col": 2, "lane": 0, "group": "g"},
                    {"id": "r", "label": "Runtime", "icon": "bedrock", "col": 3, "lane": 0, "group": "g"},
                    {"id": "c", "label": "Cognito", "icon": "cognito", "col": 1, "lane": 1, "group": "g"},
                    {"id": "d", "label": "DynamoDB", "icon": "dynamodb", "col": 3, "lane": 1, "group": "g"},
                    {"id": "s3", "label": "S3", "icon": "s3", "col": 3, "lane": 2, "group": "g"}],
             edges=[{"from": "u", "to": "a"}, {"from": "a", "to": "b"}, {"from": "b", "to": "r"},
                    {"from": "b", "to": "c"}, {"from": "b", "to": "d"}, {"from": "b", "to": "s3"}])
    xml = bd.build(s)
    assert vd.validate_text(xml, INDEX) == ([], [])
    # the corridor cell (2,1) must stay empty: park a node there and the builder names it
    s["nodes"].append({"id": "x", "label": "X", "icon": "sqs", "col": 2, "lane": 1, "group": "g"})
    s["edges"].append({"from": "c", "to": "x"})
    with pytest.raises(bd.SpecError, match="runs through 'x'"):
        bd.build(s)


def test_floating_icon_is_a_layout_defect(tmp_path):
    import subprocess
    s = spec()
    s["nodes"].append({"id": "lonely", "label": "S3", "icon": "s3", "col": 2, "lane": 0, "group": "g"})
    xml = bd.build(s)
    _, warnings = vd.validate_text(xml, INDEX)
    assert [w[:2] for w in warnings] == ["W9"] and "'lonely'" in warnings[0]
    p = tmp_path / "s.json"
    p.write_text(json.dumps(s))
    r = subprocess.run([sys.executable, str(SCRIPTS / "build_diagram.py"), str(p), str(tmp_path / "s.drawio")],
                       capture_output=True, text=True)
    assert r.returncode == 1 and "Layout defects" in r.stdout and "NOT CLEAN" in r.stdout


def test_builder_hints_about_sparse_groups(capsys):
    s = spec(groups=[{"id": "g", "label": "G", "cols": [1, 2, 3], "lanes": [0, 1, 2]}])
    bd.build(s)
    hints = bd.hints(s)
    assert any("g" in h and "empty" in h for h in hints)


BRIEF = """# T
## Components
| id | Service (stencil) | Role | Group |
|---|---|---|---|
| u | Users (`users`) | people | outside |
| a | API Gateway (`api_gateway`) | entry | G |
| b | Lambda (`lambda`) | handler | G |
| c | Cognito (`cognito`) | auth | G |
| dom | Cognito domain (not drawn) | token endpoint | G |

## Relationships
| # | From → To | What flows | Kind |
|---|---|---|---|
| 1 | u → a | HTTPS | sync |
| 2 | a → b | invoke | sync |
| 3 | a → c | token | aux (dashed) |
| 4 | b → c | JWKS | sync/aux |

## Flow
"""


def test_brief_check_passes_when_spec_matches_and_aux_may_be_omitted():
    errors, summary = bd.brief_check(BRIEF, spec())          # spec draws u→a, a→b, a→c; b→c (aux) omitted
    assert errors == []
    assert summary.startswith("brief check: 4 components → 4 nodes (1 marked not drawn); 4 relationships → 3 edges (1 aux not drawn)")


def test_brief_check_names_every_gap():
    s = spec()
    s["nodes"] = [n for n in s["nodes"] if n["id"] != "c"] + [{"id": "zz", "label": "S3", "icon": "s3", "col": 2, "lane": 0, "group": "g"}]
    s["edges"] = [{"from": "u", "to": "a"}, {"from": "b", "to": "zz"}]
    errors, _ = bd.brief_check(BRIEF, s)
    text = "\n".join(errors)
    assert "no node in the spec: c" in text
    assert "spec nodes the brief does not list: zz" in text
    assert "a → b" in text and "primary relationships are never dropped" in text
    assert "b → zz" in text


def test_cli_runs_the_brief_check_when_the_brief_sits_next_to_the_spec(tmp_path):
    import subprocess
    (tmp_path / "s.brief.md").write_text(BRIEF)
    p = tmp_path / "s.json"
    p.write_text(json.dumps(spec()))
    r = subprocess.run([sys.executable, str(SCRIPTS / "build_diagram.py"), str(p), str(tmp_path / "s.drawio")],
                       capture_output=True, text=True)
    assert r.returncode == 0 and "brief check: 4 components → 4 nodes" in r.stdout and "✓" in r.stdout
    small = spec()
    small["nodes"] = small["nodes"][:2]
    small["edges"] = small["edges"][:1]
    p.write_text(json.dumps(small))
    r = subprocess.run([sys.executable, str(SCRIPTS / "build_diagram.py"), str(p), str(tmp_path / "s.drawio")],
                       capture_output=True, text=True)
    assert r.returncode == 1 and "ERROR brief" in r.stdout and "NOT CLEAN" in r.stdout
    assert not (tmp_path / "s.drawio").exists() or "wrote" not in r.stdout
    r = subprocess.run([sys.executable, str(SCRIPTS / "build_diagram.py"), str(p), str(tmp_path / "s.drawio"), "--no-brief"],
                       capture_output=True, text=True)
    assert r.returncode == 0


def test_vertical_label_between_group_rows_clears_the_title_band():
    # a (row 1) → c (row 2, same column) with an 11-character label: the only free pocket is inside the
    # lower group, and the builder must put the label BELOW that group's title row, not on it.
    s = {
        "title": "t",
        "groups": [{"id": "g", "label": "Compute", "cols": [1], "lanes": [0]},
                   {"id": "h", "label": "Data", "cols": [1], "lanes": [1]}],
        "nodes": [{"id": "u", "label": "Users", "icon": "users", "col": 0, "lane": 0, "outside": True},
                  {"id": "a", "label": "API Gateway", "icon": "api_gateway", "col": 1, "lane": 0, "group": "g"},
                  {"id": "c", "label": "ElastiCache", "icon": "elasticache", "col": 1, "lane": 1, "group": "h"}],
        "edges": [{"from": "u", "to": "a"}, {"from": "a", "to": "c", "label": "Valkey 6379"}],
    }
    xml = bd.build(s)
    assert 'value="Valkey 6379"' in xml                      # the label survived
    assert vd.validate_text(xml, INDEX) == ([], [])          # and lands on neither a border nor a title


def test_bent_edge_carries_its_text_on_the_longer_leg():
    import xml.etree.ElementTree as ET
    s = spec()
    s["edges"].append({"from": "b", "to": "c", "label": "fetch JWKS keys"})    # an L: up from b, left into c
    xml = bd.build(s)
    cells = {c.get("id"): c for c in ET.fromstring(xml).iter("mxCell")}
    e4 = cells["e4"]
    assert e4.get("value") == "fetch JWKS keys"
    st = vd.parse_style(e4.get("style"))
    rel = float(e4.find("mxGeometry").get("x"))
    # legs: vertical 131 px (b's top to c's lane), horizontal 201 px (corner to c's right side) — the text goes
    # on the horizontal leg, i.e. past the corner (relative x > 2·131/332 − 1) and above the line
    assert rel > round(2 * 131 / 332 - 1, 3) and st["verticalAlign"] == "bottom" and st["align"] == "center"
    assert "edgeLabel" not in xml                                            # no number badges any more
    assert vd.validate_text(xml, INDEX) == ([], [])


def test_long_text_wraps_and_the_validator_measures_the_wrapped_box():
    s = spec()
    s["edges"][1]["label"] = "invoke with the validated order payload"      # a → b inside one box, 162 px
    xml = bd.build(s)
    # three lines, re-wrapped at the narrowest width that keeps three so they come out even
    assert 'value="invoke with&lt;br&gt;the validated&lt;br&gt;order payload"' in xml
    assert vd.validate_text(xml, INDEX) == ([], [])
    # a label pinned by hand at the source end lands on the users' icon: the validator says so
    s = spec()
    s["edges"][0]["label_offset"] = -0.98
    _, warnings = vd.validate_text(bd.build(s), INDEX)
    assert any(w.startswith("W7") and "icon" in w for w in warnings), warnings


def test_label_placement_avoids_other_edges_lines():
    # a's label on the vertical dashed edge to c must not be laid across the horizontal edge a → b
    s = spec()
    s["edges"][2]["label"] = "verify"
    xml = bd.build(s)
    assert vd.validate_text(xml, INDEX) == ([], [])
