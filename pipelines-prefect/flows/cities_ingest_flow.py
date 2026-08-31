"""
Cities to OpenSearch ingestion — Prefect version.

Reimplements `ingestion/cities_ingest.py`'s logic as five tasks:
    1. connect            — connect to OpenSearch, raise if unsuccessful
    2. extract_documents  — parse and chunk the markdown files
    3. ingest_chunks       — reuses the same connection: per chunk, skip if
                             already indexed, otherwise embed and add it
    4. report_results      — print added/total
    5. disconnect          — close the connection

Auth is AWS SigV4 via the task's/your own IAM credentials (boto3's default
credential chain) — no API key, matching agent/src/graph/nodes.py's approach.

Runs directly on the host via `uv run`, so unlike the Airflow container it
talks to `data/text/` at its normal host path — no volume mounts needed.

Usage:
    uv run flows/cities_ingest_flow.py
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path

from dotenv import load_dotenv
from prefect import flow, task
from prefect.logging import get_run_logger

# Loads pipelines-prefect/.env if present, without overriding vars already set
# in the shell.
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.environ.get("CITIES_DATA_DIR", REPO_ROOT / "data" / "text"))
AWS_REGION = os.environ.get("AWS_REGION", "eu-central-1")
OPENSEARCH_URL = os.environ.get("OPENSEARCH_URL", "https://localhost:9200")
OPENSEARCH_COLLECTION = os.environ.get("OPENSEARCH_COLLECTION", "cities")
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")


def chunk_id(document: dict) -> str:
    """Deterministic id so re-running the flow doesn't create duplicates."""
    metadata = document["metadata"]
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{metadata['title']}::{document['page_content']}"))


@task(retries=1, retry_delay_seconds=5)
def connect():
    """Connect to OpenSearch and return the client, raising if unsuccessful."""
    import boto3
    from opensearchpy import AWSV4SignerAuth, OpenSearch, RequestsHttpConnection

    logger = get_run_logger()
    credentials = boto3.Session().get_credentials()
    http_auth = AWSV4SignerAuth(credentials, AWS_REGION, "es")
    client = OpenSearch(
        hosts=[OPENSEARCH_URL],
        http_auth=http_auth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
    )

    if not client.ping():
        raise ConnectionError(f"Could not connect to OpenSearch at {OPENSEARCH_URL}")

    logger.info(f"Connected to OpenSearch at {OPENSEARCH_URL}")
    return client


@task(retries=1, retry_delay_seconds=5)
def extract_documents() -> list[dict]:
    """Parse and chunk every city markdown file in DATA_DIR."""
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    logger = get_run_logger()
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    files = sorted(DATA_DIR.glob("*.md"))
    documents = []

    for file_path in files:
        content = file_path.read_text()
        title_line, _, body = content.strip().partition("\n")
        title = title_line.lstrip("#").strip()
        body = "\n".join(
            line for line in body.splitlines() if not line.startswith("##")
        ).strip()

        for chunk in splitter.split_text(body):
            documents.append(
                {
                    "page_content": chunk,
                    "metadata": {
                        "title": title,
                        "source": file_path.name,
                        "embedding_model": EMBEDDING_MODEL,
                    },
                }
            )

    logger.info(f"Extracted {len(documents)} chunks from {len(files)} files")
    return documents


@task(retries=1, retry_delay_seconds=5)
def ingest_chunks(client, documents: list[dict]) -> tuple[int, int]:
    """Using the given (already-connected) client: for each chunk, skip if
    it's already indexed, otherwise embed and add it."""
    from langchain_community.embeddings import FastEmbedEmbeddings

    logger = get_run_logger()
    embeddings = FastEmbedEmbeddings(model_name=EMBEDDING_MODEL)  # loaded once, reused for every chunk

    if not client.indices.exists(index=OPENSEARCH_COLLECTION):
        vector_size = len(embeddings.embed_query("probe"))
        client.indices.create(
            index=OPENSEARCH_COLLECTION,
            body={
                "settings": {"index": {"knn": True}},
                "mappings": {
                    "properties": {
                        "vector": {"type": "knn_vector", "dimension": vector_size},
                        "page_content": {"type": "text"},
                        "title": {"type": "keyword"},
                        "source": {"type": "keyword"},
                        "embedding_model": {"type": "keyword"},
                    }
                },
            },
        )

    added = 0
    for document in documents:
        doc_id = chunk_id(document)
        already_added = client.exists(index=OPENSEARCH_COLLECTION, id=doc_id)
        if already_added:
            continue

        vector = embeddings.embed_query(document["page_content"])
        client.index(
            index=OPENSEARCH_COLLECTION,
            id=doc_id,
            body={
                "vector": vector,
                "page_content": document["page_content"],
                **document["metadata"],
            },
        )
        added += 1

    logger.info(f"Added {added} new chunks, skipped {len(documents) - added} already present")
    return added, len(documents)


@task
def report_results(added: int, total: int) -> None:
    print(f"{added}/{total} chunks added")


@task
def disconnect(client) -> None:
    client.close()


@flow(name="cities-ingest")
def cities_ingest():
    client = connect()

    documents = extract_documents()
    added, total = ingest_chunks(client, documents)
    report_results(added, total)

    disconnect(client)


if __name__ == "__main__":
    cities_ingest()
