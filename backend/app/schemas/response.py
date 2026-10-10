from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ImageData(BaseModel):
    url: str = Field(..., description="Image URL or data URI")
    format: str = Field(..., description="Image format, e.g. svg, png, webp")
    width: int = Field(..., description="Width in pixels")
    height: int = Field(..., description="Height in pixels")
    actual_cost_usd: Optional[float] = Field(None, description="Actual API cost returned by the provider if available")
    artifact_url: Optional[str] = Field(None, description="Valid served endpoint reference for saved output artifact")


class AppliedConfiguration(BaseModel):
    model: str = Field(..., description="Model identifier selected")
    quality_tier: str = Field(..., description="Selected quality tier (e.g. eco, standard, high)")
    effective_resolution: str = Field(..., description="Width x Height resolution used")
    steps: Optional[int] = Field(None, description="Inference steps if supported by provider")
    color_mode: str = Field(..., description="Enforced color/style profile")
    prompt_refinement: str = Field(..., description="Refined prompt submitted to the provider")
    sampler_name: Optional[str] = Field("Euler a", description="Sampling algorithm used")
    cfg_scale: Optional[float] = Field(7.0, description="Classifier Free Guidance scale")


class DecisionRationale(BaseModel):
    summary: str = Field(..., description="Concise human-readable explanation of choices")
    purpose_identified: str = Field(..., description="The purpose category targeted")
    reasons: List[str] = Field(..., description="Specific resource-saving considerations applied")
    recommended_tier: Optional[str] = Field(None, description="Automatically recommended quality tier")
    selected_tier: Optional[str] = Field(None, description="Final user-selected quality tier")
    tier_overridden: Optional[bool] = Field(False, description="True if user overrode the recommendation")


class ResourceMetrics(BaseModel):
    estimated_cost_usd: float = Field(..., description="Estimated cost of the optimized request in USD")
    baseline_cost_usd: float = Field(..., description="Naive baseline cost without purpose-awareness in USD")
    cost_reduction_percent: float = Field(..., description="Calculated savings percentage against baseline")
    actual_cost_usd: Optional[float] = Field(
        None, description="Actual upstream API cost billed in USD if returned by provider"
    )
    unit: str = Field(default="USD", description="Currency or metric unit for the estimate")
    provenance: str = Field(
        ...,
        description=(
            "Provenance of metric: 'mock_illustrative' (offline dev mock), "
            "'reference_estimate' (published benchmark), or 'verified_live' (actual API bill)"
        ),
    )
    pricing_basis: str = Field(..., description="Documented pricing benchmark and tier reference")
    pricing_source: str = Field(..., description="Documentation or verification source citation")
    is_live_billed: bool = Field(
        default=False,
        description="Explicit boolean stating whether live financial billing occurred",
    )
    calculation_explanation: Optional[str] = Field(
        None, description="Transparent explanation of how the baseline and savings were calculated"
    )
    latency_seconds: Optional[float] = Field(None, description="Request execution latency in seconds")
    
    # Transparent Compute-Work Proxy Metrics (Constraint 1)
    work_units: Optional[int] = Field(None, description="Actual compute work: width × height × steps")
    high_reference_units: Optional[int] = Field(
        11010048, description="Reference High units: 512 × 768 × 28 = 11,010,048"
    )
    estimated_compute_work_units: Optional[float] = Field(
        None, description="Normalized compute-work units relative to High (High = 1.0)"
    )
    compute_savings_percent: Optional[float] = Field(
        None, description="Relative compute-work savings vs High reference (High = 0%)"
    )
    formula: Optional[str] = Field(
        None, description="Exact formula string: work_units / high_reference_units"
    )
    assumptions: Optional[str] = Field(
        None, description="Explanation of compute-work proxy assumptions"
    )
    measured_elapsed_seconds: Optional[float] = Field(
        None, description="Actual measured generation duration via system monotonic timer"
    )

    # Legacy compatibility fields
    relative_resource_units: Optional[float] = Field(
        default=2.0,
        description="Estimated relative resource units (Eco: 1, Standard: 2, High Quality: 4)",
    )
    baseline_resource_units: Optional[float] = Field(
        default=4.0,
        description="Naive High Quality baseline relative resource units",
    )
    resource_savings_percent: Optional[float] = Field(
        default=50.0,
        description="Relative resource units saved compared with High Quality baseline",
    )
    is_demo: Optional[bool] = Field(
        default=False,
        description="True if output is a simulated demo preview and not AI-generated",
    )
    generation_time_label: Optional[str] = Field(
        default="measured",
        description="Whether timing is 'measured' or 'illustrative_estimate'",
    )
    calculation_method: Optional[str] = Field(
        default="illustrative_relative_units",
        description="Calculation methodology",
    )


class ImageGenerationResponse(BaseModel):
    job_id: str = Field(..., description="Unique generation run ID")
    status: str = Field(default="success", description="Status of generation execution")
    image: ImageData = Field(..., description="Generated image metadata and data URL")
    applied_configuration: AppliedConfiguration = Field(..., description="Configuration selected by engine")
    decision_rationale: DecisionRationale = Field(..., description="Explanation for the configuration")
    resource_metrics: ResourceMetrics = Field(..., description="Quantified cost and resource metrics")


class InferPurposeResponse(BaseModel):
    purpose: str = Field(..., description="Human-readable educational purpose")
    purpose_key: str = Field(..., description="Machine identifier for purpose")
    recommended_tier: str = Field(..., description="Recommended quality tier: 'eco', 'standard', 'high'")
    reason: str = Field(..., description="Explicit rationale for tier recommendation")
    confidence: str = Field(..., description="Inference confidence")
    is_ambiguous: bool = Field(..., description="Whether the prompt was ambiguous")
    suggested_color_mode: str = Field(..., description="Suggested color mode")
    default_parameters: Dict[str, Any] = Field(..., description="Resolution, steps, and compute-work preview")


class GenerationRecordResponse(BaseModel):
    job_id: str
    timestamp: str
    prompt: str
    negative_prompt: Optional[str] = ""
    inferred_purpose: str
    recommended_tier: str
    selected_tier: str
    tier_overridden: bool
    width: int
    height: int
    steps: int
    elapsed_seconds: float
    compute_work_units: float
    savings_percent: float
    model: str
    provider: str
    status: str
    image_url: Optional[str] = None


class AnalyticsResponse(BaseModel):
    total_generations: int
    eco_count: int
    standard_count: int
    high_count: int
    overridden_count: int
    total_compute_units: float
    baseline_units: float
    units_saved: float
    overall_savings_percent: float
    avg_elapsed_seconds: float
    is_empty: bool


class ErrorResponse(BaseModel):
    error_code: str = Field(..., description="Machine-readable error identifier")
    message: str = Field(..., description="Human-readable explanation of the issue")
    fallback_available: bool = Field(default=False, description="Whether fallback mock can be used")
    instruction: Optional[str] = Field(None, description="Actionable user instructions")


class HealthResponse(BaseModel):
    status: str
    version: str
    active_provider: str
    timestamp: str
    webui_reachable: Optional[bool] = None
    api_enabled: Optional[bool] = None
    loaded_model: Optional[str] = None
    error: Optional[str] = None
