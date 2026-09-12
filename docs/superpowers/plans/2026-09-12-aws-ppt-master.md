# aws-ppt-master Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fork ppt-master 6.3.2 into `plugins/aws-ppt-master/`, keep only an Amazon Bedrock (Stability) image backend as the external model call, and add three AWS-deck aids ported from myslide: a PPTX layout/copy-voice QA script, a copy-voice reference, and a 304-icon AWS icon library.

**Architecture:** The upstream skill tree is copied verbatim under `skills/aws-ppt-master/` so every relative link in its workflow docs keeps working; removal is done by deleting files and then grepping the tree to zero for each removed name. New code follows the upstream duck-typed backend contract (`generate(...) -> path`) and the upstream test style (`unittest`, `scripts/tests/`). Removed features: 15 image backends, TTS/narration/video, stock image search, watermark remover, attribution guard.

**Tech Stack:** Python 3.10+, boto3 (bedrock-runtime `invoke_model`), python-pptx + lxml (QA), Pillow, unittest.

**Spec:** `docs/superpowers/specs/2026-09-12-aws-ppt-master-design.md`

## Global Constraints

- Repo root for every command: `/home/ubuntu/workspace/hi-aws-skills`. Shorthands used below: `P=plugins/aws-ppt-master`, `S=plugins/aws-ppt-master/skills/aws-ppt-master`.
- Upstream sources already on disk: ppt-master clone `/tmp/ppt-master` (commit `451c68148e326383651f6319ef6f91dd2932069d`), myslide sparse clone `/tmp/oh-my-skills/my-skills/myslide`. Do not fetch again.
- **Never commit or push.** The user commits on request only, as one squashed commit, without any Co-Authored-By line. Every task ends at "tests pass"; there are no commit steps.
- Test runner: `python3 -m unittest discover -s $S/scripts/tests -t $S/scripts/tests -p 'test_*.py'` (upstream has no CI; tests are plain unittest files).
- No new dependency other than `boto3`. `google-genai` and `edge-tts` leave `requirements.txt`.
- Plugin identity: name `aws-ppt-master`, version `1.0.0`, author `hi-space`, license MIT, repository `https://github.com/hi-space/hi-aws-skills`.
- Bedrock defaults: region `us-west-2`, model `stability.stable-image-core-v1:1`; aliases `core`, `ultra` → `stability.stable-image-ultra-v1:1`, `sd3.5-large` → `stability.sd3-5-large-v1:0`. Aspect ratios `1:1 16:9 21:9 2:3 3:2 4:5 5:4 9:16 9:21`.
- Korean user-facing docs (README) in Korean with a short English section; code comments and SKILL.md in English like upstream.
- Every removal task ends with a `grep -rn` over `$P` that must print nothing for the removed names.

---

### Task 1: Copy upstream into the plugin tree and record provenance

**Files:**
- Create: `plugins/aws-ppt-master/skills/aws-ppt-master/**` (copy of `/tmp/ppt-master/skills/ppt-master/`)
- Create: `plugins/aws-ppt-master/.claude-plugin/plugin.json`
- Create: `plugins/aws-ppt-master/requirements.txt`, `plugins/aws-ppt-master/.env.example` (copied, rewritten in Task 5)
- Create: `plugins/aws-ppt-master/UPSTREAM.md`

**Interfaces:**
- Produces: the directory layout every later task edits; `$S/LICENSE` unchanged from upstream (MIT, Hugo He).

- [ ] **Step 1: Copy the skill tree without caches**

```bash
cd /home/ubuntu/workspace/hi-aws-skills
mkdir -p plugins/aws-ppt-master/.claude-plugin plugins/aws-ppt-master/skills
rsync -a --exclude '__pycache__' --exclude '.pytest_cache' --exclude '.in_use' \
  /tmp/ppt-master/skills/ppt-master/ plugins/aws-ppt-master/skills/aws-ppt-master/
cp /tmp/ppt-master/.env.example plugins/aws-ppt-master/.env.example
printf -- '-r skills/aws-ppt-master/requirements.txt\n' > plugins/aws-ppt-master/requirements.txt
```

- [ ] **Step 2: Write plugin.json**

```json
{
  "name": "aws-ppt-master",
  "description": "AWS-flavoured fork of ppt-master: generate natively editable PPTX decks (real DrawingML shapes, text, charts, animations) from Markdown, documents, URLs or a topic. Image generation runs on Amazon Bedrock (Stability AI Stable Image) only; no other API keys. Adds a PPTX layout and Korean copy-voice QA gate and a 304-icon AWS service icon library. Korean triggers: 발표자료, 슬라이드 만들어, AWS 기술 발표, PPT 만들어.",
  "version": "1.0.0",
  "author": { "name": "hi-space" },
  "license": "MIT",
  "keywords": ["pptx", "presentation", "powerpoint", "aws", "bedrock", "stability", "svg", "drawingml", "korean", "qa"],
  "repository": "https://github.com/hi-space/hi-aws-skills"
}
```

Write it to `plugins/aws-ppt-master/.claude-plugin/plugin.json`.

- [ ] **Step 3: Write UPSTREAM.md**

```markdown
# Upstream

- Source: https://github.com/hugohe3/ppt-master (MIT, Copyright (c) 2025-2026 Hugo He)
- Forked at: commit 451c68148e326383651f6319ef6f91dd2932069d (skill version 6.3.2, 2026-09-12)
- Skill directory renamed `skills/ppt-master` → `skills/aws-ppt-master`; all `skills/ppt-master/` path prefixes in docs rewritten.

## Removed
- Image backends other than Bedrock (bfl, fal, gemini, ideogram, minimax, modelscope, openai, openrouter, qwen, replicate, siliconflow, stability, tencent, volcengine, zhipu)
- Narration / TTS / video: notes_to_audio.py, tts_backends/, narration_sync.py, powerpoint_video.py, video_*.py, stages/generate-audio.md, references/video-design.md
- Stock image search: image_search.py, image_sources/, references/image-searcher.md, references/executor-web-image.md
- gemini_watermark_remover.py and its assets
- attribution_guard.py, prompt_audit.py, update_repo.py, SPONSORS*.md and the integrity gate calls in entry scripts

## Added
- scripts/image_backends/backend_bedrock.py (Stability AI on Amazon Bedrock)
- scripts/pptx_qa_check.py + references/copy-voice.md (ported from jesamkim/oh-my-skills myslide 2.0.0, MIT)
- templates/icons/aws/ (304 AWS service icons from myslide)
```

- [ ] **Step 4: Verify the copy**

Run:
```bash
cd /home/ubuntu/workspace/hi-aws-skills
diff -rq --exclude '__pycache__' --exclude '.in_use' /tmp/ppt-master/skills/ppt-master plugins/aws-ppt-master/skills/aws-ppt-master && echo IDENTICAL
find plugins/aws-ppt-master -name '__pycache__' | wc -l
```
Expected: `IDENTICAL` and `0`.

---

### Task 2: Remove the attribution guard and sponsor material

**Files:**
- Delete: `$S/scripts/attribution_guard.py`, `$S/scripts/prompt_audit.py`, `$S/scripts/prompt_audit_manifest.json`, `$S/scripts/update_repo.py`, `$S/SPONSORS.md`, `$S/SPONSORS_CN.md`
- Modify: `$S/scripts/console_encoding.py`
- Modify (remove import + call): `$S/scripts/register_template.py:56,1416`, `project_manager.py:31,80`, `svg_to_pptx.py:23,30`, `template_preview_pptx.py:30,332`, `svg_quality_checker.py:28,62`, `apply_template.py:36,449`, `project_management/cli.py:57,1283`, `svg_quality/cli.py:19,163`, `svg_to_pptx/pptx_package/cli.py:28,1920`
- Modify: `$S/SKILL.md` (frontmatter metadata, Mandatory Load Order step 2, sponsor bullet at line 142)
- Modify: `$S/scripts/README.md` (drop attribution_guard / prompt_audit / update_repo rows)

**Interfaces:**
- Produces: `configure_utf8_stdio()` that only reconfigures streams and installs the transcript hook; every script starts without the integrity check.

- [ ] **Step 1: Write the failing test**

Create `$S/scripts/tests/test_no_attribution_guard.py`:

```python
#!/usr/bin/env python3
"""The fork has no integrity gate: every CLI entry point must start with --help."""

import subprocess
import sys
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
SKILL_DIR = SCRIPTS_DIR.parent

ENTRY_POINTS = [
    "console_encoding.py",
    "project_manager.py",
    "project_management/cli.py",
    "svg_quality_checker.py",
    "svg_quality/cli.py",
    "svg_to_pptx.py",
    "svg_to_pptx/pptx_package/cli.py",
    "register_template.py",
    "template_preview_pptx.py",
    "apply_template.py",
    "image_gen.py",
    "icon_sync.py",
]


class NoAttributionGuardTests(unittest.TestCase):
    def test_guard_files_are_gone(self) -> None:
        for name in ("scripts/attribution_guard.py", "SPONSORS.md", "SPONSORS_CN.md",
                     "scripts/prompt_audit.py", "scripts/prompt_audit_manifest.json"):
            self.assertFalse((SKILL_DIR / name).exists(), name)

    def test_no_source_mentions_guard(self) -> None:
        hits = []
        for path in SKILL_DIR.rglob("*"):
            if path.suffix not in {".py", ".md", ".json", ".txt"} or "tests" in path.parts:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            if "attribution_guard" in text or "require_skill_integrity" in text or "SPONSORS" in text:
                hits.append(str(path.relative_to(SKILL_DIR)))
        self.assertEqual(hits, [])

    def test_entry_points_start_without_exit_78(self) -> None:
        for rel in ENTRY_POINTS:
            with self.subTest(rel):
                proc = subprocess.run([sys.executable, str(SCRIPTS_DIR / rel), "--help"],
                                      capture_output=True, text=True, timeout=120)
                self.assertNotEqual(proc.returncode, 78, proc.stderr)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python3 -m unittest plugins/aws-ppt-master/skills/aws-ppt-master/scripts/tests/test_no_attribution_guard.py -v`
Expected: `test_guard_files_are_gone` FAIL (files exist), `test_no_source_mentions_guard` FAIL.

- [ ] **Step 3: Delete the guard files**

```bash
cd /home/ubuntu/workspace/hi-aws-skills/plugins/aws-ppt-master/skills/aws-ppt-master
git rm -q --cached -r . 2>/dev/null; rm -f scripts/attribution_guard.py scripts/prompt_audit.py scripts/prompt_audit_manifest.json scripts/update_repo.py SPONSORS.md SPONSORS_CN.md
```
(The tree is untracked at this point; plain `rm` is enough. Ignore the `git rm` line if it errors.)

- [ ] **Step 4: Rewrite console_encoding.py**

Replace the whole file with:

```python
#!/usr/bin/env python3
"""Console encoding helpers for aws-ppt-master CLI scripts."""

from __future__ import annotations

import io
import sys
from typing import TextIO

from workflow_transcript import install_auto_transcript


def _reconfigure_stream(stream: TextIO) -> TextIO:
    try:
        stream.reconfigure(encoding="utf-8", errors="replace")
        return stream
    except AttributeError:
        buffer = getattr(stream, "buffer", None)
        if buffer is None:
            return stream
        return io.TextIOWrapper(buffer, encoding="utf-8", errors="replace")
    except (OSError, ValueError):
        return stream


def configure_utf8_stdio() -> None:
    """Configure CLI streams and enable project-scoped output recording."""
    sys.stdout = _reconfigure_stream(sys.stdout)
    sys.stderr = _reconfigure_stream(sys.stderr)
    install_auto_transcript()
```

- [ ] **Step 5: Strip the import and the call from the nine entry scripts**

```bash
cd /home/ubuntu/workspace/hi-aws-skills/plugins/aws-ppt-master/skills/aws-ppt-master/scripts
for f in register_template.py project_manager.py svg_to_pptx.py template_preview_pptx.py \
         svg_quality_checker.py apply_template.py project_management/cli.py svg_quality/cli.py \
         svg_to_pptx/pptx_package/cli.py; do
  sed -i -E '/^from attribution_guard import require_skill_integrity( +# noqa: E402)?$/d; /^ *require_skill_integrity\(\)$/d' "$f"
done
grep -rn 'require_skill_integrity\|attribution_guard' . ; echo "grep exit=$?"
```
Expected: no lines printed, `grep exit=1`.

- [ ] **Step 6: Edit SKILL.md**

In `$S/SKILL.md`:
1. Frontmatter `metadata:` block → replace the `copyright`, `license`, `official_repository`, `sponsors` entries with:
   ```yaml
   metadata:
     version: "1.0.0"
     license: "MIT"
     base: "ppt-master 6.3.2 (https://github.com/hugohe3/ppt-master, MIT, Hugo He)"
     source: "https://github.com/hi-space/hi-aws-skills"
   ```
2. Under `## Mandatory Load Order`, delete the numbered item that runs `attribution_guard.py` and renumber the list 1–4.
3. Under `## Repository Compatibility`, delete the bullet beginning "Sponsor information is optional reference material".
4. In `## Global Execution Discipline` or anywhere else, `grep -n SPONSOR SKILL.md` must return nothing.

- [ ] **Step 7: Remove the rows from scripts/README.md**

Open `$S/scripts/README.md`, delete any table row or paragraph naming `attribution_guard.py`, `prompt_audit.py`, or `update_repo.py`.

- [ ] **Step 8: Run the test to verify it passes**

Run: `python3 -m unittest plugins/aws-ppt-master/skills/aws-ppt-master/scripts/tests/test_no_attribution_guard.py -v`
Expected: 3 tests OK. If an entry point still exits 78, the file still imports `console_encoding` from a stale `__pycache__`; delete `find $S -name __pycache__` and rerun.

---

### Task 3: Remove narration, TTS, and video

