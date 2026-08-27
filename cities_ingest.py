import uuid
from pathlib import Path

from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import DATA_DIR, INDEX_DIR, EMBEDDING_MODEL, QDRANT_URL, QDRANT_COLLECTION, get_encoder

def generate_embedding(query: str):
    return get_encoder().embed_query(query)

def parse_markdown(content: str) -> tuple[str, str]:
    title_line, _, body = content.strip().partition("\n")
    title = title_line.lstrip("#").strip()

    lines = [line for line in body.splitlines() if not line.startswith("##")]
    body = "\n".join(lines).strip()

    return title, body

def generate_chunks(body: str) -> list[str]:
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    return text_splitter.split_text(body)

def extract_db_documents(dir_path: Path):
    documents = []

    for file_path in sorted(dir_path.glob("*.md")):
        content = file_path.read_text()
        title, body = parse_markdown(content)
        chunks = generate_chunks(body)

        for chunk in chunks:
            metadata = {
                "title": title,
                "source": str(file_path.relative_to(dir_path.parent.parent)),
                "embedding_model": EMBEDDING_MODEL,
            }
            documents.append(Document(page_content=chunk, metadata=metadata))

    return documents

def build_vector_store(documents: list[Document], index_dir: Path = INDEX_DIR) -> QdrantVectorStore:
    client = QdrantClient(url=QDRANT_URL)
    embeddings = get_encoder()
    vector_size = len(embeddings.embed_query("probe"))

    if client.collection_exists(QDRANT_COLLECTION):
        existing_size = client.get_collection(QDRANT_COLLECTION).config.params.vectors.size
        if existing_size != vector_size:
            raise ValueError(
                f"'{QDRANT_COLLECTION}' collection has vector size {existing_size}, but "
                f"{EMBEDDING_MODEL} produces {vector_size}-dim vectors. "
                "Delete the collection or use a differently named one."
            )
    else:
        client.create_collection(
            collection_name=QDRANT_COLLECTION,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )

    vector_store = QdrantVectorStore(client=client, collection_name=QDRANT_COLLECTION, embedding=embeddings)

    ids = [
        str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{doc.metadata['title']}::{doc.page_content}"))
        for doc in documents
    ]
    vector_store.add_documents(documents, ids=ids)
    return vector_store

def count_num_chunks():
    client = QdrantClient(url=QDRANT_URL)
    info = client.get_collection(QDRANT_COLLECTION)
    print(info.points_count)
    return info.points_count


def main():
    documents = extract_db_documents(DATA_DIR)
    build_vector_store(documents)
    num_chunks = count_num_chunks()
    print(f"Indexed {len(documents)} documents into Qdrant at {INDEX_DIR} (all {num_chunks})")


if __name__ == "__main__":
    main()