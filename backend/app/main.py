from pathlib import Path
import shutil
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from qdrant_client import QdrantClient

from .config import COLLECTION_NAME, DOCUMENTS_DIR, QDRANT_PATH
from .embedding_service import embedding_model
from .ingestion import ingest_pdf
from .rag_service import ask_document
from .schemas import AskRequest, AskResponse, StatusResponse, UploadResponse

app = FastAPI(
    title="Phase 5 Document RAG API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/status", response_model=StatusResponse)
def status():
    client = QdrantClient(path=str(QDRANT_PATH))
    try:
        if not client.collection_exists(COLLECTION_NAME):
            return {"indexed": False, "document": None}

        points, _ = client.scroll(
            collection_name=COLLECTION_NAME,
            limit=1,
            with_payload=True,
            with_vectors=False,
        )

        if not points:
            return {"indexed": False, "document": None}

        count = client.count(
            collection_name=COLLECTION_NAME,
            exact=True,
        ).count

        payload = points[0].payload or {}

        return {
            "indexed": True,
            "document": {
                "filename": payload.get("source", "Unknown.pdf"),
                "chunks_created": int(count),
                "vector_dimension": int(
                    embedding_model.get_sentence_embedding_dimension()
                ),
                "collection": COLLECTION_NAME,
            },
        }
    finally:
        client.close()

@app.post("/upload", response_model=UploadResponse)
def upload_pdf(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="File has no filename.")

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")

    safe_filename = Path(file.filename).name
    file_path = DOCUMENTS_DIR / safe_filename

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        with open(file_path, "rb") as pdf_file:
            header = pdf_file.read(5)

        if header != b"%PDF-":
            file_path.unlink(missing_ok=True)
            raise HTTPException(
                status_code=400,
                detail="The uploaded file is not a valid PDF.",
            )

        result = ingest_pdf(file_path)

        for old_pdf in DOCUMENTS_DIR.glob("*.pdf"):
            if old_pdf.resolve() != file_path.resolve():
                old_pdf.unlink(missing_ok=True)

        return {
            "message": "PDF uploaded and indexed successfully.",
            "document": result,
        }

    except HTTPException:
        raise
    except ValueError as error:
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=str(error))
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="PDF processing failed: " + str(error),
        )
    finally:
        file.file.close()

@app.post("/ask", response_model=AskResponse)
def ask_question(request: AskRequest):
    question = request.question.strip()

    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    history = [
        {"role": message.role, "content": message.content}
        for message in request.history
    ]

    try:
        result = ask_document(question=question, history=history)
        return {
            "question": question,
            "answer": result["answer"],
            "sources": result["sources"],
        }
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="Question answering failed: " + str(error),
        )
