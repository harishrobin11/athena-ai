import os
import pytest
from app.rag.loader import load_pdf
from app.rag.splitter import DocumentSplitter

def test_document_splitter():
    sample_pdf = os.path.join("documents", "sample.pdf")
    if os.path.exists(sample_pdf):
        docs = load_pdf(sample_pdf)
        splitter = DocumentSplitter()
        chunks = splitter.split(docs)
        assert len(chunks) > 0