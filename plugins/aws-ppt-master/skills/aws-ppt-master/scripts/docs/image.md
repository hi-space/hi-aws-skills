# Image Tools

> **Design boundary**: keep provider credentials explicit, keep in-pipeline
> acquisition manifest-driven, and treat external image references as authoring
> inputs while delivery writes self-contained SVG previews and native PPTX
> media.

Image tools cover prompt-based AI generation, project-local treatment, and
image inspection. Native formula authoring belongs to the SVG pipeline, not
the image pipeline.

## Legacy standalone `latex_render.py`

This retained standalone utility renders a user-authored
`images/formula_manifest.json` to PNG. Neither Default nor Quick Generate calls
it, and new projects do not create formula manifests or formula images. The
supported generated-deck path authors a native formula marker in SVG and lets
`svg_to_pptx.py` compile its LaTeX payload to editable PowerPoint OMML.

```bash
python3 scripts/latex_render.py <project_path>
python3 scripts/latex_render.py <project_path> --dry-run
```

Use it only for an explicitly requested external raster workflow. It is not a
compatibility fallback for Keynote, WPS, LibreOffice, or another client.

## `image_gen.py`

Unified image generation entry point.

This script is the **Path A** API/proxy executor for generated images. Default
Generate checks `design_spec.md §I / AI Image Acquisition Path` before manifest
mode: only `api` / `auto` permits Path A; a missing or unknown value fails
closed and returns to Step 4 recovery. Quick Generate has no Design Spec: use
the explicit active-context path when supplied, otherwise `auto` selects the
A → B chain defined in
[`image-generator.md`](../../references/image-generator.md) §7 without asking;
exhausted automation triggers Quick's no-AI replan rather than Offline Manual.
In either profile, `host-native` uses the host image tool directly and an
explicit `manual` choice uses the read-only Markdown sidecar.

```bash
python3 scripts/image_gen.py "A modern futuristic workspace"
python3 scripts/image_gen.py "Abstract tech background" --aspect_ratio 16:9 --image_size 4K
python3 scripts/image_gen.py "Concept car" -o projects/demo/images
python3 scripts/image_gen.py --list-backends
```

The only backend is **Amazon Bedrock** (Stability AI Stable Image). Run
`python3 scripts/image_gen.py --list-backends` to confirm the resolved
configuration.

Aspect ratios accepted by the Bedrock backend (its `VALID_ASPECT_RATIOS`;
`--manifest` rejects any other ratio before sending a request):
`1:1 16:9 21:9 2:3 3:2 4:5 5:4 9:16 9:21`.

Configuration sources:

1. Current process environment variables
2. First `.env` found in this order:
   - Current working directory
   - Skill directory (e.g. `~/.agents/skills/aws-ppt-master/.env`)
   - Clone repo root
   - `~/.ppt-master/.env`

Env keys:

| Key | Required | Notes |
| --- | --- | --- |
| `IMAGE_BACKEND` | no | default `bedrock`, the only valid value |
| `AWS_PROFILE` | no | boto3 default credential chain |
| `AWS_REGION` / `AWS_DEFAULT_REGION` | no | default `us-west-2` (serves Core, Ultra, and SD3.5 Large) |
| `BEDROCK_REGION` | no | overrides `AWS_REGION`/`AWS_DEFAULT_REGION` for image generation only; use when a global `AWS_REGION` doesn't serve the Stability models |
| `BEDROCK_IMAGE_MODEL` | no | default `stability.stable-image-core-v1:1`; aliases below |
| `BEDROCK_NEGATIVE_PROMPT` | no | free text |
| `BEDROCK_SEED` | no | integer 0..4294967295; 0 or unset is random |

Model aliases (`BEDROCK_IMAGE_MODEL` or `--model`):

| Alias | Resolves to |
| --- | --- |
| `core` | `stability.stable-image-core-v1:1` (default) |
| `ultra` | `stability.stable-image-ultra-v1:1` |
| `sd3.5-large` | `stability.sd3-5-large-v1:0` |

Example `.env`:

```env
IMAGE_BACKEND=bedrock
AWS_PROFILE=default
AWS_REGION=us-west-2
BEDROCK_IMAGE_MODEL=core
```

Example process environment:

```bash
export AWS_REGION=us-west-2
export BEDROCK_IMAGE_MODEL=ultra
```

Current process environment wins over `.env`. Credentials always come from
the boto3 default chain (`AWS_PROFILE`, static keys, SSO, or an instance
role) — there is no API key to set.

Bedrock backend notes:
- Enable "Model access" for the Stability model in the Bedrock console of
  the target region before first use.
- `image_size` is accepted for CLI parity but ignored: Stability's Stable
  Image models pick their own output resolution per aspect ratio.
- `AccessDeniedException` means Model access is not enabled, the region does
  not serve the model, or the active credentials cannot call
  `bedrock:InvokeModel`.
- `pip install boto3` if the backend reports a missing dependency.

## `image_gen.py --manifest` runner and legacy manifest spellings

