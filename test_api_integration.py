"""
Integration tests for the hosted Ollama API client and library-topic filter.
These tests do NOT require a live Ollama connection – they mock the HTTP layer
so the test suite remains reliable in CI and offline environments.

Run with:
    python test_api_integration.py
"""

import sys
import json
import unittest
import urllib.error
from io import BytesIO
from unittest.mock import patch, MagicMock

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_response(body: dict, status: int = 200):
    """Return a mock HTTP response that urllib.request.urlopen would return."""
    encoded = json.dumps(body).encode("utf-8")
    mock_resp = MagicMock()
    mock_resp.status = status
    mock_resp.read.return_value = encoded
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


# ---------------------------------------------------------------------------
# 1. Config: OLLAMA_API_KEY and OLLAMA_MODEL read from environment
# ---------------------------------------------------------------------------
class TestConfig(unittest.TestCase):

    def test_api_key_read_from_env(self):
        import os
        import importlib
        os.environ["OLLAMA_API_KEY"] = "test-key-123"
        import config
        importlib.reload(config)
        self.assertEqual(config.OLLAMA_API_KEY, "test-key-123")

    def test_model_read_from_env(self):
        import os
        import importlib
        os.environ["OLLAMA_MODEL"] = "mymodel:latest"
        import config
        importlib.reload(config)
        self.assertEqual(config.OLLAMA_MODEL, "mymodel:latest")

    def test_chat_endpoint_uses_base_url(self):
        import os
        import importlib
        os.environ["OLLAMA_BASE_URL"] = "https://ollama.com"
        import config
        importlib.reload(config)
        self.assertEqual(config.OLLAMA_CHAT_ENDPOINT, "https://ollama.com/api/chat")


# ---------------------------------------------------------------------------
# 2. ollama_client: Authorization header is sent when key is present
# ---------------------------------------------------------------------------
class TestOllamaClientAuth(unittest.TestCase):

    def _call_with_mock(self, mock_resp):
        import config
        config.OLLAMA_API_KEY = "secret-key"
        config.OLLAMA_CHAT_ENDPOINT = "https://ollama.com/api/chat"
        config.OLLAMA_MODEL = "llama3:latest"
        config.OLLAMA_TIMEOUT = 30

        captured = {}

        def fake_urlopen(req, timeout=None):
            captured["headers"] = dict(req.headers)
            return mock_resp

        import ollama_client
        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            ollama_client.query_ollama("Who wrote Hamlet?", intent="book_information")

        return captured

    def test_authorization_header_present(self):
        mock_resp = _make_response({"message": {"content": "Shakespeare"}})
        captured = self._call_with_mock(mock_resp)
        auth = captured["headers"].get("Authorization") or captured["headers"].get("authorization")
        self.assertIsNotNone(auth, "Authorization header should be present when OLLAMA_API_KEY is set")
        self.assertTrue(auth.startswith("Bearer "), "Authorization should start with 'Bearer '")

    def test_no_auth_header_when_key_missing(self):
        import config
        config.OLLAMA_API_KEY = None
        config.OLLAMA_CHAT_ENDPOINT = "https://ollama.com/api/chat"
        config.OLLAMA_MODEL = "llama3:latest"
        config.OLLAMA_TIMEOUT = 30

        captured = {}

        def fake_urlopen(req, timeout=None):
            captured["headers"] = dict(req.headers)
            return _make_response({"message": {"content": "Shakespeare"}})

        import ollama_client
        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            ollama_client.query_ollama("Who wrote Hamlet?", intent="book_information")

        auth = captured["headers"].get("Authorization") or captured["headers"].get("authorization")
        self.assertIsNone(auth, "No Authorization header when OLLAMA_API_KEY is not set")


# ---------------------------------------------------------------------------
# 3. ollama_client: reads answer from message.content
# ---------------------------------------------------------------------------
class TestOllamaClientResponseParsing(unittest.TestCase):

    def _query(self, body):
        import config
        config.OLLAMA_API_KEY = None
        config.OLLAMA_CHAT_ENDPOINT = "http://localhost:11434/api/chat"
        config.OLLAMA_MODEL = "llama3:latest"
        config.OLLAMA_TIMEOUT = 30

        import ollama_client
        with patch("urllib.request.urlopen", return_value=_make_response(body)):
            return ollama_client.query_ollama("test question", intent="general_library")

    def test_reads_message_content(self):
        result = self._query({"message": {"content": "Here is the answer."}})
        self.assertTrue(result["success"])
        self.assertEqual(result["answer"], "Here is the answer.")
        self.assertEqual(result["source"], "ollama")

    def test_empty_content_handled(self):
        result = self._query({"message": {"content": ""}})
        # Should not crash; returns fallback or error
        self.assertIn("answer", result)
        self.assertNotIn("Traceback", result["answer"])


