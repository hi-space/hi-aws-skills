<!-- Fill the <...> fields and send as the prompt of the `aws-tech-blog-writer:blog-fact-checker` agent
     (Agent tool, subagent_type). Its procedure lives in agents/blog-fact-checker.md; this prompt carries
     only the paths and the review-specific instructions. If the plugin agent is not registered, send
     this same prompt to a general-purpose subagent and prepend the body of agents/blog-fact-checker.md. -->

Fact-check `<work>/draft.md` and write `<work>/05-claims.md`. Read, and nothing else about the project:

1. `<writer-dir>/references/verification.md` ("Shared rules" and "Fact-check")
2. `<writer-dir>/templates/claims.md`
3. `<work>/draft.md`
4. Project facts: <facts: <work>/01-facts.md | none>

Every sentence that asserts AWS, SDK, or protocol behaviour is a claim, including sentences that also
state what the project did. If a facts file is given, a sentence it states with a source ID is a project
fact and gets no row unless it also asserts AWS behaviour; if `none`, there is no fact table and you
treat every project statement that asserts AWS behaviour as a claim. Project timeline and region, for
availability checks: <기간, 리전 | unknown; check as of today>.

Currency: for every name, availability, limit, and API claim, also record whether the current page
differs from what the draft says (renamed service or feature, preview to GA, deprecated or superseded
operation, changed default or quota). Such a row is `corrected`, with the change and the date you saw
it in Note. A newer service that would do the job better is not a correction; list it separately under
"권고" in your reply.

Do not edit the draft. Reply with the counts (verified / corrected / unverified / out-of-scope), the
corrections list (original sentence, proposed sentence or placeholder text, URL), where documentation
links should be added (claim ID, section, URL), and the 권고 list.
