"""awsdiag — programmatic SVG generator for the aws-diagram-design skill (AWS brand skin).

Encodes the skill's mandatory rules in code so a spec only supplies layout and text:
white paper, squid-ink text, smile-orange accent on 1-2 focal nodes, Amazon Ember type at the
presentation ramp (16px names / 12px sublabels and arrow labels), official AWS Architecture Icons
(icon-left nodes, group badges on zones), rounded orthogonal connectors (r=8), masked arrow labels,
bottom legend strip, accessible <title>/<desc>. Korean text falls back to Noto Sans KR / NanumBarunGothic
because Amazon Ember has no Hangul glyphs.

Usage from a spec file (see spec_example.py):

    from awsdiag import Canvas, T
    def build(lang):
        t = lambda ko, en: T(lang, ko, en)
        c = Canvas(960, 560, "my-slug", t("제목", "Title"), t("한 문장 설명", "One-sentence description"), lang)
        c.node(40, 40, 240, 56, "Amazon S3", "raw/ · checkpoints/", icon="S3", kind="store")
        ...
        return [("my-slug", c)]

Asset paths resolve relative to this file: <skill>/assets/aws-icons, <skill>/assets/fonts/woff2,
<skill>/references/primitive-icons.md. Override with AWS_DIAGRAM_SKILL_DIR if the skill lives elsewhere.
"""
from __future__ import annotations
import html, os, pathlib, re, sys

SKILL = pathlib.Path(os.environ.get("AWS_DIAGRAM_SKILL_DIR") or pathlib.Path(__file__).resolve().parents[2])
ICONS = SKILL / "assets/aws-icons"
FONTS = SKILL / "assets/fonts/woff2"
GENERIC_MD = SKILL / "references/primitive-icons.md"

# ---- style-guide.md tokens (AWS skin) ---------------------------------------------------------
PAPER = "#FFFFFF"; PAPER2 = "#F2F3F3"; INK = "#232F3E"; MUTED = "#545B64"; SOFT = "#7D8998"
RULE = "rgba(35,47,62,0.12)"; ACCENT = "#EC7211"; ACCENT_TINT = "rgba(255,153,0,0.10)"; LINK = "#0972D3"

SANS = "'Amazon Ember','Noto Sans KR','NanumBarunGothic','Helvetica Neue',Helvetica,Arial,sans-serif"
MONO = "'Amazon Ember Mono','Noto Sans KR','NanumGothicCoding',ui-monospace,monospace"
KR_FONTS = "https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700&display=swap"

KIND = {  # node kind → (fill, stroke, dash)   [SKILL.md §5 node type → treatment]
    "step":     (PAPER, INK, None),
    "focal":    (ACCENT_TINT, ACCENT, None),
    "store":    ("rgba(35,47,62,0.05)", MUTED, None),
    "external": ("rgba(35,47,62,0.03)", "rgba(35,47,62,0.30)", None),
    "input":    ("rgba(84,91,100,0.10)", SOFT, None),
    "optional": ("rgba(35,47,62,0.02)", "rgba(35,47,62,0.20)", "4,3"),
    "security": ("rgba(236,114,17,0.05)", "rgba(236,114,17,0.50)", "4,4"),
}
# presentation ramp (output-spec.md §2): readable at doc width and when projected
NAME_SIZE = 16; SUB_SIZE = 12; LABEL_SIZE = 12; TAG_SIZE = 10; ZONE_SIZE = 14; LEGEND_SIZE = 12
ARROW = {"default": (MUTED, "arrow"), "accent": (ACCENT, "arrow-accent"), "link": (LINK, "arrow-link"), "soft": (SOFT, "arrow-soft")}

