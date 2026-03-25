import urllib.request
import json

snippet = """
def login(username, password):
    # connecting to db...
    query = "SELECT * FROM users WHERE user='" + username + "' AND pass='" + password + "'"
    cursor.execute(query)
    # logic...
    return True
"""

url = "http://localhost:8000/review"
payload = json.dumps({"code_snippet": snippet}).encode('utf-8')
headers = {'Content-Type': 'application/json'}
req = urllib.request.Request(url, data=payload, headers=headers)

print("Sending request to Gemini Code Review Agent...")
try:
    with urllib.request.urlopen(req, timeout=60) as response:
        print(f"Status Code: {response.getcode()}")
        body = response.read().decode('utf-8')
        print("Response Body:")
        try:
            print(json.dumps(json.loads(body), indent=2))
        except json.JSONDecodeError:
            print(body)
except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"Error connecting to server: {e}")
