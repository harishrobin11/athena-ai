from ..providers.ollama_provider import ask_llm
from ..core.router_prompt import ROUTER_PROMPT


def classify_query(
    query: str,
    selected_documents=None,
) -> str:

    q = query.lower().strip()

    # -------------------------------
    # FAST RULES (No LLM)
    # -------------------------------

    # Explicit memory requests
    memory_keywords = [
        "remember",
        "previous",
        "earlier",
        "history",
        "conversation",
        "last chat",
        "continue",
        "what did i",
        "what was my",
        "my project",
        "my name",
    ]

    if any(k in q for k in memory_keywords):
        return "memory"

    # Explicit document requests
    if selected_documents and any(
        k in q for k in [
            "pdf",
            "document",
            "file",
            "summarize",
            "summary",
            "notes",
            "uploaded",
        ]
    ):
        return "documents"

    # Calculator
    if any(op in q for op in ["+", "-", "*", "/", "%"]):
        return "calculator"

    # -------------------------------
    # FALLBACK TO LLM ROUTER
    # -------------------------------

    prompt = f"""
{ROUTER_PROMPT}

User:
{query}
"""

    response = ask_llm(
        [
            {
                "role": "user",
                "content": prompt,
            }
        ]
    )

    return response.strip().lower()