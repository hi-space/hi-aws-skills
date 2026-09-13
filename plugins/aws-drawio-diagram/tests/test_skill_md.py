import re
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1]
SKILL = PLUGIN / "skills" / "aws-drawio-diagram"
SKILL_MD = SKILL / "SKILL.md"


def test_frontmatter():
    text = SKILL_MD.read_text()
    fm = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    assert fm, "missing frontmatter"
    assert "name: aws-drawio-diagram" in fm.group(1)
    assert "draw.io로" in fm.group(1) and "드로우아이오" in fm.group(1)
    assert "aws-diagram-design" in fm.group(1)


def test_every_linked_reference_exists():
    text = SKILL_MD.read_text()
    links = set(re.findall(r"\]\((references/[^)#]+|scripts/[^)#]+|templates/[^)#]+)\)", text))
    assert links, "SKILL.md should link its references"
    missing = sorted(l for l in links if not (SKILL / l).exists())
    assert missing == []


def test_mentions_validator_and_lookup_order():
    text = SKILL_MD.read_text()
    assert "scripts/validate_drawio.py" in text
    assert "aws-icons-aliases.md" in text and "aws-icons-extra.md" in text
    assert "aws3d" not in text.lower()


def test_phased_procedure_and_builder():
    text = SKILL_MD.read_text()
    for needle in ("Architect", "Assessor", "Drawer", "Reviewer", "scripts/build_diagram.py",
                   "references/architecture-brief.md", "references/architecture-review.md",
                   "references/review-checklist.md", "references/from-source-code.md", "W7", "W9",
                   "scripts/scaffold_spec.py", "layout.py", ".layout.json"):
        assert needle in text, needle
    assert (SKILL / "scripts" / "build_diagram.py").exists()
    assert (SKILL / "references" / "architecture-review.md").exists()


def test_output_set_has_a_guide_and_a_single_final_png():
    skill = SKILL_MD.read_text()
    # the step-by-step companion is its own deliverable, written from a template
    assert ".guide.md" in skill and "references/architecture-guide.md" in skill
    guide = (SKILL / "references" / "architecture-guide.md").read_text()
    for needle in ("## Step-by-step", "## Services", "## Design decisions", "Language:",
                   "One step per row of the brief's Relationships"):
        assert needle in guide, needle
    # the preview PNG is a Reviewer working file: it is deleted once the verdict is `ready`
    assert ".preview.png" in skill and "delete" in skill.lower()
    review = (SKILL / "references" / "review-checklist.md").read_text()
    assert ".guide.md" in review and ".preview.png" in review
    # layout-and-style no longer describes a different companion file than SKILL.md does
    style = (SKILL / "references" / "layout-and-style.md").read_text()
    assert "architecture-guide.md" in style and "name.md" not in style


def test_edge_text_is_the_what_flows_phrase():
    style = (SKILL / "references" / "layout-and-style.md").read_text()
    section = style.split("## 5.")[1].split("## 6.")[0]
    for needle in ("What flows", "3 lines", "24 characters", "6 characters", "12 characters", "longest leg", "OUTSIDE_GAP"):
        assert needle in section, needle
    assert "badge" not in section and "cannot carry a label" not in section
    brief = (SKILL / "references" / "architecture-brief.md").read_text()
    assert "## Edge text" in brief and "What flows" in brief and "Label on diagram" not in brief and "badge" not in brief
    skill = SKILL_MD.read_text()
    assert "What flows" in skill and "number badge" not in skill        # "corner badge" of a group is a different thing
    review = (SKILL / "references" / "review-checklist.md").read_text()
    assert "≤ 5 edge labels" not in review and "badge" not in review and "What flows" in review


def test_contract_lock_and_title_band_are_documented():
    skill = SKILL_MD.read_text()
    assert ".contract.json" in skill
    brief = (SKILL / "references" / "architecture-brief.md").read_text()
    assert ".contract.json" in brief
    review = (SKILL / "references" / "review-checklist.md").read_text()
    assert ".contract.json" in review and "newly marked" in review
    style = (SKILL / "references" / "layout-and-style.md").read_text()
    assert "title" in style.split("## 5.")[1].split("## 6.")[0].lower()
    # a primary label that does not fit stops the build; "acceptable" is not a Reviewer verdict for it
    assert "ERROR label" in skill and "ERROR label" in review and "ERROR label" in style


def test_guide_is_numbered_in_the_users_language_and_checked_mechanically():
    skill = SKILL_MD.read_text()
    assert "Language:" in skill and "scripts/check_guide.py" in skill
    guide = (SKILL / "references" / "architecture-guide.md").read_text()
    for needle in ("Language:", "What flows", "(라벨 `", "## 단계별 흐름", "## 서비스", "## 설계 결정", "step per relationship"):
        assert needle in guide, needle
    assert "badge" not in guide and "배지" not in guide
    brief = (SKILL / "references" / "architecture-brief.md").read_text()
    assert "Language:" in brief
    review = (SKILL / "references" / "review-checklist.md").read_text()
    assert "check_guide.py" in review and "quote" in review
    assert (SKILL / "scripts" / "check_guide.py").exists()


def test_architecture_review_is_evidence_only():
    text = (SKILL / "references" / "architecture-review.md").read_text()
    for needle in ("No source → no finding", "knowledge-mcp.global.api.aws", "retrieve_skill",
                   "search_documentation", "wellarchitected/latest", "skipped"):
        assert needle in text, needle
    # the brief template reserves the section the Assessor fills in
    assert "## Architecture review" in (SKILL / "references" / "architecture-brief.md").read_text()


def test_codebase_input_rules_are_present():
    skill = SKILL_MD.read_text()
    assert "abstract node" in skill and "deployable unit" in skill
    src = (SKILL / "references" / "from-source-code.md").read_text()
    for needle in ("## Scope", "Evidence", "Provenance", "deployed", "referenced", "assumed",
                   "Never an abstract node", "one diagram", "aws_lambda_function", "Res_Amazon-Bedrock-AgentCore_Runtime_48.svg"):
        assert needle in src, needle
    # every stencil the mapping table names exists in the catalog
    import json, re
    index = set(json.loads((SKILL / "scripts" / "stencil-index.json").read_text())["stencils"])
    table = src[src.index("| Terraform / CloudFormation / CDK"):src.index("Every other type")]
    names = set(re.findall(r"\| `([a-z0-9_]+)`", table)) | set(re.findall(r", `([a-z0-9_]+)`", table)) | set(re.findall(r"`([a-z0-9_]+)` / `([a-z0-9_]+)`", table) and sum(re.findall(r"`([a-z0-9_]+)` / `([a-z0-9_]+)`", table), ()))
    names = {n for n in names if not n.startswith("aws_") and n not in {"lambda_function", "ecs", "agentcore", "eks_cloud"}}
    missing = sorted(n for n in names if n not in index)
    assert missing == [], missing
    review = (SKILL / "references" / "review-checklist.md").read_text()
    assert "No abstract nodes" in review and "not ready" in review and "W9" in review
    assess = (SKILL / "references" / "architecture-review.md").read_text()
    assert "Spot-check" in assess and "call count" in assess
