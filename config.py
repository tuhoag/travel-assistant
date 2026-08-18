import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain_openai import ChatOpenAI

load_dotenv()

DATA_DIR = Path(__file__).parent / "data" / "text"
INDEX_DIR = Path(os.environ.get("QDRANT_INDEX_DIR") or Path(__file__).parent / "db" / "qdrant_storage")
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL")
CHAT_MODEL = os.environ.get("CHAT_MODEL")
CHAT_BASE_URL = os.environ.get("CHAT_BASE_URL")
CHAT_API_KEY = os.environ.get("GROQ_API_KEY") or os.environ.get("OPENROUTER_API_KEY")

QDRANT_URL = os.environ.get("QDRANT_URL")
QDRANT_COLLECTION = "cities"


def get_encoder() -> FastEmbedEmbeddings:
    return FastEmbedEmbeddings(model_name=EMBEDDING_MODEL)

def get_chat_model() -> ChatOpenAI:
    if os.environ.get("ENVIRONMENT") == "dev":
        return ChatOpenAI(
            model=CHAT_MODEL,
            base_url=CHAT_BASE_URL,
            api_key="not-needed"
        )
    elif os.environ.get("ENVIRONMENT") == "prod":
        return ChatOpenAI(
            model=CHAT_MODEL,
            base_url=CHAT_BASE_URL,
            api_key=CHAT_API_KEY,
        )
    else:
        raise ValueError("Invalid environment. Must be 'dev' or 'prod'.")
