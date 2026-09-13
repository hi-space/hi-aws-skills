# 이벤트 기반 주문 처리 파이프라인

모바일 앱의 주문이 하나의 REST API로 들어와 큐에 쌓이고, 저장된 뒤 결제·재고 두 단계의 saga로 처리되어 고객에게
알림으로 끝나는 시스템이다. 요청 경로는 왼쪽에서 오른쪽으로 — Mobile client → API Gateway → SQS → Order handler →
Step Functions — 흐르고, 데이터는 DynamoDB(주문), S3(보관), 고객의 메일함에 놓인다.

![이벤트 기반 주문 처리 파이프라인](order-pipeline.drawio.png)

## 다이어그램 읽는 법
- **API & Ingestion** — 비즈니스 로직 전에 요청이 거치는 것들: API, 인증기, 주문 큐와 그 dead-letter 큐.
- **Order processing** — 주문 하나를 책임지는 Lambda와 그것이 쓰는 테이블.
- **Payment & inventory workflow** — Step Functions saga와 두 개의 task Lambda.
- **Notification**, **Observability**, **Archive** — 각각 서비스 하나: 상태·지표·이력이 가는 곳.
- **선** — 실선 = 동기 호출, 점선 = 비동기·보조. 선 위의 글자가 그 홉에서 **무엇이 흐르는지**(브리프의 What flows)이고,
  아래 단계마다 같은 글자를 `라벨`로 인용했으니 그림에서 그 화살표를 찾으면 된다. 단계 번호는 브리프 관계표의 `#` 순서다.
- Mobile client와 Customer는 AWS Cloud 상자 밖에 있다.

## 단계별 흐름
1. **Mobile client → API Gateway** — 앱이 REST 엔드포인트를 HTTPS로 호출한다. API Gateway가 TLS를 종료하고 요청
   형식을 검증하고 스로틀링한다. (라벨 `order requests`)
2. **API Gateway → SQS** — 주문을 메시지로 큐에 넣고 클라이언트에는 즉시 202를 돌려준다. 이 큐가 비동기 경계라서
   뒤쪽 처리가 느려져도 주문 접수는 계속된다. (라벨 `order message`)
3. **API Gateway → Cognito** — 모든 호출에서 bearer 토큰을 검증한다. 점선: 요청 데이터 경로의 한 홉이 아니라 요청
   옆에서 도는 검사다. (라벨 `token validation`)
4. **SQS → Order handler** — Lambda가 큐를 배치로 폴링한다. (라벨 `batch poll`)
5. **Order handler → DynamoDB** — 주문을 orders 테이블에 먼저 쓴다. saga는 항상 저장된 레코드를 기준으로 돈다.
   (라벨 `put order`)
6. **Order handler → Step Functions** — 주문마다 Step Functions 실행(saga) 하나를 시작한다. (라벨 `start saga`)
7. **Step Functions → Payment** — 결제 Lambda를 task로 호출한다. 꺾인 선의 위쪽 다리에 글자가 있다; 8번과 같은
   종류의 task 호출이다. 재시도와 보상(compensation)은 state machine이 맡는다 — 두 단계를 직접 이어 붙이지 않은
   이유다. (라벨 `task invoke`)
8. **Step Functions → Inventory** — 재고 예약 Lambda를 task로 호출한다. (라벨 `task invoke`)
9. **Step Functions → SNS** — saga가 끝나면(성공이든 보상된 실패든) 결과를 order-status 토픽에 발행한다.
   (라벨 `post status`)
10. **SNS → Customer** — 토픽이 이메일·푸시 구독으로 팬아웃한다. 점선: 비동기이고 요청 경로 밖이다. (라벨 `email / push`)
11. **API Gateway → CloudWatch** — API 지표와 접근 로그가 CloudWatch로 흐른다. Lambda들도 로그를 쓰지만 대표 엣지
    하나(API)만 그렸다. 점선·보조. (라벨 `metrics, logs`)
12. **DynamoDB → S3** — 주기적인 point-in-time export로 orders 테이블을 S3에 보관한다. 이 export는 테이블에
    point-in-time recovery가 켜져 있어야 한다(그림이 보여줄 수 없는 테이블 설정). 점선·보조. (라벨 `PITR export`)
13. **SQS → SQS (DLQ)** — `maxReceiveCount`를 넘겨 계속 실패하는 메시지는 무한 재시도 대신 dead-letter 큐로 옮긴다.
    Architecture review R1로 추가되었다. 점선·보조. (라벨 `messages that exceed maxReceiveCount`)

## 서비스
| 서비스 | 이 시스템에서의 역할 | 비고 |
|---|---|---|
| Mobile client | 고객의 앱; API의 유일한 호출자 | 클라우드 밖 |
| API Gateway | REST 진입점, 요청 검증, 스로틀링 | |
| Cognito | API의 JWT 인증기 | 점선: 홉이 아닌 옆 검사 |
| SQS (orders) | 주문 큐; API와 처리 사이의 버스트 완충 | |
| SQS (DLQ) | 주문 큐의 dead-letter 큐 | review R1로 추가 |
| Lambda (Order handler) | 검증·저장·워크플로 시작 | |
| DynamoDB (orders) | 주문 테이블; handler가 쓰고 workflow와 export가 읽음 | |
| Step Functions | 결제·재고 saga; 재시도와 보상 담당 | Standard workflow (review R3) |
| Lambda (Payment) | saga의 결제 단계 | |
| Lambda (Inventory) | saga의 재고 예약 단계 | |
| SNS (order status) | 주문 상태 토픽 | |
| User (Customer) | 알림 수신자 | 클라우드 밖 |
| CloudWatch | 지표·로그·알람 | 대표 엣지 하나만 그림 |
| S3 (order archive) | 주문 테이블의 보관소 | DynamoDB export가 채움 |

## 설계 결정
- 결제와 재고를 별도의 Lambda 두 개로 그려 saga를 보이게 했다; 더 큰 워크플로라면 Lambda를 더 늘리는 대신 상세
  페이지로 옮긴다.
- CloudWatch는 현행 아이콘 `cloudwatch_2`를 쓴다.
- **R1 수정** — 주문 큐에 dead-letter 큐를 추가했다(`sqs → dlq`, `redrive`): event-source 레퍼런스가 SQS 소스에는
  DLQ / redrive policy를 "always" 전략으로 든다(aws-serverless skill, `references/event-sources.md`).
- **R2 v1 수용** — API Gateway 앞에 AWS WAF가 아직 없다; API가 프로덕션에서 공개될 때 추가한다(출처: API Gateway
  security whitepaper, "AWS WAF integration",
  https://docs.aws.amazon.com/whitepapers/latest/security-overview-amazon-api-gateway/security-design-principles.html).
- **R3 v1 수용** — 결제 단계가 멱등하지 않으므로 saga는 Standard workflow로 돈다; state machine 설정이라 그리지
  않았다(출처: aws-serverless skill, `references/orchestration.md` § Standard vs Express).
- DynamoDB → S3 export에는 테이블의 point-in-time recovery가 필요하다(출처:
  https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/S3DataExport_Requesting.html).

## 이 다이어그램에 없는 것
- VPC·서브넷·IAM 역할 — 워크로드 전체가 서비스 레벨이고 VPC에 묶인 것이 없다.
- handler와 두 task Lambda의 CloudWatch 로깅 — 암묵적; API 엣지만 그렸다.
- CI/CD와 state machine의 ASL 정의.
