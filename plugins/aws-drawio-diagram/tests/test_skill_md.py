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