**Files:**
- Delete: `$S/scripts/notes_to_audio.py`, `$S/scripts/tts_backends/`, `$S/scripts/narration_sync.py`, `$S/scripts/powerpoint_video.py`, `$S/scripts/video_motion_plan.py`, `$S/scripts/video_sound_mix.py`, `$S/scripts/video_subtitles.py`
- Delete: `$S/workflows/stages/generate-audio.md`, `$S/references/video-design.md`, `$S/scripts/docs/narration.md`, `$S/scripts/docs/video-motion-plan.md`
- Delete: `$S/scripts/tests/test_video_subtitles.py`, `$S/scripts/tests/test_minimax_subtitles.py`
- Modify: `$S/scripts/tests/test_dogfood_leaves_fixes.py` (drop the `narration_sync` import at line 35 and the test at lines 166–174)
- Modify docs: `$S/SKILL.md`, `workflows/routing.md`, `workflows/index.md`, `workflows/generate-pptx.md`, `workflows/profiles/quick-generate.md`, `workflows/edit-native-pptx.md`, `workflows/stages/customize-animations.md`, `workflows/stages/resume-execute.md`, `workflows/governance/failure-recovery.md`, `references/animations.md`, `references/executor-notes.md`, `references/image-base.md:51`, `scripts/docs/pptx-animations.md`, `scripts/docs/svg-pipeline.md`, `scripts/docs/troubleshooting.md`, `scripts/README.md`, `requirements.txt`, `.env.example`
- Keep: `scripts/sound_sync.py`, `templates/sounds/` (CC0 animation sound effects, no network).

**Interfaces:**
- Produces: routing table with Generate (Default / Quick / Image-to-PPTX / Beautify), Create Template, Edit Native PPTX only. Speaker Notes and Custom Animations stay; "Narration Audio" production field disappears.

- [ ] **Step 1: Write the failing test**

Create `$S/scripts/tests/test_removed_features.py` (this file grows in Tasks 4 and 5):

```python
#!/usr/bin/env python3
"""Names of removed upstream features must not survive anywhere in the skill tree."""

import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[2]
TEXT_SUFFIXES = {".py", ".md", ".json", ".txt", ".example", ".yaml", ".yml", ".sh"}

REMOVED_NARRATION = [
    "notes_to_audio", "tts_backends", "narration_sync", "powerpoint_video",
    "video_motion_plan", "video_sound_mix", "video_subtitles",
    "generate-audio", "video-design.md", "edge-tts", "edge_tts", "elevenlabs", "cosyvoice",
    "Narration Audio", "--use-narration-timings", "--recorded-narration",
]


def _hits(needles):
    found = []
    for path in SKILL_DIR.rglob("*"):
        if not path.is_file() or path.suffix not in TEXT_SUFFIXES and path.name != ".env.example":
            continue
        if "tests" in path.parts:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for needle in needles:
            if needle in text:
                found.append(f"{path.relative_to(SKILL_DIR)}: {needle}")
    return found


class RemovedFeatureTests(unittest.TestCase):
    def test_narration_video_gone(self) -> None:
        for rel in ("scripts/notes_to_audio.py", "scripts/tts_backends", "scripts/narration_sync.py",
                    "workflows/stages/generate-audio.md", "references/video-design.md"):
            self.assertFalse((SKILL_DIR / rel).exists(), rel)
        self.assertEqual(_hits(REMOVED_NARRATION), [])

    def test_sound_library_kept(self) -> None:
        self.assertTrue((SKILL_DIR / "scripts/sound_sync.py").exists())
        self.assertTrue((SKILL_DIR / "templates/sounds/README.md").exists())


if __name__ == "__main__":
    unittest.main()
```

Also add `plugins/aws-ppt-master/.env.example` to the scan: after `SKILL_DIR = ...` add `PLUGIN_DIR = SKILL_DIR.parents[1]` and in `_hits` iterate over `list(SKILL_DIR.rglob("*")) + [PLUGIN_DIR / ".env.example"]`.

- [ ] **Step 2: Run it to verify it fails**

Run: `python3 -m unittest plugins/aws-ppt-master/skills/aws-ppt-master/scripts/tests/test_removed_features.py -v`
Expected: `test_narration_video_gone` FAIL with a long list of hits.

- [ ] **Step 3: Delete the scripts, docs, and tests**

```bash
cd /home/ubuntu/workspace/hi-aws-skills/plugins/aws-ppt-master/skills/aws-ppt-master
rm -rf scripts/notes_to_audio.py scripts/tts_backends scripts/narration_sync.py scripts/powerpoint_video.py \
       scripts/video_motion_plan.py scripts/video_sound_mix.py scripts/video_subtitles.py \
       workflows/stages/generate-audio.md references/video-design.md scripts/docs/narration.md scripts/docs/video-motion-plan.md \
       scripts/tests/test_video_subtitles.py scripts/tests/test_minimax_subtitles.py
```

- [ ] **Step 4: Fix test_dogfood_leaves_fixes.py**

Delete line 35 (`from narration_sync import _project_input_path  # noqa: E402`) and the whole method `test_project_input_path_accepts_a_cwd_relative_existing_file` (lines 166–174). Run `python3 -m unittest $S/scripts/tests/test_dogfood_leaves_fixes.py` and confirm it imports and passes.

- [ ] **Step 5: Edit the docs, file by file**

Work through this list; for each hit remove the row, bullet, sentence, or paragraph so the surrounding text still reads. Do not leave "(removed)" notes.

| File | What to change |
|---|---|
| `SKILL.md` | description: delete "requests a presentation-authored narrated/self-running video," ; `## Phase Frame` and elsewhere keep Notes/Animations. |
| `workflows/routing.md` | line 31 route description: drop "/video"; line 33: drop ", narration, timing"; delete the table rows at lines 43 (video-design) and 58 (narration → generate-audio); delete the paragraph at line 98 about narrating through generate-audio. |
| `workflows/index.md` | delete the `generate-audio` row (line 37). |
| `workflows/generate-pptx.md` | line 108 row (video-design) delete; line 174 "Speaker Notes, Custom Animations, and Narration Audio" → "Speaker Notes and Custom Animations"; line 178 paragraph "Prepared final narration" delete; line 180 → "**Output**: `design_spec.md` and `spec_lock.md`."; line 365 drop the sentence "For a narrated MP4, …"; line 377 Next bullet: keep "report the exported PPTX path", drop the narration clause. |
| `workflows/profiles/quick-generate.md` | lines 33, 45, 63, 110–111, 122, 245: same treatment — remove narration/video clauses, keep notes and animations. |
| `workflows/edit-native-pptx.md` | line 13 drop "narration / auto-advance"; line 46 row: drop `audio/`, `video/`; lines 91–92 rows (Narration audio, Auto-advance) delete; line 99 drop "generating audio,"; §6 heading → "## 6. Notes and Motion", delete the "Narration audio" paragraph (line 137); line 149 drop the `--recorded-narration audio --use-narration-timings` clause; line 163 checklist "Notes / audio / motion" → "Notes / motion". |
| `workflows/stages/customize-animations.md` | line 112: delete the sentence about `video_motion_plan.py` / `--conversion-trace` for downstream renderers. |
| `workflows/stages/resume-execute.md`, `workflows/governance/failure-recovery.md` | remove rows/bullets naming generate-audio, narration, or video export. |
| `references/animations.md` | line 249 paragraph on video renderers delete; keep §2.2 sound (sound_sync). |
| `references/executor-notes.md` | delete the audio/TTS subsection (grep `TTS\|audio`); notes authoring stays. |
| `references/image-base.md:51` | "(TTS would speak them)" → delete the parenthetical. |
| `scripts/docs/pptx-animations.md:248`, `scripts/docs/svg-pipeline.md:917`, `scripts/docs/troubleshooting.md:83` | delete the video_motion_plan / narration / edge-tts items. |
| `scripts/README.md` | delete rows for notes_to_audio, narration_sync, powerpoint_video, video_*. |
| `requirements.txt` | delete the "Recorded narration" comment block and `edge-tts>=7.2.8`. |
| `.env.example` (plugin root) | delete the TTS block (it is rewritten fully in Task 5 anyway). |

- [ ] **Step 6: Run the test until it passes**

Run: `python3 -m unittest plugins/aws-ppt-master/skills/aws-ppt-master/scripts/tests/test_removed_features.py -v`
Expected: OK. Each remaining failure line names the file and needle; fix and rerun.

- [ ] **Step 7: Run the whole suite**

Run: `python3 -m unittest discover -s plugins/aws-ppt-master/skills/aws-ppt-master/scripts/tests -t plugins/aws-ppt-master/skills/aws-ppt-master/scripts/tests -p 'test_*.py' 2>&1 | tail -5`
Expected: OK (some upstream tests may be skipped when optional binaries are missing; failures are not acceptable).

---

### Task 4: Remove stock image search and the watermark remover

**Files:**
- Delete: `$S/scripts/image_search.py`, `$S/scripts/image_sources/`, `$S/references/image-searcher.md`, `$S/references/executor-web-image.md`, `$S/scripts/gemini_watermark_remover.py`, `$S/scripts/assets/bg_48.png`, `$S/scripts/assets/bg_96.png`, `$S/scripts/tests/test_image_search.py`
- Modify: `$S/scripts/image_treat.py:58-67` (inline the two manifest helpers), `$S/scripts/svg_quality/checker.py:6608`, `$S/scripts/tests/test_slice_images.py:345-357`
- Modify docs: `references/image-base.md` (web row at line 24, "An all-`web` deck…" sentence), `references/executor-image.md:14-15`, `references/executor-base.md:20`, `references/svg-image-embedding.md:27`, `references/image-generator.md` (any `image_search` mention), `scripts/README.md`, `scripts/docs/image.md`, `scripts/docs/troubleshooting.md`, `requirements.txt` (gemini_watermark_remover comment lines), `.env.example` (PEXELS/PIXABAY block)

**Interfaces:**
- Produces: `image_treat.py` self-contained with `_read_sources_manifest(path) -> dict` and `_write_sources_manifest(path, item) -> Path` implemented locally (same behaviour as upstream `image_search._read_existing_manifest` / `write_sources_manifest`).

- [ ] **Step 1: Extend the failing test**

In `$S/scripts/tests/test_removed_features.py` add:

```python
REMOVED_SEARCH = [
    "image_search", "image_sources/", "image-searcher", "executor-web-image",
    "gemini_watermark_remover", "PEXELS_API_KEY", "PIXABAY_API_KEY", "openverse", "wikimedia",
]


class RemovedSearchTests(unittest.TestCase):
    def test_search_and_watermark_gone(self) -> None:
        for rel in ("scripts/image_search.py", "scripts/image_sources", "references/image-searcher.md",
                    "references/executor-web-image.md", "scripts/gemini_watermark_remover.py",
                    "scripts/assets/bg_48.png", "scripts/assets/bg_96.png"):
            self.assertFalse((SKILL_DIR / rel).exists(), rel)
        self.assertEqual(_hits(REMOVED_SEARCH), [])

    def test_image_treat_still_imports(self) -> None:
        import importlib, sys
        sys.path.insert(0, str(SKILL_DIR / "scripts"))
        mod = importlib.import_module("image_treat")
        self.assertTrue(callable(mod._read_sources_manifest))
        self.assertTrue(callable(mod._write_sources_manifest))
```

Note: `image_sources.json` (the per-project manifest filename) is still legitimate; the needle is `image_sources/` with the slash.

- [ ] **Step 2: Run it to verify it fails**

Run: `python3 -m unittest plugins/aws-ppt-master/skills/aws-ppt-master/scripts/tests/test_removed_features.py -k Search -v`
Expected: `test_search_and_watermark_gone` FAIL.

- [ ] **Step 3: Move the manifest helpers into image_treat.py**

Copy the bodies of `_read_existing_manifest` (upstream `image_search.py:1312-1378`) and `write_sources_manifest` (`:1380-1420`, ends where the function returns `manifest_path`) plus the helper `_validate_bare_filename` they call (find it with `grep -n 'def _validate_bare_filename' image_search.py`) into `image_treat.py` above `_read_sources_manifest`. Then change the two wrappers to:

```python
def _read_sources_manifest(path: Path) -> dict:
    return _read_existing_manifest(path)


def _write_sources_manifest(path: Path, item: dict) -> Path:
    return write_sources_manifest(path, item)
```

Add `import json` to `image_treat.py` if not already imported. Do this **before** deleting `image_search.py` so you can copy from the plugin tree.

- [ ] **Step 4: Delete the files**

```bash
cd /home/ubuntu/workspace/hi-aws-skills/plugins/aws-ppt-master/skills/aws-ppt-master
rm -rf scripts/image_search.py scripts/image_sources references/image-searcher.md references/executor-web-image.md \
       scripts/gemini_watermark_remover.py scripts/assets/bg_48.png scripts/assets/bg_96.png scripts/tests/test_image_search.py
rmdir scripts/assets 2>/dev/null || true
```

- [ ] **Step 5: Fix the two code references and the test**

- `scripts/svg_quality/checker.py:6608`: the message string mentions `image_search.py records the legal tier in images/image_sources.json;` → rewrite to `the image sources manifest images/image_sources.json records the legal tier;`.
- `scripts/tests/test_slice_images.py`: delete the method `test_watermark_processing_applies_orientation` (lines 345–357).

- [ ] **Step 6: Edit the docs**

| File | Change |
|---|---|
| `references/image-base.md` | delete the `web` row (line 24) and the sentence "An all-`web` deck never reads `image-generator.md`, and vice versa." |
| `references/executor-image.md:14-15` | row 14: drop "a manifest-backed file also loads executor-web-image.md"; row 15 (`Sourced`): delete the row. |
| `references/executor-base.md:20` | delete the trigger row for executor-web-image. |
| `references/svg-image-embedding.md:27` | delete the `Sourced` row. |
| `references/image-generator.md` | `grep -n image_search` → delete each sentence. |
| `scripts/README.md`, `scripts/docs/image.md`, `scripts/docs/troubleshooting.md` | delete sections/rows for image_search.py, image_sources, gemini_watermark_remover. |
| `requirements.txt` | delete the two `gemini_watermark_remover.py` comment lines; keep Pillow and numpy (used elsewhere). |
| `.env.example` | delete the image search block. |

