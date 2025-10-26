import os
from dotenv import load_dotenv

load_dotenv()

PORT = int(os.getenv("PORT", "8000"))
ENV = os.getenv("ENV", "dev")

NEXT_PUBLIC_API_BASE = os.getenv("NEXT_PUBLIC_API_BASE", "http://localhost:3000")
CORS_ORIGINS = [NEXT_PUBLIC_API_BASE]

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./data/uploads")
SQLITE_PATH = os.getenv("SQLITE_PATH", "./data/hinder.db")

CHROMA_DIR = os.getenv("CHROMA_DIR", "./chroma_data")
CHROMA_COLLECTION = os.getenv("CHROMA_COLLECTION", "profiles_vectors")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
EMBEDDINGS_PROVIDER = os.getenv("EMBEDDINGS_PROVIDER", "local")  # local|gemini
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-3-5-haiku-latest")

RERANK_PROVIDER = os.getenv("RERANK_PROVIDER", "none")
RERANK_ENDPOINT = os.getenv("RERANK_ENDPOINT", "")

EXPLAIN_PROVIDER = os.getenv("EXPLAIN_PROVIDER", "anthropic")
MAX_TOKENS_EXPLAIN = int(os.getenv("MAX_TOKENS_EXPLAIN", "120"))

BRIGHTDATA_ENABLED = os.getenv("BRIGHTDATA_ENABLED", "0") == "1"
BRIGHTDATA_API_KEY = os.getenv("BRIGHTDATA_API_KEY", "")

ALLOWED_PDF_MB = 10

# Auth
JWT_SECRET = os.getenv("JWT_SECRET", "dev_secret_change_me")
JWT_ALG = os.getenv("JWT_ALG", "HS256")
