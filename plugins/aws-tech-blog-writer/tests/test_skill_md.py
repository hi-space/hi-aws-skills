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


def test_writer_pipeline_ends_by_invoking_the_review_skill():
    text = SKILL_MD.read_text()
    # the progress checklist stops at the hand-off; fact-check, style pass and Word build live in aws-blog-review
    assert re.search(r"- \[ \] Stage 5 .*aws-blog-review", text), "Stage 5 must be the hand-off to aws-blog-review"
    for gone in ("Stage 6", "Stage 5b", "06-final", "Style pass", "prompt-fact-checker.md",
                 "build_docx.js <work>", "check_claims.py <work>"):
        assert gone not in text, f"writer SKILL.md still carries the old pipeline: {gone}"
    assert "--in-place" in text, "the hand-off must tell the review skill to work inside <work>"
    assert "Never build a Word file from `04-draft.md`" in text
    assert not (SKILL / "templates" / "prompt-fact-checker.md").exists(), "only the review skill fact-checks now"
    # the Word build still exists, in the review skill, and names the file after the post title
    review = (PLUGIN / "skills" / "aws-blog-review" / "SKILL.md").read_text()
    assert "build_docx.js" in review and "--name-from-title" not in SKILL_MD.read_text()


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


def test_draft_runs_in_a_fresh_subagent():
    text = SKILL_MD.read_text()
    assert "prompt-drafter.md" in text
    assert "Never fork yourself" in text
    for tpl in ("prompt-drafter.md", "brief.md", "research.md"):
        assert (SKILL / "templates" / tpl).exists(), tpl
    # the drafter packet excludes the sources and digests
    drafter = (SKILL / "templates" / "prompt-drafter.md").read_text()
    assert "Do not open the source documents" in drafter
    assert "aws-tech-blog-writer:blog-drafter" in drafter


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


def test_writer_names_the_drafter_and_a_fallback_and_the_review_skill_names_the_checkers():
    text = re.sub(r"\s+", " ", SKILL_MD.read_text())
    for needle in ("subagent_type: aws-tech-blog-writer:blog-drafter", "agents/blog-drafter.md", "not registered"):
        assert needle in text, needle
    assert "subagent_type: aws-tech-blog-writer:blog-fact-checker" not in text, "the writer no longer fact-checks"
    review = re.sub(r"\s+", " ", (PLUGIN / "skills" / "aws-blog-review" / "SKILL.md").read_text())
    for needle in ("subagent_type: aws-tech-blog-writer:blog-fact-checker", "subagent_type: aws-tech-blog-writer:blog-reviewer"):
        assert needle in review, needle
    for agent in ("blog-drafter", "blog-fact-checker", "blog-reviewer"):
        assert (PLUGIN / "agents" / f"{agent}.md").exists(), agent
        assert agent in (PLUGIN / "README.md").read_text(), agent


def test_agents_and_references_no_longer_point_at_the_writer_fact_check_stage():
    for name in ("blog-fact-checker", "blog-reviewer", "blog-drafter"):
        body = (PLUGIN / "agents" / f"{name}.md").read_text()
        for gone in ("Stage 5", "Stage 5b", "style pass", "06-final"):
            assert gone not in body, f"{name}: {gone}"
    fc = agent_frontmatter("blog-fact-checker")
    assert "aws-blog-review" in fc["description"] and "Stage 5 of the aws-tech-blog-writer" not in fc["description"]
    for ref in ("verification.md", "placeholders.md", "voice.md"):
        text = (SKILL / "references" / ref).read_text()
        for gone in ("Stage 5", "Stage 6", "style pass"):
            assert gone not in text, f"{ref}: {gone}"
    assert "## Fact-check" in (SKILL / "references" / "verification.md").read_text()


# ---- aws-blog-review, the plugin's second skill

REVIEW = PLUGIN / "skills" / "aws-blog-review"
REVIEW_MD = REVIEW / "SKILL.md"


def review_frontmatter() -> str:
    fm = re.match(r"^---\n(.*?)\n---\n", REVIEW_MD.read_text(), re.S)
    assert fm, "missing frontmatter"
    return fm.group(1)


def test_review_skill_frontmatter_names_it_and_fits_the_limit():
    fm = review_frontmatter()
    assert "name: aws-blog-review" in fm
    assert len(fm) <= 1024, f"frontmatter is {len(fm)} chars"
    assert fm.count("description:") == 1
    for needle in ("블로그 리뷰", "블로그 검토", "Not for writing a post"):
        assert needle in fm, needle
    version = json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_text())["version"]
    assert f'version: "{version}"' in fm


