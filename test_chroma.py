from app.rag.vector_store import VectorStore

store = VectorStore()

print("Embeddings:", store.count_embeddings())
print(store.debug_collection())