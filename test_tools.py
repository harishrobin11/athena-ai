from app.tools.registry import execute_tool
from app.rag.retriever import Retriever


print(
    execute_tool(
        "search_documents",
        "company policy"
    )
)