"""
Cities to Qdrant ingestion — Prefect version.

Reimplements `ingestion/cities_ingest.py`'s logic as four tasks:
    1. check_qdrant_connection — fail fast if Qdrant isn't reachable
    2. extract_documents        — parse and chunk the markdown files
    3. ingest_chunks             — per chunk: skip if already in Qdrant,
                                    otherwise embed and add it
    4. report_results            — print added/total

Runs directly on the host via `uv run`, so unlike the Airflow container it
talks to `data/text/` and Qdrant at their normal host paths/ports — no volume
mounts or `host.docker.internal` needed.

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
# in the shell — so `QDRANT_URL=... uv run flows/cities_ingest_flow.py` still
# wins over whatever the .env file has.
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.environ.get("CITIES_DATA_DIR", REPO_ROOT / "data" / "text"))
QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.environ.get("QDRANT_API_KEY")  # required once QDRANT_URL is a Qdrant Cloud cluster
QDRANT_COLLECTION = os.environ.get("QDRANT_COLLECTION", "cities")
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")


def chunk_id(document: dict) -> str:
    """Deterministic id so re-running the flow doesn't create duplicate points."""
    metadata = document["metadata"]
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{metadata['title']}::{document['page_content']}"))


@task(retries=1, retry_delay_seconds=5)
def check_qdrant_connection() -> bool:
    """Ping Qdrant before doing any real work."""
    from qdrant_client import QdrantClient

    logger = get_run_logger()
    try:
        client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
        client.get_collections()
        logger.info(f"Connected to Qdrant at {QDRANT_URL}")
        return True
    except Exception as exc:
        logger.error(f"Could not connect to Qdrant at {QDRANT_URL}: {exc}")
        return False


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
def ingest_chunks(documents: list[dict]) -> tuple[int, int]:
    """For each chunk: skip if it's already in Qdrant, otherwise embed and add it."""
    from langchain_community.embeddings import FastEmbedEmbeddings
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, PointStruct, VectorParams

    logger = get_run_logger()
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    embeddings = FastEmbedEmbeddings(model_name=EMBEDDING_MODEL)  # loaded once, reused for every chunk

    if not client.collection_exists(QDRANT_COLLECTION):
        vector_size = len(embeddings.embed_query("probe"))
        client.create_collection(
            collection_name=QDRANT_COLLECTION,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )

    added = 0
    for document in documents:
        point_id = chunk_id(document)
        already_added = bool(client.retrieve(collection_name=QDRANT_COLLECTION, ids=[point_id]))
        if already_added:
            continue

        vector = embeddings.embed_query(document["page_content"])
        client.upsert(
            collection_name=QDRANT_COLLECTION,
            points=[
                PointStruct(
                    id=point_id,
                    vector=vector,
                    payload={"page_content": document["page_content"], **document["metadata"]},
                )
            ],
        )
        added += 1

    logger.info(f"Added {added} new chunks, skipped {len(documents) - added} already present")
    return added, len(documents)


@task
def report_results(added: int, total: int) -> None:
    print(f"{added}/{total} chunks added")


@flow(name="cities-ingest")
def cities_ingest():
    connected = check_qdrant_connection()
    if not connected:
        raise RuntimeError(f"Aborting: could not connect to Qdrant at {QDRANT_URL}")

    documents = extract_documents()
    added, total = ingest_chunks(documents)
    report_results(added, total)


if __name__ == "__main__":
    cities_ingest()
