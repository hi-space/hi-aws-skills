"""record_demo.mjs: the --layout option (one-screen UI laid out at 1280x720, zoomed to fill 1080p).

The smoke test needs Playwright: set PLAYWRIGHT_ROOT to a directory whose node_modules has playwright
(with chromium installed); otherwise it is skipped. Needs ffmpeg/ffprobe.
"""
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

PLUGIN = Path(__file__).resolve().parents[1]
SCRIPTS = PLUGIN / "skills" / "recording-demo-videos" / "scripts"
PW_ROOT = os.environ.get("PLAYWRIGHT_ROOT")

PAGE = """<!doctype html><html><head><style>
html,body{margin:0;height:100%;background:#ff0000}
body{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:8px;padding:8px;box-sizing:border-box;font:24px sans-serif}
.card{background:#fff;padding:12px;height:120px}
</style></head><body>
<script>for(let i=0;i<12;i++){document.write('<div class="card" id="c'+i+'">card '+i+'</div>')}</script>
</body></html>"""

STORYBOARD = """export default async function storyboard({ page, rec, siteUrl }) {
  await page.goto(siteUrl);
  await page.waitForTimeout(300);
  await rec.install();
  await rec.reset('wide', 'overview');
  await rec.sleep(1200);
  await rec.focus('card', '#c5', { pad: 12, kmax: 2 }, 'one card');
  await rec.sleep(1800);
  rec.note('done');
}"""


def test_node_scripts_parse():
    for f in ("record_demo.mjs", "storyboard.example.mjs"):
        subprocess.run(["node", "--check", str(SCRIPTS / f)], check=True)


def test_recorder_warns_when_a_selector_matches_nothing():
    src = (SCRIPTS / "record_demo.mjs").read_text()
    assert "missing" in src and "console.warn" in src, "a silent no-op focus cost a whole take; warn and mark the camlog"


def test_recorder_offers_the_layout_option_in_its_usage():
    src = (SCRIPTS / "record_demo.mjs").read_text()
    assert "--layout" in src and "1280x720" in src


def test_layout_must_keep_the_16_9_aspect():
    r = subprocess.run(["node", str(SCRIPTS / "record_demo.mjs"), "--url", "http://x", "--storyboard", "none.mjs",
                        "--layout", "1280x800"], capture_output=True, text=True)
    assert r.returncode == 2 and "16:9" in r.stderr, r.stderr


def frame_pixels(video: Path, t: float, tmp: Path) -> "list[tuple[int, int, int]]":
    from PIL import Image
    png = tmp / f"f{t}.png"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(t), "-i", str(video), "-frames:v", "1", str(png)], check=True)
    im = Image.open(png).convert("RGB")
    w, h = im.size
    assert (w, h) == (1920, 1080)
    return [im.getpixel((w - 3, h - 3)), im.getpixel((w - 3, 3)), im.getpixel((w // 2, h // 2))]


@pytest.mark.skipif(PW_ROOT is None or shutil.which("ffmpeg") is None, reason="needs PLAYWRIGHT_ROOT and ffmpeg")
def test_layout_1280x720_fills_the_1080p_frame_and_the_camera_still_lands(tmp_path):
    (tmp_path / "page.html").write_text(PAGE)
    (tmp_path / "sb.mjs").write_text(STORYBOARD)
    r = subprocess.run(["node", str(SCRIPTS / "record_demo.mjs"), "--url", (tmp_path / "page.html").as_uri(),
                        "--storyboard", str(tmp_path / "sb.mjs"), "--name", "t", "--out", str(tmp_path / "raw"),
                        "--playwright-root", PW_ROOT, "--layout", "1280x720"], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    log = json.loads((tmp_path / "raw" / "t.camlog.json").read_text())
    shots = [e for e in log["log"] if e["kind"] == "shot"]
    assert [s["key"] for s in shots] == ["wide", "card"] and not any(s.get("missing") for s in shots)
    assert log["layout"] == "1280x720"
    # wide shot: the page background reaches the bottom-right corner (no grey pad from a small viewport)
    wide_t = shots[0]["t"] + 0.8
    corner, top_right, _ = frame_pixels(tmp_path / "raw" / "t.webm", wide_t, tmp_path)
    for px in (corner, top_right):
        assert px[0] > 180 and px[1] < 80 and px[2] < 80, f"frame edge is not the page background: {px}"
    # focus shot: the camera zoomed in (k > 1) and the frame centre is the white card, not red background
    cam = shots[1]["camera"]
    assert cam and cam["k"] > 1.5, cam
    _, _, centre = frame_pixels(tmp_path / "raw" / "t.webm", shots[1]["t"] + 1.6, tmp_path)
    assert min(centre) > 200, f"centre of the focus shot is not the card: {centre}"
