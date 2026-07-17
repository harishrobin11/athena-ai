from app.memory.store import memory_collection


def search_memory(
    query: str,
    user_id: str,
    top_k: int = 5,
):
    """
    Search semantic memories for a user.
    """

    results = memory_collection.query(
        query_texts=[query],
        n_results=top_k,
        where={
            "user_id": user_id,
        },
    )

    documents = results.get("documents", [[]])[0]

    if not documents:
        return "No relevant memories found."

    return "\n".join(documents)