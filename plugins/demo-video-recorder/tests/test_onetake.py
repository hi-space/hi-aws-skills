"""onetake.py: contiguous speed-ramped segments, caption timing, lint, and a synthetic encode (needs ffmpeg)."""
import importlib.util
import json
import shutil
import subprocess
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "skills" / "recording-demo-videos" / "scripts"
spec_ = importlib.util.spec_from_file_location("onetake", SCRIPTS / "onetake.py")
ot = importlib.util.module_from_spec(spec_); spec_.loader.exec_module(ot)

EVENTS = {"home": 1.0, "a_typing": 3.0, "a_typed": 5.0, "a_working": 6.0, "a_result": 14.0, "pop_closed": 17.0, "end": 19.0}
SPEC = {"start": "home", "end": "end", "turns": ["a"], "speeds": {"wait": 4, "type": 2},
        "captions": [{"from": "home", "to": "a_typing", "chip": "01 시작", "title": "매장에서 상담을 시작합니다"},
                     {"from": "a_typing", "to": "a_result", "chip": "02 질문", "title": "원하는 옷을 말로 찾습니다", "how": "에이전트가 검색 도구를 호출합니다"},
                     {"from": "a_result", "to": "end", "title": "추천 상품을 확인합니다"}]}


def test_segments_are_contiguous_and_only_speed_differs():
    segs = ot.build_segments(EVENTS, 1.0, SPEC)
    assert segs[0]["m0"] == 1.0 and segs[-1]["m1"] == 19.0
    for a, b in zip(segs, segs[1:]):
        assert a["m1"] == pytest.approx(b["m0"]) and a["o1"] == pytest.approx(b["o0"])
    speeds = [(round(s["m0"], 2), round(s["m1"], 2), s["speed"], s["badge"]) for s in segs]
    assert speeds == [(1.0, 3.0, 1.0, False), (3.0, 5.0, 2.0, False), (5.0, 6.0, 1.0, False),
                      (6.0, 14.0, 4.0, True), (14.0, 19.0, 1.0, False)]
    # 2 + 1 + 1 + 2 + 5 seconds of output
    assert segs[-1]["o1"] == pytest.approx(11.0)


def test_media_clock_factor_scales_every_anchor():
    segs = ot.build_segments(EVENTS, 1.05, SPEC)
    assert segs[0]["m0"] == pytest.approx(1.05) and segs[-1]["m1"] == pytest.approx(19.95)


def test_to_out_maps_through_fast_segments_and_clamps():
    segs = ot.build_segments(EVENTS, 1.0, SPEC)
    assert ot.to_out(segs, 10.0) == pytest.approx(4.0 + 1.0)   # 2+1+1 before the wait, 4 s into it at x4
    assert ot.to_out(segs, 0.0) == 0.0 and ot.to_out(segs, 99) == pytest.approx(11.0)


def test_insert_replaces_the_take_before_its_anchor():
    spec = {**SPEC, "inserts": [{"file": "raw/pop.webm", "until": "pop_closed", "offset": 0, "max": 2}]}
    segs = ot.build_segments(EVENTS, 1.0, spec, {"raw/pop.webm": 5.0})
    pop = [s for s in segs if s["src"]]
    assert len(pop) == 1 and pop[0]["m0"] == pytest.approx(15.0) and pop[0]["m1"] == pytest.approx(17.0)
    assert segs[-1]["m1"] == 19.0


def test_missing_turn_typing_notes_are_optional_but_wait_notes_are_not():
    ev = {k: v for k, v in EVENTS.items() if not k.startswith("a_typ")}
    assert len(ot.build_segments(ev, 1.0, SPEC)) == 3
    with pytest.raises(KeyError):
        ot.build_segments({k: v for k, v in EVENTS.items() if k != "a_result"}, 1.0, SPEC)


def test_lint_catches_rules_and_missing_anchors():
    bad = {**SPEC, "captions": [
        {"from": "home", "to": "nope", "title": "가" * 46},
        {"from": "home", "to": "end", "title": "검색 · 추천", "how": "4배속으로 보여 줍니다"},
    ]}
    errs = "\n".join(ot.lint(bad, EVENTS))
    assert "no camlog event 'nope'" in errs and "46 chars" in errs
    assert "middle dot" in errs and "speed wording" in errs
    assert ot.lint(SPEC, EVENTS) == []


