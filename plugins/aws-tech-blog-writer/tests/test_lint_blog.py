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
