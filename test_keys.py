"""Quick diagnostic: test each LLM API key individually."""
import os, json, urllib.request, urllib.error, sys
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv
load_dotenv()

# 1. Test Gemini
print("=" * 50)
print("1. TESTING GEMINI API KEY...")
key = os.environ.get("GEMINI_API_KEY", "")
if not key:
    print("   [MISSING] GEMINI_API_KEY is empty in .env")
else:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent?key={key}"
    payload = json.dumps({"contents": [{"parts": [{"text": "Say hello"}]}]}).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            print(f"   [OK] Gemini works! (status {r.status})")
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"   [FAIL] Gemini HTTP {e.code}: {body[:300]}")
    except Exception as e:
        print(f"   [FAIL] Gemini error: {e}")

# 2. Test OpenAI
print("\n2. TESTING OPENAI API KEY...")
key = os.environ.get("OPENAI_API_KEY", "").strip()
if not key:
    print("   [MISSING] OPENAI_API_KEY is empty in .env")
else:
    url = "https://api.openai.com/v1/chat/completions"
    payload = json.dumps({"model": "gpt-4o", "messages": [{"role": "user", "content": "Say hello"}], "max_tokens": 5}).encode()
    req = urllib.request.Request(url, data=payload, headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            print(f"   [OK] OpenAI works! (status {r.status})")
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"   [FAIL] OpenAI HTTP {e.code}: {body[:300]}")
    except Exception as e:
        print(f"   [FAIL] OpenAI error: {e}")

# 3. Test DeepSeek
print("\n3. TESTING DEEPSEEK API KEY...")
key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
if not key:
    print("   [MISSING] DEEPSEEK_API_KEY is empty in .env")
else:
    url = "https://api.deepseek.com/chat/completions"
    payload = json.dumps({"model": "deepseek-coder", "messages": [{"role": "user", "content": "Say hello"}], "max_tokens": 5}).encode()
    req = urllib.request.Request(url, data=payload, headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            print(f"   [OK] DeepSeek works! (status {r.status})")
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"   [FAIL] DeepSeek HTTP {e.code}: {body[:300]}")
    except Exception as e:
        print(f"   [FAIL] DeepSeek error: {e}")

print("\n" + "=" * 50)
