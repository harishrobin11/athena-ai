import math
from typing import List, Dict, Any, Optional

class VectorStore:
    def __init__(self, persist_directory: str = "data/chroma"):
        self._embedding = None  # lazy-loaded on first use
        self.persist_directory = persist_directory

    @property
    def embedding(self):
        if self._embedding is None:
            from app.rag.embedder import EmbeddingModel
            self._embedding = EmbeddingModel().get_model()
        return self._embedding

    def _get_tenant_db(self, dept_id: str) -> Any:
        """
        Private factory method to isolate collection naming boundaries dynamically.
        """
        import os
        azure_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
        azure_key = os.getenv("AZURE_SEARCH_KEY")
        
        # Formulate a safe, uniform string token matching tenant boundaries
        clean_dept = dept_id.lower().strip().replace("-", "")
        collection_name = f"tenant-{clean_dept}-vault"
        
        if azure_endpoint and azure_key:
            try:
                from langchain_community.vectorstores.azuresearch import AzureSearch
                return AzureSearch(
                    azure_search_endpoint=azure_endpoint,
                    azure_search_key=azure_key,
                    index_name=collection_name,
                    embedding_function=self.embedding.embed_query
                )
            except ImportError:
                print("azure-search-documents missing, falling back to Chroma")
        
        chroma_collection = f"tenant_{clean_dept}_vault"
        try:
            from langchain_chroma import Chroma
        except ImportError:
            from langchain_community.vectorstores import Chroma
        return Chroma(
            collection_name=chroma_collection,
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
        if hasattr(db, "_collection"):
            result = db._collection.get(include=["metadatas"])
            return result["metadatas"][:5]
        return []

    def delete_document_embeddings(self, filename: str, user_id: str, dept_id: str):
        """Purges document embeddings matching structural boundaries within the tenant collection."""
        db = self._get_tenant_db(dept_id)
        if hasattr(db, "_collection"):
            db._collection.delete(
                where={
                    "$and": [
                        {"filename": filename},
                        {"user_id": user_id},
                    ]
                }
            )
        else:
            print("Deletion for AzureSearch backend not implemented via Chroma API yet.")

    def count_embeddings(self, dept_id: str) -> int:
        """Counts total active vector records registered within a tenant's vault."""
        db = self._get_tenant_db(dept_id)
        if hasattr(db, "_collection"):
            result = db._collection.get()
            return len(result["ids"])
        return 0
    
    def keyword_search(
        self,
        query: str,
        dept_id: str,
        limit: int = 10,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ):
        """Executes your customizable term frequency scoring model across tenant metadata horizons."""
        db = self._get_tenant_db(dept_id)
        if not hasattr(db, "_collection"):
            # For AzureSearch, standard similarity search often includes semantic hybrid functionality
            docs = db.similarity_search(query, k=limit)
            return [{"document": d.page_content, "metadata": d.metadata, "keyword_score": 1.0} for d in docs]

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

    def hybrid_search_with_rerank(
        self,
        query: str,
        dept_id: str,
        limit: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Executes a dense vector search to retrieve a larger pool of candidates,
        then uses a Cross-Encoder Neural Re-ranker (FlashRank) to re-score and 
        prune down to the absolute most relevant top `limit` documents.
        """
        # Step 1: Broad Dense Retrieval (get 20 documents)
        initial_candidates = self.similarity_search(
            query=query, 
            dept_id=dept_id, 
            k=20, 
            filter_metadata=filter_metadata
        )
        
        if not initial_candidates:
            return []

        # Step 2: Cross-Encoder Neural Re-ranking
        try:
            from flashrank import Ranker, RerankRequest
            import os
            
            # Use the lightweight MiniLM model (ONNX)
            ranker = Ranker(model_name="ms-marco-MiniLM-L-6-v2", cache_dir=os.path.join(self.persist_directory, "flashrank_models"))
            
            # Format for flashrank
            passages = []
            for i, doc in enumerate(initial_candidates):
                passages.append({
                    "id": str(i),
                    "text": doc.page_content,
                    "meta": doc.metadata
                })
                
            rerankrequest = RerankRequest(query=query, passages=passages)
            rerank_results = ranker.rerank(rerankrequest)
            
            # Map back to our standard document structure
            final_results = []
            for result in rerank_results[:limit]:
                final_results.append({
                    "document": result["text"],
                    "metadata": result["meta"],
                    "relevance_score": result["score"]
                })
            
            return final_results
            
        except ImportError:
            from app.core.logger import logger
            logger.warning("Flashrank not installed. Falling back to base similarity search.")
            return [{"document": d.page_content, "metadata": d.metadata, "relevance_score": 1.0} for d in initial_candidates[:limit]]
        except Exception as e:
            from app.core.logger import logger
            logger.error(f"Neural Re-ranking failed: {e}. Falling back to base search.")
            return [{"document": d.page_content, "metadata": d.metadata, "relevance_score": 1.0} for d in initial_candidates[:limit]]