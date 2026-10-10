import re
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse

from .config import settings
from .schemas.request import ImageGenerationRequest, InferPurposeRequest
from .schemas.response import (
    ImageGenerationResponse,
    HealthResponse,
    ErrorResponse,
    InferPurposeResponse,
    GenerationRecordResponse,
    AnalyticsResponse,
)
from .services.decision_engine import DecisionEngine
from .services.purpose_inference import infer_purpose_from_prompt
from .services.resource_estimator import get_tier_defaults, TIER_SPECIFICATIONS
from .services.storage import (
    OUTPUTS_DIR,
    save_output_artifact,
    save_generation_record,
    get_generation_history,
    clear_generation_history,
    get_real_analytics,
)
from .providers import (
    get_image_provider,
    Automatic1111ImageProvider,
    Automatic1111ProviderError,
    HuggingFaceProviderError,
    GoogleProviderError,
    OpenRouterProviderError,
)

app = FastAPI(
    title="ResourceAware — Resource-Aware Image Generation API",
    description="Intelligently matches computational effort to intended image purpose and transparently reports compute-work metrics.",
    version="0.2.0",
)

# CORS configuration for React frontend integration (loopback only)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:[0-9]+)?$",
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS", "HEAD", "PUT", "PATCH"],
    allow_headers=["Content-Type", "Authorization", "Accept", "Origin", "X-Requested-With", "*"],
)


