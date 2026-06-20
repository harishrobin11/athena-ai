from app.rag.loader import load_pdf
from app.rag.splitter import DocumentSplitter

docs = load_pdf("documents/sample.pdf")

splitter = DocumentSplitter()

chunks = splitter.split(docs)

print(f"Pages : {len(docs)}")
print(f"Chunks: {len(chunks)}")

print("\nFirst chunk:\n")
print(chunks[0].page_content[:500])

print("\nMetadata:")
print(chunks[0].metadata)