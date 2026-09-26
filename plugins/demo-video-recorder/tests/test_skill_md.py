import json
import re
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1]
SKILL = PLUGIN / "skills" / "recording-demo-videos"
SKILL_MD = SKILL / "SKILL.md"
SCRIPT_MD = SKILL / "references" / "script.md"


def frontmatter() -> str:
    fm = re.match(r"^---\n(.*?)\n---\n", SKILL_MD.read_text(), re.S)
    assert fm, "missing frontmatter"
    return fm.group(1)


def test_frontmatter_names_the_skill_and_fits_the_spec_limit():
    fm = frontmatter()
    assert "name: recording-demo-videos" in fm
    assert len(fm) <= 1024, f"frontmatter is {len(fm)} chars; the Agent Skills spec caps it at 1024"
    assert re.search(r"description: Use when", fm), "description must start with the triggering condition"
    assert "데모 영상" in fm, "Korean triggers, like the other hi-aws-skills plugins"


def test_manifests_agree_on_name_and_version():
    a = json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_text())
    b = json.loads((PLUGIN / "plugin.json").read_text())
    assert a["name"] == b["name"] == "demo-video-recorder"
    assert a["version"] == b["version"]


def test_every_linked_reference_exists_and_the_old_split_is_gone():
    text = SKILL_MD.read_text()
    links = set(re.findall(r"\]\((references/[^)#]+|scripts/[^)#]+)\)", text))
    assert {"references/script.md", "references/reel-manifest.md"} <= links
    missing = sorted(l for l in links if not (SKILL / l).exists())
    assert missing == []
    # 1.2.0 merged story.md + caption-style.md into script.md; a stale file would be read by mistake
    assert not (SKILL / "references" / "story.md").exists()
    assert not (SKILL / "references" / "caption-style.md").exists()


def test_scripts_are_invoked_through_their_interpreter():
    text = SKILL_MD.read_text()
    assert "node scripts/record_demo.mjs" in text and "python3 scripts/edit_demo.py" in text
    assert "python3 scripts/make_cards.py" in text
    assert not re.search(r"(?<![\w/])scripts/edit_demo\.py clip", text.replace("python3 scripts/edit_demo.py", "")), \
        "never call a bundled script by bare path; plugin packagers strip executable bits"


def test_skill_states_the_recording_and_tempo_defaults():
    """1.2.0: output is 1080p; a UI that fits one screen is laid out at 1280x720 and zoomed; clips play at 1.25x."""
    text = SKILL_MD.read_text()
    assert "--layout 1280x720" in text, "the one-screen layout option must be in the record step"
    assert "1.25" in text, "default clip tempo"
    for must in ("speed", "fade_in", ".mov", "re-record"):
        assert must in text, f"SKILL.md lost the lesson keyed by {must!r}"


def test_skill_is_lean():
    """User request 2026-09-26: only what is necessary; over-constraints removed."""
    text = SKILL_MD.read_text()
    words = len(text.split())
    assert words <= 1100, f"SKILL.md is {words} words; 1.1.0 was 2037 and was judged too constrained"
    for residue in ("Laya", "Bedrock", "AgentCore", "Radix", "Settings 탭", "settings tab", "Argument video", "argument video"):
        assert residue not in text, f"project-specific residue {residue!r} in SKILL.md"
    for residue in ("Laya", "Bedrock", "AgentCore", "Registry", "argument video", "Argument video"):
        assert residue not in SCRIPT_MD.read_text(), f"project-specific residue {residue!r} in script.md"


def test_script_reference_defines_cards_and_voice():
    """Intro card = the message and what the demo shows; summary card = take home messages; chapter cards between."""
    ref = SCRIPT_MD.read_text()
    low = ref.lower()
    assert "intro card" in low and "the message" in low and "what the demo shows" in low, "intro card: message + what the demo shows"
    assert "take home" in low or "take-home" in low, "summary card = take home messages"
    assert "chapter card" in low or "간지" in ref, "chapter (간지) cards between chapters"
    for must in ("합니다체", "U+2014", "U+00B7", "U+2192", "45"):
        assert must in ref, f"script.md must state the voice rule keyed by {must!r}"
    assert "describe" in low or "묘사" in ref, "a beat says what the feature does, not what the frame shows"


def test_korean_examples_obey_the_voice_rules():
    """Every Korean example line (outside ✗ bad examples) must itself follow the rules, or the next reel copies it."""
    hangul = re.compile(r"[가-힣]")
    for path in (SCRIPT_MD, SKILL_MD, PLUGIN / "README.md"):
        for n, line in enumerate(path.read_text().splitlines(), 1):
            if not hangul.search(line) or "✗" in line:
                continue
            for ch in ("—", "·", "→"):
                assert ch not in line, f"{path.name}:{n} Korean line uses {ch!r}: {line.strip()}"
            assert "배속)" not in line, f"{path.name}:{n} example carries a speed label: {line.strip()}"


def test_edit_demo_docstring_carries_the_look_constants():
    """caption-style.md is gone; the drawing constants must be readable from `edit_demo.py --help`."""
    code = (SKILL / "scripts" / "edit_demo.py").read_text()
    doc = code.split('"""')[1]
    for token in ("1.25", "58", "32", "34", "h-150"):
        assert token in doc, f"edit_demo.py docstring does not state {token}"
    for token in ("size=58", "size=32", "size=34", "0x1f6feb", "h-150"):
        assert token in code, f"style constant {token} moved out of edit_demo.py"
