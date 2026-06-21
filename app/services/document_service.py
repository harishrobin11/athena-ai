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

    def ingest(self, pdf_path: str):
        # Load the PDF
        documents = load_pdf(pdf_path)

        # Split into chunks
        chunks = self.splitter.split(documents)

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
    def delete_document(self, filename: str):
    
        file_path = Path("documents") / filename

        if file_path.exists():
            file_path.unlink()

            return True

        return False
