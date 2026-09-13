# Phase 4 — Review checklist

The Reviewer gets three things: the brief, the validator output, and the rendered PNG (`<name>.preview.png` —
plain export, no `-e`, so the Read tool can display it; it is the same picture as `<name>.drawio.png` and is
deleted once the verdict is `ready`, § E). The Reviewer does **not** get the spec or the XML first — judge the
picture the way the user will, then open the spec to explain what to change.

Report as a list of findings; each finding names the fix **as a spec change** (move node X to lane 2, drop the
label on edge Y, widen group Z to cols [3,4]). The Drawer applies them and re-exports; the Reviewer looks again.
Two rounds is normal; a third means the brief or the group plan is wrong — go back to Phase 1.

**The Reviewer is not the Drawer.** Run this phase in a fresh context (subagent) whenever you can. If you must
do it yourself, write the review to `<name>.review.md` *before* touching the spec, with the counts from § A and
the validator's last summary line pasted in — a review that exists only in your head is the one that passes
everything. Verdict is `ready` or `not ready`; there is no "ready with warnings".

## A. Faithful to the brief

- [ ] **Count and write the numbers down**: brief components = nodes, brief relationships = edges (minus aux
      rows the Reviewer trimmed under Decisions). `22 rows → 12 edges` is `not ready`, whatever the picture
      looks like.
- [ ] Every component in the brief is a node; no node exists that the brief does not list (a node the Drawer
      invented — an "API" box, a "Platform" box — is `not ready`).
- [ ] **No abstract nodes.** Every node is one AWS service/resource or one user/external system, and its icon
      is that service's icon. A load-balancer icon labelled "Agent Platform", a Cognito icon labelled
      "Agents", a directory name as a node: `not ready` — the fix is separate diagrams or groups
      (from-source-code.md § 4), never a relabel.
- [ ] Every relationship is an edge with the right direction and kind (solid = sync, dashed = async/aux,
      red dashed = error). A Drawer that dropped a *primary* relationship to make layout work is `not ready`
      (fix the layout: bus, more lanes, split by request path). A brief that lists redundant *aux* edges (one
      into CloudWatch per service) is a brief defect the Reviewer may fix directly: keep the representative
      edge, delete the rest from the table, add a line under Decisions — no Phase 1 restart needed.
- [ ] Group membership matches the brief's Group column. Users / external systems are outside the AWS Cloud.
- [ ] Labels use the brief's names (current AWS service names, qualifiers in parentheses).

## B. Mechanically clean (validator)

- [ ] **Rebuild it yourself**: `python3 <skill-dir>/scripts/build_diagram.py <name>.layout.json /tmp/<name>.drawio
      --brief <name>.brief.md` must print `brief check: … ✓` and `0 errors, 0 warnings`, and `cmp` of its output
      with the delivered `<name>.drawio` must be silent. A delivered file that differs from the rebuild, or a
      log with `brief check SKIPPED` / `skipped`, is `not ready` whatever the Drawer's report says.
- [ ] When the unit was split (from-source-code.md § 1): the split briefs' Components together equal the unit's
      inventory in Scope. Pages that add up to a fraction of the inventory are `not ready`.
- [ ] **The contract held**: `<name>.contract.json` exists, the build log has no `ERROR contract`, and every
      `note: … newly marked aux / not drawn` row names something the picture cannot show (an IAM role, a VPC, an
      endpoint) — a relationship re-pointed at another service, or a service hidden so the layout converges, is
      `not ready`. A brief that was rewritten and had its contract deleted without a Decisions line is `not ready`.
- [ ] The builder exited 0 and the summary reads `0 errors, 0 warnings`. Read the codes, do not guess them:
      `W4`–`W9` are layout defects and the builder prints `Layout defects … NOT CLEAN` for them —
      W4 two-bend or long bend · W5 edge through an icon · W6 icon outside every group · W7 edge label on a
      border · W8 edges drawn on top of each other · W9 icon with no edge. Any of them → `not ready`. `W1`–`W3`
      are style hints. Builder `hint:` lines (sparse group, one-icon lane) are findings too unless the Drawer
      wrote down why not.
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
- [ ] **Edge text**: every primary edge — straight or bent — shows its brief's *What flows* phrase, in ≤ 3 lines,
      in free space (not on a border, a title row, an icon, another label or another line). Compare the brief's
      What flows column with the picture: a primary edge without its text is a finding. The builder refuses
      (`ERROR label`) a primary phrase that has no room, so a build that passed has none — a review that reads
      "too long, acceptable" next to a solid edge describes a build that did not pass, and is `not ready`.
      `note: label dropped` on a dashed edge is allowed. A phrase the Drawer condensed still means what the
      Architect wrote (`StartExecution` → `start saga` yes; `token validation` → `—` no). Node labels ≤ 3 words.
