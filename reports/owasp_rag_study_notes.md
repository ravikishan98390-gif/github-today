# OWASP/RAG Study Notes

## Goal
Demonstrate that knowledge-base retrieval can be grounded in curated security content rather than relying only on the model's general knowledge.

## Approach
- Store a small local knowledge base in `knowledge_base/owasp_cheatsheets.md`.
- Use a simple keyword-based retrieval script to pull the most relevant chunk for a user query.
- Surface the title, similarity score, source, and content to make the retrieval process explicit.

## Why This Is Useful
- It makes the demo traceable and explainable.
- It allows a mentor to see exactly which source text produced the answer.
- It is lightweight and easy to run locally without a separate vector database.

## Demo Queries
- `SQL injection`
- `hardcoded secrets`

## Notes
These chunks are drawn from OWASP cheat sheets, so the retrieval is grounded in real security guidance rather than generated from memory alone.
