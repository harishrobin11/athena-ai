from app.rag.vector_store import VectorStore

store = VectorStore()

results = store.db.similarity_search(
    query="what is machine learning",
    k=3,
    filter={
        "source": "documents/sample.pdf"
    }
)

print("Results:", len(results))

for doc in results:
    print(doc.metadata)