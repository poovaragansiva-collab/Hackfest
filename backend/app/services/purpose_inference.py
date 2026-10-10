"""Deterministic Purpose Inference and Tier Recommendation Engine.

Analyzes natural-language educational prompts to infer the intended classroom or
district use-case and recommends a justifiable compute-effort quality tier.

Satisfies Challenge Constraint 2:
- Deterministic, testable rules (no unnecessary external LLM dependency).
- Supported use cases:
  1. Children's colouring sheets (Eco)
  2. Worksheets and classroom handouts (Eco)
  3. Flashcards and simple educational illustrations (Eco)
  4. Lesson diagrams and educational infographics (Standard)
  5. Classroom presentation slides (Standard)
  6. Educational posters (Standard)
  7. Printed banners and large-format displays (High)
  8. Detailed illustrations (High)
  9. General-purpose educational requests (Standard, marked conservative default)
"""

import re
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class InferredPurpose(BaseModel):
    purpose: str = Field(..., description="Human-readable inferred educational purpose")
    purpose_key: str = Field(..., description="Machine-readable purpose identifier")
    recommended_tier: str = Field(..., description="Recommended quality tier: 'eco', 'standard', or 'high'")
    reason: str = Field(..., description="Explicit rationale for the tier recommendation")
    confidence: str = Field(default="high", description="Inference confidence: 'high', 'moderate', 'low'")
    is_ambiguous: bool = Field(default=False, description="Whether the prompt lacked explicit medium/detail cues")
    suggested_color_mode: str = Field(default="standard_color", description="Suggested color profile for rendering")