Where a doc says an image's `Status` can be `Sourced`, remove `Sourced` from the enumeration; remaining statuses are `Existing`, `Generated`, `Placeholder`.

- [ ] **Step 7: Run the tests**

Run: `python3 -m unittest plugins/aws-ppt-master/skills/aws-ppt-master/scripts/tests/test_removed_features.py plugins/aws-ppt-master/skills/aws-ppt-master/scripts/tests/test_slice_images.py -v 2>&1 | tail -5`
Expected: OK.

---

### Task 5: Bedrock (Stability) image backend

**Files:**
- Delete: `$S/scripts/image_backends/backend_{bfl,fal,gemini,ideogram,minimax,modelscope,openai,openrouter,qwen,replicate,siliconflow,stability,tencent,volcengine,zhipu}.py`, `$S/scripts/tests/test_image_backend_tencent.py`, `$S/references/ai-image-comparison/` (provider comparison sheets; keep only if they contain no provider names — they do, delete)
- Create: `$S/scripts/image_backends/backend_bedrock.py`
- Create: `$S/scripts/tests/test_image_backend_bedrock.py`
- Modify: `$S/scripts/image_gen.py` (docstring lines 7–22, `IMAGE_ENV_PREFIXES` 66–88, `BACKEND_REGISTRY` 106–241, `_load_image_env_file`/`_validate_runtime_config` replacement strings, `_BACKEND_PIP_HINTS` 300–303, `_resolve_backend` 402–435)
- Modify: `$S/requirements.txt` (google-genai → boto3), `$P/.env.example` (rewrite), `$S/scripts/docs/image.md`, `$S/references/image-generator.md` (§ IMAGE_BACKEND / Path A wording), `$S/references/plan-core.md:121`, `$S/scripts/README.md`, `$S/scripts/docs/troubleshooting.md`, `$S/workflows/generate-pptx.md:199,208`, `$S/references/ai-image-comparison/README.md` references from other docs

**Interfaces:**
- Consumes: `image_backends.backend_common` — `MAX_RETRIES`, `resolve_output_path(prompt, output_dir, filename, ext) -> str`, `save_image_bytes(image_bytes, path, content_type=None) -> str`, `report_resolution(path)`, `retry_delay(attempt, rate_limited) -> int`, `normalize_image_size(image_size) -> str`.
- Produces: module `backend_bedrock` with `VALID_ASPECT_RATIOS`, `SUPPORTS_REFERENCE_IMAGE = False`, `DEFAULT_MODEL`, `MODEL_ALIASES`, `generate(prompt, aspect_ratio="1:1", image_size="1K", output_dir=None, filename=None, model=None, max_retries=MAX_RETRIES) -> str`, and `_client(region) -> boto3 client` (patched in tests).

- [ ] **Step 1: Write the failing tests**

Create `$S/scripts/tests/test_image_backend_bedrock.py`:

```python
#!/usr/bin/env python3
"""Regression tests for the Amazon Bedrock (Stability AI) image backend."""

import base64
import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import ExitStack, redirect_stdout
from pathlib import Path
from unittest.mock import Mock, patch

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import image_gen  # noqa: E402
from image_backends import backend_bedrock  # noqa: E402

PNG_1x1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
)


class _ClientError(Exception):
    def __init__(self, code: str, message: str = "boom") -> None:
        super().__init__(f"{code}: {message}")
        self.response = {"Error": {"Code": code, "Message": message}}


def _body(payload: dict) -> dict:
    return {"body": io.BytesIO(json.dumps(payload).encode("utf-8"))}


class BedrockBackendTests(unittest.TestCase):
    def setUp(self) -> None:
        stack = ExitStack()
        self.addCleanup(stack.close)
        stack.enter_context(patch.dict(os.environ, {}, clear=True))
        stack.enter_context(redirect_stdout(io.StringIO()))
        stack.enter_context(patch("time.sleep"))
        self.client = Mock()
        self.client.invoke_model.return_value = _body(
            {"seeds": [1], "finish_reasons": [None], "images": [base64.b64encode(PNG_1x1).decode()]}
        )
        stack.enter_context(patch.object(backend_bedrock, "_client", return_value=self.client))
        self.tmp = stack.enter_context(tempfile.TemporaryDirectory())

    def _generate(self, **kw):
        return backend_bedrock.generate("a robot arm", output_dir=self.tmp, filename="robot.png", **kw)

    def test_writes_png_and_sends_stability_body(self) -> None:
        path = self._generate(aspect_ratio="16:9")
        self.assertTrue(Path(path).is_file())
        self.assertEqual(Path(path).read_bytes()[:8], PNG_1x1[:8])
        call = self.client.invoke_model.call_args.kwargs
        self.assertEqual(call["modelId"], "stability.stable-image-core-v1:1")
        body = json.loads(call["body"])
        self.assertEqual(body, {"prompt": "a robot arm", "aspect_ratio": "16:9", "output_format": "png", "mode": "text-to-image"})

    def test_env_seed_negative_prompt_and_model_alias(self) -> None:
        os.environ.update({"BEDROCK_IMAGE_MODEL": "ultra", "BEDROCK_SEED": "42", "BEDROCK_NEGATIVE_PROMPT": "text, watermark"})
        self._generate()
        call = self.client.invoke_model.call_args.kwargs
        self.assertEqual(call["modelId"], "stability.stable-image-ultra-v1:1")
        body = json.loads(call["body"])
        self.assertEqual(body["seed"], 42)
        self.assertEqual(body["negative_prompt"], "text, watermark")

    def test_explicit_model_argument_wins(self) -> None:
        os.environ["BEDROCK_IMAGE_MODEL"] = "ultra"
        self._generate(model="sd3.5-large")
        self.assertEqual(self.client.invoke_model.call_args.kwargs["modelId"], "stability.sd3-5-large-v1:0")

    def test_rejects_unsupported_aspect_ratio(self) -> None:
        with self.assertRaises(ValueError):
            self._generate(aspect_ratio="4:3")
        self.client.invoke_model.assert_not_called()

    def test_accepts_and_ignores_image_size(self) -> None:
        self._generate(image_size="2K")
        self.assertNotIn("image_size", json.loads(self.client.invoke_model.call_args.kwargs["body"]))

    def test_region_default_and_override(self) -> None:
        self._generate()
        backend_bedrock._client.assert_called_with("us-west-2")
        os.environ["AWS_REGION"] = "ap-northeast-2"
        self._generate()
        backend_bedrock._client.assert_called_with("ap-northeast-2")

    def test_throttling_retries_then_succeeds(self) -> None:
        ok = self.client.invoke_model.return_value
        self.client.invoke_model.side_effect = [_ClientError("ThrottlingException"), ok]
        path = self._generate()
        self.assertTrue(Path(path).is_file())
        self.assertEqual(self.client.invoke_model.call_count, 2)

    def test_access_denied_is_permanent_with_hint(self) -> None:
        self.client.invoke_model.side_effect = _ClientError("AccessDeniedException")
        with self.assertRaises(RuntimeError) as ctx:
            self._generate(max_retries=3)
        self.assertEqual(self.client.invoke_model.call_count, 1)
        self.assertIn("Model access", str(ctx.exception))

    def test_filtered_output_raises(self) -> None:
        self.client.invoke_model.return_value = _body({"seeds": [1], "finish_reasons": ["Filter reason: prompt"], "images": [""]})
        with self.assertRaises(RuntimeError) as ctx:
            self._generate(max_retries=0)
        self.assertIn("Filter reason: prompt", str(ctx.exception))


class ImageGenRegistryTests(unittest.TestCase):
    def test_registry_has_only_bedrock(self) -> None:
        self.assertEqual(sorted(image_gen.BACKEND_REGISTRY), ["bedrock"])
        self.assertEqual(image_gen.BACKEND_REGISTRY["bedrock"]["module"], "backend_bedrock")
        self.assertEqual(image_gen.BACKEND_REGISTRY["bedrock"]["default_model"], "stability.stable-image-core-v1:1")

    def test_env_prefixes_include_aws(self) -> None:
        self.assertIn("AWS_", image_gen.IMAGE_ENV_PREFIXES)
        self.assertIn("BEDROCK_", image_gen.IMAGE_ENV_PREFIXES)
        for stale in ("GEMINI_", "OPENAI_", "STABILITY_"):
            self.assertNotIn(stale, image_gen.IMAGE_ENV_PREFIXES)

    def test_default_backend_is_bedrock(self) -> None:
        with patch.dict(os.environ, {}, clear=True), redirect_stdout(io.StringIO()):
            module, name = image_gen._resolve_backend()
        self.assertEqual(name, "bedrock")
        self.assertIs(module, backend_bedrock)

    def test_no_other_backend_files(self) -> None:
        files = sorted(p.name for p in (SCRIPTS_DIR / "image_backends").glob("backend_*.py"))
        self.assertEqual(files, ["backend_bedrock.py", "backend_common.py"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run to verify it fails**

Run: `python3 -m unittest plugins/aws-ppt-master/skills/aws-ppt-master/scripts/tests/test_image_backend_bedrock.py -v 2>&1 | tail -3`
Expected: ImportError `cannot import name 'backend_bedrock'`.

- [ ] **Step 3: Delete the other backends and the provider comparison sheets**

```bash
cd /home/ubuntu/workspace/hi-aws-skills/plugins/aws-ppt-master/skills/aws-ppt-master
cd scripts/image_backends && ls backend_*.py | grep -v -e backend_common.py | xargs rm -f && cd ../..
rm -f scripts/tests/test_image_backend_tencent.py
rm -rf references/ai-image-comparison
ls scripts/image_backends
```
Expected: `__init__.py  backend_common.py`.

- [ ] **Step 4: Write backend_bedrock.py**

```python
#!/usr/bin/env python3
"""
Amazon Bedrock image generation backend (Stability AI Stable Image models).

Credentials come from the boto3 default chain (AWS_PROFILE, env keys, SSO, instance role).
Configuration keys (process environment or the resolved .env):
  AWS_REGION / AWS_DEFAULT_REGION   optional, default us-west-2
  AWS_PROFILE                       optional
  BEDROCK_IMAGE_MODEL               optional, default stability.stable-image-core-v1:1
                                    aliases: core | ultra | sd3.5-large
  BEDROCK_NEGATIVE_PROMPT           optional
  BEDROCK_SEED                      optional integer 0..4294967295
"""

import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from console_encoding import configure_utf8_stdio  # noqa: E402

configure_utf8_stdio()

if __name__ == "__main__":
    print(__doc__)
    print("Use via: python3 skills/aws-ppt-master/scripts/image_gen.py \"prompt\" --backend bedrock")
    raise SystemExit(0 if any(arg in {"-h", "--help", "help"} for arg in sys.argv[1:]) else 1)

import base64  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import time  # noqa: E402

from image_backends.backend_common import (  # noqa: E402
    MAX_RETRIES,
    normalize_image_size,
    report_resolution,
    resolve_output_path,
    retry_delay,
    save_image_bytes,
)

VALID_ASPECT_RATIOS = ["1:1", "16:9", "21:9", "2:3", "3:2", "4:5", "5:4", "9:16", "9:21"]
SUPPORTS_REFERENCE_IMAGE = False

DEFAULT_REGION = "us-west-2"
DEFAULT_MODEL = "stability.stable-image-core-v1:1"
MODEL_ALIASES = {
    "core": "stability.stable-image-core-v1:1",
    "stable-image-core": "stability.stable-image-core-v1:1",
    "ultra": "stability.stable-image-ultra-v1:1",
    "stable-image-ultra": "stability.stable-image-ultra-v1:1",
    "sd3.5-large": "stability.sd3-5-large-v1:0",
    "sd3-5-large": "stability.sd3-5-large-v1:0",
}

# Errors that a retry will not fix. Anything else (throttling, model busy, 5xx) is retried.
PERMANENT_ERROR_CODES = {
    "AccessDeniedException",
    "ValidationException",
    "ResourceNotFoundException",
    "UnrecognizedClientException",
    "InvalidSignatureException",
    "ExpiredTokenException",
}

_PERMANENT_HINT = (
    "Bedrock refused the request. Check: (1) Model access for the Stability model is enabled in the "
    "Bedrock console for this region, (2) AWS_REGION points at a region that serves the model "
    "(us-west-2 serves all three), (3) the active credentials (AWS_PROFILE) may call bedrock:InvokeModel."
)


def _resolve_model(model: str | None) -> str:
    raw = (model or os.environ.get("BEDROCK_IMAGE_MODEL") or DEFAULT_MODEL).strip()
    return MODEL_ALIASES.get(raw.lower(), raw)


def _resolve_region() -> str:
    return os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION") or DEFAULT_REGION


def _validate_request_options(aspect_ratio: str, image_size: str) -> None:
    if aspect_ratio not in VALID_ASPECT_RATIOS:
        raise ValueError(
            f"Unsupported aspect ratio '{aspect_ratio}' for the Bedrock Stability backend. "
            f"Supported: {VALID_ASPECT_RATIOS}"
        )
    normalize_image_size(image_size)  # accepted for CLI parity; Stability picks its own size per aspect ratio


def _client(region: str):
    """Build the bedrock-runtime client. Imported lazily so --help works without boto3."""
    try:
        import boto3
    except ImportError as exc:  # pragma: no cover - exercised by image_gen's pip hint
        raise ImportError("boto3 is required for the bedrock backend: pip install boto3") from exc
    return boto3.client("bedrock-runtime", region_name=region)


