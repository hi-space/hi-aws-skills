import json
import subprocess
from pathlib import Path

import pytest

PLUGIN = Path(__file__).resolve().parents[1]
HARNESS = PLUGIN / "skills" / "aws-drawio-diagram" / "scripts" / "extract_stencils.js"
SIDEBAR = PLUGIN / "scripts" / "fixtures" / "Sidebar-AWS4.js"


def run(source: Path):
    return subprocess.run(["node", str(HARNESS), str(source)], capture_output=True, text=True)


@pytest.fixture(scope="module")
def data():
    proc = run(SIDEBAR)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def test_captures_all_palettes_including_retired(data):
    ids = [s["id"] for s in data["sections"]]
    assert len(ids) == 31
    assert ids[0] == "aws4Arrows" and ids[-1] == "aws4r"
    assert "aws4Compute" in ids and "aws4Groups" in ids


def test_entries_have_resolved_styles(data):
    compute = next(s for s in data["sections"] if s["id"] == "aws4Compute")
    first = compute["entries"][0]
    assert first["label"] == "Compute"
    assert "shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.compute;" in first["style"]
    assert "fillColor=#ED7100" in first["style"]
    assert first["width"] == 78


def test_arrows_are_dropped_and_retired_functions_resolve(data):
    arrows = next(s for s in data["sections"] if s["id"] == "aws4Arrows")
    assert arrows["entries"] == []
    retired = next(s for s in data["sections"] if s["id"] == "aws4r")
    styles = " ".join(e["style"] for e in retired["entries"])
    assert "resIcon=mxgraph.aws4.quicksight;" in styles
    assert "fillColor=#8C4FFF" in styles


def test_fails_loudly_on_unrelated_source(tmp_path):
    bogus = tmp_path / "x.js"
    bogus.write_text("Sidebar.prototype.addAWS4Palette = function() {};")
    proc = run(bogus)
    assert proc.returncode == 1
    assert "no palettes" in proc.stderr
