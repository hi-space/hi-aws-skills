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
        ["kicker", "Physical AI · 실험", "accent"],
        ["title", "System One 모델을 로봇 제어의"],
        ["title", "어디에, 어떻게 쓸 것인가"],
        ["gap"],
        ["row", "Jev: typed 질문 → 보정된 확률, 한 번의 forward pass"],
        ["row", "Laya: 오픈 가중치 → 로봇 state로 fine-tune, 15% → 96%", "accent"],
    ]},
    "card-summary": {"seconds": 2, "lines": [
        ["kicker", "정리", "accent"],
        ["row", "코드로 처리할 판단 — 안전 정지", "warn"],
        ["row", "LLM Agent에 넘길 판단 — 복구 전략", "#b39cff"],
    ]},
}


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
