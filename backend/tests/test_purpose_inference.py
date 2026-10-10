"""Tests for Deterministic Purpose Inference and Tier Recommendation Engine.

Tests compliance with Hackathon Constraint 2:
- Acceptance test 1: Colouring sheet for young child -> Eco
- Acceptance test 2: Educational poster -> Standard
- Acceptance test 3: Printed exhibition banner -> High
- Additional educational use cases: worksheets, flashcards, slides, diagrams
- Ambiguous prompts and conservative defaults
"""

import pytest
from backend.app.services.purpose_inference import infer_purpose_from_prompt
from backend.app.services.decision_engine import DecisionEngine
from backend.app.schemas.request import ImageGenerationRequest, IntendedUseEnum


def test_acceptance_prompt_colouring_sheet():
    prompt = "Make a simple black-and-white colouring sheet of a butterfly for a seven-year-old."
    result = infer_purpose_from_prompt(prompt)

    assert result.purpose == "Children's colouring sheet"
    assert result.recommended_tier == "eco"
    assert "Simple outlines" in result.reason
    assert "black-and-white output" in result.reason
    assert result.suggested_color_mode == "monochrome_line_art"
    assert result.is_ambiguous is False


def test_acceptance_prompt_educational_poster():
    prompt = "Create an illustrated educational poster about the water cycle."
    result = infer_purpose_from_prompt(prompt)

    assert result.purpose == "Educational poster"
    assert result.recommended_tier == "standard"
    assert "readable composition" in result.reason
    assert result.is_ambiguous is False


def test_acceptance_prompt_printed_banner():
    prompt = "Create a highly detailed illustration for a large printed school exhibition banner."
    result = infer_purpose_from_prompt(prompt)

    assert result.purpose == "Large-format printed banner"
    assert result.recommended_tier == "high"
    assert "intended print use" in result.reason
    assert result.is_ambiguous is False


def test_worksheet_and_classroom_handout():
    prompt = "Math worksheet geometry activity with angle triangles"
    result = infer_purpose_from_prompt(prompt)

    assert result.purpose == "Worksheet / classroom handout"
    assert result.recommended_tier == "eco"
    assert "handouts" in result.reason.lower()


def test_educational_flashcard():
    prompt = "A simple flashcard illustration of an apple for vocabulary"
    result = infer_purpose_from_prompt(prompt)

    assert result.purpose == "Educational flashcard"
    assert result.recommended_tier == "eco"
    assert "Flashcards prioritize" in result.reason


def test_lesson_diagram():
    prompt = "A labeled science diagram of plant photosynthesis cycle"
    result = infer_purpose_from_prompt(prompt)

    assert result.purpose == "Lesson diagram / educational infographic"
    assert result.recommended_tier == "standard"
    assert "Lesson diagrams require" in result.reason


def test_presentation_slide():
    prompt = "A presentation slide illustrating plate tectonics for grade 8"
    result = infer_purpose_from_prompt(prompt)

    assert result.purpose == "Classroom presentation slide"
    assert result.recommended_tier == "standard"


def test_ambiguous_prompt_conservative_default():
    prompt = "A cute green turtle"
    result = infer_purpose_from_prompt(prompt)

    assert result.recommended_tier == "standard"
    assert result.is_ambiguous is True
    assert "conservative" in result.reason.lower() or "default" in result.reason.lower()


def test_purpose_inference_with_user_override():
    # Inferred tier is Eco, but user requests High override
    req = ImageGenerationRequest(
        prompt="Make a simple black-and-white colouring sheet of a butterfly for a seven-year-old.",
        quality_tier="high",
    )
    decision = DecisionEngine.evaluate(req)

    assert decision.rationale.recommended_tier == "eco"
    assert decision.rationale.selected_tier == "high"
    assert decision.rationale.tier_overridden is True
    assert any("User manual override applied" in r for r in decision.rationale.reasons)


def test_small_thumbnail_icon_infers_eco():
    test_cases = [
        "A small thumbnail icon for a personal project.",
        "A simple favicon of a blue bird",
        "A profile avatar for a student portal",
        "A small badge icon for achievements",
    ]
    for prompt in test_cases:
        result = infer_purpose_from_prompt(prompt)
        assert result.purpose == "Small icon / thumbnail", f"Failed for {prompt}"
        assert result.recommended_tier == "eco", f"Failed for {prompt}"
        assert "icon" in result.reason.lower() or "thumbnail" in result.reason.lower()
        assert result.suggested_color_mode == "isolated_subject"
        assert result.is_ambiguous is False


def test_icon_conflicting_with_high_res_print_prefers_high():
    # Prompt combines icon keywords with explicit high-resolution or large-format print requirements
    prompt = "A high-resolution printed promotional banner with detailed typography and icons."
    result = infer_purpose_from_prompt(prompt)

    # Must NOT be overridden by Eco icon rule
    assert result.purpose_key == "large_format_banner"
    assert result.recommended_tier == "high"
    assert result.is_ambiguous is False

    # Another conflict case: high-resolution print display
    prompt2 = "A high-resolution exhibition display banner with custom icons"
    result2 = infer_purpose_from_prompt(prompt2)
    assert result2.purpose_key == "large_format_banner"
    assert result2.recommended_tier == "high"


def test_empty_or_whitespace_prompt_handling():
    for empty_p in ["", "   ", "\t\n"]:
        result = infer_purpose_from_prompt(empty_p)
        assert result.recommended_tier == "standard"
        assert result.is_ambiguous is True
        assert "empty prompt" in result.reason.lower() or "default" in result.reason.lower()


def test_icon_thumbnail_intended_use_decision_engine():
    req = ImageGenerationRequest(
        prompt="A simple icon of an open textbook",
        intended_use=IntendedUseEnum.ICON_THUMBNAIL,
    )
    decision = DecisionEngine.evaluate(req)

    assert decision.rationale.recommended_tier == "eco"
    assert decision.rationale.selected_tier == "eco"
    assert decision.configuration.quality_tier == "eco"
    assert decision.configuration.effective_resolution == "384x384"
    assert decision.configuration.steps == 10
    assert decision.rationale.tier_overridden is False


def test_icon_thumbnail_override_decision_engine():
    # Inferred tier is Eco for icon, user explicitly overrides to High
    req = ImageGenerationRequest(
        prompt="A small app icon of a calculator",
        quality_tier="high",
    )
    decision = DecisionEngine.evaluate(req)

    assert decision.rationale.recommended_tier == "eco"
    assert decision.rationale.selected_tier == "high"
    assert decision.rationale.tier_overridden is True
    assert decision.configuration.quality_tier == "high"
    assert decision.configuration.effective_resolution == "512x768"
    assert decision.configuration.steps == 28

