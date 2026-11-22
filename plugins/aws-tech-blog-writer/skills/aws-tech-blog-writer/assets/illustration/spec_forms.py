"""Six forms for explanatory figures. Copy the form that matches what the content is, not the content.

rate-bands   layers that act at different rates          bands with pulse tracks
lanes        the same two ends, different things between  parallel lanes
timeline     what is kept as time passes                  time arrow with frames under it
boundaries   what a request must pass to reach something  nested enclosures
cycle        improvement that feeds the next run          ring with a hub that accumulates
bars         two quantities whose ratio is the point      bars drawn to one scale
"""
from awsdiag import INK, MUTED, PAPER, SOFT
from _pict import *


def rate_bands():
    X, W, H, TX = 24, 692, 92, 372
    ys = [64, 186, 308]
    rows = [(agent_icon, "판단 계층", "의도 해석, 결정, 검증", "결정 한 번에 수 초~수십 초", "rare"),
            (nn, "스킬 계층", "정책 모델, 인식 모듈", "약 5~200 Hz", "regular"),
            (gear_icon, "제어 계층", "관절 제어", "약 50 Hz~1 kHz", "dense")]
    p = [chip(190, 30, "사용자", 72), arrow(190, 42, 190, ys[0] - 2), txt(202, 56, "지시", 14, anchor="start")]
    for i, (y, (icon, name, sub, rate, kind)) in enumerate(zip(ys, rows)):
        p += [icon_box(X, y, W, H, icon, name, [sub], focal=(i == 0)),
              txt(TX, y + 28, rate, 14, anchor="start"), pulses(TX, y + 44, 320, kind)]
    p += [arrow(190, ys[0] + H, 190, ys[1] - 2), txt(202, ys[1] - 10, "스킬 호출", 14, anchor="start"),
          arrow(190, ys[1] + H, 190, ys[2] - 2), txt(202, ys[2] - 10, "제어 목표", 14, anchor="start"),
          f'<rect x="800" y="{ys[0]}" width="136" height="{ys[2]+H-ys[0]}" rx="10" fill="{PALE}" stroke="{INK}" stroke-width="1.4" stroke-dasharray="5,4"/>',
          camera(858, 196, 0), txt(868, 240, "이벤트 모니터", 15, 600, INK),
          arrow(800, ys[0] + 46, X + W + 4, ys[0] + 46), txt(759, ys[0] + 36, "중단", 14),
          arrow(800, ys[2] + 46, X + W + 4, ys[2] + 46), txt(759, ys[2] + 36, "보호 정지", 14)]
    return canvas("example-rate-bands", "계층마다 다른 동작 주기",
                  "세 계층이 위에서 아래로 놓이고 계층마다 동작 주기를 나타내는 눈금이 있다. 위 계층은 드문 긴 구간, 가운데는 중간 간격, 아래는 촘촘한 눈금이다", 424, p)


def lanes():
    ys = [80, 176, 272]
    L, R = 156, 800
    p = [f'<rect x="24" y="36" width="132" height="280" rx="10" fill="{TINT}" stroke="{ACCENT}" stroke-width="1.4"/>',
         agent_icon(48, 122, 1.4), txt(90, 220, "에이전트", 16, 600, INK),
         f'<rect x="804" y="36" width="132" height="280" rx="10" fill="{GRAY}" stroke="{INK}" stroke-width="1.4"/>',
         gear_icon(840, 138), txt(870, 220, "로봇", 16, 600, INK)]
    p += [txt(L + 20, y - 16, n, 16, 600, INK, "start") for y, n in zip(ys, ["계층형", "코드 작성", "직접 제어"])]
    p += [lane(ys[0], L, R, [(318, 422), (560, 632)]), chip(370, ys[0], "컵을 집어라", 104), nn(566, ys[0] - 25), txt(596, ys[0] + 42, "VLA", 13, 600, INK),
          lane(ys[1], L, R, [(470, 530)]), doc(478, ys[1] - 28), txt(500, ys[1] + 44, "프로그램", 13, 600, INK),
          lane(ys[2], L, R, [(450, 550)]), chip(500, ys[2], "동작 명령", 100)]
    return canvas("example-lanes", "양 끝은 같고 가운데만 다른 세 경로",
                  "왼쪽의 에이전트와 오른쪽의 로봇 사이에 세 줄의 경로가 있고, 경로마다 놓인 것이 다르다", 352, p)


