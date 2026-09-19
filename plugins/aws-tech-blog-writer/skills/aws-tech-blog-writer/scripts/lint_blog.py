#!/usr/bin/env python3
"""Lint a Korean AWS Tech Blog draft for house-style and machine-text markers.

    python3 lint_blog.py <draft.md> [--placeholders-out <file>] [--strict] [--final] [--no-service-check]

Errors (exit 1): forbidden punctuation in prose, wrong AWS service prefixes or Korean transliterations,
images without file / alt / caption, code fences without a language, malformed or empty placeholders,
more than one H1. With --final, leftover fact-ID comments (<!-- F12 -->) are errors too.
Warnings (exit 1 only with --strict): translation-ese vocabulary and constructions, figurative nouns,
abstract nouns used as actors, passive endings with an available agent, plain-form headings, plain-form
or 해요체 endings, connective overuse, over-long sentences, unintroduced service short names, numbers that
need a claim row, English-only paragraphs, and other patterns from references/voice.md.
Always prints a placeholder summary; --placeholders-out writes it as Markdown for the author.
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

# --------------------------------------------------------------------------- rules

FORBIDDEN_PUNCT = {
    "—": "em dash (—)",
    "–": "en dash (–)",
    "·": "middle dot (·)",
    "•": "bullet (•)",
    "‧": "hyphenation point (‧)",
    "∙": "bullet operator (∙)",
    "・": "katakana middle dot (・)",
    "…": "ellipsis (…)",
}
ARROW_RE = re.compile(r"[←-⇿⬀-⯿]|(?<![-<])->(?!>)|=>")
EMOJI_RE = re.compile(r"[\U0001F300-\U0001FAFF☀-➿✅❌✔✓]")
DOUBLE_HYPHEN_RE = re.compile(r"\s--\s")
TILDE_OK_RE = re.compile(r"(\d|[월일년시])\s?~\s?\d")

WRONG_AMAZON_AS_AWS = re.compile(
    r"\bAWS (Bedrock|S3|DynamoDB|EC2|ECS|EKS|ECR|Cognito|CloudWatch|SageMaker|Aurora|RDS|SQS|SNS|EventBridge|"
    r"API Gateway|CloudFront|Route ?53|VPC|OpenSearch|ElastiCache|QuickSight|Kinesis|Redshift|Athena|EMR|"
    r"Comprehend|Textract|Transcribe|Polly|Rekognition|Neptune|DocumentDB|MSK|MQ|EFS|FSx|Q Developer|Q Business)\b"
)
WRONG_AWS_AS_AMAZON = re.compile(
    r"\bAmazon (Lambda|IAM|Fargate|Step Functions|Glue|CloudFormation|CDK|WAF|Shield|Secrets Manager|KMS|"
    r"CloudTrail|X-Ray|Systems Manager|PrivateLink|Network Firewall|Transform|Amplify|AppSync|Batch|Backup|"
    r"Config|Organizations|Control Tower|Direct Connect|Transit Gateway|Well-Architected|IAM Identity Center|"
    r"App Runner|Outposts|Wavelength|Snowball|DataSync|Transfer Family|Global Accelerator)\b"
)
TRANSLITERATIONS = re.compile(
    r"람다|다이나모\s?디비|다이나모DB|베드락|베드록|코그니토|클라우드워치|세이지메이커|아마존\s?S3|에스쓰리|"
    r"이씨투|파게이트|파게이트|스텝\s?펑션|이벤트브리지|클라우드프론트|오로라(?=\s?(DB|데이터베이스|PostgreSQL|MySQL))"
)
SUBSERVICE_MISNAMES = re.compile(r"\bBedrock (Gateway|Memory|Identity|Observability|Policy Engine)\b")

# short name -> full name required at or before first body mention
FULL_NAMES = {
    "AgentCore": "Amazon Bedrock AgentCore",
    "Knowledge Bases": "Amazon Bedrock Knowledge Bases",
    "Guardrails": "Amazon Bedrock Guardrails",
    "Bedrock": "Amazon Bedrock",
    "Lambda": "AWS Lambda",
    "DynamoDB": "Amazon DynamoDB",
    "S3": "Amazon S3",
    "Cognito": "Amazon Cognito",
    "Fargate": "AWS Fargate",
    "ECS": "Amazon ECS",
    "EKS": "Amazon EKS",
    "ECR": "Amazon ECR",
    "EC2": "Amazon EC2",
    "CloudWatch": "Amazon CloudWatch",
    "Aurora": "Amazon Aurora",
    "RDS": "Amazon RDS",
    "OpenSearch": "Amazon OpenSearch Service",
    "ElastiCache": "Amazon ElastiCache",
    "EventBridge": "Amazon EventBridge",
    "SQS": "Amazon SQS",
    "SNS": "Amazon SNS",
    "Step Functions": "AWS Step Functions",
    "Glue": "AWS Glue",
    "Secrets Manager": "AWS Secrets Manager",
    "IAM": "AWS IAM",
    "KMS": "AWS KMS",
    "CloudFront": "Amazon CloudFront",
    "Route 53": "Amazon Route 53",
    "API Gateway": "Amazon API Gateway",
    "VPC": "Amazon VPC",
    "SageMaker": "Amazon SageMaker AI",
    "QuickSight": "Amazon QuickSight",
    "CloudFormation": "AWS CloudFormation",
    "CDK": "AWS CDK",
    "WAF": "AWS WAF",
    "PrivateLink": "AWS PrivateLink",
    "CloudTrail": "AWS CloudTrail",
    "X-Ray": "AWS X-Ray",
}

BANNED_VOCAB = [
    "여정", "혁신적", "획기적", "강력한", "놀라운", "탁월한", "최첨단", "차세대", "게임 체인저", "게임체인저",
    "패러다임", "원활한", "원활하게", "매끄러운", "매끄럽게", "손쉽게", "한층", "한 걸음 더", "시너지",
    "레버리지", "임팩트", "비즈니스 가치", "든든한", "안정적이고 확장 가능한", "확장성과 유연성", "최적의",
    "완벽한", "성공적으로", "핵심적인 역할", "중요한 역할을", "필수적입니다", "궁극적으로", "결론적으로",
    "요약하면", "정리하면", "주목할 점은", "흥미로운 점은", "놀랍게도", "중요한 점은", "핵심은 ", "잊지 마세요",
    "살펴보도록 하겠습니다", "디지털 전환의 핵심", "인사이트",
]
SOFT_VOCAB = ["다양한", "효과적으로", "효율적으로", "이를 통해", "우리는", "저희는"]
METAPHORS = ["나침반", "등불", "항해", "심장", "두뇌", "무대", "다리 역할", "톱니바퀴", "퍼즐", "열쇠",
             "문을 열", "길을 열", "발판", "날개를", "레시피", "빙산", "이정표", "청사진", "지렛대", "밑거름",
             "뼈대", "큰 그림", "전체 그림", "목표 그림", "재료", "몫", "씨앗", "열매", "울타리", "무기"]
# 축 is literal in 시간축 / X축 / 좌표축; elsewhere it stands for a workstream or a request path
FIGURATIVE_AXIS_RE = re.compile(r"(?<![가-힣A-Za-z])축(?=[은는이가을를의로와과에 ,.:)])")
# abstract noun as the actor of a human or physical verb (voice.md §1.1)
ABSTRACT_SUBJECTS = "문제|질문|과제|조건|선택|결정|구조|차이|필요|요구|한계|이유|고민|숙제|답|일|경계|규칙|원칙|목표|비용|부담"
PERSONIFICATION_RE = re.compile(
    r"(?:" + ABSTRACT_SUBJECTS + r")(?:이|가|은|는|도)\s[^.]{0,30}?"
    r"(남습니다|남는다|남았습니다|따라옵니다|따라온다|쌓입니다|쌓인다|결정합니다|결정했습니다|뒷받침합니다|뒷받침했습니다|"
    r"말해\s?줍니다|말합니다|보여\s?줍니다|이끕니다|기다립니다|찾아옵니다|드러냅니다|떠오릅니다|등장합니다|"
    r"자리\s?잡|요구합니다|가리킵니다|알려\s?줍니다|좌우합니다|말해주듯)")
# passive endings that hide an available actor (voice.md §1.2); each occurrence warns
AGENTIVE_PASSIVES = re.compile(
    r"(요구|정리|구성|확인|진행|수행|제공|사용|적용|처리|판단|예상|기대|고려|검토|결정|선택|도입|구축|설계|운영|관리|개발|작성|"
    r"배포|호출|전달|저장|수집|분석|생성|등록|승인|검증|측정|평가)(됩니다|되었습니다|되며|되고|되어\s|될 예정)")
PASSIVE_ENDING_RE = re.compile(r"(됩니다|되었습니다|이루어집니다|어집니다|어졌습니다|여집니다)\.?$")
CONNECTIVES = ["그래서", "하지만", "이때", "결국", "다만", "즉,"]
PLAIN_HEADING_RE = re.compile(r"(는다|이다|니다|ㄴ다|않다|없다|있다|된다|한다|르다|하다|크다|많다|다르다|같다|어렵다|쉽다)\s*$")
CONSTRUCTIONS = [
    (re.compile(r"에 있어서?(?!\w)"), "'~에 있어' (translated 'in terms of'); use '~에서', '~할 때'"),
    (re.compile(r"함에 있어"), "'~함에 있어'; use '~할 때'"),
    (re.compile(r"가능하게 (합니다|했습니다|하며|하고)"), "'~를 가능하게 합니다' (translated 'enables'); use '~할 수 있습니다'"),
    (re.compile(r"라고 (할|볼) 수 있습니다"), "hedged assertion; assert or cut"),
    (re.compile(r"할 수 있게 됩니다"), "double auxiliary; use '할 수 있습니다'"),
    (re.compile(r"되어집니다|되어지"), "stacked passive"),
    (re.compile(r"에 의해 .{0,20}(되었습니다|됩니다)"), "passive 'by'; make the team the subject"),
    (re.compile(r"단순히 .{0,30}아니라"), "negative parallelism ('not just X but Y')"),
    (re.compile(r"뿐만 아니라"), "'~뿐만 아니라' parallelism; state the second half"),
    (re.compile(r"(^|\s)(첫째|둘째|셋째),"), "'첫째, 둘째, 셋째' formula; prose or a table"),
    (re.compile(r"(^|[.!?]\s+)(그것은|이것은|이는)\s"), "pronoun subject at sentence start; repeat the noun"),
    (re.compile(r"에 대해 알아보(겠|도록 하겠)습니다"), "empty section opener; state the question the section answers"),
    (re.compile(r"(하며|하면서)[^.]{0,60}(하며|하면서)[^.]{0,60}(하며|하면서)"), "three chained clauses; split"),
    (re.compile(r"의 중요성을 (보여|강조|시사)"), "significance sentence; cut"),
    (re.compile(r"여러분"), "'여러분'; address the reader indirectly"),
    (re.compile(r"(?<![니])다\.(\s|$)"), "plain form '~다.' in body; use '~합니다'"),
    (re.compile(r"(?<!니)요\.(\s|$)"), "해요체 ending; use '~합니다'"),
]
NEEDS_CLAIM_RE = re.compile(r"\d+(\.\d+)?\s?(%|배|ms|초|분|시간|TPS|RPS|GB|MB|TB|원|달러|USD)")
FACT_ID_RE = re.compile(r"<!--\s*[FRC]\d+[^>]*-->")
BOLD_RE = re.compile(r"\*\*([^*]{26,})\*\*")

PH_TAGS = ["작성자 확인", "기술 검증 필요", "이미지 필요", "인용 승인 필요"]
PH_STYLE = {
    "작성자 확인": "background-color:#FFF2CC;color:#7F6000;",
    "기술 검증 필요": "background-color:#F8CECC;color:#9F0000;",
    "이미지 필요": "background-color:#DAE8FC;color:#0B3D91;",
    "인용 승인 필요": "background-color:#D5E8D4;color:#1E5631;",
}
PH_SPAN_RE = re.compile(
    r'<span style="(?P<style>[^"]*)">\s*\[(?P<tag>' + "|".join(PH_TAGS) + r")\]\s*(?P<text>.*?)</span>", re.S
)
PH_TAG_RE = re.compile(r"\[(" + "|".join(PH_TAGS) + r")\]")

IMAGE_RE = re.compile(r"!\[(?P<alt>[^\]]*)\]\((?P<path>[^)\s]+)(?:\s+\"[^\"]*\")?\)")
CAPTION_RE = re.compile(r"^\s*(?:\*|_)?그림\s*(\d+)\.\s*\S")
FENCE_RE = re.compile(r"^(\s*)(```+|~~~+)(.*)$")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")


@dataclass
class Finding:
    level: str  # error | warn | info
    line: int
    code: str
    msg: str


@dataclass
class Report:
    findings: list = field(default_factory=list)

    def add(self, level, line, code, msg):
        self.findings.append(Finding(level, line, code, msg))

    def count(self, level):
        return sum(1 for f in self.findings if f.level == level)


# --------------------------------------------------------------------------- helpers

def strip_inline(text: str) -> str:
    """Remove inline code, URLs, HTML comments and HTML tags so punctuation checks see prose only."""
    text = re.sub(r"`[^`]*`", " ", text)
    text = re.sub(r"<!--.*?-->", " ", text)
    text = re.sub(r"\]\([^)]*\)", "]()", text)  # link targets
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"<[^>]+>", " ", text)
    return text


def split_sentences(text: str):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


# --------------------------------------------------------------------------- main lint

def lint(path: Path, final: bool, service_check: bool):
    rep = Report()
    lines = path.read_text(encoding="utf-8").splitlines()

    in_fence = False
    fence_marker = ""
    h1_count = 0
    prev_heading_level = 0
    prose_lines: list[tuple[int, str]] = []  # (lineno, prose text) outside fences
    table_lines: set[int] = set()
    images: list[tuple[int, str, str]] = []
    figure_numbers: list[tuple[int, int]] = []
    body_text_positions: list[tuple[int, str]] = []
    paragraph: list[tuple[int, str]] = []
    paragraphs: list[list[tuple[int, str]]] = []
    code_fence_count = 0

    def flush_par():
        nonlocal paragraph
        if paragraph:
            paragraphs.append(paragraph)
            paragraph = []

    for i, raw in enumerate(lines, 1):
        m = FENCE_RE.match(raw)
        if m and not in_fence:
            in_fence = True
            fence_marker = m.group(2)[0]
            code_fence_count += 1
            lang = m.group(3).strip()
            if not lang:
                rep.add("error", i, "E4", "code fence without a language (python, bash, json, yaml, hcl, sql, text)")
            flush_par()
            continue
        if in_fence:
            if m and m.group(2)[0] == fence_marker and not m.group(3).strip():
                in_fence = False
            continue

        stripped = raw.strip()
        if not stripped:
            flush_par()
            continue

        hm = HEADING_RE.match(raw)
        if hm:
            flush_par()
            level = len(hm.group(1))
            if level == 1:
                h1_count += 1
                if h1_count > 1:
                    rep.add("error", i, "E6", "more than one H1; the title is the only H1")
            elif prev_heading_level and level > prev_heading_level + 1:
                rep.add("warn", i, "W6", f"heading level jumps from H{prev_heading_level} to H{level}")
            prev_heading_level = level
            title = hm.group(2)
            if title.rstrip().endswith(("?", "!")):
                rep.add("warn", i, "W6", "heading ends with ? or !")
            if PLAIN_HEADING_RE.search(strip_inline(title)):
                rep.add("warn", i, "W6", "plain-form sentence heading; use a noun phrase (voice.md §2.4)")
            if PH_TAG_RE.search(title) and not PH_SPAN_RE.search(title):
                # placeholders in headings are allowed as bare tags
                pass

        if stripped.startswith("|"):
            table_lines.add(i)

        for im in IMAGE_RE.finditer(raw):
            images.append((i, im.group("alt"), im.group("path")))
        cm = CAPTION_RE.match(raw)
        if cm:
            figure_numbers.append((i, int(cm.group(1))))

        prose = strip_inline(raw)
        prose_lines.append((i, prose))
        body_text_positions.append((i, raw))
        if not hm and not stripped.startswith("|") and not stripped.startswith("!["):
            paragraph.append((i, prose))
    flush_par()

    # ---- punctuation and forbidden glyphs (prose only)
    for i, prose in prose_lines:
        is_h1 = lines[i - 1].startswith("# ")
        for ch, name in FORBIDDEN_PUNCT.items():
            if ch in prose:
                if ch == "·" and i in table_lines:
                    continue  # middle dots inside tables are tolerated
                if ch == "–" and is_h1:
                    continue  # series marker in the title (aws-blog-conventions.md §2)
                rep.add("error", i, "E1", f"{name} in prose")
        if i not in table_lines and ARROW_RE.search(prose):
            rep.add("error", i, "E1", "arrow in prose (allowed only in code blocks and tables)")
        if EMOJI_RE.search(prose):
            rep.add("error", i, "E1", "emoji or check mark in prose")
        if DOUBLE_HYPHEN_RE.search(prose):
            rep.add("error", i, "E1", "'--' used as a dash")
        if "~" in prose and i not in table_lines:
            # allow numeric ranges only
            residual = TILDE_OK_RE.sub("", prose)
            if "~" in residual:
                rep.add("warn", i, "W1", "'~' outside a numeric range")
        if "!" in prose and i not in table_lines and not prose.lstrip().startswith("!"):
            rep.add("warn", i, "W1", "exclamation mark in prose")
        for bm in BOLD_RE.finditer(prose):
            rep.add("warn", i, "W1", f"bold on a long phrase: '{bm.group(1)[:30]}...'")

    # ---- service naming
    if service_check:
        for i, raw in body_text_positions:
            for wm in WRONG_AMAZON_AS_AWS.finditer(raw):
                rep.add("error", i, "E2", f"'{wm.group(0)}' should be 'Amazon {wm.group(1)}'")
            for wm in WRONG_AWS_AS_AMAZON.finditer(raw):
                rep.add("error", i, "E2", f"'{wm.group(0)}' should be 'AWS {wm.group(1)}'")
            for tm in TRANSLITERATIONS.finditer(raw):
                rep.add("error", i, "E2", f"Korean transliteration '{tm.group(0)}'; write the English service name")
            for sm in SUBSERVICE_MISNAMES.finditer(raw):
                rep.add("warn", i, "W2", f"'{sm.group(0)}': AgentCore sub-services are 'AgentCore {sm.group(1)}'")
        body = "\n".join(raw for _, raw in body_text_positions)
        # skip the H1 line for first-mention check: title mentions do not count as introductions
        body_wo_title = re.sub(r"^# .*$", "", body, count=1, flags=re.M)
        for short, full in FULL_NAMES.items():
            sm = re.search(r"(?<![A-Za-z])" + re.escape(short) + r"(?![A-Za-z])", body_wo_title)
            if not sm:
                continue
            fm = body_wo_title.find(full)
            if fm == -1 or fm > sm.start():
                line_no = body_wo_title[: sm.start()].count("\n") + 1
                # map back to original line: title removal keeps line count
                rep.add("warn", line_no, "W2", f"'{short}' appears before its full name '{full}' is introduced")

    # ---- images and captions
    base = path.parent
    caption_lines = {ln for ln, _ in figure_numbers}
    for i, alt, p in images:
        if not alt.strip():
            rep.add("error", i, "E3", "image without alt text")
        if not p.startswith("http") and not (base / p).exists():
            rep.add("error", i, "E3", f"image file not found: {p}")
        # caption must appear within the next 3 lines
        window = [j for j in range(i + 1, min(i + 4, len(lines) + 1))]
        if not any(j in caption_lines for j in window):
            rep.add("error", i, "E3", "image without a '그림 N.' caption on the following line")
    nums = [n for _, n in figure_numbers]
    if nums != list(range(1, len(nums) + 1)):
        rep.add("warn", figure_numbers[0][0] if figure_numbers else 0, "W3",
                f"figure numbers are not sequential: {nums}")
    # placeholders for images count as figures too; check that 이미지 필요 placeholders carry a caption hint
    # (informational only)

    # ---- placeholders
    text = "\n".join(lines)
    placeholders = []
    for pm in PH_SPAN_RE.finditer(text):
        line_no = text[: pm.start()].count("\n") + 1
        tag = pm.group("tag")
        style = pm.group("style").replace(" ", "")
        req = re.sub(r"\s+", " ", pm.group("text")).strip()
        if PH_STYLE[tag].replace(" ", "") not in style:
            rep.add("error", line_no, "E5", f"[{tag}] span has the wrong colour style; expected {PH_STYLE[tag]}")
        if len(req) < 15:
            rep.add("error", line_no, "E5", f"[{tag}] placeholder does not describe what should go there")
        placeholders.append((line_no, tag, req))
    span_positions = {text[: m.start()].count("\n") + 1 for m in PH_SPAN_RE.finditer(text)}
    for tm in PH_TAG_RE.finditer(text):
        line_no = text[: tm.start()].count("\n") + 1
        if line_no not in span_positions:
            # bare tag allowed only inside a heading or a caption
            line = lines[line_no - 1]
            if not (HEADING_RE.match(line) or CAPTION_RE.match(line)):
                rep.add("error", line_no, "E5", f"bare {tm.group(0)} outside a coloured span (see references/placeholders.md)")

    # ---- vocabulary, constructions, metaphors (warnings)
    for i, prose in prose_lines:
        if i in table_lines:
            continue
        for w in BANNED_VOCAB:
            if w in prose:
                rep.add("warn", i, "W4", f"banned vocabulary '{w.strip()}'")
        for w in METAPHORS:
            if w in prose:
                rep.add("warn", i, "W4", f"figurative noun '{w}'; write the literal thing (voice.md §1.3)")
        if FIGURATIVE_AXIS_RE.search(prose):
            rep.add("warn", i, "W4", "'축' as a workstream or path; write 경로 / 구성 / 부분 (voice.md §1.3)")
        for rx, msg in CONSTRUCTIONS:
            if rx.search(prose):
                rep.add("warn", i, "W5", msg)
        if HEADING_RE.match(lines[i - 1]):
            continue
        for pm in PERSONIFICATION_RE.finditer(prose):
            rep.add("warn", i, "W9", f"abstract noun as actor: '{pm.group(0)[:40]}'; make the team, service, or reader the subject (voice.md §1.1)")
        for am in AGENTIVE_PASSIVES.finditer(prose):
            rep.add("warn", i, "W9", f"passive '{am.group(0).strip()}' with an available actor; name who does it (voice.md §1.2)")
    # soft vocabulary: only when frequent
    soft_counts = defaultdict(int)
    for _, prose in prose_lines:
        for w in SOFT_VOCAB:
            soft_counts[w] += prose.count(w)
    for w, c in soft_counts.items():
        if c >= 3:
            rep.add("warn", 0, "W4", f"'{w}' used {c} times; name the items or the mechanism instead")
    conn_counts = defaultdict(int)
    for _, prose in prose_lines:
        for w in CONNECTIVES:
            conn_counts[w] += prose.count(w)
    for w, c in conn_counts.items():
        if c >= 4:
            rep.add("warn", 0, "W4", f"connective '{w.rstrip(',')}' used {c} times; at most once per section, prefer a cause clause")
    # per-paragraph '를 통해' and passive-ending density
    for par in paragraphs:
        joined = " ".join(p for _, p in par)
        if joined.count("를 통해") + joined.count("을 통해") >= 2:
            rep.add("warn", par[0][0], "W5", "'~를 통해' twice in one paragraph")
        passive_sentences = [s for s in split_sentences(joined) if PASSIVE_ENDING_RE.search(s)]
        if len(passive_sentences) >= 2:
            rep.add("warn", par[0][0], "W9", f"{len(passive_sentences)} passive-ending sentences in one paragraph; name the actor (voice.md §1.2)")
        if len(joined) > 80 and not re.search(r"[가-힣]", joined) and not joined.strip().startswith(("-", "*", "|", "[")):
            rep.add("warn", par[0][0], "W7", "English-only paragraph in a Korean post")

    # ---- sentence length
    for i, prose in prose_lines:
        if i in table_lines or HEADING_RE.match(lines[i - 1]):
            continue
        for s in split_sentences(prose):
            if len(s) > 110:
                rep.add("warn", i, "W8", f"sentence of {len(s)} characters; split it")

    # ---- numbers needing a claim or fact
    for i, prose in prose_lines:
        if i in table_lines:
            continue
        for nm in NEEDS_CLAIM_RE.finditer(prose):
            rep.add("info", i, "I1", f"number '{nm.group(0)}' must trace to a fact ID or a claim row")

    # ---- leftover fact-id comments
    for i, raw in body_text_positions:
        if FACT_ID_RE.search(raw):
            rep.add("error" if final else "info", i, "E7" if final else "I2",
                    "fact-ID comment still present" + (" (strip before delivery)" if final else ""))

    return rep, placeholders, code_fence_count


def write_placeholders(placeholders, out: Path, draft: Path):
    by_tag = defaultdict(list)
    for ln, tag, req in placeholders:
        by_tag[tag].append((ln, req))
    md = [f"# 남은 placeholder ({len(placeholders)}개)", "", f"초안: `{draft.name}`", ""]
    for tag in PH_TAGS:
        items = by_tag.get(tag, [])
        md.append(f"## [{tag}] ({len(items)}개)")
        md.append("")
        if not items:
            md.append("없음")
        for ln, req in items:
            md.append(f"- L{ln}: {req}")
        md.append("")
    out.write_text("\n".join(md), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("draft")
    ap.add_argument("--placeholders-out")
    ap.add_argument("--strict", action="store_true", help="treat warnings as errors")
    ap.add_argument("--final", action="store_true", help="delivery mode: leftover fact-ID comments are errors")
    ap.add_argument("--no-service-check", action="store_true")
    ap.add_argument("--quiet-info", action="store_true", help="hide info lines")
    args = ap.parse_args()

    path = Path(args.draft)
    if not path.exists():
        print(f"not found: {path}", file=sys.stderr)
        return 2
    rep, placeholders, fences = lint(path, args.final, not args.no_service_check)

    order = {"error": 0, "warn": 1, "info": 2}
    for f in sorted(rep.findings, key=lambda f: (order[f.level], f.line)):
        if f.level == "info" and args.quiet_info:
            continue
        print(f"{f.level.upper():5} L{f.line:<4} {f.code}  {f.msg}")

    print()
    print(f"placeholders: {len(placeholders)} "
          + ", ".join(f"[{t}] {sum(1 for _, tag, _ in placeholders if tag == t)}" for t in PH_TAGS))
    print(f"code blocks: {fences} (each needs a row in 05-claims.md)")
    print(f"errors: {rep.count('error')}  warnings: {rep.count('warn')}  info: {rep.count('info')}")

    if args.placeholders_out:
        out = Path(args.placeholders_out)
        write_placeholders(placeholders, out, path)
        print(f"placeholder list written to {out}")

    if rep.count("error") or (args.strict and rep.count("warn")):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
