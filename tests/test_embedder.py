import pytest
from app.rag.embedder import EmbeddingModel

def test_embedding_model_generation():
    embedder = EmbeddingModel()
    model = embedder.get_model()
    vector = model.embed_query("What is Artificial Intelligence?")
    assert vector is not None
    assert len(vector) > 0