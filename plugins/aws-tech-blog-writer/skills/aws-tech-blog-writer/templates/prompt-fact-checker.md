<!-- Fill the <...> fields and send as the prompt of the `aws-tech-blog-writer:blog-fact-checker` agent
     (Agent tool, subagent_type). Its procedure lives in agents/blog-fact-checker.md; this prompt carries
     only the paths. If the plugin agent is not registered, send this same prompt to a general-purpose
     subagent and prepend the body of agents/blog-fact-checker.md. -->

Fact-check `<work>/04-draft.md` and write `<work>/05-claims.md`. Read, and nothing else about the project:

1. `<skill-dir>/references/verification.md` ("Shared rules" and "Stage 5")
2. `<skill-dir>/templates/claims.md`
3. `<work>/04-draft.md`

Project timeline and region, for availability checks: <기간, 리전>.
Do not edit the draft. Reply with the counts (verified / corrected / unverified / out-of-scope), the
corrections list (original sentence, proposed sentence or placeholder text, URL), and where
documentation links should be added.
