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

    def similarity_search(
        self,
        query,
        k=3,
        filter_metadata=None,
    ):
        return self.db.similarity_search(
            query=query,
            k=k,
            filter=filter_metadata,
        )

    def debug_collection(self):

        collection = self.db._collection

        result = collection.get(
            include=["metadatas"]
        )

        return result["metadatas"][:5]

    def delete_document_embeddings(
        self,
        filename,
        user_id,
    ):
        self.db._collection.delete(
            where={
                "$and": [
                    {"filename": filename},
                    {"user_id": user_id},
                ]
            }
        )
    def count_embeddings(self):
        
        result = self.db._collection.get()

        return len(result["ids"])