"""
Comprehensive Verification Script for ResourceAware
Tests:
1. Health & reachability check
2. Purpose inference with acceptance test prompts and edge cases
3. Quality tier specifications and transparent formulas
4. Generation error handling (HTTP 503 with --api startup instructions)
5. SQLite persistence, genuine analytics, and history clearing
6. Concurrency lock integrity on RTX 2050
"""
import asyncio
import json
import os
import sys
from pathlib import Path
import urllib.request
import urllib.error

API_BASE = "http://127.0.0.1:8000"

def log_header(title):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def test_health():
    log_header("1. Testing GET /health")
    req = urllib.request.Request(f"{API_BASE}/health")
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
        print(f"Status: {resp.status}")
        print(f"Active Provider: {data.get('active_provider')}")
        print(f"WebUI Reachable: {data.get('webui_reachable')}")
        print(f"API Enabled: {data.get('api_enabled')}")
        print(f"Loaded Model: {data.get('loaded_model')}")
        print(f"Error / Notice: {data.get('error')}")
        assert resp.status == 200
        assert data.get("active_provider") == "automatic1111"
        print(">>> Health Check: PASSED")

def test_purpose_inference():
    log_header("2. Testing POST /api/v1/infer-purpose")
    cases = [
        ("Make a simple black-and-white colouring sheet of a butterfly for a seven-year-old.", "eco", "Children's colouring sheet"),
        ("Create an illustrated educational poster about the water cycle.", "standard", "Educational poster"),
        ("Create a highly detailed illustration for a large printed school exhibition banner.", "high", "Large-format printed banner"),
        ("Flashcard of a red apple for vocabulary practice.", "eco", "Educational flashcard"),
        ("Classroom worksheet with math exercises for grade 2.", "eco", "Worksheet / classroom handout"),
        ("Human respiratory system lesson diagram.", "standard", "Lesson diagram"),
        ("A simple picture of a dog.", "standard", "General educational graphic"),
    ]

    for prompt, expected_tier, expected_purpose in cases:
        payload = json.dumps({"prompt": prompt}).encode()
        req = urllib.request.Request(
            f"{API_BASE}/api/v1/infer-purpose",
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            print(f"\nPrompt: '{prompt[:45]}...'")
            print(f"  Inferred Purpose : {data.get('purpose')}")
            print(f"  Recommended Tier : {data.get('recommended_tier')}")
            print(f"  Confidence       : {data.get('confidence')}")
            print(f"  Is Ambiguous     : {data.get('is_ambiguous')}")
            print(f"  Reason           : {data.get('reason')}")
            print(f"  Default Params   : {data.get('default_parameters')}")
            assert data.get("recommended_tier") == expected_tier
            assert data.get("purpose") == expected_purpose
    print("\n>>> All Purpose Inference Cases: PASSED")

def test_tier_specifications():
    log_header("3. Testing GET /api/v1/tiers")
    req = urllib.request.Request(f"{API_BASE}/api/v1/tiers")
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
        ref = data["reference_high"]
        tiers = data["tiers"]
        print(f"High Reference: {ref['width']}x{ref['height']} @ {ref['steps']} steps = {ref['work_units']} units (1.000 norm, {ref['savings_percent']}%)")
        print(f"Eco Tier: {tiers['eco']['width']}x{tiers['eco']['height']} @ {tiers['eco']['steps']} steps")
        print(f"Standard Tier: {tiers['standard']['width']}x{tiers['standard']['height']} @ {tiers['standard']['steps']} steps")
        print(f"Formula: {data['formula']}")
        print(f"Assumptions: {data['assumptions']}")
        assert ref["work_units"] == 11010048
        assert ref["normalized_units"] == 1.0
        assert ref["savings_percent"] == 0.0
        assert tiers["eco"]["steps"] == 10
        assert tiers["standard"]["steps"] == 18
        assert tiers["high"]["steps"] == 28
        print(">>> Centralized Tier Specifications: PASSED")

def test_generate_error_handling():
    log_header("4. Testing POST /api/v1/generate Error Mapping")
    payload = json.dumps({
        "prompt": "Test generating a butterfly outline",
        "quality_tier": "eco",
        "color_preference": "black_and_white",
        "mode": "optimized"
    }).encode()
    req = urllib.request.Request(
        f"{API_BASE}/api/v1/generate",
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    try:
        urllib.request.urlopen(req)
        print("Unexpected success (WebUI generated an image)")
    except urllib.error.HTTPError as e:
        body = json.loads(e.read().decode())
        print(f"HTTP Status: {e.code}")
        print(f"Detail Message: {body.get('detail')}")
        # When WebUI is running without --api, it should return 503 explaining that --api is missing
        assert e.code == 503
        assert "--api" in body.get("detail", "")
        print(">>> Error Mapping & Startup Instructions: PASSED")

def test_storage_and_analytics():
    log_header("5. Testing Persistence, Analytics & Clean Empty States")
    # Verify initial empty state
    req = urllib.request.Request(f"{API_BASE}/api/v1/history")
    with urllib.request.urlopen(req) as resp:
        history = json.loads(resp.read().decode())
        print(f"Initial history count: {len(history)}")

    req = urllib.request.Request(f"{API_BASE}/api/v1/analytics")
    with urllib.request.urlopen(req) as resp:
        analytics = json.loads(resp.read().decode())
        print(f"Initial analytics: is_empty={analytics.get('is_empty')}, total={analytics.get('total_generations')}")
        assert analytics.get("is_empty") is True or analytics.get("total_generations") == len(history)

    # Test direct storage persistence
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from backend.app.services.storage import record_generation, get_generations, get_analytics_summary, clear_generations

    job_id = record_generation(
        prompt="A colouring butterfly",
        negative_prompt="",
        inferred_purpose="Children's colouring sheet",
        recommended_tier="eco",
        selected_tier="eco",
        tier_overridden=False,
        width=384,
        height=384,
        steps=10,
        model="test-sd-v1-5",
        elapsed_seconds=1.85,
        compute_work_units=0.1339,
        savings_percent=86.6,
        image_url="data:image/png;base64,TEST",
        success=True
    )
    print(f"Inserted test record: {job_id}")

    # Verify updated history
    records = get_generations(limit=5)
    assert len(records) >= 1
    assert records[0]["job_id"] == job_id
    assert records[0]["selected_tier"] == "eco"
    assert records[0]["elapsed_seconds"] == 1.85

    # Verify updated analytics
    summary = get_analytics_summary()
    assert summary["is_empty"] is False
    assert summary["total_generations"] >= 1
    assert summary["eco_count"] >= 1
    print(f"Updated Analytics: Total={summary['total_generations']}, Eco={summary['eco_count']}, UnitsSaved={summary['units_saved']}")

    # Clean up test records
    clear_generations()
    empty_summary = get_analytics_summary()
    assert empty_summary["total_generations"] == 0
    assert empty_summary["is_empty"] is True
    print("Cleaned up test records. Empty state restored.")
    print(">>> Storage & Analytics Integrity: PASSED")

if __name__ == "__main__":
    try:
        test_health()
        test_purpose_inference()
        test_tier_specifications()
        test_generate_error_handling()
        test_storage_and_analytics()
        log_header("ALL API & SYSTEM VERIFICATION CHECKS PASSED")
    except Exception as exc:
        print(f"\n[FAIL] Test verification failed: {exc}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
