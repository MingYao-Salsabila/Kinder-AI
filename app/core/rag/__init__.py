from __future__ import annotations

import json
import math
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Iterable

if TYPE_CHECKING:
    from app.config import AppSettings

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "but", "by", "for", "from",
    "has", "have", "how", "in", "into", "is", "it", "its", "of", "on", "or",
    "our", "so", "such", "that", "the", "their", "this", "to", "was", "we",
    "what", "when", "where", "which", "who", "why", "will", "with", "you",
    "your",
}
_INDEX_FILENAME = "index.json"


@dataclass(slots=True)
class KnowledgeDocument:
    """A single lesson note loaded from the knowledge base directory."""

    title: str
    content: str
    source: str


@dataclass(slots=True)
class RetrievedSnippet:
    """A scored piece of curated content returned by a search."""

    title: str
    content: str
    score: float = 0.0
    source: str = ""

    def as_dict(self) -> dict[str, str]:
        """Plain-dict view used by LLM providers (keeps providers decoupled from this module)."""
        return {"title": self.title, "content": self.content, "source": self.source}


def _tokenize(text: str) -> list[str]:
    tokens = _TOKEN_RE.findall((text or "").lower())
    return [token for token in tokens if len(token) > 1 and token not in _STOPWORDS]


def _extract_title(text: str, fallback: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip() or fallback
        return stripped[:80]
    return fallback


def load_knowledge_base(directory: Path) -> list[KnowledgeDocument]:
    """Load every ``.md``/``.txt`` lesson note under ``directory``.

    Returns an empty list (rather than raising) if the directory does not
    exist yet, so a fresh checkout still runs without any setup step.
    """

    documents: list[KnowledgeDocument] = []
    if not directory or not directory.exists():
        return documents

    for path in sorted(directory.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".md", ".txt"}:
            continue
        try:
            text = path.read_text(encoding="utf-8").strip()
        except OSError:
            continue
        if not text:
            continue
        title = _extract_title(text, fallback=path.stem.replace("_", " ").replace("-", " ").title())
        documents.append(
            KnowledgeDocument(title=title, content=text, source=path.name)
        )
    return documents


@dataclass(slots=True)
class VectorIndex:
    """A tiny TF-IDF index with cosine-similarity search.

    Stored as plain JSON (vocabulary, IDF weights, and per-document sparse
    vectors) so it has zero runtime dependencies beyond the standard library
    and is safe to load regardless of which numpy/scikit-learn version (if
    any) built it.
    """

    vocabulary: dict[str, int]
    idf: list[float]
    documents: list[KnowledgeDocument] = field(default_factory=list)
    vectors: list[dict[int, float]] = field(default_factory=list)

    @classmethod
    def build(cls, documents: Iterable[KnowledgeDocument]) -> "VectorIndex":
        documents = list(documents)
        doc_tokens = [_tokenize(f"{doc.title}\n{doc.content}") for doc in documents]

        doc_freq: Counter[str] = Counter()
        for tokens in doc_tokens:
            doc_freq.update(set(tokens))

        vocabulary = {term: idx for idx, term in enumerate(sorted(doc_freq))}
        n_docs = max(len(documents), 1)
        idf = [math.log((1 + n_docs) / (1 + doc_freq[term])) + 1.0 for term in vocabulary]

        vectors: list[dict[int, float]] = []
        for tokens in doc_tokens:
            vectors.append(_vectorize(tokens, vocabulary, idf))

        return cls(vocabulary=vocabulary, idf=idf, documents=documents, vectors=vectors)

    def search(self, query: str, top_k: int = 3, min_score: float = 0.1) -> list[RetrievedSnippet]:
        if not query or not self.documents or not self.vocabulary:
            return []

        query_vector = _vectorize(_tokenize(query), self.vocabulary, self.idf)
        if not query_vector:
            return []

        scored: list[tuple[float, int]] = []
        for idx, doc_vector in enumerate(self.vectors):
            score = _cosine(query_vector, doc_vector)
            if score >= min_score:
                scored.append((score, idx))

        scored.sort(key=lambda item: item[0], reverse=True)
        results = []
        for score, idx in scored[: max(0, top_k)]:
            doc = self.documents[idx]
            results.append(
                RetrievedSnippet(title=doc.title, content=doc.content, score=round(score, 4), source=doc.source)
            )
        return results

    def to_dict(self) -> dict:
        return {
            "vocabulary": self.vocabulary,
            "idf": self.idf,
            "documents": [
                {"title": doc.title, "content": doc.content, "source": doc.source} for doc in self.documents
            ],
            "vectors": [{str(k): v for k, v in vec.items()} for vec in self.vectors],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "VectorIndex":
        documents = [KnowledgeDocument(**doc) for doc in data.get("documents", [])]
        vectors = [{int(k): v for k, v in vec.items()} for vec in data.get("vectors", [])]
        return cls(
            vocabulary=dict(data.get("vocabulary", {})),
            idf=list(data.get("idf", [])),
            documents=documents,
            vectors=vectors,
        )

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> "VectorIndex | None":
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        try:
            return cls.from_dict(data)
        except (TypeError, KeyError, ValueError):
            return None


def _vectorize(tokens: list[str], vocabulary: dict[str, int], idf: list[float]) -> dict[int, float]:
    if not tokens:
        return {}
    counts = Counter(tokens)
    weighted: dict[int, float] = {}
    for term, count in counts.items():
        idx = vocabulary.get(term)
        if idx is None:
            continue
        weighted[idx] = count * idf[idx]

    norm = math.sqrt(sum(value * value for value in weighted.values()))
    if norm == 0:
        return {}
    return {idx: value / norm for idx, value in weighted.items()}


def _cosine(a: dict[int, float], b: dict[int, float]) -> float:
    if len(b) < len(a):
        a, b = b, a
    return sum(value * b[idx] for idx, value in a.items() if idx in b)


# In-memory cache so repeated Streamlit reruns don't re-scan the filesystem
# or rebuild the TF-IDF index on every interaction.
_INDEX_CACHE: dict[tuple[str, str], VectorIndex] = {}


def _cache_key(settings: "AppSettings") -> tuple[str, str]:
    return (str(settings.knowledge_base_path), str(settings.vector_index_path))


def clear_index_cache() -> None:
    """Drop the in-memory index cache (used after rebuilding the index)."""
    _INDEX_CACHE.clear()


def get_index(settings: "AppSettings") -> VectorIndex:
    """Return the TF-IDF index for ``settings``, building it if necessary.

    Resolution order: in-memory cache -> persisted ``index.json`` on disk ->
    a fresh build from ``knowledge_base_path``. The result is always cached
    in memory (even an empty index), so a missing knowledge base degrades to
    "no snippets found" instead of repeated filesystem scans.
    """

    key = _cache_key(settings)
    cached = _INDEX_CACHE.get(key)
    if cached is not None:
        return cached

    persisted = VectorIndex.load(settings.vector_index_path / _INDEX_FILENAME)
    if persisted is not None and persisted.documents:
        _INDEX_CACHE[key] = persisted
        return persisted

    documents = load_knowledge_base(settings.knowledge_base_path)
    index = VectorIndex.build(documents)
    _INDEX_CACHE[key] = index
    return index


def rebuild_index(settings: "AppSettings", persist: bool = True) -> VectorIndex:
    """Rebuild the index from disk, optionally persisting it, and refresh the cache."""

    documents = load_knowledge_base(settings.knowledge_base_path)
    index = VectorIndex.build(documents)
    if persist:
        try:
            index.save(settings.vector_index_path / _INDEX_FILENAME)
        except OSError:
            # Some deployment platforms have read-only filesystems outside
            # of a designated writable directory -- keep the in-memory
            # index usable even if persistence fails.
            pass
    _INDEX_CACHE[_cache_key(settings)] = index
    return index


def retrieve_approved_snippets(
    query: str, settings: "AppSettings", top_k: int = 3, min_score: float = 0.1
) -> list[RetrievedSnippet]:
    """Return up to ``top_k`` curated lesson snippets relevant to ``query``.

    Returns an empty list for an empty query, an empty/missing knowledge
    base, or when nothing clears ``min_score`` -- callers should treat
    "no snippets" as a normal, expected case.
    """

    query = (query or "").strip()
    if not query:
        return []

    index = get_index(settings)
    return index.search(query, top_k=top_k, min_score=min_score)
