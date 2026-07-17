import json

from ..providers.ollama_provider import ask_llm
from ..core.tool_prompt import TOOL_SELECTION_PROMPT


def create_plan(user_query: str):

    prompt = f"""
{TOOL_SELECTION_PROMPT}

User:
{user_query}

Return a JSON array.

Example:

[
    {{
        "tool": "search_conversations",
        "input": "Sprint 9"
    }},
    {{
        "tool": "search_documents",
        "input": "cancellation"
    }}
]
"""

    response = ask_llm(
        [
            {
                "role": "user",
                "content": prompt,
            }
        ]
    )
    print("===== RAW PLAN =====")
    print(response)

    try:
        plan = json.loads(response)

        # Normalize to a list
        if isinstance(plan, dict):
            plan = [plan]

        print("===== PARSED PLAN =====")
        print(plan)
        print(type(plan))

        return plan
    except:
        return []
