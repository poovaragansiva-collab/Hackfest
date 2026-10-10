"""Tests for Transparent Resource Estimation and Compute-Work Calculations.

Tests compliance with Hackathon Constraint 1:
- High reference units equal 1.0 (512x768 at 28 steps = 11,010,048 units)
- High estimated savings equal 0.0%
- Eco and Standard units and savings are correctly computed
- Estimates are algorithmic proxies (width × height × steps), not fabricated energy/kWh
- Monotonic elapsed time is recorded truthfully without simulated numbers
"""

import pytest
from backend.app.services.resource_estimator import (
    HIGH_REFERENCE_WORK_UNITS,
    calculate_compute_work_units,
    calculate_normalized_resource_units,
    calculate_compute_savings_percent,
    estimate_transparent_resources,
)


def test_high_reference_baseline():
    high_work = calculate_compute_work_units(512, 768, 28)
    assert high_work == 11010048
    assert high_work == HIGH_REFERENCE_WORK_UNITS

    high_norm = calculate_normalized_resource_units(512, 768, 28)
    assert high_norm == 1.0

    high_savings = calculate_compute_savings_percent(512, 768, 28)
    assert high_savings == 0.0


def test_eco_tier_compute_work_and_savings():
    eco_work = calculate_compute_work_units(384, 384, 10)
    assert eco_work == 1474560

    eco_norm = calculate_normalized_resource_units(384, 384, 10)
    # 1,474,560 / 11,010,048 = 0.133928...
    assert round(eco_norm, 4) == 0.1339

    eco_savings = calculate_compute_savings_percent(384, 384, 10)
    # 100 * (1 - 0.133928...) = 86.607... -> 86.6%
    assert eco_savings == 86.6


def test_standard_tier_compute_work_and_savings():
    std_work = calculate_compute_work_units(512, 512, 18)
    assert std_work == 4718592

    std_norm = calculate_normalized_resource_units(512, 512, 18)
    # 4,718,592 / 11,010,048 = 0.42857...
    assert round(std_norm, 4) == 0.4286

    std_savings = calculate_compute_savings_percent(512, 512, 18)
    # 100 * (1 - 0.42857...) = 57.14... -> 57.1%
    assert std_savings == 57.1


def test_estimate_transparent_resources_dictionary():
    estimate = estimate_transparent_resources("eco", measured_seconds=1.84)
    assert estimate["tier"] == "eco"
    assert estimate["width"] == 384
    assert estimate["height"] == 384
    assert estimate["steps"] == 10
    assert estimate["compute_work_units"] == 1474560
    assert estimate["estimated_resource_units"] == 0.1339
    assert estimate["savings_percent"] == 86.6
    assert estimate["elapsed_seconds"] == 1.84
    assert estimate["timing_type"] == "measured"
    assert "work_units = 384 × 384 × 10" in estimate["formula"]
    assert "proxy for GPU load" in estimate["assumptions"]
    assert "Joules or kWh" in estimate["assumptions"]


def test_no_fake_elapsed_time():
    estimate_unmeasured = estimate_transparent_resources("standard")
    assert estimate_unmeasured["elapsed_seconds"] is None
    assert estimate_unmeasured["timing_type"] == "unmeasured"
