import math
from typing import List, Dict, Any, Optional
from langchain_chroma import Chroma
from app.rag.embedder import EmbeddingModel

class VectorStore:
    def __init__(self, persist_directory: str = "data/chroma"):
        """
        Initializes the shared base configuration and embedding engine.
        Multi-tenant isolation happens dynamically per collection layout.
        """
        self.embedding = EmbeddingModel().get_model()
        self.persist_directory = persist_directory

    def _get_tenant_db(self, dept_id: str) -> Chroma:
        """
        Private factory method to isolate collection naming boundaries dynamically.
        """
        # Formulate a safe, uniform string token matching tenant boundaries
        clean_dept = dept_id.lower().strip().replace("-", "_")
        collection_name = f"tenant_{clean_dept}_vault"
        
        return Chroma(
            collection_name=collection_name,
            persist_directory=self.persist_directory,
            embedding_function=self.embedding,
        )

    def add_documents(self, documents: List[Any], dept_id: str):
        """Adds documents into the isolated tenant collection space."""
        db = self._get_tenant_db(dept_id)
        db.add_documents(documents)

    def similarity_search(
        self,
        query: str,
        dept_id: str,
        k: int = 3,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ):
        """Executes a similarity search partitioned strictly within the tenant collection."""
        db = self._get_tenant_db(dept_id)
        return db.similarity_search(
            query=query,
            k=k,
            filter=filter_metadata,
        )

    def debug_collection(self, dept_id: str) -> List[Dict[str, Any]]:
        """Inspects metadata tags for the top 5 records within a tenant collection."""
        db = self._get_tenant_db(dept_id)
        result = db._collection.get(include=["metadatas"])
        return result["metadatas"][:5]

    def delete_document_embeddings(self, filename: str, user_id: str, dept_id: str):
        """Purges document embeddings matching structural boundaries within the tenant collection."""
        db = self._get_tenant_db(dept_id)
        db._collection.delete(
            where={
                "$and": [
                    {"filename": filename},
                    {"user_id": user_id},
                ]
            }
        )

    def count_embeddings(self, dept_id: str) -> int:
        """Counts total active vector records registered within a tenant's vault."""
        db = self._get_tenant_db(dept_id)
        result = db._collection.get()
        return len(result["ids"])
    
    def keyword_search(
        self,
        query: str,
        dept_id: str,
        limit: int = 10,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ):
        """Executes your customizable term frequency scoring model across tenant metadata horizons."""
        db = self._get_tenant_db(dept_id)
        results = db._collection.get(
            where=filter_metadata,
            include=["documents", "metadatas"]
        )
        documents = results["documents"]
        total_docs = len(documents)
        
        if total_docs == 0:
            return []
            
        doc_freq = {}
        for doc in documents:
            words = set(doc.lower().split())
            for word in words:
                doc_freq[word] = doc_freq.get(word, 0) + 1

        query_words = query.lower().split()
        matches = []

        for doc, metadata in zip(results["documents"], results["metadatas"]):
            text = doc.lower()
            score = 0.0
            words = text.split()
            doc_len = len(words)

            for word in query_words:
                tf = words.count(word)
                if tf == 0:
                    continue

                df = doc_freq.get(word, 1)
                # BM25-scaled Term Frequency Inverse Document Frequency
                idf = math.log((total_docs - df + 0.5) / (df + 0.5) + 1)
                score += (tf * idf) / (tf + 1.5 * (0.25 + 0.75 * (doc_len / 100)))

            if score > 0:
                matches.append({
                    "document": doc,
                    "metadata": metadata,
                    "keyword_score": score,
                })

        matches.sort(key=lambda x: x["keyword_score"], reverse=True)
        return matches[:limit]