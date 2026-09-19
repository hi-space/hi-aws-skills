# feature-facts.md — 워크샵 AWS 기능 검증 사실표

> 연구 단계(2) 산출물. 이 워크샵(한빛페이 · Quick Desktop 사내 AI 업무 자동화, 2026-09-15 서울 온사이트)이
> **AWS 쪽에서** 다루는 Amazon Bedrock AgentCore / Amazon Bedrock 기능을 두 시나리오에 매핑하고,
> 각 기능의 **서울(ap-northeast-2) 가용성 · GA/preview · 신뢰도**를 정리한다.
>
> **범위 주의.** 이 표는 **AWS 백엔드 기능**만 다룬다. `docs/features/*`에 있는 Quick Desktop 앱 기능
> (Schedule, Activity Feed, Browser Automation 등)은 클라이언트 제품 계층이며 리전 검증 대상이 아니다.
> brief의 `aws.services = [Amazon Bedrock AgentCore, Amazon Bedrock Knowledge Bases]`가 검증 대상이다.

## 신뢰도 라벨 정의

| 라벨 | 뜻 |
| --- | --- |
| **검증됨** | 공식 AWS 문서(리전 지원표·릴리스노트)에서 이번(2026-08-27) 직접 확인, 또는 메인 루프가 웹으로 확인한 사실 |
| **문서** | 공식 문서에 적혀 있으나 값이 조건부·부분적이라 시나리오 적용 시 재확인 권장 |
| **추정** | 근거 있는 판단이지만 문서로 못 박지 못함 |
| **확인필요** | 아직 확인 안 됨. 청사진 확정 전 반드시 확인해야 하는 항목 |

확인 출처·일자는 문서 맨 끝 「출처」 참조. 공식 리전 지원표는 **2026-08-27 기준**이다(AWS는 수시로 리전을 추가하므로 배포 직전 재확인).

---

## 1. 시나리오 → 필요 기능 매핑 (요약)

| 시나리오 | tech level | 핵심 동작 | 실제로 필요한 AWS 기능 |
| --- | --- | --- | --- |
| **A. 매출 이상 탐지 자동화** | L200 | 일 180만 트랜잭션에서 이상 매출 SKU 자동 탐지·브리핑 | Runtime, Code Interpreter, Memory, **KB(내부 SKU/상품 맥락 RAG)**, 생성 FM, Observability, (Gateway) |
| **B. 정산 배치 보안 대응** | L300 | 정산 배치의 SSRF 침해 조사·대응 | Runtime, Code Interpreter, Gateway, **Identity(대응 액션 권한 스코프)**, **Policy(도구 인가)**, **KB(보안 런북 RAG)**, Memory, Observability |

두 시나리오 모두 **지식베이스(KB)** 를 쓴다 — 이 지점이 서울 제약의 핵심이다(§3, §4).

---

## 2. 기능별 검증 사실표

리전 열은 **서울(ap-northeast-2)** 기준. "Yes/No"는 2026-08-27 공식 리전 지원표 값.

