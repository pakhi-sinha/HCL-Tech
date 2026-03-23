import os
import json
import re
import asyncio
import httpx
from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from typing import List

app = FastAPI(title="PS-01 Multi-LLM Code Review Assistant")

@app.get("/")
async def root():
    return {"status": "PS-01 Multi-LLM Code Review Assistant is ONLINE and waiting for webhooks!"}

# Environment Variables
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")

async def fetch_pr_diff(repo: str, pr_num: int) -> str:
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_num}"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3.diff"
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers)
        resp.raise_for_status()
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
Analyze this unified diff for Bugs, Security (OWASP Top 10), and Code Quality.
Return ONLY a valid JSON array of objects. Schema for each object:
{
    "type": "Bug",
    "file_path": "path/to/file",
    "line": <integer of the changed line>,
    "description": "Short explanation",
    "suggestion_code": "The repaired line(s) of code for replacement"
}
If there are no actionable issues, return [].
Diff:
"""

async def call_openai(diff: str) -> List[dict]:
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "gpt-4o",
        "messages": [{"role": "system", "content": "Return ONLY JSON."}, {"role": "user", "content": PROMPT + diff}],
        "temperature": 0.1
    }
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        return extract_json(resp.json()["choices"][0]["message"]["content"])

async def call_deepseek(diff: str) -> List[dict]:
    url = "https://api.deepseek.com/chat/completions"
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "deepseek-coder",
        "messages": [{"role": "system", "content": "Return ONLY JSON."}, {"role": "user", "content": PROMPT + diff}],
        "temperature": 0.1
    }
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(url, headers=headers, json=payload)
        if resp.status_code != 200: return []
        return extract_json(resp.json()["choices"][0]["message"]["content"])

async def call_gemini(diff: str) -> List[dict]:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": PROMPT + diff}]}],
        "generationConfig": {"temperature": 0.1}
    }
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(url, json=payload)
        if resp.status_code != 200: return []
        return extract_json(resp.json()["candidates"][0]["content"]["parts"][0]["text"])

def aggregate_findings(lists: List[List[dict]]) -> tuple[List[dict], int]:
    # Rule-based Aggregation Engine
    all_findings = []
    for l in lists: 
        all_findings.extend(l)
    
    unique_findings = {}
    overlap_count = 0
    
    for f in all_findings:
        key = f"{f.get('file_path')}_{f.get('line')}_{f.get('type')}"
        if key in unique_findings:
            overlap_count += 1
            unique_findings[key]["consensus"] += 1
        else:
            f["consensus"] = 1
            unique_findings[key] = f
            
    base_score = 75
    confidence = min(100, base_score + (overlap_count * 5)) if unique_findings else 100
    
    return list(unique_findings.values()), confidence

async def post_github_comments(repo: str, pr_num: int, commit_sha: str, findings: List[dict], score: int):
    # 1. Post General Summary Comment
    issue_url = f"https://api.github.com/repos/{repo}/issues/{pr_num}/comments"
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    summary_body = f"### 🤖 PS-01 Multi-LLM Review \n\n**Confidence Score:** {score}%\n\nI have aggregated results from Gemini, OpenAI, and DeepSeek. Found {len(findings)} actionable item(s)."
    
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
    diff = await fetch_pr_diff(repo, pr_num)
    if not diff: return
    
    # Concurrent Multi-LLM Processing
    results = await asyncio.gather(
        call_openai(diff),
        call_deepseek(diff),
        call_gemini(diff),
        return_exceptions=True
    )
    
    valid_results = [r for r in results if isinstance(r, list)]
    
    # Rule-Based Aggregation
    merged_findings, score = aggregate_findings(valid_results)
    
    # Actionable Posting
    if merged_findings:
        await post_github_comments(repo, pr_num, commit_sha, merged_findings, score)

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
