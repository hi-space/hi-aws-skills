import json
import re
from pathlib import Path

import pytest

PLUGIN = Path(__file__).resolve().parents[1]
SKILL = PLUGIN / "skills" / "aws-tech-blog-writer"
SKILL_MD = SKILL / "SKILL.md"


def frontmatter() -> str:
    fm = re.match(r"^---\n(.*?)\n---\n", SKILL_MD.read_text(), re.S)
    assert fm, "missing frontmatter"
    return fm.group(1)


def test_frontmatter_names_the_skill_and_fits_the_spec_limit():
    fm = frontmatter()
    assert "name: aws-tech-blog-writer" in fm
    assert len(fm) <= 1024, f"frontmatter is {len(fm)} chars; the Agent Skills spec caps it at 1024"
    assert "AWS 기술 블로그" in fm and ".docx" in fm


def test_manifests_agree_on_name_and_version():
    a = json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_text())
    b = json.loads((PLUGIN / "plugin.json").read_text())
    assert a["name"] == b["name"] == "aws-tech-blog-writer"
    assert a["version"] == b["version"]
    assert f'version: "{a["version"]}"' in frontmatter()


def test_every_linked_reference_exists():
    text = SKILL_MD.read_text()
    links = set(re.findall(r"\]\((references/[^)#]+|scripts/[^)#]+|templates/[^)#]*)\)", text))
    assert links, "SKILL.md should link its references"
    missing = sorted(l for l in links if not (SKILL / l).exists())
    assert missing == []


def test_pipeline_ends_with_the_word_build():
    text = SKILL_MD.read_text()
    for needle in ("Stage 6", "06-final.docx", "scripts/build_docx.js", "verification", "`docx` skill",
                   "pandoc -o file.docx"):
        assert needle in text, needle
    # the progress checklist the agent copies into its reply lists the docx step
    assert re.search(r"- \[ \] Stage 6 .*06-final\.docx", text)
    assert (SKILL / "scripts" / "build_docx.js").exists()
    # the hand-back names the Word file as the deliverable
    assert "`06-final.docx` (the deliverable)" in text


def test_placeholder_reference_no_longer_claims_pandoc_keeps_colours():
    ref = (SKILL / "references" / "placeholders.md").read_text()
    assert "survive `pandoc` to DOCX" not in ref
    assert "build_docx.js" in ref


def test_marketplace_registers_plugin():
    root = PLUGIN.parents[1]
    mp_file = root / ".claude-plugin" / "marketplace.json"
    if not mp_file.exists():
        pytest.skip("not in the source repo (installed plugin copy has no marketplace.json)")
    mp = json.loads(mp_file.read_text())
    names = {p["name"]: p for p in mp["plugins"]}
    assert "aws-tech-blog-writer" in names
    assert names["aws-tech-blog-writer"]["source"] == "./plugins/aws-tech-blog-writer"
    assert "aws-tech-blog-writer" in (root / "README.md").read_text()


def test_docs_and_license_present():
    for f in ("README.md", "LICENSE"):
        assert (PLUGIN / f).exists(), f


def test_draft_and_fact_check_run_in_fresh_subagents():
    text = SKILL_MD.read_text()
    assert "prompt-drafter.md" in text and "prompt-fact-checker.md" in text
    assert "Never fork yourself" in text
    for tpl in ("prompt-drafter.md", "prompt-fact-checker.md", "brief.md", "research.md"):
        assert (SKILL / "templates" / tpl).exists(), tpl
    # the drafter packet excludes the sources and digests
    drafter = (SKILL / "templates" / "prompt-drafter.md").read_text()
    assert "do not open the source documents" in drafter


def test_voice_rules_cover_the_three_machine_habits():
    voice = (SKILL / "references" / "voice.md").read_text()
    for needle in ("Active voice", "figurative", "noun phrases", "문제가 남습니다", "정리됩니다"):
        assert needle in voice, needle
    lint = (SKILL / "scripts" / "lint_blog.py").read_text()
    for name in ("PERSONIFICATION_RE", "AGENTIVE_PASSIVES", "PLAIN_HEADING_RE", "FIGURATIVE_AXIS_RE"):
        assert name in lint, name


def test_merged_references_are_gone():
    refs = SKILL / "references"
    for old in ("author-voice.md", "writing-rules-ko.md", "research.md", "fact-check.md"):
        assert not (refs / old).exists(), old
    for new in ("voice.md", "verification.md"):
        assert (refs / new).exists(), new
