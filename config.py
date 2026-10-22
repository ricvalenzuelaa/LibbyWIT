import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent

def load_dotenv(dotenv_path=None):
    """Load simple key=value pairs from a .env file without external dependencies."""
    if dotenv_path is None:
        dotenv_path = ROOT_DIR / ".env"
    
    if os.path.exists(dotenv_path):
        try:
            with open(dotenv_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        key, val = line.split("=", 1)
                        key = key.strip()
                        val = val.strip().strip("\"'")
                        # Do not overwrite already set system environment variables
                        if key not in os.environ:
                            os.environ[key] = val
        except Exception:
            pass

# Load environment variables from .env if present (local development only)
load_dotenv()

# ---------------------------------------------------------------------------
# Ollama API Configuration
# ---------------------------------------------------------------------------
# In production (Vercel), set these as Environment Variables in the dashboard.
# In local development, set them in your .env file.
#
#   OLLAMA_BASE_URL   – base URL for the Ollama API
#                       local:      http://localhost:11434
#                       production: https://ollama.com
#   OLLAMA_MODEL      – model name to use (e.g. llama3:latest)
#   OLLAMA_API_KEY    – API key for hosted Ollama (production only; never commit)
#   OLLAMA_TIMEOUT    – request timeout in seconds (default 60)
# ---------------------------------------------------------------------------

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", os.getenv("OLLAMA_HOST", "http://localhost:11434")).rstrip("/")
OLLAMA_MODEL    = os.getenv("OLLAMA_MODEL", "llama3:latest")
OLLAMA_API_KEY  = os.getenv("OLLAMA_API_KEY")          # None when not set (local dev)
OLLAMA_CHAT_ENDPOINT = f"{OLLAMA_BASE_URL}/api/chat"
OLLAMA_TIMEOUT  = int(os.getenv("OLLAMA_TIMEOUT", "60"))

# Server Configuration (local dev only – Vercel ignores these)
SERVER_HOST = os.getenv("SERVER_HOST", "127.0.0.1")
SERVER_PORT = int(os.getenv("SERVER_PORT", "8000"))
