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
        """Caches raw loaded documents in memory for ultra-fast instant RAG lookup."""
        full_text = "\n\n".join([doc.page_content for doc in documents if doc.page_content])
        self._doc_cache[filename] = {
            "text": full_text,
            "documents": documents,
            "user_id": user_id
        }

    def get_cached_document_text(self, filename: str) -> str:
        """Retrieves cached document text if present."""
        if filename in self._doc_cache:
            return self._doc_cache[filename]["text"]
        return ""

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