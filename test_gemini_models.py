"""Quick script to test which Gemini models work on the current API key"""
import os, json, urllib.request, urllib.error, sys
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv(override=True)  # Force reload from .env

key = os.environ.get("GEMINI_API_KEY", "").strip()
print("=" * 50)
print(f"TESTING KEY: {key[:10]}...{key[-5:] if len(key)>15 else ''}")
print("=" * 50)

if not key or key == "your-github-token-here":
    print("❌ API key in .env is missing or invalid.")
    sys.exit(1)

models_to_test = [
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-1.5-pro"
]

working_model = None

for model in models_to_test:
    print(f"\nTesting model: {model}...")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    payload = json.dumps({
        "contents": [{"parts": [{"text": "Reply with 'OK'."}]}]
    }).encode()
    
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read().decode())
            print(f"   ✅ SUCCESS! {model} is working.")
            if not working_model:
                working_model = model
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"   ❌ FAILED (HTTP {e.code}):")
        try:
            err_json = json.loads(body)
            print(f"      {err_json['error']['message'][:200]}...")
        except:
            print(f"      {body[:200]}")
    except Exception as e:
        print(f"   ❌ ERROR: {e}")

print("\n" + "=" * 50)
if working_model:
    print(f"🎉 BEST WORKING MODEL: {working_model}")
else:
    print("⚠️ NO MODELS WORKED. The API key in .env has a real quota/billing limit issue.")
print("=" * 50)
