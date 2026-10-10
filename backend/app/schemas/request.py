from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class IntendedUseEnum(str, Enum):
    COLORING_WORKSHEET = "coloring_worksheet"
    FLASHCARD = "flashcard"
    CLASSROOM_HANDOUT = "classroom_handout"
    PRESENTATION_SLIDE = "presentation_slide"
    ANNUAL_REPORT_POSTER = "annual_report_poster"
    HALLWAY_BANNER = "hallway_banner"


class ColorPreferenceEnum(str, Enum):
    AUTO = "auto"
    BLACK_AND_WHITE = "black_and_white"
    LINE_ART = "line_art"
    LIMITED_COLOR = "limited_color"
    FULL_COLOR = "full_color"


class DetailLevelEnum(str, Enum):
    MINIMAL = "minimal"
    STANDARD = "standard"
    HIGH = "high"
    ULTRA = "ultra"


class TargetMediumEnum(str, Enum):
    SCREEN_ONLY = "screen_only"
    STANDARD_PRINT = "standard_print"
    HIGH_RESOLUTION_PRINT = "high_resolution_print"


class AspectRatioEnum(str, Enum):
    SQUARE = "1:1"
    PORTRAIT_STANDARD = "3:4"
    LANDSCAPE_STANDARD = "4:3"
    WIDESCREEN = "16:9"
    PORTRAIT_TALL = "9:16"


class GenerationModeEnum(str, Enum):
    OPTIMIZED = "optimized"
    BASELINE = "baseline"


class ImageGenerationRequest(BaseModel):
    prompt: str = Field(
        ...,
        min_length=3,
        max_length=1000,
        description="Text description of the requested image",
        examples=["An outline of an elephant in the savanna for young kids to color"],
    )
    intended_use: IntendedUseEnum = Field(
        ...,
        description="Specific educational use-case to inform resource-aware configuration",
    )
    color_preference: Optional[ColorPreferenceEnum] = Field(
        default=ColorPreferenceEnum.AUTO,
        description="Desired color constraint or auto-detect from purpose",
    )
    detail_level: Optional[DetailLevelEnum] = Field(
        default=DetailLevelEnum.STANDARD,
        description="Fidelity level needed for the use-case",
    )
    target_medium: Optional[TargetMediumEnum] = Field(
        default=TargetMediumEnum.STANDARD_PRINT,
        description="Output destination (screen vs paper print vs large banner)",
    )
    aspect_ratio: Optional[AspectRatioEnum] = Field(
        default=AspectRatioEnum.SQUARE,
        description="Aspect ratio constraint",
    )
    mode: Optional[GenerationModeEnum] = Field(
        default=GenerationModeEnum.OPTIMIZED,
        description="Run in resource-aware optimized mode or naive baseline mode for comparison",
    )
