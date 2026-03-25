"""Test Gemini with new model name"""
import os, json, urllib.request, urllib.error, sys
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv
load_dotenv()

key = os.environ.get("GEMINI_API_KEY")
url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={key}"

payload = json.dumps({
    "contents": [{"parts": [{"text": "Analyze this code for bugs and security issues. Return ONLY a JSON array.\n\ndef login(username, password):\n    query = \"SELECT * FROM users WHERE user='\" + username + \"' AND pass='\" + password + \"'\"\n    cursor.execute(query)\n    return True\n"}]}],
    "generationConfig": {"temperature": 0.1}
}).encode()

req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read().decode())
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        print("GEMINI RESPONSE:")
        print(text)
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f"[FAIL] HTTP {e.code}: {body[:500]}")
except Exception as e:
    print(f"[FAIL] {e}")
