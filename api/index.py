"""
Vercel Serverless Function – WIT Library Chatbot.

Vercel's @vercel/python runtime requires the entry point to be a class named
`handler` that subclasses http.server.BaseHTTPRequestHandler.

Routes:
  GET  /         → serves the chatbot HTML page
  POST /chat     → accepts { message, history } JSON, returns AI response JSON
  GET  /api/*    → also serves the HTML page (catch-all for Vercel routing)

Environment variables (set in Vercel dashboard → Project → Settings → Environment Variables):
  OLLAMA_BASE_URL   – https://ollama.com
  OLLAMA_MODEL      – model name (e.g. llama3:latest)
  OLLAMA_API_KEY    – secret API key; never committed to source control
  OLLAMA_TIMEOUT    – request timeout in seconds (optional, default 60)
"""

import json
import sys
import os
import time
from http.server import BaseHTTPRequestHandler

# Make the project root importable when Vercel runs this from the api/ directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config  # noqa: E402
from topic_validator import validate_user_query, EXACT_REFUSAL_MESSAGE  # noqa: E402
from ollama_client import query_ollama  # noqa: E402
from library_data import get_intent_answer  # noqa: E402


# ---------------------------------------------------------------------------
# classify() – mirrors app.py logic; kept in sync
# ---------------------------------------------------------------------------
def classify(message: str, history=None, use_llm: bool = True) -> dict:
    cleaned_message = (message or "").strip()
    if not cleaned_message:
        return {
            "intent": "ambiguous",
            "confidence": 0.1,
            "answer": "Please enter a question or topic related to the WIT Library, books, research, or library services."
        }

    val = validate_user_query(cleaned_message)
    status   = val["status"]
    intent   = val["intent"]
    is_mixed = val.get("is_mixed", False)

    if status == "REJECTED":
        return {"intent": "fallback", "confidence": 0.20, "answer": EXACT_REFUSAL_MESSAGE}

    if status == "AMBIGUOUS":
        return {"intent": "ambiguous", "confidence": 0.50, "answer": val["answer"]}

    if status == "CONVERSATIONAL":
        return {"intent": intent, "confidence": 0.99, "answer": val["answer"]}

    if use_llm:
        res = query_ollama(
            user_message=cleaned_message,
            intent=intent,
            is_mixed=is_mixed,
            history=history
        )
        return {
            "intent": intent,
            "confidence": 0.95 if res.get("success") else 0.70,
            "answer": res.get("answer")
        }

    verified_ans = get_intent_answer(intent) or "Verified WIT Library information is available at the circulation desk."
    return {"intent": intent, "confidence": 1.0, "answer": verified_ans}


# ---------------------------------------------------------------------------
# HTML page – import from app.py to avoid duplication
# ---------------------------------------------------------------------------
def _get_page() -> str:
    try:
        from app import PAGE
        return PAGE
    except Exception:
        return "<h1>WIT Library Chatbot</h1><p>Frontend unavailable.</p>"


# ---------------------------------------------------------------------------
# Vercel entry point – MUST be a class named `handler` extending
# BaseHTTPRequestHandler so @vercel/python can find it.
# ---------------------------------------------------------------------------
class handler(BaseHTTPRequestHandler):
    """
    Vercel Python serverless handler.
    Vercel looks for a top-level class named `handler` subclassing
    BaseHTTPRequestHandler, or a callable named `app` / `application`.
    Using the BaseHTTPRequestHandler class keeps this project dependency-free
    (no Flask or FastAPI needed).
    """

    def log_message(self, format, *args):
        # Suppress default access log lines in Vercel output
        pass

    # ── GET → serve the chatbot HTML page ────────────────────────────────────
    def do_GET(self):
        page = _get_page()
        body = page.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    # ── POST /chat → process a chat message ──────────────────────────────────
    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(content_length).decode("utf-8") if content_length else ""

        message = ""
        history = []
        try:
            data    = json.loads(raw_body) if raw_body else {}
            message = data.get("message", "")
            history = data.get("history", [])
        except Exception:
            pass

        start_time = time.perf_counter()
        result     = classify(message, history=history, use_llm=True)
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 3)
        result["server_ms"] = elapsed_ms

        response_bytes = json.dumps(result, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response_bytes)))
        self.end_headers()
        self.wfile.write(response_bytes)
