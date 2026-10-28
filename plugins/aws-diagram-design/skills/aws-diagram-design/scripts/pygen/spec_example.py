"""Example spec: a training pipeline on AWS, one layout rendered in Korean and English.

    python3 build.py . --out /tmp/diag --png

Shows the house style and the compact layout recipe: widths come from min_node_w (not a generous
fixed box), neighbours sit 40 px apart or label-mask + 16 px when the connector carries a label,
rows 40 px apart, 56 px boxes with 24 px icons, AWS Cloud zone with badge, one focal node,
orthogonal r=8 connectors, arrow labels in the sublabel face one px smaller, no legend
(call c.legend([...]) only when the reader asks for a key; it needs ~56px more canvas height).
"""
from awsdiag import Canvas, T, min_node_w, text_w, LABEL_SIZE

H, ROW, PAD = 56, 40, 24                       # node height, row gap, zone side padding
up4 = lambda v: int(-(-v // 4) * 4)
gap = lambda label=None: 40 if not label else up4(text_w(label, LABEL_SIZE) + 24)   # mask clears both boxes by 8


def width(*texts):
    """Widest min_node_w over every (name, sub) pair, so one box fits both languages."""
    return up4(max(min_node_w(n, s, True, H) for n, s in texts))


def build(lang):
    t = lambda ko, en: T(lang, ko, en)
    # --- text budget: one name line + one short sublabel per node, sized for the longer language
    w_user = width(("데이터 엔지니어", "robot dataset"), ("Data engineer", "robot dataset"))
    w_s3 = width(("Amazon S3", "raw/ · checkpoints/"))
    w_sm = width(("SageMaker Training", "ml.g5.12xlarge · 1 노드"), ("SageMaker Training", "ml.g5.12xlarge · 1 node"))
    w_ecr = width(("Amazon ECR", "학습 컨테이너 이미지"), ("Amazon ECR", "training container image"))
    w_col3 = max(w_sm, w_ecr)
    # --- columns: user | zone( S3 | SageMaker / ECR )
    x_user = 40
    x_s3 = x_user + w_user + gap("UPLOAD")
    x_sm = x_s3 + w_s3 + gap("READ")
    zx, zw = x_s3 - PAD, (x_sm + w_col3 + PAD) - (x_s3 - PAD)
    y1 = 40 + 40                               # zone top 40 + badge row
    y2 = y1 + H + ROW
    zh = (y2 + H + PAD) - 40
    c = Canvas(up4(zx + zw + 40), up4(40 + zh + 40), "training-pipeline",
               t("모델 학습 파이프라인", "Model training pipeline"),
               t("사용자가 S3에 데이터를 올리면 SageMaker 학습 잡이 ECR 이미지로 실행되고 체크포인트가 S3로 돌아가는 흐름",
                 "A user uploads data to S3, a SageMaker training job runs from an ECR image, and checkpoints return to S3"),
               lang)
    c.zone(zx, 40, zw, zh, "AWS Cloud", kind="cloud")
    # arrows first (painted behind nodes); endpoints computed from node geometry, two per edge ≥12 px apart
    cy = y1 + H // 2
    c.path(c.hline(x_user + w_user, cy, x_s3)); c.label((x_user + w_user + x_s3) / 2, cy - 12, "UPLOAD")
    c.path(c.hline(x_s3 + w_s3, y1 + H // 3, x_sm)); c.label((x_s3 + w_s3 + x_sm) / 2, y1 + H // 3 - 12, "READ")
    c.path(c.hline(x_sm, y1 + 2 * H // 3, x_s3 + w_s3), dashed=True); c.label((x_s3 + w_s3 + x_sm) / 2, y1 + 2 * H // 3 + 22, "CKPT")
    sm_cx = x_sm + w_col3 // 2
    c.path(c.vline(sm_cx, y1 + H, y2)); c.label(sm_cx + 12, y1 + H + ROW // 2 + 5, "PULL", anchor="start")
    # nodes
    c.node(x_user, y1, w_user, H, t("데이터 엔지니어", "Data engineer"), "robot dataset", icon="User", kind="input")
    c.node(x_s3, y1, w_s3, H, "Amazon S3", "raw/ · checkpoints/", icon="S3", kind="store")
    c.node(x_sm, y1, w_col3, H, "SageMaker Training", t("ml.g5.12xlarge · 1 노드", "ml.g5.12xlarge · 1 node"), icon="SageMaker", kind="focal")
    c.node(x_sm, y2, w_col3, H, "Amazon ECR", t("학습 컨테이너 이미지", "training container image"), icon="ECR")
    return [("training-pipeline", c)]
