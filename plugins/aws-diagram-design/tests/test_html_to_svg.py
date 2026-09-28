"""html_to_svg.py lifts the diagram out of a 1.x HTML page without losing page CSS or nested icons."""
import subprocess
import sys

from conftest import SCRIPTS, load_script

h2s = load_script("html_to_svg")
sc = load_script("self_check")

PAGE = """<!DOCTYPE html><html><head><style>
  body { background: #fff; }
  .frame { max-width: 1200px; }
  h1 { font-size: 2rem; }
  :root { --ink: #232F3E; }
  .node-title { font-family: 'Amazon Ember'; font-weight: 600; }
  text.sub, .chip-text { font-size: 9px; }
  @media (max-width: 600px) { .node-title { font-size: 10px; } .frame { padding: 0; } }
  @font-face { font-family: 'Amazon Ember'; src: url('../fonts/x.woff2'); }
</style></head><body><div class="frame"><p class="eyebrow">ARCH</p><h1>Title</h1>
<svg viewBox="0 0 400 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="x-title x-desc">
  <title id="x-title">X</title>
  <desc id="x-desc">Y.</desc>
  <rect width="100%" height="100%" fill="#ffffff"/>
  <rect x="40" y="72" width="80" height="56" fill="var(--ink)"/>
  <text x="80" y="104" class="node-title">Client</text>
  <text x="80" y="120" class="sub">sub</text>
  <foreignObject x="32" y="186" width="140" height="24"><div xmlns="http://www.w3.org/1999/xhtml" class="field-value" style="line-height:1.25">NiFi ingest</div></foreignObject>
  <svg x="10" y="10" width="16" height="16" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="6"/></svg>
  <text x="200" y="104" class="chip-text">chip</text>
</svg>
<div class="card">Summary</div></div></body></html>"""


def test_extract_keeps_nested_svg_icons():
    svg = h2s.extract_svg(PAGE)
    assert svg.count("<svg") == 2 and svg.rstrip().endswith("</svg>") and "chip" in svg


def test_relevant_css_keeps_only_rules_the_svg_uses():
    css = h2s.relevant_css(PAGE.split("<style>")[1].split("</style>")[0], h2s.extract_svg(PAGE))
    assert ".node-title" in css and "text.sub" in css and ":root" in css
    assert "body" not in css and ".frame" not in css and "h1" not in css and "@font-face" not in css
    assert "@media" not in css and "font-size: 10px" in css  # media rules flattened, page ones dropped


def test_foreign_object_becomes_text():
    out = h2s.replace_foreign_objects(h2s.extract_svg(PAGE))
    assert "<foreignObject" not in out
    assert '<text x="32" y="202" class="field-value">NiFi ingest</text>' in out


def test_convert_produces_checkable_svg(tmp_path):
    out = tmp_path / "x.svg"
    out.write_text(h2s.convert(PAGE), encoding="utf-8")
    text = out.read_text(encoding="utf-8")
    assert text.startswith('<?xml version="1.0" encoding="UTF-8"?>\n<svg')
    assert "local('Amazon Ember')" in text and "url(" not in text.split("</style>")[0].replace("url(#", "")
    assert sc.verify(out) == []


def test_convert_keeps_nested_svg_icons(tmp_path):
    out = tmp_path / "x.svg"
    out.write_text(h2s.convert(PAGE), encoding="utf-8")
    assert out.read_text(encoding="utf-8").count("<svg") == 2


def test_cli_writes_next_to_source_and_deletes(tmp_path):
    src = tmp_path / "page.html"
    src.write_text(PAGE, encoding="utf-8")
    r = subprocess.run([sys.executable, str(SCRIPTS / "html_to_svg.py"), str(src), "--delete-source"], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert (tmp_path / "page.svg").exists() and not src.exists()


def test_no_svg_is_an_error(tmp_path):
    src = tmp_path / "nope.html"
    src.write_text("<html><body>hi</body></html>", encoding="utf-8")
    r = subprocess.run([sys.executable, str(SCRIPTS / "html_to_svg.py"), str(src)], capture_output=True, text=True)
    assert r.returncode == 1 and "no <svg>" in r.stderr


def test_convert_adds_xmlns_when_missing(tmp_path):
    page = PAGE.replace(' xmlns="http://www.w3.org/2000/svg"', "", 1)
    out = tmp_path / "x.svg"
    out.write_text(h2s.convert(page), encoding="utf-8")
    text = out.read_text(encoding="utf-8")
    assert text.count('xmlns="http://www.w3.org/2000/svg"') == 1
    assert sc.verify(out) == []


def test_extract_skips_svg_inside_html_comment():
    page = PAGE.replace("<svg viewBox", "<!-- <svg viewBox=\"0 0 1 1\"><title>stale</title></svg> -->\n<svg viewBox", 1)
    svg = h2s.extract_svg(page)
    assert svg.startswith('<svg viewBox="0 0 400 200"') and "stale" not in svg


def test_relevant_css_drops_root_svg_layout_rule():
    css = "svg { width: 100%; min-width: 900px; display: block; }\nsvg text { fill: red; }\n.node-title { font-weight: 600; }"
    kept = h2s.relevant_css(css, h2s.extract_svg(PAGE))
    assert "min-width" not in kept and "svg text" in kept and ".node-title" in kept


def test_root_vars_kept_when_var_used_only_in_kept_css():
    css = ":root { --ink: #232F3E; --sans: 'Amazon Ember'; }\n.node-title { fill: var(--ink); font: 600 13px var(--sans); }\nbody { color: var(--ink); }"
    svg = h2s.extract_svg(PAGE).replace('fill="var(--ink)"', 'fill="#000"')  # markup itself has no var(
    kept = h2s.relevant_css(css, svg)
    assert kept.startswith(":root") and "--ink" in kept and ".node-title" in kept and "body" not in kept


def test_root_vars_dropped_when_nothing_uses_them():
    css = ":root { --ink: #232F3E; }\n.node-title { fill: #000; }"
    svg = h2s.extract_svg(PAGE).replace('fill="var(--ink)"', 'fill="#000"')
    assert ":root" not in h2s.relevant_css(css, svg)
