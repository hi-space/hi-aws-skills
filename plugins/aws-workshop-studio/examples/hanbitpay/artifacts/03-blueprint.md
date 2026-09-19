# 한빛페이 AgentCore 워크숍 청사진 (blueprint.md)

> 전제: 서울(ap-northeast-2)에서 실제로 되는 것만 씬에 넣었습니다 — AgentCore Runtime·Gateway·Memory·Identity·Code Interpreter·Browser·Observability·Policy·Evaluations, 그리고 brief의 "Bedrock Knowledge Bases"는 (구)클래식 KB로 확정해 사용합니다. AgentCore Managed KB·Guardrails-in-Policy·Web Search Tool·Agent Registry·Runtime "Instances" 배포모드는 서울에 없으므로 씬 설계에서 배제했고, 시나리오 B의 보안 통제는 Guardrails 대신 **Policy(도구 인가) + Identity(권한 스코프) + IAM**으로 짰습니다.

---

## 1. 시나리오 씬 분해

난이도는 ★(관찰·오리엔테이션) ~ ★★★★(승인 게이트·정량 평가가 얽히는 고난도)로 표시했고, 인접 씬끼리 1단계 이상 벌어지지 않게 배치했습니다.

### 시나리오 A — "매출 이상 탐지 자동화" (L200)

| 씬 | 제목 | 한줄 상황 | 사용 기능 | 난이도 |
|---|---|---|---|---|
| PRE | 준비 | 참가자가 에이전트를 기동하고, 일 180만 건 트랜잭션 중 최근 며칠 샘플이 이미 인덱싱돼 있는지 확인한다 | Runtime, (사전 인제스트된) 클래식 KB | ★ |
| Scene 1 | 이상 SKU 탐지 | "오늘 매출이 이상한 가맹점/카테고리 찾아줘" 한 문장으로 통계 이상탐지를 돌린다 | Code Interpreter | ★★ |
| Scene 2 | 원인 후보 좁히기 | 탐지된 이상 건에 대해 과거 유사 사례·업종 특성을 RAG로 조회해 "이게 사기인지 정상 급증인지" 후보를 좁힌다 | 클래식 KB(RAG) + Titan V2 임베딩 | ★★ |
| Scene 3 | 사실 확인 | 가맹점 공개 웹페이지에서 실제 프로모션 여부를 확인(Browser)하고, 내부 가맹점 시스템 mock API를 스코프된 자격증명으로 조회(Gateway+Identity)한다 | Browser, Gateway, Identity | ★★★ |
| Scene 4 | 자동 브리핑 | 지금까지 판단 과정을 Observability로 추적해 보여주고, 최종 브리핑을 생성해 Memory에 이슈로 남긴다(다음에 같은 가맹점 이슈가 또 뜨면 재사용) | Observability, Memory | ★★★ |
| Scene 5 | 신뢰성 검증 | "이 에이전트가 맞는 판단을 하고 있다는 걸 어떻게 아나"에 답한다 — Evaluations로 라벨링된 과거 케이스셋 대비 정확도를 측정하고, Policy로 "알림까지는 자동, 계좌 조치는 승인 필요" 경계를 보여준다 | Evaluations, Policy | ★★★★ |

### 시나리오 B — "정산 배치 보안 대응" (L300)

L300이라 PRE부터 A보다 한 단계 높게 시작합니다.