def _build_body(prompt: str, aspect_ratio: str) -> dict:
    body = {
        "prompt": prompt,
        "aspect_ratio": aspect_ratio,
        "output_format": "png",
        "mode": "text-to-image",
    }
    negative = os.environ.get("BEDROCK_NEGATIVE_PROMPT", "").strip()
    if negative:
        body["negative_prompt"] = negative
    seed = os.environ.get("BEDROCK_SEED", "").strip()
    if seed:
        body["seed"] = int(seed)
    return body


def _error_code(exc: Exception) -> str | None:
    response = getattr(exc, "response", None)
    if isinstance(response, dict):
        return response.get("Error", {}).get("Code")
    return None


def _is_permanent(exc: Exception) -> bool:
    return isinstance(exc, ValueError) or _error_code(exc) in PERMANENT_ERROR_CODES


def _generate_image(client, prompt: str, aspect_ratio: str, output_dir: str | None,
                    filename: str | None, model_id: str) -> str:
    body = _build_body(prompt, aspect_ratio)
    print("[Amazon Bedrock / Stability AI]")
    print(f"  Model:        {model_id}")
    print(f"  Prompt:       {prompt[:120]}{'...' if len(prompt) > 120 else ''}")
    print(f"  Aspect Ratio: {aspect_ratio}")
    print()
    print("  [..] Generating...", end="", flush=True)
    start = time.time()
    response = client.invoke_model(modelId=model_id, body=json.dumps(body))
    payload = json.loads(response["body"].read().decode("utf-8"))
    elapsed = time.time() - start
    print(f"\n  [DONE] Response received ({elapsed:.1f}s)")

    reasons = payload.get("finish_reasons") or [None]
    if reasons[0]:
        raise RuntimeError(f"Bedrock filtered the request: {reasons[0]}. Rephrase the prompt.")
    images = payload.get("images") or []
    if not images:
        raise RuntimeError("Bedrock returned no image data.")

    path = resolve_output_path(prompt, output_dir, filename, ".png")
    saved = save_image_bytes(base64.b64decode(images[0]), path, "image/png")
    print(f"  File saved to: {saved}")
    report_resolution(saved)
    return saved


def generate(prompt: str,
             aspect_ratio: str = "1:1", image_size: str = "1K",
             output_dir: str = None, filename: str = None,
             model: str = None, max_retries: int = MAX_RETRIES) -> str:
    """Generate one image on Amazon Bedrock with retries for transient errors."""
    _validate_request_options(aspect_ratio, image_size)
    model_id = _resolve_model(model)
    client = _client(_resolve_region())

    last_error = None
    for attempt in range(max_retries + 1):
        try:
            return _generate_image(client, prompt, aspect_ratio, output_dir, filename, model_id)
        except Exception as exc:
            last_error = exc
            if _is_permanent(exc):
                if isinstance(exc, ValueError):
                    raise
                raise RuntimeError(f"{exc}\n{_PERMANENT_HINT}") from exc
            if isinstance(exc, RuntimeError) and "filtered" in str(exc):
                raise
            if attempt >= max_retries:
                break
            limited = _error_code(exc) == "ThrottlingException"
            delay = retry_delay(attempt, rate_limited=limited)
            print(f"\n  [WARN] {'Throttled' if limited else f'Error: {exc}'}. Retrying in {delay}s...")
            time.sleep(delay)

    raise RuntimeError(f"Failed after {max_retries + 1} attempts. Last error: {last_error}")
```

- [ ] **Step 5: Rewrite the registry and env handling in image_gen.py**

1. Module docstring (lines 7–22): replace the provider list with one line: `Backend: bedrock (Amazon Bedrock, Stability AI Stable Image Core / Ultra / SD3.5 Large).`
2. `IMAGE_ENV_PREFIXES = ("IMAGE_", "AWS_", "BEDROCK_")`.
3. `BACKEND_REGISTRY`:
   ```python
   BACKEND_REGISTRY = {
       "bedrock": {
           "module": "backend_bedrock",
           "tier": "core",
           "label": "Amazon Bedrock (Stability AI)",
           "default_model": "stability.stable-image-core-v1:1",
           "default_image_size": "1K",
           "key_hint": "AWS credentials (AWS_PROFILE) + AWS_REGION",
           "aliases": ["aws", "stability"],
       },
   }
   ```
4. In `_load_image_env_file` and `_validate_runtime_config`, replace the three `replacements` strings with `"BEDROCK_IMAGE_MODEL / AWS_REGION"` (the deprecated-key rejection stays).
5. `_BACKEND_PIP_HINTS = {"bedrock": "boto3"}`.
6. `_resolve_backend`: `backend_name = os.environ.get("IMAGE_BACKEND", "bedrock").strip().lower() or "bedrock"`; delete the "No image backend configured" branch entirely (unreachable now).
7. `grep -n 'openai\|gemini\|OPENAI\|GEMINI' image_gen.py` → rewrite every remaining help string to mention only bedrock.

- [ ] **Step 6: Run the tests**

Run: `python3 -m unittest plugins/aws-ppt-master/skills/aws-ppt-master/scripts/tests/test_image_backend_bedrock.py -v`
Expected: 13 tests OK.

- [ ] **Step 7: requirements.txt and .env.example**

`$S/requirements.txt`: replace the "AI image generation tool" block with:
```
# ─────────────────────────────────────────────────────────────
# AI image generation / AI 이미지 생성 (skills/aws-ppt-master/scripts/image_gen.py)
# ─────────────────────────────────────────────────────────────
# Amazon Bedrock backend (Stability AI Stable Image). Credentials via the boto3 default chain.
boto3>=1.34.0
```

`$P/.env.example` — replace the whole file with:
```
# aws-ppt-master image generation / 이미지 생성 설정
# Optional fallback for image_gen.py. Process environment variables win over this file.
# Resolution order (first existing file only): ./.env → <skill-dir>/.env → <repo-root>/.env → ~/.ppt-master/.env
#
# The only backend is Amazon Bedrock. Credentials come from the boto3 default chain:
# AWS_PROFILE, AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY, SSO, or an instance role.
# 유일한 백엔드는 Amazon Bedrock 입니다. 자격 증명은 boto3 기본 체인을 따릅니다.
# Enable "Model access" for the Stability model in the Bedrock console of AWS_REGION first.

# IMAGE_BACKEND=bedrock                          # default; the only valid value
# AWS_PROFILE=default
# AWS_REGION=us-west-2                           # us-west-2 serves Core, Ultra and SD3.5 Large
# BEDROCK_IMAGE_MODEL=stability.stable-image-core-v1:1
#   aliases: core | ultra (stability.stable-image-ultra-v1:1) | sd3.5-large (stability.sd3-5-large-v1:0)
# BEDROCK_NEGATIVE_PROMPT=text, watermark, logo
# BEDROCK_SEED=0                                 # 0 or unset = random
# IMAGE_CONCURRENCY=3                            # --manifest batch concurrency; halves on throttling
```

- [ ] **Step 8: Rewrite the backend docs**

- `$S/scripts/docs/image.md`: replace the per-provider sections under `image_gen.py` with one "Amazon Bedrock (Stability AI)" section: env keys (table above), model aliases, aspect ratios, the `--manifest` and single-prompt invocations unchanged, and a troubleshooting list (AccessDeniedException → enable model access; region; `pip install boto3`).
- `$S/references/image-generator.md:331-359`: keep Path A / Path B text but rewrite "IMAGE_BACKEND gates auto" to "IMAGE_BACKEND defaults to `bedrock`; Path A is available whenever AWS credentials resolve".
- `$S/references/plan-core.md:121`, `$S/workflows/generate-pptx.md:199,208`, `$S/scripts/README.md`, `$S/scripts/docs/troubleshooting.md`: remove provider names; say "Bedrock backend".
- Delete every link to `ai-image-comparison/` (`grep -rn ai-image-comparison $S`).

- [ ] **Step 9: Extend test_removed_features.py and run everything**

Add to `REMOVED_SEARCH` (or a new list `REMOVED_BACKENDS`) the needles `"backend_gemini", "backend_openai", "GEMINI_API_KEY", "OPENAI_API_KEY", "STABILITY_API_KEY", "google-genai", "google.genai", "ai-image-comparison", "IMAGE_BACKEND=openai", "IMAGE_BACKEND=gemini"` with a test `test_backends_gone`. Run:

`python3 -m unittest discover -s plugins/aws-ppt-master/skills/aws-ppt-master/scripts/tests -t plugins/aws-ppt-master/skills/aws-ppt-master/scripts/tests -p 'test_*.py' 2>&1 | tail -5`
Expected: OK.

- [ ] **Step 10: One live call**

```bash
cd /home/ubuntu/workspace/hi-aws-skills
AWS_REGION=us-west-2 python3 plugins/aws-ppt-master/skills/aws-ppt-master/scripts/image_gen.py \
  "flat vector illustration of a robot arm sorting parcels, orange and navy palette, clean white background" \
  --aspect-ratio 16:9 --output-dir /tmp/bedrock-smoke --filename smoke.png
python3 -c "from PIL import Image; im=Image.open('/tmp/bedrock-smoke/smoke.png'); print(im.size)"
```
Expected: `Using backend: bedrock`, a PNG whose width/height ratio is about 16:9 (Stability Core returns 1344×768 or similar). If `AccessDeniedException`: the account needs Model access enabled for Stability in us-west-2; report that instead of retrying. Check the exact `--aspect-ratio` / `--output-dir` flag names with `image_gen.py --help` first.

---

### Task 6: PPTX layout and copy-voice QA (ported from myslide)

**Files:**
- Create: `$S/scripts/pptx_qa_check.py` (from `/tmp/oh-my-skills/my-skills/myslide/scripts/qa_validate.py`)
- Create: `$S/scripts/tests/test_pptx_qa_check.py` (from myslide `test_qa_checks.py`), `$S/scripts/tests/test_pptx_qa_copy.py` (from myslide `test_ai_copy.py`)
- Create: `$S/references/copy-voice.md` (from myslide `references/copy-voice.md`)
- Modify: `$S/workflows/generate-pptx.md` (Step 7 export block, near line 367), `$S/workflows/profiles/quick-generate.md` (export section near line 229), `$S/workflows/edit-native-pptx.md` (export/checklist near line 163), `$S/references/executor-base.md` (trigger table), `$S/scripts/README.md`

**Interfaces:**
- Produces: CLI `python3 scripts/pptx_qa_check.py <deck.pptx> [--checks bounds,connectors,font_size,zero_size,image_aspect,copy] [--json] [--strict]`; exit 0 clean / 1 critical found / 2 error. Python API `validate(pptx_path, strict=False, checks=None) -> (issues, prs)`, `check_ai_copy(prs) -> list[Issue]`, `Issue.level in {"critical","warning","info"}`, `Issue.slide_num`.

- [ ] **Step 1: Port the tests first**

```bash
cd /home/ubuntu/workspace/hi-aws-skills/plugins/aws-ppt-master/skills/aws-ppt-master/scripts
cp /tmp/oh-my-skills/my-skills/myslide/scripts/test_qa_checks.py tests/test_pptx_qa_check.py
cp /tmp/oh-my-skills/my-skills/myslide/scripts/test_ai_copy.py tests/test_pptx_qa_copy.py
```

Edit both files:
- `sys.path.insert(0, str(Path(__file__).resolve().parent))` → `sys.path.insert(0, str(Path(__file__).resolve().parents[1]))`.
- `import qa_validate as qa` / `import qa_validate as qv` → `import pptx_qa_check as qa` / `import pptx_qa_check as qv`.
- In `test_pptx_qa_copy.py`, wrap the script so unittest discovers it: rename `def main():` to `def collect_failures():` and make it `return failures` (delete the `print` / `return 1 if failures else 0` tail), then append:

```python
class CopyVoiceTests(unittest.TestCase):
    def test_all_cases(self) -> None:
        failures = collect_failures()
        self.assertEqual(failures, [], "\n".join(failures))


if __name__ == "__main__":
    unittest.main()
```
and add `import unittest` at the top. Remove the old `if __name__ == "__main__": sys.exit(main())` block.

Also add to `tests/test_pptx_qa_check.py` one new test for the `--checks` filter:

```python
class ChecksFilterTests(unittest.TestCase):
    def test_checks_filter_limits_run(self) -> None:
        import tempfile
        prs = _new_prs()
        s = prs.slides.add_slide(prs.slide_layouts[6])
        tb = s.shapes.add_textbox(Inches(1), Inches(1), Inches(4), Inches(1))
        tb.text_frame.text = "제목 — 부제"          # em dash: copy critical
        tb.text_frame.paragraphs[0].runs[0].font.size = Pt(10)   # add `Pt` to the pptx.util import
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "t.pptx"
            prs.save(path)
            only_copy, _ = qa.validate(str(path), checks=["copy"])
            only_bounds, _ = qa.validate(str(path), checks=["bounds"])
        self.assertTrue(any(i.check == "ai_copy" for i in only_copy))
        self.assertFalse(any(i.check == "ai_copy" for i in only_bounds))
