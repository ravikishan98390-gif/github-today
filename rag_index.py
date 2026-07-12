r"""
rag_index.py
============
RAG Indexing Pipeline

Reads all .txt and .md files from the assets directory, splits them into
overlapping word-based chunks (300-500 words), generates sentence embeddings
via a local SentenceTransformer model, and stores everything in a persistent
local Chroma vector database.

Usage:
    .venv\Scripts\python.exe rag_index.py [--assets-dir PATH] [--db-dir PATH]
                                          [--chunk-size INT] [--overlap INT]
                                          [--reset]
"""

import argparse
import os
import re
import sys
import time
from pathlib import Path

# Force UTF-8 output on Windows so Unicode chars don't crash cp1252 terminals
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction


# ─────────────────────────────────────────────────────────────────────────────
# Constants / defaults
# ─────────────────────────────────────────────────────────────────────────────

DEFAULT_ASSETS_DIR = r"C:\Users\Aayush\Desktop\Project\assets"
DEFAULT_DB_DIR     = r"C:\Users\Aayush\Desktop\Project\chroma_db"
DEFAULT_CHUNK_SIZE = 400   # target words per chunk
DEFAULT_OVERLAP    = 60    # words of overlap between consecutive chunks
COLLECTION_NAME    = "codelint_docs"
EMBED_MODEL        = "all-MiniLM-L6-v2"   # fast, 384-dim, runs fully offline


# ─────────────────────────────────────────────────────────────────────────────
# Text chunker
# ─────────────────────────────────────────────────────────────────────────────

def tokenize_words(text: str) -> list[str]:
    """Split text into whitespace-separated tokens (words)."""
    return text.split()


def chunk_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP,
) -> list[str]:
    """
    Sliding-window word chunker.

    Produces chunks of approximately `chunk_size` words with `overlap` words
    carried over from the previous chunk.  Any markdown headings that fall
    mid-chunk are preserved as-is because we work at word level.

    Returns a list of chunk strings.
    """
    words = tokenize_words(text)
    if not words:
        return []

    chunks: list[str] = []
    step = max(1, chunk_size - overlap)
    start = 0

    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        if end == len(words):
            break
        start += step

    return chunks


# ─────────────────────────────────────────────────────────────────────────────
# File reader
# ─────────────────────────────────────────────────────────────────────────────

def read_documents(assets_dir: str) -> list[dict]:
    """
    Walk `assets_dir` and return a list of document dicts:
      { "filename": str, "path": str, "text": str }
    Includes .txt and .md files only.
    """
    docs = []
    for path in sorted(Path(assets_dir).iterdir()):
        if path.suffix.lower() in {".txt", ".md"} and path.is_file():
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
                docs.append({
                    "filename": path.name,
                    "path": str(path),
                    "text": text,
                })
                print(f"  [read]  {path.name}  ({len(text):,} chars)")
            except Exception as exc:
                print(f"  [skip]  {path.name}  — {exc}")
    return docs


# ─────────────────────────────────────────────────────────────────────────────
# Main indexing routine
# ─────────────────────────────────────────────────────────────────────────────

def build_index(
    assets_dir: str,
    db_dir: str,
    chunk_size: int,
    overlap: int,
    reset: bool,
) -> None:
    t0 = time.perf_counter()

    # ── 1. Load documents ─────────────────────────────────────────────────
    print(f"\n[1/4] Reading documents from: {assets_dir}")
    docs = read_documents(assets_dir)
    if not docs:
        print("  No .txt or .md files found. Exiting.")
        return
    print(f"  {len(docs)} file(s) loaded.")

    # ── 2. Chunk ──────────────────────────────────────────────────────────
    print(f"\n[2/4] Chunking (size={chunk_size} words, overlap={overlap} words)…")
    all_ids: list[str]       = []
    all_texts: list[str]     = []
    all_meta: list[dict]     = []

    for doc in docs:
        chunks = chunk_text(doc["text"], chunk_size, overlap)
        for i, chunk in enumerate(chunks):
            chunk_id = f"{doc['filename']}::chunk_{i:04d}"
            all_ids.append(chunk_id)
            all_texts.append(chunk)
            all_meta.append({
                "source":     doc["filename"],
                "path":       doc["path"],
                "chunk_index": i,
                "total_chunks": len(chunks),
                "word_count": len(chunk.split()),
            })
        print(f"  {doc['filename']:40s} -> {len(chunks):3d} chunks")

    print(f"  Total chunks: {len(all_ids)}")

    # ── 3. Set up Chroma + embedding function ─────────────────────────────
    print(f"\n[3/4] Initialising Chroma DB at: {db_dir}")
    print(f"  Embedding model: {EMBED_MODEL}  (downloading on first run…)")

    embed_fn = SentenceTransformerEmbeddingFunction(model_name=EMBED_MODEL)
    client   = chromadb.PersistentClient(path=db_dir)

    if reset:
        try:
            client.delete_collection(COLLECTION_NAME)
            print(f"  Existing collection '{COLLECTION_NAME}' deleted (--reset).")
        except Exception:
            pass

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embed_fn,
        metadata={"hnsw:space": "cosine"},
    )

    # ── 4. Upsert in batches (Chroma has a default batch limit) ───────────
    print(f"\n[4/4] Embedding & storing {len(all_ids)} chunks…")
    BATCH = 64
    for start in range(0, len(all_ids), BATCH):
        end = min(start + BATCH, len(all_ids))
        collection.upsert(
            ids=all_ids[start:end],
            documents=all_texts[start:end],
            metadatas=all_meta[start:end],
        )
        print(f"  Upserted batch {start//BATCH + 1}/{-(-len(all_ids)//BATCH)}"
              f"  (chunks {start}–{end-1})")

    elapsed = time.perf_counter() - t0
    print(f"\nDone. {len(all_ids)} chunks indexed in {elapsed:.1f}s.")
    print(f"Database stored at: {db_dir}")
    print(f"\nQuery with:\n  .venv\\Scripts\\python.exe rag_query.py --query \"your question here\"")


# ─────────────────────────────────────────────────────────────────────────────
# CLI entry point
# ─────────────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="RAG Indexing Pipeline")
    p.add_argument("--assets-dir",  default=DEFAULT_ASSETS_DIR,
                   help="Folder containing .txt/.md documents")
    p.add_argument("--db-dir",      default=DEFAULT_DB_DIR,
                   help="Folder where the Chroma DB will be persisted")
    p.add_argument("--chunk-size",  type=int, default=DEFAULT_CHUNK_SIZE,
                   help="Target words per chunk (default: 400)")
    p.add_argument("--overlap",     type=int, default=DEFAULT_OVERLAP,
                   help="Overlap words between consecutive chunks (default: 60)")
    p.add_argument("--reset",       action="store_true",
                   help="Delete and recreate the collection before indexing")
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    build_index(
        assets_dir=args.assets_dir,
        db_dir=args.db_dir,
        chunk_size=args.chunk_size,
        overlap=args.overlap,
        reset=args.reset,
    )
