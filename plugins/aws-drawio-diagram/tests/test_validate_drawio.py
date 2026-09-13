import subprocess
import sys
from pathlib import Path

import pytest

PLUGIN = Path(__file__).resolve().parents[1]
SKILL = PLUGIN / "skills" / "aws-drawio-diagram"
SCRIPTS = SKILL / "scripts"
sys.path.insert(0, str(SCRIPTS))

import validate_drawio as vd  # noqa: E402

INDEX = vd.load_index()


def wrap(cells: str) -> str:
    return f"""<mxfile><diagram id="d" name="P"><mxGraphModel><root>
<mxCell id="0"/><mxCell id="1" parent="0"/>
{cells}
</root></mxGraphModel></diagram></mxfile>"""


SERVICE_OK = '<mxCell id="a" value="Lambda" style="sketch=0;fillColor=#ED7100;strokeColor=#ffffff;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.lambda;" vertex="1" parent="1"><mxGeometry x="0" y="0" width="78" height="78" as="geometry"/></mxCell>'
RESOURCE_OK = '<mxCell id="b" value="Fn" style="sketch=0;fillColor=#ED7100;strokeColor=none;shape=mxgraph.aws4.lambda_function;" vertex="1" parent="1"><mxGeometry x="300" y="0" width="78" height="78" as="geometry"/></mxCell>'
EDGE_OK = '<mxCell id="e" style="edgeStyle=orthogonalEdgeStyle;strokeWidth=2;exitX=1;exitY=0.5;entryX=0;entryY=0.5;" edge="1" source="a" target="b" parent="1"><mxGeometry relative="1" as="geometry"/></mxCell>'


def codes(msgs):
    return sorted({m.split()[0] for m in msgs})


def test_clean_minimal_diagram_passes():
    errors, warnings = vd.validate_text(wrap(SERVICE_OK + RESOURCE_OK + EDGE_OK), INDEX)
    assert errors == [] and warnings == []


def test_unknown_stencil_is_error():
    bad = SERVICE_OK.replace("aws4.lambda;", "aws4.lambda_supreme;")
    errors, _ = vd.validate_text(wrap(bad), INDEX)
    assert codes(errors) == ["E1"] and "lambda_supreme" in errors[0]


def test_vidanov_broken_names_are_caught():
    bad = RESOURCE_OK.replace("lambda_function", "vpc_peering")
    errors, _ = vd.validate_text(wrap(bad), INDEX)
    assert codes(errors) == ["E1"]


def test_service_with_stroke_none_is_error():
    bad = SERVICE_OK.replace("strokeColor=#ffffff", "strokeColor=none")
    errors, _ = vd.validate_text(wrap(bad), INDEX)
    assert codes(errors) == ["E2"]


def test_resource_with_white_stroke_is_error():
    bad = RESOURCE_OK.replace("strokeColor=none", "strokeColor=#ffffff")
    errors, _ = vd.validate_text(wrap(bad), INDEX)
    assert codes(errors) == ["E2"]


def test_resource_stroke_none_is_case_insensitive():
    ok = RESOURCE_OK.replace("strokeColor=none", "strokeColor=NONE")
    errors, _ = vd.validate_text(wrap(ok), INDEX)
    assert errors == []


def test_product_icon_counts_as_service_level():
    ok = SERVICE_OK.replace("resourceIcon;resIcon=", "productIcon;prIcon=")
    errors, _ = vd.validate_text(wrap(ok), INDEX)
    assert errors == []


def test_legacy_group_vpc_badge_is_accepted_and_group_needs_container():
    grp = ('<mxCell id="g" value="VPC" style="shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_vpc;'
           'strokeColor=#8C4FFF;fillColor=none;" vertex="1" parent="1"><mxGeometry x="0" y="0" width="400" height="300" as="geometry"/></mxCell>')
    errors, warnings = vd.validate_text(wrap(grp), INDEX)
    assert codes(errors) == ["E4"]
    fixed = grp.replace("fillColor=none;", "fillColor=none;container=1;")
    errors, warnings = vd.validate_text(wrap(fixed), INDEX)
    assert errors == [] and codes(warnings) == ["W3"]


