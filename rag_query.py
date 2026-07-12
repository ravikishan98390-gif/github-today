r"""
rag_query.py
============
RAG Query Script

Connects to the local Chroma vector database built by rag_index.py,
embeds an input query using the same local SentenceTransformer model,
and retrieves the top-k most semantically similar chunks.

Usage:
    # Single query via argument:
    .venv\Scripts\python.exe rag_query.py --query "How do I prevent SQL injection?"

    # Interactive REPL mode (no --query given):
    .venv\Scripts\python.exe rag_query.py

    # Show more results, different DB path:
    .venv\Scripts\python.exe rag_query.py --query "CSRF tokens" --top-k 5 --db-dir ./chroma_db
"""

import argparse
import sys
import textwrap
from pathlib import Path

# Force UTF-8 output so box-drawing chars don't crash Windows cp1252 terminals
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction


# ─────────────────────────────────────────────────────────────────────────────
# Constants (must match rag_index.py)
# ─────────────────────────────────────────────────────────────────────────────

DEFAULT_DB_DIR      = r"C:\Users\Aayush\Desktop\Project\chroma_db"
COLLECTION_NAME     = "codelint_docs"
EMBED_MODEL         = "all-MiniLM-L6-v2"
DEFAULT_TOP_K       = 3
PREVIEW_WORDS       = 80          # words shown per chunk in summary mode
SEPARATOR       = "-" * 70


# ─────────────────────────────────────────────────────────────────────────────
# Pretty printing helpers
# ─────────────────────────────────────────────────────────────────────────────

def _truncate(text: str, max_words: int) -> str:
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]) + " …"


def print_result(rank: int, doc: str, meta: dict, distance: float) -> None:
    source      = meta.get("source", "unknown")
    chunk_idx   = meta.get("chunk_index", "?")
    total       = meta.get("total_chunks", "?")
    word_count  = meta.get("word_count", "?")
    # Cosine distance: 0 = identical, 1 = orthogonal  →  similarity = 1 - distance
    similarity  = max(0.0, 1.0 - distance)

    print(f"\n{'='*70}")
    print(f"  Match #{rank}  |  Similarity: {similarity:.1%}  |  Distance: {distance:.4f}")
    print(f"  Source : {source}  (chunk {chunk_idx + 1}/{total}, {word_count} words)")
    print(SEPARATOR)

    # Word-wrap the chunk preview at 80 chars
    preview = _truncate(doc, PREVIEW_WORDS)
    wrapped = textwrap.fill(preview, width=78, initial_indent="  ", subsequent_indent="  ")
    print(wrapped)


def print_full_result(rank: int, doc: str, meta: dict, distance: float) -> None:
    """Print the full chunk text (used with --full flag)."""
    source      = meta.get("source", "unknown")
    chunk_idx   = meta.get("chunk_index", "?")
    total       = meta.get("total_chunks", "?")
    word_count  = meta.get("word_count", "?")
    similarity  = max(0.0, 1.0 - distance)

    print(f"\n{'='*70}")
    print(f"  Match #{rank}  |  Similarity: {similarity:.1%}  |  Source: {source}")
    print(f"  Chunk {chunk_idx + 1}/{total}  ({word_count} words)")
    print(SEPARATOR)
    wrapped = textwrap.fill(doc, width=78, initial_indent="  ", subsequent_indent="  ")
    print(wrapped)


# ─────────────────────────────────────────────────────────────────────────────
# Query engine
# ─────────────────────────────────────────────────────────────────────────────

def load_collection(db_dir: str) -> chromadb.Collection:
    """Load the persisted Chroma collection (raises if it doesn't exist)."""
    if not Path(db_dir).exists():
        raise FileNotFoundError(
            f"Chroma DB not found at: {db_dir}\n"
            "Run the indexer first:\n"
            r"  .venv\Scripts\python.exe rag_index.py"
        )

    embed_fn   = SentenceTransformerEmbeddingFunction(model_name=EMBED_MODEL)
    client     = chromadb.PersistentClient(path=db_dir)
    collection = client.get_collection(
        name=COLLECTION_NAME,
        embedding_function=embed_fn,
    )
    return collection


def retrieve_context(query: str, top_k: int = 3, db_dir: str = DEFAULT_DB_DIR) -> list[dict]:
    """
    Programmatic interface to retrieve context for a given query.
    Returns a list of matches, each a dict with text, metadata, and similarity.
    """
    if not query.strip():
        return []
        
    collection = load_collection(db_dir)
    
    if collection.count() == 0:
        return []

    results = collection.query(
        query_texts=[query],
        n_results=min(top_k, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    docs      = results["documents"][0]
    metas     = results["metadatas"][0]
    distances = results["distances"][0]

    matches = []
    for doc, meta, dist in zip(docs, metas, distances):
        matches.append({
            "text": doc,
            "meta": meta,
            "similarity": max(0.0, 1.0 - dist),
            "distance": dist
        })
    
    return matches


def run_query(
    collection: chromadb.Collection,
    query: str,
    top_k: int,
    full: bool,
) -> None:
    """Embed the query and display top-k results."""
    if not query.strip():
        print("  (empty query — skipping)")
        return

    results = collection.query(
        query_texts=[query],
        n_results=min(top_k, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    docs      = results["documents"][0]
    metas     = results["metadatas"][0]
    distances = results["distances"][0]

    if not docs:
        print("  No results found.")
        return

    print(f"\nQuery : \"{query}\"")
    print(f"Top {len(docs)} match(es) from {collection.count()} indexed chunks:\n")

    printer = print_full_result if full else print_result
    for rank, (doc, meta, dist) in enumerate(zip(docs, metas, distances), start=1):
        printer(rank, doc, meta, dist)

    print(f"\n{'='*70}\n")


# ─────────────────────────────────────────────────────────────────────────────
# CLI / REPL
# ─────────────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="RAG Query Script")
    p.add_argument("--query",  "-q", default=None,
                   help="Query string (omit for interactive REPL mode)")
    p.add_argument("--db-dir", default=DEFAULT_DB_DIR,
                   help="Path to the persisted Chroma DB directory")
    p.add_argument("--top-k",  "-k", type=int, default=DEFAULT_TOP_K,
                   help=f"Number of results to return (default: {DEFAULT_TOP_K})")
    p.add_argument("--full",   action="store_true",
                   help="Print the full chunk text instead of a preview")
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()

    print("Loading Chroma collection…")
    try:
        collection = load_collection(args.db_dir)
    except (FileNotFoundError, Exception) as exc:
        print(f"Error: {exc}")
        raise SystemExit(1)

    total = collection.count()
    print(f"Collection '{COLLECTION_NAME}' loaded — {total} chunks indexed.\n")

    if args.query:
        # Single-shot mode
        run_query(collection, args.query, args.top_k, args.full)
    else:
        # Interactive REPL
        print("Interactive RAG Query  (type 'quit' or Ctrl-C to exit)")
        print(f"Returning top-{args.top_k} results per query.\n")
        try:
            while True:
                try:
                    query = input("Query> ").strip()
                except EOFError:
                    break
                if query.lower() in {"quit", "exit", "q"}:
                    break
                run_query(collection, query, args.top_k, args.full)
        except KeyboardInterrupt:
            pass
        print("\nGoodbye.")
