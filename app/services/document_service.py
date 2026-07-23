from app.rag.loader import load_pdf
from app.rag.splitter import DocumentSplitter
from app.rag.vector_store import VectorStore
from pathlib import Path

class DocumentService:
    def __init__(self):
        self.splitter = DocumentSplitter()
        self.store = None
        self._doc_cache = {}  # In-memory document text cache keyed by filename

    def _get_store(self):
        if self.store is None:
            self.store = VectorStore()
        return self.store

    def cache_document_text(self, filename: str, documents: list, user_id: int = None):
        """Caches raw loaded documents and chunked representations in memory for ultra-fast instant RAG lookup."""
        full_text = "\n\n".join([doc.page_content for doc in documents if doc.page_content])
        chunks = self.splitter.split(documents) if documents else []
        self._doc_cache[filename] = {
            "text": full_text,
            "documents": documents,
            "chunks": chunks,
            "user_id": user_id
        }

    def get_cached_document_chunks(self, filename: str, query: str = "", top_k: int = 5) -> list:
        """Retrieves top matching cached document chunks for a query instead of the whole file."""
        if filename not in self._doc_cache:
            return []
        
        entry = self._doc_cache[filename]
        chunks = entry.get("chunks", [])
        if not chunks:
            chunks = entry.get("documents", [])
            
        if not chunks:
            return []

        query_clean = (query or "").strip().lower()
        if not query_clean or any(kw in query_clean for kw in ["full text", "entire document", "read full", "whole pdf", "all content"]):
            return chunks

        query_words = [w for w in query_clean.split() if len(w) > 2]
        if not query_words:
            query_words = query_clean.split()

        scored = []
        for chunk in chunks:
            content = getattr(chunk, "page_content", str(chunk)).lower()
            score = sum(content.count(w) for w in query_words)
            scored.append((score, chunk))
            
        scored.sort(key=lambda x: x[0], reverse=True)
        top_matches = [item[1] for item in scored if item[0] > 0][:top_k]
        return top_matches if top_matches else chunks[:top_k]

    def get_cached_document_text(self, filename: str, query: str = None) -> str:
        """Retrieves cached document text. If query is provided, returns targeted top matching chunks."""
        if filename not in self._doc_cache:
            return ""
        
        if query:
            matched = self.get_cached_document_chunks(filename, query=query, top_k=5)
            if matched:
                return "\n\n".join([getattr(c, "page_content", str(c)) for c in matched])
                
        return self._doc_cache[filename]["text"]

    def ingest(
        self,
        pdf_path: str,
        user_id: int,
        original_filename: str = None,
        dept_id: str = "GENERAL"
    ):
        # Load the PDF
        documents = load_pdf(pdf_path)
        filename = original_filename or Path(pdf_path).name

        # Cache in memory immediately for 0ms chat access
        self.cache_document_text(filename, documents, user_id=user_id)

        # Split into chunks
        chunks = self.splitter.split(documents)

        for chunk in chunks:
            chunk.metadata["user_id"] = user_id
            chunk.metadata["filename"] = filename

        # Get (or create) the vector store
        store = self._get_store()
        
        # Store the chunks
        store.add_documents(chunks, dept_id=dept_id)

        return len(chunks)
    
    def list_documents(self):
    
        documents_dir = Path("documents")

        documents_dir.mkdir(exist_ok=True)

        return [
            file.name
            for file in documents_dir.glob("*.pdf")
        ]
        
    def delete_document(
        self,
        filename: str,
        user_id: int,
        dept_id: str = "GENERAL"
    ):
        file_path = (
            Path("documents")
            / f"user_{user_id}"
            / filename
        )

        if file_path.exists():
            file_path.unlink()

        store = self._get_store()
        store.delete_document_embeddings(
            filename=filename,
            user_id=user_id,
            dept_id=dept_id,
        )

        return True
    
    def document_count(self):
        
        return len(
            self.list_documents()
        )