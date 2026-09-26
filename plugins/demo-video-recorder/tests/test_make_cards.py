"""make_cards.py: title/summary cards from a JSON spec → 1080p MP4 + PNG. Needs ffmpeg and Pillow."""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

PLUGIN = Path(__file__).resolve().parents[1]
SCRIPTS = PLUGIN / "skills" / "recording-demo-videos" / "scripts"
pytest.importorskip("PIL")
needs_ffmpeg = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not installed")

SPEC = {
    "card-intro": {"seconds": 3, "lines": [
        ["kicker", "Agent Platform 데모", "accent"],
        ["title", "코드 없이 에이전트를 만들고"],
        ["title", "한 화면에서 운영합니다"],
        ["gap"],
        ["row", "Registry에서 에이전트와 스킬을 찾아 바로 실행해 봅니다"],
        ["row", "비용과 사용량, 가드레일을 한 화면에서 확인합니다", "accent"],
    ]},
    "card-summary": {"seconds": 2, "lines": [
        ["kicker", "정리", "accent"],
        ["row", "에이전트는 코드 배포 없이 만들고 수정합니다", "warn"],
        ["row", "모델과 프롬프트는 대화마다 바꿉니다", "#b39cff"],
    ]},
}


def test_fixture_obeys_the_caption_voice_rules():
    """The fixture is the example the next reel copies; it must follow references/script.md itself."""
    for card in SPEC.values():
        for line in card["lines"]:
            text = line[1] if len(line) > 1 else ""
            for ch in ("—", "·", "→"):
                assert ch not in text, f"fixture line uses {ch!r}: {text}"


def probe(path: Path, entries: str) -> str:
    return subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", entries, "-of", "csv=p=0",
                           str(path)], check=True, capture_output=True, text=True).stdout.strip()


@needs_ffmpeg
def test_cards_render_to_1080p_mp4_and_png(tmp_path, monkeypatch):
    spec = tmp_path / "cards.json"
    spec.write_text(json.dumps(SPEC, ensure_ascii=False))
    monkeypatch.setenv("TMPDIR", str(tmp_path / "tmp"))
    (tmp_path / "tmp").mkdir()
    subprocess.run([sys.executable, str(SCRIPTS / "make_cards.py"), str(spec), "--out", str(tmp_path / "cards")], check=True)
    for name, card in SPEC.items():
        mp4, png = tmp_path / "cards" / f"{name}.mp4", tmp_path / "cards" / f"{name}.png"
        assert mp4.exists() and png.exists()
        assert probe(mp4, "stream=width,height") == "1920,1080"
        assert abs(float(probe(mp4, "format=duration")) - card["seconds"]) < 0.3
    assert list((tmp_path / "tmp").iterdir()) == [], "cards must not leave temp files"


def test_unknown_line_kind_or_colour_role_is_an_error(tmp_path):
    spec = tmp_path / "cards.json"
    spec.write_text(json.dumps({"c": {"seconds": 1, "lines": [["headline", "x"]]}}))
    r = subprocess.run([sys.executable, str(SCRIPTS / "make_cards.py"), str(spec), "--out", str(tmp_path / "o")],
                       capture_output=True, text=True)
    assert r.returncode != 0 and "headline" in r.stderr
