import os
import pytest
from app.rag.loader import load_pdf
from app.services.document_service import DocumentService

def test_pymupdf_fast_loading(tmp_path):
    sample_pdf = os.path.join(os.getcwd(), "documents", "sample.pdf")
    if os.path.exists(sample_pdf):
        docs = load_pdf(sample_pdf)
        assert len(docs) > 0
        assert docs[0].page_content is not None
        assert len(docs[0].page_content.strip()) > 0

def test_document_service_cache():
    doc_service = DocumentService()
    sample_filename = "test_invoice.pdf"
    
    # Verify cache starts empty
    assert doc_service.get_cached_document_text(sample_filename) == ""
    
    from langchain_core.documents import Document
    mock_docs = [Document(page_content="Invoice #12345 Grand Total: $500.00", metadata={"source": sample_filename})]
    
    # Cache document
    doc_service.cache_document_text(sample_filename, mock_docs, user_id=1)
    
    # Verify fast cache retrieval
    cached = doc_service.get_cached_document_text(sample_filename)
    assert "Invoice #12345" in cached
    assert "$500.00" in cached