# Regex patterns and associated purpose rules
# Evaluated in priority order: highly specific constraints first
PURPOSE_RULES = [
    # 1. Children's Colouring Sheets
    {
        "purpose_key": "coloring_sheet",
        "purpose": "Children's colouring sheet",
        "tier": "eco",
        "reason": "Simple outlines, black-and-white output, and classroom worksheet use do not require maximum rendering effort.",
        "patterns": [
            r"\bcolou?ring\s+(sheet|page|book|worksheet|picture|outline|art|image|drawing)\b",
            r"\bcolou?r\s+in\b",
            r"\bblack[- ]and[- ]white\s+(outline|drawing|sheet|page|illustration)\b",
            r"\b(simple\s+outline|bold\s+outline|line\s*art\s+outline)\b",
            r"\bfor\s+(a\s+)?([3-9]|1[0-2])[- ]year[- ]old\b.*\b(colou?r|draw|outline|sheet)\b",
            r"\b(colou?r|draw|outline|sheet)\b.*\bfor\s+(a\s+)?([3-9]|1[0-2])[- ]year[- ]old\b",
            r"\boutline\s+of\s+.*\bto\s+colou?r\b",
        ],
        "suggested_color_mode": "monochrome_line_art",
    },
    # 2. Large-Format Printed Banners and Displays
    {
        "purpose_key": "large_format_banner",
        "purpose": "Large-format printed banner",
        "tier": "high",
        "reason": "The intended print use and detail requirements justify greater rendering effort.",
        "patterns": [
            r"\b(exhibition|hallway|auditorium|school|campus|gym|stage)\s+banner\b",
            r"\b(large[- ]format|large[- ]printed|large\s+print)\b",
            r"\bprinted\s+(banner|billboard|mural|exhibition)\b",
            r"\bbanner\s+for\s+(a\s+)?(school|exhibition|hallway|auditorium)\b",
            r"\bexhibition\s+display\b",
        ],
        "suggested_color_mode": "vibrant_color",
    },
    # 3. Detailed Illustrations
    {
        "purpose_key": "detailed_illustration",
        "purpose": "Detailed illustration",
        "tier": "high",
        "reason": "Intricate artistic detail, complex textures, and high visual fidelity justify full sampling passes and maximum supported resolution.",
        "patterns": [
            r"\bhighly\s+detailed\s+(illustration|artwork|rendering|drawing|painting)\b",
            r"\b(intricate|photorealistic|hyperrealistic|ultra[- ]detailed|fine[- ]art)\b",
            r"\bhigh[- ]resolution\s+illustration\b",
            r"\bannual\s+report\s+(cover|illustration|showcase)\b",
        ],
        "suggested_color_mode": "vibrant_color",
    },
    # 4. Small Thumbnails, Icons, Favicons, Avatars, and Badges
    {
        "purpose_key": "icon_thumbnail",
        "purpose": "Small icon / thumbnail",
        "tier": "eco",
        "reason": "Small icons, thumbnails, favicons, and avatars focus on compact, simplified visual subjects that do not require high rendering resolution or heavy sampling passes.",
        "patterns": [
            r"\b(thumbnails?|icons?|favicons?|avatars?|small\s+badges?|app\s+icons?|ui\s+icons?)\b",
            r"\bsmall\s+(graphic|symbol|logo|badge)\b",
            r"\bprofile\s+(picture|pic|avatar|photo|icon)\b",
        ],
        "suggested_color_mode": "isolated_subject",
    },
    # 5. Educational Flashcards
    {
        "purpose_key": "flashcard",
        "purpose": "Educational flashcard",
        "tier": "eco",
        "reason": "Flashcards prioritize subject clarity and high contrast over fine textural nuance, conserving compute.",
        "patterns": [
            r"\bflash[- ]?cards?\b",
            r"\bvocabulary\s+cards?\b",
            r"\balphabet\s+cards?\b",
            r"\bstudy\s+cards?\b",
            r"\bsimple\s+card\s+illustration\b",
        ],
        "suggested_color_mode": "isolated_subject",
    },
    # 5. Worksheets and Classroom Handouts
    {
        "purpose_key": "classroom_handout",
        "purpose": "Worksheet / classroom handout",
        "tier": "eco",
        "reason": "Classroom worksheets and handouts are printed in volume where simple composition and minimal sampling steps are optimal.",
        "patterns": [
            r"\bworksheets?\b",
            r"\bclassroom\s+(handouts?|activity|exercise)\b",
            r"\bhandouts?\b",
            r"\bhomework\s+sheets?\b",
            r"\bexercise\s+sheets?\b",
            r"\bprintable\s+handouts?\b",
            r"\bquiz\s+illustration\b",
        ],
        "suggested_color_mode": "monochrome_line_art",
    },
    # 6. Lesson Diagrams and Educational Infographics
    {
        "purpose_key": "educational_infographic",
        "purpose": "Lesson diagram / educational infographic",
        "tier": "standard",
        "reason": "Lesson diagrams require clear structural composition and moderate detail without automatically using the most expensive settings.",
        "patterns": [
            r"\b(lesson|science|biology|physics|chemistry|anatomy|geography|math)\s+diagram\b",
            r"\bdiagram\s+of\b",
            r"\b(infographics?|flowcharts?|schematics?)\b",
            r"\blabeled\s+diagram\b",
            r"\bprocess\s+diagram\b",
            r"\bcycle\s+diagram\b",
        ],
        "suggested_color_mode": "standard_color",
    },
    # 7. Classroom Presentation Slides
    {
        "purpose_key": "presentation_slide",
        "purpose": "Classroom presentation slide",
        "tier": "standard",
        "reason": "Screen-projected presentation slides require balanced resolution and color clarity without high-density print rendering passes.",
        "patterns": [
            r"\b(presentation|lecture|classroom)\s+slides?\b",
            r"\bslide\s+deck\b",
            r"\bpowerpoint\b",
            r"\bkeynote\b",
            r"\bslideshow\b",
        ],
        "suggested_color_mode": "standard_color",
    },
    # 8. Educational Posters
    {
        "purpose_key": "educational_poster",
        "purpose": "Educational poster",
        "tier": "standard",
        "reason": "The poster needs readable composition and moderate detail without automatically using the most expensive settings.",
        "patterns": [
            r"\b(educational|classroom|wall|science|history|reading|math)\s+posters?\b",
            r"\bposters?\s+about\b",
            r"\bposters?\s+of\b",
            r"\bposters?\b",
        ],
        "suggested_color_mode": "standard_color",
    },
]


