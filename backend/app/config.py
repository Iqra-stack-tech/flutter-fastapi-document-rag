from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
STORAGE_DIR = BACKEND_DIR / "storage"
DOCUMENTS_DIR = STORAGE_DIR / "documents"
QDRANT_PATH = STORAGE_DIR / "qdrant_data"

DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
QDRANT_PATH.mkdir(parents=True, exist_ok=True)

COLLECTION_NAME = "pdf_chunks"
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
GROQ_MODEL = "openai/gpt-oss-20b"

MAX_CHUNK_SIZE = 700
CHUNK_OVERLAP_SIZE = 120

SEMANTIC_CANDIDATES = 12
TOP_K = 5
MIN_SEMANTIC_SCORE = 0.20
KEYWORD_MATCH_THRESHOLD = 0.50
SEMANTIC_WEIGHT = 0.72
KEYWORD_WEIGHT = 0.28