def timeline_memory():
    old = [frame(60 + k * 74, 104, dashed=True, cupx=0.2 + 0.15 * k, fill=PALE) for k in range(4)]
    new = [frame(420 + k * 74, 104, cupx=0.4 + 0.15 * k, lifted=(k == 2)) for k in range(3)]
    p = [panel(24, 24, 912, 252), timeline(52, 652, 84, "작업 시작", "지금"),
         f'<line x1="392" y1="92" x2="392" y2="250" stroke="{SOFT}" stroke-width="1.2" stroke-dasharray="5,4"/>',
         *old, *new,
         arrow(190, 156, 190, 180), doc(168, 184), title(154, 208, "장기 기억", ["언어로 요약"], "end"),
         title(420, 180, "단기 기억", ["최근 관측 그대로"], "start"),
         arrow(220, 230, 682, 198, via=[(660, 230), (660, 198)]), arrow(636, 127, 682, 127),
         icon_box(690, 96, 230, 128, agent_icon, "에이전트", ["두 기억을", "함께 읽는다"], True)]
    return canvas("example-timeline", "시간 순서로 본 두 종류의 기억",
                  "시간 순서로 놓인 카메라 프레임 가운데 오래된 것은 요약 문서로 줄고 최근 것은 그대로 남아 에이전트로 들어간다", 300, p)


def boundaries():
    p = [boundary(300, 110, 610, 268, shield_icon, "실행 전 검사", "범위, 승인"),
         boundary(500, 180, 390, 178, gear_icon, "하드 리밋", "힘, 속도 제한", PAPER),
         block(720, 251, 100, 46, "로봇"),
         agent_icon(40, 249),
         arrow(104, 274, 140, 274), chip(190, 274, "스킬 요청", 96), arrow(240, 274, 286, 274), mark(300, 274, True),
         arrow(314, 274, 486, 274), mark(500, 274, True), arrow(514, 274, 712, 274),
         arrow(70, 304, 114, 340, via=[(70, 340)]), chip(176, 340, "범위 밖 요청", 120), arrow(238, 340, 286, 340), mark(300, 340, False),
         txt(320, 345, "거부", 14, 600, INK, "start"),
         f'<rect x="650" y="24" width="240" height="56" rx="10" fill="{PAPER}" stroke="{INK}" stroke-width="1.4"/>',
         camera(684, 52, 0), txt(718, 57, "이벤트 모니터", 16, 600, INK, "start"),
         arrow(770, 80, 770, 243, color=ACCENT), txt(782, 100, "보호 정지", 14, 600, INK, "start")]
    return canvas("example-boundaries", "요청이 지나야 하는 두 겹의 경계",
                  "로봇을 두 겹의 경계가 감싼다. 요청은 두 경계를 차례로 통과하고, 범위 밖 요청은 바깥 경계에서 거부된다. 이벤트 모니터는 경계를 거치지 않고 로봇을 정지시킨다", 402, p)


def cycle():
    R = (480, 228, 300, 132)
    p = [panel(24, 24, 912, 408),
         ring_arc(*R, 24, 64), ring_arc(*R, 116, 160), ring_arc(*R, 200, 244),
         doc(458, 68), txt(514, 100, "실행 기록", 14, 600, INK, "start"),
         agent_icon(750, 196), txt(780, 266, "실패 진단", 14, 600, INK),
         doc(458, 332), txt(480, 410, "코드 수정", 14, 600, INK),
         shield_icon(150, 196), txt(180, 266, "회귀 검사", 14, 600, INK),
         db(452, 192), txt(480, 274, "스킬 라이브러리", 14, 600, INK),
         arrow(216, 222, 442, 222, color=ACCENT), txt(329, 210, "통과한 수정", 14),
         arrow(480, 184, 480, 132, color=ACCENT), txt(492, 162, "다음 실행에서 사용", 14, anchor="start")]
    return canvas("example-cycle", "가운데에 결과가 쌓이는 순환",
                  "실행 기록, 실패 진단, 코드 수정, 회귀 검사가 고리 모양으로 이어지고, 검사를 통과한 수정이 가운데 라이브러리에 쌓여 다음 실행에 쓰인다", 456, p)


def bars():
    a, _ = put_arm(640, 196, **GRASP)
    PX = 32  # px per second, the same for both bars
    p = [panel(20, 20, 400, 262), panel(540, 20, 400, 262),
         title(40, 56, "클라우드: 느린 추론", (), "start"), server(60, 92), agent_icon(170, 113, 1.1),
         bar(40, 238, 7.5 * PX, "한 턴 7.5초"),
         title(560, 56, "로봇: 빠른 제어", (), "start"), table(584, 196, 200), a, cup(696, 196), nn(836, 120), txt(866, 190, "VLA", 13, 600, INK),
         bar(560, 238, 0.6 * PX, "정책 호출 0.6초"),
         arrow(428, 120, 532, 120), txt(480, 104, "스킬 요청", 14), arrow(532, 164, 428, 164), txt(480, 188, "결과", 14)]
    return canvas("example-bars", "길이가 비례하는 두 시간",
                  "왼쪽 클라우드의 에이전트 한 턴 7.5초와 오른쪽 로봇의 정책 호출 0.6초를 같은 축척의 막대로 그렸다", 302, p)


def build(lang):
    return [(c.slug, c) for c in (rate_bands(), lanes(), timeline_memory(), boundaries(), cycle(), bars())]
