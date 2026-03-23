import os
import re
import subprocess
import urllib.request
import urllib.error
import json

def get_repo():
    try:
        out = subprocess.check_output(['git', 'remote', '-v'], text=True)
        # Match git@github.com:owner/repo.git or https://github.com/owner/repo.git
        match = re.search(r'github\.com[:/]([^/]+)/([^/\s\.]+)', out)
        if match:
            return f"{match.group(1)}/{match.group(2)}"
        return None
    except Exception:
        return None

token = os.environ.get("GITHUB_TOKEN")
if not token:
    print("[ERROR] GITHUB_TOKEN not found in environment.")
    exit(1)

repo = get_repo()
if not repo:
    print("[ERROR] Could not detect GitHub repository from git remote -v. Are you in a git repository with an origin set?")
    exit(1)

# Ensure webhook is added
api_url = f"https://api.github.com/repos/{repo}/hooks"
headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/vnd.github.v3+json",
    "Content-Type": "application/json"
}

payload = {
    "name": "web",
    "active": True,
    "events": ["pull_request"],
    "config": {
        "url": "https://young-friends-judge.loca.lt/webhook",
        "content_type": "json",
        "insecure_ssl": "0"
    }
}

req = urllib.request.Request(api_url, data=json.dumps(payload).encode('utf-8'), headers=headers)

try:
    with urllib.request.urlopen(req) as response:
        print(f"[SUCCESS] Webhook securely added to {repo} (Status {response.status})")
except urllib.error.URLError as e:
    body = e.read().decode('utf-8') if hasattr(e, 'read') else str(e)
    # 422 usually means the hook already exists
    if "already exists" in body.lower():
        print(f"[SUCCESS] Webhook is already configured on {repo}!")
    else:
        print(f"[ERROR] Failed to add webhook: {e}")
        print(body)