def test_edge_endpoint_and_orthogonal_warning():
    dangling = EDGE_OK.replace('target="b"', 'target="zzz"')
    errors, _ = vd.validate_text(wrap(SERVICE_OK + RESOURCE_OK + dangling), INDEX)
    assert codes(errors) == ["E3"]
    no_ports = EDGE_OK.replace("exitX=1;exitY=0.5;entryX=0;entryY=0.5;", "")
    errors, warnings = vd.validate_text(wrap(SERVICE_OK + RESOURCE_OK + no_ports), INDEX)
    assert errors == [] and codes(warnings) == ["W1"]
    iso = no_ports.replace("orthogonalEdgeStyle", "isometricEdgeStyle")
    errors, warnings = vd.validate_text(wrap(SERVICE_OK + RESOURCE_OK + iso), INDEX)
    assert errors == [] and warnings == []


def test_duplicate_id_comment_and_compressed():
    errors, _ = vd.validate_text(wrap(SERVICE_OK + SERVICE_OK), INDEX)
    assert "E5" in codes(errors)
    errors, _ = vd.validate_text(wrap("<!-- note -->" + SERVICE_OK), INDEX)
    assert codes(errors) == ["E6"]
    compressed = '<mxfile><diagram id="d" name="P">eJxTKM5ILEhVAAA=</diagram></mxfile>'
    errors, _ = vd.validate_text(compressed, INDEX)
    assert codes(errors) == ["E6"]
    xxe = '<!DOCTYPE x [<!ENTITY e SYSTEM "file:///etc/passwd">]>' + wrap(SERVICE_OK)
    errors, _ = vd.validate_text(xxe, INDEX)
    assert codes(errors) == ["E6"]


def test_missing_fill_is_warning():
    nofill = SERVICE_OK.replace("fillColor=#ED7100;", "")
    errors, warnings = vd.validate_text(wrap(nofill), INDEX)
    assert errors == [] and codes(warnings) == ["W2"]


@pytest.mark.parametrize("tpl", sorted((SKILL / "templates").glob("*.drawio")), ids=lambda p: p.name)
def test_shipped_templates_have_no_errors(tpl):
    errors, _ = vd.validate_file(tpl, INDEX)
    assert errors == []


def test_cli_exit_codes(tmp_path):
    good = tmp_path / "good.drawio"
    good.write_text(wrap(SERVICE_OK + RESOURCE_OK + EDGE_OK))
    bad = tmp_path / "bad.drawio"
    bad.write_text(wrap(SERVICE_OK.replace("strokeColor=#ffffff", "strokeColor=none")))
    ok = subprocess.run([sys.executable, str(SCRIPTS / "validate_drawio.py"), str(good)], capture_output=True, text=True)
    assert ok.returncode == 0 and "0 errors" in ok.stdout
    ko = subprocess.run([sys.executable, str(SCRIPTS / "validate_drawio.py"), str(bad)], capture_output=True, text=True)
    assert ko.returncode == 1 and "E2" in ko.stdout


def test_w4_unaligned_edge_and_w5_blocked_corridor():
    # RESOURCE_OK sits at (300,0); a target at (300,300) is aligned vertically with it,
    # while a third icon parked on that corridor triggers W5.
    below = RESOURCE_OK.replace('id="b"', 'id="c"').replace('x="300" y="0"', 'x="300" y="300"')
    blocker = RESOURCE_OK.replace('id="b"', 'id="k"').replace('x="300" y="0"', 'x="300" y="150"')
    edge_bc = EDGE_OK.replace('id="e"', 'id="e2"').replace('source="a"', 'source="b"').replace('target="b"', 'target="c"')
    errors, warnings = vd.validate_text(wrap(SERVICE_OK + RESOURCE_OK + below + blocker + edge_bc), INDEX)
    assert errors == [] and codes(warnings) == ["W5", "W9"] and "'k'" in warnings[0]     # W9: 'a' and 'k' float
    diagonal = RESOURCE_OK.replace('id="b"', 'id="d"').replace('x="300" y="0"', 'x="420" y="260"')
    edge_ad = EDGE_OK.replace('id="e"', 'id="e3"').replace('target="b"', 'target="d"')
    errors, warnings = vd.validate_text(wrap(SERVICE_OK + diagonal + edge_ad), INDEX)
    assert errors == [] and codes(warnings) == ["W4"]


