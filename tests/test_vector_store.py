import os
import pytest
from app.rag.loader import load_pdf
from app.rag.splitter import DocumentSplitter
from app.rag.vector_store import VectorStore

def test_vector_store_operations():
    sample_pdf = os.path.join("documents", "sample.pdf")
    if os.path.exists(sample_pdf):
        docs = load_pdf(sample_pdf)
        splitter = DocumentSplitter()
        chunks = splitter.split(docs)
        db = VectorStore()
        db.add_documents(chunks, dept_id="GENERAL")
        results = db.similarity_search("What is Artificial Intelligence?", dept_id="GENERAL")
        assert isinstance(results, list)