import os
import json
import re
import asyncio
import httpx
from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import List
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="PS-01 Gemini Code Review Agent")

# CORS Middleware — allows frontend to call API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"status": "PS-01 Gemini Code Review Agent is ONLINE and waiting for webhooks!"}

# Serve frontend UI
@app.get("/ui")
async def serve_ui():
    return FileResponse(os.path.join(os.path.dirname(__file__), "frontend", "index.html"))

# Mount static files for CSS/JS
app.mount("/frontend", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "frontend")), name="frontend")

# Environment Variables
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

async def fetch_pr_diff(repo: str, pr_num: int) -> str:
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_num}"
    headers = {"Accept": "application/vnd.github.v3.diff"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
        
    async with httpx.AsyncClient(follow_redirects=True) as client:
        resp = await client.get(url, headers=headers)
        resp.raise_for_status()
        print(f"Fetched PR #{pr_num} diff perfectly ({len(resp.text)} chars). Dispatching to Gemini...")
        return resp.text

def extract_json(text: str) -> List[dict]:
    # Regex extract JSON array from potential markdown blocks outputted by LLMs
    match = re.search(r'\[.*\]', text.strip(), re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            pass
    return []

PROMPT = """
Analyze this code for Bugs, Security (OWASP Top 10), and Code Quality.
Return ONLY a valid JSON array of objects. Schema for each object:
{
    "type": "Bug" or "Security" or "Quality",
    "file_path": "path/to/file",
    "line": <integer of the problematic line>,
    "description": "Short explanation",
    "suggestion_code": "The repaired line(s) of code for replacement"
}
If there are no actionable issues, return [].
Code:
"""

DIFF_PROMPT = """
Analyze this unified diff for Bugs, Security (OWASP Top 10), and Code Quality.
Return ONLY a valid JSON array of objects. Schema for each object:
{
    "type": "Bug" or "Security" or "Quality",
    "file_path": "path/to/file",
    "line": <integer of the changed line>,
    "description": "Short explanation",
    "suggestion_code": "The repaired line(s) of code for replacement"
}
If there are no actionable issues, return [].
Diff:
"""

async def call_gemini(code: str, prompt: str = None) -> List[dict]:
    if not GEMINI_API_KEY:
        print("[ERROR] GEMINI_API_KEY is missing!")
        return []
    prompt = prompt or PROMPT
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": prompt + code}]}],
        "generationConfig": {"temperature": 0.1}
    }
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(url, json=payload)
        if resp.status_code != 200: 
            print(f"[ERROR] Gemini API returned {resp.status_code}: {resp.text}")
            return []
        
        try:
            return extract_json(resp.json()["candidates"][0]["content"]["parts"][0]["text"])
        except (KeyError, IndexError) as e:
            print(f"[ERROR] Failed to parse Gemini response: {e}")
            return []

# ==================== /review ENDPOINT (for frontend & test_client) ====================

class ReviewRequest(BaseModel):
    code_snippet: str

@app.post("/review")
async def review_code(req: ReviewRequest):
    """Direct code review: sends code to Gemini and returns structured results."""
    code = req.code_snippet

    findings = await call_gemini(code)
    
    # Calculate a simple mock score based on number of findings
    score = max(10, 100 - (len(findings) * 5)) if findings else 100

    # Separate by type for frontend
    bugs = [f"{f.get('description')}" for f in findings if f.get("type") in ("Bug", "Quality")]
    security = [f"{f.get('description')}" for f in findings if f.get("type") == "Security"]

    # Build refactored code block
    refactored_lines = [f.get("suggestion_code", "") for f in findings if f.get("suggestion_code")]
    refactored_code = "\n".join(refactored_lines) if refactored_lines else ""

    return {
        "confidence_score": score,
        "merged_bugs": bugs,
        "security_flaws": security,
        "refactored_code": refactored_code,
        "raw_findings": findings
    }

# ==================== /webhook ENDPOINT (for GitHub) ====================

async def post_github_comments(repo: str, pr_num: int, commit_sha: str, findings: List[dict]):
    # Fallback print if no write-access token explicitly provided
    if not GITHUB_TOKEN:
        print("\n" + "="*60)
        print(f"[No GITHUB_TOKEN] PS-01 Gemini Review Results for PR #{pr_num}:")
        for f in findings:
            print(f"- [{f.get('type')}] {f.get('file_path')}:{f.get('line')} -> {f.get('description')}")
            if f.get('suggestion_code'):
                print(f"  Suggested Fix:\n{f.get('suggestion_code')}")
        print("="*60 + "\n")
        return

    # 1. Post General Summary Comment
    issue_url = f"https://api.github.com/repos/{repo}/issues/{pr_num}/comments"
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    summary_body = f"### 🤖 PS-01 Gemini Code Review \n\nI have analyzed the code. Found {len(findings)} actionable item(s)."
    
    async with httpx.AsyncClient() as client:
        await client.post(issue_url, headers=headers, json={"body": summary_body})
        
        # 2. Post Inline Code Suggestion Review Comments
        review_url = f"https://api.github.com/repos/{repo}/pulls/{pr_num}/comments"
        for f in findings:
            if not f.get('file_path') or not f.get('line'): continue
            
            suggestion_body = f"**[{f['type']}]** {f['description']}\n\n```suggestion\n{f.get('suggestion_code', '')}\n```"
            payload = {
                "body": suggestion_body,
                "commit_id": commit_sha,
                "path": f["file_path"],
                "line": int(f["line"]),
                "side": "RIGHT"
            }
            try:
                # Fire and forget line-specific comments
                await client.post(review_url, headers=headers, json=payload)
            except Exception:
                # Fails gracefully if line number inferred by LLM falls outside of the PR diff bounds
                pass

async def process_pr(repo: str, pr_num: int, commit_sha: str):
    try:
        diff = await fetch_pr_diff(repo, pr_num)
        if not diff: return
    except Exception as e:
        print("\n" + "="*60)
        print(f"[CRITICAL ERROR] Failed to fetch PR code diff for {repo}#{pr_num}!")
        print(f"Error Details: {str(e)}")
        print("CAUSE: If this repository is PRIVATE, GitHub blocks access without a token and returns a 401/404.")
        print("FIX: Provide a valid GITHUB_TOKEN or ensure the repo is public.")
        print("="*60 + "\n")
        return
    
    # Single LLM Processing
    findings = await call_gemini(diff, DIFF_PROMPT)
    
    # Actionable Posting
    if findings:
        await post_github_comments(repo, pr_num, commit_sha, findings)

@app.post("/webhook")
async def github_webhook(request: Request, bg_tasks: BackgroundTasks):
    event = request.headers.get("X-GitHub-Event")
    if event != "pull_request":
        return {"status": "ignored", "reason": "not a pull_request event"}
        
    payload = await request.json()
    action = payload.get("action")
    
    if action in ["opened", "synchronize"]:
        repo_full_name = payload["repository"]["full_name"]
        pr_number = payload["pull_request"]["number"]
        commit_sha = payload["pull_request"]["head"]["sha"]
        
        # Async background task ensures GitHub receives < 3s HTTP 200 acknowledgment
        bg_tasks.add_task(process_pr, repo_full_name, pr_number, commit_sha)
        return {"status": "processing", "pr": pr_number}
        
    return {"status": "ignored", "reason": f"action {action} not monitored"}