def test_layout_checks_resolve_container_offsets():
    grp = ('<mxCell id="g" value="VPC" style="shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_vpc2;'
           'strokeColor=#8C4FFF;fillColor=none;container=1;dropTarget=1;" vertex="1" parent="1">'
           '<mxGeometry x="100" y="100" width="600" height="300" as="geometry"/></mxCell>')
    inside = RESOURCE_OK.replace('id="b"', 'id="b"').replace('parent="1"', 'parent="g"').replace('x="300" y="0"', 'x="200" y="-100"')
    # absolute position of b = (300, 0): aligned with a at (0,0) → clean
    errors, warnings = vd.validate_text(wrap(SERVICE_OK + grp + inside + EDGE_OK), INDEX)
    assert errors == [] and warnings == []


CLOUD = ('<mxCell id="cloud" value="AWS Cloud" style="shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_aws_cloud_alt;'
         'strokeColor=#232F3E;fillColor=none;container=1;dropTarget=1;" vertex="1" parent="1">'
         '<mxGeometry x="200" y="100" width="800" height="600" as="geometry"/></mxCell>')
ROLE_GROUP = ('<mxCell id="g1" value="Frontend" style="rounded=0;fillColor=#F7F8FA;strokeColor=#C9D1D9;container=1;dropTarget=1;" '
              'vertex="1" parent="cloud"><mxGeometry x="40" y="60" width="200" height="300" as="geometry"/></mxCell>')


def icon(cid, parent, x, y):
    return (f'<mxCell id="{cid}" value="{cid}" style="sketch=0;fillColor=#ED7100;strokeColor=#ffffff;'
            f'shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.lambda;" vertex="1" parent="{parent}">'
            f'<mxGeometry x="{x}" y="{y}" width="78" height="78" as="geometry"/></mxCell>')


def test_w6_icon_inside_cloud_but_not_in_a_role_group():
    # 'good' is a child of a role group; 'loose' sits geometrically inside the cloud but is parented to the
    # canvas; 'direct' is parented to the cloud itself. Users outside the cloud never warn.
    good = icon("good", "g1", 61, 100)
    loose = icon("loose", "1", 600, 300)
    direct = icon("direct", "cloud", 500, 400)
    users = icon("users", "1", 20, 300)
    errors, warnings = vd.validate_text(wrap(CLOUD + ROLE_GROUP + good + loose + direct + users), INDEX)
    assert errors == []
    w6 = [w for w in warnings if w.startswith("W6")]
    assert len(w6) == 2 and any("'loose'" in w for w in w6) and any("'direct'" in w for w in w6)
    assert not any("'good'" in w or "'users'" in w for w in warnings)


def test_w6_silent_without_a_cloud_group():
    errors, warnings = vd.validate_text(wrap(icon("a", "1", 0, 0)), INDEX)
    assert errors == [] and codes(warnings) == []


def edge_cell(cid, src, dst, ports, label=""):
    val = f' value="{label}"' if label else ""
    return (f'<mxCell id="{cid}"{val} style="edgeStyle=orthogonalEdgeStyle;strokeWidth=2;{ports}" edge="1" '
            f'source="{src}" target="{dst}" parent="1"><mxGeometry relative="1" as="geometry"/></mxCell>')


UP_THEN_RIGHT = "exitX=0.5;exitY=0;entryX=0;entryY=0.5;"
RIGHT_TO_LEFT = "exitX=1;exitY=0.5;entryX=0;entryY=0.5;"


def test_fan_out_l_edge_with_matching_ports_is_accepted():
    # Source at column 300 lane 300; upper target one column right, one lane up.
    # Exit top + enter left = a single bend: no W4.
    src = icon("s", "1", 300, 300)
    upper = icon("t", "1", 540, 130)
    errors, warnings = vd.validate_text(wrap(src + upper + edge_cell("e", "s", "t", UP_THEN_RIGHT)), INDEX)
    assert errors == [] and warnings == []
    # Same geometry with side-to-side ports needs an S-shape (two bends): W4.
    _, warnings = vd.validate_text(wrap(src + upper + edge_cell("e", "s", "t", RIGHT_TO_LEFT)), INDEX)
    assert codes(warnings) == ["W4"]
    # An icon parked on the horizontal leg of the L triggers W5.
    blocker = icon("k", "1", 420, 130)
    _, warnings = vd.validate_text(wrap(src + upper + blocker + edge_cell("e", "s", "t", UP_THEN_RIGHT)), INDEX)
    assert codes(warnings) == ["W5", "W9"] and "'k'" in warnings[0] and "'k'" in warnings[1]   # W9: k floats