| 씬 | 제목 | 한줄 상황 | 사용 기능 | 난이도 |
|---|---|---|---|---|
| PRE | 인시던트 접수 | 정산 배치의 아웃바운드 호출 로그에서 이상 패턴(내부 메타데이터 엔드포인트 호출 시도) 알림을 받고 조사 에이전트를 기동한다 | Runtime, Observability | ★★ |
| Scene 1 | 증거 수집 | 배치 실행 로그와 모니터링 화면을 훑어 SSRF 흔적(허용되지 않은 목적지로의 아웃바운드 호출)을 확인한다 | Observability, Browser | ★★ |
| Scene 2 | 대응 절차 조회 | 사내 보안 런북·과거 유사 사고를 RAG로 조회해 "이 사고는 몇 단계 대응 절차를 밟아야 하는지" 체크리스트를 뽑는다 | 클래식 KB(RAG) | ★★★ |
| Scene 3 | 영향 범위 특정 | 에이전트가 전체 시스템에 무제한 접근하는 게 아니라, Identity가 발급한 임시 스코프 자격증명으로 Gateway가 허용한 도구만 써서 "이 사고로 영향받은 정산 배치·가맹점"을 특정한다 | Gateway, Identity, Memory | ★★★ |
| Scene 4 | 승인 기반 대응 | 에이전트는 "이 배치를 격리하고 키를 회전해야 한다"고 제안하지만, 비가역 액션이라 Policy의 도구 인가 게이트를 통과해야만(=사람 승인 필요) 실행되는 것을 확인한다. 마지막에 Evaluations로 이번 대응이 체크리스트를 다 지켰는지 자동 채점한다 | Policy, Evaluations | ★★★★ |

**왜 이렇게 나눴는가.** A는 "탐지 → 원인 파악 → 사실 확인 → 보고 → 신뢰성 검증"이라는 분석가의 자연스러운 사고 순서를 따라가면서 AgentCore 요소를 하나씩 얹었고, B는 A와 똑같은 기능 팔레트(KB·Gateway·Identity·Memory·Policy·Evaluations)를 재사용하되 "조사 대상이 보안 사고"라는 무게감 때문에 처음부터 한 단계 높게 시작해 마지막 승인 게이트에서 정점을 찍도록 짰습니다. 두 시나리오가 같은 서비스 조합을 다른 업무 맥락에 다시 쓰는 구조라, 참가자는 A에서 배운 도구를 B에서 "이번엔 보안 조사용으로" 다시 만나게 됩니다 — 학습 곡선이 완만해지는 대신, A를 건너뛰고 B만 하는 참가자에게는 Gateway/Identity/Policy가 낯설게 느껴질 수 있다는 점은 감안해야 합니다.

---

## 2. 기능 → 씬 매핑표 (flows.ts 내용)

두 시나리오가 같은 AgentCore 서비스를 공유하므로, 기능 페이지는 시나리오별로 중복 생성하지 않고 **하나의 카탈로그를 A/B 양쪽에서 참조**하는 구조를 제안합니다(quick-* 원본도 `Code Execution`처럼 A의 PRE 흐름에서 b-접두 기능을 그대로 참조한 전례가 있습니다).

### flowA

| Scene | steps (label → id) |
|---|---|
| PRE | Runtime → `agentcore-runtime` · Bedrock KB(사전 인제스트) → `bedrock-kb-classic` |
| Scene 1 | Code Interpreter → `agentcore-code-interpreter` |
| Scene 2 | Bedrock KB(RAG) → `bedrock-kb-classic` |
| Scene 3 | Browser → `agentcore-browser` · Gateway → `agentcore-gateway` · Identity → `agentcore-identity` |
| Scene 4 | Observability → `agentcore-observability` · Memory → `agentcore-memory` |
| Scene 5 | Evaluations → `agentcore-evaluations` · Policy → `agentcore-policy` |

### flowB

| Scene | steps (label → id) |
|---|---|
| PRE | Runtime → `agentcore-runtime` · Observability → `agentcore-observability` |
| Scene 1 | Observability → `agentcore-observability` · Browser → `agentcore-browser` |
| Scene 2 | Bedrock KB(RAG) → `bedrock-kb-classic` |
| Scene 3 | Gateway → `agentcore-gateway` · Identity → `agentcore-identity` · Memory → `agentcore-memory` |
| Scene 4 | Policy → `agentcore-policy` · Evaluations → `agentcore-evaluations` |

---

## 3. features/ 페이지 목록

기능 페이지도 A/B로 나누지 않고 10개 공통 카탈로그로 두고, 각 페이지에 `scenario: 'A' | 'B' | 'Both'`와 `scenes` 필드로 어디서 쓰였는지만 다르게 표시하는 걸 권합니다. 이렇게 하면 "Gateway가 뭔지"를 두 번 따로 설명하지 않아도 됩니다.