| # | 기능 | 무엇인지 (1줄) | 서울 가용 | GA/Preview | 신뢰도 | 사용 시나리오 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | **AgentCore Runtime** (microVMs) | 에이전트를 관리형 HTTPS 엔드포인트로 호스팅하는 서버리스 런타임 | **Yes** | GA | **검증됨** | A, B (에이전트 실행 기반) |
| 1b | AgentCore **Runtime Instances** (배포 모드) | Runtime의 별도 인스턴스형 배포 옵션 | **No** (서울은 microVM만) | GA(타리전) | **검증됨** | 해당 배포 모드 선택 시만 |
| 2 | **AgentCore Gateway** | 에이전트가 외부 도구·API·Lambda를 MCP로 호출하도록 중개 | **Yes** | GA | **검증됨** | B(핵심), A(도구 연결) |
| 3 | **AgentCore Memory** | 단기 대화·장기 지식 메모리 계층 | **Yes** | GA | **검증됨** | A(과거 유사 이슈 연결), B(조사 맥락 유지) |
| 4 | **AgentCore Identity** | 에이전트에 스코프된 자격증명·아웃바운드 OAuth 인증 | **Yes** | GA | **검증됨** | B(대응 액션 권한 최소화), A |
| 5 | **Built-in Tools — Code Interpreter** | 샌드박스 Python 실행 환경 | **Yes** | GA | **검증됨** | A(트랜잭션 이상탐지 계산), B(로그 분석) |
| 6 | **Built-in Tools — Browser** | 관리형 클라우드 브라우저 제어 | **Yes** | GA | **검증됨** | A(외부 조회 옵션), B(제한적) |
| 7 | **AgentCore Observability** | 에이전트 트레이스·메트릭을 CloudWatch로 | **Yes** | GA | **검증됨** | A, B (감사·디버깅) |
| 8 | **Policy in AgentCore** | 에이전트–도구 상호작용의 세분화 인가(결정론적) | **Yes** | GA | **검증됨** | B(핵심: 대응 도구 통제), A |
| 9 | **Guardrails-in-Policy** | Policy 안에 Bedrock Guardrails를 결합 | **No** (IAD/London/Stockholm/Sydney/Tokyo만) | GA(제한 리전) | **검증됨** (메인루프) | B(원했다면 대체 필요) |
| 10 | **AgentCore Managed Knowledge Base** | 게이트웨이로 질의하는 완전관리형 RAG(6커넥터·자동싱크·관리형 벡터스토어) | **No** (지원: us-east-1·us-west-2·eu-west-1·eu-central-1·ap-southeast-2·eu-west-2·**ap-northeast-1(도쿄)**·govcloud) | GA | **검증됨** (메인루프; 공식 리전표에는 별도 행 없음 → 리전 목록은 메인루프 검증값) | A, B의 KB 후보(서울 불가) |
| 11 | **AgentCore Web Search Tool** | 게이트웨이 내장 웹검색 커넥터(웹 그라운딩) | **No** (IAD·Ireland·Tokyo만) | GA(제한 리전) | **검증됨** (리전표) | A(웹 그라운딩 필요 시 영향) |
| 12 | **AWS Agent Registry** | 거버넌스 에이전트/툴 카탈로그·크로스계정 공유 | **No** (IAD·Oregon·Ireland·Sydney·Tokyo) | GA(제한 리전) | **검증됨** (리전표) | B(에이전트 공유를 AWS로 매핑 시 영향) |
| 13 | **AgentCore Evaluations / Optimization** | 에이전트 품질 평가·최적화 | **Yes** | GA | **검증됨** | (워크샵 선택 확장) |
| 14 | **Amazon Bedrock Knowledge Bases (클래식/벡터스토어 RAG)** | 데이터소스→임베딩→벡터DB→Retrieve/RetrieveAndGenerate. 구조화 데이터스토어 NLQ 포함 | **Yes** (구조화 데이터스토어 NLQ도 서울 지원) | GA | **검증됨** (공식 docs) | A, B — **서울에서 KB 쓰려면 이쪽** |
| 15 | **Titan Text Embeddings V2** | 클래식 KB 임베딩 모델 | **Yes** (ap-northeast-2) | GA | **검증됨** (docs) | A, B(클래식 KB 임베딩) |
| 16 | **생성 FM (Claude / Nova 계열)** | 에이전트 추론·KB 응답 생성용 모델 | **확인필요** | — | **확인필요** | A, B (모델 미확정) |
| 17 | **Bedrock Guardrails (클래식 본체)** | 콘텐츠·토픽·PII 필터 | **확인필요** | — | **확인필요** | B(콘텐츠 통제 필요 시) |

---

## 3. KB 명칭 모호성 해소 — 청사진 확정용

brief의 `Amazon Bedrock Knowledge Bases`는 **두 개의 서로 다른 기능** 중 어느 쪽인지 모호했다. 검증 결과:

| 구분 | (구) **Bedrock 클래식 Knowledge Bases** | (신) **AgentCore Managed Knowledge Base** |
| --- | --- | --- |
| 정체 | Bedrock의 RAG — 데이터소스 인제스트 + 임베딩 + 벡터DB(OpenSearch Serverless/Aurora 등) + Retrieve/RetrieveAndGenerate API | AgentCore의 완전관리형 RAG — 게이트웨이로 질의, 6커넥터(S3·SharePoint·Confluence·Drive·OneDrive·WebCrawler)·자동싱크·관리형 벡터스토어 |
| **서울 가용** | **Yes (가능)** | **No (불가)** — 도쿄가 가장 가까운 지원 리전 |
| 손이 가는 정도 | 벡터스토어·인제스트를 직접 구성해야 함 | 커넥터만 붙이면 끝(관리형) |
| 신뢰도 | 검증됨 | 검증됨(메인루프) |

**결론(청사진 확정 권고):** 서울 온사이트 + 금융 데이터 레지던시를 고려하면 brief의 KB는
**(구) 클래식 Bedrock Knowledge Bases 로 확정 해석**한다. 모든 산출물에서 용어를 이 값으로 고정하고,
"AgentCore Managed KB는 서울 미지원이라 클래식 KB를 쓴다"는 각주를 슬라이드/문서에 명시한다.

