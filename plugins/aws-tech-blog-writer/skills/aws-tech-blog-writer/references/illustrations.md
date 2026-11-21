# Illustrated concept figures

Concept figures in a post explain an idea to a reader who has not seen it before. A row of labelled boxes
restates the paragraph; a drawing of the thing itself (a robot arm reaching for a cup, a person holding a
controller, a server running four simulated environments) lets the reader see what the words refer to.
The author asked for this style after seeing box-only concept figures, so it is the default for concept
figures in this plugin. Architecture figures keep the official AWS icons and are not drawn this way.

## When to draw a scene and when to keep boxes

| The figure shows | Draw it as |
|---|---|
| Something physical or a process with actors: a device, a robot, a person doing a step, data moving between machines, before and after | Scene with pictograms (this file) |
| How a model or component is built from parts, when one end touches the physical world (inputs on the left, the thing acting on the right) | Boxes for the parts, pictograms for the inputs and the result |
| AWS architecture: services, accounts, networks, request paths | `aws-drawio-diagram`, official icons, no pictograms |
| A taxonomy or a comparison of abstract categories with nothing to depict | Box figure with `aws-diagram-design` |

If more than half of the figures in the plan are box figures, look again for the object or the actor each
one is about. A post about a physical system should open with a scene.

## Style

- Canvas 960 px wide (viewBox units); the PNG is rendered at 2x. Height follows the content.
- Three colours carry the drawing: ink `#232F3E` for outlines and solid parts, gray for bodies and
  furniture, orange `#EC7211` for the one thing the reader should follow (joints, the cup, the focal
  model box, intended motion). Green and red appear only in `mark()` for success and failure.
- Solid gray arrows are data or control flow. Dashed orange paths are intended motion or a human link
  (teleoperation, correction). Do not use dashed orange for data.
- Text sizes: 16 px bold for a name, 14 px for a detail line or a sentence, 13 px for the label under an
  object. Nothing smaller. Korean labels, English for product and model names.
- Words come from the post and stay short: a name, a noun, a phrase next to the thing it names. No
  sentence under a drawing or along the bottom of a panel explaining what the picture means. The author
  removed those; the explanation belongs in the paragraph that introduces the figure and in the caption.
- One idea per figure. Two panels side by side for a comparison, three scenes in a row for a sequence.
  A fourth scene means a second figure.
- Everything that stands has something to stand on: `table()` or `ground()`.
- Leave air. No text over a drawing, no drawing touching a panel edge, at least 16 px between a label and
  the next object.

## Pictogram catalog (`assets/illustration/_pict.py`)

| Function | Draws | Anchor |
|---|---|---|
| `arm(a1, a2, hold=False)` via `put_arm(x, y, **GRASP or **CARRY)` | Two-link robot arm with gripper; returns the gripper tip so a path can start there | base centre on the ground |
| `humanoid(x, y, s, step)` | Humanoid robot, walking or standing | ground under the hips |
| `person(x, y, controller=True, flip=False)` | Person with a hand controller, or reaching with one arm | bottom centre of the torso |
| `cup`, `table`, `shelf`, `ground` | Props and floor | bottom centre, top-left, top-left, line |
| `camera(x, y, rot)` | Camera, rotated toward what it sees | centre |
| `frame(x, y, w, h, cupx, lifted, dashed)` | Camera frame thumbnail; dashed outline means predicted or generated | top-left |
| `monitor(x, y, w, h, inner)` | Screen on a stand; put a simulated scene inside | top-left |
| `server`, `db`, `doc` | Server, storage, document | top-left |
| `nn`, `model_box(x, y, w, h, name, sub, focal)` | Network icon; model box with the icon, a name and up to two lines | top-left |
| `mark(x, y, ok)` | Success or failure badge | centre |
| `bubble`, `chip` | Spoken instruction; a small named value | top-left, centre |
| `panel`, `title`, `txt`, `lines`, `arrow`, `motion` | Layout: background panel, name with detail lines, text, flow arrow, dashed motion path | |
| `canvas(slug, title, desc, h, parts)` | Wraps the list of strings into a figure | |

`spec_example.py` in the same directory builds two figures with these and is the pattern to copy.

### Adding a pictogram

A post about a warehouse needs a conveyor, a post about vehicles needs a car. Draw it in the work
directory's copy of `_pict.py`:

1. Decide the anchor (ground contact for things that stand, top-left for boxes) and draw in local
   coordinates around it, 40 to 110 px tall at scale 1.
2. Use the same construction as the existing ones: an ink outline of 1.5 to 2 px on a gray or white body,
   thick round-capped lines for limbs, at most one or two orange parts.
3. Keep it to what identifies the object at 60 px. Eight to fifteen SVG elements is typical.
4. Build a figure that contains only the new pictogram next to an existing one and look at the preview.
   Proportions and stroke weight should match.

If the pictogram will be useful in later posts, copy it back into the skill's `_pict.py`.

## Procedure

1. In the plan, give each concept figure one sentence: what the reader sees, and what they understand
   afterwards. List the objects in it. If you cannot name an object, it is a box figure.
2. Write `<work>/diagrams/_specs/spec_<topic>.py`. Each figure is a function that returns
   `canvas(slug, title, desc, height, parts)`; `build(lang)` returns the list. Place objects first, then
   arrows, then text.
3. Build and look:
   ```bash
   python3 <skill-dir>/scripts/build_figures.py <work>
   ```
   Open `<work>/diagrams/out/preview.png` with Read. The geometry checker of `aws-diagram-design` does not
   see pictograms, so overlaps are found only by looking. Check, for every figure: no text on a drawing
   or on a panel edge, arrows start and end in open space next to the thing they refer to, held objects
   sit in the gripper, nothing is cut by the canvas.
4. Fix coordinates and rebuild until the sheet is clean. Two or three rounds is normal.
5. Install the ones that ship, with their figure numbers:
   ```bash
   python3 <skill-dir>/scripts/build_figures.py <work> --install 1:policy-loop 2:il-vs-rl
   ```
   This writes `images/figN-<slug>.png` and keeps the SVG in `diagrams/`.
6. Verify against the facts as for any figure (`diagrams.md`, "Verification you do yourself"): every
   label, every arrow direction, and every sentence in the picture must match the fact base or the
   research file. Record the row in `diagrams/manifest.md` with skill `illustration`.

Alt text describes the scene ("사람이 조종기로 로봇 팔을 조종하고 ..."), not the layout of boxes.
