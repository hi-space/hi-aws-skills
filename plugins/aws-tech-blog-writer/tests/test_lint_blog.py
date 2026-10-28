"""lint_blog.py findings must point at the right line of the draft."""
import re
import subprocess
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1]
LINT = PLUGIN / "skills" / "aws-tech-blog-writer" / "scripts" / "lint_blog.py"


def lint(path: Path) -> str:
    return subprocess.run(["python3", str(LINT), str(path), "--quiet-info"], capture_output=True, text=True).stdout


def test_first_mention_warning_reports_the_original_line_number(tmp_path):
    draft = tmp_path / "d.md"
    # blank lines and a code fence precede the short name; the lint must not count in a filtered copy
    draft.write_text(
        "# 제목\n"
        "\n"
        "도입 문장입니다.\n"
        "\n"
        "```bash\n"
        "echo hi\n"
        "```\n"
        "\n"
        "## 1. 구성\n"
        "\n"
        "Lambda 함수가 요청을 처리합니다.\n",
        encoding="utf-8",
    )
    out = lint(draft)
    m = re.search(r"WARN\s+L(\d+)\s+W2\s+'Lambda' appears before its full name", out)
    assert m, out
    assert int(m.group(1)) == 11, out


# ---- E8: first mention of an AWS service must link to its official documentation (conventions §9)

def _doc(body: str) -> str:
    return "# 제목\n\n" + body + "\n"


def test_unlinked_first_mention_is_an_error_at_the_right_line(tmp_path):
    draft = tmp_path / "d.md"
    draft.write_text(_doc("도입 문장입니다.\n\n## 1. 구성\n\nAmazon S3 버킷에 저장합니다.\n"), encoding="utf-8")
    out = lint(draft)
    m = re.search(r"ERROR L(\d+)\s+E8\s+first mention of 'Amazon S3' is not linked", out)
    assert m, out
    assert int(m.group(1)) == 7, out


def test_first_mention_linked_to_aws_docs_passes(tmp_path):
    draft = tmp_path / "d.md"
    draft.write_text(_doc(
        "[Amazon S3](https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html) 버킷에 저장합니다. "
        "S3 버킷은 두 개입니다.\n"), encoding="utf-8")
    out = lint(draft)
    assert "E8" not in out, out


def test_first_mention_linked_to_a_non_aws_page_is_an_error(tmp_path):
    draft = tmp_path / "d.md"
    draft.write_text(_doc("[Amazon S3](https://en.wikipedia.org/wiki/Amazon_S3) 버킷에 저장합니다.\n"), encoding="utf-8")
    out = lint(draft)
    assert re.search(r"E8\s+first mention of 'Amazon S3' links to en\.wikipedia\.org", out), out


def test_heading_and_caption_mentions_do_not_count_as_the_first_mention(tmp_path):
    draft = tmp_path / "d.md"
    (tmp_path / "fig1.png").write_bytes(b"")
    draft.write_text(_doc(
        "## 1. Amazon S3 구성\n\n"
        "![전체 구성](fig1.png)\n\n"
        "그림 1. Amazon S3 중심 구성\n\n"
        "[Amazon S3](https://aws.amazon.com/ko/s3/) 버킷에 저장합니다.\n"), encoding="utf-8")
    out = lint(draft)
    assert "E8" not in out, out


def test_a_prefix_service_is_checked_separately_from_its_sub_services(tmp_path):
    draft = tmp_path / "d.md"
    draft.write_text(_doc(
        "[Amazon Bedrock AgentCore](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/what-is-bedrock-agentcore.html) "
        "위에 올렸습니다.\n\n"
        "모델 호출은 Amazon Bedrock 를 씁니다.\n"), encoding="utf-8")
    out = lint(draft)
    assert "first mention of 'Amazon Bedrock AgentCore'" not in out, out
    assert re.search(r"ERROR L5\s+E8\s+first mention of 'Amazon Bedrock' is not linked", out), out


def test_first_mention_inside_a_longer_link_text_passes(tmp_path):
    draft = tmp_path / "d.md"
    draft.write_text(_doc(
        "[Amazon Bedrock AgentCore 개발자 가이드](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/) 를 따라 배포했습니다.\n"),
        encoding="utf-8")
    out = lint(draft)
    assert "E8" not in out, out


