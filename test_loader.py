from app.rag.loader import load_pdf

docs = load_pdf("documents/sample.pdf")

print(f"Pages: {len(docs)}")

print()
print(docs[0].page_content[:500])