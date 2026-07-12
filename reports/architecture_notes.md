# Architecture Notes

## Components
- Frontend: React + Vite UI served on port 5173.
- Backend: FastAPI application served by Uvicorn on port 8000.
- Validation Layer: Python and Java validators in `validators/`.
- Knowledge Retrieval: Local markdown knowledge base plus `rag_query.py` for retrieval demos.

## Data Flow
1. The frontend sends code submissions to the FastAPI `/submit-code` endpoint.
2. The backend routes the request to the language-specific validator.
3. The validator returns structured validation results to the frontend.
4. The RAG demo script loads markdown content from the local knowledge base and returns relevant chunks for demo queries.

## Demo Readiness
The following files are ready for live presentation:
- `demo_samples/valid_python.py`
- `demo_samples/broken_python.py`
- `demo_samples/unsupported_file.txt`
