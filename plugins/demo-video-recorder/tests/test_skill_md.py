import json
import re
import subprocess
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1]
SKILL = PLUGIN / "skills" / "recording-demo-videos"
SKILL_MD = SKILL / "SKILL.md"


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


def test_every_linked_reference_exists():
    text = SKILL_MD.read_text()
    links = set(re.findall(r"\]\((references/[^)#]+|scripts/[^)#]+)\)", text))
    assert {"references/story.md", "references/caption-style.md", "references/reel-manifest.md"} <= links
    missing = sorted(l for l in links if not (SKILL / l).exists())
    assert missing == []


def test_scripts_are_invoked_through_their_interpreter():
    text = SKILL_MD.read_text()
    assert "node scripts/record_demo.mjs" in text and "python3 scripts/edit_demo.py" in text
    assert not re.search(r"(?<![\w/])scripts/edit_demo\.py clip", text.replace("python3 scripts/edit_demo.py", "")), \
        "never call a bundled script by bare path; plugin packagers strip executable bits"


def test_skill_records_the_lessons_from_real_takes():
    text = SKILL_MD.read_text()
    for must in (
        "speed",                 # compress waits instead of playing them in full
        "fade_in",               # join pieces of one scene without a dip to black
        "re-record",             # second anchors need re-tuning, event anchors survive
        "caption-style.md",      # visual + writing rules live in one place
        ".mov",                  # a screen recording is a valid source, anchors are raw seconds
    ):
        assert must in text, f"SKILL.md is missing the lesson keyed by {must!r}"


def test_story_comes_before_the_screen():
    """User feedback 2026-09-25: captions carry the video's message; the frame is the evidence, not the text."""
    skill = SKILL_MD.read_text()
    story = (SKILL / "references" / "story.md").read_text()
    style = (SKILL / "references" / "caption-style.md").read_text()
    assert "python3 scripts/make_cards.py" in skill, "intro/summary cards are part of the pipeline"
    for must in ("message", "chapter", "card"):
        assert must in story.lower(), f"story.md must define the {must}"
    assert "not a description of the frame" in style or "describe the frame" in style, \
        "caption-style must say what a beat is instead of what is visible"
    assert "story.md" in style, "caption-style points back to the message the beats serve"


def test_caption_style_reference_matches_the_code():
    ref = (SKILL / "references" / "caption-style.md").read_text()
    code = (SKILL / "scripts" / "edit_demo.py").read_text()
    for token in ("size=58", "size=32", "size=34", "0x1f6feb", "h-150", "0.35"):
        assert token in code, f"style constant {token} moved out of edit_demo.py"
    for human in ("58", "32", "34", "1f6feb", "45"):
        assert human in ref, f"caption-style.md does not state {human}"
    assert "metaphor" in ref.lower() or "비유" in ref


def test_node_scripts_parse():
    for f in ("record_demo.mjs", "storyboard.example.mjs"):
        subprocess.run(["node", "--check", str(SKILL / "scripts" / f)], check=True)


def test_recorder_warns_when_a_selector_matches_nothing():
    src = (SKILL / "scripts" / "record_demo.mjs").read_text()
    assert "missing" in src and "console.warn" in src, "a silent no-op focus cost a whole take; warn and mark the camlog"


def test_caption_voice_rules_and_examples_obey_them():
    """User feedback 2026-09-25: a feature-tour reel was rejected for machine-sounding captions.

    The references must state the rules, and every Korean example they give (outside lines
    marked as a bad example with ✗) must itself follow them, or the next reel copies the example.
    """
    refs = SKILL / "references"
    style = (refs / "caption-style.md").read_text()
    for must in ("합니다체", "U+2014", "U+00B7", "U+2192", "배속", "누르지 않았습니다", "Feature tour"):
        assert must in style, f"caption-style.md must state the voice rule keyed by {must!r}"
    hangul = re.compile(r"[가-힣]")
    for name in ("caption-style.md", "story.md"):
        for n, line in enumerate((refs / name).read_text().splitlines(), 1):
            if not hangul.search(line) or "✗" in line:
                continue
            for ch in ("—", "·", "→"):
                assert ch not in line, f"{name}:{n} Korean example uses {ch!r}: {line.strip()}"
            assert "배속)" not in line, f"{name}:{n} example carries a speed label: {line.strip()}"
