import chromadb

# Persistent database
client = chromadb.PersistentClient(path="data/chroma")

# Collection for semantic memories
memory_collection = client.get_or_create_collection(
    name="semantic_memory"
)


def save_memories(
    user_id: str,
    memories: list,
):
    """
    Save or update semantic memories.
    """

    if not memories:
        return

    for memory in memories:

        memory_type = memory.get("type")
        key = memory.get("key")
        value = memory.get("value")

        if not key or not value:
            continue

        document = f"{key}: {value}"

        # Stable ID for each user's memory key
        memory_id = f"{user_id}:{key}"

        memory_collection.upsert(
            ids=[memory_id],
            documents=[document],
            metadatas=[
                {
                    "user_id": user_id,
                    "type": memory_type,
                    "key": key,
                }
            ],
        )