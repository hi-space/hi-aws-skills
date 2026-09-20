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
    assert "Do not open the source documents" in drafter
    assert "aws-tech-blog-writer:blog-drafter" in drafter
    assert "aws-tech-blog-writer:blog-fact-checker" in (SKILL / "templates" / "prompt-fact-checker.md").read_text()


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


def test_root_manifest_mirrors_claude_plugin_manifest_apart_from_schema():
    a = json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_text())
    b = json.loads((PLUGIN / "plugin.json").read_text())
    b.pop("$schema", None)
    assert a == b, "root plugin.json drifted from .claude-plugin/plugin.json (the other plugins keep them identical)"


def test_skill_source_url_matches_plugin_repository():
    repo = json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_text())["repository"]
    assert f'source: "{repo}"' in frontmatter()


def test_conventions_skeletons_do_not_use_the_figurative_axis():
    conv = (SKILL / "references" / "aws-blog-conventions.md").read_text()
    for phrase in ("각 축", "핵심 축", "평면/축", "축 3~5개"):
        assert phrase not in conv, f"'{phrase}': voice.md §1.3 bans 축 as a workstream, and the drafter reads this file"


def test_blog_post_template_reaches_the_drafter_and_is_not_pre_copied():
    drafter = (SKILL / "templates" / "prompt-drafter.md").read_text()
    assert "templates/blog-post.md" in drafter, "the drafter must read the skeleton or the template is dead weight"
    assert "templates/blog-post.md" in (PLUGIN / "agents" / "blog-drafter.md").read_text()
    init = (SKILL / "scripts" / "init_workspace.py").read_text()
    assert '"blog-post.md": "04-draft.md"' not in init, "04-draft.md is written by the drafter, not pre-filled"
    assert "eight files" in SKILL_MD.read_text()


def test_figure_file_names_agree_across_skill_and_templates():
    files = [SKILL_MD, SKILL / "templates" / "blog-post.md", SKILL / "templates" / "diagram-manifest.md"]
    for f in files:
        assert ".drawio.png" not in f.read_text(), f"{f.name}: shipping PNGs are figN-<name>.png (SKILL.md Stage 3)"


def agent_frontmatter(name: str) -> dict:
    text = (PLUGIN / "agents" / f"{name}.md").read_text()
    fm = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    assert fm, f"{name}: missing frontmatter"
    fields = dict(re.findall(r"^(\w+):\s*(.*)$", fm.group(1), re.M))
    fields["_body"] = text[fm.end():]
    return fields


def test_drafter_agent_is_confined_to_read_and_write():
    a = agent_frontmatter("blog-drafter")
    assert a["name"] == "blog-drafter"
    tools = {x.strip() for x in a["tools"].split(",")}
    assert tools == {"Read", "Write"}, "the drafter must not be able to search, run commands, or spawn agents"
    assert len(a["_body"]) <= 10000
    for needle in ("voice.md", "01-facts.md", "04-draft.md", "<!-- F04 F09 -->", "When to invoke"):
        assert needle in a["_body"], needle


def test_fact_checker_agent_has_documentation_tools_and_cannot_edit_the_draft_by_design():
    a = agent_frontmatter("blog-fact-checker")
    tools = {x.strip() for x in a["tools"].split(",")}
    assert {"Read", "Write", "WebFetch", "mcp__aws-docs__search_documentation", "mcp__aws-docs__read_documentation",
            "mcp__aws-mcp__aws___search_documentation"} <= tools
    assert "Bash" not in tools and "Agent" not in tools and "Edit" not in tools
    assert len(a["_body"]) <= 10000
    for needle in ("05-claims.md", "never edit", "unverified", "check_claims.py", "When to invoke"):
        assert needle in a["_body"], needle


def test_skill_md_names_both_agents_and_a_fallback():
    text = re.sub(r"\s+", " ", SKILL_MD.read_text())
    for needle in ("subagent_type: aws-tech-blog-writer:blog-drafter", "subagent_type: aws-tech-blog-writer:blog-fact-checker",
                   "agents/blog-drafter.md", "agents/blog-fact-checker.md", "not registered"):
        assert needle in text, needle
    assert (PLUGIN / "agents" / "blog-drafter.md").exists() and (PLUGIN / "agents" / "blog-fact-checker.md").exists()
    assert "blog-drafter" in (PLUGIN / "README.md").read_text()
