"""Build (or rebuild) the local TF-IDF retrieval index.

This is optional: :func:`app.core.rag.get_index` will build an in-memory
index on the fly from ``app/data/knowledge_base`` if no index file exists.
Running this script pre-builds and persists ``app/data/vector_index/index.json``
so the first request doesn't pay the (tiny) build cost, and so the index can
be inspected or committed alongside the lesson notes.

Usage:
    python -m scripts.build_vector_index
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import load_settings
from app.core.rag import rebuild_index


def main() -> None:
    settings = load_settings()
    index = rebuild_index(settings, persist=True)
    index_file = settings.vector_index_path / "index.json"
    print(f"Indexed {len(index.documents)} document(s) from {settings.knowledge_base_path}")
    for doc in index.documents:
        print(f"  - {doc.title} ({doc.source})")
    print(f"Saved index to {index_file}")


if __name__ == "__main__":
    main()
