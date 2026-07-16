from app.rag.loader import load_pdf
from app.rag.splitter import DocumentSplitter
from app.rag.vector_store import VectorStore

docs = load_pdf("documents/sample.pdf")

splitter = DocumentSplitter()

chunks = splitter.split(docs)

db = VectorStore()

db.add_documents(chunks, dept_id="GENERAL")

print("Documents added successfully!")

results = db.similarity_search(
    query="What is Artificial Intelligence?",
    dept_id="GENERAL"
)

print("\nTop Results:\n")

for i, doc in enumerate(results, 1):
    print(f"Result {i}")
    print(doc.page_content[:250])
    print("-" * 50)