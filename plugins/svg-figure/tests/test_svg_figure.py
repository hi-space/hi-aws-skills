import importlib.util
import json
import re
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1]
SKILL = PLUGIN / "skills" / "svg-figure"
SKILL_MD = SKILL / "SKILL.md"

spec = importlib.util.spec_from_file_location("svg_figure", SKILL / "scripts" / "svg_figure.py")
sf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sf)

LIGHT, DARK = sf.load_tokens(sf.DEFAULT_TOKENS)
EXAMPLE = (SKILL / "assets" / "example.src.svg").read_text(encoding="utf-8")


def fig(body: str, head: str = 'viewBox="0 0 560 200" role="img" aria-labelledby="f-title f-desc"') -> str:
    return (f'<svg {head}><title id="f-title">제목</title><desc id="f-desc">설명</desc>{body}</svg>')


def errors(src: str, **kw) -> str:
    return "\n".join(sf.check_svg(src, LIGHT, **kw).errors)


def warnings(src: str) -> str:
    return "\n".join(sf.check_svg(src, LIGHT).warnings)


# ── the shipped example is the contract in one file ──

def test_example_passes_clean_with_its_prefix():
    rep = sf.check_svg(EXAMPLE, LIGHT, prefix="ex-")
    assert rep.errors == [] and rep.warnings == []


def test_tokens_have_a_light_and_dark_value_for_every_name():
    assert set(LIGHT) == set(DARK)
    assert LIGHT["--ink"] != DARK["--ink"]
    for name in ("--ok", "--ok-bg", "--new", "--new-bg", "--risk", "--risk-bg", "--key", "--band", "--panel"):
        assert name in LIGHT


# ── contract errors ──

def test_literal_colours_and_unknown_tokens_are_errors():
    assert "never a literal" in errors(fig('<rect width="10" height="10" fill="#fff"/>'))
    assert "never a literal" in errors(fig('<rect width="10" height="10" stroke="red"/>'))
    assert "unknown token" in errors(fig('<rect width="10" height="10" fill="var(--brand)"/>'))
    assert errors(fig('<rect width="10" height="10" fill="none" stroke="var(--line)"/>')) == ""


def test_key_token_is_a_fill_only():
    assert "--key" in errors(fig('<text x="10" y="40" font-size="17" fill="var(--key)">가</text>'))
    assert "--key" in errors(fig('<line x1="0" y1="0" x2="9" y2="9" stroke="var(--key)"/>'))
    assert errors(fig('<rect width="10" height="10" fill="var(--key)"/>')) == ""


def test_font_floor_follows_the_canvas_width():
    small = '<text x="10" y="40" font-size="15" fill="var(--ink)">가나다</text>'
    assert "needs 17px" in errors(fig(small))
    wide = 'viewBox="0 0 1120 200" role="img" aria-labelledby="f-title f-desc"'
    assert errors(fig(small, wide)) == ""
    tall = 'viewBox="0 0 400 200" role="img" aria-labelledby="f-title f-desc"'
    assert errors(fig(small.replace('"15"', '"14"'), tall)) == ""
    assert "no font-size" in errors(fig('<text x="10" y="40" fill="var(--ink)">가</text>'))


def test_root_must_be_accessible_and_unsized():
    assert 'role="img"' in errors('<svg viewBox="0 0 560 100"><title id="a">t</title><desc id="b">d</desc></svg>')
    assert "viewBox" in errors('<svg role="img"><title id="a">t</title><desc id="b">d</desc></svg>')
    assert "fixes the size" in errors(fig("", 'viewBox="0 0 560 100" width="560" role="img" aria-labelledby="f-title f-desc"'))
    no_ids = '<svg viewBox="0 0 560 100" role="img"><title>t</title><desc>d</desc></svg>'
    assert "aria-labelledby" in errors(no_ids)
    assert "first child must be <title>" in errors('<svg viewBox="0 0 560 100" role="img"><rect/></svg>')


