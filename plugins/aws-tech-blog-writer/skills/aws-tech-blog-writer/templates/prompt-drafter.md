<!-- Fill the <...> fields and send as the prompt of the `aws-tech-blog-writer:blog-drafter` agent
     (Agent tool, subagent_type). Its rules live in agents/blog-drafter.md; this prompt carries only the
     paths and the variables of this post. If the plugin agent is not registered, send this same prompt
     to a general-purpose subagent and prepend the body of agents/blog-drafter.md. Attach nothing else. -->

Write the first full draft to `<work>/04-draft.md`. Read, in this order, and nothing else:

1. `<skill-dir>/references/voice.md`
2. `<skill-dir>/references/aws-blog-conventions.md` (§1 skeleton <A|B|C>, §2, §3, §5, §6 to §10)
3. `<skill-dir>/references/placeholders.md`
4. `<work>/02-plan.md`
5. `<work>/01-facts.md`
6. `<work>/03-research.md`
7. `<work>/diagrams/manifest.md`
8. `<skill-dir>/templates/blog-post.md`

Post type: <A|B|C>. Title (fixed in the plan): <제목>.
Body length: <목표 글자 수> Korean characters, within 15 percent.
Target reader, in one sentence: <독자 한 문장>.
Do not open the source documents, do not search the web, do not spawn subagents, do not lint, do not
build the Word file. Reply with the file path and the number of placeholders you wrote.