```
(`Issue` fields are `level`, `slide_num`, `check`, `message`; the copy detector sets `check="ai_copy"`. Confirm with `grep -n 'Issue(' pptx_qa_check.py | head` after porting; if the copy check uses another string, use that one.)

- [ ] **Step 2: Run to verify they fail**

Run: `python3 -m unittest plugins/aws-ppt-master/skills/aws-ppt-master/scripts/tests/test_pptx_qa_check.py plugins/aws-ppt-master/skills/aws-ppt-master/scripts/tests/test_pptx_qa_copy.py 2>&1 | tail -3`
Expected: `ModuleNotFoundError: No module named 'pptx_qa_check'`.

- [ ] **Step 3: Port the checker**

```bash
cp /tmp/oh-my-skills/my-skills/myslide/scripts/qa_validate.py plugins/aws-ppt-master/skills/aws-ppt-master/scripts/pptx_qa_check.py
```
Edit `pptx_qa_check.py`:
1. Docstring: title `PPTX Layout & Copy QA (aws-ppt-master)`; replace references to "SKILL.md > Decoration Discipline" and "the Agenda separator" with neutral wording ("a low-alpha full-bleed wash ellipse", "a horizontal rule"); add `Usage: python3 scripts/pptx_qa_check.py <deck.pptx> [--checks ...] [--json] [--strict]` and `Ported from jesamkim/oh-my-skills myslide qa_validate.py (MIT).`
2. Add the upstream header used by every script, right after the imports:
   ```python
   _SCRIPTS_DIR = Path(__file__).resolve().parent
   if str(_SCRIPTS_DIR) not in sys.path:
       sys.path.insert(0, str(_SCRIPTS_DIR))
   from console_encoding import configure_utf8_stdio  # noqa: E402
   configure_utf8_stdio()
   ```
3. Replace `validate`:
   ```python
   CHECKS = {
       "bounds": check_bounds,
       "connectors": check_connectors,
       "font_size": check_font_sizes,
       "zero_size": check_zero_size,
       "image_aspect": check_image_aspect,
       "copy": check_ai_copy,
   }


   def validate(pptx_path, strict=False, checks=None):
       """Run the selected checks (all by default). Returns (issues, presentation)."""
       prs = Presentation(pptx_path)
       selected = list(CHECKS) if not checks else list(checks)
       unknown = [c for c in selected if c not in CHECKS]
       if unknown:
           raise ValueError(f"unknown checks: {unknown}; valid: {sorted(CHECKS)}")
       all_issues = []
       for name in selected:
           all_issues.extend(CHECKS[name](prs))
       if not strict:
           all_issues = [i for i in all_issues if i.level != "info"]
       return all_issues, prs
   ```
4. In `main()` add
   ```python
   parser.add_argument("--checks", help="Comma-separated subset: " + ",".join(CHECKS))
   ```
   and pass `checks=args.checks.split(",") if args.checks else None` into `validate`. A `ValueError` from unknown checks prints to stderr and exits 2 (it is already inside the `except Exception` block).
5. Leave every detector unchanged. The 15pt body floor and 8pt caption floor stay as constants `MIN_BODY_SZ`, `MIN_CAPTION_SZ`.

- [ ] **Step 4: Run the tests**

Run: `python3 -m unittest plugins/aws-ppt-master/skills/aws-ppt-master/scripts/tests/test_pptx_qa_check.py plugins/aws-ppt-master/skills/aws-ppt-master/scripts/tests/test_pptx_qa_copy.py -v 2>&1 | tail -5`
Expected: 20 tests OK (18 ported + 1 filter + 1 copy aggregate).

- [ ] **Step 5: Port copy-voice.md**

```bash
cp /tmp/oh-my-skills/my-skills/myslide/references/copy-voice.md plugins/aws-ppt-master/skills/aws-ppt-master/references/copy-voice.md
```
Edit: delete sentences that mention PptxGenJS, `theme.js`, `qa_validate.py`, or myslide-specific slide names; replace `qa_validate.py` with `pptx_qa_check.py --checks copy`. Add a two-line header: `> Load when authoring or rewriting on-slide text in Korean or English. Machine check: scripts/pptx_qa_check.py --checks copy. Ported from myslide (jesamkim, MIT).` Keep the rule list, the 번역투 table, and the rewrite brief intact.

- [ ] **Step 6: Wire into the workflows**

Add this block (adapt heading level to the neighbours) right after the export success-criterion paragraph in `workflows/generate-pptx.md` (Step 7), in `workflows/profiles/quick-generate.md` (export section), and in `workflows/edit-native-pptx.md` (export section):

```markdown
**Layout and copy gate**: run `python3 "${SKILL_DIR}/scripts/pptx_qa_check.py" exports/<file>.pptx`
next to `pptx_delivery_check.py`. Any `critical` (shape off-slide, body text under 15pt, image aspect
mismatch over 2%, em/en dash or meta label in slide copy) blocks delivery: repair the owning SVG or text,
re-export, rerun. `warning` items are listed in the completion report.
```

In `references/executor-base.md` trigger table add a row: `| On-slide text is written or rewritten (any language) | [copy-voice.md](./copy-voice.md) |`.
In `scripts/README.md` add a row for `pptx_qa_check.py` in the QA/validation section.

- [ ] **Step 7: Smoke the CLI on a real deck**

```bash
cd /home/ubuntu/workspace/hi-aws-skills/plugins/aws-ppt-master/skills/aws-ppt-master
python3 - <<'EOF'
from pptx import Presentation
from pptx.util import Inches, Pt
prs = Presentation(); prs.slide_width, prs.slide_height = Inches(13.33), Inches(7.5)
s = prs.slides.add_slide(prs.slide_layouts[6])
tb = s.shapes.add_textbox(Inches(12), Inches(1), Inches(4), Inches(1))   # off-slide
r = tb.text_frame.paragraphs[0].add_run(); r.text = "왜 중요한가 — 핵심"; r.font.size = Pt(12)
prs.save("/tmp/qa-smoke.pptx")
EOF
python3 scripts/pptx_qa_check.py /tmp/qa-smoke.pptx; echo "exit=$?"
python3 scripts/pptx_qa_check.py /tmp/qa-smoke.pptx --checks copy --json | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['summary'])"
```
Expected: first run exit=1 with bounds critical, font_size critical, ai_copy critical (dash + meta label); second run summary shows only copy issues.

---

### Task 7: AWS icon library

**Files:**
- Create: `$S/templates/icons/aws/*.svg` (304 files from `/tmp/oh-my-skills/my-skills/myslide/icons/`)
- Modify: `$S/scripts/icon_sync.py:38-44` (`_SYNC_LIBRARIES`), help text at line ~124
- Modify: `$S/templates/icons/README.md` (table row + a paragraph), `$S/templates/icons/THIRD_PARTY_NOTICES.md`, `$S/references/executor-base.md` §4 icon paragraph
- Test: `$S/scripts/tests/test_aws_icons.py`

**Interfaces:**
- Consumes: `icon_sync.sync_icons(project_path, icon_names, global_dir) -> (copied, missing)`; `svg_finalize/embed_icons.py` resolves `data-icon="aws/<name>"` from `<project>/icons/aws/`.
- Produces: library id `aws`, allowed alongside one stylistic library (same rule as `simple-icons`).

- [ ] **Step 1: Write the failing test**

Create `$S/scripts/tests/test_aws_icons.py`:

```python
#!/usr/bin/env python3
"""The bundled AWS icon library is complete, well-formed, and syncable."""

import re
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import icon_sync  # noqa: E402

AWS_DIR = SCRIPTS_DIR.parent / "templates" / "icons" / "aws"


class AwsIconLibraryTests(unittest.TestCase):
    def test_count_and_names(self) -> None:
        files = sorted(AWS_DIR.glob("*.svg"))
        self.assertEqual(len(files), 304)
        for f in files:
            self.assertRegex(f.stem, r"^[a-z0-9]+(-[a-z0-9]+)*$", f.name)
        for required in ("lambda", "s3", "ec2", "eks", "sagemaker", "bedrock",
                         "agentcore-runtime-blue-light", "agentcore-gateway-purple-dark"):
            self.assertTrue((AWS_DIR / f"{required}.svg").is_file(), required)

    def test_every_file_is_svg_with_viewbox(self) -> None:
        for f in AWS_DIR.glob("*.svg"):
            text = f.read_text(encoding="utf-8")
            self.assertIn("<svg", text, f.name)
            self.assertRegex(text, r'viewBox="[^"]+"', f.name)

    def test_sync_allows_aws_with_one_stylistic_library(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            copied, missing = icon_sync.sync_icons(Path(d), ["aws/lambda", "tabler-outline/home"])
        self.assertEqual(missing, [])
        self.assertEqual(copied, ["aws/lambda", "tabler-outline/home"])

    def test_readme_lists_aws(self) -> None:
        readme = (SCRIPTS_DIR.parent / "templates" / "icons" / "README.md").read_text(encoding="utf-8")
        self.assertIn("| `aws` |", readme)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run to verify it fails**

Run: `python3 -m unittest plugins/aws-ppt-master/skills/aws-ppt-master/scripts/tests/test_aws_icons.py -v 2>&1 | tail -3`
Expected: FAIL (`AWS_DIR` missing → count 0; sync raises `unsupported bundled icon library: 'aws'`).

- [ ] **Step 3: Copy the icons**

```bash
mkdir -p /home/ubuntu/workspace/hi-aws-skills/plugins/aws-ppt-master/skills/aws-ppt-master/templates/icons/aws
cp /tmp/oh-my-skills/my-skills/myslide/icons/*.svg /home/ubuntu/workspace/hi-aws-skills/plugins/aws-ppt-master/skills/aws-ppt-master/templates/icons/aws/
ls /home/ubuntu/workspace/hi-aws-skills/plugins/aws-ppt-master/skills/aws-ppt-master/templates/icons/aws | wc -l
```
Expected: 304. If a stem fails the lowercase-hyphen regex in Step 1, rename it (`git mv`-free `mv`) and note the rename in `UPSTREAM.md`.

- [ ] **Step 4: Allow `aws` in icon_sync.py**

Line 44: `_SYNC_LIBRARIES = _STYLISTIC_LIBRARIES | {"simple-icons", "aws"}`. Update the module docstring (line 10) and the error text near line 124 to "simple-icons and aws may coexist for real brand / AWS service marks."

- [ ] **Step 5: Document**

`templates/icons/README.md`:
- Count line: "12,027" → "12,331 SVG icons across six libraries".
- Table row: `| \`aws\` | **AWS service marks** — official Architecture Icon Deck style (coloured category square + white glyph) for 248 services, plus 56 Amazon Bedrock AgentCore component variants (`agentcore-<part>-<blue|cyan|purple|teal>-<light|dark>`), colours fixed | 304 | `0 0 80 80` (AgentCore variants vary) | `aws/` |`
- Paragraph after the table: "`aws` is a brand-mark library like `simple-icons`: it accompanies one stylistic library and never replaces it. Do not recolour AWS marks via `fill`; on dark backgrounds use the `-dark` AgentCore variants. For the full official set (800+ icons) copy files from the sibling plugin `aws-diagram-design` (`assets/aws-icons/`) into `<project>/icons/custom/`."
- Usage example: `<use data-icon="aws/lambda" x="100" y="200" width="48" height="48"/>` (no `fill`).

`templates/icons/THIRD_PARTY_NOTICES.md`: add a section "aws — AWS Architecture Icons. Source: AWS Architecture Icons (https://aws.amazon.com/architecture/icons/), redistributed as prepared in jesamkim/oh-my-skills myslide (MIT). AWS trademarks and icons are subject to the AWS Trademark Guidelines; use them only to represent the named AWS service."

`references/executor-base.md` §4 (icon selection): add one paragraph: "AWS services are always drawn with `aws/<service>` marks (`aws/lambda`, `aws/s3`, `aws/bedrock`), never with a generic glyph or a recoloured silhouette. Bedrock AgentCore components use `aws/agentcore-<part>-<colour>-<light|dark>`; pick `-dark` on dark page fields."

- [ ] **Step 6: Run the test and an embed check**

Run: `python3 -m unittest plugins/aws-ppt-master/skills/aws-ppt-master/scripts/tests/test_aws_icons.py -v`
Expected: 4 tests OK.

Embed smoke:
```bash
cd /tmp && rm -rf icon-smoke && mkdir -p icon-smoke/svg_output && cd icon-smoke
S=/home/ubuntu/workspace/hi-aws-skills/plugins/aws-ppt-master/skills/aws-ppt-master
python3 $S/scripts/icon_sync.py . aws/lambda aws/agentcore-runtime-blue-dark
cat > svg_output/p1.svg <<'EOF'
<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720">
  <use data-icon="aws/lambda" x="100" y="100" width="64" height="64"/>
  <use data-icon="aws/agentcore-runtime-blue-dark" x="200" y="100" width="64" height="64"/>
</svg>
EOF
python3 $S/scripts/svg_finalize/embed_icons.py svg_output/p1.svg && grep -c '<path' svg_output/p1.svg
```
Expected: the script exits 0 and the file now contains `<path` elements (embedded icon geometry). If `embed_icons.py` takes a project path rather than files, read its `--help` and adapt. Failure here means the AgentCore viewBox shape is unsupported; report it rather than patching the embedder.

---

### Task 8: Identity, paths, docs, marketplace, validation

**Files:**
- Modify: `$S/SKILL.md` (name, description, §Repository Compatibility), every text file containing `skills/ppt-master/`, `$S/scripts/config.py` (only if it hardcodes `ppt-master` paths that must change — keep `~/.ppt-master/.env`)
- Create: `$P/README.md`, `$P/THIRD_PARTY_LICENSES.md`
- Modify: `.claude-plugin/marketplace.json`, root `README.md`
- Test: `$S/scripts/tests/test_plugin_identity.py`

**Interfaces:**
- Produces: installable plugin `aws-ppt-master@hi-aws-skills`.

- [ ] **Step 1: Write the failing test**

Create `$S/scripts/tests/test_plugin_identity.py`:

```python
#!/usr/bin/env python3
"""Plugin identity: names, paths and manifests agree."""

import json
import re
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[2]
PLUGIN_DIR = SKILL_DIR.parents[1]
REPO_DIR = PLUGIN_DIR.parents[1]


class PluginIdentityTests(unittest.TestCase):
    def test_skill_frontmatter(self) -> None:
        head = SKILL_DIR.joinpath("SKILL.md").read_text(encoding="utf-8").split("\n---\n", 1)[0]
        self.assertIn("name: aws-ppt-master", head)
        self.assertIn('version: "1.0.0"', head)
        self.assertNotIn("sponsors", head)
        self.assertNotIn("video", head)

    def test_no_stale_skill_path(self) -> None:
        hits = []
        for path in PLUGIN_DIR.rglob("*"):
            if path.is_file() and path.suffix in {".md", ".py", ".json", ".txt", ".html", ".js", ".yaml", ".yml"}:
                if "skills/ppt-master/" in path.read_text(encoding="utf-8", errors="ignore"):
                    hits.append(str(path.relative_to(PLUGIN_DIR)))
        self.assertEqual(hits, [])

    def test_manifests(self) -> None:
        plugin = json.loads((PLUGIN_DIR / ".claude-plugin" / "plugin.json").read_text())
        self.assertEqual(plugin["name"], "aws-ppt-master")
        self.assertEqual(plugin["version"], "1.0.0")
        market = json.loads((REPO_DIR / ".claude-plugin" / "marketplace.json").read_text())
        names = [p["name"] for p in market["plugins"]]
        self.assertIn("aws-ppt-master", names)
        entry = next(p for p in market["plugins"] if p["name"] == "aws-ppt-master")
        self.assertEqual(entry["source"], "./plugins/aws-ppt-master")

    def test_third_party_and_readme_exist(self) -> None:
        tp = (PLUGIN_DIR / "THIRD_PARTY_LICENSES.md").read_text(encoding="utf-8")
        for needle in ("Hugo He", "Jesam Kim", "AWS Architecture Icons"):
            self.assertIn(needle, tp)
        self.assertTrue((PLUGIN_DIR / "README.md").is_file())
        self.assertIn("aws-ppt-master", (REPO_DIR / "README.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run to verify it fails**

Run: `python3 -m unittest plugins/aws-ppt-master/skills/aws-ppt-master/scripts/tests/test_plugin_identity.py 2>&1 | tail -3`
Expected: FAIL on frontmatter name and stale paths.

- [ ] **Step 3: Rewrite SKILL.md identity**

Frontmatter:
```yaml
---
name: aws-ppt-master
description: >
  AI-driven presentation workflow for generating natively editable PPTX decks
  and slides, reconstructing page visuals, creating reusable Brand/Style/Layout/Deck
  workspaces, filling native PPTX templates, and enhancing finished PPTX files,
  with AI images generated on Amazon Bedrock (Stability AI) and a layout plus
  Korean copy-voice QA gate before delivery. Use when the user asks to create,
  generate, reconstruct, regenerate, beautify, redesign, template, fill, or
  enhance a presentation, PPT, PPTX, slide deck, or courseware — including adding
  speaker notes or animation — or says 발표자료, 슬라이드 만들어, PPT 만들어,
  AWS 기술 발표, or mentions aws-ppt-master or ppt-master.
license: MIT
metadata:
  version: "1.0.0"
  base: "ppt-master 6.3.2 (https://github.com/hugohe3/ppt-master, MIT, Hugo He)"
  source: "https://github.com/hi-space/hi-aws-skills"
---
```
Title line `# PPT Master Skill` → `# AWS PPT Master Skill`, first paragraph unchanged except "PPT Master" → "AWS PPT Master".
Add under `## Repository Compatibility` a bullet: "AI image generation uses Amazon Bedrock only (`scripts/image_gen.py`, backend `bedrock`). Configure AWS credentials and `AWS_REGION` before Path A; see `scripts/docs/image.md`."

- [ ] **Step 4: Rewrite the path prefix everywhere**

```bash
cd /home/ubuntu/workspace/hi-aws-skills/plugins/aws-ppt-master
grep -rl 'skills/ppt-master/' --include='*.md' --include='*.py' --include='*.json' --include='*.txt' --include='*.html' --include='*.js' --include='*.yaml' --include='*.yml' . \
  | xargs sed -i 's#skills/ppt-master/#skills/aws-ppt-master/#g'
grep -rn 'skills/ppt-master/' . | wc -l
```
Expected: `0`. Then run the whole test suite; upstream tests that assert on help text containing the path must still pass because they read the same constants.

Check `scripts/config.py`: `~/.ppt-master/.env` stays as a documented user-level location (mention in README). Any `resource_paths.py` constant naming `ppt-master` as a directory segment must be inspected: `grep -n "ppt-master" scripts/resource_paths.py scripts/config.py`.

- [ ] **Step 5: Plugin README and THIRD_PARTY_LICENSES**

`$P/README.md` (Korean, then a short English section):

```markdown
# aws-ppt-master

[ppt-master](https://github.com/hugohe3/ppt-master) 6.3.2 를 포크해 AWS 기술 발표 자료 제작에 맞춘 Claude Code 플러그인입니다.
Markdown·문서·URL·주제에서 **네이티브로 편집 가능한 PPTX**(실제 DrawingML 도형·텍스트·표·차트·애니메이션)를 만듭니다.

원본과 다른 점

| 영역 | aws-ppt-master |
|---|---|
| AI 이미지 생성 | Amazon Bedrock 의 Stability AI Stable Image 만 사용 (API 키 없음, boto3 자격 증명 체인) |
| 나레이션·TTS·영상 | 제외 |
| 스톡 이미지 검색·워터마크 제거 | 제외 |
| QA | `scripts/pptx_qa_check.py`: 슬라이드 경계, 본문 15pt 하한, 이미지 비율, 커넥터, 한국어·영어 카피 보이스(em dash·메타 라벨·번역투) |
| 아이콘 | `templates/icons/aws/` AWS 서비스 마크 304개 (AgentCore 변형 포함) |
| 무결성 게이트·스폰서 자료 | 제거 (원저작자 고지는 LICENSE, THIRD_PARTY_LICENSES.md) |

## 설치

```
/plugin marketplace add hi-space/hi-aws-skills
/plugin install aws-ppt-master@hi-aws-skills
```

설치된 플러그인 디렉터리에서 Python 의존성을 설치합니다.

```
pip install -r requirements.txt
```

## Bedrock 설정

1. Bedrock 콘솔(기본 리전 `us-west-2`) → Model access 에서 Stability AI 모델(Stable Image Core, Ultra, SD3.5 Large) 접근을 활성화합니다.
2. 자격 증명은 boto3 기본 체인을 따릅니다. `AWS_PROFILE` 또는 액세스 키, SSO, 인스턴스 롤 중 하나면 됩니다.
3. 선택 설정은 환경변수 또는 `.env`(예시: `.env.example`) 로 줍니다.

| 키 | 기본값 | 설명 |
|---|---|---|
| `AWS_REGION` | `us-west-2` | 모델을 서비스하는 리전 |
| `BEDROCK_IMAGE_MODEL` | `stability.stable-image-core-v1:1` | 별칭 `core`, `ultra`, `sd3.5-large` |
| `BEDROCK_NEGATIVE_PROMPT` | 없음 | 제외할 요소 |
| `BEDROCK_SEED` | 무작위 | 재현용 시드 |

동작 확인:

```
python3 skills/aws-ppt-master/scripts/image_gen.py "flat illustration of a robot arm" --aspect-ratio 16:9
```

## 사용

트리거: "발표자료 만들어줘", "이 문서로 PPT 만들어", "AWS 기술 발표 10장", 또는 `/aws-ppt-master`.
워크플로·라우팅·레퍼런스 문서는 원본 구조를 그대로 유지합니다. 시작점은 `skills/aws-ppt-master/SKILL.md` 입니다.

## English

AWS-flavoured fork of ppt-master 6.3.2. Only external model call: Amazon Bedrock (Stability AI Stable Image). Removed narration/TTS/video, stock image search, watermark removal, and the upstream integrity gate. Added `pptx_qa_check.py` (layout + Korean/English copy-voice QA) and a 304-icon AWS service icon library. Install with the two `/plugin` commands above, then `pip install -r requirements.txt` and enable Stability model access in Bedrock.

## License

MIT. Upstream and third-party notices: [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md), [UPSTREAM.md](UPSTREAM.md).
```

`$P/THIRD_PARTY_LICENSES.md`:

```markdown
# Third-party licenses

## ppt-master
- https://github.com/hugohe3/ppt-master — MIT License, Copyright (c) 2025-2026 Hugo He.
- This plugin is a modified copy of `skills/ppt-master` at commit 451c68148e326383651f6319ef6f91dd2932069d. The full license text is kept at `skills/aws-ppt-master/LICENSE`. Changes are listed in `UPSTREAM.md`.

## myslide (jesamkim/oh-my-skills)
- https://github.com/jesamkim/oh-my-skills/tree/main/my-skills/myslide — MIT License, Copyright (c) 2026 Jesam Kim.
- Ported: `scripts/pptx_qa_check.py` (from `qa_validate.py`), its tests, `references/copy-voice.md`, and the 304 SVG files under `templates/icons/aws/`.

## AWS Architecture Icons
- `templates/icons/aws/` contains AWS service and Amazon Bedrock AgentCore icons derived from the AWS Architecture Icons (https://aws.amazon.com/architecture/icons/). AWS trademarks are the property of Amazon.com, Inc. or its affiliates and are used here only to represent the named services, subject to the AWS Trademark Guidelines.

## Bundled icon and sound libraries
- See `skills/aws-ppt-master/templates/icons/THIRD_PARTY_NOTICES.md` and `skills/aws-ppt-master/templates/sounds/THIRD_PARTY_NOTICES.md` (unchanged from upstream).
```

- [ ] **Step 6: Marketplace and root README**

`.claude-plugin/marketplace.json`: append to `plugins`:
```json
{
  "name": "aws-ppt-master",
  "source": "./plugins/aws-ppt-master",
  "description": "Natively editable PPTX decks from documents or a topic (ppt-master fork); AI images on Amazon Bedrock only; PPTX layout + Korean copy-voice QA gate; 304 AWS service icons."
}
```
and update `metadata.description` to mention both plugins.

Root `README.md` skill table: add
`| [aws-ppt-master](plugins/aws-ppt-master/) | ppt-master 포크. 문서·주제에서 네이티브 편집 가능한 PPTX 생성. AI 이미지는 Amazon Bedrock(Stability) 만 사용, PPTX 레이아웃·한국어 카피 보이스 QA, AWS 아이콘 304개 | [README](plugins/aws-ppt-master/README.md) · [SKILL.md](plugins/aws-ppt-master/skills/aws-ppt-master/SKILL.md) |`
and in the install section add `/plugin install aws-ppt-master@hi-aws-skills`.

- [ ] **Step 7: Validate and run everything**

```bash
cd /home/ubuntu/workspace/hi-aws-skills
claude plugin validate plugins/aws-ppt-master
python3 -m unittest discover -s plugins/aws-ppt-master/skills/aws-ppt-master/scripts/tests -t plugins/aws-ppt-master/skills/aws-ppt-master/scripts/tests -p 'test_*.py' 2>&1 | tail -5
find plugins/aws-ppt-master -name '__pycache__' -prune -exec rm -rf {} +
git status --short | head
```
Expected: validate OK; suite OK; `git status` shows only `plugins/aws-ppt-master/`, `.claude-plugin/marketplace.json`, `README.md`, and the two docs files as changes. Do not commit.

---

### Task 9: Fresh-agent skill test

**Files:**
- No source changes unless the test reveals a defect; fixes go to the owning file and are re-verified.

- [ ] **Step 1: Dispatch a fresh subagent**

Prompt (paste verbatim, replace nothing):

```
You are testing a Claude Code skill. Skill directory: /home/ubuntu/workspace/hi-aws-skills/plugins/aws-ppt-master/skills/aws-ppt-master (treat this as SKILL_DIR). Read SKILL.md and follow it exactly.
Task: create a 6-slide Korean presentation titled "Amazon Bedrock AgentCore 소개" for an audience of solutions architects: what AgentCore is, Runtime, Gateway, Memory, Identity/Observability, and a closing summary. Use the Quick profile if the routing allows it; otherwise the Default route. Answer any blocking question yourself with a sensible default and state the default you chose. Produce the exported .pptx under /tmp/agentcore-deck/. Do not commit anything. At the end report: (1) the route you took, (2) which scripts you ran, in order, (3) whether image generation was attempted and which backend name was printed, (4) which icon library ids you used, (5) the pptx_qa_check.py and pptx_delivery_check.py results, (6) anything in the docs that was contradictory, missing, or referred to a file that does not exist.
```

- [ ] **Step 2: Score the report**

Pass criteria, all required:
- Route is Generate (Quick or Default); no attempt to load narration/video/audio stages.
- If image generation ran, output shows `Using backend: bedrock`; no request for an API key.
- Icons drawn for AWS services use `aws/...` ids.
- `pptx_qa_check.py` was run and its criticals were fixed (or report explains why none).
- Item (6) lists no dangling file references.

- [ ] **Step 3: Fix what failed**

For each failure: find the owning doc or script, fix it, add a needle to `test_removed_features.py` or a case to the relevant test if it was a removal leak, rerun the suite, and rerun Step 1 with a fresh subagent. Stop when a run passes all criteria.

- [ ] **Step 4: Report to the user**

Summarise: file counts removed/added, test totals, the live Bedrock image result, the fresh-agent outcome, and that nothing is committed.

---

## Addendum (2026-09-12): Tasks 10–14 — research → storyline → build → review process, font fallback, iterate

Spec authority for these tasks: `docs/superpowers/specs/2026-09-12-aws-ppt-master-design.md` §11 (부록 A). Same Global Constraints as above (no commits; `$S=plugins/aws-ppt-master/skills/aws-ppt-master`; unittest discover; pre-existing failures list; every removal/edit grep-verified). Hook points found in the tree (line numbers approximate):

- Research stage: `workflows/stages/topic-research.md` ("When to Run" table L11-16, sufficiency test L18, artifacts L62-81, worker dispatch L42-46); referenced from `workflows/generate-pptx.md` Step 1 (L41, L45) and Step 2 (L66), `workflows/profiles/quick-generate.md` §2 (L51, L59), `workflows/routing.md` L44.
- Strategist / §IX: `references/strategist.md` (Stage 2 scope L30, gates L21/L67/L257/L259), `templates/design_spec_reference.md` §IX L163-175 (+ `Fact IDs` L189), `references/plan-core.md` L60 (fact_id rule) and §4 L70-83; ⛔ gates in `workflows/generate-pptx.md` L127 and L158.
- Post-build: `workflows/generate-pptx.md` Step 7 "Layout and copy gate" L363-367; `workflows/profiles/quick-generate.md` §4 L222-226; `workflows/edit-native-pptx.md` §7 L153-155; opt-in `workflows/stages/visual-review.md`.
- Fonts: `references/plan-core.md` §6.2 L161-184; `references/shared-standards-core.md` §4.1 L168; `templates/brands/aws/templates/design_spec.md` §III L34-41 (currently Arial / Microsoft YaHei); `references/executor-base.md` §5 L354-361.
- Artifact matrix: `references/artifact-ownership.md` §1 L11-57. Project dirs from `scripts/project_management/cli.py` L333-347 (`analysis/`, `validation/`, `sources/` exist; no `research/`).
- Subagent conventions: `topic-research.md` L42-46 (one worker, paths not bodies, 250-word receipt); `workflows/stages/visual-review.md` L40-49; `references/copy-voice.md` L284-290.

### Task 10: Fact-verification gate (topic-research becomes mandatory for technical decks)

**Files:**
- Modify: `$S/workflows/stages/topic-research.md` (When to Run table, tools paragraph, artifacts section)
- Modify: `$S/workflows/generate-pptx.md` Step 1–2, `$S/workflows/profiles/quick-generate.md` §2, `$S/workflows/routing.md` L44
- Modify: `$S/references/plan-core.md` L60 (fact_id rule wording), `$S/SKILL.md` (Global Execution Discipline: one new numbered item)
- Test: `$S/scripts/tests/test_process_gates.py` (new; grows in Tasks 11–12)

**Interfaces:**
- Produces: the rule "every technical claim on a slide traces to a fact id in `sources/<slug>.facts.json`; unverified claims are `classification: unverified` and never appear as fact on a slide"; tool order deep-research/web-research skill → WebSearch/WebFetch → aws-docs MCP / docs.aws.amazon.com; `retrieved_at` on every fact.

- [ ] **Step 1: Write the failing test**

Create `$S/scripts/tests/test_process_gates.py`:

```python
#!/usr/bin/env python3
"""The research → storyline → build → review process is wired into the workflow docs."""

import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[2]


def _read(rel: str) -> str:
    return (SKILL_DIR / rel).read_text(encoding="utf-8")


class ResearchGateTests(unittest.TestCase):
    def test_topic_research_runs_for_technical_claims(self) -> None:
        text = _read("workflows/stages/topic-research.md")
        for needle in ("classification", "unverified", "retrieved_at", "deep-research", "aws-docs", "docs.aws.amazon.com"):
            self.assertIn(needle, text, needle)
        self.assertNotIn("Sufficient or closed corpus → skip", text)

    def test_routes_reference_verification_pass(self) -> None:
        for rel in ("workflows/generate-pptx.md", "workflows/profiles/quick-generate.md", "workflows/routing.md"):
            self.assertIn("verification pass", _read(rel), rel)

    def test_skill_md_names_the_process(self) -> None:
        text = _read("SKILL.md")
        for needle in ("fact", "storyline", "deck review"):
            self.assertIn(needle, text.lower(), needle)


if __name__ == "__main__":
    unittest.main()
```

(`test_skill_md_names_the_process` will only pass after Tasks 11–12 add the other two words; that is expected — Task 10 makes the first two tests pass and leaves the third RED for Task 12 to close. Say so in the report.)

- [ ] **Step 2: Run it (RED)**

`python3 -m unittest $S/scripts/tests/test_process_gates.py -v` → all three FAIL.

- [ ] **Step 3: Edit topic-research.md**

1. "When to Run" table: replace the three rows with

| Input | Action |
|---|---|
| Topic only | Full research: build the fact set before any storyline or design work |
| Documents / URLs provided, deck makes technical claims (service behaviour, limits, numbers, dates, pricing) | **Verification pass**: import the sources, then verify every technical claim the storyline will need that the sources do not themselves substantiate |
| User states the corpus is closed ("출처는 내 문서만" / "only my documents") | Skip; record the statement in `design_spec.md §I` and treat every claim as user-attested |

Delete the sufficiency-test paragraph that let research be skipped when sources "look sufficient"; replace it with: "Sufficiency is not a judgement about volume. A deck that names an AWS service limit, a price, a release date, or a behaviour that the sources do not show needs the verification pass, however thick the source folder is. Slides with wrong numbers cost more to retract than one research pass costs to run."

2. Tools paragraph (L52 area): "Use the first available: a `deep-research` or `web-research` skill in the host, then the host's WebSearch/WebFetch tools, then the aws-docs MCP (`search_documentation`, `read_documentation`) or a direct fetch of docs.aws.amazon.com pages. For AWS services, an official docs.aws.amazon.com or aws.amazon.com page is the primary source; blogs and third-party posts are supporting evidence only. Record `retrieved_at` (ISO date) on every fact."

3. Artifacts section: add to the facts.json contract "`classification` values: `official` (AWS documentation), `vendor` (AWS blog / announcement), `secondary` (third party), `unverified` (no source found). An `unverified` fact never becomes an assertion on a slide: it is dropped, or shown as a question with `[확인 필요]`, and listed in the research brief's open questions."

- [ ] **Step 4: Wire the routes**

- `workflows/generate-pptx.md` Step 1 table: the "Topic only" row stays; add a row "Documents + technical claims → run the topic-research **verification pass** (stage) before Step 3". Step 2: after the research pair import sentence add "The verification pass may add facts to the same pair; re-import after it."
- `workflows/profiles/quick-generate.md` §2: same two rows (Quick still runs the verification pass; it is the design that Quick skips, never the facts).
- `workflows/routing.md` L44 rule: append "; documents with technical claims → verification pass".
- `references/plan-core.md` L60: extend "cite fact_id on every §IX page that uses an external claim" with "— a page that states a number, limit, date, price or service behaviour without a fact id is a Plan defect, not an Executor choice".
- `SKILL.md` Global Execution Discipline: add item 8 "**Facts before slides** — technical claims come from `sources/<slug>.facts.json`; the storyline (Task 11) and every §IX page cite fact ids; unverified claims are questions, never assertions." (Reword item numbering if the list is renumbered elsewhere.)

- [ ] **Step 5: Run the tests (GREEN for the first two)**

`python3 -m unittest $S/scripts/tests/test_process_gates.py -v` → `test_topic_research_runs_for_technical_claims` OK, `test_routes_reference_verification_pass` OK, `test_skill_md_names_the_process` still FAIL (expected until Task 12). Full suite: no new failures besides that one.

### Task 11: Storyline gate

**Files:**
- Create: `$S/references/storyline.md`
- Modify: `$S/workflows/generate-pptx.md` (new Step 3a between source intake and Confirm UI; ⛔ BLOCKING), `$S/workflows/profiles/quick-generate.md` (§2 storyline block, 🚧), `$S/workflows/edit-native-pptx.md` (§4 plan: storyline required when content changes), `$S/references/strategist.md` (Stage 2 input: storyline; §IX pages cite storyline ids), `$S/templates/design_spec_reference.md` §IX (optional `Storyline` field), `$S/references/artifact-ownership.md` §1 (row for `analysis/storyline.md`), `$S/workflows/index.md` (reference list)
- Test: extend `$S/scripts/tests/test_process_gates.py`

**Interfaces:**
- Produces: artifact `analysis/storyline.md` with the template below; storyline slide ids `S01…`; §IX pages carry `Storyline: S03` and `Fact IDs: F002, F007`.

- [ ] **Step 1: Extend the failing test**

```python
class StorylineGateTests(unittest.TestCase):
    def test_reference_exists_with_template(self) -> None:
        text = _read("references/storyline.md")
        for needle in ("analysis/storyline.md", "Audience and decision", "Core thesis", "| S01 |", "Fact IDs", "Must-show technical elements", "Excluded"):
            self.assertIn(needle, text, needle)

    def test_default_route_blocks_on_storyline(self) -> None:
        text = _read("workflows/generate-pptx.md")
        idx_story = text.find("analysis/storyline.md")
        idx_confirm = text.find("Confirm UI")
        self.assertGreater(idx_story, 0)
        self.assertLess(idx_story, idx_confirm, "storyline must come before the Confirm UI stage")
        self.assertIn("⛔ BLOCKING", text[idx_story - 400: idx_story + 1200])

    def test_quick_and_edit_native_mention_storyline(self) -> None:
        for rel in ("workflows/profiles/quick-generate.md", "workflows/edit-native-pptx.md", "references/strategist.md", "references/artifact-ownership.md"):
            self.assertIn("storyline", _read(rel).lower(), rel)
```

- [ ] **Step 2: RED** — run the file; the three new tests fail.

- [ ] **Step 3: Write references/storyline.md**

```markdown
# Storyline — `analysis/storyline.md`

Write this file after the research pair exists and before the Confirm UI or any design work. It is the
argument of the deck in prose form; the Strategist turns it into pages, the Executor draws it, the deck
review checks the export against it. A deck built without it tends to be a list of facts in the order they
were found. A deck built from it is a case the audience can follow and act on.

## Template (copy verbatim, fill every field)

```markdown
# Storyline: <deck title>

## Audience and decision
Who sits in the room (role, level), what they know already, and the one decision or action the deck should
make easier for them.

## Core thesis
One sentence. If the audience remembers nothing else, they remember this.

## Narrative arc
3–5 beats, one line each: situation → tension → resolution → proof → ask.

## Slides
| Id | Claim (one sentence the slide asserts) | Fact IDs | Must-show technical elements | Limits / counter-points |
|---|---|---|---|---|
| S01 | … | F001 | … | … |

## Excluded
Topics that were considered and left out, with the reason (audience, time, unverified).
```

## Rules
- One claim per slide, phrased as an assertion the evidence supports (assertion–evidence), not a topic label.
- Every claim that states a number, limit, date, price or behaviour lists at least one fact id from
  `sources/<slug>.facts.json`; an `unverified` fact can only appear in *Limits / counter-points* as a question.
- "Must-show technical elements" names the diagram, table, code, or parameter the slide cannot do without;
  the deck review fails a slide that drops one.
- The title of a slide never repeats in its body; the body carries the evidence, the title carries the claim.
- Korean decks keep AWS service names in English; explain each acronym once, at first use.
- Six to twelve slides for a 20–30 minute technical talk; if the table runs longer, cut beats before cutting evidence.

## Gate
Default route: ⛔ BLOCKING — show the storyline (table included) and wait for the user's confirmation before
the Confirm UI. Quick profile: write the file, summarise thesis + slide claims in chat, continue unless the user
objects (🚧). Edit Native: required whenever page content changes; skip for pure design/notes edits.
```

- [ ] **Step 4: Wire the workflows**

- `workflows/generate-pptx.md`: insert **Step 3a — Storyline** after source import / research and before the Confirm UI step: "Read `references/storyline.md`; write `analysis/storyline.md` from the research pair and the sources. ⛔ **BLOCKING**: present it and wait for confirmation. The Strategist may only add, split, or merge pages with a note in §IX; it may not introduce a claim the storyline lacks." Update the Phase Frame table in SKILL.md if it enumerates Plan steps (Plan = Steps 1–5 stays; 3a is inside).
- `workflows/profiles/quick-generate.md` §2: add the storyline block (🚧, file + chat summary).
- `workflows/edit-native-pptx.md` §4 plan table: add row "Content changes → `analysis/storyline.md` (references/storyline.md) before editing pages".
- `references/strategist.md` Stage 2 inputs: "the confirmed `analysis/storyline.md` is the narrative authority; each §IX page names its storyline id (`Storyline: S03`) and copies its fact ids". `templates/design_spec_reference.md` §IX: add optional field `Storyline` next to `Fact IDs` (no schema change: `project_manager.py validate` must still pass on the scaffold; run it once on a fresh `project_manager.py init` project to confirm).
- `references/artifact-ownership.md` §1: add a row for `analysis/storyline.md` (owner: Plan; readers: Strategist, deck review; rebuilt when: sources or thesis change).
- `workflows/index.md`: list `references/storyline.md`.

- [ ] **Step 5: GREEN** — run `test_process_gates.py` (Storyline tests OK) and the full suite.

### Task 12: Deck review gate (fresh-context reviewer) + deck_text_dump.py

**Files:**
- Create: `$S/scripts/deck_text_dump.py`, `$S/scripts/tests/test_deck_text_dump.py`
- Create: `$S/workflows/stages/deck-review.md`, `$S/references/deck-review.md`
- Modify: `$S/workflows/generate-pptx.md` Step 7 (after the Layout and copy gate), `$S/workflows/profiles/quick-generate.md` §4, `$S/workflows/edit-native-pptx.md` §7, `$S/workflows/index.md`, `$S/SKILL.md` (Phase Frame: Check includes deck review; Global Execution Discipline item), `$S/scripts/README.md`
- Test: extend `$S/scripts/tests/test_process_gates.py`

**Interfaces:**
- Produces: CLI `python3 scripts/deck_text_dump.py <deck.pptx> [--out validation/deck_text.md]` → markdown, one `## Slide N` section per slide with `### Title`, `### Text` (paragraph per line, tables as pipe rows), `### Notes`, and a counts line `pictures=N groups=N shapes=N`; exit 0; API `dump_deck(pptx_path) -> str`. Stage doc dispatches a reviewer subagent with paths only and writes `validation/deck_review.md` with five PASS/FAIL items.

- [ ] **Step 1: Failing tests**

`$S/scripts/tests/test_deck_text_dump.py`:

```python
#!/usr/bin/env python3
"""deck_text_dump.py turns a PPTX into reviewable markdown."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from pptx import Presentation  # noqa: E402
from pptx.util import Inches, Pt  # noqa: E402

import deck_text_dump  # noqa: E402


def _deck(path: Path) -> None:
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.33), Inches(7.5)
    s = prs.slides.add_slide(prs.slide_layouts[6])
    t = s.shapes.add_textbox(Inches(1), Inches(0.5), Inches(10), Inches(1)); t.text_frame.text = "AgentCore Runtime 개요"
    b = s.shapes.add_textbox(Inches(1), Inches(2), Inches(10), Inches(2))
    b.text_frame.text = "세션 격리 실행 환경"
    p = b.text_frame.add_paragraph(); p.text = "최대 8시간 세션"
    tbl = s.shapes.add_table(2, 2, Inches(1), Inches(4.5), Inches(6), Inches(1)).table
    tbl.cell(0, 0).text = "항목"; tbl.cell(0, 1).text = "값"; tbl.cell(1, 0).text = "리전"; tbl.cell(1, 1).text = "us-west-2"
    s.notes_slide.notes_text_frame.text = "발표자 노트 한 줄"
    prs.save(path)


class DeckTextDumpTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.pptx = Path(self.tmp.name) / "d.pptx"; _deck(self.pptx)

    def test_dump_contains_title_text_table_notes_counts(self) -> None:
        md = deck_text_dump.dump_deck(self.pptx)
        self.assertIn("## Slide 1", md)
        self.assertIn("AgentCore Runtime 개요", md)
        self.assertIn("최대 8시간 세션", md)
        self.assertIn("| 리전 | us-west-2 |", md)
        self.assertIn("### Notes", md); self.assertIn("발표자 노트 한 줄", md)
        self.assertRegex(md, r"pictures=\d+ groups=\d+ shapes=\d+")

    def test_cli_writes_out_file(self) -> None:
        out = Path(self.tmp.name) / "deck_text.md"
        proc = subprocess.run([sys.executable, str(SCRIPTS_DIR / "deck_text_dump.py"), str(self.pptx), "--out", str(out)], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(out.is_file()); self.assertIn("## Slide 1", out.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
```

Extend `test_process_gates.py`:

```python
class DeckReviewGateTests(unittest.TestCase):
    def test_stage_and_reference_exist(self) -> None:
        stage = _read("workflows/stages/deck-review.md"); ref = _read("references/deck-review.md")
        for needle in ("deck_text_dump.py", "validation/deck_review.md", "analysis/storyline.md", "facts.json", "PASS", "FAIL"):
            self.assertIn(needle, stage, needle)
        for needle in ("Technical completeness", "Accuracy", "AI tone", "Audience fit", "Structure", "seamless", "[확인 필요]"):
            self.assertIn(needle, ref, needle)

    def test_routes_run_deck_review_after_export(self) -> None:
        for rel in ("workflows/generate-pptx.md", "workflows/profiles/quick-generate.md", "workflows/edit-native-pptx.md"):
            text = _read(rel)
            self.assertGreater(text.find("deck-review"), text.find("pptx_qa_check.py"), rel)
```

- [ ] **Step 2: RED** — both files fail (ModuleNotFoundError / missing docs).

- [ ] **Step 3: Write deck_text_dump.py**

```python
#!/usr/bin/env python3
"""
PPTX text dump for deck review.

Turn an exported .pptx into markdown a reviewer can read without opening PowerPoint: one section per
slide with title, text (tables as pipe rows), speaker notes, and shape counts.

Usage:
    python3 scripts/deck_text_dump.py <deck.pptx> [--out validation/deck_text.md]

Dependencies:
    python-pptx
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from console_encoding import configure_utf8_stdio  # noqa: E402

configure_utf8_stdio()

from pptx import Presentation  # noqa: E402
from pptx.enum.shapes import MSO_SHAPE_TYPE  # noqa: E402


def _iter_shapes(shapes):
    for shape in shapes:
        if shape.shape_type == MSO_SHAPE_TYPE.GROUP:
            yield from _iter_shapes(shape.shapes)
        else:
            yield shape


def _shape_lines(shape) -> list[str]:
    lines: list[str] = []
    if shape.has_text_frame:
        for para in shape.text_frame.paragraphs:
            text = "".join(run.text for run in para.runs).strip()
            if text:
                lines.append(text)
    if getattr(shape, "has_table", False) and shape.has_table:
        for row in shape.table.rows:
            cells = [cell.text.strip().replace("|", "\\|") for cell in row.cells]
            lines.append("| " + " | ".join(cells) + " |")
    return lines


def dump_deck(pptx_path: str | Path) -> str:
    prs = Presentation(str(pptx_path))
    out: list[str] = [f"# Deck text: {Path(pptx_path).name}", ""]
    for index, slide in enumerate(prs.slides, 1):
        flat = list(_iter_shapes(slide.shapes))
        pictures = sum(1 for s in flat if s.shape_type == MSO_SHAPE_TYPE.PICTURE)
        groups = sum(1 for s in slide.shapes if s.shape_type == MSO_SHAPE_TYPE.GROUP)
        title = ""
        if slide.shapes.title is not None and slide.shapes.title.has_text_frame:
            title = slide.shapes.title.text_frame.text.strip()
        body: list[str] = []
        for shape in flat:
            body.extend(_shape_lines(shape))
        if not title and body:
            title = body[0]
        out.append(f"## Slide {index}")
        out.append(f"### Title\n{title or '(none)'}")
        out.append("### Text\n" + ("\n".join(body) if body else "(none)"))
        notes = ""
        if slide.has_notes_slide and slide.notes_slide.notes_text_frame is not None:
            notes = slide.notes_slide.notes_text_frame.text.strip()
        out.append("### Notes\n" + (notes or "(none)"))
        out.append(f"pictures={pictures} groups={groups} shapes={len(flat)}")
        out.append("")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Dump PPTX slide text, tables and notes as markdown for review.")
    parser.add_argument("pptx")
    parser.add_argument("--out", help="write markdown here instead of stdout")
    args = parser.parse_args(argv)
    path = Path(args.pptx)
    if not path.is_file():
        print(f"Error: {path} not found", file=sys.stderr)
        return 2
    markdown = dump_deck(path)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(markdown, encoding="utf-8")
        print(f"wrote {args.out}")
    else:
        print(markdown)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Write references/deck-review.md (rubric) and workflows/stages/deck-review.md (procedure)**

`references/deck-review.md` — five items, each with what to read, what PASS means, what FAIL looks like, and where the fix belongs:

1. **Technical completeness** — every storyline slide's claim and every *Must-show technical element* is present in `deck_text.md` (diagram/table/code/parameter named); every fact id the storyline cites is used somewhere. FAIL → fix the owning SVG page (or the storyline if the claim was dropped on purpose, with a note).
2. **Accuracy** — numbers, limits, dates, prices, service and API names match `facts.json` exactly; no assertion without a fact id behind it; `[확인 필요]` items are still marked as questions. FAIL → fix text; if the fact is wrong, fix facts.json first.
3. **AI tone** — apply `copy-voice.md` (em/en dash, meta labels, one "A가 아니라 B", 번역투) plus: filler openers, tricolon spam (three parallel adjectives everywhere), buzzwords (seamless, unlock, leverage, robust, cutting-edge, 혁신적인, 게임체인저, 시너지), titles restated in the body, section labels with no content, closing slides that only say "감사합니다". FAIL → rewrite the run; do not pad.
4. **Audience fit** — level matches the storyline's audience; every acronym defined at first use; no slide that a solutions architect would call obvious or, conversely, unexplained internals. FAIL → adjust depth on that slide.
5. **Structure** — one claim per slide, the arc from the storyline is visible in the order, opening states the thesis, closing states the decision/ask and next step; no slide exceeds 60 words of body text (use `deck_text.md` counts). FAIL → split or cut.

Output format for `validation/deck_review.md`:

```markdown
# Deck review — <deck>.pptx (<date>)
| # | Item | Verdict | Evidence (slide, quote) | Fix owner |
|---|---|---|---|---|
| 1 | Technical completeness | PASS/FAIL | … | page/storyline |
…
## Overall: PASS | FAIL (N items)
```

`workflows/stages/deck-review.md` — procedure: (1) run `python3 "${SKILL_DIR}/scripts/deck_text_dump.py" exports/<file>.pptx --out validation/deck_text.md`; (2) dispatch **one fresh reviewer subagent** with paths only — `analysis/storyline.md`, `sources/<slug>.facts.json`, `validation/deck_text.md`, `${SKILL_DIR}/references/deck-review.md`, `${SKILL_DIR}/references/copy-voice.md` — and the instruction to write `validation/deck_review.md` in the rubric's format and return only the Overall line; the authoring agent never reviews its own deck; (3) on FAIL, repair at the owning layer (page SVG → re-run finalize + export + QA gate; storyline → back to Step 3a with the user), then re-run the review; (4) after two FAIL rounds, stop and show the user the open items; (5) the completion report quotes the Overall line and lists any accepted warnings. Mandatory in Default, Quick, and Edit Native (Edit Native: skip only for design-only edits with no text change).

- [ ] **Step 5: Wire the routes and SKILL.md**

- `generate-pptx.md` Step 7: after the "Layout and copy gate" paragraph add "**Deck review gate**: run [`deck-review`](stages/deck-review.md); delivery waits for `Overall: PASS`." Same in `quick-generate.md` §4 and `edit-native-pptx.md` §7. Add the stage to `workflows/index.md`.
- `SKILL.md`: Phase Frame table — Check column mentions deck review (e.g. "Steps 6–7 (QA + deck review)"); Global Execution Discipline item 9 "**Review before delivery** — a fresh-context reviewer scores the export against the storyline and facts (`stages/deck-review.md`); the author never signs off alone."
- `scripts/README.md`: one row for `deck_text_dump.py`.

- [ ] **Step 6: GREEN** — `python3 -m unittest $S/scripts/tests/test_deck_text_dump.py $S/scripts/tests/test_process_gates.py -v` all OK (including `test_skill_md_names_the_process`); full suite no new failures; `deck_text_dump.py /tmp/agentcore-deck/agentcore-intro.pptx | head -40` shows readable output — paste the first slide in the report.

### Task 13: Font fallback (Amazon Ember → Noto Sans / Noto Sans KR)

**Files:**
- Modify: `$S/templates/brands/aws/templates/design_spec.md` §III Typography (and §IV if it lists faces), `$S/references/plan-core.md` §6.2, `$S/references/shared-standards-core.md` §4.1, `$P/README.md` (한 줄: 폰트 안내)
- Test: extend `$S/scripts/tests/test_process_gates.py`

- [ ] **Step 1: Failing test**

```python
class FontFallbackTests(unittest.TestCase):
    def test_aws_brand_declares_ember_with_noto_fallback(self) -> None:
        text = _read("templates/brands/aws/templates/design_spec.md")
        self.assertIn("Amazon Ember", text); self.assertIn("Noto Sans KR", text); self.assertIn("Noto Sans", text)
        self.assertNotIn("Microsoft YaHei", text)

    def test_fallback_rule_documented(self) -> None:
        for rel in ("references/plan-core.md", "references/shared-standards-core.md"):
            self.assertIn("fc-list", _read(rel), rel)
```

- [ ] **Step 2: RED**, then **Step 3: edit**

- Brand spec §III: title `Amazon Ember` 600–700, body `Amazon Ember` 400, code `Amazon Ember Mono`; Hangul face `Noto Sans KR`; Latin fallback `Noto Sans`. Provenance column `approx` as the file already uses. Keep the "PPT Master does not auto-embed fonts" note (rename to aws-ppt-master if the sentence names the tool).
- `plan-core.md` §6.2: add one paragraph after the "stack carries at most one Latin face and one CJK face" rule: "Before locking the stack, check the authoring host: `fc-list | grep -i "<face>"`. A brand may declare a fallback face (the `aws` brand: Amazon Ember → Noto Sans, Hangul Noto Sans KR). When the first face is missing on the authoring host or the delivery target, lock the fallback instead and record the substitution in `design_spec.md §IV`; never lock a face that neither host has, because the export takes the first named face and the renderer will substitute silently."
- `shared-standards-core.md` §4.1: one sentence cross-referencing the same rule.
- `$P/README.md`: under 사용 add "폰트: Amazon Ember 가 설치돼 있으면 사용하고, 없으면 Noto Sans / Noto Sans KR 로 대체합니다(`fc-list | grep -i ember`)."

- [ ] **Step 4: GREEN** + full suite.

### Task 14: Iterate on real output (fresh-agent run 2, inspect, refine)

**Files:**
- Modify: whatever the run reveals (SKILL.md, workflows, references) — each change gets a test or a grep check; no new features.

- [ ] **Step 1: Fresh-agent run 2** — same prompt as Task 9 Step 1 with these additions appended: "Follow the research → storyline → build → deck review process the skill now prescribes. Report additionally: (7) the storyline table you confirmed, (8) the deck review Overall line and any FAIL items you fixed, (9) which research tools you used and how many facts (F-ids) you recorded." Constraints as in run 1 (no git, no edits under the skill dir, no subagents except the single deck reviewer the stage prescribes, ~60 minutes).
- [ ] **Step 2: Inspect the artefacts yourself** — read `analysis/storyline.md`, `sources/*.facts.json`, `validation/deck_text.md`, `validation/deck_review.md` under the run's project; render the deck: `python3 $S/scripts/pptx_to_svg.py --help` then convert to SVGs and rasterise with Playwright (model: `plugins/aws-diagram-design/skills/aws-diagram-design/scripts/pygen/export.py`), open 2–3 PNGs with the Read tool and judge: icons visible and coloured, text not clipped, Korean font rendered, one claim per slide.
- [ ] **Step 3: Refine** — for each defect, decide the owning doc (skill-creator guidance: explain the why, no MUST-shouting, keep SKILL.md < 500 lines, bundle a script if the agent had to write one ad hoc), edit, add a needle/test, re-run `python3 ~/.claude/skills/skill-creator/scripts/quick_validate.py $S` and the suite.
- [ ] **Step 4: Run 3 only if Step 3 changed a gate** — otherwise stop. Record what improved between runs in the ledger and the final report.
