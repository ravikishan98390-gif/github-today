# Milestone 1 Completion Report

## Project Summary
The Code Submission Module and the lightweight RAG knowledge-base retrieval demo are both running locally and verified end to end.

## What Was Built
- FastAPI backend with a `/submit-code` endpoint for validating Python and Java submissions.
- React frontend for submitting code through the browser.
- Demo sample files stored in `demo_samples/` for live presentation.
- Local knowledge base retrieval script for OWASP-inspired demo queries.

## Verification Evidence
- Backend dry-run: `python five_scenarios.py` -> 5/5 scenarios passed.
- RAG dry-run: `python rag_query.py "SQL injection"` and `python rag_query.py "hardcoded secrets"` returned relevant chunks.
- Automated RAG tests: `python -m unittest test_rag_query.py` -> 2 tests passed.

## Demo Flow
1. Open the frontend at `http://127.0.0.1:5173`.
2. Upload the valid Python sample and confirm validation passes.
3. Upload the broken Python sample and confirm syntax errors are reported.
4. Upload the unsupported `.txt` sample and confirm it is rejected cleanly.
5. Run the RAG query script for `SQL injection` and `hardcoded secrets` to show grounded retrieval.
