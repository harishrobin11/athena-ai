from app.memory.store import memory_collection

results = memory_collection.get()
for i in range(len(results['ids'])):
    print("ID:", results['ids'][i])
    print("Document:", results['documents'][i])
    print("Metadata:", results['metadatas'][i])
    print("-" * 20)
