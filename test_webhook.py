import json
import urllib.request
import urllib.error

url = "http://127.0.0.1:8080/webhook"

headers = {
    "X-GitHub-Event": "pull_request",
    "Content-Type": "application/json"
}

# Mock GitHub PR Webhook Payload
payload = {
    "action": "opened",
    "number": 42,
    "pull_request": {
        "number": 42,
        "head": {
            "sha": "abcdef1234567890abcdef1234567890abcdef12"
        }
    },
    "repository": {
        "full_name": "octocat/Hello-World"
    }
}

print(f"Sending POST request to {url}...")
print("Headers:", headers)
print("Payload:", json.dumps(payload, indent=2))

data = json.dumps(payload).encode('utf-8')
req = urllib.request.Request(url, data=data, headers=headers)

try:
    with urllib.request.urlopen(req) as response:
        print(f"\nResponse Status Code: {response.status}")
        body = response.read().decode('utf-8')
        try:
            print(f"Response JSON: {json.dumps(json.loads(body), indent=2)}")
        except ValueError:
            print(f"Response Text: {body}")
except urllib.error.URLError as e:
    if hasattr(e, 'reason') and 'Connection refused' in str(e.reason):
        print("\n[ERROR] Connection refused. Is the FastAPI server running on port 8080?")
    else:
        print(f"\n[ERROR] {e}")
