# AWS Tech Blog (Korea) conventions

Observed from posts published on aws.amazon.com/ko/blogs/tech in 2026 (LLM Gateway on Amazon Bedrock,
LG Energy Solution ERCOT agent on AgentCore, Samsung multi-datasource agent on AgentCore, GS SHOP AI-DLC,
Celltrion OMS with Kiro). Where posts differ, the safer choice is listed. Editors at AWS Korea will still
adjust the final copy; the goal here is a draft that needs no structural surgery.

## 1. Post types and section skeletons

Pick one type in the plan. Mixing types produces a post that neither tells a story nor teaches a build.

### A. Customer case study (고객 사례)

The customer is the protagonist; AWS services are the means. Numbers and quotes come from the customer.

```
(제목) <고객사>의 <AWS 서비스> 기반 <무엇> 구축기 / 구축 사례 / 운영 효율화 방안
(도입 단락 2~4개, 제목 없음)  고객 소개 한 문장, 풀려던 문제, 이 글이 다루는 범위
(Disclaimer, 필요 시)
## <문제를 나타내는 명사구 제목>      예: Trader의 반복 업무와 자동화 대상
## 솔루션 개요  또는  아키텍처        그림 1 (전체 아키텍처) + 구성 요소별 역할 설명
## 구현 상세  (H3로 구현 항목 3~5개)    항목마다: 무엇을, 왜 그렇게, 어떻게 (코드/설정 발췌)
## 결과                              정량 수치가 있으면 표로, 없으면 구조적 성과를 사실로만
## 향후 계획  (선택)
## 결론  또는  마무리
## 더 알아보기 / 참고 자료            공식 문서, GitHub, 관련 블로그 링크
(저자 소개: AWS 저자 + 고객사 저자)
```

### B. Implementation walkthrough (구현 가이드)

The reader will rebuild it. Every step has a checkable result.

```
(제목) <AWS 서비스>로 <무엇> 구축하기 / 배포하기 / 운영하기
(도입 단락)  무엇을 만들고, 왜 이 방식인지, 사전 지식
## 개요                              전체 그림 (그림 1) + 단계 요약 표
## 사전 준비                          계정 권한, 리전, CLI/SDK 버전, 비용 안내
## 1단계 ~ N단계  (H2 또는 H3)          단계마다: 목적, 명령/코드, 확인 방법
## 동작 확인  또는  테스트
## 리소스 정리                        만든 리소스를 지우는 순서 (비용 방지)
## 결론
## 더 알아보기
(저자 소개)
```

### C. Architecture deep dive (아키텍처 해설)

A design and the reasoning behind it. Numbered H2s, noun-phrase headings.

```
(제목) <AWS 서비스> 위에 <무엇> 구축하기: <부제로 다루는 구성 요소 3개>
(도입 단락)  이해관계자의 문제 진술(인용 가능), 배경, Disclaimer
## 1. 왜 지금 이 문제인가
## 2. 대안과의 차이                    오픈소스/직접 연결과 무엇이 다른가
## 3. 솔루션 아키텍처                  그림 1 + 컴포넌트 역할
## 4. ~ 6. 평면별 상세                  데이터 플레인, 컨트롤 플레인, 운영
## 7. 검증                            부하 테스트, 데모 결과
## 8. 정리                            도입 질문에 답으로 대응, 자가 점검 체크리스트(선택)
## 참고 자료
(저자 소개)
```

## 2. Title

- Korean sentence with English service names, ending in a noun or a verbal noun: `~ 구축하기`, `~ 운영하기`,
  `~ 구축기`, `~ 사례`, `~ 고도화 사례`, `~ 방안`.
- Contains the primary AWS service by its full name (`Amazon Bedrock AgentCore`, `Amazon EKS`).
- Customer posts lead with the company name (`LG에너지솔루션의 ...`, `셀트리온제약의 ...`).
- Subtitle after a colon is acceptable for deep dives (`...: 인증, 비용, 거버넌스`). Use a colon, not a dash.
- Series markers are the one accepted use of an en dash: `~ 구축하기 – (1) 데이터`, or a `Part 1:` prefix.
  The lint allows an en dash on the H1 line only.
