import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
CHAT_MODEL = os.environ.get("CHAT_MODEL")
CHAT_BASE_URL = os.environ.get("CHAT_BASE_URL")
CHAT_API_KEY = os.environ.get("GROQ_API_KEY") or os.environ.get("OPENROUTER_API_KEY")
QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
QDRANT_COLLECTION = "cities"


def get_chat_model() -> ChatOpenAI:
    """Build the chat model client for the configured environment."""
    if os.environ.get("ENVIRONMENT") == "development":
        return ChatOpenAI(model=CHAT_MODEL, base_url=CHAT_BASE_URL, api_key="not-needed")
    elif os.environ.get("ENVIRONMENT") == "production":
        return ChatOpenAI(model=CHAT_MODEL, base_url=CHAT_BASE_URL, api_key=CHAT_API_KEY)
    raise ValueError("Invalid environment. Must be 'development' or 'production'.")
