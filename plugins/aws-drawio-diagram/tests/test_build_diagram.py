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
    e1 = next(c for c in ET.fromstring(xml).iter("mxCell") if c.get("id") == "e1")
    assert float(e1.find("mxGeometry").get("x")) < -0.3
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
    (lambda s: s["edges"].append({"from": "b", "to": "c", "label": "x"}), "bent edge cannot carry a label"),
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
    s["edges"].append({"from": "b", "to": "far"})                    # (2,1) → (4,0): not adjacent
    with pytest.raises(bd.SpecError, match="adjacent"):
        bd.build(s)
    s["edges"].pop()
    s["nodes"].append({"id": "dn", "label": "Down", "icon": "sns", "col": 3, "lane": 2, "group": "g"})
    s["nodes"].append({"id": "up", "label": "Up", "icon": "sqs", "col": 3, "lane": 0, "group": "g"})
    s["edges"] += [{"from": "b", "to": "dn"}, {"from": "b", "to": "up"}]  # one leaves bottom, one leaves top: fine
    assert vd.validate_text(bd.build(s), INDEX) == ([], [])
    s["nodes"].append({"id": "dn2", "label": "Down2", "icon": "s3", "col": 1, "lane": 2, "group": "g"})
    s["edges"].append({"from": "b", "to": "dn2"})                    # second bend leaving the bottom
    with pytest.raises(bd.SpecError, match="both use its"):
        bd.build(s)


def test_builder_hints_about_sparse_groups(capsys):
    s = spec(groups=[{"id": "g", "label": "G", "cols": [1, 2, 3], "lanes": [0, 1, 2]}])
    bd.build(s)
    hints = bd.hints(s)
    assert any("g" in h and "empty" in h for h in hints)
