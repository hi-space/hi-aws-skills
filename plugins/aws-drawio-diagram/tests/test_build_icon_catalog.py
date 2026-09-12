import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

PLUGIN = Path(__file__).resolve().parents[1]
SKILL = PLUGIN / "skills" / "aws-drawio-diagram"
SCRIPTS = SKILL / "scripts"
sys.path.insert(0, str(SCRIPTS))

import build_icon_catalog as bic  # noqa: E402

SIDEBAR = PLUGIN / "scripts" / "fixtures" / "Sidebar-AWS4.js"
NAMES = PLUGIN / "scripts" / "fixtures" / "aws4-stencil-names.txt"


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    out = tmp_path_factory.mktemp("refs")
    data = bic.extract(SIDEBAR)
    stencils, boundaries = bic.build_index(data, bic.load_stencil_names(NAMES))
    files = bic.render_markdown(stencils, boundaries, out)
    bic.write_index(stencils, out / "stencil-index.json", {"sidebar": "test", "stencils": "test"})
    return stencils, boundaries, files, out


def test_counts_meet_floors(built):
    stencils, _, _, _ = built
    kinds = {}
    for s in stencils.values():
        kinds[s["kind"]] = kinds.get(s["kind"], 0) + 1
    assert kinds["service"] >= 300
    assert kinds["resource"] >= 500
    assert kinds["group"] == 15                      # 15 distinct grIcons (subnets share group_security_group)
    assert kinds["legacy"] >= 50


def test_classification_examples(built):
    stencils, _, _, _ = built
    assert stencils["lambda"]["kind"] == "service"
    assert stencils["lambda"]["fillColor"] == "#ED7100"
    assert stencils["lambda_function"]["kind"] == "resource"
    assert stencils["group_vpc2"]["kind"] == "group"
    assert stencils["group_vpc"]["kind"] == "legacy"          # renders, not in palette
    assert stencils["quicksight"]["section"] == "retired"
    assert stencils["elasticsearch_service"]["kind"] == "service"


def test_classify_and_slug():
    assert bic.classify("a;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.ec2;") == ("service", "ec2")
    assert bic.classify("shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_region;") == ("group", "group_region")
    assert bic.classify("shape=mxgraph.aws4.instance2;") == ("resource", "instance2")
    assert bic.classify("fillColor=none;strokeColor=#147EBA;") == ("style", None)
    assert bic.slug_for("aws4Network Content Delivery") == "network-content-delivery"
    assert bic.slug_for("aws4r") == "retired"
    assert bic.slug_for("aws4Illustrations") == "general"


def test_every_template_stencil_is_in_index(built):
    stencils, _, _, _ = built
    used = set()
    for tpl in (SKILL / "templates").glob("*.drawio"):
        used |= set(re.findall(r"mxgraph\.aws4\.([A-Za-z0-9_]+)", tpl.read_text()))
    used -= set(bic.JS_SHAPES)
    missing = sorted(n for n in used if n not in stencils)
    assert missing == []


def test_markdown_files_and_headers(built):
    _, _, files, out = built
    names = sorted(p.name for p in files)
    assert "aws-icons-compute.md" in names
    assert "aws-icons-groups.md" in names
    assert "aws-icons-general.md" in names
    assert "aws-icons-retired.md" in names
    assert "aws-icons-legacy.md" in names
    compute = (out / "aws-icons-compute.md").read_text()
    assert compute.startswith("# AWS Icons: Compute")
    assert "Do not edit by hand" in compute
    assert "fillColor: `#ED7100`" in compute
    assert "| `lambda` | Lambda |" in compute
    assert "| `lambda_function` | Lambda Function |" in compute   # if the sidebar label differs, assert the real label
    groups = (out / "aws-icons-groups.md").read_text()
    assert "| `group_vpc2` | `#8C4FFF` | VPC |" in groups
    assert "Availability Zone" in groups           # boundary style without grIcon


def test_index_json_shape(built):
    _, _, _, out = built
    idx = json.loads((out / "stencil-index.json").read_text())
    assert set(idx) == {"generated_from", "js_shapes", "stencils"}
    assert idx["js_shapes"] == list(bic.JS_SHAPES)
    assert idx["stencils"]["s3"]["kind"] == "service"


def test_cli_fails_on_empty_source(tmp_path):
    bogus = tmp_path / "Sidebar-AWS4.js"
    bogus.write_text("Sidebar.prototype.addAWS4Palette = function() {};")
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / "build_icon_catalog.py"), "--sidebar", str(bogus),
         "--stencils", str(NAMES), "--out-dir", str(tmp_path / "refs"), "--index", str(tmp_path / "i.json")],
        capture_output=True, text=True,
    )
    assert proc.returncode == 1