- [ ] **Typography**: one font family throughout (Amazon Ember or Noto Sans); title 20 bold, subtitle grey;
      group titles and node labels 13 bold; nothing in a second colour except the grey subtitle/legend.
- [ ] **Legend** present iff there are two edge kinds; title carries author · date · version.

## D. Correct as architecture (sanity re-check)

- [ ] Entry, auth, async boundaries, state, observability — the brief's Checks section is still true in the
      picture (nothing got dropped to make layout easier). Every *fixed* finding in `## Architecture review`
      is visible; every *accepted* one is under Decisions with its source. If the Drawer removed a component for layout
      reasons, that is a finding: the fix is a layout change, not a smaller architecture.
- [ ] When the input was a codebase: the brief has `Repo:` and the scaffold log shows no "evidence path … does
      not exist" line (spot-check two paths yourself); every node has Evidence and Provenance; `assumed` nodes are
      each a Decisions line; the `## Architecture review` header states the MCP call count and every source in
      a finding appears in *Sources consulted*.

## E. Hand-off (after `ready`, before telling the user)

- [ ] `<name>.guide.md` exists next to the `.drawio`, written from the template in `architecture-guide.md`, in the
      brief's `Language:` (Korean prose with English service names for `ko`). Its step-by-step section has **one
      numbered step per row of the brief's Relationships, numbered like the brief's `#`, and every step quotes
      the text drawn on that arrow** — the row's *What flows* phrase, as (라벨 `…`); aux rows not drawn say so.
      Its Services table has one row per Components row, and Design decisions carries every Decisions line, every
      accepted review finding with its source, every icon substitution and every trimmed aux edge.
- [ ] `python3 <skill-dir>/scripts/check_guide.py <name>.guide.md <name>.brief.md` exits 0 (`guide check … ✓`).
      It refuses the wrong language, a missing or mis-numbered step, a step that names the wrong endpoints or does
      not quote its phrase, and a component missing from Services. A guide that fails it is `not ready`, whatever
      it reads like.
- [ ] Spot-check three arrows: the text on the picture is the brief's *What flows* phrase for that pair, and the
      guide step with that number quotes the same words.
- [ ] `<name>.preview.png` has been deleted. The delivered image is `<name>.drawio.png` alone (XML embedded);
      `ls` the directory and check — two identical-looking PNGs is a finding.

## Typical findings → spec fixes

| Finding | Spec fix |
|---|---|
| Edge text on a border, an icon or another line (W7, hand-written XML) | set `label_offset` to a free stretch of the edge, or move the node so the edge has a longer leg |
| `ERROR label … no clear place` on a primary edge | Drawer condenses the brief's *What flows* phrase to what the edge offers (a hop between two group boxes holds words of ≤ 6 letters: `start saga`, `write to lake`) and reruns the scaffold; or moves a node in the `.layout.json` so the edge runs inside one box or vertically |
| `note: label dropped` on a dashed edge | allowed; the guide quotes the phrase and says the line has no text — or condense it as above so it appears |
| Primary edge with no text although the brief has a phrase | the text was removed by hand — restore it in the spec; if it W7s, move the node |
| Node label runs into the neighbouring column | label > 22 characters and the builder could not split it (no space) — shorten or add a space before the qualifier |
| Line disappears behind a node label | hand-written XML without the `B` port — use `exitY`/`entryY` = (78 + 4 + 18·lines)/78 with `*Perimeter=0` (layout-and-style.md §5) |
| Dead column inside a group | move a neighbour into that cell or shrink the group's `cols` |
| Empty band across the top of the cloud | move upper-lane items there (auth, static assets, memory) or drop lane 0 and fan out downward |
| Fan-out edge runs through an icon (W5) | the hub's own column must be empty on every lane the trunk crosses; move that icon into an adjacent column |
| Icon with no edge (W9) | the brief has a relationship for it — draw it; or the component does not belong in this diagram |
| A hub has more neighbours than free sides | bus: stack the neighbours in the two adjacent columns above and below the hub, keep the hub's column clear (layout-and-style.md §5) |
| Straight edge and bends on the same side | move the straight target to another side, or make it part of the bus by shifting it one column |
| A bend crosses two columns (W4 "adjacent") | the horizontal leg reaches one column only; move the target, or connect via the node in between |
| Brief has 30+ components and the spec has 8 | not a layout problem: rebuild with `scaffold_spec.py` + auto layout; still too dense → one diagram per deployable unit or per request path (from-source-code.md §1) |
| Layout `unresolved:` line for one edge | move one endpoint in `<name>.layout.json` (a node with neighbours in four columns wants the middle one), or split the diagram |
| Whole lane holds one icon (`hint:`) | give that icon the main lane or its neighbour's lane; a one-icon lane is an empty band |
| Group taller than its neighbours for one icon | split lanes: give the extra icon its own single-lane group in the next row |
