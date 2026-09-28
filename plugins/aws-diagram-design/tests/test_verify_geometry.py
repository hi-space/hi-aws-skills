"""verify-geometry.py must read standalone SVG and cover it in --all."""
from conftest import GOOD_SVG, load_script

vg = load_script("verify-geometry")


def test_clipped_mask_in_svg_is_reported(tmp_path):
    # a 40x10 label mask painted before a 100x60 node that overlaps it
    svg = GOOD_SVG.replace(
        '<rect x="40" y="72" width="80" height="56"',
        '<rect x="105" y="90" width="40" height="10" fill="#fff"/>\n  <rect x="40" y="72" width="100" height="60"',
    )
    p = tmp_path / "clip.svg"
    p.write_text(svg, encoding="utf-8")
    findings = vg.check(p)
    assert len(findings) == 1 and "clipped by node" in findings[0]


def test_all_targets_include_svg(monkeypatch, tmp_path):
    (tmp_path / "a.svg").write_text(GOOD_SVG, encoding="utf-8")
    (tmp_path / "b.html").write_text("<svg></svg>", encoding="utf-8")
    monkeypatch.setattr(vg, "ASSET_DIR", tmp_path)
    names = sorted(p.name for p in vg.targets(vg.argparse.Namespace(all=True, files=[])))
    assert names == ["a.svg", "b.html"]
