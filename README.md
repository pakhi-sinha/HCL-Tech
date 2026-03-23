# Multi-LLM Code Review Aggregator

An intelligent, autonomous backend service built with **Python**, **FastAPI**, and **LangChain** that aggregates code reviews from multiple state-of-the-art LLMs. 

## 🚀 How It Works
The aggregator exposes a `/review` API endpoint. Once a code snippet is submitted:
1. **Parallel Dispatch**: The snippet is simultaneously dispatched to 3 asynchronous AI Workers: **ChatGPT**, **DeepSeek**, and **Grok**.
2. **Aggregation Engine**: The worker reviews are grouped and sent to the Main Judge (**Google Gemini**).
3. **Consensus & Resolution**: Gemini evaluates the reviews based on Completeness, Overlap, and Clarity, merging them into a single, cohesive JSON payload containing bugs, security flaws, refactored code, and a confidence score.
4. **Self-Healing Fallback**: If standard workers hit rate limits or quota errors, the aggregator catches the resulting parsing failure and triggers a graceful fallback response to prevent a catastrophic 500 Server Error.

## 📁 Project Structure
- `main.py`: The Main FastAPI application containing the `/review` endpoint, parallel dispatch logic, and Gemini Aggregator Engine.
- `requirements.txt`: Project dependencies needed to run the backend.
- `test_client.py`: A simple standalone test script to trigger the aggregator API and print the formatted JSON response.
- `README.md`: Project documentation.

## 🛠️ Installation
1. Ensure you have Python installed.
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## 💻 Running the Server
Run the FastAPI application locally using `uvicorn`:
```bash
python -m uvicorn main:app --reload --port 8000
```
*(The server will start at `http://127.0.0.1:8000`)*

## 🧪 Testing the Aggregator
Run the included `test_client.py` script to send a sample review payload to the server:
```bash
python test_client.py
```
