# hi-aws-skills

AWS 작업용 Agent Skills 모음입니다. Claude Code 플러그인 마켓플레이스로 설치하거나, `plugins/<name>/skills/<name>` 을 그대로 스킬 디렉터리에 복사·심링크해 Kiro 등 다른 런타임에서도 쓸 수 있습니다.

| 스킬 | 하는 일 | 문서 |
|---|---|---|
| [aws-diagram-design](plugins/aws-diagram-design/) | 공식 AWS Architecture Icons + Amazon Ember 스킨의 에디토리얼 다이어그램 27종을 HTML/SVG/PNG로 생성. draw.io·Mermaid 재작도. `scripts/pygen` Python 생성기로 한 레이아웃에서 ko/en PNG 세트를 일괄 생성 | [README](plugins/aws-diagram-design/README.md) · [SKILL.md](plugins/aws-diagram-design/skills/aws-diagram-design/SKILL.md) |

## 설치 (Claude Code)

```
/plugin marketplace add hi-space/hi-aws-skills
/plugin install aws-diagram-design@hi-aws-skills
/reload-plugins
```

원본 `aws-diagram-design@aws-diagram-design` 이나 `diagram-design` 플러그인이 켜져 있으면 같은 트리거에 스킬이 경쟁하므로 하나만 남기세요.

## 스킬 단독 설치 (슬래시 커맨드 없이)

```bash
git clone https://github.com/hi-space/hi-aws-skills.git
ln -s "$PWD/hi-aws-skills/plugins/aws-diagram-design/skills/aws-diagram-design" ~/.claude/skills/aws-diagram-design
```

## PNG 내보내기 사전 준비

```bash
pip install playwright && playwright install chromium
```

## 출처와 라이선스

`aws-diagram-design` 은 [masangbeom/aws-diagram-design](https://github.com/masangbeom/aws-diagram-design) 1.2.0 (MIT, [cathrynlavery/diagram-design](https://github.com/cathrynlavery/diagram-design) 기반)을 가져와 Python 생성기와 문서 작성 관례를 더한 것입니다. 라이선스와 서드파티 고지는 각 플러그인 디렉터리의 `LICENSE`, `THIRD_PARTY_LICENSES.md` 를 따릅니다. AWS Architecture Icons 는 [AWS 이용 약관](https://aws.amazon.com/architecture/icons/)에 따라 변형·재채색이 금지됩니다.
