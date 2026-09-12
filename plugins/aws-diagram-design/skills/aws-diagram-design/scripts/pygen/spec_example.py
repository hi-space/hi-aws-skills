"""Example spec: a training pipeline on AWS, one layout rendered in Korean and English.

    python3 build.py . --out /tmp/diag && python3 export.py /tmp/diag

Shows the house style: AWS Cloud zone with badge, icon-left nodes (16px name + 12px mono sublabel),
one focal node, orthogonal r=8 connectors, masked arrow labels 8px above the line, bottom legend.
"""
from awsdiag import Canvas, T


def build(lang):
    t = lambda ko, en: T(lang, ko, en)
    c = Canvas(960, 464, "training-pipeline",
               t("모델 학습 파이프라인", "Model training pipeline"),
               t("사용자가 S3에 데이터를 올리면 SageMaker 학습 잡이 ECR 이미지로 실행되고 체크포인트가 S3로 돌아가는 흐름",
                 "A user uploads data to S3, a SageMaker training job runs from an ECR image, and checkpoints return to S3"),
               lang)
    # zone: AWS Cloud container (official badge + border colour)
    c.zone(240, 56, 680, 320, "AWS Cloud", kind="cloud")
    # arrows first (painted behind nodes)
    c.path(c.hline(224, 168, 292)); c.label(258, 156, "UPLOAD")
    c.path(c.elbow_hvh(532, 168, 620, 168)); c.label(576, 156, "READ")
    c.path(c.vline(700, 200, 288)); c.label(716, 252, "PULL", anchor="start")
    c.path(c.hline(620, 192, 532), dashed=True); c.label(576, 212, "CKPT")
    # nodes
    c.node(40, 136, 184, 64, t("데이터 엔지니어", "Data engineer"), "robot dataset", icon="User", kind="input")
    c.node(292, 136, 240, 64, "Amazon S3", "raw/ · checkpoints/", icon="S3", kind="store")
    c.node(620, 136, 264, 64, "SageMaker Training", t("ml.g5.12xlarge · 1 노드", "ml.g5.12xlarge · 1 node"), icon="SageMaker", kind="focal")
    c.node(620, 288, 264, 64, "Amazon ECR", t("학습 컨테이너 이미지", "training container image"), icon="ECR")
    c.legend([("focal", t("핵심 단계", "Focal step")), ("store", t("스토리지", "Storage")), ("input", t("사용자", "User")),
              ("arrow", t("데이터 흐름", "Data flow")), ("arrow-dashed", t("체크포인트 반환", "Checkpoint return"))])
    return [("training-pipeline", c)]
