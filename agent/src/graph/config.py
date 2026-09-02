import os

from langchain_aws import ChatBedrock

EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
CHAT_MODEL = os.environ.get("CHAT_MODEL")
AWS_REGION = os.environ.get("AWS_REGION", "eu-central-1")

OPENSEARCH_URL = os.environ.get("OPENSEARCH_URL")
OPENSEARCH_COLLECTION = "cities"

MCP_HOTELS_URL = os.environ.get("MCP_HOTELS_URL", "http://localhost:8080/mcp")

# Reflection loop cap (generate -> reflect -> revise), per lane — bounds the
# retry loop so a stubborn low-quality answer can't loop forever; the best
# attempt so far is accepted once this is hit.
MAX_REVISIONS = 2


def get_chat_model() -> ChatBedrock:
    """Build the Bedrock chat model client. Auth is via the task's own IAM
    role (SigV4) — no API key, unlike the Groq/OpenRouter setup this replaced."""
    return ChatBedrock(model_id=CHAT_MODEL, region_name=AWS_REGION)