# Friendly aliases → icon file. Anything not listed here resolves by file stem (see resolve_icon).
AWS = {
    "EC2": "service/Compute/Arch_Amazon-EC2_48.svg",
    "DCV": "service/Compute/Arch_Amazon-DCV_48.svg",
    "Lambda": "service/Compute/Arch_AWS-Lambda_48.svg",
    "CloudFront": "service/Networking-Content-Delivery/Arch_Amazon-CloudFront_48.svg",
    "VPC": "service/Networking-Content-Delivery/Arch_Amazon-Virtual-Private-Cloud_48.svg",
    "ALB": "service/Networking-Content-Delivery/Arch_Elastic-Load-Balancing_48.svg",
    "APIGateway": "service/Networking-Content-Delivery/Arch_Amazon-API-Gateway_48.svg",
    "SQS": "service/Application-Integration/Arch_Amazon-Simple-Queue-Service_48.svg",
    "SNS": "service/Application-Integration/Arch_Amazon-Simple-Notification-Service_48.svg",
    "EventBridge": "service/Application-Integration/Arch_Amazon-EventBridge_48.svg",
    "StepFunctions": "service/Application-Integration/Arch_AWS-Step-Functions_48.svg",
    "SecretsManager": "service/Security-Identity/Arch_AWS-Secrets-Manager_48.svg",
    "IAM": "service/Security-Identity/Arch_AWS-Identity-and-Access-Management_48.svg",
    "KMS": "service/Security-Identity/Arch_AWS-Key-Management-Service_48.svg",
    "Cognito": "service/Security-Identity/Arch_Amazon-Cognito_48.svg",
    "S3": "service/Storage/Arch_Amazon-Simple-Storage-Service_48.svg",
    "FSx": "service/Storage/Arch_Amazon-FSx-for-Lustre_48.svg",
    "EFS": "service/Storage/Arch_Amazon-EFS_48.svg",
    "EBS": "service/Storage/Arch_Amazon-Elastic-Block-Store_48.svg",
    "SageMaker": "service/Artificial-Intelligence/Arch_Amazon-SageMaker-AI_48.svg",
    "Bedrock": "service/Artificial-Intelligence/Arch_Amazon-Bedrock_48.svg",
    "AgentCore": "service/Artificial-Intelligence/Arch_Amazon-Bedrock-AgentCore_48.svg",
    "EKS": "service/Containers/Arch_Amazon-Elastic-Kubernetes-Service_48.svg",
    "ECS": "service/Containers/Arch_Amazon-Elastic-Container-Service_48.svg",
    "ECR": "service/Containers/Arch_Amazon-Elastic-Container-Registry_48.svg",
    "Fargate": "service/Containers/Arch_AWS-Fargate_48.svg",
    "DynamoDB": "service/Databases/Arch_Amazon-DynamoDB_48.svg",
    "RDS": "service/Databases/Arch_Amazon-RDS_48.svg",
    "Aurora": "service/Databases/Arch_Amazon-Aurora_48.svg",
    "ElastiCache": "service/Databases/Arch_Amazon-ElastiCache_48.svg",
    "IoTCore": "service/Internet-of-Things/Arch_AWS-IoT-Core_48.svg",
    "Greengrass": "service/Internet-of-Things/Arch_AWS-IoT-Greengrass_48.svg",
    "CodeBuild": "service/Developer-Tools/Arch_AWS-CodeBuild_48.svg",
    "CodePipeline": "service/Developer-Tools/Arch_AWS-CodePipeline_48.svg",
    "CDK": "service/Developer-Tools/Arch_AWS-Cloud-Development-Kit_48.svg",
    "AMP": "service/Management-Tools/Arch_Amazon-Managed-Service-for-Prometheus_48.svg",
    "AMG": "service/Management-Tools/Arch_Amazon-Managed-Grafana_48.svg",
    "SSM": "service/Management-Tools/Arch_AWS-Systems-Manager_48.svg",
    "CloudFormation": "service/Management-Tools/Arch_AWS-CloudFormation_48.svg",
    "CloudWatch": "service/Management-Tools/Arch_Amazon-CloudWatch_48.svg",
    "CloudTrail": "service/Management-Tools/Arch_AWS-CloudTrail_48.svg",
    "Kinesis": "service/Analytics/Arch_Amazon-Kinesis_48.svg",
    "Glue": "service/Analytics/Arch_AWS-Glue_48.svg",
    "Athena": "service/Analytics/Arch_Amazon-Athena_48.svg",
    "Redshift": "service/Analytics/Arch_Amazon-Redshift_48.svg",
    "OpenSearch": "service/Analytics/Arch_Amazon-OpenSearch-Service_48.svg",
    # resource-level icons
    "SSMParam": "resource/Management-Governance/Res_AWS-Systems-Manager_Parameter-Store_48.svg",
    "CWLogs": "resource/Management-Governance/Res_Amazon-CloudWatch_Logs_48.svg",
    "User": "resource/General-Icons/Res_User_48_Light.svg",
    "Users": "resource/General-Icons/Res_Users_48_Light.svg",
    "Internet": "resource/General-Icons/Res_Internet_48_Light.svg",
    "Server": "resource/General-Icons/Res_Server_48_Light.svg",
    "Client": "resource/General-Icons/Res_Client_48_Light.svg",
    "EC2Instance": "resource/Compute/Res_Amazon-EC2_Instance_48.svg",
    "EC2Instances": "resource/Compute/Res_Amazon-EC2_Instances_48.svg",
    "IGW": "resource/Networking-Content-Delivery/Res_Amazon-VPC_Internet-Gateway_48.svg",
    "NAT": "resource/Networking-Content-Delivery/Res_Amazon-VPC_NAT-Gateway_48.svg",
    "SMTrain": "resource/Artificial-Intelligence/Res_Amazon-SageMaker-AI_Train_48.svg",
    "SMModel": "resource/Artificial-Intelligence/Res_Amazon-SageMaker-AI_Model_48.svg",
    "ECRImage": "resource/Containers/Res_Amazon-Elastic-Container-Registry_Image_48.svg",
    "GGComponent": "resource/IoT/Res_AWS-IoT-Greengrass_Component_48.svg",
    "GGComponentML": "resource/IoT/Res_AWS-IoT-Greengrass_Component-Machine-Learning_48.svg",
    "GGNucleus": "resource/IoT/Res_AWS-IoT-Greengrass_Component-Nucleus_48.svg",
    "S3Bucket": "resource/Storage/Res_Amazon-Simple-Storage-Service_Bucket-With-Objects_48.svg",
    "LambdaFunction": "resource/Compute/Res_AWS-Lambda_Lambda-Function_48.svg",
    # Amazon Bedrock AgentCore resources (traced, see THIRD_PARTY_LICENSES.md); "AgentCore" alias = official service icon
    "AgentCoreRes": "resource/Artificial-Intelligence/Res_Amazon-Bedrock-AgentCore_AgentCore_48.svg",
    "AIAgent": "resource/Artificial-Intelligence/Res_Amazon-Bedrock-AgentCore_AI-Agent_48.svg",
    "AgentCoreRuntime": "resource/Artificial-Intelligence/Res_Amazon-Bedrock-AgentCore_Runtime_48.svg",
    "AgentCoreGateway": "resource/Artificial-Intelligence/Res_Amazon-Bedrock-AgentCore_Gateway_48.svg",
    "AgentCoreMemory": "resource/Artificial-Intelligence/Res_Amazon-Bedrock-AgentCore_Memory_48.svg",
    "AgentCoreIdentity": "resource/Artificial-Intelligence/Res_Amazon-Bedrock-AgentCore_Identity_48.svg",
    "AgentCoreObservability": "resource/Artificial-Intelligence/Res_Amazon-Bedrock-AgentCore_Observability_48.svg",
    "AgentCorePolicy": "resource/Artificial-Intelligence/Res_Amazon-Bedrock-AgentCore_Policy-Engine_48.svg",
    "AgentCoreEvaluations": "resource/Artificial-Intelligence/Res_Amazon-Bedrock-AgentCore_Evaluations_48.svg",
    "AgentCoreBrowser": "resource/Artificial-Intelligence/Res_Amazon-Bedrock-AgentCore_Browser-Tool_48.svg",
    "AgentCoreCodeInterpreter": "resource/Artificial-Intelligence/Res_Amazon-Bedrock-AgentCore_Code-Interpreter_48.svg",
}
GROUP = {  # zone kind → (border, dash, badge file)   [primitive-aws-icons.md § group conventions]
    "cloud":      ("#242F3E", None, "group/AWS-Cloud_32.svg"),
    "account":    ("#E7157B", None, "group/AWS-Account_32.svg"),
    "region":     ("#00A4A6", "4,4", "group/Region_32.svg"),
    "vpc":        ("#8C4FFF", None, "group/Virtual-private-cloud-VPC_32.svg"),
    "public":     ("#7AA116", None, "group/Public-subnet_32.svg"),
    "private":    ("#00A4A6", None, "group/Private-subnet_32.svg"),
    "ec2":        ("#ED7100", None, "group/EC2-instance-contents_32.svg"),
    "greengrass": ("#7AA116", None, "group/AWS-IoT-Greengrass-Deployment_32.svg"),
    "server":     ("#7D8998", None, "group/Server-contents_32.svg"),
    "corporate":  ("#7D8998", None, "group/Corporate-data-center_32.svg"),
    "autoscaling": ("#ED7100", "4,4", "group/Auto-Scaling-group_32.svg"),
}

