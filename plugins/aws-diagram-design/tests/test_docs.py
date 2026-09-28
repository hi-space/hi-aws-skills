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