def infer_purpose_from_prompt(prompt: str) -> InferredPurpose:
    """Deterministically infers educational purpose and quality tier from natural language."""
    if not prompt or not prompt.strip():
        return InferredPurpose(
            purpose="General-purpose educational request",
            purpose_key="general_purpose",
            recommended_tier="standard",
            reason="Empty prompt received; defaulting to Standard tier as a resource-aware baseline.",
            confidence="low",
            is_ambiguous=True,
            suggested_color_mode="standard_color",
        )

    text = prompt.lower().strip()

    # Special check for acceptance test 1:
    # "Make a simple black-and-white colouring sheet of a butterfly for a seven-year-old."
    # Both colouring indicators and age indicators strongly map to coloring_sheet.
    for rule in PURPOSE_RULES:
        for pattern in rule["patterns"]:
            if re.search(pattern, text, re.IGNORECASE):
                # Extra check for small icon keywords conflicting with explicit high-resolution/print requirements
                if rule["purpose_key"] == "icon_thumbnail":
                    if re.search(
                        r"\b(high[- ]resolution|high[- ]res|large[- ]format|large[- ]printed|large\s+print|printed\s+banner|billboard|exhibition|poster|banner|detailed\s+typography|photorealistic|hyperrealistic|highly\s+detailed)\b",
                        text,
                        re.IGNORECASE,
                    ):
                        # Explicit high-resolution, print, or large-format requirement detected; avoid overriding with Eco!
                        continue
                return InferredPurpose(
                    purpose=rule["purpose"],
                    purpose_key=rule["purpose_key"],
                    recommended_tier=rule["tier"],
                    reason=rule["reason"],
                    confidence="high",
                    is_ambiguous=False,
                    suggested_color_mode=rule["suggested_color_mode"],
                )

    # Secondary check: general keyword cues
    if "outline" in text or "black and white" in text or "b&w" in text or "line art" in text:
        return InferredPurpose(
            purpose="Line art illustration",
            purpose_key="coloring_sheet",
            recommended_tier="eco",
            reason="Outline and monochrome styling detected; Eco tier recommended to minimize inference steps.",
            confidence="moderate",
            is_ambiguous=False,
            suggested_color_mode="monochrome_line_art",
        )

    if "banner" in text or "large" in text or "print" in text and "exhibit" in text:
        return InferredPurpose(
            purpose="Large-format printed display",
            purpose_key="large_format_banner",
            recommended_tier="high",
            reason="Large-format display keywords detected; High tier selected for print fidelity.",
            confidence="moderate",
            is_ambiguous=False,
            suggested_color_mode="vibrant_color",
        )

    if "icon" in text or "thumbnail" in text or "avatar" in text or "favicon" in text:
        if not re.search(r"\b(high[- ]resolution|large|print|banner|exhibit)\b", text, re.IGNORECASE):
            return InferredPurpose(
                purpose="Small icon / thumbnail",
                purpose_key="icon_thumbnail",
                recommended_tier="eco",
                reason="Small icons and thumbnails focus on compact, simplified subjects that do not require high rendering resolution or heavy sampling passes.",
                confidence="moderate",
                is_ambiguous=False,
                suggested_color_mode="isolated_subject",
            )

    # Ambiguous / general fallback
    return InferredPurpose(
        purpose="General-purpose educational request",
        purpose_key="general_purpose",
        recommended_tier="standard",
        reason="Prompt does not specify a print medium or outline constraint; applying balanced Standard tier as a conservative, resource-aware default.",
        confidence="moderate",
        is_ambiguous=True,
        suggested_color_mode="standard_color",
    )
