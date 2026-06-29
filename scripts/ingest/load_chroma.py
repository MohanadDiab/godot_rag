"""Load merged chunks into ChromaDB."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.chunk.config import CHUNKS_JSONL_PATH, ensure_data_dirs, get_paths
from scripts.chunk.schema import Chunk, read_chunks_jsonl
from scripts.ingest.chroma_utils import (
    chunk_to_chroma_metadata,
    get_chroma_client,
    get_or_create_collection,
)

logger = logging.getLogger(__name__)

DEFAULT_BATCH_SIZE = 100


def load_chunks_to_chroma(
    *,
    chunks_path: Path | None = None,
    persist_dir: Path | None = None,
    rebuild: bool = False,
    upsert: bool = True,
    batch_size: int = DEFAULT_BATCH_SIZE,
    limit: int | None = None,
) -> dict:
    """Ingest chunks.jsonl into a persistent Chroma collection."""
    ensure_data_dirs()
    paths = get_paths()
    jsonl_path = chunks_path or paths.chunks_jsonl
    chroma_dir = persist_dir or paths.chroma_persist

    if not jsonl_path.exists():
        raise FileNotFoundError(f"Missing merged chunks: {jsonl_path}")

    chunks = read_chunks_jsonl(jsonl_path)
    if limit:
        chunks = chunks[:limit]

    client = get_chroma_client(str(chroma_dir))
    collection = get_or_create_collection(client, rebuild=rebuild)

    total = len(chunks)
    ingested = 0

    for start in range(0, total, batch_size):
        batch = chunks[start : start + batch_size]
        ids = [c.chunk_id for c in batch]
        documents = [c.text for c in batch]
        metadatas = [chunk_to_chroma_metadata(c) for c in batch]

        if rebuild or upsert:
            collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
        else:
            collection.add(ids=ids, documents=documents, metadatas=metadatas)

        ingested += len(batch)
        logger.info("Ingested %d / %d chunks", ingested, total)

    return {
        "collection": collection.name,
        "persist_dir": str(chroma_dir),
        "chunks_ingested": ingested,
        "rebuild": rebuild,
        "upsert": upsert,
        "batch_size": batch_size,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Load chunks.jsonl into ChromaDB")
    parser.add_argument(
        "--chunks",
        type=str,
        default=None,
        help="Path to chunks.jsonl (default: data/chunks.jsonl)",
    )
    parser.add_argument(
        "--persist-dir",
        type=str,
        default=None,
        help="Chroma persist directory (default: data/chroma)",
    )
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Delete and recreate the collection before loading",
    )
    parser.add_argument(
        "--add",
        action="store_true",
        help="Use add instead of upsert (fails if IDs exist)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help="Batch size for upsert",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Ingest only the first N chunks (for testing)",
    )
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    result = load_chunks_to_chroma(
        chunks_path=Path(args.chunks) if args.chunks else None,
        persist_dir=Path(args.persist_dir) if args.persist_dir else None,
        rebuild=args.rebuild,
        upsert=not args.add,
        batch_size=args.batch_size,
        limit=args.limit,
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
