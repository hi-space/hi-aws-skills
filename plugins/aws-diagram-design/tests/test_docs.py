"""Docs and commands describe the SVG-first contract, never an HTML deliverable."""
import re
from pathlib import Path

from conftest import PLUGIN, SKILL

REFS = SKILL / "references"
CMDS = PLUGIN / "commands"


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def test_import_commands_default_to_svg_png():
    for name in ("import-drawio.md", "import-mermaid.md"):
        text = read(CMDS / name)
        assert "--format=svg+png|svg|png" in text, name
        assert "--variant=light|dark|terminal" in text, name
        assert "html+png" not in text and "full" not in text.split("---", 2)[1], name


def test_export_command_takes_svg_or_html():
    text = read(CMDS / "export-diagram.md")
    assert "<svg-or-html-file>" in text and "finalize.py" in text


def test_output_spec_format_dial():
    text = read(REFS / "output-spec.md")
    assert "`svg+png`" in text and "Always generate the HTML first" not in text


def test_export_reference_is_motion_and_legacy_only():
    text = read(REFS / "export.md")
    assert "finalize.py" in text and "html_to_svg.py" in text
    assert "Never hand-author an SVG" not in text


def test_no_reference_lists_html_examples():
    for p in sorted(REFS.glob("type-*.md")):
        text = read(p)
        assert not re.search(r"example-[\w-]+\.html", text), p.name
        assert "-full" not in text, p.name


def test_skill_md_describes_svg_first():
    text = read(SKILL / "SKILL.md")
    assert 'version: "2.0.0"' in text
    assert "finalize.py" in text
    assert "template.svg" in text and "template-full" not in text
    assert "Always produce a single self-contained `.html` file" not in text
    assert "Full editorial" not in text
    assert "html+png" not in text and "`html`" not in text.split("## 11.")[1].split("## 12.")[0]


def test_python_generator_doc_uses_build_png():
    text = read(REFS / "python-generator.md")
    assert "--png" in text and "export.py" not in text and "html()" not in text


import json


def test_manifests_at_2_1_1():
    for p in (PLUGIN / "plugin.json", PLUGIN / ".claude-plugin" / "plugin.json"):
        data = json.loads(read(p))
        assert data["version"] == "2.1.1", p
        assert "HTML" not in data["description"], p


def test_samples_are_svg_png_pairs():
    samples = PLUGIN / "docs" / "samples"
    assert not list(samples.glob("*.html"))
    svgs = sorted(p.stem for p in samples.glob("*.svg"))
    assert svgs == sorted(p.stem for p in samples.glob("*.png")) and len(svgs) == 5
    for p in samples.glob("*.svg"):
        assert "base64," in read(p), p.name  # README samples are deliverables: fonts embedded


def test_readmes_do_not_point_at_html():
    for name in ("README.md", "README.en.md"):
        text = read(PLUGIN / name)
        assert "samples/" in text and not re.search(r"samples/[\w-]+\.html", text), name
        assert "export-diagram my-diagram.svg" in text, name


def test_every_example_named_in_references_exists():
    assets = SKILL / "assets"
    docs = list(REFS.glob("*.md")) + [SKILL / "SKILL.md"]
    for p in docs:
        text = read(p)
        for name in re.findall(r"example-[\w-]+\.svg", text):
            assert (assets / name).exists(), f"{p.name} names {name}, which does not exist under assets/"
