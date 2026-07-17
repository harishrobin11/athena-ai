import json

from ..providers.ollama_provider import ask_llm
from ..core.tool_prompt import TOOL_SELECTION_PROMPT


def select_tool(user_query: str):

    prompt = f"""
{TOOL_SELECTION_PROMPT}

User Question:
{user_query}
"""

    response = ask_llm(
        [
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    print("RAW LLM RESPONSE:")
    print(response)

    try:
        return json.loads(response)

    except Exception:
        return {
            "tool": None,
            "input": None,
        }