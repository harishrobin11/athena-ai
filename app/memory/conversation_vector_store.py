from app.rag.embedder import EmbeddingModel
from langchain_core.documents import Document
import uuid


class ConversationVectorStore:

    def __init__(
        self,
        persist_directory="data/chroma_conversations",
    ):
        self.embedding = EmbeddingModel().get_model()
        
        import os
        azure_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
        azure_key = os.getenv("AZURE_SEARCH_KEY")
        
        if azure_endpoint and azure_key:
            try:
                from langchain_community.vectorstores.azuresearch import AzureSearch
                self.db = AzureSearch(
                    azure_search_endpoint=azure_endpoint,
                    azure_search_key=azure_key,
                    index_name="athena-conversations",
                    embedding_function=self.embedding.embed_query
                )
                return
            except ImportError:
                print("azure-search-documents missing, falling back to Chroma")

        try:
            from langchain_chroma import Chroma
        except ImportError:
            from langchain_community.vectorstores import Chroma

        try:
            self.db = Chroma(
                persist_directory=persist_directory,
                embedding_function=self.embedding,
            )
        except Exception as e:
            print(f"[CHROMA RECOVERY] Recovering Chroma index at {persist_directory}: {e}")
            import os, shutil
            if os.path.exists(persist_directory):
                try:
                    shutil.rmtree(persist_directory)
                except Exception:
                    pass
            self.db = Chroma(
                persist_directory=persist_directory,
                embedding_function=self.embedding,
            )

    def add_message(
        self,
        message,
        user_id,
        conversation_id,
        role,
        timestamp,
    ):
        doc = Document(
            page_content=message,
            metadata={
                "user_id": str(user_id),
                "conversation_id": str(conversation_id),
                "role": role,
                "timestamp": timestamp,
            },
        )

        self.db.add_documents(
            [doc],
            ids=[str(uuid.uuid4())],
        )

    def search_messages(
        self,
        query,
        user_id,
        k=8,
    ):
        return self.db.similarity_search(
            query,
            k=k,
            filter={
                "user_id": str(user_id),
            },
        )