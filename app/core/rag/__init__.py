from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(slots=True)
class RetrievedSnippet:
    title: str
    content: str
    score: float = 0.0


def retrieve_approved_snippets(query: str, documents: Iterable[RetrievedSnippet] | None = None) -> list[RetrievedSnippet]:
    documents = list(documents or [])
    if not query.strip() or not documents:
        return []
    tokens = {token for token in query.lower().split() if len(token) > 2}
    scored: list[RetrievedSnippet] = []
    for doc in documents:
        haystack = f"{doc.title} {doc.content}".lower()
        score = sum(1 for token in tokens if token in haystack)
        if score:
            scored.append(RetrievedSnippet(title=doc.title, content=doc.content, score=float(score)))
    return sorted(scored, key=lambda item: item.score, reverse=True)[:3]
