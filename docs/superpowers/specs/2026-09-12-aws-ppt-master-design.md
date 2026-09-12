# aws-ppt-master 플러그인 설계

날짜: 2026-09-12
상태: 승인됨(2026-09-12), 구현 진행
위치: `plugins/aws-ppt-master/`

## 1. 목적

[hugohe3/ppt-master](https://github.com/hugohe3/ppt-master) 6.3.2(MIT)를 포크해 hi-aws-skills 마켓플레이스의 두 번째 플러그인으로 넣는다.
외부 모델 호출은 Amazon Bedrock 의 Stability 이미지 모델 하나만 남기고, AWS 기술 발표 자료를 자주 만드는 용도에 맞춰
[jesamkim/oh-my-skills myslide](https://github.com/jesamkim/oh-my-skills/tree/main/my-skills/myslide) 2.0.0(MIT)의
디자인 무관 요소 세 가지(한국어 카피 보이스 검사, AWS 아이콘 304개, PPTX 레이아웃 QA)를 이식한다.

시각 체계(색·타이포·레이아웃·전략가 규칙)는 ppt-master 원본을 그대로 쓴다. myslide 의 테마·패턴·브랜드 템플릿은 가져오지 않는다.

## 2. 확정된 결정

| 항목 | 결정 |
|---|---|
| 이름 | `aws-ppt-master` (플러그인, 스킬, 트리거 모두 동일) |
| 엔진 | ppt-master 의 SVG → 네이티브 DrawingML 파이프라인 그대로 |
| 이미지 생성 | Bedrock Stability 백엔드 하나. 다른 백엔드 15종 제거 |
| 나레이션·TTS·영상 | 라우트와 스크립트 전부 제거 |
| 이미지 분석·워터마크 제거 | 제거 (`analyze_images.py` 는 로컬 Pillow 지표만 내므로 유지) |
| 스톡 이미지 검색 | 제거 |
| attribution guard | 제거. 원저작자 고지는 `LICENSE` 와 `THIRD_PARTY_LICENSES.md` 로 유지 |
| myslide 디자인 스타일 | 채택하지 않음 |
| myslide 에서 이식 | 카피 보이스 검사, AWS 아이콘 304개, PPTX QA 검사 |

## 3. 레포 구조

```
hi-aws-skills/
  .claude-plugin/marketplace.json        # aws-ppt-master 항목 추가
  README.md                              # 스킬 표에 한 줄 추가
  plugins/aws-ppt-master/
    .claude-plugin/plugin.json           # name aws-ppt-master, version 1.0.0, author hi-space
    README.md                            # 설치·설정(AWS 자격 증명)·원본 대비 변경 요약
    UPSTREAM.md                          # 포크 기준 커밋, 제거·추가 목록
    THIRD_PARTY_LICENSES.md              # ppt-master(MIT, Hugo He), myslide(MIT, jesamkim), 아이콘 라이브러리, AWS 아이콘 출처
    requirements.txt                     # boto3 추가, google-genai·edge-tts 제거
    .env.example                         # Bedrock 블록만
    skills/aws-ppt-master/
      SKILL.md
      LICENSE                            # 원본 MIT 그대로
      workflows/                         # 원본 유지, 오디오·영상 스테이지 삭제
      references/                        # 원본 유지 + copy-voice.md 추가, 삭제 대상 제거
      scripts/                           # 원본 유지 + backend_bedrock.py, pptx_qa_check.py 추가
      templates/                         # 원본 유지 + icons/aws/ 추가
```

원본의 `skills/ppt-master/` 내부 배치를 그대로 두어 워크플로 문서의 상대 경로가 깨지지 않게 한다.
문서 안의 `skills/ppt-master/` 경로 접두어는 `skills/aws-ppt-master/` 로 일괄 치환한다.

## 4. 제거 목록

스크립트

- `scripts/image_backends/backend_{bfl,fal,gemini,ideogram,minimax,modelscope,openai,openrouter,qwen,replicate,siliconflow,stability,tencent,volcengine,zhipu}.py`
- `scripts/notes_to_audio.py`, `scripts/tts_backends/`, `scripts/narration_sync.py`,
  `scripts/powerpoint_video.py`, `scripts/video_motion_plan.py`, `scripts/video_sound_mix.py`, `scripts/video_subtitles.py`
  (`scripts/sound_sync.py` 와 `templates/sounds/` 는 애니메이션용 CC0 효과음 라이브러리로 외부 호출이 없어 유지)
- `scripts/image_search.py`, `scripts/image_sources/` (`image_treat.py` 가 쓰는 매니페스트 읽기·쓰기 함수 두 개는 `image_treat.py` 로 옮김)
- `scripts/gemini_watermark_remover.py`, `scripts/assets/bg_48.png`, `scripts/assets/bg_96.png`
- `scripts/attribution_guard.py`, `scripts/prompt_audit.py`, `scripts/prompt_audit_manifest.json`, `scripts/update_repo.py`
- `scripts/tests/test_image_backend_tencent.py`, `test_image_search.py`, `test_video_subtitles.py`

코드 수정

- `image_gen.py`: `BACKEND_REGISTRY` 를 bedrock 하나로, `IMAGE_ENV_PREFIXES` 에 `AWS_`·`BEDROCK_` 추가, `_BACKEND_PIP_HINTS` 에 boto3, 모듈 docstring 의 백엔드 목록 갱신, `IMAGE_BACKEND` 미설정 시 기본 `bedrock`
- 9개 진입 스크립트에서 `from attribution_guard import require_skill_integrity` 와 첫 호출 제거
- `console_encoding.py` 에서 `_require_official_distribution_identity` 제거

문서·템플릿

- `workflows/stages/generate-audio.md`, `references/video-design.md`, `references/image-searcher.md`, `references/executor-web-image.md`
- `SPONSORS.md`, `SPONSORS_CN.md`, `scripts/docs/narration.md`
- `references/executor-notes.md` 의 오디오 절, `scripts/docs/image.md` 의 백엔드별 절, `scripts/docs/troubleshooting.md` 의 google-genai·edge-tts 항목,
  `scripts/README.md` 의 해당 항목, `workflows/generate-pptx.md` 의 나레이션 분기
- `SKILL.md`: 메타데이터(`copyright`·`sponsors`·`official_repository`) 정리, Mandatory Load Order 2단계(guard) 삭제,
  description 에서 "narrated/self-running video" 제거, Repository Compatibility 의 스폰서 문단 삭제

라우팅 표에 남는 라우트: Generate(Default / Quick / Image-to-PPTX / Beautify), Create Template, Edit Native PPTX.

제거 뒤 `grep -rn` 으로 `notes_to_audio|tts_backends|image_search|IMAGE_BACKEND=(openai|gemini|…)|attribution_guard|SPONSORS|google-genai|edge_tts` 가 0건인지 확인한다.

## 5. Bedrock 이미지 백엔드

파일 `scripts/image_backends/backend_bedrock.py`. 원본 `backend_stability.py` 의 계약을 따른다.

```python
VALID_ASPECT_RATIOS = ["1:1", "16:9", "21:9", "3:2", "2:3", "4:5", "5:4", "9:16", "9:21"]
SUPPORTS_REFERENCE_IMAGE = False

def generate(prompt, aspect_ratio="1:1", image_size="1K", output_dir=None,
             filename=None, model=None, max_retries=MAX_RETRIES) -> str
```

- 호출: `boto3.client("bedrock-runtime", region_name=...)` → `invoke_model(modelId, body=json)`.
  본문은 `{"prompt", "aspect_ratio", "output_format": "png", "mode": "text-to-image", "seed"?, "negative_prompt"?}`.
  응답 `images[0]`(base64)을 디코드해 `backend_common.save_image_bytes` 로 저장.
- 모델: 기본 `stability.stable-image-core-v1:1`. `BEDROCK_IMAGE_MODEL` 로 `stability.stable-image-ultra-v1:1`, `stability.sd3-5-large-v1:0` 선택.
  `--model` 인자가 우선.
- 설정 키: `AWS_PROFILE`(선택), `AWS_REGION`(기본 `us-west-2`), `BEDROCK_IMAGE_MODEL`, `BEDROCK_NEGATIVE_PROMPT`, `BEDROCK_SEED`.
  자격 증명은 boto3 기본 체인(프로필, 환경변수, 인스턴스 롤)에 맡기고 키를 직접 읽지 않는다.
- `image_size`(1K/2K)는 Stability 모델이 받지 않으므로 수용만 하고 무시한다.
- 오류: `ThrottlingException`·`ServiceUnavailable` 은 `backend_common.retry_delay` 로 지수 재시도, `AccessDeniedException`·`ValidationException` 은
  즉시 실패하며 메시지에 모델 접근 활성화(Bedrock 콘솔 Model access)와 리전 안내를 포함한다.
- `.env.example` 은 Bedrock 블록만 남기고 한국어·영어 설명을 단다.

문서: `scripts/docs/image.md` 의 백엔드 절을 Bedrock 하나로 다시 쓰고, `references/image-generator.md` 의 `IMAGE_BACKEND` 언급을 갱신한다.

## 6. myslide 이식

### 6.1 카피 보이스 검사

- `references/copy-voice.md`: 규칙 6개(라벨 슬롯에는 답을, 메타 서술 금지, "A가 아니라 B" 데크당 1회, em/en dash 금지, 번역투 표, 영어 AI 어투), 재작성 브리프.
  myslide 원문에서 PptxGenJS 관련 문장만 뺀다.
- 검사 구현은 `scripts/pptx_qa_check.py` 의 `copy` 검사(6.3)로 통합한다. 별도 스크립트를 만들지 않는다.
- 워크플로 편입: `workflows/generate-pptx.md` Step 7(Check)과 Quick 프로필, Edit Native 의 검사 절에 "카피 패스 후 `pptx_qa_check.py --checks copy`" 를 추가.
  `references/executor-base.md` 의 텍스트 작성 규칙에 copy-voice.md 를 읽도록 트리거 한 줄.

### 6.2 AWS 아이콘 라이브러리

- `templates/icons/aws/` 에 myslide 아이콘 304개를 넣는다(서비스 248, AgentCore 변형 56). 파일명은 원본 소문자 하이픈 그대로.
- `templates/icons/README.md` 표에 `aws` 행 추가: "AWS 서비스 마크(공식 Architecture Icon Deck 스타일, 배경 사각형 포함, 색 고정) · `0 0 80 80` · `simple-icons` 와 같은 브랜드 마크 취급 → 스타일 라이브러리 하나와 공존 가능".
- `icon_sync.py` 의 공존 규칙에 `aws` 를 `simple-icons` 와 같은 예외 집합으로 추가.
- `references/executor-base.md` §4 아이콘 절에 "AWS 서비스를 그릴 때는 `aws/<service>` 를 쓰고 색을 바꾸지 않는다, 다크 배경에서 AgentCore 는 `-dark` 변형" 한 문단.
- `templates/icons/THIRD_PARTY_NOTICES.md` 에 AWS 아이콘 출처(AWS Architecture Icons, AWS 상표 가이드라인 준수) 추가.
- 공식 전체 세트(812개)가 필요하면 같은 마켓플레이스의 aws-diagram-design 자산을 `<project>/icons/custom/` 으로 복사해 쓰도록 README 에 안내.

### 6.3 PPTX 레이아웃 QA

- `scripts/pptx_qa_check.py`: myslide `qa_validate.py` 를 이식. python-pptx 로 `.pptx` 를 읽어 다음을 검사한다.

  | 검사 | 내용 | 수준 |
  |---|---|---|
  | `bounds` | 도형이 슬라이드 밖으로 나감 (배경 90% 이상 도형 예외) | critical |
  | `connectors` | 커넥터 끝점 슬라이드 밖, 길이 0.1in 미만 | warning |
  | `font_size` | 8pt 미만 critical, 본문 15pt 미만 warning (myslide 검출기 그대로) | |
  | `zero_size` | 폭 또는 높이 0 (선 예외) | warning |
  | `image_aspect` | 배치 비율과 픽셀 비율 2% 초과 불일치 | critical |
  | `copy` | 6.1 의 카피 보이스 정규식(한/영, 모노스페이스 런 제외) | dash·메타 라벨 critical, 나머지 warning |

  인터페이스: `pptx_qa_check.py <pptx> [--checks a,b,c] [--json] [--strict]`, 종료 코드 0/1/2.
- 기존 `pptx_delivery_check.py`(패키지 무결성·폰트·미디어) 와 역할이 겹치지 않으므로 둘을 나란히 Check 단계에 둔다.
- `scripts/tests/test_pptx_qa_check.py`: myslide 의 `test_ai_copy.py`(50 케이스)와 `test_qa_checks.py`(18 케이스)를 이식.

## 7. 문서

- `SKILL.md` frontmatter: `name: aws-ppt-master`, description 은 원본 트리거 + "AWS 기술 발표, 발표자료, 슬라이드 만들어, Bedrock 이미지" 추가.
  `metadata.version 1.0.0`, `base: ppt-master 6.3.2`, `source: https://github.com/hi-space/hi-aws-skills`.
- 플러그인 `README.md`(한국어, 영어 요약 포함): 설치 두 줄, `pip install -r requirements.txt`, AWS 자격 증명·리전·모델 접근 활성화, 원본 대비 변경 표, 라이선스.
- 루트 `README.md` 스킬 표와 `marketplace.json` 갱신.
- 원본 레포 루트의 `docs/`, `README_CN.md`, 스폰서 자료는 가져오지 않는다.

## 8. 검증

1. `python3 -m pytest scripts/tests` 통과(제거 대상 테스트 삭제 후, 이식 테스트 포함).
2. 모든 `scripts/*.py` 가 `--help` 로 기동(guard 제거 후 exit 78 없음).
3. 백엔드 단위 테스트: boto3 클라이언트 mock 으로 요청 본문·비율 검증·base64 디코드·스로틀 재시도. 실제 호출 1회: 이 계정 us-west-2 에서 Stable Image Core 16:9 한 장.
4. `claude plugin validate plugins/aws-ppt-master` 통과.
5. 남은 참조 grep 0건(§4).
6. 새 에이전트 테스트: 스킬 경로만 주고 "AWS 기술 발표 6장(Bedrock AgentCore 소개), 한국어" 과제. 확인 항목: 라우팅이 Generate Default 로 가는지, 이미지 생성 시 Bedrock 백엔드가 호출되는지, `aws/` 아이콘을 쓰는지, Check 단계에서 `pptx_qa_check.py` 를 돌리고 WARN 을 고치는지.

## 9. 범위 외

Amazon Polly, 참조 이미지(img2img) 편집, Confirm UI(Flask/JS) 내부 수정, myslide 의 테마·패턴·브랜드 템플릿·발표자 바이라인, 원본 중국어 문서, physical-ai-on-aws 프로젝트와의 연결.

## 10. 커밋 규칙

커밋과 푸시는 사용자가 요청할 때만 한다. Co-Authored-By 줄을 넣지 않는다. 작업분은 요청 시 하나의 커밋으로 합친다.

## 11. 부록 A (2026-09-12 추가 요구): 리서치 → 스토리라인 → 제작 → 리뷰 프로세스

사용자 요구: "처음부터 PPT 를 만들지 말고, deep-research 나 외부 검색으로 사실 검증을 명확히 하고, 스토리라인을 잡은 뒤 그것을 기반으로 PPTX 를 만들고, 만든 뒤 AI 어투와 기술 설명 완결성을 리뷰한다."
원본에 이미 있는 것: `workflows/stages/topic-research.md`(사실 ID `F001…` 를 가진 `<slug>.facts.json`, 주제만 있을 때만 실행, 충분하면 건너뜀), 전략가의 `design_spec.md §IX Content Outline`(페이지별 Core message + Fact IDs), 내보내기 뒤 `svg_quality_checker` / `pptx_delivery_check` / `pptx_qa_check`. 없는 것: 스토리라인 산출물과 게이트, 기술 정확성·AI 어투 리뷰.

### 11.1 사실 검증 게이트 (topic-research 강화)
- 실행 조건을 "기술 주장을 담는 모든 데크"로 확대한다. 주제만 있으면 전체 리서치, 문서가 있으면 문서 밖 주장(서비스 사양·수치·출시일·한도)에 대한 검증 패스. 건너뛰기는 사용자가 "출처는 내 문서만" 이라고 명시한 폐쇄 코퍼스일 때만.
- 도구 우선순위: 호스트에 `deep-research` 또는 `web-research` 스킬이 있으면 그것, 없으면 WebSearch/WebFetch, AWS 서비스 사실은 aws-docs MCP(`search_documentation`/`read_documentation`) 또는 docs.aws.amazon.com 을 1차 출처로. 출처마다 `retrieved_at` 기록.
- 산출물은 원본 계약 그대로(`sources/<slug>.md` + `<slug>.facts.json`). 검증 실패 주장은 facts.json 에 `classification: unverified` 로 남기고 슬라이드에서 제외하거나 `[확인 필요]` 로 표시한다.

### 11.2 스토리라인 게이트 (신규)
- 산출물 `analysis/storyline.md`: 청중과 그들이 내릴 결정, 핵심 명제 한 문장, 서사 흐름(3~5 비트), 슬라이드별 {주장, 근거 fact ID, 반드시 들어갈 기술 요소, 한계/반론}, 제외한 주제와 이유.
- 위치: 리서치 뒤, Confirm UI Stage 1 / 전략가 앞. Default 라우트에서는 ⛔ BLOCKING(사용자 확인), Quick 에서는 파일로 쓰고 채팅에 요약 제시 후 진행(🚧).
- 전략가의 §IX 각 페이지는 storyline 슬라이드 id 와 fact ID 를 인용해야 한다. `project_manager.py validate` 는 건드리지 않는다(스키마 변경 없음). `references/storyline.md` 에 템플릿·규칙(assertion-evidence, 슬라이드당 주장 하나, 제목을 본문에서 반복 금지)을 둔다. `artifact-ownership.md` 행 추가.

### 11.3 데크 리뷰 게이트 (신규)
- `scripts/deck_text_dump.py <pptx> [--out validation/deck_text.md]`: python-pptx 로 슬라이드별 제목·본문·표·노트, 그림·아이콘 개수를 마크다운으로 덤프. 리뷰어가 PPTX 를 직접 열지 않게 한다.
- `workflows/stages/deck-review.md` + `references/deck-review.md`: 내보내기·QA 게이트 뒤에 **새 컨텍스트의 리뷰어 서브에이전트**(경로만 전달: storyline.md, facts.json, deck_text.md, copy-voice.md)를 띄워 5개 항목을 PASS/FAIL 로 채점한다. (1) 기술 완결성: storyline 의 모든 주장·기술 요소가 슬라이드에 있는가. (2) 정확성: 수치·이름·한도가 facts.json 과 일치, 출처 없는 주장 없음. (3) AI 어투: copy-voice 규칙 + 채움말·3항 나열 남용·유행어(seamless/unlock/leverage/혁신적인/게임체인저)·제목 되풀이·빈 메타 라벨. (4) 청중 적합성: 수준, 약어 정의. (5) 구조: 한 슬라이드 한 메시지, 여는/닫는 슬라이드 역할.
- 결과 `validation/deck_review.md`. FAIL 항목은 소유 계층(스토리라인/SVG/노트)에서 고치고 재내보내기; 2회 반복 후에도 FAIL 이면 사용자에게 보고. Default·Quick·Edit Native 모두 필수.

### 11.4 폰트 대체
- `templates/brands/aws/templates/design_spec.md §III`: 제목·본문 Amazon Ember(600/400), 코드 Amazon Ember Mono; 대체 스택 Noto Sans(라틴)·Noto Sans KR(한글). 원본 규칙(스택은 라틴 1 + CJK 1, 내보내기는 첫 서체)을 지키므로 "설치 확인 후 첫 서체를 선택"하는 규칙을 `plan-core.md §6.2` 와 `shared-standards-core.md §4.1` 에 한 문단씩 추가: 저작 호스트나 전달 대상에 Amazon Ember 가 없으면(`fc-list | grep -i "Amazon Ember"`) Noto Sans / Noto Sans KR 을 선택하고 design_spec §IV 에 기록.

### 11.5 결과물 기반 반복 개선
- 새 에이전트 테스트를 같은 주제로 다시 돌려(리서치→스토리라인→제작→리뷰) 산출물(`deck_text.md`, `deck_review.md`, 렌더 PNG)을 직접 보고 SKILL.md·워크플로·참조를 고친다. skill-creator 의 `quick_validate.py` 로 구조 검증, SKILL.md 는 500줄 이하, "왜"를 설명하는 서술형 규칙 우선(대문자 MUST 남발 금지).
- 렌더: `pptx_to_svg.py` 로 SVG 를 뽑고 Playwright 로 PNG 를 만들어 눈으로 확인한다(LibreOffice 는 이 머신에서 PPTX 로드 실패).