| id | 이름 | 시나리오 | 아이콘 후보 |
|---|---|---|---|
| `agentcore-runtime` | AgentCore Runtime | Both | `runtime`(신규 — microVM 상자 아이콘) |
| `agentcore-gateway` | AgentCore Gateway | Both | `connect` (기존 재사용) |
| `agentcore-identity` | AgentCore Identity | Both | `key`(신규) |
| `agentcore-memory` | AgentCore Memory | Both | `brain` (기존 재사용) |
| `agentcore-observability` | AgentCore Observability | Both | `analyze` (기존 재사용) |
| `agentcore-policy` | AgentCore Policy | Both | `shield`(신규) |
| `agentcore-evaluations` | AgentCore Evaluations | Both | `gauge`(신규) 또는 `check`(신규) |
| `agentcore-code-interpreter` | AgentCore Code Interpreter | 주로 A(B에서도 재사용 가능) | `code` (기존 재사용) |
| `agentcore-browser` | AgentCore Browser Tool | Both | `web` (기존 재사용) |
| `bedrock-kb-classic` | Bedrock Knowledge Bases (클래식) | Both | `knowledge` (기존 재사용) |

기존 quick-* 아이콘 세트 중 `notify`·`generate`·`proactive`·`research`·`trust`는 이번 카탈로그에서 자연스럽게 매칭되는 항목이 없어 제외했습니다. `runtime`·`key`·`shield`·`gauge` 4개는 새로 그려야 하는데, 이 4개는 AWS 공식 아이콘 세트에도 대응 아이콘이 있으니(AgentCore·IAM·CloudWatch 계열) 새로 디자인하기보다 공식 아이콘을 축약해 쓰는 쪽이 제작 공수가 덜 듭니다.

---

## 4. 데이터셋 요구사항

한빛페이(간편결제 PG, 일 180만 트랜잭션) 도메인에 맞춰 설계했습니다. 실제 운영 데이터는 절대 쓸 수 없으니 전부 합성 데이터이고, "실제소스"는 데모가 흉내내는 실제 시스템이 뭔지를 밝혀 참가자가 "이게 진짜라면 어디서 나온 데이터겠구나"를 감 잡게 하는 용도입니다.

### 시나리오 A

| 파일명 | 주요 컬럼 | 행수 | 실제 소스 vs 데모 대체 |
|---|---|---|---|
| `transactions_sample.csv` | transaction_id, merchant_id, category, amount, payment_method, channel, status, timestamp | 5~10만 행 (일 180만 건 중 통계적 이상 패턴 재현에 필요한 최소 샘플로 다운샘플) | 실제: 결제 게이트웨이 스트림/DB(Kinesis·DynamoDB) → 데모: 합성 CSV, 이상탐지 시연을 위해 급증/급감 케이스를 의도적으로 삽입 |
| `merchant_master.json` | merchant_id, name, category, region, signup_date, avg_daily_volume, risk_grade | 약 500건 | 실제: 가맹점 마스터 RDS → 데모: mock JSON |
| `past_anomaly_cases.json` (KB 인제스트) | case_id, date, merchant_id, symptom, root_cause, resolution, tags | 15~20건 | 실제: 리스크팀 CS 티켓/위키 → 데모: 합성 케이스, KB 청크 단위로 문서화 |
| `business_rules.md` (KB 인제스트) | (문서) 이상탐지 임계값, 정상 프로모션 판정 기준 | 1개 문서 | 실제: 내부 정책 위키 → 데모: 직접 작성한 markdown |
| `promo_calendar.json` | merchant_id, promo_name, start_date, end_date, expected_lift(%) | 30~50건 | 실제: 마케팅팀 프로모션 캘린더 시스템 → 데모: mock JSON (Scene 3의 Browser 시연용 가맹점 공개 웹페이지 내용과 짝을 맞춤) |

### 시나리오 B

