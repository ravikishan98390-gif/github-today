r"""
rag_query.py
============
RAG Query Script

Supports two retrieval modes:
1. A local markdown knowledge-base demo for live presentations and tests.
2. A Chroma-based retrieval flow when a persisted vector database is available.

Usage:
    .venv\Scripts\python.exe rag_query.py "How do I prevent SQL injection?"
    .venv\Scripts\python.exe rag_query.py --query "CSRF tokens" --top-k 5
"""

from __future__ import annotations

import argparse
import re
import sys
import textwrap
from pathlib import Path
from typing import Dict, List

# Force UTF-8 output so box-drawing chars don't crash Windows cp1252 terminals
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

try:
    import chromadb
    from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
except ImportError:  # pragma: no cover - environment-dependent
    chromadb = None
    SentenceTransformerEmbeddingFunction = None


DEFAULT_DB_DIR = r"C:\Users\Aayush\Desktop\Project\chroma_db"
COLLECTION_NAME = "codelint_docs"
EMBED_MODEL = "all-MiniLM-L6-v2"
DEFAULT_TOP_K = 3
PREVIEW_WORDS = 80
SEPARATOR = "-" * 70
ROOT = Path(__file__).resolve().parent
KB_PATH = ROOT / "knowledge_base" / "owasp_cheatsheets.md"


def _truncate(text: str, max_words: int) -> str:
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]) + " …"


def print_result(rank: int, doc: str, meta: dict, distance: float) -> None:
    source = meta.get("source", "unknown")
    chunk_idx = meta.get("chunk_index", "?")
    total = meta.get("total_chunks", "?")
    word_count = meta.get("word_count", "?")
    similarity = max(0.0, 1.0 - distance)

    print(f"\n{'=' * 70}")
    print(f"  Match #{rank}  |  Similarity: {similarity:.1%}  |  Distance: {distance:.4f}")
    print(f"  Source : {source}  (chunk {chunk_idx + 1}/{total}, {word_count} words)")
    print(SEPARATOR)

    preview = _truncate(doc, PREVIEW_WORDS)
    wrapped = textwrap.fill(preview, width=78, initial_indent="  ", subsequent_indent="  ")
    print(wrapped)


def print_full_result(rank: int, doc: str, meta: dict, distance: float) -> None:
    source = meta.get("source", "unknown")
    chunk_idx = meta.get("chunk_index", "?")
    total = meta.get("total_chunks", "?")
    word_count = meta.get("word_count", "?")
    similarity = max(0.0, 1.0 - distance)

    print(f"\n{'=' * 70}")
    print(f"  Match #{rank}  |  Similarity: {similarity:.1%}  |  Source: {source}")
    print(f"  Chunk {chunk_idx + 1}/{total}  ({word_count} words)")
    print(SEPARATOR)
    wrapped = textwrap.fill(doc, width=78, initial_indent="  ", subsequent_indent="  ")
    print(wrapped)


def load_collection(db_dir: str):
    if chromadb is None or SentenceTransformerEmbeddingFunction is None:
        raise ImportError("chromadb is not installed")
    if not Path(db_dir).exists():
        raise FileNotFoundError(
            f"Chroma DB not found at: {db_dir}\n"
            "Run the indexer first or use the local markdown knowledge base fallback."
        )

    embed_fn = SentenceTransformerEmbeddingFunction(model_name=EMBED_MODEL)
    client = chromadb.PersistentClient(path=db_dir)
    return client.get_collection(name=COLLECTION_NAME, embedding_function=embed_fn)


