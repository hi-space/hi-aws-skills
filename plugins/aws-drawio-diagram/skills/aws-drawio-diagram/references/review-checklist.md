# Phase 4 — Review checklist

The Reviewer gets three things: the brief, the validator output, and the rendered PNG (plain export, no `-e`,
so the Read tool can display it). The Reviewer does **not** get the spec or the XML first — judge the picture the
way the user will, then open the spec to explain what to change.

Report as a list of findings; each finding names the fix **as a spec change** (move node X to lane 2, drop the
label on edge Y, widen group Z to cols [3,4]). The Drawer applies them and re-exports; the Reviewer looks again.
Two rounds is normal; a third means the brief or the group plan is wrong — go back to Phase 1.

## A. Faithful to the brief

- [ ] Every component in the brief is a node; no node exists that the brief does not list.
- [ ] Every relationship is an edge with the right direction and kind (solid = sync, dashed = async/aux,
      red dashed = error). Count them: brief rows = edges. A Drawer that dropped a *primary* relationship to
      make layout work is a finding (fix the layout). A brief that lists redundant *aux* edges (one into
      CloudWatch per service) is a brief defect the Reviewer may fix directly: keep the representative edge,
      delete the rest from the table, add a line under Decisions — no Phase 1 restart needed.
- [ ] Group membership matches the brief's Group column. Users / external systems are outside the AWS Cloud.
- [ ] Labels use the brief's names (current AWS service names, qualifiers in parentheses).

## B. Mechanically clean (validator)

- [ ] `0 errors, 0 warnings`. `W4`–`W8` are layout defects, not style opinions:
      W4 two-bend or long bend · W5 edge through an icon · W6 icon outside every group · W7 edge label on a
      border · W8 edges drawn on top of each other. Builder `hint:` lines (sparse group, one-icon lane) are
      findings too unless the Drawer wrote down why not.
- [ ] **A blank coloured square** where an icon should be is not a spec bug: the stencil is newer than the
      installed draw.io (e.g. `quick_suite`, `bedrock_agentcore`). Say so in the report; if the user's draw.io
      is also old, switch to the legacy alias when one exists (`quicksight`) and note it in the brief.

## C. Human-readable (look at the PNG)

- [ ] **Nothing overlaps**: no text on a line, no line through an icon, no label across a group border, no
      node label touching the group's bottom border. Every node label is *below* its icon; a vertical edge
      starts under the label, never through it. Zoom in on every edge label.
- [ ] **Read order**: main request path runs left → right on one lane; auxiliary paths hang below (or above);
      the eye finds the entry point in the first second.
- [ ] **Grouping**: 2–7 role groups, each titled, each with 1–4 icons; no group with more empty cells than
      icons; no lonely icon floating in the cloud.
- [ ] **Balance**: the cloud box has no empty quadrant larger than a group; the canvas hugs the content
      (roughly equal margins); no half-empty page.
- [ ] **Edges**: every edge is straight or has one bend; fan-out bends are all on the same side of the source;
      no two edges share a segment.
- [ ] **Labels**: ≤ 5 edge labels for ~15 nodes; each in free space; each ≤ 2 words. Node labels ≤ 3 words.
- [ ] **Typography**: one font family throughout (Amazon Ember or Noto Sans); title 20 bold, subtitle grey;
      group titles and node labels 13 bold; nothing in a second colour except the grey subtitle/legend.
- [ ] **Legend** present iff there are two edge kinds; title carries author · date · version.

## D. Correct as architecture (sanity re-check)

- [ ] Entry, auth, async boundaries, state, observability — the brief's Checks section is still true in the
      picture (nothing got dropped to make layout easier). Every *fixed* finding in `## Architecture review`
      is visible; every *accepted* one is under Decisions with its source. If the Drawer removed a component for layout
      reasons, that is a finding: the fix is a layout change, not a smaller architecture.

## Typical findings → spec fixes

| Finding | Spec fix |
|---|---|
| Label on a group border | remove `label`, or move the node so the segment crosses a row gap, or set `label_offset` |
| Node label runs into the neighbouring column | label > 22 characters and the builder could not split it (no space) — shorten or add a space before the qualifier |
| Line disappears behind a node label | hand-written XML without the `B` port — use `exitY`/`entryY` = (78 + 4 + 18·lines)/78 with `*Perimeter=0` (layout-and-style.md §5) |
| Dead column inside a group | move a neighbour into that cell or shrink the group's `cols` |
| Empty band across the top of the cloud | move upper-lane items there (auth, static assets, memory) or drop lane 0 and fan out downward |
| Fan-out edge runs through an icon | the source's top/bottom cell must be empty; move that icon or fan out on the other side |
| Several edges leave one node downward as one line (W8) | one edge per side: put a queue/topic between the node and its many consumers, or move consumers to the node's other sides |
| A bend crosses half the diagram (W4 "adjacent") | the target must be in the diagonally adjacent cell; move it, or connect via the node in between |
| Whole lane holds one icon (`hint:`) | give that icon the main lane or its neighbour's lane; a one-icon lane is an empty band |
| Group taller than its neighbours for one icon | split lanes: give the extra icon its own single-lane group in the next row |