# ---- false positives found on a real draft during the aws-blog-review field run

def test_vpc_lattice_does_not_count_as_a_mention_of_amazon_vpc(tmp_path):
    draft = tmp_path / "d.md"
    draft.write_text(_doc("[Amazon VPC Lattice](https://aws.amazon.com/ko/vpc/lattice/) 기반 private endpoint를 구성했습니다.\n"),
                     encoding="utf-8")
    out = lint(draft)
    assert "first mention of 'Amazon VPC'" not in out, out


def test_managed_knowledge_bases_introduces_the_short_name(tmp_path):
    draft = tmp_path / "d.md"
    draft.write_text(_doc(
        "[Amazon Bedrock Managed Knowledge Bases](https://docs.aws.amazon.com/bedrock/latest/userguide/kb-managed.html) 를 썼습니다. "
        "Knowledge Bases 생성은 관리자만 합니다.\n"), encoding="utf-8")
    out = lint(draft)
    assert "'Knowledge Bases' appears before its full name" not in out, out
    assert "E8" not in out, out


def test_placeholder_text_is_not_prose_for_voice_and_link_checks(tmp_path):
    draft = tmp_path / "d.md"
    span = ('<span style="background-color:#FFF2CC;color:#7F6000;padding:1px 4px;">[작성자 확인] 운영 MS-SQL의 배치를 '
            '적어 주세요. 코드는 데모용 Amazon EC2 SQL Server 2022(새 Amazon VPC)와 기존 서버 연결 두 모드를 지원합니다. '
            '시연과 파일럿이 어느 모드였는지, 기존 서버라면 Lambda를 어느 VPC에 두었는지 한 문장으로 적으면 독자가 자기 환경과 '
            '비교할 수 있습니다.</span>')
    draft.write_text(_doc("본문 문장입니다.\n\n" + span + "\n"), encoding="utf-8")
    out = lint(draft)
    assert "해요체" not in out, out
    assert "W8" not in out, out
    assert "first mention of 'Amazon EC2'" not in out, out
    assert "first mention of 'Amazon VPC'" not in out, out
    assert "placeholders: 1 [작성자 확인] 1" in out, out


def test_image_alt_text_is_not_a_sentence_for_the_length_check(tmp_path):
    draft = tmp_path / "d.md"
    (tmp_path / "fig1.png").write_bytes(b"")
    alt = "전체 아키텍처: " + ", ".join(f"구성 요소 {i}" for i in range(30))
    draft.write_text(_doc(f"아래 그림 1은 전체 구성입니다.\n\n![{alt}](fig1.png)\n\n그림 1. 전체 구성\n"), encoding="utf-8")
    out = lint(draft)
    assert "W8" not in out, out


def test_w6_catches_every_sentence_heading_including_copula_and_colon_segments(tmp_path):
    headings = [
        "## 1. 개요: 챗봇 하나가 아니라 플랫폼이 필요했다",
        "### 1.1 범용 챗봇에 SQL을 붙이면 통제가 챗봇 밖에 남는다",
        "### 1.2 개인 도구 축과 업무 에이전트 축은 다른 경로다",
        "### 1.3 에이전트 운영 부담의 대부분은 인프라 영역이다: AgentCore를 선택한 이유",
        "### 3.1 Text-to-SQL: 에이전트 로직을 문서로 옮기다",
        "### 3.2 SAP: 기존 REST API와 사내 인증을 그대로 두고 연결하다",
    ]
    fine = [
        "## 2. 전체 아키텍처",
        "### 3.3 문서: Managed Knowledge Bases와 KB 전용 Gateway",
        "## 7. 핵심 교훈 (Key Takeaways)",
        "### 4.1 등록과 승인: AWS Agent Registry",
        "## 바다",
    ]
    body = "# 제목\n\n" + "\n\n본문입니다.\n\n".join(headings + fine) + "\n\n본문입니다.\n"
    p = tmp_path / "d.md"; p.write_text(body, encoding="utf-8")
    out = lint(p)
    w6 = [l for l in out.splitlines() if "W6" in l and "plain-form" in l]
    assert len(w6) == len(headings), out
    for h in fine:
        line = body.splitlines().index(h) + 1
        assert not any(f"L{line} " in l for l in w6), (h, w6)