def test_caption_windows_follow_output_time():
    segs = ot.build_segments(EVENTS, 1.0, SPEC)
    wins = ot.caption_windows(SPEC, EVENTS, 1.0, segs)
    assert wins[1]["o0"] == pytest.approx(2.15) and wins[1]["o1"] == pytest.approx(6.0 - 0.1)


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="needs ffmpeg")
def test_edit_and_assemble_encode_a_synthetic_take(tmp_path):
    raw = tmp_path / "raw"; raw.mkdir()
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "testsrc=size=1920x1080:rate=30:duration=20",
                    "-c:v", "libvpx", "-b:v", "1M", str(raw / "take.webm")], check=True)
    log = [{"t": t, "kind": k} for k, t in EVENTS.items()]
    (raw / "take.camlog.json").write_text(json.dumps({"ok": True, "duration_s": 20.0, "log": log}))
    (tmp_path / "onetake.json").write_text(json.dumps({**SPEC, "take": "raw/take.webm", "out": "clips/take.mp4"}, ensure_ascii=False))
    assert ot.main(["check", str(tmp_path / "onetake.json")]) == 0
    assert ot.main(["edit", str(tmp_path / "onetake.json")]) == 0
    take = tmp_path / "clips" / "take.mp4"
    assert ot.duration(take) == pytest.approx(11.0, abs=0.15)
    assert (take.with_suffix(".srt")).read_text().count("-->") == 3
    from PIL import Image
    Image.new("RGB", (1920, 1080), "#f4efe7").save(tmp_path / "card.png")
    (tmp_path / "final.json").write_text(json.dumps({"pre": [{"png": "card.png", "seconds": 2, "title": "소개"}], "take": "clips/take.mp4",
                                                     "post": [{"png": "card.png", "seconds": 2}], "out": "demo.mp4", "fade_color": "#f4efe7"}))
    assert ot.main(["assemble", str(tmp_path / "final.json")]) == 0
    assert ot.duration(tmp_path / "demo.mp4") == pytest.approx(15.0, abs=0.2)
    srt = (tmp_path / "demo.ko.srt").read_text()
    assert srt.startswith("1\n00:00:00,300") and "00:00:02," in srt.split("\n\n")[1]  # take captions shifted by the 2 s card
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(tmp_path / "demo.mp4"), "-f", "null", "-"], capture_output=True, text=True)
    assert r.stderr == ""


# ---------------------------------------------------------------- end-to-end smoke with the example storyboard
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

CHAT_PAGE = """<!doctype html><html lang="ko"><head><meta charset="utf-8"><style>
body{margin:0;font:20px sans-serif;background:#f4efe7}
[aria-label=Assistant]{position:fixed;right:20px;top:20px;bottom:20px;width:560px;background:#fff;display:flex;flex-direction:column}
.overflow-y-auto{overflow-y:auto;flex:1}article{border:1px solid #ccc;margin:8px;height:160px}
</style></head><body><h1>Store</h1>
<div aria-label="Assistant"><div class="overflow-y-auto"><ol></ol></div>
<input id="chat-input"><button id="send">보내기</button><button id="stop" hidden>응답 멈추기</button></div>
<script>
const ol=document.querySelector('ol');
document.getElementById('send').onclick=async()=>{
  const q=document.getElementById('chat-input').value;ol.insertAdjacentHTML('beforeend','<li>'+q+'</li>');
  const stop=document.getElementById('stop');stop.hidden=false;
  const r=await fetch('/v1/invocations',{method:'POST',body:JSON.stringify({message:q,session_id:'s_0123456789abcdef'})});
  const t=await r.text();stop.hidden=true;
  ol.insertAdjacentHTML('beforeend','<li>추천입니다<article>card A</article><article>card B</article></li>');
};
</script></body></html>"""


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8"); self.end_headers()
        self.wfile.write(CHAT_PAGE.encode())
    def do_POST(self):
        self.rfile.read(int(self.headers.get("Content-Length", 0)))
        import time; time.sleep(2.0)
        body = ('data: {"type":"textDelta","data":{"text":"추천"}}\n'
                'data: {"type":"toolUse","data":{"name":"search_products"}}\n'
                'data: {"type":"messageStop","data":{"stopReason":"end_turn"}}\n')
        self.send_response(200); self.send_header("Content-Type", "text/event-stream"); self.end_headers()
        self.wfile.write(body.encode())


@pytest.mark.skipif(not (os.environ.get("PLAYWRIGHT_ROOT") and shutil.which("ffmpeg")), reason="needs PLAYWRIGHT_ROOT and ffmpeg")
def test_example_storyboard_records_and_edits_one_take(tmp_path):
    srv = ThreadingHTTPServer(("127.0.0.1", 0), _Handler); threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        sb = (SCRIPTS / "storyboard.onetake.example.mjs").read_text()
        (tmp_path / "storyboard.mjs").write_text(sb)
        (tmp_path / ".login.json").write_text('{"username":"u","password":"p"}')
        (tmp_path / "qa").mkdir()
        r = subprocess.run(["node", str(SCRIPTS / "record_demo.mjs"), "--url", f"http://127.0.0.1:{srv.server_port}/", "--storyboard",
                            str(tmp_path / "storyboard.mjs"), "--name", "take", "--out", str(tmp_path / "raw"), "--camera", "zoom",
                            "--playwright-root", os.environ["PLAYWRIGHT_ROOT"], "--max-seconds", "120"], capture_output=True, text=True, timeout=240)
        assert r.returncode == 0, r.stdout + r.stderr
    finally:
        srv.shutdown()
    camlog = json.loads((tmp_path / "raw" / "take.camlog.json").read_text())
    assert camlog["ok"] and camlog["camera"] == "zoom"
    turns = json.loads((tmp_path / "qa" / "turns.json").read_text())
    assert [t["http"] for t in turns] == [200, 200] and turns[0]["tools"] == ["search_products"]
    spec = {"take": "raw/take.webm", "out": "clips/take.mp4", "start": "home", "end": "end", "turns": ["first", "followup"],
            "captions": [{"from": "home", "to": "first_typing", "chip": "01 시작", "title": "매장에서 상담을 시작합니다"},
                         {"from": "first_typing", "to": "first_result", "chip": "02 질문", "title": "원하는 옷을 말로 찾습니다", "how": "에이전트가 검색 도구를 호출합니다"}]}
    (tmp_path / "onetake.json").write_text(json.dumps(spec, ensure_ascii=False))
    assert ot.main(["edit", str(tmp_path / "onetake.json")]) == 0
    assert ot.duration(tmp_path / "clips" / "take.mp4") > 10
