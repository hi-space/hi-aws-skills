#!/usr/bin/env python3
"""
Amazon Bedrock image generation backend (Stability AI Stable Image models).

Credentials come from the boto3 default chain (AWS_PROFILE, env keys, SSO, instance role).
Configuration keys (process environment or the resolved .env):
  BEDROCK_REGION                    optional, region used for image generation only;
                                    takes precedence over AWS_REGION/AWS_DEFAULT_REGION.
                                    Use this when a global AWS_REGION doesn't serve the
                                    Stability models.
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
    """Region precedence: BEDROCK_REGION > AWS_REGION > AWS_DEFAULT_REGION > DEFAULT_REGION.

    BEDROCK_REGION lets a user with a global AWS_REGION set to a region that doesn't
    serve the Stability models (e.g. their home region) still generate images correctly,
    without having to override AWS_REGION itself for the whole environment.
    """
    return (
        os.environ.get("BEDROCK_REGION")
        or os.environ.get("AWS_REGION")
        or os.environ.get("AWS_DEFAULT_REGION")
        or DEFAULT_REGION
    )


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
    body_stream = response["body"]
    try:
        body_stream.seek(0)  # tolerate a rewindable stream reused across calls (e.g. tests)
    except (AttributeError, OSError, ValueError):
        pass  # real botocore StreamingBody is not seekable; read forward as usual
    payload = json.loads(body_stream.read().decode("utf-8"))
    elapsed = time.time() - start
    print(f"\n  [DONE] Response received ({elapsed:.1f}s)")

    reasons = payload.get("finish_reasons") or [None]
    if reasons[0]:
        raise RuntimeError(f"Bedrock filtered the request: {reasons[0]}. Rephrase the prompt.")
    images = payload.get("images") or []
    if not images:
        raise RuntimeError("Bedrock returned no image data.")

    path = resolve_output_path(prompt, output_dir, filename, ".png")
    # save_image_bytes already prints "File saved to" + the resolution; no need to repeat.
    return save_image_bytes(base64.b64decode(images[0]), path, "image/png")


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
