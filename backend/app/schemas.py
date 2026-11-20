from typing import Literal
from pydantic import BaseModel, Field

class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str

class AskRequest(BaseModel):
    question: str
    history: list[ChatMessage] = Field(default_factory=list)

class SourceItem(BaseModel):
    file: str
    page: int
    chunk_id: int
    score: float
    semantic_score: float
    keyword_score: float

class AskResponse(BaseModel):
    question: str
    answer: str
    sources: list[SourceItem]

class DocumentInfo(BaseModel):
    filename: str
    chunks_created: int
    vector_dimension: int
    collection: str

class UploadResponse(BaseModel):
    message: str
    document: DocumentInfo

class StatusResponse(BaseModel):
    indexed: bool
    document: DocumentInfo | None = None
