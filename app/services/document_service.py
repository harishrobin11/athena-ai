from app.rag.loader import load_pdf
from app.rag.splitter import DocumentSplitter
from app.rag.vector_store import VectorStore
from pathlib import Path

class DocumentService:
    def __init__(self):
        self.splitter = DocumentSplitter()
        self.store = None

    def _get_store(self):
        if self.store is None:
            self.store = VectorStore()
        return self.store

    def ingest(
        self,
        pdf_path: str,
        user_id: int,
        original_filename: str = None,
        dept_id: str = "GENERAL"
    ):
        # Load the PDF
        documents = load_pdf(pdf_path)

        # Split into chunks
        chunks = self.splitter.split(documents)
        filename = original_filename or Path(pdf_path).name

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