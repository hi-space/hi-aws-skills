"""self_check.py must verify standalone SVG files with the same contract as inline diagrams."""
from conftest import GOOD_SVG, load_script

sc = load_script("self_check")


def write(tmp_path, text, name="d.svg"):
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return p


def test_good_svg_passes(good_svg):
    assert sc.verify(good_svg) == []


def test_bare_title_id_fails(tmp_path):
    bad = GOOD_SVG.replace('id="demo-title"', 'id="title"').replace("demo-title demo-desc", "title demo-desc")
    errors = sc.verify(write(tmp_path, bad))
    assert any("prefixed" in e for e in errors)


def test_script_element_fails(tmp_path):
    bad = GOOD_SVG.replace("</svg>", "<script>alert(1)</script></svg>")
    assert any("script" in e for e in sc.verify(write(tmp_path, bad)))


def test_foreign_object_fails(tmp_path):
    bad = GOOD_SVG.replace("</svg>", '<foreignObject x="0" y="0" width="10" height="10"/></svg>')
    assert any("foreignObject" in e for e in sc.verify(write(tmp_path, bad)))


def test_external_url_fails(tmp_path):
    bad = GOOD_SVG.replace("<defs>", "<defs><style>@font-face{font-family:'X';src:url('../fonts/x.woff2')}</style>")
    assert any("external" in e for e in sc.verify(write(tmp_path, bad)))


def test_data_font_url_is_allowed(tmp_path):
    ok = GOOD_SVG.replace("<defs>", "<defs><style>@font-face{font-family:'X';src:url(data:font/woff2;base64,AAAA)}</style>")
    assert sc.verify(write(tmp_path, ok)) == []


def test_missing_xmlns_fails(tmp_path):
    bad = GOOD_SVG.replace(' xmlns="http://www.w3.org/2000/svg"', "")
    assert any("xmlns" in e for e in sc.verify(write(tmp_path, bad)))


def test_malformed_xml_reports_position(tmp_path):
    bad = GOOD_SVG.replace(">Client<", ">R&D<")
    errors = sc.verify(write(tmp_path, bad))
    assert len(errors) == 1 and "line" in errors[0]


def test_title_not_first_child_fails(tmp_path):
    bad = GOOD_SVG.replace('  <title id="demo-title">Demo</title>\n', "").replace("</defs>", '</defs>\n  <title id="demo-title">Demo</title>')
    assert any("first child" in e for e in sc.verify(write(tmp_path, bad)))


def test_nested_aria_hidden_svg_is_ignored(tmp_path):
    ok = GOOD_SVG.replace("</svg>", '<svg x="10" y="10" width="16" height="16" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="6"/></svg></svg>')
    assert sc.verify(write(tmp_path, ok)) == []


def test_on_attribute_fails(tmp_path):
    bad = GOOD_SVG.replace('<rect x="40"', '<rect onclick="x()" x="40"')
    assert any("executable" in e for e in sc.verify(write(tmp_path, bad)))


def test_doctype_is_rejected_before_parsing(tmp_path):
    # XXE / billion-laughs guard: a deliverable SVG never needs a DOCTYPE
    bad = GOOD_SVG.replace("<svg ", '<!DOCTYPE svg [<!ENTITY x "y">]>\n<svg ', 1)
    errors = sc.verify(write(tmp_path, bad))
    assert len(errors) == 1 and "DOCTYPE" in errors[0]


def test_html_path_still_works(skill_dir):
    # motion template is HTML and must keep passing through the old parser
    assert sc.verify(skill_dir / "assets" / "template-motion.html") == []
