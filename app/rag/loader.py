from langchain_community.document_loaders import PyPDFLoader


def load_pdf(file_path):
    """
    Load a PDF and return a list of LangChain Document objects.
    """
    loader = PyPDFLoader(file_path)
    documents = loader.load()

    return documents