WARNINGS: list[str] = []   # build.py reads this; every entry is a label wider than its box


def _warn(msg: str) -> None:
    WARNINGS.append(msg); print("WARN " + msg, file=sys.stderr)


def min_node_w(name: str, sub: str | None = None, icon: bool = True, h: int = 64, name_size: int = NAME_SIZE, sub_size: int = SUB_SIZE) -> int:
    """Smallest node width (4px grid) that fits `name` and `sub` with the icon-left pattern at height `h`."""
    names = name if isinstance(name, list) else [name]
    tw = max([text_w(n, name_size) for n in names] + ([text_w(sub, sub_size, mono=True)] if sub else [0]))
    isz = (32 if h >= 64 else (24 if h >= 48 else 16)) if icon else 0
    pad = (12 + isz + 12 + 8) if icon else 16
    return int(-(-(tw + pad) // 4) * 4)


_svg_cache: dict[str, tuple[str, float]] = {}
_icon_index: dict[str, pathlib.Path] | None = None


def resolve_icon(name: str) -> pathlib.Path:
    """Alias (AWS dict) → path; otherwise match a file stem anywhere under assets/aws-icons.

    Accepts 'S3', 'Arch_Amazon-EC2_48', 'Amazon-EC2', 'Res_Amazon-EC2_Instance_48', or a relative path.
    """
    global _icon_index
    if name in AWS:
        return ICONS / AWS[name]
    if "/" in name:
        p = ICONS / name
        if p.exists(): return p
    if _icon_index is None:
        _icon_index = {}
        for p in ICONS.rglob("*.svg"):
            stem = p.stem
            for key in (stem, re.sub(r"^(Arch_|Res_)", "", stem), re.sub(r"^(Arch_|Res_)|_(48|32)(_Light|_Dark)?$", "", stem)):
                _icon_index.setdefault(key, p)
    if name in _icon_index:
        return _icon_index[name]
    raise KeyError(f"unknown AWS icon '{name}'. Add an alias in awsdiag.AWS or use a stem from assets/aws-icons/INDEX.md")


def _inner_g(path: pathlib.Path) -> tuple[str, float]:
    """Return (inner markup, viewBox size) of an icon SVG with ids stripped so many copies can share a document."""
    key = str(path)
    if key not in _svg_cache:
        s = path.read_text()
        s = re.sub(r"<\?xml[^>]*\?>", "", s); s = re.sub(r"<title>.*?</title>", "", s, flags=re.S)
        m = re.search(r"<svg([^>]*)>(.*)</svg>", s, flags=re.S)
        vb = re.search(r'viewBox="[\d.\s-]*?([\d.]+)\s+([\d.]+)"', m.group(1))
        size = float(vb.group(1)) if vb else 64.0
        body = re.sub(r'\s+id="[^"]*"', "", m.group(2))
        _svg_cache[key] = (body.strip(), size)
    return _svg_cache[key]


def aws_icon(name: str, x: float, y: float, size: int = 24) -> str:
    """Official icon, unmodified and uncolored, scaled to `size` px at (x, y)."""
    body, vb = _inner_g(resolve_icon(name))
    return f'<g transform="translate({x},{y}) scale({size / vb:.4f})" aria-hidden="true">{body}</g>'


def group_badge(kind: str, x: float, y: float, size: int = 24) -> str:
    body, vb = _inner_g(ICONS / GROUP[kind][2])
    return f'<g transform="translate({x},{y}) scale({size / vb:.3f})" aria-hidden="true">{body}</g>'


_generic: dict[str, str] = {}


def generic_icon(name: str, x: float, y: float, size: int = 24, color: str = INK) -> str:
    """Monochrome icon from references/primitive-icons.md (robot, python, docker, kubernetes, file, ...)."""
    if not _generic:
        txt = GENERIC_MD.read_text()
        for m in re.finditer(r"^### (\S+)\n.*?```svg\n(.*?)\n```", txt, flags=re.S | re.M):
            _generic[m.group(1)] = m.group(2)
    if name not in _generic:
        raise KeyError(f"unknown generic icon '{name}'. See references/primitive-icons.md headings")
    svg = re.sub(r"<title>.*?</title>", "", _generic[name])
    svg = svg.replace("<svg ", f'<svg x="{x}" y="{y}" style="color:{color}" ', 1)
    svg = re.sub(r'width="24" height="24"', f'width="{size}" height="{size}"', svg, count=1)
    return svg


def is_aws_icon(name: str) -> bool:
    try:
        resolve_icon(name); return True
    except KeyError:
        return False


def _icon(name: str, x: float, y: float, size: int, color: str = INK) -> str:
    return aws_icon(name, x, y, size) if is_aws_icon(name) else generic_icon(name, x, y, size, color)


def esc(s: str) -> str:
    return html.escape(s, quote=False)


def is_cjk(ch: str) -> bool:
    o = ord(ch)
    return (0xAC00 <= o <= 0xD7A3) or (0x3130 <= o <= 0x318F) or (0x4E00 <= o <= 0x9FFF) or (0x3000 <= o <= 0x303F)


def text_w(s: str, size: float, mono: bool = False) -> float:
    """Conservative width estimate (no font metrics at build time). Mono over-estimates by ~10px on long strings."""
    w = 0.0
    for ch in s:
        if is_cjk(ch): w += size * 1.0
        elif ch in "il.,:;'| ": w += size * (0.6 if mono else 0.3)
        elif ch.isupper() or ch.isdigit(): w += size * (0.6 if mono else 0.66)
        else: w += size * (0.6 if mono else 0.54)
    return w


def _polyline(d: str) -> list[tuple[float, float]]:
    """Anchor points of an orthogonal path string (M/H/V/L/Q); curve control points are skipped."""
    pts: list[tuple[float, float]] = []; x = y = 0.0
    for cmd, args in re.findall(r"([MHVLQ])\s*([-\d.,\s]*)", d):
        nums = [float(n) for n in re.findall(r"-?\d+(?:\.\d+)?", args)]
        if cmd == "M" or cmd == "L": x, y = nums[0], nums[1]
        elif cmd == "H": x = nums[0]
        elif cmd == "V": y = nums[0]
        elif cmd == "Q": x, y = nums[2], nums[3]
        pts.append((x, y))
    return pts


class Canvas:
    """One diagram. Paint order: zones → arrows → labels → nodes → overlay → legend (SKILL.md §6)."""

    def __init__(self, w: int, h: int, slug: str, title: str, desc: str, lang: str = "en"):
        self.w, self.h, self.slug, self.title, self.desc, self.lang = w, h, slug, title, desc, lang
        self.zones: list[str] = []; self.arrows: list[str] = []; self.nodes: list[str] = []
        self.labels: list[str] = []; self.overlay: list[str] = []; self.legend_items: list = []
        self._rects: list[tuple] = []; self._zrects: list[tuple] = []; self._ends: list[tuple] = []; self._lifelines: list[float] = []

    # ---- zones -----------------------------------------------------------
    def zone(self, x, y, w, h, label: str | None = None, kind: str = "generic", icon: str | None = None):
        """AWS group container (kind in GROUP: cloud/vpc/public/private/ec2/...) or kind="generic" (quiet box,
        optional icon) for any other grouping such as a cluster, a service, a team, or a phase."""
        if kind != "generic" and kind not in GROUP:
            raise KeyError(f"unknown zone kind '{kind}'. Use one of {sorted(GROUP)} or 'generic'")
        self._zrects.append((x, y, w, h, label or kind))
        if kind in GROUP:
            border, dash, _ = GROUP[kind]
            dsh = f' stroke-dasharray="{dash}"' if dash else ""
            self.zones.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="none" stroke="{border}" stroke-width="1"{dsh}/>')
            self.zones.append(group_badge(kind, x, y, 28))
            if label:
                self.zones.append(f'<text x="{x+36}" y="{y+19}" fill="{INK}" font-size="{ZONE_SIZE}" font-weight="600" font-family="{SANS}">{esc(label)}</text>')
        else:
            self.zones.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="rgba(35,47,62,0.02)" stroke="rgba(35,47,62,0.12)" stroke-width="0.8"/>')
            lx = x + 12
            if icon:
                self.zones.append(_icon(icon, x + 8, y + 6, 24, MUTED)); lx = x + 40
            if label:
                self.zones.append(f'<text x="{lx}" y="{y+21}" fill="{INK}" font-size="{ZONE_SIZE}" font-weight="600" font-family="{SANS}">{esc(label)}</text>')

    # ---- arrows ----------------------------------------------------------
    def path(self, d: str, style: str = "default", dashed: bool = False, head: bool = True, width: float | None = None):
        """Connector. style in ARROW (default/accent/link/soft); dashed = optional/async/return."""
        color, marker = ARROW[style]
        self._ends.append(_polyline(d))
        sw = width or (1.0 if dashed else 1.2)
        dash = ' stroke-dasharray="5,4"' if dashed else ""
        mk = f' marker-end="url(#{marker})"' if head else ""
        self.arrows.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{sw}"{dash}{mk}/>')

    def label(self, x, y, text: str, *, anchor: str = "middle", size: int | None = None, color: str = SOFT):
        """Arrow label at (x, baseline y) on an opaque paper mask; anchor/size/color are keyword-only.
        Horizontal arrow at Y: label(mid_x, Y - 12, "TEXT"). Vertical arrow at X: label(X + 16, y, "TEXT", anchor="start").
        Keep the mask on open canvas: nodes paint later and would clip it."""
        size = size or LABEL_SIZE
        lines = text.split("\n"); lh = size + 3
        mw = max(text_w(l, size, mono=True) for l in lines) + 8
        top = y - size - 1 - (len(lines) - 1) * lh
        mx = x - mw / 2 if anchor == "middle" else (x - 4 if anchor == "start" else x - mw + 4)
        self.labels.append(f'<rect x="{mx:.0f}" y="{top:.0f}" width="{mw:.0f}" height="{len(lines)*lh + 2}" rx="2" fill="{PAPER}"/>')
        for i, l in enumerate(lines):
            yy = y - (len(lines) - 1 - i) * lh
            self.labels.append(f'<text x="{x}" y="{yy}" fill="{color}" font-size="{size}" font-family="{MONO}" text-anchor="{anchor}" letter-spacing="0.04em">{esc(l)}</text>')

    # ---- nodes -----------------------------------------------------------
    def node(self, x, y, w, h, name, sub: str | None = None, icon: str | None = None, kind: str = "step",
             tag: str | None = None, name_size: int = NAME_SIZE, sub_size: int | None = None, icon_color: str = INK):
        """Block node: name (1 line, or list for 2) + optional one-line sublabel. icon: AWS alias/stem or generic name."""
        fill, stroke, dash = KIND[kind]
        self._rects.append((x, y, w, h, name if isinstance(name, str) else " / ".join(name)))
        dsh = f' stroke-dasharray="{dash}"' if dash else ""
        p = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{PAPER}"/>',
             f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{fill}" stroke="{stroke}" stroke-width="1"{dsh}/>']
        ss = sub_size or SUB_SIZE
        names = name if isinstance(name, list) else [name]
        block = len(names) * (name_size + 4) + ((ss + 4) if sub else 0) + ((TAG_SIZE + 4) if tag else 0)
        if icon:
            isz = 32 if h >= 64 else (24 if h >= 48 else 16)
            p.append(_icon(icon, x + 12, y + (h - isz) // 2, isz, icon_color))
            tx, anchor, avail = x + 12 + isz + 12, "start", w - (12 + isz + 12) - 8
        else:
            tx, anchor, avail = x + w / 2, "middle", w - 16
        by = y + h / 2 - block / 2 + name_size - 1
        if tag:
            p.append(f'<text x="{tx:.0f}" y="{by - name_size + TAG_SIZE + 1:.0f}" fill="{SOFT}" font-size="{TAG_SIZE}" font-family="{MONO}" text-anchor="{anchor}" letter-spacing="0.08em">{esc(tag)}</text>')
            by += TAG_SIZE + 4
        for l in names:
            if text_w(l, name_size) > avail: _warn(f"name [{self.slug}-{self.lang}] '{l}' needs w>={min_node_w(l, None, bool(icon), h, name_size)} (box {w}, text {text_w(l, name_size):.0f} > {avail:.0f} avail)")
        if sub and text_w(sub, ss, mono=True) > avail: _warn(f"sub  [{self.slug}-{self.lang}] '{sub}' needs w>={min_node_w('', sub, bool(icon), h, name_size, ss)} (box {w}, text {text_w(sub, ss, mono=True):.0f} > {avail:.0f} avail)")
        for i, l in enumerate(names):
            p.append(f'<text x="{tx:.0f}" y="{by + i*(name_size+4):.0f}" fill="{INK}" font-size="{name_size}" font-weight="600" font-family="{SANS}" text-anchor="{anchor}">{esc(l)}</text>')
        if sub:
            p.append(f'<text x="{tx:.0f}" y="{by + (len(names)-1)*(name_size+4) + ss + 5:.0f}" fill="{MUTED}" font-size="{ss}" font-family="{MONO}" text-anchor="{anchor}">{esc(sub)}</text>')
        self.nodes.append("\n".join(p))

    def stack(self, x, y, w, h, *args, depth: int = 2, **kw):
        """Node with `depth` offset ghost outlines behind it (a set of similar things: replicas, workers)."""
        kind = kw.get("kind", "step"); stroke = KIND[kind][1]
        for i in range(depth, 0, -1):
            self.nodes.append(f'<rect x="{x+4*i}" y="{y-4*i}" width="{w}" height="{h}" rx="6" fill="{PAPER}" stroke="{stroke}" stroke-opacity="{0.55 - 0.15*i:.2f}" stroke-width="1"/>')
        self.node(x, y, w, h, *args, **kw)

    def decision(self, cx, cy, w, h, text: str, kind: str = "step"):
        """Flowchart decision diamond centered at (cx, cy)."""
        fill, stroke, _ = KIND[kind]
        self._rects.append((cx - w / 2, cy - h / 2, w, h, text))
        pts = f"{cx},{cy-h/2} {cx+w/2},{cy} {cx},{cy+h/2} {cx-w/2},{cy}"
        self.nodes.append(f'<polygon points="{pts}" fill="{PAPER}"/><polygon points="{pts}" fill="{fill}" stroke="{stroke}" stroke-width="1"/>')
        self.nodes.append(f'<text x="{cx}" y="{cy+4}" fill="{INK}" font-size="12" font-family="{MONO}" text-anchor="middle">{esc(text)}</text>')

    def lifeline(self, x, y1, y2):
        """Sequence-diagram lifeline (dashed vertical) painted with zones, behind everything."""
        self._lifelines.append(x)
        self.zones.append(f'<line x1="{x}" y1="{y1}" x2="{x}" y2="{y2}" stroke="{SOFT}" stroke-width="1" stroke-dasharray="4,4"/>')

    def note(self, x, y, text: str, anchor: str = "middle", size: int = 12, color: str = MUTED):
        """Free mono annotation painted above nodes (multi-line with \\n)."""
        for i, l in enumerate(text.split("\n")):
            self.overlay.append(f'<text x="{x}" y="{y + i*(size+4)}" fill="{color}" font-size="{size}" font-family="{MONO}" text-anchor="{anchor}">{esc(l)}</text>')

    def legend(self, items):
        """Bottom strip. items: [(key, text)] where key is a KIND name, 'arrow', 'arrow:accent', 'arrow-dashed',
        'arrow:link-dashed', an AWS icon alias, or a generic icon name. Reserve ~56px of canvas height."""
        self.legend_items = items

    # ---- connectors (all orthogonal, r=8 quarter arcs) -------------------
    @staticmethod
    def hline(x1, y, x2): return f"M {x1},{y} H {x2}"
    @staticmethod
    def vline(x, y1, y2): return f"M {x},{y1} V {y2}"

    @staticmethod
    def elbow_hvh(x1, y1, x2, y2, mid=None, r=8):
        """Horizontal → vertical → horizontal; `mid` = x of the vertical leg."""
        mid = (x1 + x2) / 2 if mid is None else mid
        sx = 1 if x2 > x1 else -1; sy = 1 if y2 > y1 else -1
        if y1 == y2: return f"M {x1},{y1} H {x2}"
        return (f"M {x1},{y1} H {mid - sx*r} Q {mid},{y1} {mid},{y1 + sy*r} V {y2 - sy*r} Q {mid},{y2} {mid + sx*r},{y2} H {x2}")

    @staticmethod
    def elbow_vhv(x1, y1, x2, y2, mid=None, r=8):
        """Vertical → horizontal → vertical; `mid` = y of the horizontal leg."""
        mid = (y1 + y2) / 2 if mid is None else mid
        sx = 1 if x2 > x1 else -1; sy = 1 if y2 > y1 else -1
        if x1 == x2: return f"M {x1},{y1} V {y2}"
        return (f"M {x1},{y1} V {mid - sy*r} Q {x1},{mid} {x1 + sx*r},{mid} H {x2 - sx*r} Q {x2},{mid} {x2},{mid + sy*r} V {y2}")

    @staticmethod
    def L_hv(x1, y1, x2, y2, r=8):
        """Single bend: horizontal then vertical."""
        sx = 1 if x2 > x1 else -1; sy = 1 if y2 > y1 else -1
        return f"M {x1},{y1} H {x2 - sx*r} Q {x2},{y1} {x2},{y1 + sy*r} V {y2}"

    @staticmethod
    def L_vh(x1, y1, x2, y2, r=8):
        """Single bend: vertical then horizontal."""
        sx = 1 if x2 > x1 else -1; sy = 1 if y2 > y1 else -1
        return f"M {x1},{y1} V {y2 - sy*r} Q {x1},{y2} {x1 + sx*r},{y2} H {x2}"

    # ---- layout check ----------------------------------------------------
    def check(self, tol: float = 2.0) -> list[str]:
        """Geometry rules a spec must satisfy (SKILL.md §6–§7). Returns human-readable issues; build.py reports them as WARN."""
        out = []; tag = f"[{self.slug}-{self.lang}]"

        def on_edge(px, py, x, y, w, h):
            inx = x - tol <= px <= x + w + tol; iny = y - tol <= py <= y + h + tol
            return (inx and (abs(py - y) <= tol or abs(py - (y + h)) <= tol)) or (iny and (abs(px - x) <= tol or abs(px - (x + w)) <= tol))

        def inside(px, py, x, y, w, h):
            return x + tol < px < x + w - tol and y + tol < py < y + h - tol

        R = self._rects
        for i, (x, y, w, h, n) in enumerate(R):
            for (x2, y2, w2, h2, n2) in R[i + 1:]:
                if x < x2 + w2 - tol and x2 < x + w - tol and y < y2 + h2 - tol and y2 < y + h - tol:
                    out.append(f"layout {tag} nodes overlap: '{n}' and '{n2}'")
            for (zx, zy, zw, zh, zn) in self._zrects:
                hit = x < zx + zw and zx < x + w and y < zy + zh and zy < y + h
                contained = x >= zx - tol and y >= zy - tol and x + w <= zx + zw + tol and y + h <= zy + zh + tol
                if hit and not contained:
                    out.append(f"layout {tag} node '{n}' straddles zone '{zn}': move it fully inside or outside")
                elif contained and y < zy + 36 - tol and x < zx + 40 + text_w(zn, ZONE_SIZE):
                    out.append(f"layout {tag} node '{n}' covers the badge row of zone '{zn}': start nodes at y>={zy + 40:.0f}")
            if self.legend_items and y + h > self.h - 60 + tol:
                out.append(f"layout {tag} node '{n}' collides with the legend strip: keep bottom edge <= h-60 ({self.h - 60})")
        for (zx, zy, zw, zh, zn) in self._zrects:
            if self.legend_items and zy + zh > self.h - 60 + tol:
                out.append(f"layout {tag} zone '{zn}' collides with the legend strip: keep bottom edge <= h-60 ({self.h - 60})")
        def on_segment(px, py, a, b):
            (ax, ay), (bx, by) = a, b
            return (min(ax, bx) - tol <= px <= max(ax, bx) + tol) and (min(ay, by) - tol <= py <= max(ay, by) + tol) \
                   and (abs(ax - bx) <= tol or abs(ay - by) <= tol) and (abs(px - ax) <= tol if abs(ax - bx) <= tol else abs(py - ay) <= tol)

        for i, pl in enumerate(self._ends):
            if len(pl) < 2: continue
            for (px, py) in (pl[0], pl[-1]):
                ok = any(on_edge(px, py, *r[:4]) for r in R) or any(on_edge(px, py, *z[:4]) for z in self._zrects) \
                     or any(abs(px - lx) <= 8 for lx in self._lifelines) \
                     or any(on_segment(px, py, q[k], q[k + 1]) for j, q in enumerate(self._ends) if j != i for k in range(len(q) - 1))
                if ok and any(inside(px, py, *r[:4]) for r in R):
                    ok = False
                if not ok:
                    out.append(f"layout {tag} arrow endpoint ({px:.0f},{py:.0f}) touches no node, zone edge, lifeline, or other connector: compute it from the node (x+w, y+h/2 ...)")
        return out

    # ---- render ----------------------------------------------------------
    def svg(self) -> str:
        legend = []
        if self.legend_items:
            ly = self.h - 40
            legend.append(f'<line x1="40" y1="{ly-16}" x2="{self.w-40}" y2="{ly-16}" stroke="{RULE}" stroke-width="0.8"/>')
            lx = 40
            for key, text in self.legend_items:
                if key in KIND:
                    fill, stroke, dash = KIND[key]; dsh = f' stroke-dasharray="{dash}"' if dash else ""
                    legend.append(f'<rect x="{lx}" y="{ly-8}" width="16" height="12" rx="2" fill="{fill}" stroke="{stroke}" stroke-width="1"{dsh}/>')
                elif key.startswith("arrow"):
                    dashed = key.endswith("-dashed"); st = key.split(":")[1].split("-")[0] if ":" in key else "default"
                    color, marker = ARROW[st]; dsh = ' stroke-dasharray="4,3"' if dashed else ""
                    legend.append(f'<path d="M {lx},{ly-2} H {lx+16}" stroke="{color}" stroke-width="1.2"{dsh} marker-end="url(#{marker})"/>')
                else:
                    legend.append(_icon(key, lx, ly - 12, 20, INK))
                legend.append(f'<text x="{lx+24}" y="{ly+3}" fill="{MUTED}" font-size="{LEGEND_SIZE}" font-family="{SANS}">{esc(text)}</text>')
                lx += 24 + text_w(text, LEGEND_SIZE) * 1.1 + 32
        body = "\n".join(self.zones + self.arrows + self.labels + self.nodes + self.overlay + legend)
        return f'''<svg viewBox="0 0 {self.w} {self.h}" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="{self.slug}-title {self.slug}-desc">
  <title id="{self.slug}-title">{esc(self.title)}</title>
  <desc id="{self.slug}-desc">{esc(self.desc)}</desc>
  <defs>
    <marker id="arrow" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><polygon points="0 0, 8 3, 0 6" fill="{MUTED}"/></marker>
    <marker id="arrow-accent" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><polygon points="0 0, 8 3, 0 6" fill="{ACCENT}"/></marker>
    <marker id="arrow-link" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><polygon points="0 0, 8 3, 0 6" fill="{LINK}"/></marker>
    <marker id="arrow-soft" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><polygon points="0 0, 8 3, 0 6" fill="{SOFT}"/></marker>
  </defs>
  <rect width="100%" height="100%" fill="{PAPER}"/>
{body}
</svg>'''

    def html(self, eyebrow: str = "AWS Diagram", kr_webfont: bool = True) -> str:
        """Self-contained HTML: bundled Amazon Ember via file:// @font-face (local() first) plus the Noto Sans KR
        webfont link, which also supplies glyphs Ember lacks (Hangul, →, ×). kr_webfont=False for offline builds
        (falls back to NanumBarunGothic / NanumGothicCoding if installed; arrows render thinner)."""
        f = f"file://{FONTS}"
        faces = "\n".join(
            f"@font-face{{font-family:'{fam}';font-weight:{wt};font-style:{st};src:local('{loc}'),url('{f}/{fn}') format('woff2');}}"
            for fam, wt, st, loc, fn in [
                ("Amazon Ember", 400, "normal", "Amazon Ember", "AmazonEmber_W_Rg.woff2"),
                ("Amazon Ember", 400, "italic", "Amazon Ember Italic", "AmazonEmber_W_RgIt.woff2"),
                ("Amazon Ember", 600, "normal", "Amazon Ember Medium", "AmazonEmber_W_SBd.woff2"),
                ("Amazon Ember", 700, "normal", "Amazon Ember Bold", "AmazonEmber_W_Bd.woff2"),
                ("Amazon Ember Mono", 400, "normal", "Amazon Ember Mono", "AmazonEmberMono_W_Rg.woff2"),
                ("Amazon Ember Mono", 700, "normal", "Amazon Ember Mono Bold", "AmazonEmberMono_W_Bd.woff2")])
        kr_link = f'<link href="{KR_FONTS}" rel="stylesheet">\n' if kr_webfont else ""
        return f'''<!DOCTYPE html>
<html lang="{self.lang}">
<head>
<meta charset="UTF-8">
<title>{esc(self.title)}</title>
{kr_link}<style>
{faces}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:{SANS};background:{PAPER};color:{INK};padding:2rem}}
.frame{{max-width:1200px}}
.eyebrow{{font-family:{MONO};font-size:.66rem;letter-spacing:.18em;text-transform:uppercase;color:{MUTED};margin-bottom:.5rem}}
h1{{font-family:{SANS};font-size:1.75rem;font-weight:700;margin-bottom:1.5rem}}
svg{{width:100%;display:block}}
</style></head>
<body><div class="frame">
<p class="eyebrow">{esc(eyebrow)}</p>
<h1>{esc(self.title)}</h1>
{self.svg()}
</div></body></html>'''


def T(lang: str, ko: str, en: str) -> str:
    """Pick a string by language so one layout renders both ko and en."""
    return ko if lang == "ko" else en


if __name__ == "__main__":  # python3 awsdiag.py → catalogue of names a spec may use
    generic_icon("user", 0, 0)
    print("node kinds :", " ".join(KIND))
    print("zone kinds :", " ".join(GROUP), "generic")
    print("arrow style:", " ".join(ARROW))
    print("legend keys: <node kind> | arrow | arrow:<style> | arrow-dashed | arrow:<style>-dashed | <icon name>")
    print("AWS aliases:", " ".join(sorted(AWS)))
    print("generic icons:", " ".join(sorted(_generic)))
    print("any other AWS icon: file stem from assets/aws-icons/INDEX.md, e.g. Amazon-Route-53, Res_Amazon-EC2_Instance_48")
