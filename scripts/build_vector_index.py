from __future__ import annotations

from pathlib import Path
import json


def build_index(source_dir: Path, output_file: Path) -> None:
    source_dir.mkdir(parents=True, exist_ok=True)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    documents = []
    for path in sorted(source_dir.rglob("*.txt")):
        documents.append(
            {
                "path": str(path),
                "content": path.read_text(encoding="utf-8"),
            }
        )
    output_file.write_text(json.dumps(documents, indent=2), encoding="utf-8")


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    build_index(root / "app" / "data" / "knowledge_base", root / "app" / "data" / "vector_index" / "index.json")
