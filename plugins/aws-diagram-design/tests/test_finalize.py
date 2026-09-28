"""finalize.py embeds only the Amazon Ember faces a diagram uses, idempotently."""
import base64
import re
import subprocess
import sys

import pytest

from conftest import GOOD_SVG, SCRIPTS, load_script

fz = load_script("finalize")


def faces(svg):
    return {(f.family, f.weight, f.style) for f in fz.used_faces(svg)}


def test_used_faces_minimal_sans_and_mono():
    # GOOD_SVG: sans 600 + mono default → Ember 400, Ember 600, Mono 400
    assert faces(GOOD_SVG) == {("Amazon Ember", 400, "normal"), ("Amazon Ember", 600, "normal"), ("Amazon Ember Mono", 400, "normal")}


def test_used_faces_css_shorthand_and_italic():
    svg = GOOD_SVG.replace("<defs>", "<defs><style>.t{font:italic 700 14px 'Amazon Ember'}</style>")
    got = faces(svg)
    assert ("Amazon Ember", 700, "normal") in got and ("Amazon Ember", 400, "italic") in got


def test_weight_snapping():
    svg = GOOD_SVG.replace('font-weight="600"', 'font-weight="500"').replace("font-size=\"9\"", 'font-size="9" font-weight="bold"')
    got = faces(svg)
    assert ("Amazon Ember", 400, "normal") in got and ("Amazon Ember", 600, "normal") not in got
    assert ("Amazon Ember Mono", 700, "normal") in got


def test_embed_writes_data_uri_for_each_used_face():
    out = fz.embed_fonts(GOOD_SVG)
    assert out.count("url(data:font/woff2;base64,") == 3
    assert "/* finalize:fonts */" in out and "/* /finalize:fonts */" in out
    payload = re.search(r"base64,([A-Za-z0-9+/=]+)", out).group(1)
    assert base64.b64decode(payload)[:4] == b"wOF2"


def test_embed_is_idempotent():
    once = fz.embed_fonts(GOOD_SVG)
    assert fz.embed_fonts(once) == once


def test_embed_replaces_local_only_font_face():
    svg = fz.inject_style(GOOD_SVG, fz.LOCAL_FONT_FACE_CSS, "fonts")
    out = fz.embed_fonts(svg)
    assert out.count("font-family: 'Amazon Ember';") + out.count("font-family:'Amazon Ember';") == 2  # 400 + 600, nothing else
    assert "url(data:" in out and "/* fonts */" not in out


def test_embed_without_defs_creates_one_after_desc():
    svg = re.sub(r"\s*<defs>.*?</defs>", "", GOOD_SVG, flags=re.S).replace('marker-end="url(#arrow)"', "")
    out = fz.embed_fonts(svg)
    assert re.search(r"</desc>\s*<defs>\s*<style>", out)


def test_embedded_svg_stays_well_formed(tmp_path):
    p = tmp_path / "d.svg"
    p.write_text(fz.embed_fonts(GOOD_SVG), encoding="utf-8")
    sc = load_script("self_check")
    assert sc.verify(p) == []


def test_embed_resolves_fonts_from_skill_dir(tmp_path, good_svg):
    # run from an unrelated cwd: font files must still be found next to the script
    r = subprocess.run([sys.executable, str(SCRIPTS / "finalize.py"), str(good_svg), "--no-png"], cwd=tmp_path, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert "base64," in good_svg.read_text(encoding="utf-8")


def run(*args, cwd=None):
    return subprocess.run([sys.executable, str(SCRIPTS / "finalize.py"), *map(str, args)], cwd=cwd, capture_output=True, text=True)


def test_check_only_passes_and_does_not_write(good_svg):
    before = good_svg.read_text(encoding="utf-8")
    r = run(good_svg, "--check-only")
    assert r.returncode == 0 and "OK" in r.stdout
    assert good_svg.read_text(encoding="utf-8") == before


def test_check_failure_leaves_file_untouched(tmp_path):
    p = tmp_path / "bad.svg"
    bad = GOOD_SVG.replace("</svg>", "<script>1</script></svg>")
    p.write_text(bad, encoding="utf-8")
    r = run(p, "--no-png")
    assert r.returncode == 1 and "script" in r.stdout + r.stderr
    assert p.read_text(encoding="utf-8") == bad


def test_check_reports_unescaped_ampersand(tmp_path):
    p = tmp_path / "amp.svg"
    p.write_text(GOOD_SVG.replace(">Client<", ">R&D<"), encoding="utf-8")
    r = run(p, "--check-only")
    assert r.returncode == 1 and "&amp;" in r.stdout + r.stderr


def test_geometry_finding_fails_check(tmp_path):
    p = tmp_path / "clip.svg"
    p.write_text(GOOD_SVG.replace('<rect x="40" y="72" width="80" height="56"', '<rect x="105" y="90" width="40" height="10" fill="#fff"/>\n  <rect x="40" y="72" width="100" height="60"'), encoding="utf-8")
    r = run(p, "--check-only")
    assert r.returncode == 1 and "clipped" in r.stdout + r.stderr


def test_html_shell_adds_noto_only_for_hangul():
    plain = fz.html_shell(GOOD_SVG, 400, 200)
    korean = fz.html_shell(GOOD_SVG.replace(">Client<", ">클라이언트<"), 400, 200)
    assert "fonts.googleapis.com" not in plain
    assert "Noto+Sans+KR" in korean
    assert "width:400px;height:200px" in plain.replace(" ", "")


def test_png_size_default_scale(good_svg):
    pytest.importorskip("playwright")
    r = run(good_svg)
    assert r.returncode == 0, r.stderr
    png = good_svg.with_suffix(".png")
    assert png.exists() and fz.png_size(png) == (800, 400)


def test_png_size_fractional_scale(good_svg, tmp_path):
    pytest.importorskip("playwright")
    out_dir = tmp_path / "png"
    r = run(good_svg, "--scale", "1.25", "--png-dir", out_dir)
    assert r.returncode == 0, r.stderr
    assert fz.png_size(out_dir / "demo.png") == (500, 250)


def test_scale_out_of_range_rejected(good_svg):
    r = run(good_svg, "--scale", "6")
    assert r.returncode == 2 and "1" in r.stderr and "4" in r.stderr


def test_missing_playwright_keeps_svg(good_svg, monkeypatch):
    # simulate absence by forcing the import to fail inside render_png
    import builtins
    real_import = builtins.__import__

    def fake(name, *a, **k):
        if name.startswith("playwright"):
            raise ImportError(name)
        return real_import(name, *a, **k)

    monkeypatch.setattr(builtins, "__import__", fake)
    assert fz.render_png(GOOD_SVG, good_svg.with_suffix(".png"), 2.0) is False
    assert not good_svg.with_suffix(".png").exists()
