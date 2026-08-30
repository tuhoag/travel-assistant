import os

# from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from langchain_openai.chat_models.base import BaseChatOpenAI
from langchain_openrouter import ChatOpenRouter
from langchain_groq import ChatGroq

# load_dotenv()

EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL")
CHAT_MODEL = os.environ.get("CHAT_MODEL")
QDRANT_URL = os.environ.get("QDRANT_URL")
QDRANT_API_KEY = os.environ.get("QDRANT_API_KEY")
QDRANT_COLLECTION = "cities"

# Each provider owns its own base_url and where its API key comes from, so
# selecting one is explicit — no more guessing which key was meant if
# multiple happened to be set.
PROVIDERS = {
    "docker": {
        # local Docker Model Runner / vLLM — CHAT_BASE_URL is injected by
        # docker-compose's `models: chat: endpoint_var: CHAT_BASE_URL`.
        "base_url": os.environ.get("CHAT_BASE_URL"),
        "api_key": "not-needed",
    },
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "api_key": os.environ.get("GROQ_API_KEY"),
    },
}



def get_chat_model(provider: str | None = None) -> BaseChatOpenAI:
    """Build the chat model client for the given provider (defaults to $PROVIDER)."""
    provider = provider or os.environ.get("CHAT_MODEL_PROVIDER")
    if provider not in PROVIDERS:
        raise ValueError(f"Invalid provider '{provider}'. Must be one of: {', '.join(PROVIDERS)}")

    config = PROVIDERS[provider]
    print(f"Using chat model provider '{provider}' with model '{CHAT_MODEL}'")
    match provider:
        case "docker":
            return ChatOpenAI(model=CHAT_MODEL, base_url=config["base_url"], api_key=config["api_key"])
        case "groq":
            config = PROVIDERS["groq"]
            return ChatGroq(model=CHAT_MODEL, api_key=config["api_key"])

        case _:
            raise RuntimeError(f"Unsupported chat model from provider '{provider}'")
