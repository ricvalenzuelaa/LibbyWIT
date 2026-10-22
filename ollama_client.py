"""
Ollama API Client for WIT Library Chatbot.
Supports both local Ollama (http://localhost:11434) and hosted Ollama (https://ollama.com).
Uses Authorization: Bearer <key> when OLLAMA_API_KEY is set (production / hosted).
Handles connection errors, timeouts, authentication failures, rate limits,
and unavailable models gracefully without exposing internal tracebacks.
"""

import json
import re  # Added re module to strip markdown characters
import urllib.request
import urllib.error
from typing import List, Dict, Any, Optional

import config
from library_data import get_verified_knowledge_text, get_intent_answer

BASE_SYSTEM_PROMPT = (
    "You are the WIT Library Chatbot. You assist users exclusively with library-related questions, "
    "books, authors, reading recommendations, academic research, library resources, and library services.\n\n"
    "Answer clearly, accurately, politely, and concisely. Stay within the library domain. "
    "Do not answer unrelated general-knowledge questions. Questions about books, authors, academic research, "
    "and finding information through library resources are permitted.\n\n"
    "Do not invent library opening hours, addresses, book holdings, availability, borrowing limits, overdue fines, "
    "membership requirements, digital subscriptions, or policies. Use verified library data supplied by the application. "
    "If the required information is unavailable, explain that you cannot verify it.\n\n"
    "If a question is ambiguous, ask a clarifying question. "
    "If a question contains both library-related and unrelated requests, answer only the library-related portion.\n\n"
    "Do not claim to have searched the actual library catalog, checked a user's account, or verified book availability "
    "unless the application has genuinely performed that action.\n\n"
    "Respond in plain text only. Do NOT use markdown styling such as asterisks (*), underscores (_), bolding (**), or italics (*).\n\n"
    "Remain professional, helpful, and focused on library assistance."
)

def build_full_system_prompt() -> str:
    """Combine base system prompt with structured verified WIT library facts."""
    verified_text = get_verified_knowledge_text()
    return f"{BASE_SYSTEM_PROMPT}\n\n{verified_text}"

def _friendly_error(http_status: int, intent: str) -> Dict[str, Any]:
    """
    Convert an HTTP error from the Ollama hosted API into a user-friendly message.
    Never exposes internal details or stack traces.
    """
    verified_fallback = get_intent_answer(intent)

    if http_status == 401:
        msg = (
            "The library assistant is temporarily unable to connect to the AI service "
            "(authentication issue). Please try again later or contact WIT Library staff for help."
        )
    elif http_status == 403:
        msg = (
            "Access to the AI service has been denied. "
            "Please contact WIT Library staff for assistance."
        )
    elif http_status == 404:
        msg = (
            "The requested AI model is not available in the hosted service at this time. "
            "Please contact WIT Library staff for assistance."
        )
    elif http_status == 429:
        msg = (
            "The library assistant is receiving too many requests right now. "
            "Please wait a moment and try again."
        )
    elif http_status and http_status >= 500:
        msg = (
            "The AI service is temporarily unavailable. "
            "Please try again later or contact WIT Library staff for help."
        )
    else:
        msg = (
            "Sorry, the library assistant encountered a temporary issue processing your request. "
            "Please try again or contact WIT Library staff for help."
        )

    if verified_fallback:
        # Strip asterisks/underscores from fallback text as well
        clean_fallback = re.sub(r'[\*_]{1,2}', '', verified_fallback)
        return {
            "success": True,
            "answer": (
                f"I'm unable to reach the AI service right now, but here is verified "
                f"WIT Library information for your query:\n\n{clean_fallback}"
            ),
            "source": "fallback_data"
        }
    return {"success": False, "answer": msg, "source": "error"}