def test_w7_edge_label_on_a_group_border():
    # Two role groups 40 px apart; a labelled edge between their icons puts the label on the border.
    g1 = ('<mxCell id="g1" value="A" style="rounded=0;fillColor=#F7F8FA;strokeColor=#C9D1D9;container=1;dropTarget=1;" '
          'vertex="1" parent="1"><mxGeometry x="280" y="160" width="200" height="220" as="geometry"/></mxCell>')
    g2 = g1.replace('id="g1"', 'id="g2"').replace('x="280"', 'x="520"')
    a = icon("a", "g1", 61, 100)     # abs (341, 260)
    b = icon("b", "g2", 61, 100)     # abs (581, 260)
    _, warnings = vd.validate_text(wrap(g1 + g2 + a + b + edge_cell("e", "a", "b", RIGHT_TO_LEFT, "On completion")), INDEX)
    assert codes(warnings) == ["W7"]
    # Unlabelled: silent. Labelled but both nodes inside the same group: silent.
    _, warnings = vd.validate_text(wrap(g1 + g2 + a + b + edge_cell("e", "a", "b", RIGHT_TO_LEFT)), INDEX)
    assert warnings == []
    wide = g1.replace('width="200"', 'width="500"')
    b_in = icon("b", "g1", 301, 100)
    _, warnings = vd.validate_text(wrap(wide + a + b_in + edge_cell("e", "a", "b", RIGHT_TO_LEFT, "alarm")), INDEX)
    assert warnings == []


def test_w7_respects_relative_label_offset():
    # Users outside the cloud → first icon inside. The midpoint label sits on the cloud border (x=200);
    # shifting it toward the source (mxGeometry x=-0.4) clears it.
    users = icon("u", "1", 1, 391)           # right edge at 79
    cf = icon("cf", "cloud", 121, 291)       # abs (321, 391): same lane, edge midpoint = 200
    mid = edge_cell("e", "u", "cf", RIGHT_TO_LEFT, "HTTPS")
    _, warnings = vd.validate_text(wrap(CLOUD + ROLE_GROUP + users + cf + mid), INDEX)
    assert "W7" in codes(warnings)
    shifted = mid.replace('<mxGeometry relative="1" as="geometry"/>', '<mxGeometry x="-0.4" relative="1" as="geometry"/>')
    _, warnings = vd.validate_text(wrap(CLOUD + ROLE_GROUP + users + cf + shifted), INDEX)
    assert "W7" not in codes(warnings)


def test_long_l_edge_is_accepted_when_its_legs_are_empty():
    src = icon("s", "1", 300, 300)
    far = icon("t", "1", 780, 130)               # two columns right, one lane up: one bend, long horizontal leg
    _, warnings = vd.validate_text(wrap(src + far + edge_cell("e", "s", "t", UP_THEN_RIGHT)), INDEX)
    assert warnings == []
    blocker = icon("k", "1", 540, 130)           # parked on the horizontal leg
    _, warnings = vd.validate_text(wrap(src + far + blocker + edge_cell("e", "s", "t", UP_THEN_RIGHT)), INDEX)
    assert codes(warnings) == ["W5", "W9"]


