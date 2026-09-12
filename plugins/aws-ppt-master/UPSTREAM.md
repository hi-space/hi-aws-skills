# Upstream

- Source: https://github.com/hugohe3/ppt-master (MIT, Copyright (c) 2025-2026 Hugo He)
- Forked at: commit 451c68148e326383651f6319ef6f91dd2932069d (skill version 6.3.2, 2026-09-12)
- Skill directory renamed `skills/ppt-master` → `skills/aws-ppt-master`; all old `skills/ppt-master` path prefixes in docs rewritten.

## Removed
- Image backends other than Bedrock (bfl, fal, gemini, ideogram, minimax, modelscope, openai, openrouter, qwen, replicate, siliconflow, stability, tencent, volcengine, zhipu)
- Narration / TTS / video: notes_to_audio.py, tts_backends/, narration_sync.py, powerpoint_video.py, video_*.py, stages/generate-audio.md, references/video-design.md
- Stock image search: image_search.py, image_sources/, references/image-searcher.md, references/executor-web-image.md
- gemini_watermark_remover.py and its assets
- attribution_guard.py, prompt_audit.py, update_repo.py, SPONSORS*.md and the integrity gate calls in entry scripts

## Added
- scripts/image_backends/backend_bedrock.py (Stability AI on Amazon Bedrock)
- scripts/pptx_qa_check.py + references/copy-voice.md (ported from jesamkim/oh-my-skills myslide 2.0.0, MIT)
- templates/icons/aws/ (304 AWS service icons from myslide); root attribute data-icon-style=preserve-color added so the embedder keeps colours and aspect
- templates/icons/aws/: stripped decorative Illustrator `id="..."` attributes (root `<svg id="Icons">`, `Icon-Architecture*`, `Rectangle`, ...) from all 304 files to stop duplicate-id collisions when an icon is used twice on one page
- scripts/bake_icon_clips.py (plugin-level tool, `pip install skia-pathops`): flattens a rect `<clipPath>` on a `<g>` into real `<path>` geometry instead of stripping it, for icons where the clip is visually load-bearing (not dead code) but still trips the exporter's "clip-path only on `<image>`" rule and duplicate-id collisions. Used to bake the 38 `agentcore-*` "split" icons that carried a live clip (see task-9-fix-report.md); `--check` renders before/after with cairosvg to verify no visible change

## Changed
- Default typography: `Amazon Ember, Noto Sans KR` (fallback `Noto Sans, Noto Sans KR`) instead of the upstream Windows-stock default. Rule in `SKILL.md` (Repository Compatibility), `references/plan-core.md` §6.2, `references/strategist.md` §g.
- `scripts/svg_to_pptx/drawingml/utils.py`: `PPT_SAFE_FONTS` gains `amazon ember`, `amazon ember display`, `amazon ember mono`, `noto sans`, `noto sans kr`, `noto serif kr` (no font-portability warning from export or `pptx_delivery_check.py`); Korean EA fallback in `_EA_DEFAULTS_BY_LANGUAGE` is `Noto Sans KR` / `Noto Serif KR` instead of `Malgun Gothic` / `Batang`. Tests: `scripts/tests/test_aws_font_defaults.py`.
