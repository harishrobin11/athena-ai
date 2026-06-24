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
        user_id: int
    ):
        # Load the PDF
        documents = load_pdf(pdf_path)

        # Split into chunks
        chunks = self.splitter.split(documents)
        filename = Path(pdf_path).name

        for chunk in chunks:
            chunk.metadata["user_id"] = user_id
            chunk.metadata["filename"] = filename

        # Get (or create) the vector store
        store = self._get_store()
        
        # Store the chunks
        store.add_documents(chunks)

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
        user_id: int
    ):
        file_path = (
            Path("documents")
            / f"user_{user_id}"
            / filename
        )

        if file_path.exists():
            
            store = self._get_store()

            store.delete_document_embeddings(
                filename=filename,
                user_id=user_id,
            )

            file_path.unlink()

            return True

        return False
    
    def document_count(self):
        
        return len(
            self.list_documents()
        )