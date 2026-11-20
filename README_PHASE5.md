# Phase 5 - Final Document RAG Project

## Final architecture

- Flutter Web UI
- FastAPI backend
- PDF page extraction with pypdf
- Page-aware overlapping chunks
- SentenceTransformer embeddings
- Qdrant local vector store
- Hybrid retrieval:
  - semantic vector similarity
  - exact keyword matching
- Groq/OpenAI-compatible LLM
- Source/page/chunk citations
- Conversational follow-ups
- Active-document status restored after Flutter refresh

## Backend setup

From:

```powershell
cd D:\FastApi\phase5_rag
```

Copy your current `.env` to:

```text
backend\.env
```

It must contain:

```text
GROQ_API_KEY=your_real_key
```

Install:

```powershell
& D:\FastApi\myenv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
```

Start backend from the Phase 5 project root:

```powershell
uvicorn backend.app.main:app
```

Endpoints:

- http://127.0.0.1:8000/health
- http://127.0.0.1:8000/status
- http://127.0.0.1:8000/docs

Avoid `--reload` while using local Qdrant on Windows during this learning project.

## Flutter setup

Keep the Flutter project's generated platform directories.
Replace only `flutter_app\lib\` with the packaged version.

Then:

```powershell
cd D:\FastApi\phase5_rag\flutter_app
flutter pub add http file_picker
flutter pub get
flutter run -d chrome
```

The current file_picker v13 API used by this code is:

- `FilePicker.pickFile()`
- `PlatformFile.readAsBytes()`

## Test plan

1. Start FastAPI.
2. Start Flutter in Chrome.
3. Upload `sample.pdf`.
4. Ask:
   - What is PaperLab?
   - Who would use PaperLab?
   - What problem does PaperLab solve?
   - Which project compares a circuit drawing with physical wiring?
   - What is AgentGuard designed to prevent?
5. Ask a follow-up:
   - Why is that useful?
6. Ask something absent:
   - What is the population of Japan?
   Expected: insufficient-information response.

## Phase 5 move-on checklist

- PDF upload works.
- Non-PDF upload is rejected.
- PDF is chunked into multiple page-aware chunks.
- Qdrant stores embeddings + payload.
- Exact named queries work through hybrid retrieval.
- Semantic paraphrases work.
- Follow-up questions use recent history.
- Answers stay document-grounded.
- Sources include file, page, and chunk.
- Irrelevant questions return the refusal response.
- Flutter UI works in Chrome.
- Project structure, README, and `.gitignore` are clean.