@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Returns service health status, active provider, and WebUI connectivity."""
    webui_reachable = False
    api_enabled = False
    loaded_model = None
    error_msg = None

    if settings.active_provider in ("automatic1111", "local", "sd"):
        provider = Automatic1111ImageProvider()
        health_info = await provider.check_health()
        webui_reachable = health_info.get("reachable", False)
        api_enabled = health_info.get("api_enabled", False)
        loaded_model = health_info.get("model")
        error_msg = health_info.get("error")

    return HealthResponse(
        status="healthy",
        version="0.1.0",
        active_provider=settings.active_provider,
        timestamp=datetime.now(timezone.utc).isoformat(),
        webui_reachable=webui_reachable,
        api_enabled=api_enabled,
        loaded_model=loaded_model,
        error=error_msg,
    )


@app.post("/api/v1/infer-purpose", response_model=InferPurposeResponse, tags=["Inference"])
async def infer_purpose_endpoint(request: InferPurposeRequest):
    """Deterministically infers educational purpose and quality tier from natural language."""
    inferred = infer_purpose_from_prompt(request.prompt)
    tier_defaults = get_tier_defaults(inferred.recommended_tier)
    return InferPurposeResponse(
        purpose=inferred.purpose,
        purpose_key=inferred.purpose_key,
        recommended_tier=inferred.recommended_tier,
        reason=inferred.reason,
        confidence=inferred.confidence,
        is_ambiguous=inferred.is_ambiguous,
        suggested_color_mode=inferred.suggested_color_mode,
        default_parameters=tier_defaults,
    )


@app.get("/api/v1/tiers", tags=["Configuration"])
async def get_tier_configurations():
    """Returns centralized quality tier specifications and transparent formulas."""
    return {
        "reference_high": {
            "width": 512,
            "height": 768,
            "steps": 28,
            "work_units": 11010048,
            "normalized_units": 1.0,
            "savings_percent": 0.0,
        },
        "tiers": TIER_SPECIFICATIONS,
        "formula": "work_units = width × height × steps; normalized_units = work_units / 11,010,048; savings_percent = 100 × (1 - normalized_units)",
        "assumptions": "Estimated compute-work units serve as an algorithmic proxy for relative GPU load, not direct physical energy measurements (Joules or kWh).",
    }


@app.post(
    "/api/v1/generate",
    response_model=ImageGenerationResponse,
    responses={
        422: {"model": ErrorResponse, "description": "Validation error"},
        503: {"model": ErrorResponse, "description": "Provider unavailable"},
        500: {"model": ErrorResponse, "description": "Generation error"},
    },
    tags=["Generation"],
)
async def generate_image(request: ImageGenerationRequest):
    """Processes generation request through the Decision Engine and dispatches to provider."""
    start_time = time.perf_counter()
    job_id = f"gen_{uuid.uuid4().hex[:8]}"

    try:
        # 1. Decision Engine evaluates purpose and right-sizes parameters
        decision = DecisionEngine.evaluate(request)

        # 2. Retrieve configured provider adapter
        provider = get_image_provider()
        is_demo = False

        if isinstance(provider, Automatic1111ImageProvider):
            # Check availability - never silently fall back to mock at runtime!
            health = await provider.check_health()
            if not health.get("reachable"):
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=(
                        "Local AUTOMATIC1111 WebUI is unreachable at http://127.0.0.1:7860. "
                        "Please launch the WebUI with the '--api' flag:\n"
                        "Run webui-user.bat with COMMANDLINE_ARGS=--api --medvram"
                    ),
                )
            if not health.get("api_enabled"):
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=(
                        "AUTOMATIC1111 WebUI is running on 127.0.0.1:7860, but the REST API is disabled. "
                        "Please edit webui-user.bat, add '--api' to COMMANDLINE_ARGS, and restart the WebUI."
                    ),
                )
        elif provider.provider_id == "mock":
            is_demo = True

        # 3. Generate image using adapter
        image_data = await provider.generate_image(
            request=request,
            config=decision.configuration,
        )

        # Capture measured elapsed duration via monotonic timer
        elapsed = getattr(image_data, "_measured_elapsed", round(time.perf_counter() - start_time, 3))
        metrics = decision.metrics
        metrics.latency_seconds = elapsed
        metrics.measured_elapsed_seconds = elapsed
        metrics.is_demo = is_demo
        metrics.generation_time_label = "measured"

        # 4. Save generated artifact in controlled outputs directory
        artifact_ref = save_output_artifact(
            job_id=job_id,
            image_url=image_data.url,
            format_hint=image_data.format,
        )
        if artifact_ref:
            image_data.artifact_url = artifact_ref

        # 5. Persist real generation record to SQLite
        try:
            parts = decision.configuration.effective_resolution.split("x")
            w = int(parts[0]) if len(parts) == 2 else 512
            h = int(parts[1]) if len(parts) == 2 else 512
            steps = decision.configuration.steps or 18

            save_generation_record({
                "job_id": job_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "prompt": request.prompt,
                "negative_prompt": request.negative_prompt or "",
                "inferred_purpose": decision.rationale.purpose_identified,
                "recommended_tier": decision.rationale.recommended_tier or "standard",
                "selected_tier": decision.rationale.selected_tier or "standard",
                "tier_overridden": decision.rationale.tier_overridden or False,
                "width": w,
                "height": h,
                "steps": steps,
                "elapsed_seconds": elapsed,
                "compute_work_units": metrics.estimated_compute_work_units or 1.0,
                "savings_percent": metrics.compute_savings_percent or 0.0,
                "model": decision.configuration.model,
                "provider": provider.provider_id,
                "status": "success",
                "image_url": artifact_ref or (image_data.url if len(image_data.url) < 50000 else image_data.url[:500] + "..."),
            })
        except Exception:
            pass  # Do not fail generation response if persistence has a transient issue

        return ImageGenerationResponse(
            job_id=job_id,
            status="success",
            image=image_data,
            applied_configuration=decision.configuration,
            decision_rationale=decision.rationale,
            resource_metrics=metrics,
        )

    except Automatic1111ProviderError as a_err:
        detail_msg = f"{a_err.message}\n\n{a_err.instruction}" if a_err.instruction else a_err.message
        raise HTTPException(
            status_code=a_err.status_code,
            detail=detail_msg,
        )
    except GoogleProviderError as g_err:
        raise HTTPException(
            status_code=g_err.status_code,
            detail=g_err.message,
        )
    except HuggingFaceProviderError as hf_err:
        raise HTTPException(
            status_code=hf_err.status_code,
            detail=hf_err.message,
        )
    except OpenRouterProviderError as or_err:
        raise HTTPException(
            status_code=or_err.status_code,
            detail=or_err.message,
        )
    except HTTPException:
        raise
    except NotImplementedError as nie:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=str(nie),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during generation: {str(exc)}",
        )


@app.get("/api/v1/history", response_model=List[GenerationRecordResponse], tags=["History"])
async def get_history_endpoint(limit: int = 50):
    """Retrieves real persisted generation history records."""
    records = get_generation_history(limit=limit)
    return [
        GenerationRecordResponse(
            job_id=r["job_id"],
            timestamp=r["timestamp"],
            prompt=r["prompt"],
            negative_prompt=r.get("negative_prompt", ""),
            inferred_purpose=r["inferred_purpose"],
            recommended_tier=r["recommended_tier"],
            selected_tier=r["selected_tier"],
            tier_overridden=bool(r["tier_overridden"]),
            width=r["width"],
            height=r["height"],
            steps=r["steps"],
            elapsed_seconds=r["elapsed_seconds"],
            compute_work_units=r["compute_work_units"],
            savings_percent=r["savings_percent"],
            model=r["model"],
            provider=r["provider"],
            status=r["status"],
            image_url=r.get("image_url"),
        )
        for r in records
    ]


@app.delete("/api/v1/history", tags=["History"])
async def clear_history_endpoint():
    """Clears all persisted real generation history records."""
    clear_generation_history()
    return {"status": "cleared", "message": "Generation history cleared successfully."}


@app.get("/api/v1/analytics", response_model=AnalyticsResponse, tags=["Analytics"])
async def get_analytics_endpoint():
    """Computes authentic aggregate metrics derived strictly from real recorded generations."""
    return get_real_analytics()


@app.get("/api/v1/outputs/{filename}", tags=["Outputs"])
async def get_output_artifact_endpoint(filename: str):
    """Securely serves generated image files from the controlled outputs directory.
    
    Validates filenames, prevents directory traversal attacks, and never exposes
    arbitrary or sensitive server filesystem paths.
    """
    # 1. Strict filename validation: alphanumeric, hyphens, underscores, and safe extensions
    if not re.match(r"^[a-zA-Z0-9_\-]+\.(png|jpg|jpeg|webp|svg)$", filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename. Only alphanumeric characters, hyphens, underscores, and safe image extensions (.png, .jpg, .webp, .svg) are allowed.",
        )

    # 2. Path traversal security check
    base_dir = Path(OUTPUTS_DIR).resolve()
    target_path = (base_dir / filename).resolve()

    if not str(target_path).startswith(str(base_dir)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Path traversal is not permitted.",
        )

    # 3. File existence check
    if not target_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Artifact '{filename}' not found.",
        )

    ext = target_path.suffix.lower()
    media_types = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".svg": "image/svg+xml",
    }
    media_type = media_types.get(ext, "application/octet-stream")

    return FileResponse(path=target_path, media_type=media_type)
