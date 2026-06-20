from langchain_huggingface import HuggingFaceEmbeddings


class EmbeddingModel:
    def __init__(self):
        self.model = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={
                "device": "cpu",
                "local_files_only": True,
            },
        )

    def get_model(self):
        return self.model