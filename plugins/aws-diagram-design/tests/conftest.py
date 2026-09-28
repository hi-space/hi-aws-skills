"""Load the skill's hyphen-named scripts as modules."""
import importlib.util
import sys
from pathlib import Path

import pytest

PLUGIN = Path(__file__).resolve().parents[1]
SKILL = PLUGIN / "skills" / "aws-diagram-design"
SCRIPTS = SKILL / "scripts"


def load_script(name: str):
    """`load_script("verify-geometry")` → module object for <skill>/scripts/verify-geometry.py."""
    path = SCRIPTS / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="session")
def skill_dir() -> Path:
    return SKILL


GOOD_SVG = """<?xml version="1.0" encoding="UTF-8"?>
<svg viewBox="0 0 400 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="demo-title demo-desc">
  <title id="demo-title">Demo</title>
  <desc id="demo-desc">Two boxes joined by an arrow.</desc>
  <defs>
    <marker id="arrow" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><polygon points="0 0, 8 3, 0 6" fill="#545B64"/></marker>
  </defs>
  <rect width="100%" height="100%" fill="#ffffff"/>
  <path d="M 120,100 H 240" stroke="#545B64" stroke-width="1.2" marker-end="url(#arrow)"/>
  <rect x="40" y="72" width="80" height="56" rx="6" fill="#ffffff" stroke="#232F3E"/>
  <text x="80" y="104" font-family="'Amazon Ember', Helvetica, Arial, sans-serif" font-size="12" font-weight="600" text-anchor="middle" fill="#232F3E">Client</text>
  <rect x="240" y="72" width="80" height="56" rx="6" fill="#ffffff" stroke="#232F3E"/>
  <text x="280" y="104" font-family="'Amazon Ember Mono', ui-monospace, monospace" font-size="9" text-anchor="middle" fill="#545B64">api:443</text>
</svg>
"""


@pytest.fixture
def good_svg(tmp_path) -> Path:
    p = tmp_path / "demo.svg"
    p.write_text(GOOD_SVG, encoding="utf-8")
    return p