def test_w8_two_edges_sharing_a_segment():
    src = icon("s", "1", 300, 300)
    up_right = icon("a", "1", 540, 130)
    up_left = icon("b", "1", 60, 130)
    e1 = edge_cell("e1", "s", "a", UP_THEN_RIGHT)
    e2 = edge_cell("e2", "s", "b", "exitX=0.5;exitY=0;entryX=1;entryY=0.5;")
    # Two bends leaving the same side of one node share their trunk: a bus, not an overlap.
    _, warnings = vd.validate_text(wrap(src + up_right + up_left + e1 + e2), INDEX)
    assert warnings == []
    # One leaving, one arriving on that trunk → two arrowheads on one line: W8.
    back = edge_cell("e3", "a", "s", "exitX=0;exitY=0.5;entryX=0.5;entryY=0;")
    _, warnings = vd.validate_text(wrap(src + up_right + e1 + back), INDEX)
    assert codes(warnings) == ["W8"]
    # Two edges into the same node from opposite sides do not share a segment.
    left = icon("l", "1", 60, 300)
    right = icon("r", "1", 540, 300)
    _, warnings = vd.validate_text(wrap(src + left + right + edge_cell("e1", "l", "s", RIGHT_TO_LEFT) +
                                        edge_cell("e2", "s", "r", RIGHT_TO_LEFT)), INDEX)
    assert warnings == []


def test_w7_checks_labels_on_bent_edges():
    # s (centre 380,469) bends up then right into t (centre 620,299): path length 332, so the label sits
    # 35 px into the horizontal leg at x≈415 — exactly where g2's left border is.
    g1 = ('<mxCell id="g1" value="A" style="rounded=0;fillColor=#F7F8FA;strokeColor=#C9D1D9;container=1;dropTarget=1;" '
          'vertex="1" parent="1"><mxGeometry x="280" y="160" width="200" height="390" as="geometry"/></mxCell>')
    g2 = ('<mxCell id="g2" value="B" style="rounded=0;fillColor=#F7F8FA;strokeColor=#C9D1D9;container=1;dropTarget=1;" '
          'vertex="1" parent="1"><mxGeometry x="415" y="160" width="300" height="220" as="geometry"/></mxCell>')
    s = icon("s", "g1", 61, 270)          # abs (341, 430)
    t = icon("t", "g2", 166, 100)         # abs (581, 260)
    lbl = edge_cell("e", "s", "t", UP_THEN_RIGHT, "put")
    _, warnings = vd.validate_text(wrap(g1 + g2 + s + t + lbl), INDEX)
    assert codes(warnings) == ["W7"]
    # unlabelled: clean
    _, warnings = vd.validate_text(wrap(g1 + g2 + s + t + edge_cell("e", "s", "t", UP_THEN_RIGHT)), INDEX)
    assert warnings == []


DOWN_UNDER_LABEL = "exitX=0.5;exitY=1.282;exitPerimeter=0;entryX=0.5;entryY=0;"


def test_w7_catches_a_vertical_label_on_a_group_title():
    # Two group rows in one column (builder grid: lane 0 centre y=260, lane 1 in the next row y=480).
    # The edge leaves under s's label (y=321) and enters t's top (y=441); midpoint 381 = g_bot's top border.
    g_top = ('<mxCell id="g_top" value="Compute" style="rounded=0;fillColor=#F7F8FA;strokeColor=#C9D1D9;container=1;dropTarget=1;" '
             'vertex="1" parent="1"><mxGeometry x="280" y="161" width="200" height="184" as="geometry"/></mxCell>')
    g_bot = ('<mxCell id="g_bot" value="Data" style="rounded=0;fillColor=#F7F8FA;strokeColor=#C9D1D9;container=1;dropTarget=1;" '
             'vertex="1" parent="1"><mxGeometry x="280" y="381" width="200" height="184" as="geometry"/></mxCell>')
    s = icon("s", "g_top", 61, 60)        # abs (341, 221)
    t = icon("t", "g_bot", 61, 60)        # abs (341, 441)
    base = edge_cell("e", "s", "t", DOWN_UNDER_LABEL, "Valkey 6379")
    # x=0.23 → label centre y≈395: clears the border (381) but sits on g_bot's title row → W7 naming the title
    on_title = base.replace('<mxGeometry relative="1" as="geometry"/>', '<mxGeometry x="0.23" relative="1" as="geometry"/>')
    _, warnings = vd.validate_text(wrap(g_top + g_bot + s + t + on_title), INDEX)
    assert codes(warnings) == ["W7"] and "title" in warnings[0], warnings
    # x=0.75 → centre y≈426: below the title band (381 + 28), above the icon (441) → clean
    # (x=0.6 would put the box top at 408.9992, a hair inside the band — the pocket is 32 px, aim for its middle)
    below_title = base.replace('<mxGeometry relative="1" as="geometry"/>', '<mxGeometry x="0.75" relative="1" as="geometry"/>')
    _, warnings = vd.validate_text(wrap(g_top + g_bot + s + t + below_title), INDEX)
    assert warnings == [], warnings


