# hi-aws-skills

AWS 작업용 Agent Skills 모음입니다. Claude Code 플러그인 마켓플레이스로 설치하거나, `plugins/<name>/skills/<name>` 을 그대로 스킬 디렉터리에 복사·심링크해 Kiro 등 다른 런타임에서도 쓸 수 있습니다.

| 스킬 | 하는 일 | 문서 |
|---|---|---|
| [aws-diagram-design](plugins/aws-diagram-design/) | 공식 AWS Architecture Icons + Amazon Ember 스킨의 에디토리얼 다이어그램 27종을 HTML/SVG/PNG로 생성. draw.io·Mermaid 재작도. `scripts/pygen` Python 생성기로 한 레이아웃에서 ko/en PNG 세트를 일괄 생성 | [README](plugins/aws-diagram-design/README.md) · [SKILL.md](plugins/aws-diagram-design/skills/aws-diagram-design/SKILL.md) |
| [aws-drawio-diagram](plugins/aws-drawio-diagram/) | **편집 가능한 `.drawio` 파일**을 생성. draw.io 소스에서 재생성한 스텐실 카탈로그(1,000개+), 서비스/리소스 두 패턴 규칙, 레이아웃 관례, 템플릿 5종, 검증 스크립트, draw.io에 없는 아이콘(Bedrock AgentCore 리소스)의 SVG 폴백 | [README](plugins/aws-drawio-diagram/README.md) · [SKILL.md](plugins/aws-drawio-diagram/skills/aws-drawio-diagram/SKILL.md) |
| [aws-ppt-master](plugins/aws-ppt-master/) | ppt-master 포크. 문서·주제에서 네이티브 편집 가능한 PPTX 생성. AI 이미지는 Amazon Bedrock(Stability) 만 사용, PPTX 레이아웃·한국어 카피 보이스 QA, AWS 아이콘 304개 | [README](plugins/aws-ppt-master/README.md) · [SKILL.md](plugins/aws-ppt-master/skills/aws-ppt-master/SKILL.md) |
| [aws-tech-blog-writer](plugins/aws-tech-blog-writer/) | AWS 기술 블로그(한국어) 원고 작성. 6단계 파이프라인(리서치와 다이어그램, 팩트체크와 린트는 병렬), 초안은 최소 packet만 받은 새 컨텍스트의 서브에이전트가 작성, 은유·행위자 없는 피동·서술형 소제목을 걷어내는 스타일 패스, AWS 공식 문서 기반 사실 검증을 거쳐 **작성자 검토용 Word(.docx)** 로 전달. 작성자만 아는 사실은 4색 placeholder로 남김 | [README](plugins/aws-tech-blog-writer/README.md) · [SKILL.md](plugins/aws-tech-blog-writer/skills/aws-tech-blog-writer/SKILL.md) |
| [aws-workshop-studio](plugins/aws-workshop-studio/) | [workshop-scaffold](https://github.com/netsgo0319/workshop-scaffold) 포크. 주제·시나리오·대상 고객에서 **핸즈온 AWS 워크샵 한 벌**(quick-* VitePress 사이트, 시나리오 실습, 샘플 데이터셋)을 8단계 파이프라인으로 생성. **왜 이 아키텍처인지·서비스별 가치·도입 전후**를 개요 페이지에 필수로 담고(INV-9), 아키텍처 다이어그램은 `aws-diagram-design` 으로 그림. 레벨×직군 페르소나 리뷰와 참가자 워크스루 루프로 검수. 단독 스킬 `aws-fact-check`(GA/리전 사실 확인), `persona-review` 포함 | [README](plugins/aws-workshop-studio/README.md) · [SKILL.md](plugins/aws-workshop-studio/skills/workshop-scaffold/SKILL.md) |

**어느 쪽을 쓸까?** 문서·슬라이드·블로그에 넣을 완성된 그림이면 `aws-diagram-design`, draw.io에서 계속 편집할 `.drawio` 파일이 필요하면 `aws-drawio-diagram`. 기존 `.drawio`를 하우스 스타일로 **재작도**하는 것은 `aws-diagram-design`의 `/aws-diagram-design:import-drawio` 가 담당합니다. PPTX 발표자료 자체를 만들 때는 `aws-ppt-master` 를, AWS 기술 블로그 원고를 쓸 때는 `aws-tech-blog-writer` 를 씁니다(다이어그램은 두 다이어그램 스킬을 내부에서 호출). 고객 대상 핸즈온 워크샵 사이트를 만들 때는 `aws-workshop-studio` 를 씁니다.

## 설치 (Claude Code)

```
/plugin marketplace add hi-space/hi-aws-skills
/plugin install aws-diagram-design@hi-aws-skills
/plugin install aws-drawio-diagram@hi-aws-skills
/plugin install aws-ppt-master@hi-aws-skills
/plugin install aws-tech-blog-writer@hi-aws-skills
/plugin install aws-workshop-studio@hi-aws-skills
/reload-plugins
```

원본 `aws-diagram-design@aws-diagram-design` 이나 `diagram-design` 플러그인, 원본 `workshop-scaffold@workshop-scaffold-marketplace` 가 켜져 있으면 같은 트리거에 스킬이 경쟁하므로 하나만 남기세요.

## 스킬 단독 설치 (슬래시 커맨드 없이)

```bash
git clone https://github.com/hi-space/hi-aws-skills.git
ln -s "$PWD/hi-aws-skills/plugins/aws-diagram-design/skills/aws-diagram-design" ~/.claude/skills/aws-diagram-design
ln -s "$PWD/hi-aws-skills/plugins/aws-drawio-diagram/skills/aws-drawio-diagram" ~/.claude/skills/aws-drawio-diagram
ln -s "$PWD/hi-aws-skills/plugins/aws-ppt-master/skills/aws-ppt-master" ~/.claude/skills/aws-ppt-master
ln -s "$PWD/hi-aws-skills/plugins/aws-tech-blog-writer/skills/aws-tech-blog-writer" ~/.claude/skills/aws-tech-blog-writer
```

`aws-workshop-studio` 는 스킬이 플러그인 루트의 `references/`·`scripts/`·`assets/` 를 참조하고 커맨드·에이전트·훅을 함께 쓰므로 심링크 단독 설치가 아니라 플러그인으로 설치해야 합니다.

## PNG 내보내기 사전 준비

```bash
pip install playwright && playwright install chromium
```

## 출처와 라이선스

`aws-diagram-design` 은 [masangbeom/aws-diagram-design](https://github.com/masangbeom/aws-diagram-design) 1.2.0 (MIT, [cathrynlavery/diagram-design](https://github.com/cathrynlavery/diagram-design) 기반)을 가져와 Python 생성기와 문서 작성 관례를 더한 것입니다. 라이선스와 서드파티 고지는 각 플러그인 디렉터리의 `LICENSE`, `THIRD_PARTY_LICENSES.md` 를 따릅니다. AWS Architecture Icons 는 [AWS 이용 약관](https://aws.amazon.com/architecture/icons/)에 따라 변형·재채색이 금지됩니다.

`aws-drawio-diagram` 은 [vidanov/aws-architecture-diagram-skill](https://github.com/vidanov/aws-architecture-diagram-skill) (MIT, 커밋 `29c1bab`)을 기반으로, 아이콘 카탈로그를 draw.io 원본(`Sidebar-AWS4.js`, `stencils/aws4.xml`, Apache-2.0)에서 스크립트로 재생성하고 검증 스크립트와 SVG 폴백을 더한 것입니다.

`aws-workshop-studio` 는 [netsgo0319/workshop-scaffold](https://github.com/netsgo0319/workshop-scaffold) 0.2.6 (커밋 `50e370a`, 저장소에 라이선스 파일 없음)을 가져와 플러그인 이름과 설치 경로만 hi-aws-skills 에 맞춘 것입니다. 생성되는 모든 워크샵 페이지에는 원본 출처 표기가 유지됩니다. 변경 내역은 `plugins/aws-workshop-studio/UPSTREAM.md` 를 따릅니다.
