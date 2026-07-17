from ..rag.retriever import Retriever


def search_documents_tool(
    tool_input,
    context,
):
    """
    Search documents using the Enterprise RAG retriever.
    """

    query = tool_input

    user_id = context.get("user_id")

    selected_documents = context.get(
        "selected_documents"
    )

    print("===== DOCUMENT TOOL =====")
    print("USER:", user_id)
    print("FILES:", selected_documents)
    print("QUERY:", query)

    retriever = Retriever()

    filter_metadata = {
        "user_id": user_id
    }

    if selected_documents:

        if len(selected_documents) == 1:

            filter_metadata = {
                "$and": [
                    {
                        "user_id": user_id
                    },
                    {
                        "source":
                        f"documents/user_{user_id}/{selected_documents[0]}"
                    }
                ]
            }

    docs = retriever.retrieve(
        query,
        filter_metadata=filter_metadata,
    )

    return "\n\n".join(
        doc["document"]
        for doc in docs
    )