def query_ollama(
    user_message: str,
    intent: str = "general_library",
    is_mixed: bool = False,
    history: Optional[List[Dict[str, str]]] = None
) -> Dict[str, Any]:
    """
    Send chat request to Ollama /api/chat (local or hosted).
    Returns dict with { "success": bool, "answer": str, "source": "ollama" | "fallback_data" | "error" }

    Authentication:
      - If OLLAMA_API_KEY is set (production), adds Authorization: Bearer <key> header.
      - If not set (local dev), no auth header is sent.

    The model name is always read from config.OLLAMA_MODEL (env var); never hardcoded.
    """
    system_prompt = build_full_system_prompt()

    # Construct message list
    messages: List[Dict[str, str]] = [
        {"role": "system", "content": system_prompt}
    ]

    # Append recent conversation history if provided (max 6 turns)
    if history:
        for turn in history[-6:]:
            role = turn.get("role")
            content = turn.get("content", "").strip()
            if role in ("user", "assistant") and content:
                messages.append({"role": role, "content": content})

    # Prepare user query with mixed context if applicable
    query_content = user_message
    if is_mixed:
        query_content += (
            "\n\n[System Instruction: This question contains both library-related and unrelated requests. "
            "Per policy, answer ONLY the library-related portion, and politely decline the unrelated portion.]"
        )

    messages.append({"role": "user", "content": query_content})

    payload = {
        "model": config.OLLAMA_MODEL,   # read from env – never hardcoded
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": 0.3,
            "num_predict": 300
        }
    }

    req_data = json.dumps(payload).encode("utf-8")

    # Build headers – add Authorization only when API key is available (hosted/production)
    headers = {"Content-Type": "application/json"}
    if config.OLLAMA_API_KEY:
        headers["Authorization"] = f"Bearer {config.OLLAMA_API_KEY}"

    req = urllib.request.Request(
        config.OLLAMA_CHAT_ENDPOINT,
        data=req_data,
        headers=headers
    )

    try:
        with urllib.request.urlopen(req, timeout=config.OLLAMA_TIMEOUT) as response:
            if response.status != 200:
                return _friendly_error(response.status, intent)

            res_json = json.loads(response.read().decode("utf-8"))
            # Hosted Ollama API response shape: { "message": { "content": "..." } }
            content = res_json.get("message", {}).get("content", "").strip()

            if not content:
                raise RuntimeError("Empty response received from Ollama model.")

            # STRIP MARKDOWN ASTERISKS (*) AND UNDERSCORES (_) HERE
            clean_content = re.sub(r'[\*_]{1,2}', '', content)

            return {
                "success": True,
                "answer": clean_content,
                "source": "ollama"
            }

    except urllib.error.HTTPError as e:
        # Handles 401, 403, 404, 429, 5xx from hosted Ollama
        return _friendly_error(e.code, intent)

    except urllib.error.URLError:
        # Connection failure – Ollama not running locally, or network issue in production
        verified_fallback = get_intent_answer(intent)
        if verified_fallback:
            clean_fallback = re.sub(r'[\*_]{1,2}', '', verified_fallback)
            return {
                "success": True,
                "answer": (
                    "I'm unable to reach the AI service at this time. "
                    "Here is the verified WIT Library information for your query:\n\n"
                    f"{clean_fallback}"
                ),
                "source": "fallback_data"
            }
        return {
            "success": False,
            "answer": (
                "I am unable to reach the AI service at this time. "
                "Please try again later or visit the WIT Library circulation desk for assistance."
            ),
            "source": "error"
        }

    except Exception:
        verified_fallback = get_intent_answer(intent)
        if verified_fallback:
            clean_fallback = re.sub(r'[\*_]{1,2}', '', verified_fallback)
            return {
                "success": True,
                "answer": clean_fallback,
                "source": "fallback_data"
            }
        return {
            "success": False,
            "answer": (
                "Sorry, the library assistant encountered a temporary issue processing your request. "
                "Please try again or contact WIT Library staff for help."
            ),
            "source": "error"
        }