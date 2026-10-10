"""Tests for Quality Tier Configuration and Parameter Mapping.

Verifies that Eco, Standard, and High tiers configure distinct real API parameters
matching hardware limits (4 GB VRAM on NVIDIA RTX 2050):
- Eco: 384x384, 10 steps, batch size 1
- Standard: 512x512, 18 steps, batch size 1
- High: 512x768, 28 steps, batch size 1
"""

import pytest
from backend.app.config import settings
from backend.app.schemas.request import ImageGenerationRequest
from backend.app.services.decision_engine import DecisionEngine
from backend.app.services.resource_estimator import (
    get_tier_defaults,
    TIER_SPECIFICATIONS,
)


@pytest.fixture(autouse=True)
def use_sd_provider(monkeypatch):
    monkeypatch.setattr(settings, "active_provider", "automatic1111")


def test_tier_specifications_table():
    eco = get_tier_defaults("eco")
    assert eco["width"] == 384
    assert eco["height"] == 384
    assert eco["steps"] == 10
    assert eco["batch_size"] == 1

    std = get_tier_defaults("standard")
    assert std["width"] == 512
    assert std["height"] == 512
    assert std["steps"] == 18
    assert std["batch_size"] == 1

    high = get_tier_defaults("high")
    assert high["width"] == 512
    assert high["height"] == 768
    assert high["steps"] == 28
    assert high["batch_size"] == 1


def test_decision_engine_configures_distinct_parameters():
    # 1. Eco tier
    req_eco = ImageGenerationRequest(
        prompt="A butterfly coloring sheet for young kids",
        quality_tier="eco",
    )
    dec_eco = DecisionEngine.evaluate(req_eco)
    assert dec_eco.configuration.effective_resolution == "384x384"
    assert dec_eco.configuration.steps == 10

    # 2. Standard tier
    req_std = ImageGenerationRequest(
        prompt="Solar system poster for middle school",
        quality_tier="standard",
    )
    dec_std = DecisionEngine.evaluate(req_std)
    assert dec_std.configuration.effective_resolution == "512x512"
    assert dec_std.configuration.steps == 18

    # 3. High tier
    req_high = ImageGenerationRequest(
        prompt="Exhibition banner for school science hall",
        quality_tier="high",
    )
    dec_high = DecisionEngine.evaluate(req_high)
    assert dec_high.configuration.effective_resolution == "512x768"
    assert dec_high.configuration.steps == 28

    # Assert all three tiers produce mutually distinct configurations
    assert dec_eco.configuration.effective_resolution != dec_std.configuration.effective_resolution
    assert dec_std.configuration.effective_resolution != dec_high.configuration.effective_resolution
    assert dec_eco.configuration.steps != dec_std.configuration.steps
    assert dec_std.configuration.steps != dec_high.configuration.steps
