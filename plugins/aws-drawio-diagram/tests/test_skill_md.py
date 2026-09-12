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
