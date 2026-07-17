from .vector_store import VectorStore


class Retriever:

    def __init__(self):
        self.store = VectorStore()

    def retrieve(
        self,
        query: str,
        filter_metadata=None,
        top_k: int = 5,
        use_hybrid: bool = True,
    ):

        vector_results = self.store.similarity_search(
            query=query,
            k=top_k,
            filter_metadata=filter_metadata,
        )

        if not use_hybrid:
            return vector_results

        keyword_results = self.store.keyword_search(
            query=query,
            limit=top_k,
        )

        merged = {}

        #
        # Vector results
        #

        for doc in vector_results:

            key = doc.page_content

            merged[key] = {
                "document": doc.page_content,
                "metadata": doc.metadata,
                "vector_score": 1.0,
                "keyword_score": 0,
            }

        #
        # Keyword results
        #

        for item in keyword_results:

            key = item["document"]

            if key in merged:

                merged[key]["keyword_score"] = (
                    item["keyword_score"]
                )

            else:

                merged[key] = {
                    "document": item["document"],
                    "metadata": item["metadata"],
                    "vector_score": 0,
                    "keyword_score": item["keyword_score"],
                }

        #
        # Hybrid scoring
        #

        for item in merged.values():

            item["hybrid_score"] = (
                item["vector_score"] * 0.7
                +
                item["keyword_score"] * 0.3
            )

        reranked = sorted(
            merged.values(),
            key=lambda x: x["hybrid_score"],
            reverse=True,
        )

        return reranked[:top_k]