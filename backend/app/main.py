import time
import uuid
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .schemas.request import ImageGenerationRequest
from .schemas.response import (
    ImageGenerationResponse,
    HealthResponse,
    ErrorResponse,
)
from .services.decision_engine import DecisionEngine
from .providers import get_image_provider

app = FastAPI(
    title="Resource-Aware Image Generation API",
    description="Backend service and Decision Engine for educational resource optimization.",
    version="0.1.0",
)

# CORS configuration for React frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Returns service health status and active provider name."""
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        active_provider=settings.active_provider,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@app.post(
    "/api/v1/generate",
    response_model=ImageGenerationResponse,
    responses={
        422: {"model": ErrorResponse, "description": "Validation error"},
        503: {"model": ErrorResponse, "description": "Provider unavailable"},
    },
    tags=["Generation"],
)
async def generate_image(request: ImageGenerationRequest):
    """Processes generation request through the Decision Engine and dispatches to provider."""
    start_time = time.perf_counter()
    job_id = f"gen_{uuid.uuid4().hex[:8]}"

    try:
        # 1. Decision Engine evaluates purpose and selects justifiable configuration
        decision = DecisionEngine.evaluate(request)

        # 2. Retrieve configured provider adapter
        provider = get_image_provider()

        # 3. Generate image using adapter
        image_data = await provider.generate_image(
            request=request,
            config=decision.configuration,
        )

        elapsed = round(time.perf_counter() - start_time, 3)
        metrics = decision.metrics
        metrics.latency_seconds = elapsed

        return ImageGenerationResponse(
            job_id=job_id,
            status="success",
            image=image_data,
            applied_configuration=decision.configuration,
            decision_rationale=decision.rationale,
            resource_metrics=metrics,
        )

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