def test_forbidden_elements_attributes_and_urls():
    assert "<style>" in errors(fig("<style>text{fill:red}</style>"))
    assert "<image> is not allowed" in errors(fig('<image x="0" y="0"/>'))
    assert "font-family" in errors(fig('<text x="1" y="40" font-size="17" font-family="Arial" fill="var(--ink)">a</text>'))
    assert "not allowed" in errors(fig('<rect width="5" height="5" style="fill:red"/>'))
    assert "only url(#id)" in errors(fig('<rect width="5" height="5" fill="url(https://x.test/a)"/>'))
    assert "only url(#id)" in errors(fig('<line x1="0" y1="0" x2="5" y2="5" marker-end="url(#nope)"/>'))
    assert "DOCTYPE" in errors('<!DOCTYPE svg [<!ENTITY a "b">]>' + fig(""))


def test_id_prefix_and_duplicate_ids_across_figures():
    assert 'does not start with the figure prefix "t1-"' in errors(fig(""), prefix="t1-")
    seen: set = set()
    assert sf.check_svg(fig(""), LIGHT, seen_ids=seen).errors == []
    assert "already used by another figure" in "\n".join(sf.check_svg(fig(""), LIGHT, seen_ids=seen).errors)


# ── geometry warnings ──

def test_label_wider_than_its_box_warns_and_two_lines_fix_it():
    box = '<rect x="20" y="20" width="120" height="60" fill="var(--panel)" stroke="var(--line)"/>'
    long = box + '<text x="80" y="56" font-size="17" text-anchor="middle" fill="var(--ink)">아주 긴 한글 라벨입니다</text>'
    assert "overflows its 120-wide box" in warnings(fig(long))
    two = box + ('<text x="80" y="46" font-size="17" text-anchor="middle" fill="var(--ink)">'
                 '<tspan x="80">긴 한글</tspan><tspan x="80" dy="22">라벨</tspan></text>')
    assert warnings(fig(two)) == ""


def test_text_outside_canvas_and_overlapping_text_warn():
    out = '<text x="500" y="40" font-size="17" fill="var(--ink)">캔버스 밖으로 나가는 글자</text>'
    assert "outside the canvas" in warnings(fig(out))
    over = ('<text x="20" y="40" font-size="17" fill="var(--ink)">첫째 라벨</text>'
            '<text x="40" y="46" font-size="17" fill="var(--ink)">둘째 라벨</text>')
    assert "overlaps" in warnings(fig(over))


def test_number_badge_on_a_box_corner_is_not_an_overflow():
    body = ('<rect x="100" y="50" width="200" height="60" fill="var(--panel)" stroke="var(--line)"/>'
            '<circle cx="100" cy="50" r="14" fill="var(--ink)"/>'
            '<text x="100" y="56" font-size="17" text-anchor="middle" fill="var(--panel)">1</text>')
    assert warnings(fig(body)) == ""


def test_translated_groups_are_measured_in_place():
    body = ('<g transform="translate(300,0)"><rect x="0" y="20" width="200" height="60" fill="var(--panel)"/>'
            '<text x="100" y="56" font-size="17" text-anchor="middle" fill="var(--ink)">가나다</text></g>')
    assert warnings(fig(body)) == ""


# ── export and preview ──

def test_export_resolves_every_token_and_stays_parseable():
    out = sf.export_svg(EXAMPLE, LIGHT, DARK)
    assert "var(" not in out and LIGHT["--ink"] in out
    assert 'xmlns="http://www.w3.org/2000/svg"' in out and "font-family=" in out
    dark = sf.export_svg(EXAMPLE, LIGHT, DARK, flat="dark", bg="paper")
    assert DARK["--paper"] in dark and LIGHT["--ink"] not in dark
    assert dark.index("</desc>") < dark.index(DARK["--paper"]), "background goes after <title>/<desc>"
    sf.ET.fromstring(out)
    sf.ET.fromstring(dark)


def test_adaptive_export_keeps_tokens_and_embeds_both_themes():
    out = sf.export_svg(EXAMPLE, LIGHT, DARK, flat=None)
    assert "var(--ink)" in out and "prefers-color-scheme:dark" in out
    assert LIGHT["--ink"] in out and DARK["--ink"] in out


def test_preview_shows_light_dark_and_phone_without_duplicate_ids():
    page = sf.build_preview([("example", EXAMPLE)], LIGHT, DARK)
    assert page.count("<svg") == 3
    ids = re.findall(r'\bid="([^"]+)"', page)
    assert len(ids) == len(set(ids))
    assert 'url(#d-ex-arr)' in page and 'aria-labelledby="p-ex-title p-ex-desc"' in page


