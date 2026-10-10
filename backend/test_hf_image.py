import os
import sys
from pathlib import Path
from dotenv import load_dotenv

from huggingface_hub import InferenceClient
from huggingface_hub.errors import HfHubHTTPError

# Ensure the repository root and backend directory are in sys.path for robust imports
current_file = Path(__file__).resolve()
backend_dir = current_file.parent
repo_root = backend_dir.parent

if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from backend.app.providers.huggingface_provider import sanitize_error_text

# 1. Load environment variables reliably from backend/.env regardless of CWD
backend_env_path = backend_dir / ".env"
root_env_path = repo_root / ".env"

if root_env_path.is_file():
    load_dotenv(root_env_path)
if backend_env_path.is_file():
    load_dotenv(backend_env_path, override=True)

# Import application settings to ensure model and provider match app config
try:
    from backend.app.config import settings
    configured_model = settings.hf_model
    configured_provider = settings.hf_provider
    token = settings.hf_token or os.getenv("HF_TOKEN", "")
except Exception:
    configured_model = os.getenv("HF_MODEL", "stabilityai/stable-diffusion-xl-base-1.0")
    configured_provider = os.getenv("HF_PROVIDER", "fal-ai")
    token = os.getenv("HF_TOKEN", "")

# 2. Validate token presence without exposing or printing secrets
token = token.strip() if token else ""
if not token:
    print("[ERROR] HF_TOKEN is not configured or is empty.", file=sys.stderr)
    print("Please add HF_TOKEN=<your_huggingface_token> to backend/.env to run this test.", file=sys.stderr)
    sys.exit(1)

print(f"HF_TOKEN found. Initializing Hugging Face client...")
print(f"  Provider : {configured_provider}")
print(f"  Model    : {configured_model}")

client = InferenceClient(
    provider=configured_provider,
    api_key=token,
)

prompt = "A simple black-and-white cat colouring sheet for children, clean line art"
output_path = (backend_dir / "test_generated.png").resolve()

print(f"Submitting text-to-image request for '{configured_model}'...")

try:
    image = client.text_to_image(
        prompt=prompt,
        negative_prompt="color, colored, shading, shadow, grayscale gradients, photorealistic",
        model=configured_model,
        num_inference_steps=20,
        width=1024,
        height=1024,
    )
    image.save(output_path)
    print(f"Success! Live image generated and saved to: {output_path}")
    sys.exit(0)

except HfHubHTTPError as hf_err:
    status_code = getattr(getattr(hf_err, "response", None), "status_code", None)
    server_message = getattr(hf_err, "server_message", "") or ""
    raw_error_text = str(hf_err)

    sanitized_msg = sanitize_error_text(server_message or raw_error_text, token)

    if status_code == 402 or "402" in raw_error_text or "credits" in raw_error_text.lower():
        print("\n" + "=" * 60, file=sys.stderr)
        print("[BILLING / CREDIT ERROR] HTTP 402 Payment Required", file=sys.stderr)
        print(f"Upstream Provider : {configured_provider}", file=sys.stderr)
        print(f"Server Message    : {sanitized_msg.strip()}", file=sys.stderr)
        print("Diagnosis         : Your Hugging Face account has 0 remaining credits for partner provider 'fal-ai'.", file=sys.stderr)
        print("Action Required   : Inference cannot proceed on fal-ai without pre-paid credits.", file=sys.stderr)
        print("Offline Fallback  : Use ACTIVE_PROVIDER=mock in backend/.env for free local/mock testing.", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        sys.exit(2)

    elif status_code in (401, 403) or "unauthorized" in raw_error_text.lower():
        print("\n" + "=" * 60, file=sys.stderr)
        print(f"[AUTHENTICATION ERROR] HTTP {status_code or 401} Unauthorized", file=sys.stderr)
        print("Diagnosis         : The provided HF_TOKEN is invalid or lacks 'Inference' permissions.", file=sys.stderr)
        print("Action Required   : Verify your token at https://huggingface.co/settings/tokens.", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        sys.exit(2)

    elif status_code == 429 or "429" in raw_error_text:
        print("\n" + "=" * 60, file=sys.stderr)
        print("[RATE LIMIT ERROR] HTTP 429 Too Many Requests", file=sys.stderr)
        print("Diagnosis         : Upstream API rate limit reached. Please wait before retrying.", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        sys.exit(2)

    elif status_code == 404:
        print("\n" + "=" * 60, file=sys.stderr)
        print(f"[MODEL ERROR] HTTP 404 Model or Provider Not Found", file=sys.stderr)
        print(f"Diagnosis         : Model '{configured_model}' not found on provider '{configured_provider}'.", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        sys.exit(2)

    else:
        print("\n" + "=" * 60, file=sys.stderr)
        print(f"[UPSTREAM ERROR] HTTP {status_code or 502}", file=sys.stderr)
        print(f"Details           : {sanitized_msg}", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        sys.exit(2)

except Exception as exc:
    sanitized_exc = sanitize_error_text(str(exc), token)
    print("\n" + "=" * 60, file=sys.stderr)
    print(f"[UNEXPECTED ERROR] Generation failed", file=sys.stderr)
    print(f"Details: {sanitized_exc}", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    sys.exit(2)