| 파일명 | 주요 컬럼 | 행수 | 실제 소스 vs 데모 대체 |
|---|---|---|---|
| `settlement_batch_logs.json` | batch_id, run_time, status, outbound_calls[](url, response_code, latency), triggered_by | 200~500건(배치 실행 단위) | 실제: 정산 배치 애플리케이션 로그(CloudWatch Logs) → 데모: 합성 로그, SSRF 증거(내부 메타데이터 주소 호출 흔적)를 의도적으로 삽입 |
| `security_runbooks.md` (KB 인제스트) | (문서) SSRF 대응 절차, 사고 심각도 분류, 에스컬레이션 기준 | 1개 문서 | 실제: 보안팀 Confluence 런북 → 데모: 직접 작성한 markdown |
| `past_incident_cases.json` (KB 인제스트) | incident_id, type, root_cause, blast_radius, resolution_time, lessons | 8~12건 | 실제: 보안팀 IR(사고대응) 기록 → 데모: 합성 사례 |
| `affected_merchants.csv` | merchant_id, batch_id, settlement_amount, exposure_flag | 50~150행 | 실제: 정산 시스템 DB 조인 결과 → 데모: mock CSV, Scene 3 조사 결과로 노출 |
| `security_findings_mock.json` | finding_id, type, resource, severity, timestamp | 10~20건 | 실제: GuardDuty/CloudTrail 실 데이터 → 데모: mock JSON (실 GuardDuty 연동은 준비 공수 대비 데모 가치가 낮아 배제, 필요하면 Scene 1 Browser 시연에서 콘솔 캡처 슬롯으로만 노출) |

---

## 5. 다이어그램 목록

| # | 무엇을 | 도구 | 목적 |
|---|---|---|---|
| D1 | 전체 워크숍 아키텍처 개요 | drawio (공식 AWS 아이콘) | AgentCore 7종 + Bedrock 모델 + 클래식 KB(+벡터스토어)를 서울 리전 박스 안에 배치 |
| D2 | 시나리오 A 데이터 흐름 | mermaid (flowchart) | 트랜잭션 샘플 → Code Interpreter → KB RAG → Gateway/Identity → Memory → 브리핑 출력, Observability 트레이스를 오버레이로 표시 |
| D3 | 시나리오 B 조사 흐름 | mermaid (sequence) | 인시던트 알림 → 증거수집 → KB 런북 조회 → Gateway+Identity 스코프 조사 → Policy 승인 게이트 → 대응 실행 |
| D4 | 서울 리전 가용성 매트릭스 | drawio (표+아이콘 하이브리드) | AgentCore 컴포넌트별 서울 O/X, 클래식 KB vs Managed KB 위치 차이를 시각적으로 구분 |
| D5 | Policy/Identity/IAM vs Guardrails 개념 구분도 | mermaid (flowchart) | "왜 이 워크숍에는 Guardrails가 없는가"를 한 장으로 설명 |
| D6 | Identity 임시 스코프 자격증명 발급 흐름 | mermaid (sequence) | 에이전트 → Identity → 스코프 토큰 → Gateway 도구 호출, B의 승인 게이트 설명에 재사용 |

**서울 KB 제약을 아키텍처에 표기하는 방식.** 모든 다이어그램에서 범례를 하나로 통일합니다 — **실선 박스 = 서울(ap-northeast-2)에 실제로 배치**, **점선+회색 박스 = 참고용이며 이번 데모에서는 쓰지 않음**. D1·D4에서 클래식 Bedrock KB는 실선으로 "ap-northeast-2" 라벨을 붙이고, AgentCore Managed KB는 점선 회색 박스로 "ap-northeast-1(도쿄) — 서울 미지원, 이번 데모 미사용"이라고 못박아 둡니다. 참가자가 "왜 AgentCore Managed KB를 안 쓰고 옛날 방식 KB를 쓰냐"고 물었을 때 발표자가 이 한 장을 보여주며 답하면 되는 구조입니다.

---

## 6. 이미지 슬롯 개략 수

| 구분 | 대상 | 개수(대략) |
|---|---|---|
| 캡처 슬롯 (실제 AWS 콘솔/실행 결과 스크린샷) | 기능 페이지 10개 × 1장 | 10 |
| 캡처 슬롯 (씬별 실행 결과 화면) | A 5씬 + B 4씬 = 9씬 × 1장 | 9 |
| 생성 슬롯 (다이어그램, 5절 D1~D6) | drawio/mermaid | 6 |
| 생성 슬롯 (start 페이지 히어로/개요용 1장) | drawio 또는 mermaid | 1 |

