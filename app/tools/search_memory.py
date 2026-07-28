from app.memory.store import memory_collection


from .registry import register_tool

@register_tool("search_memory")
def search_memory(
    tool_input: str,
    context: dict,
):
    query = tool_input
    user_id = context.get("user_id")
    top_k = 5
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