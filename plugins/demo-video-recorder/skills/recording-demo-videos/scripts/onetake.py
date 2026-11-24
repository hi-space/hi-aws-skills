#!/usr/bin/env python3
"""One-take demo editor: one uninterrupted take, speed-ramped waits, three-line captions, cards only outside.

  python3 onetake.py check    onetake.json                 # anchors exist, caption rules, overlaps (no encode)
  python3 onetake.py edit     onetake.json                 # -> spec["out"] (take with captions) + .srt
  python3 onetake.py assemble final.json                   # cards before/after the take -> final mp4 + .srt
  python3 onetake.py scan     video.mp4                    # near-white / near-black runs (navigation flashes)
  python3 onetake.py sheet    video.mp4 --every 10         # contact sheet PNG next to the video

The take is cut into contiguous segments that differ only in playback speed and are joined without fades, so
the viewer sees one continuous session (references/onetake.md). Times in the spec are camlog event keys from
record_demo.mjs (`rec.note(kind)` or a shot key); they are mapped to media time with K = media / camlog
duration, because Playwright's video clock runs a few percent longer than the wall clock.

onetake.json:
  {"take": "raw/take.webm", "out": "clips/take.mp4",
   "start": "home", "end": "end", "end_offset": -0.3,
   "turns": ["coat", "budget"],              # <k>_typing→<k>_typed at speeds.type, <k>_working→<k>_result at speeds.wait (+badge)
   "speeds": {"wait": 4, "type": 1.6},
   "ramps": [{"from": "cognito", "to": "signed_in", "speed": 2.5}],          # extra ramps; "badge": true to show it
   "inserts": [{"file": "raw/popup.webm", "until": "popup_closed", "offset": -0.3, "max": 9}],  # replaces the take's last seconds before `until`
   "captions": [{"from": "home", "to": "hero_typing", "chip": "01 매장 진입", "title": "…", "how": "…"}],
   "badge": "응답 대기 구간  ×{speed} 빨리 감기",
   "style": {"box": "#1c2321", "accent": "#a8432f", "text": "#f4efe7", "soft": "#cdd2ce"}}
final.json:
  {"pre": [{"png": "cards/intro.png", "seconds": 6.5, "title": "srt text"}], "take": "clips/take.mp4",
   "post": [{"png": "cards/summary.png", "seconds": 10, "title": "…"}], "out": "demo.mp4", "fade_color": "#f4efe7"}
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

W, H, FPS = 1920, 1080, 30
TITLE_MAX, HOW_MAX = 45, 70
BANNED = {'·': 'middle dot', '→': 'arrow', '—': 'em dash'}
DEFAULT_STYLE = {'box': '#1c2321', 'accent': '#a8432f', 'text': '#f4efe7', 'soft': '#cdd2ce', 'badge_bg': '#fffdf9'}


# ---------------------------------------------------------------- timeline (pure, unit-tested)
def event_times(camlog: dict) -> dict[str, float]:
    """First time of every note kind and shot key (shot keys win nothing: both forms are just names)."""
    out: dict[str, float] = {}
    for e in camlog['log']:
        key = e.get('key') if e.get('kind') == 'shot' else e.get('kind')
        if key is not None:
            out.setdefault(key, float(e['t']))
    return out


def ramp_list(spec: dict) -> list[dict]:
    speeds = {'wait': 4.0, 'type': 1.6, **spec.get('speeds', {})}
    ramps = []
    for k in spec.get('turns', []):
        ramps.append({'from': f'{k}_typing', 'to': f'{k}_typed', 'speed': speeds['type'], 'optional': True})
        ramps.append({'from': f'{k}_working', 'to': f'{k}_result', 'speed': speeds['wait'], 'badge': True})
    return ramps + list(spec.get('ramps', []))


def build_segments(events: dict, k: float, spec: dict, insert_lengths: dict | None = None) -> list[dict]:
    """Contiguous [m0, m1) media segments covering start..end. Each has speed, badge and source file."""
    t = lambda key, off=0.0: (events[key] + off) * k
    start, end = t(spec.get('start', 'home'), spec.get('start_offset', 0.0)), t(spec.get('end', 'end'), spec.get('end_offset', 0.0))
    cuts = []
    for r in ramp_list(spec):
        if r['from'] not in events or r['to'] not in events:
            if r.get('optional'):
                continue
            raise KeyError(f"ramp anchor missing: {r['from']} → {r['to']}")
        a, b = t(r['from'], r.get('from_offset', 0.0)), t(r['to'], r.get('to_offset', 0.0))
        if b > a:
            cuts.append({'m0': a, 'm1': b, 'speed': float(r['speed']), 'badge': bool(r.get('badge')), 'src': None})
    for ins in spec.get('inserts', []):
        length = (insert_lengths or {}).get(ins['file'])
        if not length:
            continue
        b = t(ins['until'], ins.get('offset', -0.3))
        a = b - min(length - 0.4, float(ins.get('max', 9.0)))
        cuts.append({'m0': a, 'm1': b, 'speed': 1.0, 'badge': False, 'src': ins['file'], 'src_len': length})
    cuts.sort(key=lambda c: c['m0'])
    segs, cur = [], start
    for c in cuts:
        a, b = max(c['m0'], cur, start), min(c['m1'], end)
        if b <= a:
            continue  # overlapped by an earlier cut or outside the take
        if a > cur:
            segs.append({'m0': cur, 'm1': a, 'speed': 1.0, 'badge': False, 'src': None})
        segs.append({**c, 'm0': a, 'm1': b}); cur = b
    if end > cur:
        segs.append({'m0': cur, 'm1': end, 'speed': 1.0, 'badge': False, 'src': None})
    segs = [s for s in segs if s['m1'] - s['m0'] > 0.05]
    acc = 0.0
    for s in segs:
        s['o0'] = acc; acc += (s['m1'] - s['m0']) / s['speed']; s['o1'] = acc
    return segs


def to_out(segs: list[dict], m: float) -> float:
    """Output-time of media time m (clamped to the take)."""
    if m <= segs[0]['m0']:
        return 0.0
    for s in segs:
        if s['m0'] <= m <= s['m1']:
            return s['o0'] + (m - s['m0']) / s['speed']
    return segs[-1]['o1']


def caption_windows(spec: dict, events: dict, k: float, segs: list[dict]) -> list[dict]:
    out = []
    for c in spec.get('captions', []):
        a = to_out(segs, (events[c['from']] + c.get('from_offset', 0.0)) * k) + 0.15
        b = to_out(segs, (events[c['to']] + c.get('to_offset', 0.0)) * k) - 0.1
        out.append({**c, 'o0': a, 'o1': b})
    return out


def lint(spec: dict, events: dict) -> list[str]:
    """Problems that should stop an encode: missing anchors, caption rules, overlapping captions."""
    errs = []
    for r in ramp_list(spec):
        if not r.get('optional'):
            for side in ('from', 'to'):
                if r[side] not in events:
                    errs.append(f"ramp {r['from']}→{r['to']}: no camlog event '{r[side]}'")
    for key in (spec.get('start', 'home'), spec.get('end', 'end')):
        if key not in events:
            errs.append(f"start/end: no camlog event '{key}'")
    for ins in spec.get('inserts', []):
        if ins['until'] not in events:
            errs.append(f"insert {ins['file']}: no camlog event '{ins['until']}'")
    prev = None
    for i, c in enumerate(spec.get('captions', [])):
        tag = f"caption {i} ({c.get('chip', '')})"
        for side in ('from', 'to'):
            if c.get(side) not in events:
                errs.append(f"{tag}: no camlog event '{c.get(side)}'")
        if len(c.get('title', '')) > TITLE_MAX:
            errs.append(f"{tag}: title {len(c['title'])} chars > {TITLE_MAX}")
        if len(c.get('how', '')) > HOW_MAX:
            errs.append(f"{tag}: how {len(c['how'])} chars > {HOW_MAX}")
        for ch, name in BANNED.items():
            for field in ('chip', 'title', 'how'):
                if ch in c.get(field, ''):
                    errs.append(f"{tag}: {name} in {field}; join with a comma or 와/과")
        if '배속' in c.get('title', '') + c.get('how', ''):
            errs.append(f"{tag}: speed wording belongs to the badge, not the caption")
        if prev is not None and c.get('from') in events and prev.get('to') in events and events[c['from']] < events[prev['to']]:
            errs.append(f"{tag}: starts before the previous caption ends ({prev['to']})")
        prev = c
    return errs


# ---------------------------------------------------------------- overlays
def _font(env: str, names: list[str], pattern: str) -> str:
    if os.environ.get(env):
        return os.environ[env]
    for n in names:
        if Path(n).exists():
            return n
    out = subprocess.run(['fc-match', '-f', '%{file}', pattern], capture_output=True, text=True)
    return out.stdout.strip()


FONT_B = _font('DEMO_FONT_BOLD', ['/usr/share/fonts/truetype/nanum/NanumSquareB.ttf', '/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf'], 'NanumGothic:bold')
FONT_R = _font('DEMO_FONT_REGULAR', ['/usr/share/fonts/truetype/nanum/NanumSquareR.ttf', '/usr/share/fonts/truetype/nanum/NanumGothic.ttf'], 'NanumGothic')


def _rgb(h: str, a: int = 255):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (a,)


def _wrap(draw, text, font, width):
    lines, line = [], ''
    for word in text.split(' '):
        trial = (line + ' ' + word).strip()
        if not line or draw.textlength(trial, font=font) <= width:
            line = trial
        else:
            lines.append(line); line = word
    return lines + ([line] if line else [])


def caption_png(path: Path, chip: str, title: str, how: str, style: dict, x=56, maxw=1080, bottom=H - 44):
    """Lower-left box: accent chip, bold title, soft 'how it works' line. Kept left so a right-side panel stays visible."""
    from PIL import Image, ImageDraw, ImageFont
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    fc, ft, fh = ImageFont.truetype(FONT_B, 22), ImageFont.truetype(FONT_B, 36), ImageFont.truetype(FONT_R, 25)
    pad = 28
    tl = _wrap(d, title, ft, maxw - 2 * pad); hl = _wrap(d, how, fh, maxw - 2 * pad) if how else []
    h = pad + (48 if chip else 0) + len(tl) * 50 + (12 + len(hl) * 38 if hl else 0) + pad - 6
    w = min(maxw, int(max([d.textlength(chip, font=fc) + 40 if chip else 0] + [d.textlength(l, font=ft) for l in tl] + [d.textlength(l, font=fh) for l in hl]) + 2 * pad))
    y0 = bottom - h
    d.rounded_rectangle([x, y0, x + w, bottom], 16, fill=_rgb(style['box'], 236))
    d.rectangle([x, y0 + 16, x + 6, bottom - 16], fill=_rgb(style['accent']))
    y = y0 + pad
    if chip:
        cw = d.textlength(chip, font=fc) + 28
        d.rounded_rectangle([x + pad, y, x + pad + cw, y + 34], 17, fill=_rgb(style['accent']))
        d.text((x + pad + 14, y + 6), chip, font=fc, fill=_rgb(style['text'])); y += 48
    for l in tl:
        d.text((x + pad, y), l, font=ft, fill=_rgb(style['text'])); y += 50
    if hl:
        y += 12
        for l in hl:
            d.text((x + pad, y), l, font=fh, fill=_rgb(style['soft'])); y += 38
    img.save(path)


def badge_png(path: Path, text: str, style: dict, x=56, y=100):
    from PIL import Image, ImageDraw, ImageFont
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    f = ImageFont.truetype(FONT_B, 22); w = d.textlength(text, font=f) + 36
    d.rounded_rectangle([x, y, x + w, y + 40], 20, fill=_rgb(style['badge_bg'], 235), outline=_rgb(style['accent']), width=2)
    d.text((x + 18, y + 9), text, font=f, fill=_rgb(style['accent']))
    img.save(path)


# ---------------------------------------------------------------- ffmpeg helpers
def duration(p) -> float:
    return float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(p)], text=True))


def srt_time(x: float) -> str:
    h, r = divmod(max(x, 0.0), 3600); m, s = divmod(r, 60)
    return f'{int(h):02d}:{int(m):02d}:{s:06.3f}'.replace('.', ',')


def write_srt(path: Path, rows):
    path.write_text(''.join(f'{i}\n{srt_time(a)} --> {srt_time(b)}\n{t}\n\n' for i, (a, b, t) in enumerate(rows, 1)))


ENC = ['-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', '-r', str(FPS)]


def render_segment(seg, take: Path, base: Path, overlays, out: Path):
    o0, o1 = seg['o0'], seg['o1']; length = seg['m1'] - seg['m0']
    if seg['src']:
        inp = ['-ss', f"{max(0.0, seg['src_len'] - 0.4 - length):.3f}", '-t', f'{length:.3f}', '-i', str(base / seg['src'])]
    else:
        inp = ['-ss', f"{seg['m0']:.3f}", '-t', f'{length:.3f}', '-i', str(take)]
    act = [o for o in overlays if o[0] < o1 and o[1] > o0]
    cmd = ['ffmpeg', '-y', '-v', 'error', *inp]
    fil = [f"[0:v]setpts=(PTS-STARTPTS)/{seg['speed']},fps={FPS},scale={W}:{H},format=yuv420p[v0]"]
    for i, (a, b, png) in enumerate(act):
        cmd += ['-loop', '1', '-t', f'{o1 - o0 + 0.1:.3f}', '-i', str(png)]
        la, lb = a - o0, b - o0
        fades = []
        if la > -0.01: fades.append(f'fade=in:st={max(la, 0):.3f}:d=0.3:alpha=1')       # true start of the caption
        if lb < o1 - o0 + 0.01: fades.append(f'fade=out:st={max(lb - 0.3, 0):.3f}:d=0.3:alpha=1')  # true end
        fil.append(f"[{i + 1}:v]format=rgba{',' if fades else ''}{','.join(fades)}[c{i}]")
        fil.append(f"[v{i}][c{i}]overlay=0:0:enable='between(t,{max(la, 0):.3f},{lb:.3f})'[v{i + 1}]")
    cmd += ['-filter_complex', ';'.join(fil), '-map', f'[v{len(act)}]', '-t', f'{o1 - o0:.3f}', *ENC, '-an', str(out)]
    subprocess.run(cmd, check=True)


def concat(parts, out: Path, audio=True):
    with tempfile.NamedTemporaryFile('w', suffix='.txt', delete=False) as f:
        f.write(''.join(f"file '{Path(p).resolve()}'\n" for p in parts)); lst = f.name
    cmd = ['ffmpeg', '-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', lst]
    if audio:
        cmd += ['-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=stereo', '-shortest', '-map', '0:v', '-map', '1:a', '-c:a', 'aac', '-b:a', '96k']
    cmd += ['-c:v', 'copy', '-movflags', '+faststart', str(out)]
    try:
        subprocess.run(cmd, check=True)
    finally:
        os.unlink(lst)


# ---------------------------------------------------------------- commands
def load(spec_path: Path):
    spec = json.loads(spec_path.read_text()); base = spec_path.parent
    take = base / spec['take']
    camlog = json.loads(take.with_suffix('.camlog.json').read_text())
    return spec, base, take, camlog


def cmd_check(spec_path: Path) -> int:
    spec, base, take, camlog = load(spec_path)
    errs = lint(spec, event_times(camlog))
    if not camlog.get('ok', False):
        errs.append('camlog ok=false: the take did not finish; re-record or edit only what it covers')
    for e in errs:
        print('✗', e)
    print('ok' if not errs else f'{len(errs)} problem(s)')
    return 1 if errs else 0


def cmd_edit(spec_path: Path) -> int:
    spec, base, take, camlog = load(spec_path)
    events = event_times(camlog)
    errs = lint(spec, events)
    if errs:
        for e in errs: print('✗', e)
        return 1
    k = duration(take) / camlog['duration_s']
    lengths = {i['file']: duration(base / i['file']) for i in spec.get('inserts', []) if (base / i['file']).exists()}
    segs = build_segments(events, k, spec, lengths)
    style = {**DEFAULT_STYLE, **spec.get('style', {})}
    out = base / spec.get('out', 'clips/take.mp4'); out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='onetake-') as tmp:
        tmp = Path(tmp); overlays, rows = [], []
        for i, c in enumerate(caption_windows(spec, events, k, segs)):
            png = tmp / f'cap{i:03d}.png'; caption_png(png, c.get('chip', ''), c['title'], c.get('how', ''), style)
            overlays.append((c['o0'], c['o1'], png))
            rows.append((c['o0'], c['o1'], (f"[{c['chip']}] " if c.get('chip') else '') + c['title'] + (f"\n{c['how']}" if c.get('how') else '')))
        badge = spec.get('badge', '▶▶  응답 대기 구간  ×{speed} 빨리 감기')
        for j, s in enumerate(segs):
            if s['badge']:
                png = tmp / f'badge{j:03d}.png'; badge_png(png, badge.format(speed=f"{s['speed']:g}"), style)
                overlays.append((s['o0'], s['o1'], png))
        parts = []
        for j, s in enumerate(segs):
            p = tmp / f'seg{j:03d}.mp4'; render_segment(s, take, base, overlays, p); parts.append(p)
            print(f"seg {j:03d} {s['src'] or 'take'} {s['m0']:7.2f}-{s['m1']:7.2f} x{s['speed']:g} -> {s['o0']:7.2f}", flush=True)
        concat(parts, out, audio=False)
    write_srt(out.with_suffix('.srt'), rows)
    (out.with_suffix('.timeline.json')).write_text(json.dumps({'K': k, 'segments': segs, 'captions': [r[:2] for r in rows]}, ensure_ascii=False, indent=1))
    print(f'{out} {segs[-1]["o1"]:.1f}s, {len(segs)} segments, {len(rows)} captions, K={k:.4f}')
    return 0


def cmd_assemble(spec_path: Path) -> int:
    spec = json.loads(spec_path.read_text()); base = spec_path.parent
    color = '0x' + spec.get('fade_color', '#000000').lstrip('#')
    take = base / spec['take']; out = base / spec['out']
    with tempfile.TemporaryDirectory(prefix='onetake-cards-') as tmp:
        def card(c, i):
            p = Path(tmp) / f'card{i}.mp4'; s = float(c['seconds'])
            subprocess.run(['ffmpeg', '-y', '-v', 'error', '-loop', '1', '-t', str(s), '-i', str(base / c['png']),
                            '-vf', f'scale={W}:{H},fps={FPS},format=yuv420p,fade=in:st=0:d=0.5:color={color},fade=out:st={s - 0.5}:d=0.5:color={color}',
                            *ENC, str(p)], check=True)
            return p
        pre = [card(c, i) for i, c in enumerate(spec.get('pre', []))]
        post = [card(c, 100 + i) for i, c in enumerate(spec.get('post', []))]
        concat(pre + [take] + post, out)
    rows, t = [], 0.0
    for c in spec.get('pre', []):
        if c.get('title'): rows.append((t + 0.3, t + c['seconds'] - 0.3, c['title']))
        t += c['seconds']
    take_srt = take.with_suffix('.srt')
    if take_srt.exists():
        for block in take_srt.read_text().strip().split('\n\n'):
            lines = block.split('\n'); a, b = [_parse(x) for x in lines[1].split(' --> ')]
            rows.append((a + t, b + t, '\n'.join(lines[2:])))
    t += duration(take)
    for c in spec.get('post', []):
        if c.get('title'): rows.append((t + 0.3, t + c['seconds'] - 0.3, c['title']))
        t += c['seconds']
    write_srt(out.with_suffix('.ko.srt'), rows)
    print(f'{out} {duration(out):.1f}s')
    return 0


def _parse(s: str) -> float:
    h, m, rest = s.strip().split(':'); sec, ms = rest.split(',')
    return int(h) * 3600 + int(m) * 60 + int(sec) + int(ms) / 1000


def cmd_scan(video: Path, hi=225.0, lo=25.0) -> int:
    """Runs of near-white or near-black frames: a navigation flash or a blank tab the take should speed through."""
    out = subprocess.run(['ffmpeg', '-i', str(video), '-vf', 'fps=4,signalstats,metadata=mode=print:key=lavfi.signalstats.YAVG:file=-',
                          '-f', 'null', '-'], capture_output=True, text=True).stdout
    t, flagged, runs = None, [], []
    for line in out.splitlines():
        if 'pts_time:' in line:
            t = float(line.split('pts_time:')[1].split()[0])
        elif 'YAVG=' in line and t is not None:
            y = float(line.split('=')[1])
            if y > hi or y < lo: flagged.append(t)
    for x in flagged:
        if runs and x - runs[-1][1] <= 0.3: runs[-1][1] = x
        else: runs.append([x, x])
    for a, b in runs:
        print(f'blank-ish {a:7.2f}-{b + 0.25:7.2f}s')
    print(f'{len(runs)} run(s)')
    return 0


def cmd_sheet(video: Path, every: float) -> int:
    from PIL import Image, ImageDraw
    total = duration(video); times = [x * every for x in range(int(total // every) + 1) if x * every < total - 0.2]
    tw, th, cols = 480, 270, 4
    sheet = Image.new('RGB', (tw * cols, th * ((len(times) + cols - 1) // cols)), 'white')
    with tempfile.TemporaryDirectory() as tmp:
        for i, s in enumerate(times):
            p = Path(tmp) / f'{i}.png'
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{s:.2f}', '-i', str(video), '-frames:v', '1', '-vf', f'scale={tw}:{th}', str(p)], check=True)
            im = Image.open(p); sheet.paste(im, ((i % cols) * tw, (i // cols) * th))
            ImageDraw.Draw(sheet).text(((i % cols) * tw + 6, (i // cols) * th + 4), f'{s:.0f}s', fill='red')
    out = video.with_suffix('.sheet.png'); sheet.save(out); print(out)
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    for name in ('check', 'edit', 'assemble'):
        sub.add_parser(name).add_argument('spec', type=Path)
    sub.add_parser('scan').add_argument('video', type=Path)
    sh = sub.add_parser('sheet'); sh.add_argument('video', type=Path); sh.add_argument('--every', type=float, default=10.0)
    a = ap.parse_args(argv)
    if a.cmd == 'check': return cmd_check(a.spec)
    if a.cmd == 'edit': return cmd_edit(a.spec)
    if a.cmd == 'assemble': return cmd_assemble(a.spec)
    if a.cmd == 'scan': return cmd_scan(a.video)
    return cmd_sheet(a.video, a.every)


if __name__ == '__main__':
    sys.exit(main())
