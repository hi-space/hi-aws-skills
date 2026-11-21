# Technical illustrations: objects and how they work

When the position, shape, sensing or movement of a real thing is the point, draw the thing. A system box diagram cannot show where a sensor sits, and three boxes named after steps cannot show a movement.

## Kinds

| Kind | Explains | Built from |
|---|---|---|
| `annotated` | Where parts are and what they do | Simplified outline + parts + callout lines |
| `coverage` | Field of view, sensing or reach | Object + translucent sector or arc + area label |
| `cutaway` | What is hidden inside | Casing partly opened or faded + inner parts |
| `exploded` | How parts fit together | Parts spread along one axis + dashed alignment guides |
| `motion` | Travel, rotation, joint movement | Object pose + path or rotation arrow + before/after position |
| `storyboard` | A situation changing over time | The same subject in 2-4 scenes + order numbers + one short line each |

The kinds combine: sensor positions with coverage and a travel path is one figure. If it gets too dense to read in order, split it into scenes. Message order between systems is a sequence diagram and a branching decision is a flowchart; neither is a storyboard. Every storyboard scene shows the actual subject and what changed around it.

## Before drawing, settle

1. Subject and viewpoint: a mobile robot from above, an articulated arm from the side.
2. The parts confirmed by the input and their relative positions. An unknown position stays unknown.
3. The meaning to show: which sensor sees which area, what moves and how.
4. Layout: object in the centre, margin for labels, order of scenes.
5. What is fact and what is a conceptual rendering (not to scale, concept placement).

## Rules for all kinds

- Build the object from the allowed primitives: body as a rounded rectangle, ellipse or path; wheels as circles or short rectangles; sensors as small circles or squares. The goal is a recognisable silhouette. No product logos, no CAD precision.
- A callout line starts with a small dot on the actual part and runs to a label in empty space outside the outline. A dot marks a callout; an arrowhead means movement. Keep the two distinct. Callouts do not cross each other, a sensing area's label, or another label.
- Draw order: **background and sensing areas, then body and parts, then callout lines and dots, then text.** A callout must be visible along its whole length, so it is drawn after the opaque body it crosses.
- Outline and part labels are strong (`--ink`, weight 700). Secondary outlines and a previous pose are light (`--line` or `--muted`, dashed for a previous pose).
- The same part keeps the same shape and orientation mark in every scene.
- State colours keep their meaning here too: a sensor is not `--risk` because it is a different kind of sensor. Neutral parts use `--panel` with `--ink` or `--line`; a sensing or reach area is filled with `--muted` (or the state token, when the area has a state) at `fill-opacity` 0.12-0.2, with a dashed edge when its extent is conceptual.
- Part labels are required information: start from 3-6 and size the canvas to fit them at the font floor.

## Per kind

**annotated.** One central object, 3-6 parts, each with a short role. If the input does not give a mounting position, label only what is known or mark the figure as a concept placement.

**coverage.** The area starts at the sensor. Fill with low `fill-opacity`, mark the edge and direction with a line or arc, and keep it clear of the object and labels. With no angle or range in the input, the shape is a concept: say so in a label and put no numbers on it. Concentric rings here mean space, not data.

**cutaway.** Break or fade part of the casing and keep enough of it to hold the overall shape. Only confirmed parts go inside; a simplified inner layout is labelled as a concept.

**exploded.** Parts keep their orientation and spread along one axis. Alignment guides are dashed; an arrow appears only where the assembly direction matters. Gaps are not dimensions, so no length marks. No fasteners that the input does not mention.

**motion.** Distinguish the current pose from the previous or next one. A curved arrow is a travel path; a rotation arc is centred on the real pivot. Speed, angle and time appear only when given.

**storyboard.** Split a process the input describes (detect, stop, turn, move) into 2-4 scenes. Each scene shows the object, the obstacle and the changed state. Viewpoint and scale stay fixed and the change is what stands out. In a 560 or 400 canvas the scenes stack top to bottom, each with an order number and a short line.