---

## 4. 설계 함의 — 서울 제약이 시나리오 설계에 주는 영향

**(1) KB 선택이 시나리오 설계의 갈림길이다.** 두 시나리오 모두 내부 지식(A: SKU/상품 맥락, B: 보안 런북)을 RAG로 쓴다.
그런데 관리형이라 가장 편한 **AgentCore Managed KB가 서울에 없다.** 선택지는 셋:

- **(a) 클래식 Bedrock KB를 서울에서 사용 (권고).** 서울 가용성은 검증됨. 대신 관리형 RAG 파이프라인·6커넥터·자동싱크는 못 쓰고, 벡터스토어(OpenSearch Serverless 등)와 데이터소스 인제스트를 **직접 구성**해야 한다. 대가는 데모 세팅 손이 더 가는 것.
- **(b) Managed KB만 도쿄(ap-northeast-1)에 두고 크로스리전.** 관리형 편의는 얻지만 **데이터가 리전 경계를 넘는다.** 한빛페이는 간편결제 PG(금융·결제 데이터)라 데이터 레지던시가 민감하고, 지연·거버넌스를 별도로 설명해야 한다. 온사이트 90분 핸즈온에서 리스크.
- **(c) KB 없이 시나리오 축소.** 두 시나리오의 핵심(내부 지식 결합)을 훼손 → 비권장.

→ **권고: (a)**. 그래서 §3의 명칭 확정이 필요하다.

**(2) 통제(보안) 데모는 Guardrails가 아니라 Policy+Identity 축으로.** 시나리오 B(SSRF 침해 대응)는 "위험 도구를 막는다"를
보여주고 싶어진다. 하지만 **Guardrails-in-Policy가 서울 미지원**이다. 서울에서 결정론적으로 집행 가능한 것은
**AgentCore Policy(도구 인가, 서울 O) + Identity(권한 스코프, 서울 O) + IAM**이다. 이 조합을 B의 통제 축으로 삼는다.
콘텐츠/PII 필터가 꼭 필요하면 클래식 Bedrock Guardrails 본체의 서울 가용성을 **확인**해야 한다(현재 확인필요).

**(3) 서울에 없는 기능에 시나리오가 의존하지 않게 한다.** 공식 리전표 기준 서울 미지원:
**Managed KB · Guardrails-in-Policy · Web Search Tool · Agent Registry · Runtime Instances(배포 모드) · AgentCore payments.**
- 웹 그라운딩이 필요하면 AgentCore 내장 Web Search 대신 Quick의 브라우저/웹검색 기능으로 시연(클라이언트 계층).
- "에이전트 공유"는 AWS Agent Registry가 아니라 Quick 제품 기능으로 시연.

**(4) 서울에서 되는 것은 넉넉하다.** Runtime(microVM 서버리스)·Gateway·Memory·Identity·Built-in Tools(Browser·Code Interpreter)·
Observability·Policy·Evaluations 모두 서울 Yes(검증됨). 핸즈온 실행 자체는 서울 단일 리전으로 무리 없이 구성 가능.
단, **Runtime "Instances" 배포 모드는 서울 미지원**이므로 배포 방식은 microVM(서버리스)로 잡는다.

**(5) 남은 확인필요 항목 (청사진 확정 전 처리).**
- **생성 FM**: 에이전트 추론·KB 응답생성에 쓸 모델(Claude/Nova 등)을 서울 가용 모델 중에서 **지정하고 확인**. (임베딩은 Titan V2 서울 검증됨.)
- **Bedrock Guardrails(클래식 본체) 서울 가용성**: B에서 콘텐츠 필터를 쓸지 결정 후 확인.
- **리전표 재확인**: AWS는 리전을 수시 추가하므로 배포 직전(2026-09 초) 리전 지원표를 다시 확인.

---

## 출처

리전 지원표·릴리스노트는 **2026-08-27** 직접 확인. Managed KB 리전 목록과 Guardrails-in-Policy 서울 미지원은 메인 루프의 웹 검증값(검증됨).

- AgentCore 리전 지원표: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/agentcore-regions.html
- AgentCore 릴리스 노트(서울 Runtime/Tools/Observability 확장 명시): https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/release-notes.html
- 클래식 Bedrock KB 지원 모델·리전(구조화 데이터스토어 서울 포함, Titan Embed V2 ap-northeast-2): https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base-supported.html