# ---------------------------------------------------------------------------
# 4. ollama_client: HTTP error codes produce friendly messages
# ---------------------------------------------------------------------------
class TestOllamaClientErrorHandling(unittest.TestCase):

    def _query_with_http_error(self, code: int):
        import config
        config.OLLAMA_API_KEY = "key"
        config.OLLAMA_CHAT_ENDPOINT = "https://ollama.com/api/chat"
        config.OLLAMA_MODEL = "llama3:latest"
        config.OLLAMA_TIMEOUT = 30

        import ollama_client
        err = urllib.error.HTTPError(url="", code=code, msg="", hdrs=None, fp=None)
        with patch("urllib.request.urlopen", side_effect=err):
            return ollama_client.query_ollama("What are the library hours?", intent="library_hours_location")

    def test_401_friendly_message(self):
        result = self._query_with_http_error(401)
        self.assertNotIn("Traceback", result["answer"])
        self.assertFalse(result.get("success") and result["source"] == "ollama")

    def test_429_friendly_message(self):
        result = self._query_with_http_error(429)
        self.assertNotIn("Traceback", result["answer"])

    def test_500_friendly_message(self):
        result = self._query_with_http_error(500)
        self.assertNotIn("Traceback", result["answer"])

    def test_404_friendly_message(self):
        result = self._query_with_http_error(404)
        self.assertNotIn("Traceback", result["answer"])

    def test_url_error_friendly_message(self):
        import config
        config.OLLAMA_API_KEY = None
        config.OLLAMA_CHAT_ENDPOINT = "http://localhost:59999/api/chat"
        config.OLLAMA_MODEL = "llama3:latest"
        config.OLLAMA_TIMEOUT = 5

        import ollama_client
        err = urllib.error.URLError(reason="Connection refused")
        with patch("urllib.request.urlopen", side_effect=err):
            result = ollama_client.query_ollama("What are the library hours?", intent="library_hours_location")
        self.assertNotIn("Traceback", result["answer"])


# ---------------------------------------------------------------------------
# 5. Topic filter: the four previously-rejected valid library questions
# ---------------------------------------------------------------------------
class TestTopicFilter(unittest.TestCase):

    def _validate(self, q):
        from topic_validator import validate_user_query
        return validate_user_query(q)

    def test_library_location_accepted(self):
        v = self._validate("Where is the WIT Library located?")
        self.assertEqual(v["status"], "ACCEPTED",
            f"Expected ACCEPTED for location question, got {v['status']}")

    def test_computers_for_students_accepted(self):
        v = self._validate("Does the library have computers for students?")
        self.assertEqual(v["status"], "ACCEPTED",
            f"Expected ACCEPTED for computers question, got {v['status']}")

    def test_academic_journals_accepted(self):
        v = self._validate("How can I find academic journals online?")
        self.assertEqual(v["status"], "ACCEPTED",
            f"Expected ACCEPTED for academic journals question, got {v['status']}")

    def test_digital_resources_from_home_accepted(self):
        v = self._validate("Can I access the library's digital resources from home?")
        self.assertEqual(v["status"], "ACCEPTED",
            f"Expected ACCEPTED for digital resources question, got {v['status']}")


# ---------------------------------------------------------------------------
# 6. Topic filter: genuinely unrelated questions are still rejected
# ---------------------------------------------------------------------------
class TestTopicFilterRefusal(unittest.TestCase):

    def _should_reject(self, q):
        from topic_validator import validate_user_query
        v = validate_user_query(q)
        self.assertEqual(v["status"], "REJECTED",
            f"Expected REJECTED for '{q}', got {v['status']}")

    def test_rejects_food_order(self):    self._should_reject("Can you order food for me?")
    def test_rejects_weather(self):       self._should_reject("What is the weather today?")
    def test_rejects_coding(self):        self._should_reject("Write a python script to reverse a string")
    def test_rejects_math(self):          self._should_reject("Solve 2x + 10 = 20")
    def test_rejects_sports(self):        self._should_reject("Who won the Super Bowl?")
    def test_rejects_cooking(self):       self._should_reject("How to bake a chocolate cake")


# ---------------------------------------------------------------------------
# 7. API key is never exposed in responses
# ---------------------------------------------------------------------------
class TestApiKeyNotExposed(unittest.TestCase):

    def test_error_message_does_not_contain_api_key(self):
        import config
        config.OLLAMA_API_KEY = "super-secret-key-9999"
        config.OLLAMA_CHAT_ENDPOINT = "https://ollama.com/api/chat"
        config.OLLAMA_MODEL = "llama3:latest"
        config.OLLAMA_TIMEOUT = 5

        import ollama_client
        err = urllib.error.HTTPError(url="", code=401, msg="Unauthorized", hdrs=None, fp=None)
        with patch("urllib.request.urlopen", side_effect=err):
            result = ollama_client.query_ollama("What are the library hours?", intent="library_hours_location")

        self.assertNotIn("super-secret-key-9999", result["answer"],
            "API key must never appear in user-facing responses")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 60)
    print("WIT LIBRARY CHATBOT – API INTEGRATION TESTS")
    print("=" * 60)
    loader  = unittest.TestLoader()
    suite   = loader.loadTestsFromModule(sys.modules[__name__])
    runner  = unittest.TextTestRunner(verbosity=2)
    result  = runner.run(suite)
    print("=" * 60)
    print(f"TEST RESULTS: {result.testsRun - len(result.failures) - len(result.errors)} PASSED, "
          f"{len(result.failures) + len(result.errors)} FAILED (Total: {result.testsRun})")
    print("=" * 60)
    sys.exit(0 if result.wasSuccessful() else 1)