- Under about 60 Korean characters. No question marks, no exclamation marks, no quotation marks.

## 3. Opening (before the first heading)

Two to four paragraphs, no heading. In order: the situation or a stakeholder's statement of the problem
(italic quote is a common device), why it matters now, what this post covers and for whom. State the
scope honestly ("이 글은 PoC 1단계 결과를 다룹니다").

Disclaimer, when the post describes a PoC, an internal implementation, or names third-party products:

> *Disclaimer: 본 글은 <조직>이 수행한 PoC 구현을 정리한 것으로, 특정 제품이나 구성을 권고하는 것은 아닙니다.
> 언급된 수치는 <시점> 기준이며, 각 조직의 환경에 맞게 검토하시기 바랍니다.*

Customer names, logos, screenshots, and quotes require the customer's approval; mark them
`[인용 승인 필요]` until the author confirms.

## 4. Voice and register

Sentence-level rules live in `voice.md`; the conventions that editors check are repeated here.

- `합니다`체 throughout. Never `해요`, never `~다.` plain form in body text.
- Headings are noun phrases (`3.2 SAP 에이전트: OpenAPI 타깃과 interceptor`), numbered in case studies
  and deep dives. Not sentences, not questions.
- Subject is the team or the organization (`경신홀딩스 정보전략팀은`, `AWS 팀은`), a service, or the post
  itself (`이 글에서는`). `저희는` only where a decision is attributed in a co-authored post. Avoid
  `우리`/`여러분`.
- Reader is addressed indirectly: `~할 수 있습니다`, `~를 권장합니다`. No `하세요` outside a step list;
  `다음 명령을 실행합니다` even there.
- Technical nouns stay in English inside Korean sentences: `Lambda 함수`, `IAM 역할`, `MCP 서버`. Korean
  transliteration (`람다`, `다이나모디비`) is wrong.
- Numbers use Arabic digits with Korean counters: `4주`, `2개 DB`, `27개 컴포넌트`. Percentages `35%`.
- Dates: `2026년 9월 8일`; ranges `7월~8월` (the only accepted use of `~`).

## 5. AWS service naming

Full official name at first mention in the body (the title counts as a mention only if the body also
introduces it). Later mentions may drop the prefix when unambiguous (`Bedrock`, `Lambda`), but keep the
full name when two services share a word (`Bedrock Knowledge Bases` vs `Bedrock AgentCore Memory`).

The prefix is part of the name and is not interchangeable. Common ones:

| Amazon ... | AWS ... | No prefix (third party or open source) |
|---|---|---|
| Amazon Bedrock, Amazon Bedrock AgentCore (Runtime, Gateway, Memory, Identity, Observability, Policy), Amazon Bedrock Knowledge Bases, Amazon Bedrock Guardrails | AWS Lambda, AWS Fargate, AWS Step Functions, AWS Glue | Claude, Claude Code, Codex, Strands Agents SDK, LangGraph, MCP (Model Context Protocol) |
| Amazon S3, Amazon DynamoDB, Amazon Aurora, Amazon RDS, Amazon ElastiCache, Amazon OpenSearch Service | AWS IAM, AWS IAM Identity Center, AWS Secrets Manager, AWS Systems Manager, AWS KMS | Kiro, Terraform, Kubernetes |
| Amazon EC2, Amazon ECS, Amazon EKS, Amazon ECR | AWS CloudFormation, AWS CDK, AWS WAF, AWS Network Firewall, AWS PrivateLink, AWS Transform | Microsoft Entra ID, SAP |
| Amazon API Gateway, Amazon CloudFront, Amazon Route 53, Amazon VPC, Amazon Cognito | AWS CloudTrail, AWS X-Ray, AWS Well-Architected Framework | |
| Amazon CloudWatch, Amazon EventBridge, Amazon SNS, Amazon SQS, Amazon SageMaker AI, Amazon Q Developer, Amazon QuickSight | | |

