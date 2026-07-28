from app.rag.vector_store import VectorStore

store = VectorStore()

results = store.similarity_search(
    query="what is machine learning",
    dept_id="GENERAL",
    k=3,
    filter_metadata={
        "source": "documents/sample.pdf"
    }
)

print("Results:", len(results))

for doc in results:
    print(doc.metadata)