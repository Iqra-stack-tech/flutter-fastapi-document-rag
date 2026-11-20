import re
from pathlib import Path
from pypdf import PdfReader
from qdrant_client import QdrantClient, models
from .config import CHUNK_OVERLAP_SIZE, COLLECTION_NAME, MAX_CHUNK_SIZE, QDRANT_PATH
from .embedding_service import embedding_model

def normalize_pdf_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()

def split_text_with_overlap(
    text: str,
    max_chunk_size: int = MAX_CHUNK_SIZE,
    overlap_size: int = CHUNK_OVERLAP_SIZE,
) -> list[str]:
    text = normalize_pdf_text(text)
    if not text:
        return []

    words = text.split()
    chunks: list[str] = []
    current_words: list[str] = []

    for word in words:
        possible_words = current_words + [word]
        possible_text = " ".join(possible_words)

        if current_words and len(possible_text) > max_chunk_size:
            chunks.append(" ".join(current_words).strip())

            overlap_words: list[str] = []
            overlap_length = 0

            for old_word in reversed(current_words):
                added_length = len(old_word) + 1
                if overlap_length + added_length > overlap_size:
                    break
                overlap_words.insert(0, old_word)
                overlap_length += added_length

            current_words = overlap_words + [word]
        else:
            current_words.append(word)

    if current_words:
        chunks.append(" ".join(current_words).strip())

    return chunks

def create_pdf_chunks(pdf_path: Path) -> list[dict]:
    reader = PdfReader(str(pdf_path))
    chunks: list[dict] = []
    chunk_id = 1

    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        page_chunks = split_text_with_overlap(text)

        for chunk_text in page_chunks:
            chunks.append({
                "chunk_id": chunk_id,
                "source": pdf_path.name,
                "page": page_number,
                "text": chunk_text,
            })
            chunk_id += 1

    return chunks

def ingest_pdf(pdf_path: Path) -> dict:
    chunks = create_pdf_chunks(pdf_path)

    if not chunks:
        raise ValueError("No readable text was found inside the PDF.")

    chunk_texts = [chunk["text"] for chunk in chunks]
    embeddings = embedding_model.encode(chunk_texts)
    vector_size = int(embeddings.shape[1])

    client = QdrantClient(path=str(QDRANT_PATH))

    try:
        if client.collection_exists(COLLECTION_NAME):
            client.delete_collection(collection_name=COLLECTION_NAME)

        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(
                size=vector_size,
                distance=models.Distance.COSINE,
            ),
        )

        points = []
        for index, chunk in enumerate(chunks):
            points.append(
                models.PointStruct(
                    id=chunk["chunk_id"],
                    vector=embeddings[index].tolist(),
                    payload={
                        "chunk_id": chunk["chunk_id"],
                        "source": chunk["source"],
                        "page": chunk["page"],
                        "text": chunk["text"],
                    },
                )
            )

        client.upsert(
            collection_name=COLLECTION_NAME,
            points=points,
            wait=True,
        )
    finally:
        client.close()

    return {
        "filename": pdf_path.name,
        "chunks_created": len(chunks),
        "vector_dimension": vector_size,
        "collection": COLLECTION_NAME,
    }
