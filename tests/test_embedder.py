from app.rag.embedder import EmbeddingModel

if __name__ == "__main__":
    embedder = EmbeddingModel()
    model = embedder.get_model()
    vector = model.embed_query("What is Artificial Intelligence?")
    print(f"Embedding length: {len(vector)}")
    print(vector[:10])  # First 10 values