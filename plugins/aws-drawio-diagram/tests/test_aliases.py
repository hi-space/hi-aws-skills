import json
import re
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1]
SKILL = PLUGIN / "skills" / "aws-drawio-diagram"
ALIASES = SKILL / "references" / "aws-icons-aliases.md"
INDEX = SKILL / "scripts" / "stencil-index.json"

ROW = re.compile(r"^\|\s*[^|]+\|\s*`([A-Za-z0-9_]+)`\s*\|\s*(service|resource|group|image)\s*\|", re.M)


def test_every_alias_target_exists_in_index():
    idx = json.loads(INDEX.read_text())["stencils"]
    rows = ROW.findall(ALIASES.read_text())
    assert len(rows) >= 20
    bad = [(n, p) for n, p in rows if p != "image" and n not in idx]
    assert bad == []


def test_alias_patterns_agree_with_index_kind():
    idx = json.loads(INDEX.read_text())["stencils"]
    rows = ROW.findall(ALIASES.read_text())
    mismatched = []
    for name, pattern in rows:
        if pattern == "image":
            continue
        kind = idx[name]["kind"]
        ok = (pattern == "service" and kind in ("service", "legacy")) \
            or (pattern == "resource" and kind in ("resource", "legacy")) \
            or (pattern == "group" and kind in ("group", "legacy"))
        if not ok:
            mismatched.append((name, pattern, kind))
    assert mismatched == []
