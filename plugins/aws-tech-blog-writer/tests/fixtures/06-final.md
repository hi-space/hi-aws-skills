# Amazon Bedrock AgentCore로 사내 Agent Platform 구축하기 – (1) 아키텍처

<span style="background-color:#D5E8D4;color:#1E5631;padding:1px 4px;">[인용 승인 필요] 고객사명 공개 여부를 확인해 주세요. 공개 불가 시 "국내 제조 기업 A사"로 표기합니다.</span>는 2025년 상반기에 PoC를 진행했습니다.

*Disclaimer: 본 글은 PoC 구현을 정리한 것으로, 특정 구성을 권고하는 것은 아닙니다.*

## 1. 문제: 팀마다 다른 LLM 접근 방식

`Amazon Bedrock`을 팀마다 직접 호출했습니다.

아래 그림 1은 전체 구성을 보여줍니다.

![Agent Platform 전체 아키텍처를 보여주는 다이어그램](images/fig1-arch.drawio.png)

그림 1. Amazon Bedrock AgentCore를 중심으로 구성한 전체 아키텍처

| 구성 요소 | 역할 | 선택 이유 |
|---|---|---|
| AgentCore Gateway | MCP 도구 노출 | 인증 위임 |
| AWS Lambda | 도구 실행 | 서버리스 |

```python
# gateway/handler.py
def handler(event, context):
    return {"ok": True}
```

Gateway는 <span style="background-color:#F8CECC;color:#9F0000;padding:1px 4px;">[기술 검증 필요] (C08) Lambda 타겟 호출 시 인증 방식(SigV4 여부)을 공식 문서에서 확인해 주세요.</span> 방식으로 호출합니다.

## 2. 결과

<p><span style="background-color:#FFF2CC;color:#7F6000;padding:1px 4px;">[작성자 확인] 결과 섹션. 파일럿 사용자 수와 기간, 정답률, 비용 중 확인 가능한 항목을 적어 주세요.</span></p>

<span style="background-color:#DAE8FC;color:#0B3D91;padding:1px 4px;">[이미지 필요] Registry 화면 캡처. 등록된 에이전트 목록이 보이도록 캡처해 주세요. 캡션: 그림 2. Registry 화면</span>

---

**저자 소개**

<span style="background-color:#FFF2CC;color:#7F6000;padding:1px 4px;">[작성자 확인] 이름은 AWS 직함으로, 전문 영역을 담당하고 있습니다.</span>
