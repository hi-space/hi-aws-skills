<!-- Fill the <...> fields and send as the prompt of a general-purpose subagent. -->

You are fact-checking a Korean AWS Tech Blog draft against official documentation. You do not know the
project and must not assume the author is right. Do not edit the draft. Do not spawn subagents.

Read `<skill-dir>/references/verification.md` ("Shared rules" and "Stage 5"), then `<work>/04-draft.md`.
Fill `<work>/05-claims.md` from `<skill-dir>/templates/claims.md`: one row per technical claim (every
code block is at least one row), with status, URL, date opened, and evidence quoted from the page.

Tools: `aws-docs` MCP (`search_documentation`, `read_documentation`, `read_sections`, `recommend`),
`aws-mcp` proxy tools as fallback, `WebFetch` for vendor and GitHub pages. A search snippet is not
evidence; open the page.

Reply with:
1. Counts: verified / corrected / unverified / out-of-scope.
2. The corrections list: for each `corrected` row, the original sentence and the proposed sentence
   with its URL; for each `unverified` row, the original sentence and the proposed `[기술 검증 필요]
   (Cnn) ...` placeholder text. The style pass will apply these.
3. Any place a documentation link should be added to the draft (claim ID, section, URL).
