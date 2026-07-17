from langchain_chroma import Chroma
from app.rag.embedder import EmbeddingModel
import math

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
    
    def keyword_search(
        self,
        query: str,
        limit: int = 10,
        filter_metadata=None,
    ):
        results = self.db._collection.get(
            where=filter_metadata,
            include=["documents", "metadatas"]
        )
        documents = results["documents"]

        total_docs = len(documents)
        doc_freq = {}

        for doc in documents:

            words = set(
                doc.lower().split()
            )

            for word in words:

                doc_freq[word] = (
                    doc_freq.get(word, 0)
                    + 1
                )

        query_words = (
            query.lower().split()
        )

        matches = []

        for doc, metadata in zip(
            results["documents"],
            results["metadatas"],
        ):

            text = doc.lower()

            score = 0.0

            words = text.split()

            doc_len = len(words)

            for word in query_words:

                tf = words.count(word)

                if tf == 0:
                    continue

                df = doc_freq.get(word, 1)

                idf = math.log(
                    (
                        total_docs - df + 0.5
                    )
                    /
                    (
                        df + 0.5
                    )
                    + 1
                )

                score += (
                    tf * idf
                ) / (
                    tf
                    + 1.5
                    * (
                        0.25
                        + 0.75
                        * (doc_len / 100)
                    )
                )

            if score > 0:

                matches.append(
                    {
                        "document": doc,
                        "metadata": metadata,
                        "keyword_score": score,
                    }
                )

        matches.sort(
            key=lambda x: x["keyword_score"],
            reverse=True,
        )

        return matches[:limit]