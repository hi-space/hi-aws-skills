"""edit_demo.py: anchor resolution, speed, reel fades, temp-dir cleanup. Needs ffmpeg/ffprobe on PATH."""
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

PLUGIN = Path(__file__).resolve().parents[1]
SCRIPTS = PLUGIN / "skills" / "recording-demo-videos" / "scripts"

spec = importlib.util.spec_from_file_location("edit_demo", SCRIPTS / "edit_demo.py")
edit_demo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(edit_demo)

needs_ffmpeg = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not installed")

LOG = [
    {"t": 1.0, "kind": "shot", "key": "hero", "label": "Page overview"},
    {"t": 3.0, "kind": "shot", "key": "stage", "label": "Stage"},
    {"t": 4.5, "kind": "play"},
    {"t": 6.0, "kind": "caption", "text": "System 2에 복구를 요청"},
    {"t": 8.0, "kind": "shot", "key": "stage", "label": "Stage again"},
]


# ---------------------------------------------------------------- script_time

def test_anchor_forms_resolve_to_camlog_seconds():
    assert edit_demo.script_time(41.0, LOG) == 41.0
    assert edit_demo.script_time("shot:stage", LOG) == 3.0
    assert edit_demo.script_time("shot:stage#2", LOG) == 8.0
    assert edit_demo.script_time("caption:System 2", LOG) == 6.0
    assert edit_demo.script_time("note:play", LOG) == 4.5
    assert edit_demo.script_time("play", LOG) == 4.5


def test_missing_anchor_aborts_with_its_name():
    with pytest.raises(SystemExit, match="shot:table"):
        edit_demo.script_time("shot:table", LOG)


# ---------------------------------------------------------------- fixtures

def make_video(path: Path, seconds: float, size: str = "1920x1080") -> Path:
    """Test pattern. .webm = a raw Playwright take (VP8, no audio); .mp4 = a finished clip (H.264 + silent AAC)."""
    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"testsrc=size={size}:rate=30:duration={seconds}"]
    if path.suffix == ".webm":
        cmd += ["-c:v", "libvpx", "-pix_fmt", "yuv420p"]
    else:
        cmd += ["-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000", "-shortest",
                "-pix_fmt", "yuv420p", "-c:a", "aac"]
    subprocess.run(cmd + [str(path)], check=True)
    return path


@pytest.fixture
def raw(tmp_path):
    """A 10 s webm with a camlog beside it, like record_demo.mjs writes (long enough for beats after the 4.2 s title)."""
    video = make_video(tmp_path / "take.webm", 10)
    (tmp_path / "take.camlog.json").write_text(json.dumps({"log": [
        {"t": 0.5, "kind": "shot", "key": "hero", "label": "wide"},
        {"t": 2.0, "kind": "run_clicked"},
        {"t": 4.0, "kind": "shot", "key": "table", "label": "results"},
    ]}))
    return video


@pytest.fixture
def private_tmp(tmp_path, monkeypatch):
    """Point tempfile at an empty dir so leftovers are visible."""
    d = tmp_path / "tmpdir"
    d.mkdir()
    monkeypatch.setenv("TMPDIR", str(d))
    import tempfile
    tempfile.tempdir = None
    yield d
    tempfile.tempdir = None


# ---------------------------------------------------------------- clip

@needs_ffmpeg
def test_clip_removes_its_temp_dir_and_reports_caption_count(raw, tmp_path, private_tmp, capsys):
    script = tmp_path / "story.json"
    script.write_text(json.dumps({"title": "T", "subtitle": "S", "beats": [
        {"at": "shot:hero", "text": "first"},
        {"at": "run_clicked", "text": "second", "style": "insight"},
        {"at": "shot:table", "text": "third", "pos": "top"},
    ]}))
    out = tmp_path / "clips" / "take.mp4"
    edit_demo.build_clip(raw, out, None, None, None, None, True, None, script)
    assert out.exists()
    assert list(private_tmp.iterdir()) == [], "clip must delete its drawtext temp dir"
    report = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert report["captions"] == 3, "count beats, not filter-graph entries"


@needs_ffmpeg
def test_clip_default_tempo_is_1_25x(raw, tmp_path, private_tmp):
    """1.2.0: every clip plays at 1.25x unless the script says otherwise; 10 s of raw footage becomes 8 s."""
    script = tmp_path / "story.json"
    script.write_text(json.dumps({"start": 0, "beats": [{"at": 4.0, "text": "late"}]}))
    out = tmp_path / "default.mp4"
    edit_demo.build_clip(raw, out, None, None, None, None, True, None, script)
    assert abs(edit_demo.probe_duration(out) - 8.0) < 0.3
    assert edit_demo.DEFAULT_SPEED == 1.25


@needs_ffmpeg
def test_clip_speed_shortens_the_output_and_keeps_raw_second_anchors(raw, tmp_path, private_tmp):
    script = tmp_path / "story.json"
    script.write_text(json.dumps({"speed": 2, "start": 0, "beats": [{"at": 4.0, "text": "late"}]}))
    out = tmp_path / "fast.mp4"
    edit_demo.build_clip(raw, out, None, None, None, None, True, None, script)
    assert abs(edit_demo.probe_duration(out) - 5.0) < 0.3


@needs_ffmpeg
def test_clip_without_script_uses_shot_labels_and_default_clips_dir(raw, tmp_path, private_tmp, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["edit_demo.py", "clip", str(raw), "--title", "T"])
    edit_demo.main()
    assert (tmp_path / "clips" / "take.mp4").exists(), "default output is ./clips/<stem>.mp4, not a project path"


# ---------------------------------------------------------------- reel

@needs_ffmpeg
def test_reel_honours_per_segment_fades_and_cleans_up(tmp_path, private_tmp):
    a = make_video(tmp_path / "a.mp4", 3)
    b = make_video(tmp_path / "b.mp4", 3)
    spec_path = tmp_path / "reel.json"
    spec_path.write_text(json.dumps({"fade": 0.4, "segments": [
        {"file": str(a), "start": 0, "end": 2, "fade_out": 0},
        {"file": str(b), "start": 1, "end": 3, "fade_in": 0},
    ]}))
    out = tmp_path / "reel.mp4"
    edit_demo.build_reel(spec_path, out)
    assert abs(edit_demo.probe_duration(out) - 4.0) < 0.3
    assert list(private_tmp.iterdir()) == [], "reel must delete its part files"


@needs_ffmpeg
def test_reel_refuses_mixed_resolutions_before_encoding(tmp_path, private_tmp):
    a = make_video(tmp_path / "a.mp4", 2)
    b = make_video(tmp_path / "b.mp4", 2, size="1080x1080")
    spec_path = tmp_path / "reel.json"
    spec_path.write_text(json.dumps({"segments": [{"file": str(a)}, {"file": str(b)}]}))
    with pytest.raises(SystemExit, match="1080x1080"):
        edit_demo.build_reel(spec_path, tmp_path / "reel.mp4")