Elastic Load Balancing is `Elastic Load Balancing`; the resource is an `Application Load Balancer`.
`Amazon Bedrock AgentCore` may be shortened to `AgentCore` after first mention; its sub-services are
`AgentCore Gateway`, `AgentCore Runtime`, and so on, never `Bedrock Gateway`.
When unsure, search the service's documentation landing page title with the `aws-docs` MCP; the page
title is the canonical name.

Model names follow the vendor: `Claude Opus 5`, `Claude Sonnet 5`, `Claude Haiku 4.5`. Never invent a
version; if the source does not say, placeholder it.

## 6. Figures

- Every figure is introduced in the text before it appears (`아래 그림 1은 전체 구성을 보여줍니다.`).
- Caption on the line under the image, sequential numbering, no period at the end of a noun phrase:
  `그림 1. Amazon Bedrock AgentCore를 중심으로 구성한 전체 아키텍처`
- Alt text in the Markdown image is a plain description for screen readers, not the caption.
- Architecture figures come from `aws-drawio-diagram` (official icons, verified). Concept figures from
  `aws-diagram-design`. Screenshots the author must take are `[이미지 필요]` placeholders with a caption
  already written so the author knows what to capture.
- No text-heavy slides pasted as images. If a picture needs a paragraph to read, it becomes a table.

## 7. Code and configuration

- Fenced block with a language (`python`, `bash`, `json`, `yaml`, `hcl`, `sql`, `text`).
- First line inside the block is a comment naming the file or the context:
  `# gateway-proxy/src/app/middleware/auth.py` or `# 예: Lambda 핸들러 일부`.
- Show the smallest excerpt that makes the point (10 to 30 lines). Elide with `# ...` and say what was cut.
- Never show a snippet you did not take from a source or verify against the SDK/API reference. A
  plausible-looking `boto3` call with a wrong parameter name is the most common technical error in
  submitted drafts. Every code block therefore gets at least one row in `05-claims.md`.
- Secrets, account IDs, internal hostnames, and customer data are replaced with obvious placeholders
  (`<ACCOUNT_ID>`, `example.com`), and the replacement is mentioned once.

## 8. Tables

Use a table when three or more items share the same attributes (component / role / why chosen; before /
after; step / command / expected result). Header row in Korean, values may be English. No empty cells;
write `해당 없음`.

## 9. Links

- Official documentation: `[Amazon Bedrock AgentCore 개발자 가이드](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/)`.
  Link text names the document, not "여기" or "이 링크".
- GitHub repositories with the org (`awslabs/amazon-bedrock-agentcore-samples`).
- Other AWS blog posts by full title.
- Collect them again under `## 더 알아보기` or `## 참고 자료` at the end, as a bullet list.

## 10. Closing sections

- `## 결론` or `## 정리` (deep dives) or `## 결과` (case studies). Answers the question posed in the
  opening in two to four paragraphs. States what is next (production rollout, second phase) as fact or as
  a placeholder, not as a wish.
- Optional `핵심 교훈 (Key Takeaways)` before the conclusion: four generalisable one-sentence lessons.
- Optional `자가 점검 체크리스트`: five yes/no questions the reader can ask of their own environment.
- `## 더 알아보기`: links.
- Author bios, one sentence or two, third person:
  AWS: `<이름> <직함>는 <배경 경험>을 바탕으로 고객이 비즈니스 목표를 달성하도록 아키텍처 설계와 기술을 지원하고 있습니다.`
  Customer: `<이름> <사내 호칭>는 <팀>의 <직함>로서 <전문 분야>의 경험을 바탕으로 <담당 업무>를 담당하고 있습니다.`
  Verbatim examples in `voice.md` §2.8. Bios come from the author; until then they are `[작성자 확인]`
  placeholders with the pattern filled in.

## 11. What editors send back

- Marketing adjectives (`혁신적인`, `강력한`, `획기적인`) and unsourced superlatives.
- Claims about AWS behaviour without a documentation link.
- Architecture pictures with non-official icons or services that are not in the text.
- Customer data, names, or quotes without approval.
- English-only paragraphs, or Korean paragraphs that read as translated English (see
  `voice.md`).
- Posts over roughly 4,000 Korean characters of body text without a strong reason. A typical case study
  is 2,500 to 3,500 characters plus figures and code; deep dives run longer and are numbered.
