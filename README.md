# Gemini Code Review Agent

An intelligent, autonomous backend service built with **Python** and **FastAPI** that provides automated code reviews using the lightning-fast **Google Gemini 2.5 Flash** model.

## 🚀 How It Works
The service exposes a `/review` API endpoint and a gorgeous frontend UI. Once a code snippet is submitted:
1. **Direct Dispatch**: The snippet is dispatched natively to Google Gemini 2.5 Flash with a strictly engineered prompt.
2. **Analysis**: Gemini evaluates the code based on Bugs, Code Quality, and Security (OWASP Top 10) vulnerabilities.
3. **Structured Response**: The backend forces a clean JSON payload parsing out detected bugs, security flaws, refactored code suggestions, and outputs it to the UI.
4. **Resiliency**: If rate limits or quota errors hit, it gracefully handles failure without crashing the service.

## 📁 Project Structure
- `main.py`: The Main FastAPI application containing the `/review` endpoint and UI routing.
- `frontend/`: Contains the futuristic glassmorphism `index.html`, CSS, and JS.
- `requirements.txt`: Project dependencies needed to run the backend.
- `test_client.py`: A simple standalone CLI test script to trigger the aggregator API without a browser.
- `.env`: Holds the `GEMINI_API_KEY` (must be provided natively).

## 🛠️ Installation
1. Ensure you have Python installed.
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the root directory and add your free Google AI Studio key:
   ```env
   GEMINI_API_KEY=your_api_key_here
   ```

## 💻 Running the Server
Run the FastAPI application locally using `uvicorn`:
```bash
python -m uvicorn main:app --port 8000
```
Open **[http://localhost:8000/ui](http://localhost:8000/ui)** in your browser to access the Code Review UI.

## 🧪 Testing the API
Run the included `test_client.py` script to send a sample payload directly via terminal:
```bash
python test_client.py
```