def retrieve_context(query: str, top_k: int = 3, db_dir: str = DEFAULT_DB_DIR) -> list[dict]:
    if not query.strip():
        return []

    try:
        collection = load_collection(db_dir)
    except (FileNotFoundError, ImportError):
        return query_knowledge_base(query, top_k=top_k)

    if collection.count() == 0:
        return []

    results = collection.query(
        query_texts=[query],
        n_results=min(top_k, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    docs = results["documents"][0]
    metas = results["metadatas"][0]
    distances = results["distances"][0]

    return [
        {
            "text": doc,
            "meta": meta,
            "similarity": max(0.0, 1.0 - dist),
            "distance": dist,
        }
        for doc, meta, dist in zip(docs, metas, distances)
    ]


def run_query(collection, query: str, top_k: int, full: bool) -> None:
    if not query.strip():
        print("  (empty query — skipping)")
        return

    results = collection.query(
        query_texts=[query],
        n_results=min(top_k, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    docs = results["documents"][0]
    metas = results["metadatas"][0]
    distances = results["distances"][0]

    if not docs:
        print("  No results found.")
        return

    print(f"\nQuery : \"{query}\"")
    print(f"Top {len(docs)} match(es) from {collection.count()} indexed chunks:\n")

    printer = print_full_result if full else print_result
    for rank, (doc, meta, dist) in enumerate(zip(docs, metas, distances), start=1):
        printer(rank, doc, meta, dist)

    print(f"\n{'=' * 70}\n")


def load_chunks(path: Path) -> List[Dict[str, str]]:
    text = path.read_text(encoding="utf-8")
    sections = re.split(r"\n## ", text)
    chunks: List[Dict[str, str]] = []
    for section in sections:
        if not section.strip():
            continue
        lines = [line.strip() for line in section.splitlines() if line.strip()]
        if not lines:
            continue
        title = lines[0].replace("#", "").strip()
        body = " ".join(lines[1:])
        if not body:
            continue
        source_match = re.search(r"Source:\s*(https?://\S+)", section)
        source = source_match.group(1) if source_match else "local-knowledge-base"
        chunks.append({"title": title, "content": body, "source": source})
    return chunks


def score_chunk(query: str, chunk: Dict[str, str]) -> float:
    query_terms = set(re.findall(r"[a-z0-9]+", query.lower()))
    if not query_terms:
        return 0.0
    text = f"{chunk['title']} {chunk['content']}".lower()
    matches = sum(1 for term in query_terms if term in text)
    return matches / max(len(query_terms), 1)


def query_knowledge_base(query: str, top_k: int = 3) -> List[Dict[str, str]]:
    chunks = load_chunks(KB_PATH)
    scored = []
    for chunk in chunks:
        score = score_chunk(query, chunk)
        if score > 0:
            scored.append({**chunk, "score": round(score, 3)})
    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored[:top_k]


def print_fallback_results(query: str, results: List[Dict[str, str]]) -> None:
    print(f"\nQuery: {query}\n")
    if not results:
        print("No matching chunks found.")
        return

    for idx, result in enumerate(results, 1):
        print(f"{idx}. {result['title']}")
        print(f"   Score: {result['score']}")
        print(f"   Source: {result['source']}")
        print(f"   Chunk: {result['content']}")
        print()


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="RAG Query Script")
    p.add_argument("query", nargs="?", default=None, help="Query string (omit for interactive REPL mode)")
    p.add_argument("--query", "-q", dest="query_flag", default=None, help="Query string")
    p.add_argument("--db-dir", default=DEFAULT_DB_DIR, help="Path to the persisted Chroma DB directory")
    p.add_argument("--top-k", "-k", type=int, default=DEFAULT_TOP_K, help=f"Number of results to return (default: {DEFAULT_TOP_K})")
    p.add_argument("--full", action="store_true", help="Print the full chunk text instead of a preview")
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    query = args.query_flag or args.query

    if query:
        try:
            collection = load_collection(args.db_dir)
        except (FileNotFoundError, ImportError):
            print("Using local markdown knowledge-base fallback.\n")
            results = query_knowledge_base(query, top_k=args.top_k)
            print_fallback_results(query, results)
        else:
            run_query(collection, query, args.top_k, args.full)
    else:
        print("Interactive RAG Query  (type 'quit' or Ctrl-C to exit)")
        print(f"Returning top-{args.top_k} results per query.\n")
        try:
            while True:
                try:
                    current_query = input("Query> ").strip()
                except EOFError:
                    break
                if current_query.lower() in {"quit", "exit", "q"}:
                    break
                try:
                    collection = load_collection(args.db_dir)
                except (FileNotFoundError, ImportError):
                    results = query_knowledge_base(current_query, top_k=args.top_k)
                    print_fallback_results(current_query, results)
                else:
                    run_query(collection, current_query, args.top_k, args.full)
        except KeyboardInterrupt:
            pass
        print("\nGoodbye.")
