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
    assert errors == [] and codes(warnings) == ["W5"] and "'k'" in warnings[0]
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
