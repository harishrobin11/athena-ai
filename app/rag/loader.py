import os
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_core.documents import Document

def load_pdf(file_path: str):
    """
    Load a PDF, Image, or Text file and return a list of LangChain Document objects.
    Robust fallback handling for PDFs, images, and text.
    """
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext in [".png", ".jpg", ".jpeg", ".tiff", ".webp", ".bmp"]:
        text_content = ""
        try:
            from PIL import Image
            import pytesseract
            img = Image.open(file_path)
            text_content = pytesseract.image_to_string(img).strip()
        except Exception:
            pass
            
        if not text_content:
            filename = os.path.basename(file_path)
            text_content = f"[Image Document: {filename}]\nImage file uploaded and ingested into knowledge vault."
            
        return [Document(page_content=text_content, metadata={"source": file_path})]

    if ext in [".txt", ".md", ".csv", ".json"]:
        try:
            return TextLoader(file_path, encoding="utf-8").load()
        except Exception:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return [Document(page_content=f.read(), metadata={"source": file_path})]

    try:
        loader = PyPDFLoader(file_path)
        documents = loader.load()
        if documents:
            return documents
    except Exception as e:
        print(f"[LOADER WARNING] PyPDFLoader failed for {file_path}: {e}")

    try:
        import fitz  # PyMuPDF
        doc = fitz.open(file_path)
        documents = []
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            if text.strip():
                documents.append(Document(page_content=text, metadata={"source": file_path, "page": page_num + 1}))
        if documents:
            return documents
    except Exception as ex:
        print(f"[LOADER WARNING] PyMuPDF fallback failed: {ex}")

    filename = os.path.basename(file_path)
    return [Document(page_content=f"[Document: {filename}]\nFile uploaded into knowledge vault.", metadata={"source": file_path})]