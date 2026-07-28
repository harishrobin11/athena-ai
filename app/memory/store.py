import os
import chromadb

_client = None
_collection = None

def _get_memory_collection():
    global _client, _collection
    if _collection is None:
        path = "data/chroma"
        try:
            _client = chromadb.PersistentClient(path=path)
        except Exception as e:
            print(f"[CHROMA RECOVERY] Recovering corrupted Chroma index at {path}: {e}")
            db_file = os.path.join(path, "chroma.sqlite3")
            if os.path.exists(db_file):
                try:
                    os.remove(db_file)
                except Exception:
                    pass
            _client = chromadb.PersistentClient(path=path)
        _collection = _client.get_or_create_collection(name="semantic_memory")
    return _collection

class _MemoryCollectionProxy:
    def __getattr__(self, name):
        return getattr(_get_memory_collection(), name)

memory_collection = _MemoryCollectionProxy()


def save_memories(
    user_id: str,
    memories: list,
):
    """
    Save or update semantic memories.
    """
    if not memories:
        return

    collection = _get_memory_collection()
    for memory in memories:
        memory_type = memory.get("type")
        key = memory.get("key")
        value = memory.get("value")

        if not key or not value:
            continue

        document = f"{key}: {value}"
        memory_id = f"{user_id}:{key}"

        collection.upsert(
            ids=[memory_id],
            documents=[document],
            metadatas=[
                {
                    "user_id": str(user_id),
                    "type": memory_type,
                    "key": key,
                }
            ],
        )

def search_memories(user_id: str, query: str, top_k: int = 5) -> list[str]:
    """
    Retrieve semantic memories for a user based on a query.
    """
    try:
        collection = _get_memory_collection()
        results = collection.query(
            query_texts=[query],
            n_results=top_k,
            where={"user_id": str(user_id)}
        )
        
        if results and results.get("documents") and len(results["documents"]) > 0:
            return results["documents"][0]
        return []
    except Exception as e:
        print(f"[MEMORY LOG] Error retrieving semantic memories: {e}")
        return []