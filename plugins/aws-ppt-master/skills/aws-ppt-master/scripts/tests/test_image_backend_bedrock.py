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

    def test_bedrock_region_takes_precedence_over_aws_region(self) -> None:
        # A user's global AWS_REGION (e.g. their home region) must not force Bedrock
        # image generation into a region that doesn't serve the Stability models.
        os.environ["AWS_REGION"] = "us-east-1"
        os.environ["BEDROCK_REGION"] = "us-west-2"
        self._generate()
        backend_bedrock._client.assert_called_with("us-west-2")

    def test_aws_default_region_used_when_aws_region_unset(self) -> None:
        os.environ["AWS_DEFAULT_REGION"] = "eu-west-1"
        self._generate()
        backend_bedrock._client.assert_called_with("eu-west-1")

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
