"""Example illustrated figures. Copy the pattern, not the content: one idea per figure, objects first, few words."""
from awsdiag import INK
from _pict import *


def policy_loop():
    a, _ = put_arm(130, 300, **GRASP)
    p = [panel(24, 24, 420, 330),
         table(60, 300, 350), shelf(320, 228, 76, 72), a, cup(186, 300),
         motion("M 200,268 Q 270,170 352,214"),
         camera(74, 96, 38), motion("M 96,113 L 150,230 M 96,113 L 300,180", SOFT, head=False),
         txt(74, 68, "카메라", 13), bubble(214, 44, 176, 34, "컵을 선반에 올려 줘"), txt(302, 108, "언어 지시", 13),
         txt(130, 338, "로봇", 13),
         model_box(660, 150, 276, 100, "정책(policy)", ["관측에서 다음", "액션을 계산"]),
         arrow(452, 178, 652, 178), title(552, 112, "관측", ["카메라 영상, 로봇 상태,", "언어 지시"]),
         arrow(652, 222, 452, 222), title(552, 250, "액션", ["각 관절을 움직일 값"]),
         ]
    return canvas("example-policy-loop", "정책이 로봇을 움직이는 과정",
                  "카메라와 로봇 팔, 컵, 선반이 있는 장면에서 관측이 정책으로 들어가고 정책이 낸 액션이 로봇으로 돌아가는 과정", 374, p)


def two_panels():
    a1, _ = put_arm(170, 228, **CARRY)
    p = [panel(20, 20, 450, 290), panel(490, 20, 450, 290),
         title(40, 52, "Imitation learning", ["사람의 시연을 따라 하도록 학습"], "start"),
         ground(40, 250, 228), person(78, 228), a1, motion("M 116,200 Q 140,214 160,204", head=False),
         txt(145, 256, "사람이 로봇을 조종", 14),
         arrow(256, 168, 282, 168),
         frame(302, 130, cupx=0.7, lifted=True), frame(295, 138, cupx=0.55, lifted=True), frame(288, 146, cupx=0.4),
         txt(326, 216, "시연", 14, 600, INK), txt(326, 235, "관측과 액션의 기록", 13),
         arrow(366, 168, 392, 168), nn(398, 144), txt(428, 216, "정책", 14, 600, INK),

         title(510, 52, "데이터 파이프라인", ["문서를 저장소에 넣고 서버가 처리"], "start"),
         doc(540, 150), doc(552, 160), arrow(610, 190, 660, 190), db(672, 158), arrow(740, 190, 790, 190), server(802, 144),
         txt(570, 250, "원본 문서", 14), txt(700, 250, "저장소", 14), txt(839, 262, "처리 서버", 14),
         ]
    return canvas("example-two-panels", "두 칸으로 나란히 비교하는 그림",
                  "왼쪽은 사람이 로봇을 조종해 시연을 남기는 장면, 오른쪽은 문서와 저장소와 서버 픽토그램을 늘어놓은 예시", 330, p)


def build(lang):
    return [(c.slug, c) for c in (policy_loop(), two_panels())]
