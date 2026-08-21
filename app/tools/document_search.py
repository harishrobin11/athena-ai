from ..rag.retriever import Retriever
from .registry import register_tool

@register_tool("search_documents")
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

    filter_metadata = {}
    if user_id is not None:
        filter_metadata["user_id"] = user_id

    if selected_documents and user_id is not None:
        if len(selected_documents) == 1:
            filter_metadata = {
                "$and": [
                    {
                        "user_id": user_id
                    },
                    {
                        "filename": selected_documents[0]
                    }
                ]
            }

    if not filter_metadata:
        filter_metadata = None

    dept_id = context.get("dept_id", "GENERAL") if context else "GENERAL"
    docs = retriever.retrieve(
        query=query,
        dept_id=dept_id,
        filter_metadata=filter_metadata,
    )

    def _extract_text(doc):
        if hasattr(doc, "page_content"):
            return doc.page_content
        if isinstance(doc, dict):
            return doc.get("document", str(doc))
        return str(doc)

    return "\n\n".join(
        _extract_text(doc)
        for doc in docs
    )