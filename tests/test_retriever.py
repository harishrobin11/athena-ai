import pytest
from app.rag.retriever import Retriever

def test_retriever_query():
    retriever = Retriever()
    results = retriever.retrieve("What is Artificial Intelligence?")
    assert isinstance(results, list)