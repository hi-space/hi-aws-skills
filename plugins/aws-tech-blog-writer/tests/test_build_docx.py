"""build_docx.js turns the final Markdown into the Word deliverable without losing what the author must see.

The RED run that motivated the script: `pandoc draft.md -o draft.docx` produced 0 shaded runs, so the
four placeholder colours were gone. These tests build the fixture draft and read word/document.xml back.
"""
import re
import shutil
import struct
import subprocess
import zipfile
import zlib
from pathlib import Path

import pytest

PLUGIN = Path(__file__).resolve().parents[1]
SKILL = PLUGIN / "skills" / "aws-tech-blog-writer"
BUILD = SKILL / "scripts" / "build_docx.js"
LINT = SKILL / "scripts" / "lint_blog.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures"

COLOURS = {"작성자 확인": "FFF2CC", "기술 검증 필요": "F8CECC", "이미지 필요": "DAE8FC", "인용 승인 필요": "D5E8D4"}

needs_tools = pytest.mark.skipif(
    not (shutil.which("node") and shutil.which("pandoc") and shutil.which("unzip")),
    reason="node, pandoc and unzip are required to build the .docx",
)


def png(width: int, height: int) -> bytes:
    """Minimal valid RGB PNG so the fixture's image exists without PIL."""
    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    raw = b"".join(b"\x00" + b"\xc8\xdc\xf0" * width for _ in range(height))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


@pytest.fixture
def work(tmp_path):
    shutil.copy(FIXTURES / "06-final.md", tmp_path / "06-final.md")
    shutil.copy(FIXTURES / "placeholders.md", tmp_path / "placeholders.md")
    (tmp_path / "images").mkdir()
    (tmp_path / "images" / "fig1-arch.drawio.png").write_bytes(png(1600, 800))  # wider than the text column
    return tmp_path


def build(work, *extra):
    return subprocess.run(["node", str(BUILD), str(work), *extra], capture_output=True, text=True)


def document_xml(docx: Path) -> str:
    with zipfile.ZipFile(docx) as z:
        return z.read("word/document.xml").decode("utf-8")


def test_fixture_is_a_valid_final_draft():
    r = subprocess.run(["python3", str(LINT), str(FIXTURES / "06-final.md"), "--final", "--quiet-info", "--no-service-check"],
                       capture_output=True, text=True)
    # the fixture's image lives in the tmp work dir, so only the missing-file error is tolerated here
    errors = [l for l in r.stdout.splitlines() if l.startswith("ERROR") and "image file not found" not in l]
    assert errors == [], r.stdout


@needs_tools
def test_build_writes_docx_and_verifies(work):
    r = build(work)
    assert r.returncode == 0, r.stdout + r.stderr
    assert (work / "06-final.docx").exists()
    assert "verification: ok" in r.stdout
    assert "images: markdown 1, embedded 1" in r.stdout


@needs_tools
def test_every_placeholder_colour_survives(work):
    build(work)
    xml = document_xml(work / "06-final.docx")
    for tag, fill in COLOURS.items():
        assert f'w:fill="{fill}"' in xml, f"{tag} lost its shading"
        # the tag is one run, not split into "[작성자" and "확인]" as pandoc tokenises it
        assert f"[{tag}]" in xml, f"{tag} text split across runs"
    # the request text is shaded too, not only the tag: the run holding the request carries the fill
    request_run = next(r for r in re.findall(r"<w:r>.*?</w:r>", xml, re.S) if "Lambda 타겟" in r)
    assert 'w:fill="F8CECC"' in request_run and 'w:color w:val="9F0000"' in request_run


@needs_tools
def test_structure_and_hygiene(work):
    build(work)
    xml = document_xml(work / "06-final.docx")
    assert xml.count("<pic:pic") == 1
    # image scaled to the 6.5in text column (EMU), not its 1600px natural width
    cx = int(re.search(r'<wp:extent cx="(\d+)"', xml).group(1))
    assert cx == 5943600
    assert 'w:val="Title"' in xml and 'w:val="Heading1"' in xml
    assert "<w:tbl>" in xml
    assert 'xml:space="preserve">    return' in xml  # code indentation kept
    assert "F01" not in xml  # fact-ID HTML comments never reach the author
    assert 'w:type="page"' in xml and "남은 placeholder" in xml  # appendix from placeholders.md


@needs_tools
def test_no_appendix_flag_and_missing_image_fails(work):
    r = build(work, "--no-appendix")
    assert r.returncode == 0 and "appendix: no" in r.stdout
    assert "남은 placeholder" not in document_xml(work / "06-final.docx")

    (work / "images" / "fig1-arch.drawio.png").unlink()
    r = build(work)
    assert r.returncode == 1
    assert "MISSING" in r.stdout and "verification: FAILED" in r.stdout
