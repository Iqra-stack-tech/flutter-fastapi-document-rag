from sentence_transformers import SentenceTransformer
from .config import EMBEDDING_MODEL_NAME

embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
