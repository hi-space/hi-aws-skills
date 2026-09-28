"""finalize.py embeds only the Amazon Ember faces a diagram uses, idempotently."""
import base64
import re
import subprocess
import sys

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