Validates the file behind every `Generated` row before skipping it, iterates retryable rows with bounded adaptive concurrency, and writes each status atomically; a missing or corrupt file returns to `Failed`, and persistent rate limits end the run as retryable `Failed`. Options: `--concurrency` (default `IMAGE_CONCURRENCY` or 3; halves on rate limit, min 1), `--image_size`, `--output`/`-o`, `--backend`/`-b`, `--model`/`-m`, `--list-backends`. Interrupting is safe (completed items stay `Generated`); the Markdown sidecar re-renders on completion, or run `--render-md` after an interruption. Configuration: process environment first, then the first `.env` in cwd, the skill directory, the clone root, `~/.ppt-master/.env` — `IMAGE_BACKEND` (optional; default `bedrock`), `IMAGE_CONCURRENCY`, and the Bedrock keys above (never `IMAGE_API_KEY` / `IMAGE_MODEL` / `IMAGE_BASE_URL`); see `.env.example`. The single-image form `image_gen.py "prompt" --filename …` remains for ad-hoc re-rolls.

**Compatibility**: legacy `type` values read as `background` → `hero_page` + no type, `hero` → `hero_page` + Primitive A, `portrait` → `local` + Primitive B, `typography` → `hero_page` + `embedded` + Primitive C; a missing `page_role` is `local`, a missing `text_policy` is `none` (one aggregate warning per manifest); an existing manifest lacking `deck_rendering` or an item lacking `type` replays its assembled `prompt` verbatim without reconstruction; a legacy `deck_style_anchor` or `deck_palette` never overrides `deck_rendering` / `color_scheme`; legacy `page_role: full_page` reads as `hero_page`.

## `image_treat.py`

Create a non-destructive PNG derivative from one bitmap already prepared under
`<project_path>/images/`. Use this only when a slide needs a baked bitmap effect;
crop, mask, rotation, mirror, opacity, shadow, scrim, outline, and overlap remain
native SVG/PPT treatments. This tool does not perform semantic background
removal: use `slice_images.py --alpha --bg <key> --strict-alpha` for flat-color
keys (a pure red/green/blue key also recovers soft alpha and removes spill from
key-dominant blends, leaving an opaque foreground of the key's hue untouched; thin
dark strokes of that hue can still fringe, so choose the key by hue absence;
strict alpha diagnoses off-key haze from the four 10% key-only margins, allowing
soft shadows and glows on a clean key), an
already prepared RGBA asset or the active host image editor for a standalone cutout, and
[`image-generator.md`](../../references/image-generator.md) §4.4 only for
registered subject/base layers.

```bash
python3 scripts/image_treat.py projects/demo hero.jpg \
  --output hero_soft.png --brightness 0.9 --contrast 1.1 --blur 12

python3 scripts/image_treat.py projects/demo hero.jpg \
  --output hero_duotone.png --duotone "#14213D" "#FCA311"

python3 scripts/image_treat.py projects/demo title_art.png \
  --output title_art_fit.png --fit 920x228
```

Supported operations are brightness, contrast, desaturation/grayscale,
duotone, Gaussian blur, and `--fit WxH` (downscale to fit inside a pixel
box, aspect ratio and alpha preserved; never upscales). They compose in a
fixed order: brightness → contrast → tone treatment → blur → fit. Desaturation, grayscale, and duotone are
mutually exclusive. At least one option must produce a real change; animated
sources are rejected rather than reduced to one frame, while a camera
multi-picture JPEG (MPO) contributes its primary frame.

Both input and output are bare filenames directly under `images/`; output must
be a new `.png` file, or a new `.jpg` file when the source is opaque (a
photograph downscaled with `--fit` keeps its weight in check that way; a
source with transparency is refused for `.jpg`). The tool keeps the EXIF-corrected display dimensions,
leaves any alpha mask unchanged, and never overwrites the source or an existing
derivative. If `images/image_sources.json` contains the source filename, the
new record inherits that legal provenance and records `derived_from` plus the
ordered `treatments`. Run `analyze_images.py` after all planned derivatives are
ready so the inventory reflects the files that SVG authoring will consume.

## `analyze_images.py`

Analyze objective image-file facts in a project directory before writing the
design spec or authoring SVG.

```bash
python3 scripts/analyze_images.py <project_path>/images
```

The tool does not resolve a canvas or recommend a left/right, top/bottom, or
other slide layout. Its atomic CSV records EXIF-corrected native dimensions and
`AspectRatio`, the objective aspect-ratio category, optional source
`SourceDisplayRatio`, format, actual transparent-pixel presence, usage count,
and bitmap/vector capability facts. The usage count (`Uses` in the table) is
how many source occurrences the import manifest recorded for the asset; it is
not a count of SVG references and does not find unused assets. An empty folder rewrites a header-only
report; unreadable supported files still refresh the report and produce a
non-zero exit.

Use this as the default factual inventory; it does not perform semantic image
understanding or choose composition. Generate planning follows the Strategist's
context-first boundary: source context, captions / alt text / titles, filenames,
user notes, and existing resource records come first. Only an already-selected
provided asset whose focal-safe crop, overlay contrast, or quiet region
remains materially ambiguous may be inspected for that placement; this never
reopens selection or provenance, never bulk-opens the image folder, and never
restores routine readback of AI-generated images.
