from __future__ import annotations

from app.core.rag import (
    KnowledgeDocument,
    VectorIndex,
    clear_index_cache,
    get_index,
    load_knowledge_base,
    rebuild_index,
    retrieve_approved_snippets,
)


def test_load_knowledge_base_missing_directory_returns_empty(tmp_path):
    docs = load_knowledge_base(tmp_path / "does-not-exist")

    assert docs == []


def test_load_knowledge_base_extracts_title_from_heading(populated_settings):
    docs = load_knowledge_base(populated_settings.knowledge_base_path)

    titles = {doc.title for doc in docs}
    assert "Plants and Photosynthesis" in titles
    assert "The Water Cycle" in titles


def test_vector_index_search_finds_relevant_document():
    documents = [
        KnowledgeDocument(
            title="Plants and Photosynthesis",
            content="Plants make food using sunlight and water.",
            source="plants.md",
        ),
        KnowledgeDocument(
            title="The Water Cycle",
            content="Water evaporates, condenses, and falls as rain.",
            source="water.md",
        ),
    ]
    index = VectorIndex.build(documents)

    results = index.search("How do plants make food?", top_k=2)

    assert results
    assert results[0].title == "Plants and Photosynthesis"
    assert results[0].score > 0


def test_vector_index_search_empty_query_returns_nothing():
    documents = [KnowledgeDocument(title="A", content="Some content.", source="a.md")]
    index = VectorIndex.build(documents)

    assert index.search("", top_k=3) == []


def test_vector_index_round_trips_through_json(tmp_path):
    documents = [KnowledgeDocument(title="A", content="Plants make food using sunlight.", source="a.md")]
    index = VectorIndex.build(documents)

    path = tmp_path / "index.json"
    index.save(path)
    loaded = VectorIndex.load(path)

    assert loaded is not None
    assert [d.title for d in loaded.documents] == ["A"]
    results = loaded.search("plants and sunlight")
    assert results and results[0].title == "A"


def test_vector_index_load_missing_file_returns_none(tmp_path):
    assert VectorIndex.load(tmp_path / "missing.json") is None


def test_retrieve_approved_snippets_empty_query_returns_empty(populated_settings):
    assert retrieve_approved_snippets("", populated_settings) == []


def test_retrieve_approved_snippets_no_knowledge_base_returns_empty(settings):
    clear_index_cache()
    assert retrieve_approved_snippets("anything", settings) == []


def test_retrieve_approved_snippets_finds_lesson(populated_settings):
    clear_index_cache()

    results = retrieve_approved_snippets("Tell me about the water cycle", populated_settings, top_k=1)

    assert len(results) == 1
    assert results[0].title == "The Water Cycle"


def test_get_index_is_cached(populated_settings):
    clear_index_cache()

    first = get_index(populated_settings)
    second = get_index(populated_settings)

    assert first is second


def test_rebuild_index_persists_and_refreshes_cache(populated_settings):
    clear_index_cache()
    get_index(populated_settings)  # build & cache the in-memory index first

    index = rebuild_index(populated_settings, persist=True)

    index_file = populated_settings.vector_index_path / "index.json"
    assert index_file.exists()
    assert len(index.documents) == 2
    assert get_index(populated_settings) is index
