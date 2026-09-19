# Stage 3: Diagrams (runs in parallel with research)

A blog post about an AWS project is judged first by its architecture figure. Readers zoom in on it before
they read a paragraph, and reviewers at AWS compare it against the text. The figure therefore has to be
built from the fact base, with official icons, and checked twice: once by the diagram skill's own
validator and once by you against `01-facts.md`.

## Which skill

| You need | Skill | Output that ships |
|---|---|---|
| AWS architecture: services, accounts, VPC boundaries, request paths, what calls what | `aws-drawio-diagram` | `<name>.drawio.png` (XML embedded, editable), plus `<name>.brief.md` and `<name>.guide.md` kept next to it |
| Concept figure: before/after, layered model, process, swimlane, sequence between actors, comparison quadrant | `aws-diagram-design` | PNG exported from the generated HTML via its export procedure |
| A second, simplified view of the same architecture for the opening (fewer boxes) | `aws-drawio-diagram` with a reduced brief, or `aws-diagram-design` Architecture type redrawing the `.drawio` | PNG |
| Console screenshot, demo UI, dashboard | Nobody: `[이미지 필요]` placeholder with the caption written | (author supplies) |

Do not draw architecture with `mermaid` or with hand-written SVG for a blog post; icons will be wrong and
reviewers will ask for a redo. Do not use `aws-diagram-design` for the main architecture when a
`.drawio` can be produced; editors and co-authors expect an editable file.

## Briefing the architecture skill from the fact base

The `aws-drawio-diagram` skill starts with an Architect phase that writes a brief (components,
relationships, groups). Feed it the component inventory and the flows from `01-facts.md`, not your
recollection of the sources:

1. Copy the inventory rows (service, role, group) into the request, with the fact IDs.
2. Copy the request paths as numbered flows (`users → ALB → web → server → AgentCore Runtime → Bedrock`).
3. State the audience (`technical`), the language (`ko`), and that a PNG is wanted.
4. State what must not appear: services the project did not use, even if typical. The skill's Assessor
   phase may propose additions from Well-Architected guidance; accept them into the picture only if the
   project actually had them, otherwise record them as text in the post ("프로덕션 전환 시 WAF 추가를
   권고했습니다") with a fact or placeholder.

If the project already has `.brief.md` and `.drawio` files (a previous run of the skill, often in the
source material), register them as sources, verify they still match the facts, and rebuild rather than
redraw. The rebuild command is in the skill's review checklist (`build_diagram.py <name>.layout.json ...
--brief <name>.brief.md` must print `brief check ... ✓`).

## Briefing the concept skill

`aws-diagram-design` wants a type (Architecture, Process, Sequence, Layer stack, ...), a size preset, and
the content. Keep it under nine nodes; the skill's own philosophy is deletion. Because the post is in
Korean, ask for `ko` labels with English service names, and use its Python generator when you need a
ko/en pair or several figures in one style. Run `scripts/self_check.py` from that skill on the HTML, then
export PNG with its `export.md` procedure (Playwright screenshot of the SVG node).

## Verification you do yourself

The diagram skills verify layout and icon validity. They cannot know whether the picture is true. After
the skill reports `ready`:

1. Open the PNG (`Read` on the plain PNG; the `-e` embedded PNG cannot be displayed, so keep a preview copy
   until this step is done, then delete it).
2. Write down every node label and every edge (from, to, label) you see. Do this from the picture, not
   from the spec.
3. Check each node against the component inventory in `01-facts.md`. A node with no inventory row is
   either an invention (remove it) or a missing fact (add the fact with its source, or a placeholder in
   the text and remove the node).
4. Check each inventory component marked as part of this diagram's scope against the nodes. A missing
   component is a defect unless the brief's Decisions say why it is not drawn.
5. Check every edge against the flows in the facts. Direction matters (`server → Cognito` for token
   validation, not `Cognito → server`).
6. Check names: current AWS names, correct prefixes, same spelling as the text.
7. Check the picture is readable at blog width (about 800 px). If labels need zoom, ask for a split
   into two figures rather than a smaller font.

Record the result in `<work>/diagrams/manifest.md` (template in `templates/diagram-manifest.md`). A
figure without a manifest row does not go into the draft.

## Embedding

```markdown
아래 그림 1은 PoC에서 구성한 전체 아키텍처입니다. 사용자의 요청은 Application Load Balancer를 거쳐 ...

![Agent Platform 전체 아키텍처: ALB, ECS Fargate, Cognito, DynamoDB, S3, Bedrock AgentCore Runtime과 Gateway, Bedrock 모델](images/fig1-agent-platform.drawio.png)

그림 1. Amazon Bedrock AgentCore 기반 Agent Platform 전체 아키텍처
```

- Copy the shipping PNG into `<work>/images/` with a `figN-` prefix; keep the original next to its brief
  in `<work>/diagrams/`.
- Alt text describes; caption names. Do not duplicate one into the other.
- Reference the figure in the text before it appears. A figure that the text never mentions is decoration
  and gets cut.
- Figure numbering is sequential in reading order, including placeholders for screenshots.
