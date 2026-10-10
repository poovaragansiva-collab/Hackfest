import urllib.request
import json

BASE_URL = "http://127.0.0.1:8000"

def test_endpoint(name, url, method="GET", payload=None):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Content-Type": "application/json"} if payload is not None else {}
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            return resp.status, body
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8"))

print("=== 1. HEALTH CHECK ===")
status, res = test_endpoint("Health", f"{BASE_URL}/health")
print(f"Health Status: {status}, Active Provider: {res.get('active_provider')}, WebUI Reachable: {res.get('webui_reachable')}")

print("\n=== 2. PURPOSE INFERENCE TESTS ===")
prompts = [
    ("Small thumbnail icon", "A small thumbnail icon for a personal project."),
    ("Favicon", "A simple favicon of a blue bird"),
    ("Profile avatar", "A profile avatar for a student portal"),
    ("Small badge", "A small badge icon for student reading club"),
    ("Conflicting banner with icons", "A high-resolution printed promotional banner with detailed typography and icons."),
    ("Acceptance Test 1 (Colouring Sheet)", "Make a simple black-and-white colouring sheet of a butterfly for a seven-year-old."),
    ("Acceptance Test 2 (Educational Poster)", "Create an illustrated educational poster about the water cycle."),
    ("Acceptance Test 3 (Exhibition Banner)", "Create a highly detailed illustration for a large printed school exhibition banner."),
]

for label, p in prompts:
    status, res = test_endpoint("Infer", f"{BASE_URL}/api/v1/infer-purpose", method="POST", payload={"prompt": p})
    print(f"[{label}]")
    print(f"  Prompt: {p}")
    print(f"  Inferred: {res.get('purpose')} | Tier: {res.get('recommended_tier')} | Ambiguous: {res.get('is_ambiguous')}")
    print(f"  Reason: {res.get('reason')}")

print("\n=== 3. EMPTY PROMPT VALIDATION ===")
status, res = test_endpoint("Empty prompt infer", f"{BASE_URL}/api/v1/infer-purpose", method="POST", payload={"prompt": ""})
print(f"Infer with empty prompt: Status {status} (Expected 422)")

status, res = test_endpoint("Empty prompt generate", f"{BASE_URL}/api/v1/generate", method="POST", payload={"prompt": ""})
print(f"Generate with empty prompt: Status {status} (Expected 422)")

print("\n=== 4. DATABASE & ANALYTICS INTEGRITY ===")
status, hist = test_endpoint("History", f"{BASE_URL}/api/v1/history")
gen_list = hist if isinstance(hist, list) else hist.get('generations', [])
print(f"History Status: {status}, Count: {len(gen_list)}")
for g in gen_list:
    print(f"  - ID: {g.get('generation_id')}, Tier: {g.get('selected_tier')}, Purpose: {g.get('inferred_purpose')}, Work Units: {g.get('resource_metrics', {}).get('work_units')}")

status, analytics = test_endpoint("Analytics", f"{BASE_URL}/api/v1/analytics")
print(f"Analytics Status: {status}")
print(f"  Total Generations: {analytics.get('total_generations')}")
print(f"  Cumulative Cost Savings: {analytics.get('cumulative_cost_savings_usd')}")
print(f"  Average Savings %: {analytics.get('average_savings_percent')}%")