def test_cli_check_exit_codes(tmp_path, capsys):
    good = tmp_path / "good.src.svg"
    good.write_text(EXAMPLE, encoding="utf-8")
    bad = tmp_path / "bad.src.svg"
    bad.write_text(fig('<rect width="5" height="5" fill="#000"/>'), encoding="utf-8")
    assert sf.main(["check", str(good), "--prefix", "ex-"]) == 0
    assert sf.main(["check", str(bad)]) == 1
    page = tmp_path / "page.html"
    page.write_text(f"<html><body>{EXAMPLE}{EXAMPLE}</body></html>", encoding="utf-8")
    assert sf.main(["check", str(page)]) == 1
    assert "already used by another figure" in capsys.readouterr().out


# ── skill document ──

def frontmatter() -> str:
    fm = re.match(r"^---\n(.*?)\n---\n", SKILL_MD.read_text(encoding="utf-8"), re.S)
    assert fm, "missing frontmatter"
    return fm.group(1)


def test_frontmatter_names_the_skill_and_fits_the_spec_limit():
    fm = frontmatter()
    assert "name: svg-figure" in fm
    assert len(fm) <= 1024, f"frontmatter is {len(fm)} chars; the Agent Skills spec caps it at 1024"
    assert re.search(r"description: Use when", fm)
    assert "그림 그려줘" in fm, "Korean triggers, like the other hi-aws-skills plugins"
    assert "aws-diagram-design" in fm, "the description must send icon diagrams to the other skill"


def test_manifests_agree_and_marketplace_lists_the_plugin():
    a = json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_text())
    b = json.loads((PLUGIN / "plugin.json").read_text())
    assert a["name"] == b["name"] == "svg-figure" and a["version"] == b["version"]
    market = json.loads((PLUGIN.parents[1] / ".claude-plugin" / "marketplace.json").read_text())
    assert any(p["name"] == "svg-figure" and p["source"] == "./plugins/svg-figure" for p in market["plugins"])


def test_every_linked_file_exists_and_scripts_run_through_python():
    text = SKILL_MD.read_text(encoding="utf-8")
    links = set(re.findall(r"\]\(((?:references|assets|scripts)/[^)#]+)\)", text))
    assert {"references/technical-illustration.md", "assets/example.src.svg", "assets/figure-tokens.css"} <= links
    assert [l for l in links if not (SKILL / l).exists()] == []
    assert not re.search(r"(?<!python3 )scripts/svg_figure\.py (check|preview|export)", text)


def test_skill_states_the_numbers_the_checker_enforces():
    text = SKILL_MD.read_text(encoding="utf-8")
    for width, floor in ((560, 17), (1120, 15), (400, 14)):
        assert sf.min_font_for(width) == floor
        assert re.search(rf"`0 0 {width} H` \| {floor} \|", text), f"SKILL.md table lost {width} → {floor}"
    for tag in sf.ALLOWED_TAGS:
        assert tag in text
    for token in LIGHT:
        assert token in text, f"{token} is in the tokens file but not explained in SKILL.md"


def test_line_through_a_label_warns_and_a_line_beside_it_does_not():
    label = '<text x="100" y="60" font-size="17" fill="var(--ink)">직접 쓰기</text>'
    through = label + '<line x1="80" y1="55" x2="220" y2="55" stroke="var(--muted)"/>'
    assert "a line runs through text" in warnings(fig(through))
    beside = label + '<line x1="80" y1="72" x2="220" y2="72" stroke="var(--muted)"/>'
    assert warnings(fig(beside)) == ""


def test_label_in_a_filled_pill_on_top_of_a_line_is_fine():
    body = ('<line x1="100" y1="10" x2="100" y2="190" stroke="var(--line)" stroke-width="4"/>'
            '<rect x="40" y="80" width="120" height="40" rx="20" fill="var(--panel)" stroke="var(--line)"/>'
            '<text x="100" y="106" font-size="17" text-anchor="middle" fill="var(--ink)">RJ45 이더넷</text>')
    assert warnings(fig(body)) == ""
