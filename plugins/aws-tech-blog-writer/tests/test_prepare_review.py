"""prepare_review.py must give the review the same structure the builder put into the Word file."""
import re
import shutil
import subprocess
from pathlib import Path

import pytest

PLUGIN = Path(__file__).resolve().parents[1]
BUILD = PLUGIN / "skills" / "aws-tech-blog-writer" / "scripts" / "build_docx.js"
PREPARE = PLUGIN / "skills" / "aws-blog-review" / "scripts" / "prepare_review.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "06-final.md"

needs_tools = pytest.mark.skipif(not (shutil.which("node") and shutil.which("pandoc")), reason="node and pandoc required")


@needs_tools
def test_markdown_draft_is_copied_with_its_images(tmp_path):
    src = tmp_path / "src"; src.mkdir(); (src / "images").mkdir()
    (src / "images" / "fig1.png").write_bytes(b"\x89PNG")
    (src / "post.md").write_text("# 제목\n\n![그림](images/fig1.png)\n\n그림 1. 구성\n", encoding="utf-8")
    r = subprocess.run(["python3", str(PREPARE), str(src / "post.md"), "--dir", str(tmp_path / "rev")],
                       capture_output=True, text=True, check=True)
    work = tmp_path / "rev" / "post"
    assert (work / "draft.md").exists() and (work / "images" / "fig1.png").exists()
    assert (work / "05-claims.md").exists() and (work / "review-report.md").exists()
    assert "1 images" in r.stdout


@needs_tools
def test_word_file_from_the_builder_round_trips_structure(tmp_path):
    work = tmp_path / "w"; work.mkdir(); (work / "images").mkdir()
    md = FIXTURE.read_text(encoding="utf-8")
    for img in set(re.findall(r"!\[[^\]]*\]\(([^)\s]+)\)", md)):
        (work / img).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(PLUGIN.parents[1] / "plugins" / "aws-diagram-design" / "README.md", work / img) if False else None
    # a real PNG so docx-js can embed it
    png = bytes.fromhex("89504e470d0a1a0a0000000d494844520000000100000001080600000" "01f15c4890000000d49444154789c6360000002000154a24f5d0000000049454e44ae426082")
    for img in set(re.findall(r"!\[[^\]]*\]\(([^)\s]+)\)", md)):
        (work / img).write_bytes(png)
    (work / "06-final.md").write_text(md, encoding="utf-8")
    (work / "placeholders.md").write_text("# 남은 placeholder (0개)\n", encoding="utf-8")
    subprocess.run(["node", str(BUILD), str(work / "06-final.md"), "--out", str(work / "06-final.docx")],
                   capture_output=True, text=True, check=True)

    r = subprocess.run(["python3", str(PREPARE), str(work / "06-final.docx"), "--slug", "rt", "--dir", str(tmp_path / "rev")],
                       capture_output=True, text=True, check=True)
    out = (tmp_path / "rev" / "rt" / "draft.md").read_text(encoding="utf-8")

    def count(pattern, text):
        return len(re.findall(pattern, text, flags=re.M))
    assert count(r"^# ", out) == 1, out[:400]
    assert count(r"^## ", out) == count(r"^## ", md)
    assert count(r"^### ", out) == count(r"^### ", md)
    assert count(r"^```", out) == count(r"^```", md), out
    assert count(r"^!\[", out) == count(r"^!\[", md)
    assert "<img" not in out and "custom-style" not in out and "남은 placeholder" not in out
    for tag in ("[작성자 확인]", "[기술 검증 필요]", "[이미지 필요]", "[인용 승인 필요]"):
        assert md.count(tag) == out.count(tag), tag
        assert out.count(f'<span style="background-color') >= 1
    assert not (tmp_path / "rev" / "rt" / "media").exists()
    assert "code blocks" in r.stdout


def test_in_place_reviews_the_writer_work_dir_without_copying_it(tmp_path):
    work = tmp_path / "blog-work" / "post"; (work / "images").mkdir(parents=True)
    (work / "images" / "fig1.png").write_bytes(b"\x89PNG")
    (work / "01-facts.md").write_text("# facts\n", encoding="utf-8")
    src_text = "# 제목\n\n![그림](images/fig1.png)\n\n그림 1. 구성\n"
    (work / "04-draft.md").write_text(src_text, encoding="utf-8")
    r = subprocess.run(["python3", str(PREPARE), str(work / "04-draft.md"), "--in-place"],
                       capture_output=True, text=True, cwd=tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr
    assert (work / "draft.md").read_text(encoding="utf-8") == src_text
    assert (work / "04-draft.md").read_text(encoding="utf-8") == src_text, "the writer's artifact is untouched"
    assert (work / "05-claims.md").exists() and (work / "review-report.md").exists()
    assert not (tmp_path / "blog-review").exists(), "in-place must not create a second work dir"
    assert f"work: {work.resolve()}" in r.stdout
    assert "images/fig1.png" in src_text and (work / "images" / "fig1.png").exists()
