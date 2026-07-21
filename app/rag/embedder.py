class EmbeddingModel:
    def __init__(self):
        try:
            from langchain_huggingface import HuggingFaceEmbeddings
        except ImportError:
            from langchain_community.embeddings import HuggingFaceEmbeddings
        try:
            self.model = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                model_kwargs={
                    "device": "cpu",
                    "local_files_only": True,
                },
            )
        except Exception:
            self.model = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                model_kwargs={
                    "device": "cpu",
                },
            )

    def get_model(self):
        return self.model