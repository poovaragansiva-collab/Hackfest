import urllib.request
import json
import base64
import os
from PIL import Image
import io

print("1. Sending generation request to ResourceAware backend at http://127.0.0.1:8000/api/v1/generate...")
payload = {
    "prompt": "Simple black-and-white outline of a friendly turtle for a children's coloring worksheet, plain white background.",
    "quality_tier": "eco"
}
req = urllib.request.Request(
    "http://127.0.0.1:8000/api/v1/generate",
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)

with urllib.request.urlopen(req, timeout=120) as resp:
    status_code = resp.status
    data = json.loads(resp.read().decode("utf-8"))

print(f"Status Code: {status_code}")
assert status_code == 200, f"Expected 200, got {status_code}"
assert data["status"] == "success"
job_id = data["job_id"]
print(f"Generated Job ID: {job_id}")

# 2. Verify response metadata matches settings
config = data["applied_configuration"]
print(f"Applied Config: {config['effective_resolution']}, steps={config['steps']}, tier={config['quality_tier']}")
assert config["quality_tier"] == "eco"
assert config["effective_resolution"] == "384x384"
assert config["steps"] == 10

# 3. Verify real image data
img_obj = data["image"]
url = img_obj["url"]
print(f"Image URL format: {url[:40]}... (total length: {len(url)})")
assert url.startswith("data:image/png;base64,")
b64_data = url.split(",", 1)[1]
raw_bytes = base64.b64decode(b64_data)
pil_img = Image.open(io.BytesIO(raw_bytes))
print(f"Decoded Image format: {pil_img.format}, size: {pil_img.size}")
assert pil_img.format == "PNG"
assert pil_img.size == (384, 384)

# 4 & 5. Verify saved artifact and fetch via output endpoint
artifact_url = img_obj.get("artifact_url")
print(f"Artifact URL: {artifact_url}")
assert artifact_url is not None
fetch_url = f"http://127.0.0.1:8000{artifact_url}"
with urllib.request.urlopen(fetch_url) as art_resp:
    art_bytes = art_resp.read()
    print(f"Fetched artifact bytes: {len(art_bytes)}")
    assert art_resp.status == 200
    art_img = Image.open(io.BytesIO(art_bytes))
    assert art_img.size == (384, 384)

# 6. Verify SQLite record
history_req = urllib.request.Request("http://127.0.0.1:8000/api/v1/history")
with urllib.request.urlopen(history_req) as hist_resp:
    history = json.loads(hist_resp.read().decode("utf-8"))
    print(f"History records count: {len(history)}")
    latest = next((h for h in history if h["job_id"] == job_id), None)
    assert latest is not None, f"Job {job_id} not found in history"
    print(f"Found history record: {latest['job_id']}, prompt: {latest['prompt'][:50]}...")
    assert latest["selected_tier"] == "eco"
    assert latest["steps"] == 10
    assert latest["width"] == 384
    assert latest["height"] == 384

# 7. Verify Analytics update
analytics_req = urllib.request.Request("http://127.0.0.1:8000/api/v1/analytics")
with urllib.request.urlopen(analytics_req) as anal_resp:
    analytics = json.loads(anal_resp.read().decode("utf-8"))
    print(f"Analytics: total={analytics['total_generations']}, eco={analytics['eco_count']}, is_empty={analytics['is_empty']}")
    assert analytics["total_generations"] >= 1
    assert analytics["eco_count"] >= 1
    assert analytics["is_empty"] is False

print("\n--- ALL 10 SMOKE TEST VERIFICATION CHECKS PASSED SUCCESSFULLY! ---")
