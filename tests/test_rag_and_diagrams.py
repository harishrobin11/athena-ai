import pytest
from app.services.document_service import DocumentService
from langchain_core.documents import Document

def test_cached_document_chunks_targeted_query():
    doc_service = DocumentService()
    
    # Create sample multi-page document
    sample_docs = [
        Document(page_content="Page 1: Overview of Athena AI system architecture. The system uses LangGraph and FastAPI.", metadata={"page": 1}),
        Document(page_content="Page 2: Financial records. Total Q3 revenue was $500,000 and total expenses were $120,000 for server hosting.", metadata={"page": 2}),
        Document(page_content="Page 3: Compliance policy. All employees must pass security training every year.", metadata={"page": 3}),
    ]
    
    doc_service.cache_document_text("test_doc.pdf", sample_docs, user_id=1)
    
    # Query specifically about expenses
    expense_chunks = doc_service.get_cached_document_chunks("test_doc.pdf", query="what were the expenses for server hosting?", top_k=1)
    assert len(expense_chunks) == 1
    assert "expenses were $120,000" in expense_chunks[0].page_content
    assert "Compliance policy" not in expense_chunks[0].page_content

def test_cached_document_text_query_filtering():
    doc_service = DocumentService()
    
    sample_docs = [
        Document(page_content="Section A: User authentication with JWT tokens.", metadata={"page": 1}),
        Document(page_content="Section B: Database schema details for PostgreSQL tables.", metadata={"page": 2})
    ]
    doc_service.cache_document_text("auth_doc.pdf", sample_docs, user_id=1)
    
    filtered_text = doc_service.get_cached_document_text("auth_doc.pdf", query="authentication JWT tokens")
    assert "User authentication" in filtered_text
    assert "Database schema" not in filtered_text

def test_full_text_fallback_when_explicitly_requested():
    doc_service = DocumentService()
    
    sample_docs = [
        Document(page_content="Part 1: Intro.", metadata={"page": 1}),
        Document(page_content="Part 2: Conclusion.", metadata={"page": 2})
    ]
    doc_service.cache_document_text("full_doc.pdf", sample_docs, user_id=1)
    
    full_text = doc_service.get_cached_document_text("full_doc.pdf", query="read full entire document")
    assert "Part 1" in full_text
    assert "Part 2" in full_text
