<!-- Fill the <...> fields and send as the prompt of the `aws-tech-blog-writer:blog-reviewer` agent
     (Agent tool, subagent_type). Its procedure lives in agents/blog-reviewer.md; this prompt carries
     only the paths. If the plugin agent is not registered, send this same prompt to a general-purpose
     subagent and prepend the body of agents/blog-reviewer.md. -->

Review the story and logic of `<draft: <work>/draft.md, or 04-draft.md from the writer skill>` and write
`<output: <work>/story.md>`. Read, in this order, and nothing else:

1. `<skill-dir>/references/review-rubric.md` (criterion E, severity, finding format, story.md layout)
2. `<writer-dir>/references/aws-blog-conventions.md` (§1, §3, §6, §10)
3. the draft above, then every PNG it embeds under `<work>/images/`

Post type as the title suggests: <A 고객 사례 | B 구현 가이드 | C 아키텍처 해설 | unknown>.
Target reader: <one sentence, or "the engineer or architect the title addresses">.
Do not check AWS facts or sentence style; other checks cover them. Do not edit the draft. Reply with
the one-sentence reading, counts by severity, the three findings that matter most, and whether the
section order should change.
