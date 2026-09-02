import os

from langchain_aws import ChatBedrock

EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
CHAT_MODEL = os.environ.get("CHAT_MODEL")
AWS_REGION = os.environ.get("AWS_REGION", "eu-central-1")

OPENSEARCH_URL = os.environ.get("OPENSEARCH_URL")
OPENSEARCH_COLLECTION = "cities"


def get_chat_model() -> ChatBedrock:
    """Build the Bedrock chat model client. Auth is via the task's own IAM
    role (SigV4) — no API key, unlike the Groq/OpenRouter setup this replaced."""
    return ChatBedrock(model_id=CHAT_MODEL, region_name=AWS_REGION)
