from langchain_text_splitters import RecursiveCharacterTextSplitter


class DocumentSplitter:
    def __init__(self, chunk_size=500, chunk_overlap=100):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=[
                "\n\n",
                "\n",
                ". ",
                " ",
                "",
            ],
        )

    def split(self, documents):
        return self.splitter.split_documents(documents)