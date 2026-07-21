from app.rag.retriever import Retriever

if __name__ == "__main__":
    retriever = Retriever()
    results = retriever.retrieve(
        "What is Artificial Intelligence?"
    )
    print(f"Retrieved {len(results)} documents.\n")
    for i, doc in enumerate(results, start=1):
        print(f"Result {i}")
        print("=" * 60)
        print(doc.page_content[:400])
        print("\nMetadata:", doc.metadata)
        print("-" * 60)