#!/usr/bin/env python3
"""Names of removed upstream features must not survive anywhere in the skill tree."""

import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[2]
PLUGIN_DIR = SKILL_DIR.parents[1]
TEXT_SUFFIXES = {".py", ".md", ".json", ".txt", ".example", ".yaml", ".yml", ".sh"}

REMOVED_NARRATION = [
    "notes_to_audio", "tts_backends", "narration_sync", "powerpoint_video",
    "video_motion_plan", "video_sound_mix", "video_subtitles",
    "generate-audio", "video-design.md", "edge-tts", "edge_tts", "elevenlabs", "cosyvoice",
    "Narration Audio",
]


def _hits(needles):
    found = []
    for path in list(SKILL_DIR.rglob("*")) + [PLUGIN_DIR / ".env.example"]:
        if not path.is_file() or path.suffix not in TEXT_SUFFIXES and path.name != ".env.example":
            continue
        if "tests" in path.parts:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        try:
            rel = path.relative_to(SKILL_DIR)
        except ValueError:
            rel = path.relative_to(PLUGIN_DIR)
        for needle in needles:
            if needle in text:
                found.append(f"{rel}: {needle}")
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


REMOVED_SEARCH = [
    "image_search", "image_sources/", "image-searcher", "executor-web-image",
    "gemini_watermark_remover", "PEXELS_API_KEY", "PIXABAY_API_KEY", "openverse",
    # "wikimedia" deliberately omitted: it false-positives on scripts/latex_render.py's
    # unrelated Wikimedia Mathoid LaTeX rendering provider and on bundled-asset
    # license notices (templates/icons/THIRD_PARTY_NOTICES.md), neither of which is
    # part of the removed image-search feature.
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


REMOVED_BACKENDS = [
    "backend_gemini", "backend_openai", "GEMINI_API_KEY", "OPENAI_API_KEY",
    "STABILITY_API_KEY", "google-genai", "google.genai", "ai-image-comparison",
    "IMAGE_BACKEND=openai", "IMAGE_BACKEND=gemini",
]


class RemovedBackendsTests(unittest.TestCase):
    def test_backends_gone(self) -> None:
        image_backends_dir = SKILL_DIR / "scripts" / "image_backends"
        for rel in (
            "backend_bfl.py", "backend_fal.py", "backend_gemini.py", "backend_ideogram.py",
            "backend_minimax.py", "backend_modelscope.py", "backend_openai.py",
            "backend_openrouter.py", "backend_qwen.py", "backend_replicate.py",
            "backend_siliconflow.py", "backend_stability.py", "backend_tencent.py",
            "backend_volcengine.py", "backend_zhipu.py",
        ):
            self.assertFalse((image_backends_dir / rel).exists(), rel)
        self.assertFalse(
            (SKILL_DIR / "scripts/tests/test_image_backend_tencent.py").exists()
        )
        self.assertFalse((SKILL_DIR / "references/ai-image-comparison").exists())
        self.assertEqual(_hits(REMOVED_BACKENDS), [])


if __name__ == "__main__":
    unittest.main()