def test_w7_measures_wrapped_labels_and_follows_the_alignment():
    g1 = ('<mxCell id="g1" value="A" style="rounded=0;fillColor=#F7F8FA;strokeColor=#C9D1D9;container=1;dropTarget=1;" '
          'vertex="1" parent="1"><mxGeometry x="280" y="160" width="200" height="220" as="geometry"/></mxCell>')
    g2 = ('<mxCell id="g2" value="B" style="rounded=0;fillColor=#F7F8FA;strokeColor=#C9D1D9;container=1;dropTarget=1;" '
          'vertex="1" parent="1"><mxGeometry x="520" y="160" width="200" height="220" as="geometry"/></mxCell>')
    a = icon("a", "g1", 61, 100)     # abs (341, 260); right edge 419 — g1's border at 480: a 61 px pocket
    b = icon("b", "g2", 61, 100)     # abs (581, 260)
    # 'put order' on one line (72 px) cannot sit in the pocket: centred at x=-0.6 → 449 it covers the border
    one_line = edge_cell("e", "a", "b", RIGHT_TO_LEFT + "verticalAlign=bottom;", "put order").replace(
        '<mxGeometry relative="1" as="geometry"/>', '<mxGeometry x="-0.6" relative="1" as="geometry"/>')
    _, warnings = vd.validate_text(wrap(g1 + g2 + a + b + one_line), INDEX)
    assert codes(warnings) == ["W7"] and "border" in warnings[0], warnings
    # wrapped into two lines (47 px wide) at the same spot it fits — the validator measures the longest LINE
    two_lines = one_line.replace('value="put order"', 'value="put&lt;br&gt;order"')
    _, warnings = vd.validate_text(wrap(g1 + g2 + a + b + two_lines), INDEX)
    assert warnings == [], warnings
    # a label centred ON the line (no alignment flag) that another edge runs through is a W7 too
    c = icon("c", "g1", 61, 30)      # abs (341, 190), above a
    down = edge_cell("f", "c", "a", "exitX=0.5;exitY=1.282;exitPerimeter=0;entryX=0.5;entryY=0;")
    across = edge_cell("e", "a", "b", RIGHT_TO_LEFT, "x").replace(
        '<mxGeometry relative="1" as="geometry"/>', '<mxGeometry x="-0.9" relative="1" as="geometry"/>')
    _, warnings = vd.validate_text(wrap(g1 + g2 + a + b + c + down + across), INDEX)
    assert any(w.startswith("W7") and ("icon" in w or "line of edge" in w) for w in warnings), warnings


def test_w7_label_covering_an_icon_or_another_label():
    a = icon("a", "1", 300, 300)
    b = icon("b", "1", 540, 300)                                   # same lane, 162 px clear between the icons
    near_b = edge_cell("e", "a", "b", RIGHT_TO_LEFT + "verticalAlign=bottom;", "HTTPS").replace(
        '<mxGeometry relative="1" as="geometry"/>', '<mxGeometry x="0.97" relative="1" as="geometry"/>')
    _, warnings = vd.validate_text(wrap(a + b + near_b), INDEX)
    assert codes(warnings) == ["W7"] and "icon" in warnings[0], warnings
    c = icon("c", "1", 300, 60)                                    # above a: a vertical edge c → a beside the horizontal one
    down = edge_cell("f", "c", "a", "exitX=0.5;exitY=1.282;exitPerimeter=0;entryX=0.5;entryY=0;align=right;spacingRight=4;", "session lookup")
    _, warnings = vd.validate_text(wrap(a + b + c + down + edge_cell("e", "a", "b", RIGHT_TO_LEFT + "verticalAlign=bottom;", "HTTPS")), INDEX)
    assert warnings == [], warnings                                # two labels, different places: clean
