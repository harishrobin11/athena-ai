from langchain_chroma import Chroma
from app.rag.embedder import EmbeddingModel


class VectorStore:
    def __init__(self, persist_directory="data/chroma"):
        self.embedding = EmbeddingModel().get_model()

        self.db = Chroma(
            persist_directory=persist_directory,
            embedding_function=self.embedding,
        )

    def add_documents(self, documents):
        self.db.add_documents(documents)

    def similarity_search(self, query, k=3):
        return self.db.similarity_search(query, k=k)