from app.memory.conversation_vector_store import (
    ConversationVectorStore,
)


from .registry import register_tool

@register_tool("search_conversations")
def search_conversations_tool(
    tool_input,
    context,
):
    """
    Search semantically across previous conversations.
    """

    query = tool_input

    user_id = context.get("user_id")

    print("\n===== SEMANTIC SEARCH =====")
    print("Query:", query)
    print("User:", user_id)

    store = ConversationVectorStore()

    docs = store.search_messages(
        query=query,
        user_id=user_id,
        k=10,
    )

    print("Documents found:", len(docs))

    for i, doc in enumerate(docs):
        print(f"\nResult {i + 1}")
        print("Metadata:", doc.metadata)
        print("Content:", doc.page_content)

    results = []

    for doc in docs:
        results.append(
            {
                "conversation_id": doc.metadata.get("conversation_id"),
                "role": doc.metadata.get("role"),
                "content": doc.page_content,
                "timestamp": doc.metadata.get("timestamp"),
            }
        )

    return results