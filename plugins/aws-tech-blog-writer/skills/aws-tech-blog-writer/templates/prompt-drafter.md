<!-- Fill the <...> fields and send as the prompt of a general-purpose subagent. Attach nothing else. -->

You are writing the first full draft of a Korean AWS Tech Blog post. Work only from the files listed
below; do not open the source documents, do not search the web, do not spawn subagents. Write the draft
to `<work>/04-draft.md` and reply with two lines: the file path and the number of placeholders you wrote.

Read, in this order:
1. `<skill-dir>/references/voice.md`            how every sentence has to read (the whole file)
2. `<skill-dir>/references/aws-blog-conventions.md` §1 <A|B|C> skeleton, §2 title, §3 opening, §5 naming, §6 to §10
3. `<skill-dir>/references/placeholders.md`     the four placeholder spans, exact HTML
4. `<work>/02-plan.md`                         the plan you are executing, section by section
5. `<work>/01-facts.md`                        the only project statements you may make (fact table, inventory, timeline)
6. `<work>/03-research.md`                     verified AWS facts with URLs; cite them where the plan says
7. `<work>/diagrams/manifest.md`               figures that exist, their files under images/, captions

Rules that decide whether the draft is accepted:
- Every project statement ends with its fact IDs in an HTML comment: `... 배포했습니다. <!-- F04 F09 -->`.
  If no fact supports a sentence, write a placeholder span instead of the sentence.
- Every AWS statement rests on a research entry (`<!-- R03 -->`) or is written as a claim the
  fact-checker will test. Numbers come only from facts or research; no estimates, no `약 30%`.
- Placeholders follow placeholders.md exactly: coloured span, tag, what is missing, why the post needs
  it, what a good answer looks like. Author bios, customer name approval, screenshots, unknown results
  are placeholders, not guesses.
- Headings are noun phrases. Subjects are people, teams, services, or components. No passive with a
  known actor, no figurative nouns, no evaluation words (voice.md §1).
- AWS service names as AWS writes them, full name at first body mention (conventions §5).
- Figures: introduce in the text, embed `![alt](images/figN-....png)`, caption `그림 N. ...` on the
  next line, numbered in reading order. Screenshots the author must take are `[이미지 필요]` spans
  with the caption written.
- Length: <목표 글자 수> Korean characters of body text, ±15%.
- Write the whole post in one pass, then read it once as the target reader (<독자 한 문장>) and reorder
  sections if the argument reads better; then stop. Do not lint, do not build the Word file.

Post type: <A|B|C>. Title (fixed in the plan): <제목>.