**캡처 약 19장, 생성 약 7장.** 제품 스크린샷을 생성하지 않는 원칙은 그대로 지키되, 이번 워크숍은 소비자 앱이 아니라 AWS 콘솔·Observability 대시보드가 화면의 대부분이라 "캡처해야 할 화면"이 quick-* 워크숍보다 오히려 더 많습니다. 캡처 19장을 실습 전에 다 확보하지 못하면 씬 진행이 막히므로, 우선순위는 씬별 실행 결과(9장) > Policy 승인 게이트·Evaluations 리포트 화면(고난도 씬 2개) 순으로 잡는 걸 권합니다.

---

## 7. 열린 질문 (SA 결정 필요)

아래는 제가 임의로 정하지 않고 SA 판단을 받아야 하는 항목입니다. 확실한 것과 추정을 섞지 않으려고 일부러 결정하지 않았습니다.

- **생성 FM 모델 지정** — Claude/Nova 계열 중 서울(ap-northeast-2)에서 온디맨드로 실제 되는 정확한 모델 ID·버전을 배포 직전 재확인해야 합니다. 크로스리전 추론 프로파일이 필요한 모델이면 "서울에서 된다"는 말의 의미가 달라지니 이 부분도 같이 확인이 필요합니다.
- **클래식 Guardrails 본체의 서울 가용성** — "Guardrails-in-Policy"(Policy 안에 Guardrails를 끼워 쓰는 조합)는 서울 미지원이 확정됐지만, Bedrock의 클래식 Guardrails 리소스 자체를 서울에서 독립적으로 만들 수 있는지는 별도 확인 대상입니다. 시나리오 B에서 보조 통제로 얹을 수 있는지가 여기 달려 있습니다.
- **클래식 KB의 벡터스토어 선택** — OpenSearch Serverless / Aurora PostgreSQL(pgvector) / 신규 S3 Vectors 중 서울 가용성과 데모 세팅 공수가 가장 적은 조합을 정해야 합니다. 이건 단순 기술 선택이 아니라 "핸즈온 90분 안에 참가자가 직접 인제스트까지 돌려볼 수 있는가"를 좌우하는 선택이라, 세팅이 무거운 쪽을 고르면 발표자가 사전에 다 만들어 놓고 참가자는 조회만 하는 형태로 씬이 바뀔 수 있습니다.
- **Code Interpreter 이상탐지 로직의 수준** — Code Interpreter 안에서 z-score/이동평균 같은 단순 통계로 끝낼지, SageMaker 등 별도 서비스를 얹을지. 별도 서비스를 추가하면 그 서비스의 서울 가용성도 새로 확인해야 하는 연쇄 작업이 붙습니다.
- **시나리오 B의 "실물 재현" 범위** — 실제 인프라에 SSRF 취약점을 심어 라이브로 뚫어 보일지, 로그·데이터만으로 조사 흐름을 시뮬레이션할지. 전자는 준비 리스크와 안전 문제가 커서(L300 대상이라도) 90분 핸즈온에 넣기엔 부담이 클 수 있습니다 — 이 결정에 따라 씬 3~4의 실습 강도가 크게 달라집니다.
- **Evaluations의 채점 기준(ground truth)** — 합성 데이터라 "정답"을 임의로 정해야 하는데, 몇 개 항목·어느 수준 상세도로 정할지가 시나리오 A Scene 5, B Scene 4의 설득력을 결정합니다. 너무 단순하면 "그냥 정해놓은 답 맞추기"처럼 보이고, 너무 정교하면 준비 공수가 커집니다.
- **Policy 승인 게이트의 시연 방식** — 사람이 실제로 승인 버튼을 누르는 UI를 만들지, 정책이 막았다는 로그만 보여줄지. 전자가 체감은 훨씬 크지만 90분 안에 그 UI까지 만들 시간이 되는지는 SA가 판단해야 합니다.
- **3개 언어(ko/en/ja) 지원 범위** — 발표 진행은 한국어로 하고 문서·데이터셋만 3개 언어로 낼지, 발표 자체도 언어별로 따로 준비할지. 범위가 좁으면 준비는 가볍지만 en/ja 참가자의 현장 체감이 떨어지고, 범위가 넓으면 그 반대입니다.