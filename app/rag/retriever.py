from .vector_store import VectorStore


class Retriever:
    def __init__(self):
        self.store = VectorStore()

    def retrieve(
        self,
        query,
        k=3,
        filter_metadata=None,
    ):
        return self.store.similarity_search(
            query=query,
            k=k,
            filter_metadata=filter_metadata,
        )