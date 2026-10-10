from typing import List, Optional
from pydantic import BaseModel, Field


class ImageData(BaseModel):
    url: str = Field(..., description="Image URL or data URI")
    format: str = Field(..., description="Image format, e.g. svg, png, webp")
    width: int = Field(..., description="Width in pixels")
    height: int = Field(..., description="Height in pixels")


class AppliedConfiguration(BaseModel):
    model: str = Field(..., description="Model identifier selected")
    quality_tier: str = Field(..., description="Selected quality tier (e.g. standard vs hd)")
    effective_resolution: str = Field(..., description="Width x Height resolution used")
    steps: Optional[int] = Field(None, description="Inference steps if supported by provider")
    color_mode: str = Field(..., description="Enforced color/style profile")
    prompt_refinement: str = Field(..., description="Refined prompt submitted to the provider")


class DecisionRationale(BaseModel):
    summary: str = Field(..., description="Concise human-readable explanation of choices")
    purpose_identified: str = Field(..., description="The purpose category targeted")
    reasons: List[str] = Field(..., description="Specific resource-saving considerations applied")


class ResourceMetrics(BaseModel):
    estimated_cost_usd: float = Field(..., description="Cost of the optimized request in USD")
    baseline_cost_usd: float = Field(..., description="Naive baseline cost without purpose-awareness")
    cost_reduction_percent: float = Field(..., description="Calculated savings percentage")
    pricing_source: str = Field(..., description="Documentation or verification source for pricing basis")
    latency_seconds: Optional[float] = Field(None, description="Request execution latency in seconds")


class ImageGenerationResponse(BaseModel):
    job_id: str = Field(..., description="Unique generation run ID")
    status: str = Field(default="success", description="Status of generation execution")
    image: ImageData = Field(..., description="Generated image metadata and data URL")
    applied_configuration: AppliedConfiguration = Field(..., description="Configuration selected by engine")
    decision_rationale: DecisionRationale = Field(..., description="Explanation for the configuration")
    resource_metrics: ResourceMetrics = Field(..., description="Quantified cost and resource metrics")


class ErrorResponse(BaseModel):
    error_code: str = Field(..., description="Machine-readable error identifier")
    message: str = Field(..., description="Human-readable explanation of the issue")
    fallback_available: bool = Field(default=False, description="Whether fallback mock can be used")


class HealthResponse(BaseModel):
    status: str
    version: str
    active_provider: str
    timestamp: str
