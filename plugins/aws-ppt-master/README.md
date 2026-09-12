# aws-ppt-master

[ppt-master](https://github.com/hugohe3/ppt-master) 6.3.2 를 포크해 AWS 기술 발표 자료 제작에 맞춘 Claude Code 플러그인입니다.
Markdown·문서·URL·주제에서 **네이티브로 편집 가능한 PPTX**(실제 DrawingML 도형·텍스트·표·차트·애니메이션)를 만듭니다.

원본과 다른 점

| 영역 | aws-ppt-master |
|---|---|
| AI 이미지 생성 | Amazon Bedrock 의 Stability AI Stable Image 만 사용 (API 키 없음, boto3 자격 증명 체인) |
| 나레이션·TTS·영상 | 제외 |
| 스톡 이미지 검색·워터마크 제거 | 제외 |
| QA | `scripts/pptx_qa_check.py`: 슬라이드 경계, 본문 15pt 하한, 이미지 비율, 커넥터, 한국어·영어 카피 보이스(em dash·메타 라벨·번역투) |
| 아이콘 | `templates/icons/aws/` AWS 서비스 마크 304개 (AgentCore 변형 포함) |
| 무결성 게이트·스폰서 자료 | 제거 (원저작자 고지는 LICENSE, THIRD_PARTY_LICENSES.md) |

## 설치

```
/plugin marketplace add hi-space/hi-aws-skills
/plugin install aws-ppt-master@hi-aws-skills
```

설치된 플러그인 디렉터리에서 Python 의존성을 설치합니다.

로컬 체크아웃을 설치 없이 그대로 쓰려면 세션을 이렇게 시작합니다.

```
claude --plugin-dir /path/to/hi-aws-skills/plugins/aws-ppt-master
```

```
pip install -r requirements.txt
```

## Bedrock 설정

1. Bedrock 콘솔(기본 리전 `us-west-2`) → Model access 에서 Stability AI 모델(Stable Image Core, Ultra, SD3.5 Large) 접근을 활성화합니다.
2. 자격 증명은 boto3 기본 체인을 따릅니다. `AWS_PROFILE` 또는 액세스 키, SSO, 인스턴스 롤 중 하나면 됩니다.
3. 선택 설정은 환경변수 또는 `.env`(예시: `.env.example`) 로 줍니다.

| 키 | 기본값 | 설명 |
|---|---|---|
| `AWS_REGION` | `us-west-2` | 모델을 서비스하는 리전 |
| `BEDROCK_REGION` | AWS_REGION 값, 없으면 us-west-2 | 이미지 생성에만 쓰는 리전. 전역 AWS_REGION 이 다른 리전일 때 지정 |
| `BEDROCK_IMAGE_MODEL` | `stability.stable-image-core-v1:1` | 별칭 `core`, `ultra`, `sd3.5-large` |
| `BEDROCK_NEGATIVE_PROMPT` | 없음 | 제외할 요소 |
| `BEDROCK_SEED` | 무작위 | 재현용 시드 |

동작 확인:

```
python3 skills/aws-ppt-master/scripts/image_gen.py "flat illustration of a robot arm" --aspect-ratio 16:9
```

## 폰트

기본 서체는 **Amazon Ember**(영문)와 **Noto Sans KR**(한글)을 한 스택으로 씁니다(`Amazon Ember, Noto Sans KR`). 전달 대상 PC에 Amazon Ember 가 없으면 `Noto Sans, Noto Sans KR` 로 대체합니다. 사용자나 템플릿이 서체를 지정하면 그 지정이 우선합니다. 내보내기와 `pptx_delivery_check.py` 는 이 서체들을 승인된 서체로 보고 이식성 경고를 내지 않습니다. PPTX 에는 폰트가 포함되지 않으므로 여는 PC에 Amazon Ember 와 [Noto Sans KR](https://fonts.google.com/noto/specimen/Noto+Sans+KR) 이 설치되어 있어야 합니다. 작성 호스트에도 같은 폰트를 두면 SVG 미리보기와 텍스트 폭 측정이 실제 PPTX 와 일치합니다.

## 도구

- `scripts/bake_icon_clips.py <svg_dir_or_files...> [--check]`: `<g clip-path>` 로 잘라낸 아이콘 영역을 실제 `<path>` 도형으로 굽는다(`pip install skia-pathops`). PPTX 내보내기는 `<image>` 이외의 clip-path 를 거부하므로, 시각적으로 필요한 클립은 지우는 대신 이 도구로 굽는다.

## 사용

트리거: "발표자료 만들어줘", "이 문서로 PPT 만들어", "AWS 기술 발표 10장", 또는 `/aws-ppt-master`.
워크플로·라우팅·레퍼런스 문서는 원본 구조를 그대로 유지합니다. 시작점은 `skills/aws-ppt-master/SKILL.md` 입니다.

## English

AWS-flavoured fork of ppt-master 6.3.2. Only external model call: Amazon Bedrock (Stability AI Stable Image). Removed narration/TTS/video, stock image search, watermark removal, and the upstream integrity gate. Added `pptx_qa_check.py` (layout + Korean/English copy-voice QA) and a 304-icon AWS service icon library. Install with the two `/plugin` commands above, then `pip install -r requirements.txt` and enable Stability model access in Bedrock.

## License

MIT. Upstream and third-party notices: [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md), [UPSTREAM.md](UPSTREAM.md).
