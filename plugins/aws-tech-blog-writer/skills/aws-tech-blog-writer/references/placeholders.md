# Placeholders: what to write when you do not know

A placeholder is a promise to the author: "the post needs this here, and here is what a good version
looks like." It is not a TODO. The author reads it in a WordPress preview or a Word file, so it must be
visible at a glance (colour), say which kind of gap it is (tag), and describe the desired content
(request). A placeholder that only says `[확인 필요]` sends the author back to you to ask what you meant.

## The four categories

| Tag | Colour (background / text) | Use for | Who fills it |
|---|---|---|---|
| `[작성자 확인]` | yellow `#FFF2CC` / `#7F6000` | Project facts only the author knows: numbers, dates, names, decisions, results, bios | Author |
| `[기술 검증 필요]` | red `#F8CECC` / `#9F0000` | An AWS or third-party technical statement you could not confirm in official documentation | Author or AWS reviewer |
| `[이미지 필요]` | blue `#DAE8FC` / `#0B3D91` | A screenshot, console view, demo capture, or photo the author must take | Author |
| `[인용 승인 필요]` | green `#D5E8D4` / `#1E5631` | Customer name, logo, quote, or data that needs the customer's or PR's approval | Author with customer |

Everything else is not a placeholder. A general technical question you can answer by opening AWS
documentation is research (Stage 3), not a placeholder.

## HTML form

Inline HTML in Markdown. Inline styles paste into the WordPress editor and survive `pandoc` to HTML; a
CSS class alone would be stripped. Keep the exact attribute order so `lint_blog.py` can find and count
them, and so `scripts/build_docx.js` can turn each span into a Word run shaded with the same two colours
(pandoc's own DOCX writer drops them, which is why the Word file is built with docx-js instead).

```html
<span style="background-color:#FFF2CC;color:#7F6000;padding:1px 4px;">[작성자 확인] 파일럿 참여 인원과 기간을 적어 주세요. 예: "정보전략팀과 IT개발팀 12명이 3주간 사용"과 같이 인원, 소속, 기간이 있으면 독자가 규모를 판단할 수 있습니다.</span>
```

```html
<span style="background-color:#F8CECC;color:#9F0000;padding:1px 4px;">[기술 검증 필요] (C08) AgentCore Gateway가 Lambda 타겟 호출 시 사용하는 인증 방식(SigV4 여부, 실행 역할 요구 사항)을 공식 문서에서 확인해 주세요. 확인 후 문장을 "Gateway는 ... 방식으로 Lambda를 호출합니다"로 바꾸면 됩니다.</span>
```

```html
<span style="background-color:#DAE8FC;color:#0B3D91;padding:1px 4px;">[이미지 필요] Agent Platform의 Registry 화면 캡처. 등록된 에이전트 목록과 검색창이 보이도록, 고객 내부 데이터는 가리고 캡처해 주세요. 캡션: 그림 4. Agent Platform Registry 화면</span>
```

```html
<span style="background-color:#D5E8D4;color:#1E5631;padding:1px 4px;">[인용 승인 필요] 최종보고 자리에서 나온 "데이터를 MCP로 바꾸는 표준 경로가 생겼다"는 취지의 발언을 인용하고자 합니다. 발언자 표기 방식(실명/직함/익명)과 문구 승인을 받아 주세요.</span>
```

A whole missing section (for example `## 결과` when no results exist yet) is a single block placeholder:

```html
<p><span style="background-color:#FFF2CC;color:#7F6000;padding:1px 4px;">[작성자 확인] 결과 섹션. 다음 중 확인 가능한 항목을 적어 주세요: (1) 파일럿 사용자 수와 기간, (2) 대표 질의 유형별 정답률 또는 골든셋 통과율, (3) 기존 방식 대비 소요 시간 변화, (4) 운영 비용(월 단위, 모델 호출 비중). 수치가 없다면 "정성적 피드백 3가지"로 대체해도 됩니다.</span></p>
```

## Writing the request

Each placeholder has three parts, in this order:

1. **What** is missing, as a noun phrase (`파일럿 참여 인원과 기간`, `결과 섹션`).
2. **Why the post needs it**, in one clause, so the author can judge whether to supply it or cut the
   sentence (`독자가 규모를 판단할 수 있습니다`).
3. **What a good answer looks like**: a pattern, an example with fake values, or the options. For
   `[기술 검증 필요]`, start with the claim ID from `05-claims.md` in parentheses, name the document or
   page to check, and give the sentence to use once confirmed.

Write the request in the language of the post. Keep it under three sentences; the author will delete it.

## Rules

- Never resolve a placeholder by inference in a later pass. If the Stage 5 fact-check answers a
  `[기술 검증 필요]`, the sentence is rewritten with a citation and the placeholder removed; if it does
  not, the placeholder stays.
- A number, a date, or a name that is not in `01-facts.md` or `03-research.md` is a placeholder, even
  when a "reasonable" value is obvious.
- Do not stack: one placeholder per gap, placed where the content will go. Do not add a second one in
  the conclusion for the same fact.
- Placeholders in captions and headings are allowed but keep them short (`그림 3. [이미지 필요] Insights 대시보드`).
- `lint_blog.py --placeholders-out <work>/placeholders.md` writes the list grouped by category with the
  line number and the request text, for the author. `build_docx.js` appends it to the Word file as the
  last section, so the author gets the post and the to-do list together.