def test_review_skill_links_resolve_and_reuses_the_writer_skill():
    text = REVIEW_MD.read_text()
    links = set(re.findall(r"\]\((references/[^)#]+|scripts/[^)#]+|templates/[^)#]*|\.\./\.\./agents/[^)#]+)\)", text))
    missing = sorted(l for l in links if not (REVIEW / l).exists())
    assert missing == [], missing
    for f in ("references/review-rubric.md", "templates/review-report.md", "templates/prompt-reviewer.md",
              "templates/prompt-fact-checker.md", "scripts/prepare_review.py"):
        assert (REVIEW / f).exists(), f
    for needle in ("lint_blog.py", "check_claims.py", "build_docx.js", "aws-tech-blog-writer:blog-fact-checker",
                   "aws-tech-blog-writer:blog-reviewer", "Never fork yourself", "review-report.md", "--in-place",
                   "--name-from-title"):
        assert needle in text, needle
    assert re.search(r"- \[ \] R5 .*<제목>\.docx", text), "the Word file is named after the post title"
    assert "revised.docx" not in text


def test_review_agent_is_read_write_only_and_the_prompts_name_the_agents():
    agent = (PLUGIN / "agents" / "blog-reviewer.md").read_text()
    fm = re.match(r"^---\n(.*?)\n---\n", agent, re.S).group(1)
    assert re.search(r"^tools: Read, Write$", fm, re.M), fm
    assert "name: blog-reviewer" in fm
    assert "aws-tech-blog-writer:blog-reviewer" in (REVIEW / "templates" / "prompt-reviewer.md").read_text()
    fc = (REVIEW / "templates" / "prompt-fact-checker.md").read_text()
    assert "aws-tech-blog-writer:blog-fact-checker" in fc and "Currency" in fc
    assert "<facts:" in fc, "when the draft comes from the writer, 01-facts.md separates project facts from claims"


def test_rubric_covers_the_six_criteria_and_eight_story_checks():
    rubric = (REVIEW / "references" / "review-rubric.md").read_text()
    for crit in ("| A |", "| B |", "| C |", "| D |", "| E |", "| F |"):
        assert crit in rubric, crit
    for check in ("S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8"):
        assert re.search(rf"\| {check} ", rubric), check
    for sev in ("차단", "수정", "권고"):
        assert sev in rubric


def test_writer_skill_hands_finished_drafts_to_the_review_skill():
    text = SKILL_MD.read_text()
    assert "aws-blog-review" in text
    readme = (PLUGIN / "README.md").read_text()
    assert "Stage 6" not in readme and "06-final" not in readme and "5b" not in readme
    assert "aws-blog-review" in readme and "--in-place" in readme
    version = json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_text())["version"]
    assert version.split(".")[0] == "3", "dropping the writer's Word build changes the outputs: major bump"
    assert "needs a style pass or a technical fact-check" not in frontmatter()
    lint = (SKILL / "scripts" / "lint_blog.py").read_text()
    assert '"E8"' in lint and "AWS_LINK_HOSTS" in lint


def test_rubric_maps_every_lint_code_and_defines_the_verdict_precedence():
    rubric = (REVIEW / "references" / "review-rubric.md").read_text()
    lint = (SKILL / "scripts" / "lint_blog.py").read_text()
    codes = sorted(set(re.findall(r'"(E\d|W\d)"', lint)))
    assert codes, "lint has no codes"
    for code in codes:
        assert re.search(rf"\| {code} ", rubric), f"lint code {code} has no row in the rubric"
    for needle in ("Never a bare `Lnn`", "One defect, one row", "구조 수정 필요 when", "criterion A; every other"):
        assert needle in rubric, needle
    assert "Lnn` for lint lines" not in REVIEW_MD.read_text()


def test_story_review_makes_heading_form_skeleton_and_figure_status_required_columns():
    rubric = (REVIEW / "references" / "review-rubric.md").read_text()
    for needle in ("| L | 소제목 (그대로) | 형태 |", "## 스켈레톤 대조", "| 그림 | 상태 |", "produces no finding"):
        assert needle in rubric, needle
    agent = (PLUGIN / "agents" / "blog-reviewer.md").read_text()
    for needle in ("Fill 형태 for each row", "스켈레톤 대조", "이미지 필요 row", "there is no finding"):
        assert needle in agent, needle
    assert "are not gaps you report" not in agent, "exemption clauses do not scope; the figure recipe carries the rule"
    # the reviewer still lists placeholders as findings in some runs; the report step filters them deterministically
    assert "**Story rows the report drops.**" in rubric
